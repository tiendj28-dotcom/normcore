"""Đơn vị reconcile.py (FEAT-017; BR-COST-015)."""

import unittest
from decimal import Decimal as D

from normcore.costing import reconcile as r
from normcore.costing.allocation import Pool


def pool(cat, pool_in, costed, center="K1"):
	return Pool(center, cat, D(pool_in), D(0), D(pool_in), D(costed), max(D(pool_in) - D(costed), D(0)))


class TestReconcile(unittest.TestCase):
	def test_bo_management_va_dong_hai_so_0(self):
		rows = r.reconcile([pool("MANAGEMENT", 10, 0), pool("LABOR", 0, 0), pool("UTILITY", 100, 100)], 10, True)
		self.assertEqual([x.cost_category for x in rows], ["UTILITY"])
		self.assertEqual((rows[0].variance, rows[0].variance_pct, rows[0].over_tolerance), (D(0), D("0.00"), False))

	def test_nguong_tren_va_duoi(self):
		up = r.reconcile([pool("LABOR", 100, 111)], 10, True)[0]
		self.assertEqual((up.variance_pct, up.over_tolerance), (D("11.00"), True))
		eq = r.reconcile([pool("LABOR", 100, 110)], 10, True)[0]
		self.assertFalse(eq.over_tolerance)
		low = r.reconcile([pool("LABOR", 100, 80), pool("DRUG_SUPPLY", 100, 80)], 10, True)
		self.assertEqual([x.over_tolerance for x in low], [False, True])  # chỉ DRUG_SUPPLY bị chặn dưới

	def test_so_ke_toan_0_ma_da_tinh_duong(self):
		x = r.reconcile([pool("LABOR", 0, 5)], 10, True)[0]
		self.assertIsNone(x.variance_pct)
		self.assertTrue(x.over_tolerance)
		self.assertEqual(x.variance, D(5))

	def test_bo_khau_hao_khi_loai_gia_khong_ket_cau(self):
		rows = r.reconcile([pool("LABOR", 100, 100), pool("DEPRECIATION", 100, 50)], 10, False, ["K1", "K1"])
		self.assertEqual([(x.cost_category, x.skipped) for x in rows], [("LABOR", False), ("DEPRECIATION", True)])
		self.assertIsNone(rows[1].costed)
		self.assertIsNone(rows[1].over_tolerance)

	def test_khau_hao_van_doi_soat_khi_ket_cau(self):
		rows = r.reconcile([pool("DEPRECIATION", 100, 50)], 10, True, ["K1"])
		self.assertEqual(len(rows), 1)
		self.assertFalse(rows[0].skipped)

	def test_thu_tu_trung_tam_roi_loai(self):
		rows = r.reconcile([pool("UTILITY", 1, 1, "K2"), pool("UTILITY", 1, 1, "K1"), pool("LABOR", 1, 1, "K2")], 10, True)
		self.assertEqual([(x.cost_center, x.cost_category) for x in rows], [("K1", "UTILITY"), ("K2", "LABOR"), ("K2", "UTILITY")])


class TestLockBlockers(unittest.TestCase):
	def test_giai_trinh_rong_hoac_khoang_trang(self):
		lines = [
			{"cost_center": "K1", "cost_category": "DRUG_SUPPLY", "over_tolerance": 1, "explanation": "  "},
			{"cost_center": "K1", "cost_category": "LABOR", "over_tolerance": 1, "explanation": None},
			{"cost_center": "K1", "cost_category": "UTILITY", "over_tolerance": 1, "explanation": "đã giải trình"},
			{"cost_center": "K1", "cost_category": "DEPRECIATION", "over_tolerance": 0, "explanation": ""},
		]
		self.assertEqual(r.lock_blockers(lines), ["K1 · DRUG_SUPPLY", "K1 · LABOR"])
		self.assertEqual(r.lock_blockers([]), [])
