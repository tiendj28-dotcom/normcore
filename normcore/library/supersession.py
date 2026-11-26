"""Thay thế văn bản (FR-LIB-007, FR-LIB-008, UC-002). Hàm thuần, không phụ thuộc frappe."""

import re
from datetime import date, datetime, timedelta

from normcore.library.search import natural_key

ALL = "Toàn bộ"
PART = "Một phần"


def _d(value):
	if value in (None, ""):
		return None
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def parse_sections(text):
	"""Tách mã mục theo `,`, `;`, xuống dòng; bỏ rỗng, bỏ trùng (casefold), sắp tự nhiên."""
	seen, out = set(), []
	for part in re.split(r"[,;\n]", text or ""):
		no = part.strip()
		key = no.casefold()
		if no and key not in seen:
			seen.add(key)
			out.append(no)
	return sorted(out, key=natural_key)


def format_sections(nos):
	return ", ".join(nos)


def expiry_for(from_date):
	"""Ngày hết hiệu lực = ngày liền trước ngày bắt đầu thay thế (FR-LIB-007)."""
	return _d(from_date) - timedelta(days=1)


def plan_expiry(current, from_date):
	"""Ngày hết hiệu lực mới, hoặc None nếu đã có ngày sớm hơn hoặc bằng (chỉ kéo sớm hơn)."""
	new = expiry_for(from_date)
	cur = _d(current)
	if cur is not None and cur <= new:
		return None
	return new


def plan_section_expiry(sections, wanted, from_date):
	"""sections: (name, section_no, expiry_date); wanted: mã mục. Trả [(name, ngày mới)] cho mục cần đổi."""
	keys = {w.strip().casefold() for w in wanted}
	out = []
	for name, section_no, expiry in sections:
		if (section_no or "").strip().casefold() not in keys:
			continue
		new = plan_expiry(expiry, from_date)
		if new is not None:
			out.append((name, new))
	return out


def covers(row, section_no):
	if row.get("scope") != PART:
		return True
	keys = {s.casefold() for s in parse_sections(row.get("superseded_sections"))}
	return (section_no or "").strip().casefold() in keys


def row_errors(rows, own_name, targets):
	"""Lỗi từng dòng (2.4.1–2.4.4). targets: tên B -> {effective_date, doc_number, section_nos}."""
	errors, first_seen = [], {}
	for row in rows:
		idx, b = row.get("idx"), row.get("superseded_document")
		if not b:
			continue
		if b == own_name:
			errors.append(f"Dòng {idx}: Văn bản không thể thay thế chính nó")
			continue
		if b in first_seen:
			errors.append(f"Dòng {idx}: Văn bản {b} đã được khai báo thay thế ở dòng {first_seen[b]}")
		else:
			first_seen[b] = idx
		info = targets.get(b) or {}
		eff = _d(info.get("effective_date"))
		frm = _d(row.get("from_date"))
		if eff and frm and frm <= eff:
			label = info.get("doc_number") or b
			errors.append(
				f"Dòng {idx}: Ngày bắt đầu thay thế phải sau ngày hiệu lực của {label} ({eff.strftime('%d/%m/%Y')})"
			)
		if row.get("scope") == PART:
			wanted = parse_sections(row.get("superseded_sections"))
			if not wanted:
				errors.append(f"Dòng {idx}: Chọn ít nhất một mục bị thay thế")
			else:
				have = {s.strip().casefold() for s in info.get("section_nos") or []}
				missing = [w for w in wanted if w.casefold() not in have]
				if missing:
					label = info.get("doc_number") or b
					errors.append(f"Dòng {idx}: Văn bản {label} không có mục: {format_sections(missing)}")
	return errors


def normalize_rows(rows):
	"""Toàn bộ: xóa danh sách mục; Một phần: về dạng chuẩn "2, 5"."""
	for row in rows:
		if row.get("scope") == PART:
			row["superseded_sections"] = format_sections(parse_sections(row.get("superseded_sections")))
		else:
			row["superseded_sections"] = ""
