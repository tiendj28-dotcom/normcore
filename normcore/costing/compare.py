"""So sánh hai lần tính giá (FEAT-018; FR-COST-013). Hàm thuần Python.

Đầu vào là bản ghi phẳng của NC Service Cost (dict cùng tên trường với DocType). Chênh lệch = lần so sánh
- lần gốc. Giá thành = trực tiếp + phân bổ (BR-COST-012) nên Σ chênh lệch hai nhóm đó = chênh giá thành.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

DIRECT, ALLOC, PRICE = "Trực tiếp", "Phân bổ", "Giá"
STATUS_ERROR = "Lỗi"
COMPONENTS = (
	(DIRECT, "direct_labor", "Nhân công"),
	(DIRECT, "direct_drug", "Thuốc"),
	(DIRECT, "direct_supply", "Vật tư"),
	(DIRECT, "direct_equipment", "Thiết bị"),
	(DIRECT, "direct_infra", "Hạ tầng"),
	(DIRECT, "direct_utility", "Tiện ích"),
	(DIRECT, "eqa_cost", "Ngoại kiểm"),
	(ALLOC, "alloc_labor", "Phân bổ nhân công"),
	(ALLOC, "alloc_drug_supply", "Phân bổ thuốc, vật tư"),
	(ALLOC, "alloc_depreciation", "Phân bổ khấu hao"),
	(ALLOC, "alloc_utility", "Phân bổ tiện ích"),
	(ALLOC, "alloc_management", "Phân bổ quản lý"),
	(PRICE, "accumulation", "Tích lũy"),
	(PRICE, "obligation", "Nghĩa vụ tài chính"),
	(PRICE, "calculated_price", "Giá tính toán"),
	(PRICE, "rounded_price", "Giá làm tròn"),
)
OPTIONAL = ("eqa_cost",)  # chỉ hiện khi có số ở ít nhất một bên (FEAT-036)
_Q2 = Decimal("0.01")

META_LABELS = (
	("fiscal_year", "Năm tài chính"),
	("costing_date", "Ngày tính giá"),
	("parameter_set", "Bộ tham số"),
	("accounting_import", "Lần nhập kế toán"),
	("price_category", "Loại giá"),
	("scope_departments", "Phạm vi khoa"),
	("scope_services", "Phạm vi dịch vụ"),
	("volume_scenario", "Kịch bản sản lượng"),
	("compliance_allocation_mode", "Cách phân bổ chi phí tuân thủ"),
)


def _r2(x) -> Decimal | None:
	return None if x is None else Decimal(str(x)).quantize(_Q2, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Delta:
	base: Decimal | None
	other: Decimal | None
	diff: Decimal | None
	pct: Decimal | None


@dataclass(frozen=True)
class ComponentDelta:
	group: str
	field: str
	label: str
	base: Decimal | None
	other: Decimal | None
	diff: Decimal | None
	pct: Decimal | None


@dataclass(frozen=True)
class ServiceDiff:
	service: str
	department: str
	presence: str  # "both" / "base_only" / "other_only"
	base_status: str | None
	other_status: str | None
	full_cost: Delta
	components: tuple


def _delta(base, other) -> Delta:
	base, other = _r2(base), _r2(other)
	if base is None or other is None:
		return Delta(base, other, None, None)
	diff = other - base
	pct = _r2(diff / base * 100) if base != 0 else None
	return Delta(base, other, diff, pct)


def _value(row, field):
	if row is None or row.get("calc_status") == STATUS_ERROR:
		return None
	return row.get(field)


def compare(base_rows, other_rows, fields=COMPONENTS) -> list[ServiceDiff]:
	"""Ghép theo (dịch vụ, khoa), sắp theo khóa."""
	key = lambda r: (r["technical_service"], r["department"])  # noqa: E731
	base = {key(r): r for r in base_rows}
	other = {key(r): r for r in other_rows}
	out = []
	for k in sorted(set(base) | set(other)):
		b, o = base.get(k), other.get(k)
		presence = "both" if b is not None and o is not None else ("base_only" if o is None else "other_only")
		comps = []
		for group, field, label in fields:
			if field in OPTIONAL and _value(b, field) is None and _value(o, field) is None:
				continue
			d = _delta(_value(b, field), _value(o, field))
			comps.append(ComponentDelta(group, field, label, d.base, d.other, d.diff, d.pct))
		out.append(
			ServiceDiff(
				k[0],
				k[1],
				presence,
				b.get("calc_status") if b else None,
				o.get("calc_status") if o else None,
				_delta(_value(b, "full_cost"), _value(o, "full_cost")),
				tuple(comps),
			)
		)
	return out


def changed(d: ServiceDiff) -> bool:
	return (
		d.presence != "both"
		or d.base_status != d.other_status
		or bool(d.full_cost.diff)
		or any(c.diff for c in d.components)
	)


def summary(diffs) -> dict:
	return {
		"services": len(diffs),
		"changed": sum(1 for d in diffs if changed(d)),
		"base_only": sum(1 for d in diffs if d.presence == "base_only"),
		"other_only": sum(1 for d in diffs if d.presence == "other_only"),
		"total_diff": sum((d.full_cost.diff for d in diffs if d.full_cost.diff is not None), Decimal("0.00")),
	}


def _text(v) -> str:
	if isinstance(v, (list, tuple, set)):
		return ", ".join(sorted(str(x) for x in v))
	return "" if v is None else str(v)


def input_changes(base_meta, other_meta) -> list[tuple[str, str, str]]:
	"""Khác nhau giữa đầu vào hai lần tính: [(nhãn, gốc, so sánh)]."""
	out = []
	for field, label in META_LABELS:
		a, b = _text(base_meta.get(field)), _text(other_meta.get(field))
		if a != b:
			out.append((label, a, b))
	return out
