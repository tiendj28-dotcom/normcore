"""Ánh xạ mục hướng dẫn QTKT với dịch vụ kỹ thuật (FR-SVC-005..007). Hàm thuần, độc lập framework.

Ngưỡng và số đề xuất là hằng số cấu hình bằng mã (ASM-022-02, Lead duyệt).
"""

import heapq
import re
from functools import lru_cache

from normcore.library.search import normalize_text

CODE_CONFIDENCE = 100
NAME_EXACT_CONFIDENCE = 95
MIN_CONFIDENCE = 50
MAX_SUGGESTIONS = 3
CONFIRMED = "Đã xác nhận"
SUGGESTED = "Đề xuất"

_LEADING_NO = re.compile(r"^\s*[0-9IVXLCivxlc]+[.)]\s*")
_PUNCT = re.compile(r"[^\w\s]|_", re.UNICODE)


class MappingError(Exception):
	"""Hai dòng cùng dịch vụ trong một mục; `args[0]` là mã dịch vụ."""


@lru_cache(maxsize=65536)
def normalize_title(s):
	s = _LEADING_NO.sub("", s or "", count=1)
	s = normalize_text(s)
	s = _PUNCT.sub(" ", s)
	return " ".join(s.split())


@lru_cache(maxsize=65536)
def title_tokens(s):
	return frozenset(normalize_title(s).split())


def code_in_heading(heading, code):
	if not code:
		return False
	if code.casefold() not in (heading or "").casefold():
		return False  # lọc nhanh trước khi dùng regex
	return bool(re.search(r"(?<![\w.])" + re.escape(code) + r"(?![\w.])", heading or "", re.I))


def _dice_confidence(inter, la, lb):
	"""round-half-up(95 x 2·inter/(la+lb)) bằng số nguyên."""
	if not inter:
		return 0
	y = la + lb
	return (2 * NAME_EXACT_CONFIDENCE * 2 * inter + y) // (2 * y)


def name_confidence(heading, service_name):
	ta, tb = title_tokens(heading), title_tokens(service_name)
	if not ta or not tb:
		return 0
	return _dice_confidence(len(ta & tb), len(ta), len(tb))


class TokenIndex(dict):
	"""token → tập mã dịch vụ; `sizes`: mã → số token của tên (chỉ để tăng tốc)."""

	sizes = None
	codes_low = None


def build_token_index(services):
	idx = TokenIndex()
	idx.sizes = {}
	idx.codes_low = [(c, c.casefold()) for c, _ in services if c]
	for code, name in services:
		toks = title_tokens(name)
		idx.sizes[code] = len(toks)
		for t in toks:
			idx.setdefault(t, set()).add(code)
	return idx


def suggest_for_section(heading, services, index=None):
	out = []
	if index is not None and getattr(index, "sizes", None) is not None:
		ht = title_tokens(heading)
		overlap = {}
		for t in ht:
			for c in index.get(t, ()):
				overlap[c] = overlap.get(c, 0) + 1
		low = (heading or "").casefold()
		coded = {c for c, cl in index.codes_low if cl in low and code_in_heading(heading, c)}
		for c in coded:
			out.append((c, CODE_CONFIDENCE))
		for c, inter in overlap.items():
			if c in coded:
				continue
			conf = _dice_confidence(inter, len(ht), index.sizes[c])
			if conf >= MIN_CONFIDENCE:
				out.append((c, conf))
	else:
		for code, name in services:
			if code_in_heading(heading, code):
				out.append((code, CODE_CONFIDENCE))
				continue
			conf = name_confidence(heading, name)
			if conf >= MIN_CONFIDENCE:
				out.append((code, conf))
	return heapq.nsmallest(MAX_SUGGESTIONS, out, key=lambda x: (-x[1], x[0]))


def merge_suggestions(existing_rows, suggestions):
	kept = [dict(r) for r in existing_rows if r.get("mapping_status") == CONFIRMED]
	have = {r["technical_service"] for r in kept}
	for code, conf in suggestions:
		if code not in have:
			kept.append({"technical_service": code, "mapping_status": SUGGESTED, "confidence": conf})
	return kept


def _put(row, key, value):
	if hasattr(row, "set"):  # frappe Document dòng con
		row.set(key, value)
	else:
		row[key] = value


def stamp_rows(rows, before_rows, user, now):
	"""Quy tắc technical-design 2.4. `rows`/`before_rows`: list dict hoặc đối tượng dạng dict."""
	seen = set()
	prev = {r.get("name"): r for r in before_rows if r.get("name")}
	for r in rows:
		svc = r.get("technical_service")
		if svc in seen:
			raise MappingError(svc)
		seen.add(svc)
		if r.get("mapping_status") == CONFIRMED:
			b = prev.get(r.get("name"))
			if b is None or b.get("mapping_status") != CONFIRMED or b.get("technical_service") != svc:
				_put(r, "confirmed_by", user)
				_put(r, "confirmed_on", now)
		else:
			_put(r, "confirmed_by", None)
			_put(r, "confirmed_on", None)


def is_draft_source(row):
	return row.get("mapping_status") == CONFIRMED


def is_mappable_section(section_no):
	return str(section_no).strip() != "0"
