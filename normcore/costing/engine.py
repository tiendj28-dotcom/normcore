"""Bộ máy tính giá Normcore - hàm thuần Python, không phụ thuộc frappe (ADR-003).

BR-COST-013 (TBD-02: công thức đang chờ Tài chính kế toán xác nhận; tỷ lệ và cách tính là tham số,
không đặt cứng ở đây).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

_Q2 = Decimal("0.01")
_Q4 = Decimal("0.0001")
ON_COST = "ON_COST"
ON_PRICE = "ON_PRICE"


def _r2(x: Decimal) -> Decimal:
	return x.quantize(_Q2, rounding=ROUND_HALF_UP)


def _r4(x: Decimal) -> Decimal:
	return x.quantize(_Q4, rounding=ROUND_HALF_UP)


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


# ---------------------------------------------------------------------------
# Dòng LABOR: BR-COST-001, BR-COST-002, BR-COST-007 (FEAT-000, walking skeleton)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JobRateResult:
	annual_cost: Decimal  # chi phí năm, không làm tròn
	hourly_rate: Decimal  # đơn giá giờ công, làm tròn 4 số lẻ HALF_UP


def job_rate(
	base_salary: Decimal,
	salary_coef: Decimal,
	allowance_coef: Decimal,
	contribution_rate: Decimal,
	other_income: Decimal,
	working_days: Decimal,
	hours_per_day: Decimal,
	annual_cost_override: Decimal | None = None,
) -> JobRateResult:
	"""BR-COST-001.

	chi phí năm = lương cơ sở * (hệ số lương + hệ số phụ cấp) * 12 * (1 + tỷ lệ đóng góp) + thu nhập khác
	đơn giá giờ công = chi phí năm / (số ngày * số giờ), làm tròn 4 số lẻ HALF_UP.
	annual_cost_override khác None (ASM-002): thay toàn bộ công thức chi phí năm.
	"""
	working_days = Decimal(working_days)
	hours_per_day = Decimal(hours_per_day)
	if working_days * hours_per_day <= 0:
		raise ValueError("Số ngày làm việc năm nhân số giờ làm việc ngày phải lớn hơn 0")
	if annual_cost_override is not None:
		annual = Decimal(annual_cost_override)
		if annual < 0:
			raise ValueError("Chi phí năm nhập thẳng không được âm")
	else:
		annual = Decimal(base_salary) * (Decimal(salary_coef) + Decimal(allowance_coef)) * 12 * (
			1 + Decimal(contribution_rate)
		) + Decimal(other_income)
	return JobRateResult(annual, _r4(annual / (working_days * hours_per_day)))


def applied_qty(hospital_qty: Decimal, authority_qty: Decimal | None = None) -> Decimal:
	"""BR-COST-007: có định mức ban hành thì lấy min; None thì lấy định mức bệnh viện (0 vẫn là "có")."""
	hospital_qty = Decimal(hospital_qty)
	if hospital_qty < 0:
		raise ValueError("Định mức không được âm")
	if authority_qty is None:
		return hospital_qty
	authority_qty = Decimal(authority_qty)
	if authority_qty < 0:
		raise ValueError("Định mức ban hành không được âm")
	return min(hospital_qty, authority_qty)


@dataclass(frozen=True)
class LaborLineResult:
	applied_qty: Decimal  # phút áp dụng
	unit_rate: Decimal  # đơn giá giờ công (đã làm tròn 4 số lẻ)
	amount: Decimal  # thành tiền, làm tròn 2 số lẻ HALF_UP


@dataclass(frozen=True)
class LaborLine:
	line_id: str
	hospital_qty: Decimal  # phút theo định mức bệnh viện
	headcount: int
	hourly_rate: Decimal  # kết quả job_rate().hourly_rate
	authority_qty: Decimal | None = None


def labor_line(
	hospital_qty: Decimal,
	authority_qty: Decimal | None,
	headcount: int,
	hourly_rate: Decimal,
) -> LaborLineResult:
	"""BR-COST-002: thành tiền = phút áp dụng / 60 * số người * đơn giá giờ công, làm tròn 2 số lẻ HALF_UP."""
	if headcount < 1:
		raise ValueError("Số người phải từ 1 trở lên")
	hourly_rate = Decimal(hourly_rate)
	if hourly_rate < 0:
		raise ValueError("Đơn giá giờ công không được âm")
	q = applied_qty(hospital_qty, authority_qty)
	return LaborLineResult(q, hourly_rate, _r2(q / 60 * headcount * hourly_rate))


# Điểm cắm ADR-017: hàm nhận dòng, trả kết quả thay thế hoặc None (= dùng cách tính mặc định).
DirectLineExtension = Callable[[LaborLine], LaborLineResult | None]


def compute_direct_lines(
	lines: Sequence[LaborLine],
	extension: DirectLineExtension | None = None,
) -> list[LaborLineResult]:
	"""Bước tính chi phí trực tiếp từng dòng. `extension` (costing/cls.py sau này) được gọi trước;
	trả None thì dòng LABOR tính theo BR-COST-001..002, 007."""
	results = []
	for line in lines:
		result = extension(line) if extension is not None else None
		if result is None:
			result = labor_line(line.hospital_qty, line.authority_qty, line.headcount, line.hourly_rate)
		results.append(result)
	return results
