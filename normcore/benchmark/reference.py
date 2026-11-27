"""Kho giá tham chiếu (FEAT-026): logic thuần, không phụ thuộc framework.

FR-BM-004 (đề xuất dịch vụ), FR-BM-005 (chỉ so sánh dòng "Đã xác nhận"),
FR-BM-006 / BR-ADJ-009 (giá hiệu chỉnh), FR-BM-007 (chống trùng).
Giả định: ASM-026-02, 03, 06, 08 (docs/decisions/assumptions/FEAT-026.md).
"""

import re
import unicodedata
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

STATUS_PROPOSED = "Đề xuất"
STATUS_CONFIRMED = "Đã xác nhận"
STATUS_REJECTED = "Loại bỏ"

# ASM-026-02: False thì mọi dòng mới đều "Đề xuất".
CONFIRM_CODED_ROWS = True
# ASM-026-03: ngưỡng Jaccard tối thiểu để đề xuất dịch vụ.
MATCH_THRESHOLD = 0.5

_NON_WORD = re.compile(r"[^0-9a-z]+")


def normalize_name(text):
	"""Chuẩn hóa tên để so khớp: hoa thường, bỏ dấu, bỏ dấu câu, gộp khoảng trắng."""
	if not text:
		return ""
	s = str(text).casefold().replace("đ", "d")
	s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
	return _NON_WORD.sub(" ", s).strip()


def suggest_service(raw_name, services):
	"""Đề xuất mã dịch vụ khớp với tên gốc (không dùng AI). Không khớp: None."""
	raw = normalize_name(raw_name)
	if not raw:
		return None
	raw_words = set(raw.split())
	best_score, best_name = 0.0, None
	for svc in services or []:
		norm = normalize_name(svc.get("service_name"))
		if not norm:
			continue
		if norm == raw:
			score = 1.0
		else:
			words = set(norm.split())
			score = len(raw_words & words) / len(raw_words | words)
		if score < MATCH_THRESHOLD:
			continue
		if score > best_score or (score == best_score and svc["name"] < best_name):
			best_score, best_name = score, svc["name"]
	return best_name


def initial_status(user_service, has_ai_log, keep_status):
	"""Trạng thái ban đầu của dòng mới (ASM-026-02)."""
	if CONFIRM_CODED_ROWS and user_service and not has_ai_log and not keep_status:
		return STATUS_CONFIRMED
	return STATUS_PROPOSED


def _to_date(value):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def month_start(d):
	"""Ngày đầu tháng của `d` (date, datetime hoặc chuỗi ISO)."""
	d = _to_date(d)
	return date(d.year, d.month, 1)


def duplicate_key_matches(a, b):
	"""Hai dòng đã cùng đơn vị: trùng khi cùng loại giá, ngày hiệu lực và cùng dịch vụ (ASM-026-06)."""
	if a.get("facility") != b.get("facility") or a.get("price_category") != b.get("price_category"):
		return False
	if _to_date(a.get("effective_date")) != _to_date(b.get("effective_date")):
		return False
	sa, sb = a.get("technical_service"), b.get("technical_service")
	if sa and sb and sa == sb:
		return True
	na = normalize_name(a.get("service_name_raw"))
	return bool(na) and na == normalize_name(b.get("service_name_raw"))


def find_duplicate(row, candidates):
	"""Tên dòng đầu tiên trong `candidates` trùng với `row` (FR-BM-007); không có: None."""
	for c in candidates or []:
		if c.get("status") == STATUS_REJECTED:
			continue
		if row.get("name") and c.get("name") == row.get("name"):
			continue
		if duplicate_key_matches(row, c):
			return c.get("name")
	return None


def comparable_prices(rows):
	"""FR-BM-005: chỉ giữ dòng "Đã xác nhận", giữ thứ tự."""
	return [r for r in rows if r.get("status") == STATUS_CONFIRMED]


def _valid_index(v):
	return v is not None and v > 0


def adjusted_price(price, index_effective, index_target):
	"""BR-ADJ-009: giá x chỉ số tháng tính giá / chỉ số tháng hiệu lực (ASM-026-08)."""
	if not _valid_index(index_effective) or not _valid_index(index_target):
		raise ValueError("Chỉ số giá phải lớn hơn 0")
	value = Decimal(str(price)) * Decimal(str(index_target)) / Decimal(str(index_effective))
	return value.quantize(Decimal("0.01"), ROUND_HALF_UP)


def adjust(row, cpi_by_month, target_month):
	"""Giá hiệu chỉnh của một dòng; thiếu chỉ số thì không áp dụng và nêu tháng thiếu."""
	eff = month_start(row["effective_date"])
	tgt = month_start(target_month)
	i_eff, i_tgt = cpi_by_month.get(eff), cpi_by_month.get(tgt)
	missing = [m for m, v in ((eff, i_eff), (tgt, i_tgt)) if not _valid_index(v)]
	missing = sorted(set(missing))
	if missing:
		return {"adjusted_price": None, "missing": missing}
	return {
		"adjusted_price": adjusted_price(row["price"], i_eff, i_tgt),
		"index_effective": i_eff,
		"index_target": i_tgt,
		"target_month": tgt,
	}
