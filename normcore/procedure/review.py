"""Rà soát quy trình khi văn bản hoặc mục hết hiệu lực (FR-LIB-009, UC-002). Hàm thuần, không phụ thuộc frappe.

Trích dẫn của quy trình lưu `legal_document`, `legal_section` dạng Data (ASM-046, ASM-021-01): hàm khớp
chấp nhận cả tên bản ghi lẫn giá trị người dùng gõ.
"""

import re
import unicodedata
from collections import namedtuple
from datetime import date, datetime

from normcore.library.search import normalize_doc_number
from normcore.procedure import approval

REASON_DOC = "Văn bản hết hiệu lực"
REASON_SECTION = "Mục hết hiệu lực"

Index = namedtuple("Index", "doc_names doc_by_number section_by_name section_by_key")


def normalize_section_no(s):
	s = unicodedata.normalize("NFC", s or "").casefold().strip()
	s = re.sub(r"^(mục|điều)\s*", "", s)
	s = "".join(s.split())
	return s.rstrip(".")


def build_index(documents, sections):
	"""documents: (name, doc_number); sections: (name, legal_document, section_no)."""
	doc_names = {n for n, _ in documents}
	by_number = {}
	for name, number in documents:
		key = normalize_doc_number(number)
		if key:
			by_number.setdefault(key, name)
	by_name = {n: (d, n) for n, d, _ in sections}
	by_key = {}
	for name, doc, no in sections:
		by_key.setdefault((doc, normalize_section_no(no)), name)
	return Index(doc_names, by_number, by_name, by_key)


def _doc_of(value, index):
	value = (value or "").strip()
	if not value:
		return None
	if value in index.doc_names:
		return value
	return index.doc_by_number.get(normalize_doc_number(value))


def resolve(citation, index):
	"""-> (văn bản, mục | None) hoặc None."""
	sec_value = (citation.get("legal_section") or "").strip()
	if sec_value in index.section_by_name:
		return index.section_by_name[sec_value]
	doc = _doc_of(citation.get("legal_document"), index)
	if doc is None:
		return None
	if not sec_value:
		return (doc, None)
	return (doc, index.section_by_key.get((doc, normalize_section_no(sec_value))))


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
