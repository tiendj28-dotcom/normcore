"""Unit test thuan BR-COST-013: tich luy va nghia vu tai chinh (unittest, chay duoc ca bench va pytest)."""

import unittest
from decimal import Decimal as D

from normcore.costing.engine import apply_accumulation


class TestAccumulation(unittest.TestCase):
	def test_TC_COST_04_on_price(self):
		r = apply_accumulation(D("1000"), "ON_PRICE", D("0.05"), D("0"))
		self.assertEqual(r.accumulation, D("52.63"))  # 1000*0.05/0.95
		self.assertEqual(r.calculated_price, D("1052.63"))

	def test_TC_COST_04_khong_tich_luy(self):
		r = apply_accumulation(D("1000"), None, D("0.05"), D("0"))
		self.assertEqual(r.accumulation, D("0.00"))
		self.assertEqual(r.calculated_price, D("1000.00"))

	def test_TC_COST_04_nghia_vu_tai_chinh(self):
		r = apply_accumulation(D("1000"), "ON_COST", D("0.05"), D("0.1"))
		self.assertEqual(r.accumulation, D("50.00"))
		self.assertEqual(r.calculated_price, D("1166.67"))  # 1050/0.9
		self.assertEqual(r.obligation, D("116.67"))

	def test_TC_COST_04_lam_tron_half_up(self):
		r = apply_accumulation(D("0.10"), "ON_COST", D("0.05"), D("0"))  # 0.005 -> 0.01
		self.assertEqual(r.accumulation, D("0.01"))

	def test_TC_COST_04_tham_so_sai(self):
		cases = [
			(D("1"), "ON_COST", D("1"), D("0")),
			(D("1"), "ON_PRICE", D("1"), D("0")),
			(D("1"), "ON_COST", D("0.05"), D("1")),
			(D("1"), "BAD", D("0.05"), D("0")),
			(D("-1"), "ON_COST", D("0.05"), D("0")),
		]
		for args in cases:
			with self.subTest(args=args), self.assertRaises(ValueError):
				apply_accumulation(*args)
