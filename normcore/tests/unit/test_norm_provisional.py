import unittest
from decimal import Decimal as D

from normcore.costing.provisional import line_amount, summarize


class TestLineAmount(unittest.TestCase):
	def test_labor(self):
		self.assertEqual(line_amount("LABOR", D("30"), D("100000"), headcount=2), D("100000.00"))

	def test_vat_tu_hao_hut_va_su_dung_lai(self):
		self.assertEqual(line_amount("DRUG", D("1"), D("25000"), wastage_rate=D("0.05")), D("26250.00"))
		self.assertEqual(line_amount("SUPPLY", D("1"), D("2000000"), reuse_count=200), D("10000.00"))

	def test_thiet_bi_phong_tien_ich(self):
		self.assertEqual(line_amount("EQUIPMENT", D("20"), D("300")), D("100.00"))
		self.assertEqual(line_amount("INFRA", D("30"), D("25")), D("12.50"))
		self.assertEqual(line_amount("UTILITY", D("0.5"), D("3000")), D("1500.00"))

	def test_lam_tron_half_up(self):
		self.assertEqual(line_amount("UTILITY", D("1"), D("0.005")), D("0.01"))

	def test_loi(self):
		for args in (("X", 1, 1), ("LABOR", -1, 1), ("SUPPLY", 1, -1)):
			with self.assertRaises(ValueError):
				line_amount(*args)
		with self.assertRaises(ValueError):
			line_amount("DRUG", 1, 1, wastage_rate=-1)
		with self.assertRaises(ValueError):
			line_amount("DRUG", 1, 1, reuse_count=0)


class TestSummarize(unittest.TestCase):
	def test_tong_theo_buoc_cau_phan(self):
		s = summarize(
			[
				("S1", "LABOR", D("10"), False),
				("S1", "LABOR", D("5"), False),
				("S1", "SUPPLY", D("2"), False),
				("S2", "SUPPLY", D("3"), False),
				("S2", "DRUG", D("99"), True),
			]
		)
		self.assertEqual(s["by_step_component"]["S1"], {"LABOR": D("15"), "SUPPLY": D("2")})
		self.assertEqual(s["by_step_component"]["S2"]["DRUG"], D("0"))
		self.assertEqual(s["by_component"]["SUPPLY"], D("5"))
		self.assertEqual(s["total"], D("20"))
		self.assertFalse(s["incomplete"])

	def test_thieu_don_gia(self):
		s = summarize([("S1", "LABOR", None, False), ("S1", "SUPPLY", D("2"), False)])
		self.assertTrue(s["incomplete"])
		self.assertEqual(s["total"], D("2"))
		self.assertNotIn("LABOR", s["by_component"])
