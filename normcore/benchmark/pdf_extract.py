"""Trích bảng giá PDF bằng AI (FEAT-027): logic thuần, không phụ thuộc frappe.

FR-BM-003, FR-AI-008, FR-AI-011. Giả định: ASM-027-04..07 (docs/decisions/assumptions/FEAT-027.md).
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from normcore.benchmark import reference

MAX_PAGES = 30  # ASM-027-05
REQUIRE_NAME_IN_SOURCE = True  # ASM-027-07: False thì giữ cả dòng có tên không thấy trong tệp
NAME_MAX = 140

SKIP_NO_NAME = "Thiếu tên dịch vụ"
SKIP_BAD_PRICE = "Giá không hợp lệ"
SKIP_NO_DATE = "Thiếu ngày hiệu lực"
SKIP_NOT_IN_FILE = "Không thấy trong tệp"

_CURRENCY = re.compile(r"(₫|đ|vnđ|vnd)", re.IGNORECASE)
_THOUSANDS = re.compile(r"^\d{1,3}([.,]\d{3})+$")
_DECIMAL = re.compile(r"^\d+([.,]\d{1,2})?$")
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")


def page_sources(pages):
	"""Nguồn gửi AI: trang có chữ, theo thứ tự (FR-AI-011)."""
	out = []
	for i, p in enumerate(pages, start=1):
		if (p.text or "").strip():
			out.append({"page": p.number or i, "text": p.text})
	return out


def check_page_count(pages):
	if len(pages) > MAX_PAGES:
		raise ValueError(f"Tệp có {len(pages)} trang, vượt {MAX_PAGES} trang. Tách tệp rồi nạp lại.")


def parse_price(value):
	"""Số dương hoặc None."""
	if isinstance(value, bool):
		return None
	if isinstance(value, int | float | Decimal):
		d = Decimal(str(value))
	elif isinstance(value, str):
		s = _CURRENCY.sub("", value).replace(" ", "").replace("\u00a0", "")
		if _THOUSANDS.match(s):
			s = s.replace(".", "").replace(",", "")
		elif _DECIMAL.match(s):
			s = s.replace(",", ".")
		else:
			return None
		try:
			d = Decimal(s)
		except InvalidOperation:
			return None
	else:
		return None
	return d if d > 0 else None


def parse_date(value):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	if not isinstance(value, str):
		return None
	s = value.strip()
	for fmt in _DATE_FORMATS:
		try:
			return datetime.strptime(s, fmt).date()
		except ValueError:
			continue
	return None


def locate(name, pages, hint=None):
	"""Số trang chứa tên dịch vụ (sau chuẩn hóa). Ưu tiên trang AI gợi ý; không thấy: None."""
	n = reference.normalize_name(name)
	if not n:
		return None
	by_number = {}
	for i, p in enumerate(pages, start=1):
		by_number[p.number or i] = reference.normalize_name(p.text)
	if isinstance(hint, int) and not isinstance(hint, bool) and n in by_number.get(hint, ""):
		return hint
	for number, text in by_number.items():
		if n in text:
			return number
	return None


def parse_rows(data, pages, default_date=None):
	"""Kết quả AI -> (dòng hợp lệ, dòng bị bỏ kèm lý do). Cấu trúc sai: ValueError (gateway ghi log "Lỗi")."""
	raw = data.get("rows") if isinstance(data, dict) else None
	if not isinstance(raw, list):
		raise ValueError("Kết quả AI thiếu danh sách rows")
	rows, skipped = [], []
	for item in raw:
		if not isinstance(item, dict):
			skipped.append({"service_name": "", "reason": SKIP_NO_NAME})
			continue
		name = item.get("service_name")
		name = name.strip() if isinstance(name, str) else ""
		if not name:
			skipped.append({"service_name": "", "reason": SKIP_NO_NAME})
			continue
		price = parse_price(item.get("price"))
		if price is None:
			skipped.append({"service_name": name, "reason": SKIP_BAD_PRICE})
			continue
		eff = parse_date(item.get("effective_date")) or default_date
		if eff is None:
			skipped.append({"service_name": name, "reason": SKIP_NO_DATE})
			continue
		page = locate(name, pages, item.get("page"))
		if REQUIRE_NAME_IN_SOURCE and page is None:
			skipped.append({"service_name": name, "reason": SKIP_NOT_IN_FILE})
			continue
		rows.append(
			{
				"service_name_raw": name[:NAME_MAX],
				"price": price,
				"effective_date": eff,
				"page": page,
			}
		)
	return rows, skipped


def source_url(file_url, page, max_len=NAME_MAX):
	if not page:
		return None
	url = f"{file_url}#page={page}"
	return url if len(url) <= max_len else None


def summary(created, duplicates, skipped):
	return {
		"created": created,
		"duplicates": list(duplicates),
		"skipped": list(skipped),
		"not_in_file": sum(1 for s in skipped if s.get("reason") == SKIP_NOT_IN_FILE),
	}
