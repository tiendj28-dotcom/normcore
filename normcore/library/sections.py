"""Tách mục từ các trang (FR-LIB-003, ASM-020-04). Hàm thuần.

Luật tách nằm trọn trong hàm này để đổi được khi thử với văn bản thật (TBD-09).
"""

import re
from dataclasses import dataclass

from normcore.library.extract import ExtractionError

HEADING_MAX = 140
_QTKT = re.compile(r"^\s*(\d{1,4})\s*[.)]\s+(.+?)\s*$")
_DIEU = re.compile(r"^\s*Điều\s+(\d+[a-zđ]?)\s*[.:]?\s*(.*?)\s*$", re.IGNORECASE)


@dataclass
class Section:
	section_no: str
	heading: str
	page_from: int | None
	page_to: int | None
	plain_text: str


def _is_upper_title(text):
	letters = [c for c in text if c.isalpha()]
	if len(letters) < 3:
		return False
	return sum(1 for c in letters if c.isupper()) / len(letters) >= 0.8


def _match_heading(line, guideline):
	if guideline:
		m = _QTKT.match(line)
		if m and _is_upper_title(m.group(2)):
			return m.group(1), " ".join(m.group(2).split())
		return None
	m = _DIEU.match(line)
	if m:
		no = f"Điều {m.group(1)}"
		return no, (" ".join(m.group(2).split()) or no)
	return None


def _page_no(p):
	return getattr(p, "number", None)


def split_sections(pages, is_procedure_guideline):
	lines = []  # (số trang, dòng)
	for p in pages:
		for ln in (p.text or "").splitlines():
			lines.append((_page_no(p), ln))

	groups = []  # [no, heading, [(page, line)]]
	for page, ln in lines:
		h = _match_heading(ln, bool(is_procedure_guideline)) if ln.strip() else None
		if h:
			groups.append([h[0], h[1], [(page, ln)]])
		elif groups:
			groups[-1][2].append((page, ln))
		elif ln.strip():
			groups.append(["0", "Phần mở đầu", [(page, ln)]])
	has_heading = any(g[0] != "0" or g[1] != "Phần mở đầu" for g in groups)
	# phần mở đầu chỉ tồn tại nếu có tiêu đề sau nó
	if groups and not has_heading:
		groups = []

	if not groups:
		groups = _fallback(pages)
	if not groups:
		raise ExtractionError("Không tách được mục nào từ tệp")

	seen, out = {}, []
	for no, heading, rows in groups:
		seen[no] = seen.get(no, 0) + 1
		if seen[no] > 1:
			no = f"{no}-{seen[no]}"
		text = "\n".join(ln for _, ln in rows).strip()
		pgs = [p for p, ln in rows if p is not None and ln.strip()]
		first = rows[0][0]
		out.append(Section(no, heading[:HEADING_MAX], first, pgs[-1] if pgs else first, text))
	return out


def _fallback(pages):
	groups = []
	numbered = [p for p in pages if _page_no(p) is not None]
	if numbered:
		for p in numbered:
			if (p.text or "").strip():
				n = f"Trang {p.number}"
				groups.append([n, n, [(p.number, ln) for ln in p.text.splitlines()]])
		return groups
	text = "\n".join(p.text or "" for p in pages)
	first = next((ln.strip() for ln in text.splitlines() if ln.strip()), None)
	if first:
		groups.append(["1", first, [(None, ln) for ln in text.splitlines()]])
	return groups
