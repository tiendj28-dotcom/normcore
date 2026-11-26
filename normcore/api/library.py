"""API và tác vụ nền của thư viện văn bản (FEAT-020).

Kiểm quyền tường minh trong từng hàm whitelisted. Thông báo dùng Notification Log (ASM-020-11).
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate, today

from normcore.library import mapping, validity
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


def _suggest_after_index(name):
	"""FR-SVC-005: lỗi đề xuất không làm văn bản thành "Lỗi" (ASM-022-10)."""
	sp = "nc_library_suggest"
	frappe.db.savepoint(sp)
	try:
		refresh_suggestions(name)
		_commit()
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(title=f"Đề xuất ánh xạ văn bản {name}")


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
		_suggest_after_index(name)
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


# ---------------------------------------------------------------------------------------------
# Ánh xạ hướng dẫn với dịch vụ (FEAT-022: FR-SVC-005..007)
# ---------------------------------------------------------------------------------------------

_MAP_FIELDS = ("name", "technical_service", "mapping_status", "confidence", "confirmed_by", "confirmed_on")


def _row_dict(r):
	return {k: r.get(k) for k in _MAP_FIELDS}


def _sig(rows):
	return sorted((r["technical_service"], r["mapping_status"], r.get("confidence")) for r in rows)


def refresh_suggestions(legal_document):
	"""Tính lại đề xuất cho mọi mục của văn bản hướng dẫn QTKT; giữ dòng "Đã xác nhận" (FR-SVC-005)."""
	doc = frappe.get_doc("NC Legal Document", legal_document)
	if not doc.is_procedure_guideline:
		return {"sections": 0, "suggested": 0}
	services = [
		(r.name, r.service_name)
		for r in frappe.get_all(
			"NC Technical Service", filters={"is_active": 1}, fields=["name", "service_name"]
		)
	]
	index = mapping.build_token_index(services)
	sections = frappe.get_all(
		"NC Legal Section",
		filters={"legal_document": legal_document},
		fields=["name", "section_no", "heading"],
	)
	n_sections = n_suggested = 0
	for sec in sections:
		if not mapping.is_mappable_section(sec.section_no):
			continue
		n_sections += 1
		section = frappe.get_doc("NC Legal Section", sec.name)
		existing = [_row_dict(r) for r in section.service_mappings]
		merged = mapping.merge_suggestions(
			existing, mapping.suggest_for_section(sec.heading or "", services, index)
		)
		n_suggested += sum(1 for r in merged if r["mapping_status"] == mapping.SUGGESTED)
		if _sig(merged) != _sig(existing):
			section.set("service_mappings", merged)
			section.save(ignore_permissions=True)
	return {"sections": n_sections, "suggested": n_suggested}


def _require_guideline_write(legal_document):
	doc = frappe.get_doc("NC Legal Document", legal_document)
	if not frappe.has_permission("NC Legal Section", "write"):
		frappe.throw(_("Bạn không có quyền chỉnh ánh xạ dịch vụ"), frappe.PermissionError)
	return doc


@frappe.whitelist()
def suggest_mappings(legal_document):
	"""Nút "Đề xuất lại" (ASM-022-08)."""
	doc = _require_guideline_write(legal_document)
	if not doc.is_procedure_guideline:
		frappe.throw(_("Văn bản không phải hướng dẫn quy trình kỹ thuật"))
	if doc.index_status != "Đã lập":
		frappe.throw(_("Văn bản chưa lập chỉ mục xong"))
	return refresh_suggestions(legal_document)


@frappe.whitelist()
def get_mappings(legal_document, unconfirmed_only=0, start=0, page_length=100):
	doc = frappe.get_doc("NC Legal Document", legal_document)
	if not frappe.has_permission("NC Legal Document", "read", doc=doc):
		frappe.throw(_("Bạn không có quyền xem văn bản này"), frappe.PermissionError)
	secs = frappe.get_all(
		"NC Legal Section",
		filters={"legal_document": legal_document},
		fields=["name", "section_no", "heading", "validity_status"],
	)
	secs = [s for s in secs if mapping.is_mappable_section(s.section_no)]
	secs.sort(key=lambda r: natural_key(r.section_no))
	maps = {}
	if secs:
		for m in frappe.db.sql(
			"SELECT m.name AS row, m.parent, m.technical_service, t.service_name, m.mapping_status, m.confidence,"
			" m.confirmed_by, m.confirmed_on FROM `tabNC Section Service Map` m"
			" LEFT JOIN `tabNC Technical Service` t ON t.name = m.technical_service"
			" WHERE m.parenttype = 'NC Legal Section' AND m.parentfield = 'service_mappings'"
			" AND m.parent IN %s ORDER BY m.idx",
			[tuple(s.name for s in secs)],
			as_dict=True,
		):
			maps.setdefault(m.pop("parent"), []).append(m)
	pending_exact = sum(
		1
		for rows in maps.values()
		for m in rows
		if m.mapping_status == mapping.SUGGESTED and (m.confidence or 0) == mapping.CODE_CONFIDENCE
	)
	out = []
	for s in secs:
		rows = maps.get(s.name, [])
		if cint(unconfirmed_only) and rows and all(m.mapping_status == mapping.CONFIRMED for m in rows):
			continue
		out.append(
			{
				"section": s.name,
				"section_no": s.section_no,
				"heading": s.heading,
				"validity_status": s.validity_status,
				"mappings": rows,
			}
		)
	start, page_length = cint(start), min(cint(page_length) or 100, 500)
	return {"total": len(out), "pending_exact": pending_exact, "rows": out[start : start + page_length]}


def _writable_section(section_name):
	section = frappe.get_doc("NC Legal Section", section_name)
	if not frappe.has_permission("NC Legal Section", "write", doc=section):
		frappe.throw(_("Bạn không có quyền chỉnh ánh xạ dịch vụ"), frappe.PermissionError)
	return section


def _confirm_rows(legal_document, only=None):
	"""Đặt "Đã xác nhận" cho các dòng "Đề xuất" (`only`: tập tên dòng, None = mọi dòng 100%)."""
	_require_guideline_write(legal_document)
	rows = frappe.db.sql(
		"SELECT m.name, m.parent, m.mapping_status, m.confidence, s.legal_document"
		" FROM `tabNC Section Service Map` m JOIN `tabNC Legal Section` s ON s.name = m.parent"
		" WHERE m.parenttype = 'NC Legal Section' AND m.parentfield = 'service_mappings'"
		" AND (s.legal_document = %s OR m.name IN %s)",
		[legal_document, tuple(only or ["-"])],
		as_dict=True,
	)
	by_name = {r.name: r for r in rows}
	if only is not None:
		for name in only:
			if name not in by_name or by_name[name].legal_document != legal_document:
				frappe.throw(_("Ánh xạ không thuộc văn bản này"))
		picked = {by_name[n].name for n in only}
	else:
		picked = {
			r.name
			for r in rows
			if r.legal_document == legal_document and (r.confidence or 0) == mapping.CODE_CONFIDENCE
		}
	todo = {}
	for r in rows:
		if r.name in picked and r.mapping_status == mapping.SUGGESTED:
			todo.setdefault(r.parent, set()).add(r.name)
	for parent, names in todo.items():
		section = _writable_section(parent)
		for row in section.service_mappings:
			if row.name in names:
				row.mapping_status = mapping.CONFIRMED
		section.save()
	return {"confirmed": sum(len(v) for v in todo.values())}


@frappe.whitelist()
def confirm_mappings(legal_document, rows):
	"""Xác nhận các dòng đã chọn (FR-SVC-006); dòng đã xác nhận được bỏ qua."""
	_require_guideline_write(legal_document)
	return _confirm_rows(legal_document, set(frappe.parse_json(rows) if isinstance(rows, str) else rows))


@frappe.whitelist()
def confirm_exact(legal_document):
	"""Xác nhận mọi dòng "Đề xuất" có độ tin cậy 100%."""
	return _confirm_rows(legal_document, None)


@frappe.whitelist()
def save_mapping(section, technical_service, row=None):
	"""Sửa dịch vụ của một dòng, hoặc thêm ánh xạ tay (UC-003 5a); kết quả luôn "Đã xác nhận"."""
	sec = _writable_section(section)
	frappe.get_doc("NC Technical Service", technical_service)  # DoesNotExistError nếu không có
	if row:
		target = next((r for r in sec.service_mappings if r.name == row), None)
		if target is None:
			frappe.throw(_("Ánh xạ không thuộc mục này"))
		if target.technical_service != technical_service:
			target.confidence = None  # độ tin cậy gắn với dịch vụ được đề xuất ban đầu
		target.technical_service = technical_service
		target.mapping_status = mapping.CONFIRMED
	else:
		target = sec.append(
			"service_mappings", {"technical_service": technical_service, "mapping_status": mapping.CONFIRMED}
		)
	sec.save()
	row_name = row or next(r.name for r in sec.service_mappings if r.technical_service == technical_service)
	return {"row": row_name, "mapping_status": mapping.CONFIRMED}


@frappe.whitelist()
def remove_mapping(row):
	"""Bỏ một ánh xạ (đề xuất sai hoặc gỡ ánh xạ, UC-003 4a)."""
	parent = frappe.db.get_value("NC Section Service Map", row, ["parent", "parenttype"], as_dict=True)
	if not parent or parent.parenttype != "NC Legal Section":
		frappe.throw(_("Không tìm thấy ánh xạ"), frappe.DoesNotExistError)
	sec = _writable_section(parent.parent)
	sec.set("service_mappings", [r for r in sec.service_mappings if r.name != row])
	sec.save()
	return {"removed": 1}


def get_draft_sources(technical_service, valid_only=True):
	"""Cửa duy nhất dựng nguồn gửi AI cho một dịch vụ (FR-SVC-007; FEAT-024 gọi hàm này).

	Chỉ mục có ánh xạ "Đã xác nhận" với dịch vụ, mặc định chỉ mục còn hiệu lực (ASM-022-07);
	qua `guard.build_source` nên chỉ mang các trường được phép gửi AI.
	"""
	from normcore.ai import guard

	validity_sql = " AND s.validity_status = 'Còn hiệu lực'" if valid_only else ""
	rows = frappe.db.sql(
		"SELECT DISTINCT s.name, s.section_no, s.heading, s.plain_text, d.doc_number"
		" FROM `tabNC Legal Section` s"
		" JOIN `tabNC Legal Document` d ON d.name = s.legal_document"
		" JOIN `tabNC Section Service Map` m ON m.parent = s.name AND m.parenttype = 'NC Legal Section'"
		" AND m.parentfield = 'service_mappings'"
		f" WHERE m.technical_service = %s AND m.mapping_status = %s{validity_sql}",
		(technical_service, mapping.CONFIRMED),
		as_dict=True,
	)
	rows.sort(key=lambda r: (normalize_doc_number(r.doc_number), natural_key(r.section_no)))
	return [guard.build_source("NC Legal Section", r) for r in rows]
