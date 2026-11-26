"""Rà soát quy trình khi văn bản hoặc mục hết hiệu lực (FR-LIB-009, UC-002). Hàm thuần, không phụ thuộc frappe.

Trích dẫn của quy trình trỏ bằng Link: `legal_section` (NC Legal Section) và/hoặc `legal_document`
(NC Legal Document, khi chỉ trích dẫn cấp văn bản). Từ NORM-65, ASM-021-13.
"""

from collections import namedtuple
from datetime import date, datetime

from normcore.procedure import approval

REASON_DOC = "Văn bản hết hiệu lực"
REASON_SECTION = "Mục hết hiệu lực"

Index = namedtuple("Index", "section_doc")


def build_index(sections):
	"""sections: (name, legal_document) của các mục liên quan."""
	return Index({name: doc for name, doc in sections})


def resolve(citation, index):
	"""-> (văn bản, mục | None) hoặc None khi trích dẫn không có Link nào."""
	sec = (citation.get("legal_section") or "").strip()
	if sec in index.section_doc:
		return (index.section_doc[sec], sec)
	doc = (citation.get("legal_document") or "").strip()
	if doc:
		return (doc, None)
	return None


def affected(citations, index, expired_docs, expired_sections):
	out = []
	for c in citations:
		hit = resolve(c, index)
		if hit is None:
			continue
		doc, sec = hit
		if doc in expired_docs:
			reason = REASON_DOC
		elif sec is not None and sec in expired_sections:
			reason = REASON_SECTION
		else:
			continue
		out.append({**c, "legal_document_name": doc, "legal_section_name": sec, "reason": reason})
	return out


def to_flag(procedures, index, expired_docs, expired_sections):
	"""procedures: dict name, workflow_state, citations -> [(name, [trích dẫn bị ảnh hưởng])]."""
	out = []
	for p in procedures:
		if p.get("workflow_state") != approval.PUBLISHED:
			continue
		refs = affected(p.get("citations") or [], index, expired_docs, expired_sections)
		if refs:
			out.append((p["name"], refs))
	return out


def _fmt(on):
	if isinstance(on, datetime):
		on = on.date()
	if isinstance(on, date):
		return on.strftime("%d/%m/%Y")
	return str(on)


def notify_subject(procedure, refs, on):
	parts, seen = [], set()
	for r in refs:
		doc = r.get("doc_number") or r.get("legal_document_name") or r.get("legal_document") or ""
		sec = r.get("section_no") or r.get("legal_section") or ""
		label = f"{doc} mục {sec}" if r.get("legal_section_name") and sec else doc
		if label not in seen:
			seen.add(label)
			parts.append(label)
	return f"Cần rà soát quy trình {procedure}: {'; '.join(parts)} hết hiệu lực từ {_fmt(on)}"


def dismiss_errors(state, needs_review, reason):
	errors = []
	if state != approval.PUBLISHED:
		errors.append("Chỉ rà soát quy trình đã ban hành")
	if not needs_review:
		errors.append("Quy trình không có cờ Cần rà soát")
	if not (reason or "").strip():
		errors.append("Cần nhập lý do không cần sửa")
	return errors
