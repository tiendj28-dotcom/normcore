"""Rà soát quy trình khi văn bản hoặc mục hết hiệu lực (FEAT-021: FR-LIB-009, UC-002 bước 5–7).

Trích dẫn của quy trình là Data (ASM-021-01): khớp theo tên bản ghi hoặc số hiệu, mã mục chuẩn hóa.
"""

import frappe
from frappe import _
from frappe.utils import getdate

from normcore.core import notify
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
		grouped.setdefault(c.proc_name, {"name": c.proc_name, "workflow_state": c.workflow_state,
			"department": c.department, "citations": []})["citations"].append(c)
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
