"""Đối soát chi phí tài chính (FEAT-017; FR-COST-008, 009; BR-COST-015, BR-COST-016).

Module thuần Python (golden `docs/golden/golden_engine.py:138-145`).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from normcore.costing.allocation import CATEGORIES

_ZERO = Decimal(0)
_Q2 = Decimal("0.01")
DRUG_SUPPLY, DEPRECIATION, MANAGEMENT = "DRUG_SUPPLY", "DEPRECIATION", "MANAGEMENT"


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


def lock_blockers(lines: Iterable) -> list[str]:
	"""Nhãn "K01 · DRUG_SUPPLY" cho dòng vượt ngưỡng chưa có giải trình (FR-COST-009)."""
	return [
		f"{x['cost_center']} · {x['cost_category']}"
		for x in lines
		if x.get("over_tolerance") and not (x.get("explanation") or "").strip()
	]
