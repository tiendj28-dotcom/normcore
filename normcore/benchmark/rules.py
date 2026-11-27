"""Gợi ý điều chỉnh theo quy tắc BR-ADJ-001..007 (FEAT-028): logic thuần, không phụ thuộc framework, không dùng AI.

FR-ADJ-005, ADR-008. Giả định ASM-028-05..07 (docs/decisions/assumptions/FEAT-028.md).
Tác động ước tính chỉ gọi lại hàm bộ máy tính giá (engine.direct_line, engine.price_service,
resources.machine_hourly_rate); phân bổ cấp 2 giữ nguyên (ASM-028-06).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal

from normcore.benchmark import stats
from normcore.costing import engine, resources

RULE_CODES = tuple(f"BR-ADJ-00{i}" for i in range(1, 8))
DOWN, UP = "Giảm", "Tăng"
UTILIZATION_TARGET = Decimal("0.5")  # BR-ADJ-001
TIME_STUDY_MARGIN = Decimal("0.15")  # BR-ADJ-002

TEMPLATES = {
	"BR-ADJ-001": "Hệ số sử dụng thiết bị {target} đang {current}, thấp hơn mức {suggested}: xem lại kế hoạch khai thác hoặc số máy.",
	"BR-ADJ-002": "Thời gian định mức của dòng {target} ({current}) vượt trung vị bấm giờ quá 15%: đề xuất {suggested}.",
	"BR-ADJ-003": "Dòng {target}: có mặt hàng tương đương rẻ hơn ({suggested}); đổi mặt hàng cần sửa quy trình.",
	"BR-ADJ-004": "Hao hụt của dòng {target} ({current}) vượt trần cho phép: đề xuất {suggested}.",
	"BR-ADJ-005": "Tỷ lệ tích lũy của bộ tham số {target} ({current}): đề xuất {suggested}.",
	"BR-ADJ-006": "Dịch vụ thiếu cấu phần {target} ({current}): đề xuất {suggested}.",
	"BR-ADJ-007": "Dữ liệu {target} đã cũ ({current}): đề xuất {suggested}.",
}


@dataclass(frozen=True)
class Suggestion:
	rule_code: str
	direction: str
	component: str
	target_ref: str
	current_value: str
	suggested_value: str
	estimated_impact: Decimal | None
	requires_procedure_change: bool
	text: str


@dataclass(frozen=True)
class ServiceFacts:
	direct_total: Decimal
	alloc_by_category: dict
	pricing: engine.PricingParams
	norm_lines: tuple
	line_rates: dict  # line_id -> engine.LineRate (đơn giá đã dùng trong lần tính)
	costing_date: date | str | None = None
	price_valid_months: int = 24
	equipment: dict = field(
		default_factory=dict
	)  # code -> {annual_cost, planned_hours, utilization, maintenance}
	time_study: dict = field(default_factory=dict)  # (step_id, resource) -> trung vị phút
	wastage_cap: Decimal = Decimal(0)
	equivalents: dict = field(default_factory=dict)  # line_id -> [(item, LineRate)] đang dùng
	stale_prices: dict = field(default_factory=dict)  # line_id -> {item, valid_from}
	latest_parameter_set: str | None = None
	parameter_set: str = ""


def _fmt(x, places=2) -> str:
	"""Số kiểu vi-VN: dấu phẩy thập phân, bỏ số 0 thừa."""
	d = Decimal(str(x)).quantize(Decimal(1).scaleb(-places)).normalize()
	text = format(d, "f")
	return text.replace(".", ",")


def _text(rule_code, target, current, suggested) -> str:
	return TEMPLATES[rule_code].format(target=target, current=current, suggested=suggested)


def _price(facts, direct_total, pricing=None):
	return engine.price_service(
		direct_total, facts.alloc_by_category, pricing or facts.pricing
	).calculated_price


def impact(facts: ServiceFacts, delta_direct, pricing=None) -> Decimal:
	"""ASM-028-06: giá tính toán với chi phí trực tiếp đổi `delta_direct` - giá hiện tại."""
	base = _price(facts, facts.direct_total)
	return _price(facts, facts.direct_total + Decimal(delta_direct), pricing) - base


def _amount(line, rate) -> Decimal:
	return engine.direct_line(line, rate).amount


def _make(rule, direction, component, target, cur, sug, impact_value, proc=False):
	return Suggestion(
		rule, direction, component, target, cur, sug, impact_value, proc, _text(rule, target, cur, sug)
	)


def rule_001_utilization(facts):
	out = []
	for code in sorted(
		{ln.resource for ln in facts.norm_lines if ln.component == "EQUIPMENT" and not ln.excluded}
	):
		eq = facts.equipment.get(code)
		if not eq or Decimal(str(eq["utilization"])) >= UTILIZATION_TARGET:
			continue
		u = Decimal(str(eq["utilization"]))
		old = resources.machine_hourly_rate(eq["annual_cost"], eq["planned_hours"], u)
		new = resources.machine_hourly_rate(eq["annual_cost"], eq["planned_hours"], UTILIZATION_TARGET)
		delta = Decimal(0)
		for ln in facts.norm_lines:
			if ln.component == "EQUIPMENT" and ln.resource == code and not ln.excluded:
				cur = facts.line_rates[ln.line_id]
				delta += _amount(ln, replace(cur, rate=new)) - _amount(ln, replace(cur, rate=old))
		out.append(
			_make(
				"BR-ADJ-001", DOWN, "EQUIPMENT", code, _fmt(u), _fmt(UTILIZATION_TARGET), impact(facts, delta)
			)
		)
	return out


def rule_002_time_study(facts):
	out = []
	for ln in facts.norm_lines:
		med = facts.time_study.get((ln.step_id, ln.resource))
		if ln.component != "LABOR" or ln.excluded or med is None:
			continue
		med = Decimal(str(med))
		# số phút đang áp theo BR-COST-007 (min với định mức ban hành); trần định mức Bộ được giữ khi đề xuất
		applied = engine.applied_qty(ln.hospital_qty, ln.authority_qty)
		if applied <= med * (1 + TIME_STUDY_MARGIN):
			continue
		rate = facts.line_rates[ln.line_id]
		new_applied = engine.applied_qty(med, ln.authority_qty)
		delta = _amount(replace(ln, hospital_qty=med), rate) - _amount(ln, rate)
		out.append(
			_make(
				"BR-ADJ-002",
				DOWN,
				"LABOR",
				ln.line_id,
				f"{_fmt(applied)} phút",
				f"{_fmt(new_applied)} phút",
				impact(facts, delta),
			)
		)
	return out


def rule_003_equivalent(facts):
	out = []
	for ln in facts.norm_lines:
		if ln.component not in ("DRUG", "SUPPLY") or ln.excluded:
			continue
		cur = facts.line_rates.get(ln.line_id)
		cheaper = [(i, r) for i, r in facts.equivalents.get(ln.line_id, []) if cur and r.rate < cur.rate]
		if not cheaper:
			continue
		item, rate = min(cheaper, key=lambda x: (x[1].rate, x[0]))
		delta = _amount(ln, rate) - _amount(ln, cur)
		out.append(
			_make(
				"BR-ADJ-003",
				DOWN,
				ln.component,
				ln.line_id,
				ln.resource,
				item,
				impact(facts, delta),
				proc=True,
			)
		)
	return out


def rule_004_wastage(facts):
	out = []
	cap = Decimal(str(facts.wastage_cap))
	for ln in facts.norm_lines:
		if ln.component not in ("DRUG", "SUPPLY") or ln.excluded or ln.wastage_rate <= cap:
			continue
		rate = facts.line_rates[ln.line_id]
		delta = _amount(replace(ln, wastage_rate=cap), rate) - _amount(ln, rate)
		out.append(
			_make(
				"BR-ADJ-004",
				DOWN,
				ln.component,
				ln.line_id,
				f"{_fmt(ln.wastage_rate * 100)}%",
				f"{_fmt(cap * 100)}%",
				impact(facts, delta),
			)
		)
	return out


def rule_005_accumulation(facts, direction):
	p = facts.pricing
	if p.accumulation_mode is None or p.accumulation_rate == 0:
		return []
	step = Decimal("0.01")
	new_rate = p.accumulation_rate - step if direction == DOWN else p.accumulation_rate + step
	if new_rate < 0:
		return []
	delta = impact(facts, 0, replace(p, accumulation_rate=new_rate))
	return [
		_make(
			"BR-ADJ-005",
			direction,
			"PARAMETER",
			facts.parameter_set,
			f"{_fmt(p.accumulation_rate * 100)}%",
			f"{_fmt(new_rate * 100)}%",
			delta,
		)
	]


def rule_006_missing(facts):
	out = []
	comps = {ln.component for ln in facts.norm_lines if not ln.excluded}
	for code in sorted(
		{ln.resource for ln in facts.norm_lines if ln.component == "EQUIPMENT" and not ln.excluded}
	):
		eq = facts.equipment.get(code)
		if eq and Decimal(str(eq.get("maintenance") or 0)) == 0:
			out.append(
				_make(
					"BR-ADJ-006",
					UP,
					"EQUIPMENT",
					code,
					"Chưa có chi phí bảo trì",
					"Bổ sung chi phí bảo trì",
					None,
				)
			)
	for comp, label in (("INFRA", "hạ tầng"), ("UTILITY", "tiện ích")):
		if comp not in comps:
			out.append(_make("BR-ADJ-006", UP, comp, comp, "Chưa có", f"Bổ sung dòng {label}", None))
	return out


def _months_before(costing_date, months):
	return stats.window_start(costing_date, months)


def rule_007_stale(facts):
	out = []
	if facts.costing_date is not None:
		limit = _months_before(facts.costing_date, facts.price_valid_months)
		for line_id in sorted(facts.stale_prices):
			info = facts.stale_prices[line_id]
			valid_from = stats._d(info["valid_from"])
			if valid_from < limit:
				out.append(
					_make(
						"BR-ADJ-007",
						UP,
						"ITEM",
						info["item"],
						valid_from.isoformat(),
						"Cập nhật đơn giá",
						None,
					)
				)
	if facts.latest_parameter_set and facts.latest_parameter_set != facts.parameter_set:
		out.append(
			_make(
				"BR-ADJ-007",
				UP,
				"PARAMETER",
				facts.parameter_set,
				facts.parameter_set,
				facts.latest_parameter_set,
				None,
			)
		)
	return out


def _sort_key(s):
	if s.estimated_impact is None:
		return (1, Decimal(0), s.rule_code, s.target_ref)
	return (0, -abs(s.estimated_impact), s.rule_code, s.target_ref)


def generate(facts: ServiceFacts, deviation_pct, tolerance) -> list:
	"""FR-ADJ-005: giá cao hơn trung vị vượt ngưỡng -> quy tắc Giảm; thấp hơn -> quy tắc Tăng (ASM-028-05)."""
	if not stats.exceeds(deviation_pct, tolerance):
		return []
	if Decimal(str(deviation_pct)) > 0:
		found = [
			*rule_001_utilization(facts),
			*rule_002_time_study(facts),
			*rule_003_equivalent(facts),
			*rule_004_wastage(facts),
			*rule_005_accumulation(facts, DOWN),
		]
	else:
		found = [*rule_006_missing(facts), *rule_007_stale(facts), *rule_005_accumulation(facts, UP)]
	found = [s for s in found if s.estimated_impact != 0]
	return sorted(found, key=_sort_key)
