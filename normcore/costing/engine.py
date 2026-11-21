"""Bộ máy tính giá Normcore - hàm thuần Python, không phụ thuộc frappe (ADR-003).

BR-COST-013 (TBD-02: công thức đang chờ Tài chính kế toán xác nhận; tỷ lệ và cách tính là tham số,
không đặt cứng ở đây).
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

_Q2 = Decimal("0.01")
ON_COST = "ON_COST"
ON_PRICE = "ON_PRICE"


def _r2(x: Decimal) -> Decimal:
	return x.quantize(_Q2, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class AccumulationResult:
	accumulation: Decimal  # khoản tích lũy
	calculated_price: Decimal  # giá tính toán (đã gồm tích lũy và nghĩa vụ tài chính)
	obligation: Decimal  # khoản nghĩa vụ tài chính = giá tính toán - (giá thành + tích lũy)


def apply_accumulation(
	full_cost: Decimal,
	mode: str | None,
	accumulation_rate: Decimal,
	obligation_rate: Decimal,
) -> AccumulationResult:
	"""BR-COST-013.

	mode ON_COST : tích lũy = giá thành * tỷ lệ
	mode ON_PRICE: tích lũy = giá thành * tỷ lệ / (1 - tỷ lệ)
	mode None    : loại giá không có tích lũy -> 0
	giá tính toán = (giá thành + tích lũy) / (1 - tỷ lệ nghĩa vụ tài chính); làm tròn 2 số lẻ HALF_UP.
	"""
	full_cost = Decimal(full_cost)
	accumulation_rate = Decimal(accumulation_rate)
	obligation_rate = Decimal(obligation_rate)
	if full_cost < 0:
		raise ValueError("Giá thành không được âm")
	if mode not in (None, ON_COST, ON_PRICE):
		raise ValueError(f"Cách tính tích lũy không hợp lệ: {mode}")
	if not (Decimal(0) <= obligation_rate < 1):
		raise ValueError("Tỷ lệ nghĩa vụ tài chính phải trong [0, 1)")
	if mode is not None and not (Decimal(0) <= accumulation_rate < 1):
		raise ValueError("Tỷ lệ tích lũy phải trong [0, 1)")

	if mode is None:
		acc = Decimal(0)
	elif mode == ON_COST:
		acc = full_cost * accumulation_rate
	else:
		acc = full_cost * accumulation_rate / (1 - accumulation_rate)
	acc = _r2(acc)
	base = full_cost + acc
	calc = _r2(base / (1 - obligation_rate))
	return AccumulationResult(acc, calc, _r2(calc - base))
