"""Rà soát quy trình khi văn bản hoặc mục hết hiệu lực (FEAT-021: FR-LIB-009, UC-002 bước 5-7).

Trích dẫn của quy trình là Data (ASM-021-01): khớp theo tên bản ghi hoặc số hiệu, mã mục chuẩn hóa.
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate

from normcore.core import notify
from normcore.core.permissions import _is_scoped, get_user_departments
from normcore.library import supersession, validity
from normcore.procedure import approval, review

DT = "NC Clinical Procedure"


def _build_index(expired_docs, expired_sections):
	"""Chỉ dựng từ văn bản và mục liên quan (NFR-SCAL-002)."""
	documents = [
		(d.name, d.doc_number) for d in frappe.get_all("NC Legal Document", fields=["name", "doc_number"])
	]
	parents = set(expired_docs)
	if expired_sections:
		parents |= set(
			frappe.get_all(
				"NC Legal Section", filters={"name": ["in", list(expired_sections)]}, pluck="legal_document"
			)
		)
	sections = []
	if parents:
		sections = [
			(s.name, s.legal_document, s.section_no)
			for s in frappe.get_all(
				"NC Legal Section",
				filters={"legal_document": ["in", list(parents)]},
				fields=["name", "legal_document", "section_no"],
			)
		]
	return review.build_index(documents, sections), dict(documents), {s[0]: s[2] for s in sections}


def _published_citations():
	return frappe.db.sql(
		"SELECT c.parent AS proc_name, c.name AS row_name, c.target_section, c.target_step_id, c.relation, "
		"c.quote, c.legal_document, c.legal_section, p.workflow_state, p.department "
		"FROM `tabNC Procedure Citation` c JOIN `tabNC Clinical Procedure` p ON p.name = c.parent "
		"WHERE c.parenttype = %s AND c.parentfield = 'citations' AND p.workflow_state = %s "
		"AND (IFNULL(c.legal_document, '') <> '' OR IFNULL(c.legal_section, '') <> '')",
		(DT, approval.PUBLISHED),
		as_dict=True,
	)


def flag_affected(expired_docs, expired_sections, on=None):
	"""Gắn cờ "Cần rà soát" và thông báo trưởng khoa; trả số quy trình được xử lý (FR-LIB-009)."""
	expired_docs, expired_sections = set(expired_docs or ()), set(expired_sections or ())
	if not (expired_docs or expired_sections):
		return 0
	on = getdate(on or frappe.utils.today())
	index, numbers, section_nos = _build_index(expired_docs, expired_sections)
	grouped = {}
	for c in _published_citations():
		grouped.setdefault(
			c.proc_name,
			{
				"name": c.proc_name,
				"workflow_state": c.workflow_state,
				"department": c.department,
				"citations": [],
			},
		)["citations"].append(c)
	count = 0
	for name, refs in review.to_flag(list(grouped.values()), index, expired_docs, expired_sections):
		p = grouped[name]
		for r in refs:
			r["doc_number"] = numbers.get(r["legal_document_name"])
			r["section_no"] = section_nos.get(r["legal_section_name"])
		subject = review.notify_subject(name, refs, on)
		if not frappe.db.get_value(DT, name, "needs_review"):
			frappe.db.set_value(DT, name, "needs_review", 1, update_modified=False)
			frappe.get_doc(DT, name).add_comment("Info", _("Cần rà soát: {0}").format(subject))
		head = frappe.db.get_value("NC Department", p["department"], "head_user")
		if head:
			notify.notify([head], subject, DT, name, from_user="Administrator")
		count += 1
	return count


# ---------------------------------------------------------------------------------------------
# Hàng đợi rà soát (SCR-DSK-012)
# ---------------------------------------------------------------------------------------------

HEAD_ROLE = "NC Department Head"
PENDING = (approval.DRAFT, *approval.PENDING_STATES)


def _can_act(department, user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return HEAD_ROLE in frappe.get_roles(user) and department in get_user_departments(user)


def _replacements(doc_name, section_no):
	rows = frappe.db.sql(
		"SELECT s.parent, s.scope, s.superseded_sections, s.from_date, d.doc_number, d.title "
		"FROM `tabNC Legal Supersession` s JOIN `tabNC Legal Document` d ON d.name = s.parent "
		"WHERE s.parenttype = 'NC Legal Document' AND s.superseded_document = %s ORDER BY s.from_date",
		(doc_name,),
		as_dict=True,
	)
	out = []
	for r in rows:
		if section_no and not supersession.covers(r, section_no):
			continue
		out.append(
			{
				"document": r.parent,
				"doc_number": r.doc_number,
				"title": r.title,
				"scope": r.scope,
				"sections": r.superseded_sections or "",
				"from_date": r.from_date,
			}
		)
	return out


@frappe.whitelist()
def get_review_queue(department=None, start=0, page_length=50):
	"""Quy trình "Đã ban hành" mang cờ "Cần rà soát" kèm trích dẫn bị ảnh hưởng (FR-LIB-009, UC-002 bước 6)."""
	if not frappe.has_permission(DT, "read"):
		frappe.throw(_("Bạn không có quyền xem hàng đợi rà soát"), frappe.PermissionError)
	start, page_length = cint(start), min(max(cint(page_length) or 50, 1), 200)
	filters = {"needs_review": 1, "workflow_state": approval.PUBLISHED}
	if department:
		filters["department"] = department
	if _is_scoped(DT, "read", frappe.session.user):
		# quy trình "Đã ban hành" đọc công khai; hàng đợi chỉ liệt kê khoa của người dùng (SCR-DSK-012)
		mine = sorted(get_user_departments())
		if department and department not in mine:
			mine = []
		filters["department"] = ["in", mine or [""]]
	names = frappe.get_list(DT, filters=filters, pluck="name", limit_page_length=0)
	rows = frappe.get_list(
		DT,
		filters={"name": ["in", names or [""]]},
		fields=["name", "technical_service", "department", "version_no", "effective_date", "decision_no"],
		order_by="modified desc",
		limit_start=start,
		limit_page_length=page_length,
	)
	expired_docs = set(frappe.get_all("NC Legal Document", {"validity_status": validity.HET}, pluck="name"))
	expired_secs = set(frappe.get_all("NC Legal Section", {"validity_status": validity.HET}, pluck="name"))
	index, _numbers, _section_nos = _build_index(expired_docs, expired_secs)
	cits = {}
	if rows:
		for c in frappe.db.sql(
			"SELECT parent, name AS row_name, target_section, target_step_id, relation, quote, legal_document, "
			"legal_section FROM `tabNC Procedure Citation` WHERE parenttype = %s AND parentfield = 'citations' "
			"AND parent IN %s ORDER BY idx",
			(DT, tuple(r.name for r in rows)),
			as_dict=True,
		):
			cits.setdefault(c.parent, []).append(c)
	out = []
	for r in rows:
		items = []
		for c in review.affected(cits.get(r.name, []), index, expired_docs, expired_secs):
			doc, sec = c["legal_document_name"], c["legal_section_name"]
			sec_info = (
				frappe.db.get_value(
					"NC Legal Section",
					sec,
					["section_no", "heading", "validity_status", "expiry_date"],
					as_dict=True,
				)
				if sec
				else None
			)
			doc_info = frappe.db.get_value(
				"NC Legal Document", doc, ["doc_number", "validity_status", "expiry_date"], as_dict=True
			)
			hit = sec_info if (c["reason"] == review.REASON_SECTION and sec_info) else doc_info
			items.append(
				{
					"row": c["row_name"],
					"target_section": c["target_section"],
					"target_step_id": c["target_step_id"],
					"relation": c["relation"],
					"quote": c["quote"],
					"legal_document": c["legal_document"],
					"legal_section": c["legal_section"],
					"doc_number": doc_info.doc_number,
					"section_no": sec_info.section_no if sec_info else None,
					"heading": sec_info.heading if sec_info else None,
					"validity_status": hit.validity_status,
					"expiry_date": hit.expiry_date,
					"reason": c["reason"],
					"replacements": _replacements(doc, sec_info.section_no if sec_info else None),
				}
			)
		pending = frappe.db.get_value(
			DT,
			{
				"technical_service": r.technical_service,
				"department": r.department,
				"workflow_state": ["in", list(PENDING)],
			},
			"name",
		)
		out.append(
			{
				**r,
				"service_name": frappe.db.get_value(
					"NC Technical Service", r.technical_service, "service_name"
				),
				"pending_revision": pending,
				"can_act": 1 if _can_act(r.department) else 0,
				"citations": items,
			}
		)
	return {"total": len(names), "rows": out}


@frappe.whitelist()
def dismiss_review(procedure, reason):
	"""UC-002 bước 7: trưởng khoa kết luận "Không cần sửa" kèm lý do; gỡ cờ."""
	state, needs, dept = frappe.db.get_value(
		DT, procedure, ["workflow_state", "needs_review", "department"]
	) or (
		None,
		0,
		None,
	)
	if dept is None:
		frappe.throw(_("Không tìm thấy quy trình {0}").format(procedure), frappe.DoesNotExistError)
	if not _can_act(dept):
		frappe.throw(_("Chỉ trưởng khoa của khoa chủ trì được kết luận rà soát"), frappe.PermissionError)
	errors = review.dismiss_errors(state, needs, reason)
	if errors:
		frappe.throw("<br>".join(_(e) for e in errors))
	frappe.db.set_value(DT, procedure, "needs_review", 0, update_modified=False)
	frappe.get_doc(DT, procedure).add_comment("Info", _("Không cần sửa: {0}").format(reason.strip()))
	return {"needs_review": 0}
