"""Golden FEAT-017: phân bổ hai cấp và đối soát so với docs/golden/golden_engine.py (không chép số)."""

import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing import allocation, engine, reconcile
from normcore.costing.allocation_rules import LEVEL1, LEVEL2
from normcore.tests.golden import test_costing_golden as tg


def _inputs(include_depr=True):
	acc = {(c, k): v for c, d in g.ACCOUNTING.items() for k, v in d.items()}
	rules = [allocation.Rule("R1-" + k, LEVEL1, k, g.L1_DRIVER, "HC") for k in g.ACCOUNTING["HC"]]
	rules += [allocation.Rule("R2-" + k, LEVEL2, k, d, None) for k, d in g.L2_DRIVER.items()]
	return allocation.AllocationInput(
		acc,
		{"K01": "Lâm sàng", "K02": "Lâm sàng", "HC": "Hỗ trợ"},
		{k: {"HEADCOUNT": v} for k, v in g.HEADCOUNT.items()},
		tuple(rules),
		include_depr,
	)


def _run(include_depr=True):
	params = tg._params(include_depr)
	results, drivers = [], {}
	for s in g.NORMS:
		inp = tg._input(s, include_depr)
		drivers[(s, "K01")] = allocation.service_drivers(inp, "K01")
		results.append(allocation.mark_volume(engine.cost_service(inp, params)))
	out = allocation.allocate(results, drivers, _inputs(include_depr))
	finished = {
		r.service: engine.finish_service(r, out.lines.get((r.service, r.department), []), params)
		for r in results
	}
	return out, finished


def _alloc(out, svc):
	return {x.component: x.amount for x in out.lines.get((svc, "K01"), [])}


def _recon(out, include_depr=True):
	return reconcile.reconcile(out.pools, g.PARAM["recon_tolerance"], include_depr, ["K01"])


class TestAllocationGolden(unittest.TestCase):
	def test_TC_COST_02_cap1_K01_nhan_LABOR_MANAGEMENT(self):
		out, _ = _run()
		_, _, recv = g.run()
		self.assertEqual(out.received[("K01", "LABOR")], recv["LABOR"])
		self.assertEqual(out.received[("K01", "MANAGEMENT")], recv["MANAGEMENT"])
		self.assertEqual(out.received[("K01", "LABOR")], D("120000000.00"))
		self.assertEqual(out.received[("K01", "MANAGEMENT")], D("160000000.00"))
		self.assertNotIn(("HC", "LABOR"), out.received)
		self.assertEqual(out.warnings, [])

	def test_TC_COST_03_phan_con_lai_va_phan_bo_theo_ca(self):
		out, fin = _run()
		g_res, g_recon, _ = g.run()
		pools = {p.cost_category: p for p in out.pools if p.cost_center == "K01"}
		for cat, costed, pool_in, rem, _pct, _over in g_recon:
			self.assertEqual(pools[cat].remainder, rem)
			self.assertEqual(pools[cat].pool_in, pool_in)
			self.assertEqual(pools[cat].costed, costed)
		self.assertEqual(
			[pools[c].remainder for c in ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT")],
			[D("365061600.00"), D("73000000.00"), D("15151520.00"), D("34000000.00"), D("260000000.00")],
		)
		for s in g.NORMS:
			with self.subTest(service=s):
				self.assertEqual(_alloc(out, s), g_res[s]["alloc"])
				self.assertEqual(fin[s].price.full_cost, g_res[s]["full"])
				self.assertEqual(fin[s].price.rounded_price, g_res[s]["rounded"])
		self.assertEqual(fin["DV-TEST-A"].price.full_cost, D("287745.46"))
		self.assertEqual(fin["DV-TEST-B"].price.full_cost, D("88169.70"))

	def test_TC_COST_05_bon_dong_doi_soat(self):
		out, _ = _run()
		_, g_recon, _ = g.run()
		rows = _recon(out)
		expected = [x for x in g_recon if x[0] != "MANAGEMENT"]
		self.assertEqual([r.cost_category for r in rows], ["LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY"])
		for r, (cat, costed, pool_in, rem, pct, over) in zip(rows, expected, strict=True):
			with self.subTest(cat=cat):
				self.assertEqual(
					(r.cost_category, r.costed, r.accounting, r.remainder, r.variance_pct, r.over_tolerance),
					(cat, costed, pool_in, rem, pct, over),
				)
		self.assertEqual([r.cost_category for r in rows if r.over_tolerance], ["DRUG_SUPPLY"])
		self.assertEqual(rows[1].variance_pct, D("-28.08"))

	def test_TC_COST_08_V5_san_luong_bang_0(self):
		with mock.patch.dict(g.VOLUME, {"DV-TEST-B": D("0")}):
			out, fin = _run()
			g_res, _, _ = g.run()
			b = fin["DV-TEST-B"]
			self.assertEqual(b.direct_total, D("32822.44"))
			self.assertEqual(_alloc(out, "DV-TEST-B"), {})
			self.assertEqual(b.alloc_by_category, {})
			self.assertIn(allocation.VOLUME_WARNING, b.message)
			self.assertEqual(_alloc(out, "DV-TEST-A"), g_res["DV-TEST-A"]["alloc"])
			self.assertEqual(g_res["DV-TEST-B"]["alloc"], {c: D("0") for c in g_res["DV-TEST-B"]["alloc"]})

	def test_TC_COST_16_phan_con_lai_am_lay_0(self):
		acc = {k: dict(v) for k, v in g.ACCOUNTING.items()}
		acc["K01"]["DEPRECIATION"] = D("200000000")
		with mock.patch.dict(g.ACCOUNTING, acc):
			out, _ = _run()
			g_res, g_recon, _ = g.run()
			pool = next(p for p in out.pools if p.cost_category == "DEPRECIATION")
			self.assertEqual(pool.remainder, D("0"))
			for s in g.NORMS:
				self.assertEqual(_alloc(out, s)["DEPRECIATION"], D("0"))
				self.assertEqual(g_res[s]["alloc"]["DEPRECIATION"], D("0"))
			row = next(r for r in _recon(out) if r.cost_category == "DEPRECIATION")
			g_row = next(x for x in g_recon if x[0] == "DEPRECIATION")
			self.assertEqual(row.variance_pct, g_row[4])
			self.assertEqual(row.variance_pct, D("42.42"))
			self.assertTrue(row.over_tolerance)
			self.assertEqual(row.over_tolerance, g_row[5])

	def test_V1_khong_phan_bo_khong_doi_soat_khau_hao(self):
		out, fin = _run(False)
		g_res, g_recon, _ = g.run(False)
		for s in g.NORMS:
			self.assertNotIn("DEPRECIATION", _alloc(out, s))
			self.assertEqual(_alloc(out, s), {k: v for k, v in g_res[s]["alloc"].items() if k != "DEPRECIATION"})
		self.assertEqual(fin["DV-TEST-A"].price.full_cost, D("224109.10"))
		rows = _recon(out, False)
		skipped = [r for r in rows if r.skipped]
		self.assertEqual([r.cost_category for r in skipped], ["DEPRECIATION"])
		self.assertEqual(
			(skipped[0].costed, skipped[0].variance_pct), (None, None)
		)
		self.assertEqual(g_recon[2], ("DEPRECIATION", None, None, None, None, None))
		self.assertEqual(len(rows), 4)
