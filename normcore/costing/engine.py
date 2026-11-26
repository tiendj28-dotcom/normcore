"""Bộ máy tính giá Normcore - hàm thuần Python, không phụ thuộc frappe (ADR-003).

BR-COST-013 (TBD-02: công thức đang chờ Tài chính kế toán xác nhận; tỷ lệ và cách tính là tham số,
không đặt cứng ở đây).
"""

from collections.abc import Callable, Mapping, Sequence
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


# ---------------------------------------------------------------------------
# FEAT-015: chi phí trực tiếp đủ sáu cấu phần, giá thành, giá tính toán, giá làm tròn, giải trình
# ---------------------------------------------------------------------------

# Cấu phần dòng định mức -> loại chi phí (= golden_engine.CATEGORY)
COMPONENT_CATEGORY = {
	"LABOR": "LABOR",
	"DRUG": "DRUG_SUPPLY",
	"SUPPLY": "DRUG_SUPPLY",
	"EQUIPMENT": "DEPRECIATION",
	"INFRA": "DEPRECIATION",
	"UTILITY": "UTILITY",
}
DEPR_EXCLUDED_WARNING = "Khấu hao bị loại (loại giá không kết cấu khấu hao)"
EXCLUDED_REASON = (
	"Thanh toán riêng ngoài giá dịch vụ"  # = pricing.EXCLUDED_REASON (giữ engine không import pricing)
)
STATUS_OK, STATUS_WARN, STATUS_ERROR = "Thành công", "Cảnh báo", "Lỗi"
LINE_DIRECT, LINE_ALLOC = "Trực tiếp", "Phân bổ"
_STALE = "Đơn giá quá hạn tham chiếu"
_UNVERIFIED = "Đơn giá chưa xác minh"
_ZERO = Decimal(0)


@dataclass(frozen=True)
class NormLine:
	"""Một dòng của bộ định mức đã khóa."""

	line_id: str
	step_id: str
	component: str
	resource: str
	resource_label: str
	hospital_qty: Decimal
	authority_qty: Decimal | None = None
	headcount: int = 1
	wastage_rate: Decimal = Decimal(0)  # phân số (Percent ÷ 100)
	excluded: bool = False
	exclude_reason: str | None = None


@dataclass(frozen=True)
class LineRate:
	"""Đơn giá của một dòng, do rates.py dựng từ dữ liệu đã nạp."""

	rate: Decimal
	source: str
	reuse_count: int = 1
	warnings: tuple = ()
	billed_separately: bool = False


@dataclass(frozen=True)
class CostLine:
	"""Một dòng bảng giải trình (NC Service Cost Line)."""

	line_type: str
	component: str
	amount: Decimal
	step_id: str = ""
	norm_line_id: str = ""
	resource_label: str = ""
	applied_qty: Decimal | None = None
	unit_rate: Decimal | None = None
	rate_source: str = ""
	warning: str = ""
	allocation_rule: str | None = None
	driver_value: Decimal | None = None
	driver_total: Decimal | None = None
	pool_amount: Decimal | None = None


@dataclass(frozen=True)
class ServiceInput:
	service: str
	department: str
	norm_set: str
	lines: tuple
	rates: Mapping  # khóa line_id; None = thiếu đơn giá
	volume: Decimal | None = None


@dataclass(frozen=True)
class PricingParams:
	accumulation_mode: str | None
	accumulation_rate: Decimal
	obligation_rate: Decimal
	rounding_unit: Decimal
	include_depreciation: bool

	@classmethod
	def from_values(cls, param_set: dict, price_category: dict) -> "PricingParams":
		"""ASM-015-09: tỷ lệ là Percent ÷ 100; NONE hoặc không tính tích lũy -> None."""
		mode = param_set.get("accumulation_mode")
		if mode in (None, "", "NONE") or not price_category.get("include_accumulation", 1):
			mode = None
		return cls(
			mode,
			Decimal(str(param_set.get("accumulation_rate") or 0)) / 100,
			Decimal(str(param_set.get("obligation_rate") or 0)) / 100,
			Decimal(str(param_set.get("rounding_unit") or 0)),
			bool(price_category.get("include_depreciation", 1)),
		)


@dataclass(frozen=True)
class PriceResult:
	full_cost: Decimal
	accumulation: Decimal
	obligation: Decimal
	calculated_price: Decimal
	rounded_price: Decimal


@dataclass(frozen=True)
class ServiceResult:
	service: str
	department: str
	norm_set: str
	status: str
	message: str
	lines: tuple
	direct_by_component: dict
	direct_by_category: dict
	direct_total: Decimal
	alloc_by_category: dict
	price: PriceResult | None
	volume: Decimal | None = None


DirectServiceExtension = Callable[[ServiceInput], "list[CostLine] | None"]


def direct_line(line: NormLine, rate: LineRate) -> CostLine:
	"""BR-COST-002..007 một dòng trực tiếp (golden `direct_lines`)."""
	from normcore.costing import provisional  # tránh vòng nhập: provisional dùng engine

	if line.excluded:
		reason = line.exclude_reason or ""
		return CostLine(
			LINE_DIRECT,
			line.component,
			_ZERO,
			line.step_id,
			line.line_id,
			line.resource_label,
			_ZERO,
			_ZERO,
			f"Loại trừ: {reason}",
		)
	q = applied_qty(line.hospital_qty, line.authority_qty)
	warning = "; ".join(rate.warnings)
	if rate.billed_separately:
		return CostLine(
			LINE_DIRECT,
			line.component,
			_ZERO,
			line.step_id,
			line.line_id,
			line.resource_label,
			q,
			_ZERO,
			rate.source,
			"; ".join((EXCLUDED_REASON, *rate.warnings)),
		)
	amount = provisional.line_amount(
		line.component, q, rate.rate, line.headcount, line.wastage_rate, rate.reuse_count
	)
	return CostLine(
		LINE_DIRECT,
		line.component,
		amount,
		line.step_id,
		line.line_id,
		line.resource_label,
		q,
		Decimal(rate.rate),
		rate.source,
		warning,
	)


def round_price(calc: Decimal, unit: Decimal) -> Decimal:
	"""BR-COST-014: làm tròn tới bội số của `unit`, HALF_UP."""
	unit = Decimal(unit)
	if unit <= 0:
		raise ValueError("Đơn vị làm tròn phải lớn hơn 0")
	return (Decimal(calc) / unit).quantize(Decimal(1), rounding=ROUND_HALF_UP) * unit


def price_service(direct_total: Decimal, alloc_by_category: Mapping, params: PricingParams) -> PriceResult:
	"""BR-COST-012 (giá thành = trực tiếp + phân bổ), BR-COST-013, BR-COST-014."""
	full = Decimal(direct_total) + sum((Decimal(v) for v in alloc_by_category.values()), _ZERO)
	acc = apply_accumulation(full, params.accumulation_mode, params.accumulation_rate, params.obligation_rate)
	return PriceResult(
		full,
		acc.accumulation,
		acc.obligation,
		acc.calculated_price,
		round_price(acc.calculated_price, params.rounding_unit),
	)


def _sum_by(lines, key) -> dict:
	out: dict = {}
	for ln in lines:
		k = key(ln)
		out[k] = out.get(k, _ZERO) + ln.amount
	return out


def cost_service(
	inp: ServiceInput, params: PricingParams, extension: DirectServiceExtension | None = None
) -> ServiceResult:
	"""Chi phí trực tiếp của một dịch vụ (chưa phân bổ, chưa giá). FR-COST-003, FR-COST-016."""
	ordered = sorted(inp.lines, key=lambda x: x.line_id)
	missing = [
		f"{x.line_id} ({x.resource})" for x in ordered if not x.excluded and inp.rates.get(x.line_id) is None
	]
	if missing:
		return ServiceResult(
			inp.service,
			inp.department,
			inp.norm_set,
			STATUS_ERROR,
			"Dòng thiếu đơn giá: " + ", ".join(missing),
			(),
			{},
			{},
			_ZERO,
			{},
			None,
			inp.volume,
		)
	lines = extension(inp) if extension is not None else None
	if lines is None:
		lines = [direct_line(x, inp.rates.get(x.line_id) or LineRate(_ZERO, "")) for x in ordered]
	lines = tuple(lines)
	by_comp = _sum_by(lines, lambda x: x.component)
	by_cat = _sum_by(lines, lambda x: COMPONENT_CATEGORY[x.component])
	warned = any(_STALE in x.warning or _UNVERIFIED in x.warning for x in lines)
	return ServiceResult(
		inp.service,
		inp.department,
		inp.norm_set,
		STATUS_WARN if warned else STATUS_OK,
		"",
		lines,
		by_comp,
		by_cat,
		sum((x.amount for x in lines), _ZERO),
		{},
		None,
		inp.volume,
	)


def finish_service(
	result: ServiceResult, alloc_lines: Sequence[CostLine], params: PricingParams
) -> ServiceResult:
	"""Gộp dòng "Phân bổ" và tính giá. Dịch vụ "Lỗi" giữ nguyên, không có giá."""
	if result.status == STATUS_ERROR:
		return result
	alloc = _sum_by(alloc_lines, lambda x: x.component)
	price = price_service(result.direct_total, alloc, params)
	return ServiceResult(
		result.service,
		result.department,
		result.norm_set,
		result.status,
		result.message,
		result.lines + tuple(alloc_lines),
		result.direct_by_component,
		result.direct_by_category,
		result.direct_total,
		alloc,
		price,
		result.volume,
	)


COMPONENT_LABEL = {
	"LABOR": "Nhân công",
	"DRUG": "Thuốc",
	"SUPPLY": "Vật tư",
	"EQUIPMENT": "Thiết bị",
	"INFRA": "Hạ tầng",
	"UTILITY": "Tiện ích",
}
COMPONENT_ORDER = ("LABOR", "DRUG", "SUPPLY", "EQUIPMENT", "INFRA", "UTILITY")


def group_explanation(lines: Sequence[CostLine]) -> list[dict]:
	"""Gom dòng trực tiếp theo cấu phần rồi theo bước (SCR-DSK-023). Bước trống = dòng chung ("")."""
	groups = []
	for comp in COMPONENT_ORDER:
		rows = [x for x in lines if x.line_type == LINE_DIRECT and x.component == comp]
		if not rows:
			continue
		steps: dict = {}
		for r in rows:
			steps.setdefault(r.step_id or "", []).append(r)
		groups.append(
			{
				"component": comp,
				"label": COMPONENT_LABEL[comp],
				"total": sum((r.amount for r in rows), _ZERO),
				"steps": [
					{"step_id": sid, "total": sum((r.amount for r in rs), _ZERO), "lines": rs}
					for sid, rs in sorted(steps.items(), key=lambda kv: (kv[0] == "", kv[0]))
				],
			}
		)
	return groups
