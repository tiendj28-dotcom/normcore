"""Chuẩn hóa và tìm kiếm văn bản (FR-LIB-002, FR-LIB-010, ADR-006). Hàm thuần."""

import re
import unicodedata

_BOOLEAN_CHARS = '+-<>()~*"@'
_VALIDITY_ORDER = {"Còn hiệu lực": 0, "Chưa hiệu lực": 1, "Hết hiệu lực": 2}


def normalize_doc_number(s):
	"""NFC, bỏ mọi khoảng trắng, casefold: '123/qđ-byt' ≡ '123 / QĐ-BYT'."""
	s = unicodedata.normalize("NFC", s or "")
	return "".join(s.split()).casefold()


def normalize_text(s):
	s = unicodedata.normalize("NFC", s or "")
	return " ".join(s.split()).casefold()


def tokenize(q):
	q = unicodedata.normalize("NFC", q or "")
	for c in _BOOLEAN_CHARS:
		q = q.replace(c, " ")
	return [t for t in re.split(r"[\s.,;:!?/\\|{}\[\]'`]+", q) if t]


def build_fulltext_query(q, min_token=3):
	tokens = [t for t in tokenize(q) if len(t) >= min_token]
	if not tokens:
		return None
	return " ".join(f"+{t}" for t in tokens)


def matches_phrase(text, q):
	needle = normalize_text(q)
	return bool(needle) and needle in normalize_text(text)


def make_snippet(text, q, width=200):
	text = " ".join((text or "").split())
	needle = normalize_text(q)
	pos = normalize_text(text).find(needle) if needle else -1
	if pos < 0:
		return text[:width] + ("…" if len(text) > width else "")
	# casefold có thể đổi độ dài; với văn bản tiếng Việt NFC độ lệch không đáng kể
	start = max(0, pos - width // 2)
	end = min(len(text), start + width)
	return ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")


def section_matches_service(heading, service_name):
	needle = normalize_text(service_name)
	return bool(needle) and needle in normalize_text(heading)


def _natural_key(section_no):
	return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", section_no or "") if t != ""]


def natural_key(section_no):
	"""Khóa sắp tự nhiên, an toàn khi trộn số và chữ."""
	return [(0, t, "") if isinstance(t, int) else (1, 0, t) for t in _natural_key(section_no)]


def rank(results):
	return sorted(
		results,
		key=lambda r: (
			_VALIDITY_ORDER.get(r.get("validity_status"), 9),
			normalize_doc_number(r.get("doc_number", "")),
			natural_key(r.get("section_no", "")),
		),
	)
