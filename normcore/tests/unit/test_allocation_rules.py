"""FEAT-016 — hàm thuần quy tắc phân bổ, sản lượng, tiêu chí (BR-COST-009)."""

import unittest
from decimal import Decimal

from normcore.costing import allocation_rules as ar


class TestRules(unittest.TestCase):
	def test_TC_ACCT_07_cap2_headcount_bi_tu_choi(self):
		errs = ar.rule_errors("Cấp 2", "LABOR", "HEADCOUNT")
		self.assertEqual(len(errs), 1)
		self.assertIn("HEADCOUNT", errs[0])
		self.assertIn("cấp 1", errs[0])

	def test_TC_ACCT_07_cap2_labor_min_hop_le(self):
		self.assertEqual(ar.rule_errors("Cấp 2", "LABOR", "LABOR_MIN"), [])

	def test_TC_ACCT_07_cap1_moi_tieu_chi(self):
		for d in ar.DRIVERS:
			self.assertEqual(ar.rule_errors("Cấp 1", "MANAGEMENT", d), [])

	def test_cap2_area_revenue_bi_tu_choi(self):
		for d in ("AREA", "REVENUE"):
			self.assertTrue(ar.rule_errors("Cấp 2", "LABOR", d))

	def test_excluded_khong_phan_bo(self):
		self.assertTrue(ar.rule_errors("Cấp 1", "EXCLUDED", "VOLUME"))

	def test_loai_trung_tam_theo_cap(self):
		self.assertEqual(ar.rule_errors("Cấp 1", "LABOR", "HEADCOUNT", "Hỗ trợ"), [])
		self.assertTrue(ar.rule_errors("Cấp 1", "LABOR", "HEADCOUNT", "Lâm sàng"))
		self.assertEqual(ar.rule_errors("Cấp 2", "LABOR", "LABOR_MIN", "Lâm sàng"), [])
		self.assertTrue(ar.rule_errors("Cấp 2", "LABOR", "LABOR_MIN", "Hỗ trợ"))


class TestValues(unittest.TestCase):
	def test_driver_errors(self):
		self.assertEqual(ar.driver_errors({"headcount": 20, "area_m2": None}), [])
		self.assertEqual(len(ar.driver_errors({"headcount": -1, "revenue": -5})), 2)

	def test_N31_07_driver_errors_dung_nhan_tieng_viet(self):
		self.assertEqual(
			ar.driver_errors({"headcount": -1, "area_m2": -2, "revenue": -5}),
			["Số nhân lực không được âm", "Diện tích (m²) không được âm", "Doanh thu không được âm"],
		)

	def test_volume_errors(self):
		self.assertEqual(ar.volume_errors(0), [])
		self.assertEqual(ar.volume_errors(None), [])
		self.assertTrue(ar.volume_errors(-1))

	def test_valid_year(self):
		self.assertTrue(ar.valid_year(2026))
		self.assertTrue(ar.valid_year("2000"))
		self.assertFalse(ar.valid_year(1999))
		self.assertFalse(ar.valid_year(2101))
		self.assertFalse(ar.valid_year("abc"))
		self.assertFalse(ar.valid_year(None))

	def test_driver_shares(self):
		s = ar.driver_shares({"K01": 20, "K02": Decimal("30")})
		self.assertEqual(s["K01"], Decimal("0.4"))
		self.assertEqual(s["K02"], Decimal("0.6"))

	def test_driver_shares_tong_0_hoac_rong(self):
		with self.assertRaises(ValueError):
			ar.driver_shares({})
		with self.assertRaises(ValueError):
			ar.driver_shares({"K01": 0})
