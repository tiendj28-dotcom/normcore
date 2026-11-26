"""Unit test FEAT-015: runner.py."""

import unittest
from decimal import Decimal as D

from normcore.costing import engine as e
from normcore.costing import runner

PARAMS = e.PricingParams(None, D("0"), D("0"), D("100"), True)
SVC = [("A", "K1"), ("B", "K1"), ("B", "K2"), ("C", "K2")]


class TestRunner(unittest.TestCase):
	def test_scope_pairs(self):
		self.assertEqual(runner.scope_pairs(SVC), sorted(SVC))
		self.assertEqual(runner.scope_pairs(SVC, ["B"], []), [("B", "K1"), ("B", "K2")])
		self.assertEqual(runner.scope_pairs(SVC, [], ["K2"]), [("B", "K2"), ("C", "K2")])
		self.assertEqual(runner.scope_pairs(SVC, ["B"], ["K2"]), [("B", "K2")])

	def test_TC_COST_17_eligibility(self):
		pairs = runner.scope_pairs(SVC, ["A", "B", "Z"], [])
		el, inel = runner.eligibility(pairs, {("A", "K1"): "NS-A"}, ["A", "B", "Z"], [])
		self.assertEqual(el, [{"service": "A", "department": "K1", "norm_set": "NS-A"}])
		self.assertEqual(inel, [("B", "K1"), ("B", "K2"), ("Z", "")])
		el, inel = runner.eligibility([], {}, ["Z"], ["K1"])
		self.assertEqual(inel, [])

	def test_needs_background(self):
		self.assertFalse(runner.needs_background(50))
		self.assertTrue(runner.needs_background(51))

	def test_run_thu_tu_tien_do_va_phan_bo(self):
		def load(el):
			return e.ServiceInput(
				el["service"],
				el["department"],
				el["norm_set"],
				(e.NormLine("L1", "", "LABOR", "DD", "DD", D("60")),),
				{"L1": e.LineRate(D("10"), "s")},
			)

		seen = []
		al = e.CostLine("Phân bổ", "LABOR", D("5"))
		res = runner.run(
			[
				{"service": "B", "department": "K1", "norm_set": "n"},
				{"service": "A", "department": "K1", "norm_set": "n"},
			],
			load,
			PARAMS,
			progress=lambda i, n: seen.append((i, n)),
			allocate=lambda rs: {("A", "K1"): [al]},
		)
		self.assertEqual([r.service for r in res], ["A", "B"])
		self.assertEqual(seen, [(1, 2), (2, 2)])
		self.assertEqual(res[0].price.full_cost, D("15.00"))
		self.assertEqual(res[1].price.full_cost, D("10.00"))
		res2 = runner.run([{"service": "A", "department": "K1", "norm_set": "n"}], load, PARAMS)
		self.assertEqual(res2[0].price.full_cost, D("10.00"))
