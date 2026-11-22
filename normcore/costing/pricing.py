"""Chọn đơn giá, cảnh báo, quy đổi đơn vị định mức, dòng chi phí vật chất (FEAT-009). Không import frappe.

BR-COST-003 (golden_engine.py::direct_lines, nhánh DRUG/SUPPLY), BR-CLS-002 (golden_cls.py::unit_price),
FR-RES-003, FR-RES-004, FR-RES-014, FR-RES-017.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

# FR-RES-004: thứ tự này là thứ tự ưu tiên khi chọn giá (cao đến thấp)
SOURCE_ORDER = ("Trúng thầu", "Hợp đồng", "Hóa đơn", "Giá công bố", "Báo giá")
STALE_MONTHS = 24
STALE_WARNING = "Đơn giá quá hạn tham chiếu"
UNVERIFIED_WARNING = "Đơn giá chưa xác minh"
EXCLUDED_REASON = "Thanh toán riêng ngoài giá dịch vụ"
# FR-RES-018: ba loại này bắt buộc khai số đơn vị định mức trong một đơn vị mua
NORM_ITEM_TYPES = ("Hóa chất", "Chất chuẩn", "Vật liệu nội kiểm")

_Q2 = Decimal("0.01")
_Q4 = Decimal("0.0001")


class NoEffectivePrice(ValueError):
	"""Mặt hàng không có đơn giá còn hiệu lực tại ngày tính giá (ASM-066)."""


@dataclass(frozen=True)
class PriceRecord:
	name: str
	unit_price: Decimal
	price_source: str
	document_date: date
	valid_from: date
	valid_to: date | None
	verified: bool


@dataclass(frozen=True)
class MaterialLineResult:
	amount: Decimal  # thành tiền, làm tròn 2 số lẻ HALF_UP
	unit_price: Decimal | None  # đơn giá một đơn vị định mức (4 số lẻ); None khi dòng bị loại
	price_name: str | None
	warnings: tuple
	excluded_reason: str | None


def _is_effective(p: PriceRecord, as_of: date) -> bool:
	return p.valid_from <= as_of and (p.valid_to is None or as_of <= p.valid_to)


def _rank(source: str) -> int:
	try:
		return SOURCE_ORDER.index(source)
	except ValueError:
		raise ValueError(f"Nguồn giá không hợp lệ: {source}") from None


def select_price(prices, as_of: date) -> PriceRecord | None:
	"""FR-RES-004: trong các đơn giá còn hiệu lực tại `as_of`, lấy loại nguồn ưu tiên cao nhất, rồi
	ngày bắt đầu hiệu lực gần nhất. Còn bằng nhau: ngày chứng từ mới hơn, rồi tên lớn hơn (ASM-063)."""
	best = None
	best_key = None
	for p in prices:
		rank = _rank(p.price_source)
		if not _is_effective(p, as_of):
			continue
		key = (-rank, p.valid_from, p.document_date, p.name)
		if best_key is None or key > best_key:
			best, best_key = p, key
	return best


def _months_before(d: date, months: int) -> date:
	total = d.year * 12 + (d.month - 1) - months
	year, month = divmod(total, 12)
	month += 1
	# ngày không có trong tháng đích (29/02, 31/…) lùi về ngày cuối tháng
	for day in (d.day, 30, 29, 28):
		try:
			return date(year, month, day)
		except ValueError:
			continue
	raise AssertionError("không tới được")


def price_warnings(price: PriceRecord, as_of: date) -> tuple:
	"""FR-RES-003 (chứng từ cũ hơn 24 tháng so với ngày tính giá; đúng 24 tháng thì chưa, ASM-064) và
	FR-RES-017 (chưa xác minh). Chỉ cảnh báo, không chặn tính giá."""
	out = []
	if price.document_date < _months_before(as_of, STALE_MONTHS):
		out.append(STALE_WARNING)
	if not price.verified:
		out.append(UNVERIFIED_WARNING)
	return tuple(out)


def unit_price_per_norm(unit_price: Decimal, units_per_purchase_unit: Decimal) -> Decimal:
	"""BR-CLS-002: đơn giá một đơn vị định mức = đơn giá đơn vị mua ÷ số đơn vị định mức, 4 số lẻ HALF_UP."""
	units = Decimal(units_per_purchase_unit)
	if units <= 0:
		raise ValueError("Số đơn vị định mức trong một đơn vị mua phải lớn hơn 0")
	return (Decimal(unit_price) / units).quantize(_Q4, rounding=ROUND_HALF_UP)


def material_line(
	applied_qty: Decimal,
	wastage_rate: Decimal,
	reuse_count: int,
	norm_units: Decimal,
	prices,
	as_of: date,
	billed_separately: bool = False,
) -> MaterialLineResult:
	"""BR-COST-003 trên đơn giá một đơn vị định mức (BR-CLS-002), 2 số lẻ HALF_UP:
	thành tiền = lượng áp dụng * (1 + hao hụt) * đơn giá một đơn vị định mức / số lần dùng,
	đơn giá một đơn vị định mức = đơn giá đơn vị mua / `norm_units` (bắt buộc, > 0; ASM-075).
	FR-RES-014: mặt hàng thanh toán riêng → thành tiền 0 kèm lý do, không cần đơn giá."""
	applied_qty, wastage_rate = Decimal(applied_qty), Decimal(wastage_rate)
	if applied_qty < 0 or wastage_rate < 0:
		raise ValueError("Lượng áp dụng và tỷ lệ hao hụt không được âm")
	if reuse_count < 1:
		raise ValueError("Số lần dùng phải từ 1 trở lên")
	if norm_units is None or Decimal(norm_units) <= 0:
		raise ValueError("Số đơn vị định mức trong một đơn vị mua phải có và lớn hơn 0")
	if billed_separately:
		return MaterialLineResult(Decimal("0"), None, None, (), EXCLUDED_REASON)
	price = select_price(prices, as_of)
	if price is None:
		raise NoEffectivePrice("Mặt hàng không có đơn giá còn hiệu lực tại ngày tính giá")
	norm_price = unit_price_per_norm(price.unit_price, norm_units)
	amount = applied_qty * (1 + wastage_rate) * norm_price / reuse_count
	return MaterialLineResult(
		amount.quantize(_Q2, rounding=ROUND_HALF_UP),
		norm_price,
		price.name,
		price_warnings(price, as_of),
		None,
	)
