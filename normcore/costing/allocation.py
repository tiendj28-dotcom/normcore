"""Phân phối chi phí hai cấp (FEAT-017; FR-COST-004, 005, 014; BR-COST-009, 010, 011, 016).

Module thuần Python, dùng Decimal, làm tròn HALF_UP đúng thứ tự golden
(`docs/golden/golden_engine.py:124-137`): nhân tỷ lệ rồi mới `r2`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from normcore.costing import engine
from normcore.costing.allocation_rules import CLINICAL, LEVEL1, LEVEL2, SUPPORT, driver_shares  # noqa: F401

CATEGORIES = ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT")  # = accounting.ALLOCATABLE
VOLUME_WARNING = "Sản lượng bằng 0 hoặc chưa có: không phân bổ chi phí chung (FR-COST-014)"
CENTER_DRIVERS = ("HEADCOUNT", "AREA", "REVENUE")
_ZERO = Decimal(0)
_Q2 = Decimal("0.01")


def _r2(x: Decimal) -> Decimal:
	return x.quantize(_Q2, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Rule:
	name: str
	level: str
	cost_category: str
	driver: str
	cost_center: str | None = None


@dataclass(frozen=True)
class ServiceDrivers:
	service: str
	department: str
	cost_center: str | None
	labor_min_per_case: Decimal  # Σ applied_qty × headcount, dòng LABOR không loại trừ
	machine_min_per_case: Decimal  # Σ applied_qty, dòng EQUIPMENT không loại trừ


@dataclass(frozen=True)
class AllocationInput:
	accounting: Mapping  # (trung tâm, loại) -> số tiền
	center_types: Mapping  # trung tâm -> "Lâm sàng" / "Hỗ trợ"
	center_drivers: Mapping  # trung tâm -> {"HEADCOUNT", "AREA", "REVENUE"}
	rules: tuple
	include_depreciation: bool


@dataclass(frozen=True)
class Pool:
	cost_center: str
	cost_category: str
	own_amount: Decimal
	received: Decimal
	pool_in: Decimal
	costed: Decimal
	remainder: Decimal
	rule: str | None = None
	driver: str | None = None
	driver_total: Decimal | None = None


@dataclass(frozen=True)
class AllocationOutcome:
	lines: dict = field(default_factory=dict)  # (dịch vụ, khoa) -> list[CostLine "Phân bổ"]
	received: dict = field(default_factory=dict)  # (trung tâm lâm sàng, loại) -> Decimal
	pools: list = field(default_factory=list)
	warnings: list = field(default_factory=list)


def _cat_index(c: str) -> int:
	return CATEGORIES.index(c) if c in CATEGORIES else len(CATEGORIES)


def service_drivers(inp: engine.ServiceInput, cost_center: str | None) -> ServiceDrivers:
	"""Phút trên một ca (golden `labor_min`, `mach_min` trước khi nhân sản lượng)."""
	labor = machine = _ZERO
	for ln in inp.lines:
		if ln.excluded:
			continue
		q = engine.applied_qty(ln.hospital_qty, ln.authority_qty)
		if ln.component == "LABOR":
			labor += q * ln.headcount
		elif ln.component == "EQUIPMENT":
			machine += q
	return ServiceDrivers(inp.service, inp.department, cost_center, labor, machine)


def _volume(result: engine.ServiceResult) -> Decimal:
	return _ZERO if result.volume is None else Decimal(result.volume)


def service_driver_value(drivers: ServiceDrivers, result: engine.ServiceResult, driver: str) -> Decimal:
	"""Tiêu chí năm của dịch vụ (BR-COST-009; golden `drv`)."""
	v = _volume(result)
	if driver == "LABOR_MIN":
		return drivers.labor_min_per_case * v
	if driver == "MACHINE_MIN":
		return drivers.machine_min_per_case * v
	if driver == "VOLUME":
		return v
	if driver == "DIRECT_COST":
		return result.direct_total * v
	return _ZERO


def find_rule(rules: Sequence[Rule], level: str, category: str, center: str | None, warnings=None):
	"""Quy tắc riêng của trung tâm thắng quy tắc chung; trùng mức thì lấy tên nhỏ nhất (ASM-017-09)."""
	for specific in (True, False):
		found = sorted(
			(
				r
				for r in rules
				if r.level == level
				and r.cost_category == category
				and ((r.cost_center == center and center) if specific else not r.cost_center)
			),
			key=lambda r: r.name,
		)
		if found:
			if len(found) > 1 and warnings is not None:
				warnings.append(
					f"Có {len(found)} quy tắc {level} cho {center or 'mọi trung tâm'} · {category}; lấy {found[0].name}"
				)
			return found[0]
	return None


def _center_driver_total(inp, members, center, driver) -> Decimal:
	if driver in CENTER_DRIVERS:
		return Decimal(str((inp.center_drivers.get(center) or {}).get(driver) or 0))
	return sum((service_driver_value(d, r, driver) for d, r in members.get(center, ())), _ZERO)


def level1(inp: AllocationInput, members: Mapping):
	"""BR-COST-010: mỗi trung tâm hỗ trợ chia một lần cho mọi trung tâm lâm sàng, không vòng."""
	received: dict = {}
	warnings: list = []
	clinical = sorted(c for c, t in inp.center_types.items() if t == CLINICAL)
	for support in sorted(c for c, t in inp.center_types.items() if t == SUPPORT):
		for cat in CATEGORIES:
			amount = Decimal(inp.accounting.get((support, cat)) or 0)
			if amount == 0:
				continue
			rule = find_rule(inp.rules, LEVEL1, cat, support, warnings)
			if rule is None:
				warnings.append(f"Thiếu quy tắc phân bổ cấp 1 cho {support} · {cat}: không chia")
				continue
			values = {k: _center_driver_total(inp, members, k, rule.driver) for k in clinical}
			if not clinical or sum(values.values(), _ZERO) == 0:
				warnings.append(
					f"Tổng tiêu chí {rule.driver} của các trung tâm lâm sàng bằng 0 ({support} · {cat}): không chia"
				)
				continue
			for k, share in driver_shares(values).items():
				received[(k, cat)] = received.get((k, cat), _ZERO) + _r2(amount * share)
	return received, warnings


def level2(inp: AllocationInput, members: Mapping, received: Mapping):
	"""BR-COST-011: phần còn lại của (trung tâm lâm sàng, loại) chia theo tiêu chí, theo ca."""
	lines: dict = {}
	pools: list = []
	warnings: list = []
	for center in sorted(members):
		rows = members[center]
		if not rows:
			continue
		cats = {c for (k, c), v in inp.accounting.items() if k == center and v}
		cats |= {c for (k, c), v in received.items() if k == center and v}
		for _, r in rows:
			cats |= {c for c, v in r.direct_by_category.items() if v}
		if not inp.include_depreciation:
			cats.discard("DEPRECIATION")  # BR-COST-016
		for cat in sorted(cats, key=_cat_index):
			own = Decimal(inp.accounting.get((center, cat)) or 0)
			recv = Decimal(received.get((center, cat)) or 0)
			pool_in = own + recv
			costed = sum((r.direct_by_category.get(cat, _ZERO) * _volume(r) for _, r in rows), _ZERO)
			remainder = max(pool_in - costed, _ZERO)
			rule = find_rule(inp.rules, LEVEL2, cat, center, warnings)
			total = None
			if rule is None:
				if remainder > 0:
					warnings.append(f"Thiếu quy tắc phân bổ cấp 2 cho {center} · {cat}: không chia")
			else:
				values = [service_driver_value(d, r, rule.driver) for d, r in rows]
				total = sum(values, _ZERO)
				if total == 0 and remainder > 0:
					warnings.append(f"Tổng tiêu chí {rule.driver} của {center} · {cat} bằng 0: không chia")
				elif total != 0:
					for (d, r), dv in zip(rows, values, strict=True):
						v = _volume(r)
						if v <= 0:
							continue
						lines.setdefault((r.service, r.department), []).append(
							engine.CostLine(
								engine.LINE_ALLOC,
								cat,
								_r2(remainder * dv / total / v),
								rate_source=f"Cấp 2 · {rule.driver}",
								allocation_rule=rule.name,
								driver_value=dv,
								driver_total=total,
								pool_amount=remainder,
							)
						)
			pools.append(
				Pool(
					center, cat, own, recv, pool_in, costed, remainder,
					rule.name if rule else None, rule.driver if rule else None, total,
				)
			)
	return lines, pools, warnings


def allocate(results: Sequence[engine.ServiceResult], drivers: Mapping, inp: AllocationInput):
	"""Cấp 1 rồi cấp 2. Bỏ dịch vụ "Lỗi" (ASM-017-04). Thứ tự tất định (NFR-REL-002)."""
	members: dict = {}
	warnings: list = []
	for r in sorted(results, key=lambda x: (x.service, x.department)):
		if r.status == engine.STATUS_ERROR:
			continue
		d = drivers.get((r.service, r.department))
		if d is None or not d.cost_center:
			warnings.append(f"Dịch vụ {r.service} · {r.department} chưa có trung tâm chi phí: không phân bổ")
			continue
		members.setdefault(d.cost_center, []).append((d, r))
	received, w1 = level1(inp, members)
	lines, pools, w2 = level2(inp, members, received)
	out_w = []
	for w in [*warnings, *w1, *w2]:
		if w not in out_w:
			out_w.append(w)
	return AllocationOutcome(lines, received, pools, out_w)


def mark_volume(result: engine.ServiceResult) -> engine.ServiceResult:
	"""FR-COST-014: sản lượng 0 hoặc thiếu thì cảnh báo, giá vẫn tính (ASM-017-02)."""
	if result.status == engine.STATUS_ERROR or (result.volume is not None and result.volume > 0):
		return result
	msg = f"{result.message}; {VOLUME_WARNING}" if result.message else VOLUME_WARNING
	return engine.ServiceResult(
		result.service, result.department, result.norm_set, result.status, msg, result.lines,
		result.direct_by_component, result.direct_by_category, result.direct_total,
		result.alloc_by_category, result.price, result.volume,
	)
