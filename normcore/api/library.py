"""API và tác vụ nền của thư viện văn bản (FEAT-020).

Kiểm quyền tường minh trong từng hàm whitelisted. Thông báo dùng Notification Log (ASM-020-11).
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate, today

from normcore.library import validity
from normcore.library.extract import ExtractionError, available_ocr, extract_pages, file_kind
from normcore.library.search import (
	build_fulltext_query,
	make_snippet,
	matches_phrase,
	natural_key,
	normalize_doc_number,
	normalize_text,
	rank,
	section_matches_service,
)
from normcore.library.sections import split_sections


def enqueue_index(name, user=None):
	"""Xếp tác vụ lập chỉ mục sau khi giao dịch lưu thành công (FR-LIB-003)."""
	frappe.enqueue(
		"normcore.api.library.index_document",
		queue="long",
		timeout=1800,
		enqueue_after_commit=True,
		name=name,
		notify_user=user,
	)


def refresh_section_validity(legal_document, on=None):
	"""Tính lại hiệu lực các mục của một văn bản (FR-LIB-006)."""
	on = getdate(on or today())
	doc_status = frappe.db.get_value("NC Legal Document", legal_document, "validity_status")
	rows = frappe.get_all(
		"NC Legal Section",
		filters={"legal_document": legal_document},
		fields=["name", "expiry_date", "validity_status"],
	)
	todo = validity.changed(
		[(r.name, doc_status, r.expiry_date, r.validity_status) for r in rows], on, section=True
	)
	for name, status in todo:
		frappe.db.set_value("NC Legal Section", name, "validity_status", status, update_modified=False)
	return len(todo)


def _commit():
	"""Tác vụ nền cần commit từng bước; test chạy trong một giao dịch nên không commit."""
	if not frappe.flags.in_test:
		frappe.db.commit()


def _write_sections(name, sections, doc_status):
	"""Ghi mục theo `section_no`: giữ tên và hạn riêng, cập nhật nội dung, xóa mục không còn (ASM-020-12)."""
	existing = {
		r.section_no: r.name
		for r in frappe.get_all(
			"NC Legal Section", filters={"legal_document": name}, fields=["name", "section_no"]
		)
	}
	keep = set()
	for s in sections:
		values = {
			"heading": s.heading,
			"page_from": s.page_from,
			"page_to": s.page_to,
			"plain_text": s.plain_text,
		}
		if s.section_no in existing:
			doc = frappe.get_doc("NC Legal Section", existing[s.section_no])
			doc.update(values)
		else:
			doc = frappe.get_doc(
				{"doctype": "NC Legal Section", "legal_document": name, "section_no": s.section_no, **values}
			)
		doc.save(ignore_permissions=True)
		keep.add(s.section_no)
	for no, sec in existing.items():
		if no not in keep:
			frappe.delete_doc("NC Legal Section", sec, ignore_permissions=True, force=True)
	return len(sections)


def _notify_failure(doc, reason, user):
	user = user or doc.owner
	if not frappe.db.get_value("User", user, "enabled"):
		return
	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"type": "Alert",
			"document_type": "NC Legal Document",
			"document_name": doc.name,
			"subject": _("Lập chỉ mục văn bản {0} thất bại: {1}").format(doc.doc_number, reason),
			"for_user": user,
			"from_user": "Administrator",
		}
	).insert(ignore_permissions=True)


def _fail(name, reason, notify_user):
	frappe.db.set_value(
		"NC Legal Document",
		name,
		{"index_status": "Lỗi", "index_error": reason},
		update_modified=False,
	)
	doc = frappe.get_doc("NC Legal Document", name)
	_notify_failure(doc, reason, notify_user)
	_commit()


def index_document(name, notify_user=None):
	"""Tác vụ nền: tách văn bản, tách mục, ghi mục (FR-LIB-003, 004, 005)."""
	if not frappe.db.exists("NC Legal Document", name):
		return
	frappe.set_user("Administrator")
	frappe.db.set_value(
		"NC Legal Document", name, {"index_status": "Đang lập", "index_error": ""}, update_modified=False
	)
	_commit()
	savepoint = "nc_library_index"
	frappe.db.savepoint(savepoint)
	try:
		doc = frappe.get_doc("NC Legal Document", name)
		file_doc = frappe.get_doc("File", {"file_url": doc.file})
		pages = extract_pages(file_doc.get_content(), file_doc.file_name or doc.file, ocr=available_ocr())
		sections = split_sections(pages, doc.is_procedure_guideline)
		_write_sections(name, sections, doc.validity_status)
		frappe.db.set_value(
			"NC Legal Document", name, {"index_status": "Đã lập", "index_error": ""}, update_modified=False
		)
		_commit()
	except ExtractionError as e:
		frappe.db.rollback(save_point=savepoint)
		_fail(name, str(e), notify_user)
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		frappe.log_error(title=f"Lập chỉ mục văn bản {name}")
		_fail(name, _("Lỗi hệ thống khi lập chỉ mục"), notify_user)


@frappe.whitelist()
def reindex(legal_document):
	"""Lập lại chỉ mục (thay tệp, chạy lại sau lỗi; UC-001 4b)."""
	doc = frappe.get_doc("NC Legal Document", legal_document)
	if not frappe.has_permission("NC Legal Document", "write", doc=doc):
		frappe.throw(_("Bạn không có quyền lập lại chỉ mục văn bản"), frappe.PermissionError)
	if doc.index_status == "Đang lập":
		frappe.throw(_("Văn bản đang được lập chỉ mục"))
	frappe.db.set_value(
		"NC Legal Document",
		legal_document,
		{"index_status": "Chưa lập", "index_error": ""},
		update_modified=False,
	)
	enqueue_index(legal_document, frappe.session.user)
	return {"index_status": "Chưa lập"}


@frappe.whitelist()
def get_sections(legal_document, start=0, page_length=100):
	doc = frappe.get_doc("NC Legal Document", legal_document)
	if not frappe.has_permission("NC Legal Document", "read", doc=doc):
		frappe.throw(_("Bạn không có quyền xem văn bản này"), frappe.PermissionError)
	rows = frappe.get_all(
		"NC Legal Section",
		filters={"legal_document": legal_document},
		fields=["name", "section_no", "heading", "page_from", "page_to", "validity_status"],
	)
	rows.sort(key=lambda r: natural_key(r.section_no))
	start, page_length = cint(start), min(cint(page_length) or 100, 500)
	return {"total": len(rows), "rows": rows[start : start + page_length]}


@frappe.whitelist()
def get_source_view(section):
	sec = frappe.get_doc("NC Legal Section", section)
	if not frappe.has_permission("NC Legal Section", "read", doc=sec):
		frappe.throw(_("Bạn không có quyền xem mục này"), frappe.PermissionError)
	doc = frappe.get_doc("NC Legal Document", sec.legal_document)
	return {
		"file_url": doc.file,
		"file_kind": file_kind(doc.file),
		"page_from": sec.page_from or None,
		"page_to": sec.page_to or None,
		"doc_number": doc.doc_number,
		"section_no": sec.section_no,
	}


def refresh_validity(today=None):
	"""Tính lại hiệu lực mọi văn bản rồi mọi mục; chỉ ghi dòng đổi (FR-LIB-006)."""
	on = getdate(today) if today else getdate(frappe.utils.today())
	docs = frappe.get_all(
		"NC Legal Document", fields=["name", "effective_date", "expiry_date", "validity_status"]
	)
	changed_docs = validity.changed(
		[(d.name, d.effective_date, d.expiry_date, d.validity_status) for d in docs], on
	)
	for name, status in changed_docs:
		frappe.db.set_value("NC Legal Document", name, "validity_status", status, update_modified=False)
	doc_status = {d.name: d.validity_status for d in docs}
	doc_status.update(dict(changed_docs))
	secs = frappe.get_all(
		"NC Legal Section", fields=["name", "legal_document", "expiry_date", "validity_status"]
	)
	changed_secs = validity.changed(
		[(s.name, doc_status.get(s.legal_document), s.expiry_date, s.validity_status) for s in secs],
		on,
		section=True,
	)
	for name, status in changed_secs:
		frappe.db.set_value("NC Legal Section", name, "validity_status", status, update_modified=False)
	return {"documents": len(changed_docs), "sections": len(changed_secs)}


def daily_job():
	"""Scheduler hằng ngày (FR-LIB-006)."""
	refresh_validity()


MODES = ("auto", "text", "doc_number", "service")
MAX_CANDIDATES = 2000
_COLS = (
	"s.name AS section, s.legal_document, d.doc_number, d.title AS doc_title, s.section_no, s.heading, "
	"s.page_from, s.page_to, s.validity_status, d.doc_type"
)
_FROM = "FROM `tabNC Legal Section` s JOIN `tabNC Legal Document` d ON d.name = s.legal_document"


def _like(q):
	return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _filters(doc_type, validity_status):
	sql, args = "", []
	if doc_type:
		sql += " AND d.doc_type = %s"
		args.append(doc_type)
	if validity_status:
		sql += " AND s.validity_status = %s"
		args.append(validity_status)
	return sql, args


def _service_names(query):
	"""Tên dịch vụ khớp `query` là mã dịch vụ hoặc mã HIS/LIS/RIS (không phân biệt hoa thường)."""
	key = normalize_text(query)
	names = set()
	for r in frappe.db.sql(
		"SELECT service_code, service_name FROM `tabNC Technical Service` WHERE LOWER(service_code) = %s",
		(key,),
		as_dict=True,
	):
		names.add((r.service_code, r.service_name))
	for r in frappe.db.sql(
		"SELECT t.service_code, t.service_name FROM `tabNC Service Code Map` m "
		"JOIN `tabNC Technical Service` t ON t.name = m.parent "
		"WHERE LOWER(m.external_code) = %s AND m.parenttype = 'NC Technical Service'",
		(key,),
		as_dict=True,
	):
		names.add((r.service_code, r.service_name))
	return names


def _search_text(query, fsql, fargs):
	ft = build_fulltext_query(query)
	if ft:
		rows = frappe.db.sql(
			f"SELECT {_COLS}, s.plain_text {_FROM} WHERE MATCH(s.heading, s.plain_text) AGAINST (%s IN BOOLEAN MODE)"
			f"{fsql} LIMIT {MAX_CANDIDATES}",
			[ft, *fargs],
			as_dict=True,
		)
		rows = [r for r in rows if matches_phrase((r.heading or "") + " " + (r.plain_text or ""), query)]
	else:
		like = _like(query)
		rows = frappe.db.sql(
			f"SELECT {_COLS}, s.plain_text {_FROM} WHERE (s.plain_text LIKE %s OR s.heading LIKE %s)"
			f"{fsql} LIMIT {MAX_CANDIDATES}",
			[like, like, *fargs],
			as_dict=True,
		)
	for r in rows:
		r["match"] = "Nội dung"
	return rows


def _search_doc_number(query, fsql, fargs):
	key = normalize_doc_number(query)
	names = [
		d.name
		for d in frappe.get_all("NC Legal Document", fields=["name", "doc_number"])
		if normalize_doc_number(d.doc_number) == key
	]
	if not names:
		return []
	rows = frappe.db.sql(
		f"SELECT {_COLS}, s.plain_text {_FROM} WHERE s.legal_document IN %s{fsql}",
		[tuple(names), *fargs],
		as_dict=True,
	)
	for r in rows:
		r["match"] = "Số hiệu"
	return rows


def _search_service(query, fsql, fargs):
	found = {}
	for code, name in _service_names(query):
		# (a) ánh xạ đã xác nhận (có từ FEAT-022)
		if frappe.db.table_exists("NC Section Service Map"):
			for r in frappe.db.sql(
				f"SELECT {_COLS}, s.plain_text {_FROM} "
				"JOIN `tabNC Section Service Map` m ON m.parent = s.name AND m.parenttype = 'NC Legal Section' "
				f"WHERE m.technical_service = %s AND m.mapping_status = 'Đã xác nhận'{fsql}",
				[code, *fargs],
				as_dict=True,
			):
				r["match"] = "Ánh xạ dịch vụ"
				found[r.section] = r
		# (b) mục của văn bản hướng dẫn QTKT có tiêu đề chứa tên dịch vụ (ASM-020-08)
		for r in frappe.db.sql(
			f"SELECT {_COLS}, s.plain_text {_FROM} "
			f"WHERE d.is_procedure_guideline = 1 AND s.heading LIKE %s{fsql}",
			[_like(name), *fargs],
			as_dict=True,
		):
			if section_matches_service(r.heading, name) and r.section not in found:
				r["match"] = "Tên dịch vụ"
				found[r.section] = r
	return list(found.values())


@frappe.whitelist()
def search_sections(query, mode="auto", doc_type=None, validity_status=None, start=0, page_length=20):
	"""Tìm mục theo từ khóa, số hiệu hoặc mã dịch vụ (FR-LIB-010)."""
	if not frappe.has_permission("NC Legal Section", "read"):
		frappe.throw(_("Bạn không có quyền tìm trong thư viện văn bản"), frappe.PermissionError)
	query = " ".join((query or "").split())
	if len(query) < 2:
		frappe.throw(_("Nhập ít nhất 2 ký tự"))
	if mode not in MODES:
		frappe.throw(_("Chế độ tìm không hợp lệ"))
	start, page_length = cint(start), min(max(cint(page_length) or 20, 1), 100)
	fsql, fargs = _filters(doc_type, validity_status)

	if mode == "auto":
		if _service_names(query):
			mode = "service"
		elif _search_doc_number(query, "", []):
			mode = "doc_number"
		else:
			mode = "text"
	if mode == "service":
		rows = _search_service(query, fsql, fargs)
	elif mode == "doc_number":
		rows = _search_doc_number(query, fsql, fargs)
	else:
		rows = _search_text(query, fsql, fargs)

	rows = rank(rows)
	out = []
	for r in rows[start : start + page_length]:
		r["page_from"] = r.page_from or None
		r["page_to"] = r.page_to or None
		r["snippet"] = make_snippet(r.pop("plain_text", "") or "", query if mode == "text" else "")
		r.pop("doc_type", None)
		out.append(r)
	return {"mode": mode, "total": len(rows), "rows": out}
