"""Golden FEAT-018: tái lập từ ảnh chụp và so sánh hai lần tính so với docs/golden/golden_engine.py."""

import json
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing import compare, snapshot
from normcore.tests.golden import test_allocation_golden as ta
from normcore.tests.golden import test_costing_golden as tg

DIRECT = {
	"LABOR": "direct_labor",
	"DRUG": "direct_drug",
	"SUPPLY": "direct_supply",
	"EQUIPMENT": "direct_equipment",
	"INFRA": "direct_infra",
	"UTILITY": "direct_utility",
}
ALLOC = {
	"LABOR": "alloc_labor",
	"DRUG_SUPPLY": "alloc_drug_supply",
	"DEPRECIATION": "alloc_depreciation",
	"UTILITY": "alloc_utility",
	"MANAGEMENT": "alloc_management",
}


def _flat(results):
	rows = []
	for r in results:
		row = {"technical_service": r.service, "department": r.department, "calc_status": r.status}
		for comp, f in DIRECT.items():
			row[f] = r.direct_by_component.get(comp, D(0))
		for cat, f in ALLOC.items():
			row[f] = r.alloc_by_category.get(cat, D(0))
		p = r.price
		row.update(
			full_cost=p.full_cost,
			accumulation=p.accumulation,
			obligation=p.obligation,
			calculated_price=p.calculated_price,
			rounded_price=p.rounded_price,
		)
		rows.append(row)
	return rows


def _snap(include_depr=True):
	alloc = {
		"input": ta._inputs(include_depr),
		"dept_center": {"K01": "K01"},
		"tolerance": repr(float(g.PARAM["recon_tolerance"])),
	}
	inputs = [tg._input(s, include_depr) for s in g.NORMS]
	return snapshot.build(inputs, tg._params(include_depr), allocation=alloc, meta={"run": "CR"})


class TestSnapshotCompareGolden(unittest.TestCase):
	def test_TC_COST_09_recompute_tu_anh_chup_vang(self):
		g_res, g_recon, _ = g.run()
		blob, h = snapshot.pack(_snap())
		again, h2 = snapshot.pack(_snap())
		self.assertEqual((blob, h), (again, h2))
		out = snapshot.recompute(snapshot.unpack(blob, h))
		by = {r.service: r for r in out.results}
		for s in g.NORMS:
			with self.subTest(service=s):
				self.assertEqual(by[s].price.full_cost, g_res[s]["full"])
				self.assertEqual(by[s].price.rounded_price, g_res[s]["rounded"])
		self.assertEqual(by["DV-TEST-A"].price.full_cost, D("287745.46"))
		self.assertEqual(by["DV-TEST-B"].price.full_cost, D("88169.70"))
		expected = [x for x in g_recon if x[0] != "MANAGEMENT"]
		self.assertEqual(len(out.recon_rows), 4)
		for r, (cat, costed, pool_in, _rem, pct, over) in zip(out.recon_rows, expected, strict=True):
			self.assertEqual(
				(r.cost_category, r.costed, r.accounting, r.variance_pct, r.over_tolerance),
				(cat, costed, pool_in, pct, over),
			)

	def test_TC_COST_09_doi_dau_vao_sau_khi_chup_khong_anh_huong(self):
		"""Ảnh chụp là bản sao tại thời điểm chụp: đổi đầu vào sống (g.ITEM, g.PARAM) không đổi kết quả."""
		snap = json.loads(snapshot.dumps(_snap()))
		before = {r.service: r.price.full_cost for r in snapshot.recompute(snap).results}
		old = g.PARAM["rounding_unit"]
		try:
			g.PARAM["rounding_unit"] = D("1000")
			after = {r.service: r.price.full_cost for r in snapshot.recompute(snap).results}
		finally:
			g.PARAM["rounding_unit"] = old
		self.assertEqual(before, after)

	def test_TC_COST_18_chenh_lech_V1_theo_cau_phan(self):
		base = snapshot.recompute(_snap(True)).results
		v1 = snapshot.recompute(_snap(False)).results
		g_base, g_v1 = g.run()[0], g.run(False)[0]
		out = {d.service: d for d in compare.compare(_flat(base), _flat(v1))}
		a = out["DV-TEST-A"]
		self.assertEqual(a.full_cost.base, g_base["DV-TEST-A"]["full"])
		self.assertEqual(a.full_cost.other, g_v1["DV-TEST-A"]["full"])
		self.assertEqual(a.full_cost.diff, g_v1["DV-TEST-A"]["full"] - g_base["DV-TEST-A"]["full"])
		self.assertEqual(a.full_cost.diff, D("-63636.36"))
		c = {x.field: x.diff for x in a.components}
		self.assertEqual(c["direct_equipment"], D("-47348.48"))
		self.assertEqual(c["direct_infra"], D("-12500.00"))
		self.assertEqual(c["alloc_depreciation"], D("-3787.88"))
		for f in ("direct_labor", "direct_drug", "direct_supply", "direct_utility", "alloc_labor", "alloc_drug_supply", "alloc_utility", "alloc_management"):
			self.assertEqual(c[f], D("0.00"), f)
		self.assertEqual(sum(x.diff for x in a.components if x.group in ("Trực tiếp", "Phân bổ")), a.full_cost.diff)
		b = out["DV-TEST-B"]
		self.assertEqual(b.full_cost.diff, D("0.00"))
		self.assertEqual(b.full_cost.base, D("88169.70"))
		self.assertTrue(compare.changed(a))
		self.assertFalse(compare.changed(b))
		self.assertEqual(compare.summary(list(out.values()))["total_diff"], D("-63636.36"))
