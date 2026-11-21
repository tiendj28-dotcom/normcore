"""Unit test thuan dong LABOR: BR-COST-001, BR-COST-002, BR-COST-007 (unittest, chay duoc ca bench va pytest)."""

import unittest
from decimal import Decimal as D

from normcore.costing.engine import (
	LaborLine,
	LaborLineResult,
	applied_qty,
	compute_direct_lines,
	job_rate,
	labor_line,
)

BASE = D("2500000")
CONTRIB = D("0.235")
DAYS = D("264")
HOURS = D("8")


def _rate(coef, allow, other=D("0"), override=None):
	return job_rate(BASE, coef, allow, CONTRIB, other, DAYS, HOURS, annual_cost_override=override)


class TestJobRate(unittest.TestCase):
	def test_TC_RES_05_bac_si(self):
		r = _rate(D("4.40"), D("0.60"))
		self.assertEqual(r.annual_cost, D("185250000"))
		self.assertEqual(r.hourly_rate, D("87713.0682"))

	def test_TC_RES_05_dieu_duong(self):
		r = _rate(D("3.00"), D("0.40"))
		self.assertEqual(r.annual_cost, D("125970000"))
		self.assertEqual(r.hourly_rate, D("59644.8864"))

	def test_TC_RES_05_thu_nhap_khac_duoc_cong(self):
		r = _rate(D("3.00"), D("0.40"), other=D("1000000"))
		self.assertEqual(r.annual_cost, D("126970000"))

	def test_TC_RES_05_nhap_thang_chi_phi_nam(self):
		# G1: thay toan bo cong thuc, ke ca thu nhap khac
		r = _rate(D("3.00"), D("0.40"), other=D("1000000"), override=D("100000000"))
		self.assertEqual(r.annual_cost, D("100000000"))
		self.assertEqual(r.hourly_rate, D("47348.4848"))  # 100000000 / 2112

	def test_TC_RES_05_nhap_thang_bang_khong(self):
		self.assertEqual(_rate(D("3"), D("0.4"), override=D("0")).hourly_rate, D("0.0000"))

	def test_TC_RES_05_dau_vao_khong_hop_le(self):
		with self.assertRaises(ValueError):
			_rate(D("3"), D("0.4"), override=D("-1"))
		with self.assertRaises(ValueError):
			job_rate(BASE, D("3"), D("0.4"), CONTRIB, D("0"), D("0"), HOURS)
		with self.assertRaises(ValueError):
			job_rate(BASE, D("3"), D("0.4"), CONTRIB, D("0"), DAYS, D("-8"))


class TestAppliedQty(unittest.TestCase):
	def test_TC_NORM_03_co_dinh_muc_ban_hanh_lay_nho_hon(self):
		self.assertEqual(applied_qty(D("20"), D("25")), D("20"))  # L03
		self.assertEqual(applied_qty(D("15"), D("10")), D("10"))  # L09

	def test_TC_NORM_03_khong_co_dinh_muc_ban_hanh(self):
		self.assertEqual(applied_qty(D("10"), None), D("10"))  # L01

	def test_TC_NORM_03_ban_hanh_bang_khong_van_la_co(self):
		self.assertEqual(applied_qty(D("10"), D("0")), D("0"))  # G4

	def test_TC_NORM_03_phut_am(self):
		with self.assertRaises(ValueError):
			applied_qty(D("-1"), None)


class TestLaborLine(unittest.TestCase):
	def test_TC_COST_01_labor_l01(self):
		r = labor_line(D("10"), None, 1, D("59644.8864"))
		self.assertEqual(r, LaborLineResult(D("10"), D("59644.8864"), D("9940.81")))

	def test_TC_COST_01_labor_l03_ap_dung_ban_hanh(self):
		r = labor_line(D("20"), D("25"), 1, D("87713.0682"))
		self.assertEqual(r.applied_qty, D("20"))
		self.assertEqual(r.amount, D("29237.69"))

	def test_TC_COST_01_labor_nhieu_nguoi(self):
		r = labor_line(D("60"), None, 3, D("100"))
		self.assertEqual(r.amount, D("300.00"))

	def test_TC_COST_01_labor_dau_vao_khong_hop_le(self):
		with self.assertRaises(ValueError):
			labor_line(D("10"), None, 0, D("1"))
		with self.assertRaises(ValueError):
			labor_line(D("10"), None, 1, D("-1"))


class TestDirectLinesExtensionPoint(unittest.TestCase):
	def setUp(self):
		self.lines = [
			LaborLine("L01", D("10"), 1, D("59644.8864")),
			LaborLine("L03", D("20"), 1, D("87713.0682"), authority_qty=D("25")),
		]

	def test_TC_COST_01_labor_khong_truyen_ham_thi_tinh_labor(self):
		out = compute_direct_lines(self.lines)
		self.assertEqual([r.amount for r in out], [D("9940.81"), D("29237.69")])

	def test_TC_COST_01_labor_diem_cam_dung_ket_qua_ham_gia(self):
		fake = LaborLineResult(D("1"), D("2"), D("3.00"))
		out = compute_direct_lines(self.lines, extension=lambda line: fake)
		self.assertEqual(out, [fake, fake])

	def test_TC_COST_01_labor_ham_gia_tra_none_thi_quay_ve_labor(self):
		out = compute_direct_lines(self.lines, extension=lambda line: None)
		self.assertEqual(out[0].amount, D("9940.81"))


if __name__ == "__main__":
	unittest.main()
