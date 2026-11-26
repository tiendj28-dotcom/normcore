"""Đối soát chi phí tài chính (FEAT-017; FR-COST-008, 009; BR-COST-015, BR-COST-016).

Module thuần Python (golden `docs/golden/golden_engine.py:138-145`).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from normcore.costing import cls, engine
from normcore.costing.allocation import CATEGORIES

_ZERO = Decimal(0)
_Q2 = Decimal("0.01")
DRUG_SUPPLY, DEPRECIATION, MANAGEMENT = "DRUG_SUPPLY", "DEPRECIATION", "MANAGEMENT"
FINANCIAL, MATERIAL, VOLUME = "Tài chính", "Vật chất", "Sản lượng"
RECONCILED, UNRECONCILED = "Đã đối soát", "Chưa đối soát"
_MATERIAL_COMPONENTS = ("DRUG", "SUPPLY")


@dataclass(frozen=True)
class ReconRow:
	cost_center: str
	cost_category: str
	costed: Decimal | None
	accounting: Decimal | None
	remainder: Decimal | None
	variance: Decimal | None
	variance_pct: Decimal | None
	over_tolerance: bool | None
	skipped: bool = False  # BR-COST-016


def reconcile(pools: Sequence, tolerance, include_depreciation: bool, depr_centers: Iterable = ()):
	"""`tolerance`: Percent (10 = 10%). Bỏ MANAGEMENT (BR-COST-015)."""
	tol = Decimal(str(tolerance or 0))
	rows = []
	for p in pools:
		if p.cost_category == MANAGEMENT:
			continue
		if p.cost_category == DEPRECIATION and not include_depreciation:
			continue
		costed, acc = Decimal(p.costed), Decimal(p.pool_in)
		if costed == 0 and acc == 0:
			continue
		variance = costed - acc
		if acc != 0:
			pct = (variance / acc * 100).quantize(_Q2, rounding=ROUND_HALF_UP)
			over = pct > tol or (p.cost_category == DRUG_SUPPLY and pct < -tol)
		else:
			pct, over = None, costed > 0
		rows.append(
			ReconRow(p.cost_center, p.cost_category, costed, acc, Decimal(p.remainder), variance, pct, over)
		)
	if not include_depreciation:
		rows += [
			ReconRow(c, DEPRECIATION, None, None, None, None, None, None, True)
			for c in sorted(set(depr_centers))
		]
	idx = {c: i for i, c in enumerate(CATEGORIES)}
	return sorted(rows, key=lambda r: (r.cost_center, idx.get(r.cost_category, len(idx))))


@dataclass(frozen=True)
class PhysRow:
	"""Một dòng đối soát Vật chất hoặc Sản lượng (FEAT-037; BR-CLS-014, 015)."""

	recon_type: str
	department: str
	item: str | None
	service: str | None
	calculated: Decimal | None
	actual: Decimal | None
	variance_pct: Decimal | None
	over_tolerance: bool
	status: str = RECONCILED
	note: str = ""


def _pct(numerator, denominator) -> Decimal:
	return (Decimal(numerator) / Decimal(denominator) * 100).quantize(_Q2, rounding=ROUND_HALF_UP)


def material_quantities(inputs: Iterable) -> dict[tuple[str, str], Decimal]:
	"""BR-CLS-014: lượng tính được (đơn vị định mức) theo (khoa, mặt hàng); không làm tròn."""
	out: dict[tuple[str, str], Decimal] = {}

	def add(key, qty):
		out[key] = out.get(key, _ZERO) + qty

	for inp in inputs:
		c = inp.paraclinical
		if c is None:
			continue
		for s in c.systems:
			qbn = Decimal(s.qbn)
			qnk, qcal, qrerun, qeqa, h, _est = cls.aux_counts(s, c.imaging)
			k, _total = cls.k_factor(qbn, qnk, qcal, qrerun, qeqa, h)
			days = cls._days(s)
			for ln in s.lines:
				n = ln.norm
				if n.excluded or n.component not in _MATERIAL_COMPONENTS or not n.resource:
					continue
				q = engine.applied_qty(n.hospital_qty, n.authority_qty)
				w = 1 + Decimal(n.wastage_rate)
				if ln.cost_level == cls.RESULT:
					qty = q * (k if ln.apply_k else 1) * qbn
				elif ln.cost_level == cls.TUBE and s.tests_per_tube:
					qty = q * w * qbn / Decimal(s.tests_per_tube)
				elif ln.cost_level == cls.BATCH and s.batch:
					qty = q * w * qbn / Decimal(s.batch)
				elif ln.cost_level == cls.DAY and days is not None:
					qty = q * w * Decimal(days)
				elif ln.cost_level == cls.PERIOD:
					qty = q * w
				else:
					continue
				add((inp.department, n.resource), qty)
			for i in s.iqc:  # BR-CLS-006
				if days is None or not i.shared_params:
					continue
				qty = (
					Decimal(i.qty_per_run)
					* Decimal(i.levels)
					* Decimal(i.runs_per_day)
					* Decimal(days)
					/ Decimal(i.shared_params)
				)
				add((inp.department, i.item), qty)
	return out


def material_rows(
	calc: Mapping,
	issued: Mapping,
	units: Mapping,
	item_meta: Mapping,
	departments_with_data: Iterable,
	tolerance,
) -> list[PhysRow]:
	"""BR-CLS-014, FR-COST-026..029. `issued` tính theo đơn vị mua; `units` = số đơn vị định mức / đơn vị mua."""
	tol = Decimal(str(tolerance))
	has_data = set(departments_with_data)
	rows: list[PhysRow] = []
	for dept in sorted({d for d, _ in calc}):
		if dept not in has_data:  # FR-COST-029, A-08
			rows.append(
				PhysRow(
					MATERIAL,
					dept,
					None,
					None,
					None,
					None,
					None,
					False,
					UNRECONCILED,
					"Khoa chưa có số liệu xuất kho",
				)
			)
	for (dept, item), qty in sorted(calc.items()):
		if dept not in has_data or qty <= 0:
			continue
		unit = units.get(item)
		need_unit = bool((item_meta.get(item) or {}).get("norm_required"))
		raw = issued.get((dept, item))
		if raw is None or Decimal(raw) == 0:
			rows.append(
				PhysRow(
					MATERIAL, dept, item, None, qty, None, None, False, UNRECONCILED, "Không có dòng xuất kho"
				)
			)
			continue
		if need_unit and not unit:
			rows.append(
				PhysRow(
					MATERIAL,
					dept,
					item,
					None,
					qty,
					None,
					None,
					False,
					UNRECONCILED,
					"Thiếu số đơn vị định mức",
				)
			)
			continue
		actual = Decimal(raw) * Decimal(unit or 1)
		pct = _pct(actual - qty, actual)
		rows.append(PhysRow(MATERIAL, dept, item, None, qty, actual, pct, abs(pct) > tol))
	rows.sort(key=lambda r: (r.department, r.item is not None, r.item or ""))
	return rows


def volume_rows(results: Mapping, his: Mapping, tolerance) -> list[PhysRow]:
	"""BR-CLS-015: (số kết quả trả - sản lượng HIS) / HIS x 100; cảnh báo, không chặn khóa."""
	tol = Decimal(str(tolerance))
	rows = []
	for (service, dept), res in sorted(results.items()):
		h = his.get((service, dept))
		if h is None or Decimal(h) == 0:
			rows.append(
				PhysRow(
					VOLUME,
					dept,
					None,
					service,
					Decimal(res),
					h,
					None,
					True,
					RECONCILED,
					"Thiếu sản lượng HIS",
				)
			)
			continue
		pct = _pct(Decimal(res) - Decimal(h), h)
		rows.append(PhysRow(VOLUME, dept, None, service, Decimal(res), Decimal(h), pct, abs(pct) > tol))
	return rows


def needs_explanation(line: Mapping) -> bool:
	"""Dòng chặn khóa khi chưa có giải trình (FR-COST-009, 027, 029). Dòng Sản lượng không chặn (FR-COST-028)."""
	if (line.get("explanation") or "").strip():
		return False
	kind = line.get("recon_type") or FINANCIAL
	if kind == VOLUME:
		return False
	if kind == MATERIAL:
		return bool(line.get("over_tolerance")) or line.get("recon_status") == UNRECONCILED
	return bool(line.get("over_tolerance"))


def _label(x: Mapping) -> str:
	if (x.get("recon_type") or FINANCIAL) == MATERIAL:
		return f"{MATERIAL} · {x.get('department')} · {x.get('item') or UNRECONCILED}"
	return f"{x['cost_center']} · {x['cost_category']}"


def lock_blockers(lines: Iterable) -> list[str]:
	"""Nhãn dòng đối soát vượt ngưỡng hoặc chưa đối soát mà chưa có giải trình."""
	return [_label(x) for x in lines if needs_explanation(x)]


def depreciation_centers(accounting, pools) -> list[str]:
	"""Trung tâm có số kế toán DEPRECIATION khác 0 và nằm trong `pools`, sắp theo tên."""
	centers = {p.cost_center for p in pools}
	return sorted(c for (c, cat), v in accounting.items() if cat == DEPRECIATION and v and c in centers)
