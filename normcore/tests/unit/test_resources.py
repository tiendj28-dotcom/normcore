"""FEAT-010: hàm thuần thiết bị và phòng (TC-RES-03, TC-RES-04, TC-RES-10, TC-CLS-48, TC-CLS-49)."""

import unittest
from datetime import date
from decimal import Decimal as D

from normcore.costing import resources as r

ON = date(2026, 12, 31)
EQ1 = dict(cost=D("1200000000"), life=D("8"), maint=D("30000000"), calib=D("6000000"))


def eq1_rate(in_service, expired_mode=r.ZERO):
	m = r.machine_annual(r.BUY, EQ1["cost"], EQ1["life"], in_service, None, ON, expired_mode)
	annual = r.equipment_annual(m, EQ1["maint"], EQ1["calib"])
	return m, r.machine_hourly_rate(annual, D("2112"), D("0.5"))


class TestResources(unittest.TestCase):
	def test_TC_RES_03_eq1(self):
		m, rate = eq1_rate(date(2022, 1, 1))
		self.assertEqual(m, D("150000000"))
		self.assertEqual(rate, D("176136.3636"))

	def test_TC_RES_04_v2_zero(self):
		m, rate = eq1_rate(date(2015, 1, 1), r.ZERO)
		self.assertEqual(m, 0)
		self.assertEqual(rate, D("34090.9091"))

	def test_TC_RES_04_v2_continue(self):
		m, _ = eq1_rate(date(2015, 1, 1), r.CONTINUE)
		self.assertEqual(m, D("150000000"))

	def test_het_han_dung_ngay(self):
		self.assertTrue(r.is_expired(date(2018, 12, 31), 8, ON))
		self.assertFalse(r.is_expired(date(2019, 1, 1), 8, ON))

	def test_TC_RES_10_phong_r1(self):
		self.assertEqual(r.room_hourly_rate(D("52800000"), D("2112")), D("25000.0000"))
		self.assertEqual(
			r.validate_room({"annual_infrastructure_cost": 52800000, "available_hours_per_year": 2112}), []
		)
		self.assertTrue(r.validate_room({"annual_infrastructure_cost": 52800000}))
		self.assertRaises(ValueError, r.room_hourly_rate, 1, 0)

	def test_TC_CLS_48_truong_bat_buoc(self):
		base = dict(acquisition_mode=r.BUY, allocation_basis=r.BASIS_RESULT)
		self.assertTrue(r.validate_equipment({**base, "acquisition_mode": r.RENT}))
		self.assertTrue(r.validate_equipment({**base, "useful_life_years": 8}))
		self.assertEqual(r.validate_equipment({**base, "original_cost": 1, "useful_life_years": 8}), [])
		self.assertEqual(r.validate_equipment({**base, "acquisition_mode": r.VENDOR}), [])
		self.assertEqual(
			r.validate_equipment({**base, "acquisition_mode": r.JOINT, "annual_contract_cost": 5}), []
		)
		hours = dict(acquisition_mode=r.VENDOR, allocation_basis=r.BASIS_HOURS)
		self.assertEqual(len(r.validate_equipment(hours)), 2)
		self.assertEqual(
			r.validate_equipment({**hours, "planned_hours_per_year": 100, "utilization_rate": 1}), []
		)
		self.assertTrue(r.validate_equipment({**base, "acquisition_mode": "X", "allocation_basis": "Y"}))
		self.assertTrue(r.validate_equipment({**base, "original_cost": -1, "useful_life_years": 8}))

	def test_TC_CLS_49_ty_le_khoa(self):
		self.assertTrue(r.validate_allocations([("A", 60), ("B", 30)]))
		self.assertEqual(r.validate_allocations([("A", 60), ("B", 40)]), [])
		self.assertEqual(r.validate_allocations([]), [])
		self.assertTrue(r.validate_allocations([("A", 50), ("A", 50)]))
		self.assertTrue(r.validate_allocations([("A", 110), ("B", -10)]))

	def test_thue_va_dat(self):
		self.assertEqual(r.machine_annual(r.RENT, contract_cost=450000000), D("450000000"))
		self.assertEqual(r.machine_annual(r.JOINT, contract_cost=1), 1)
		self.assertEqual(r.machine_annual(r.VENDOR, 1, 1), 0)
		self.assertEqual(r.machine_annual(r.BUY, 100, 4, include_depr=False), 0)
		self.assertRaises(ValueError, r.machine_annual, "X")
		self.assertRaises(ValueError, r.machine_annual, r.BUY, 1, 0)
		self.assertRaises(ValueError, r.machine_annual, r.BUY, 1, 1, expired_mode="Q")

	def test_dat_bao_tri_va_linh_kien_nha_cung_cap(self):
		comps = [(D("24000000"), r.LIFE_MONTH, D("12"), True), (D("1200"), r.LIFE_MONTH, D("12"), False)]
		a = r.equipment_annual(0, 40000000, 0, comps, r.VENDOR, True)
		self.assertEqual(a, D("1200"))
		self.assertRaises(ValueError, r.equipment_annual, 0, 0, 0, [(1, r.LIFE_MONTH, 0, False)])
		self.assertEqual(r.equipment_annual(0, 0, 0, [(1, "Số kết quả", 5, False)]), 0)

	def test_don_gia_gio_chia_khong(self):
		self.assertRaises(ValueError, r.machine_hourly_rate, 1, 0, 1)


class TestResourcesReview(unittest.TestCase):
	def test_TC_CLS_48_trong_la_khong_hop_le(self):
		for empty in ("", None):
			f = dict(acquisition_mode=r.BUY, allocation_basis=empty, original_cost=1, useful_life_years=1)
			self.assertTrue(r.validate_equipment(f), empty)
			f = dict(acquisition_mode=empty, allocation_basis=r.BASIS_RESULT)
			self.assertTrue(r.validate_equipment(f), empty)

	def test_het_han_ngay_29_02_nam_dich_khong_nhuan(self):
		# ASM-083: 29/02/2024 + 5 năm → 28/02/2029; không ném ValueError
		self.assertFalse(r.is_expired(date(2024, 2, 29), 5, date(2029, 2, 27)))
		self.assertTrue(r.is_expired(date(2024, 2, 29), 5, date(2029, 2, 28)))
		self.assertTrue(r.is_expired(date(2024, 2, 29), 4, date(2028, 2, 29)))  # năm đích nhuận: giữ 29/02
		self.assertFalse(r.is_expired(date(2024, 2, 29), 4, date(2028, 2, 28)))
		self.assertTrue(r.is_expired(date(2000, 2, 29), 100, date(2100, 2, 28)))  # 2100 không nhuận

	def test_so_nam_le_cat_ve_so_nguyen(self):
		self.assertFalse(r.is_expired(date(2020, 1, 1), 5.9, date(2024, 12, 31)))
		self.assertTrue(r.is_expired(date(2020, 1, 1), 5.9, date(2025, 1, 1)))

	def test_thong_bao_am_tieng_viet(self):
		errs = r.validate_equipment(
			dict(acquisition_mode=r.VENDOR, allocation_basis=r.BASIS_RESULT, power_kw=-1)
		)
		self.assertEqual(errs, ["Công suất khi chạy không được âm"])
