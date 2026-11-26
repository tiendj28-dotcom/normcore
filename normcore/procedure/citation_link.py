"""NORM-65 (ASM-046): chuyển giá trị Data cũ của NC Procedure Citation sang tên bản ghi Link. Hàm thuần.

Giá trị cũ khớp được thì đổi sang tên `LD-…`/`LS-…`; không khớp được thì không mất: ghi vào đầu `quote`
dạng "[Căn cứ cũ: …]" và để trống trường Link."""

import re

from normcore.library.search import normalize_doc_number

LEGACY_PREFIX = "[Căn cứ cũ: "


def _section_key(s):
	"""'Điều 5' ≡ '5' ≡ 'điều5'; mã mục chuẩn hóa như số hiệu (NFC, bỏ khoảng trắng, casefold)."""
	return re.sub(r"^(điều|muc|mục)", "", normalize_doc_number(s))


def match_document(value, documents):
	"""`documents`: {name: doc_number}. Khớp theo tên `LD-…`, rồi số hiệu chuẩn hóa bằng nhau,
	rồi số hiệu nằm trong giá trị ('Thông tư 43/2013/TT-BYT'); chỉ nhận khi duy nhất."""
	value = (value or "").strip()
	if not value:
		return None
	if value in documents:
		return value
	key = normalize_doc_number(value)
	for test in (lambda k: k == key, lambda k: k and k in key):
		hits = [n for n, num in documents.items() if test(normalize_doc_number(num))]
		if len(hits) == 1:
			return hits[0]
		if hits:
			return None
	return None


def match_section(value, document, sections):
	"""`sections`: {name: (legal_document, section_no)}. Trả (tên mục, tên văn bản của mục) hoặc (None, None).
	Khớp theo tên `LS-…` (văn bản lấy từ mục), hoặc mã mục chuẩn hóa trong `document` đã khớp; chỉ nhận khi duy nhất."""
	value = (value or "").strip()
	if not value:
		return None, None
	if value in sections:
		return value, sections[value][0]
	if not document:
		return None, None
	key = _section_key(value)
	hits = [n for n, (d, no) in sections.items() if d == document and key and _section_key(no) == key]
	if len(hits) == 1:
		return hits[0], document
	return None, None


def convert_row(legal_document, legal_section, quote, documents, sections):
	"""Trả (legal_document, legal_section, quote) mới. Đã là tên hợp lệ thì giữ nguyên (chạy lại không đổi)."""
	doc_value = (legal_document or "").strip()
	sec_value = (legal_section or "").strip()
	if not doc_value and not sec_value:
		return None, None, quote
	matched_doc = match_document(doc_value, documents)
	sec, sec_doc = match_section(sec_value, matched_doc, sections)
	doc = sec_doc if sec else matched_doc  # mục khớp theo tên LS-: tin mục (ASM-NORM65-03)
	lost = []
	if (doc_value and doc != matched_doc) or (doc_value and not matched_doc):
		lost.append(
			doc_value
		)  # văn bản cũ không khớp, hoặc khớp ra văn bản khác với văn bản của mục: giữ dấu vết
	if sec_value and not sec:
		lost.append(sec_value)
	if lost:
		note = f"{LEGACY_PREFIX}{' — '.join(lost)}]"
		quote = f"{note} {quote}" if quote else note
	return doc, sec, quote
