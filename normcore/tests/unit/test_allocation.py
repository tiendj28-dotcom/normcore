"""Đơn vị allocation.py (FEAT-017): mọi nhánh của phân bổ hai cấp."""

import unittest
from decimal import Decimal as D

from normcore.costing import allocation as a
from normcore.costing import engine

L1, L2 = "Cấp 1", "Cấp 2"


def result(svc="S1", dept="D1", vol="10", direct=None, status="Thành công", msg=""):
	direct = direct or {"LABOR": D("100")}
	return engine.ServiceResult(
		svc, dept, "NS", status, msg, (), {}, direct, sum(direct.values(), D(0)), {}, None,
		None if vol is None else D(vol),
	)


def drv(svc="S1", dept="D1", center="K1", labor="5", machine="0"):
	return a.ServiceDrivers(svc, dept, center, D(labor), D(machine))


def inp(acc=None, rules=(), types=None, cdrv=None, depr=True):
	return a.AllocationInput(
		acc or {}, types or {"K1": "Lâm sàng", "HC": "Hỗ trợ"}, cdrv or {}, tuple(rules), depr
	)


class TestDrivers(unittest.TestCase):
	def test_service_drivers_bo_dong_loai_tru_va_dinh_muc_ban_hanh(self):
		lines = (
			engine.NormLine("1", "", "LABOR", "BS", "BS", D("20"), D("15"), 2),
			engine.NormLine("2", "", "LABOR", "DD", "DD", D("10"), None, 1, excluded=True),
			engine.NormLine("3", "", "EQUIPMENT", "E", "E", D("7")),
			engine.NormLine("4", "", "SUPPLY", "G", "G", D("1")),
		)
		s = engine.ServiceInput("S", "D", "N", lines, {}, D("1"))
		d = a.service_drivers(s, "K1")
		self.assertEqual((d.labor_min_per_case, d.machine_min_per_case, d.cost_center), (D("30"), D("7"), "K1"))

	def test_service_driver_value_cac_tieu_chi(self):
		d, r = drv(machine="2"), result(vol="4", direct={"LABOR": D("50")})
		self.assertEqual(a.service_driver_value(d, r, "LABOR_MIN"), D("20"))
		self.assertEqual(a.service_driver_value(d, r, "MACHINE_MIN"), D("8"))
		self.assertEqual(a.service_driver_value(d, r, "VOLUME"), D("4"))
		self.assertEqual(a.service_driver_value(d, r, "DIRECT_COST"), D("200"))
		self.assertEqual(a.service_driver_value(d, r, "HEADCOUNT"), D("0"))
		self.assertEqual(a.service_driver_value(d, result(vol=None), "VOLUME"), D("0"))


class TestFindRule(unittest.TestCase):
	def test_cu_the_thang_chung(self):
		rs = [a.Rule("A", L2, "LABOR", "VOLUME"), a.Rule("B", L2, "LABOR", "LABOR_MIN", "K1")]
		self.assertEqual(a.find_rule(rs, L2, "LABOR", "K1").name, "B")
		self.assertEqual(a.find_rule(rs, L2, "LABOR", "K2").name, "A")
		self.assertIsNone(a.find_rule(rs, L1, "LABOR", "K1"))
		self.assertIsNone(a.find_rule(rs, L2, "UTILITY", "K1"))

	def test_trung_lay_ten_nho_va_canh_bao(self):
		rs = [a.Rule("Z", L2, "LABOR", "VOLUME"), a.Rule("M", L2, "LABOR", "VOLUME")]
		w = []
		self.assertEqual(a.find_rule(rs, L2, "LABOR", "K1", w).name, "M")
		self.assertEqual(len(w), 1)


class TestLevel1(unittest.TestCase):
	def test_chia_theo_headcount_va_bo_hong_so_0(self):
		i = inp(
			acc={("HC", "LABOR"): D("100"), ("HC", "UTILITY"): D("0")},
			rules=[a.Rule("R", L1, "LABOR", "HEADCOUNT", "HC")],
			types={"K1": "Lâm sàng", "K2": "Lâm sàng", "HC": "Hỗ trợ"},
			cdrv={"K1": {"HEADCOUNT": 1}, "K2": {"HEADCOUNT": 2}},
		)
		rec, w = a.level1(i, {})
		self.assertEqual(rec, {("K1", "LABOR"): D("33.33"), ("K2", "LABOR"): D("66.67")})
		self.assertEqual(w, [])

	def test_thieu_quy_tac_canh_bao(self):
		rec, w = a.level1(inp(acc={("HC", "LABOR"): D("5")}), {})
		self.assertEqual(rec, {})
		self.assertIn("Thiếu quy tắc phân bổ cấp 1", w[0])

	def test_tong_tieu_chi_0_canh_bao(self):
		i = inp(acc={("HC", "LABOR"): D("5")}, rules=[a.Rule("R", L1, "LABOR", "HEADCOUNT")])
		rec, w = a.level1(i, {})
		self.assertEqual(rec, {})
		self.assertIn("bằng 0", w[0])

	def test_khong_co_trung_tam_lam_sang(self):
		i = a.AllocationInput(
			{("HC", "LABOR"): D(5)}, {"HC": "Hỗ trợ"}, {}, (a.Rule("R", L1, "LABOR", "VOLUME"),), True
		)
		rec, w = a.level1(i, {})
		self.assertEqual(rec, {})
		self.assertEqual(len(w), 1)

	def test_tieu_chi_VOLUME_va_DIRECT_COST_theo_dich_vu(self):
		members = {
			"K1": [(drv(), result(vol="1", direct={"LABOR": D("10")}))],
			"K2": [(drv("S2", "D2", "K2"), result("S2", "D2", vol="3", direct={"LABOR": D("10")}))],
		}
		types = {"K1": "Lâm sàng", "K2": "Lâm sàng", "HC": "Hỗ trợ"}
		for driver, e1 in (("VOLUME", D("25.00")), ("DIRECT_COST", D("25.00"))):
			i = a.AllocationInput(
				{("HC", "LABOR"): D(100)}, types, {}, (a.Rule("R", L1, "LABOR", driver),), True
			)
			rec, _ = a.level1(i, members)
			self.assertEqual(rec[("K1", "LABOR")], e1)
			self.assertEqual(rec[("K2", "LABOR")], D("75.00"))


class TestLevel2(unittest.TestCase):
	def _members(self, vols=("10", "30")):
		return {
			"K1": [
				(drv("S1", "D1", "K1", "5"), result("S1", vol=vols[0], direct={"LABOR": D("10")})),
				(drv("S2", "D1", "K1", "5"), result("S2", vol=vols[1], direct={"LABOR": D("10")})),
			]
		}

	def test_chia_theo_ca_va_ghi_tieu_chi(self):
		i = inp(acc={("K1", "LABOR"): D("1000")}, rules=[a.Rule("R", L2, "LABOR", "VOLUME")])
		lines, pools, w = a.level2(i, self._members(), {("K1", "LABOR"): D("200")})
		self.assertEqual(w, [])
		self.assertEqual(pools[0].pool_in, D("1200"))
		self.assertEqual(pools[0].costed, D("400"))
		self.assertEqual(pools[0].remainder, D("800"))
		x = lines[("S1", "D1")][0]
		self.assertEqual((x.amount, x.driver_value, x.driver_total, x.pool_amount), (D("20.00"), D("10"), D("40"), D("800")))
		self.assertEqual(x.allocation_rule, "R")
		self.assertEqual(x.rate_source, "Cấp 2 · VOLUME")
		self.assertEqual(lines[("S2", "D1")][0].amount, D("20.00"))

	def test_phan_con_lai_am_lay_0_van_ghi_dong(self):
		i = inp(acc={("K1", "LABOR"): D("100")}, rules=[a.Rule("R", L2, "LABOR", "VOLUME")])
		lines, pools, _ = a.level2(i, self._members(), {})
		self.assertEqual(pools[0].remainder, D(0))
		self.assertEqual(lines[("S1", "D1")][0].amount, D(0))

	def test_thieu_quy_tac_cap_2(self):
		i = inp(acc={("K1", "LABOR"): D("1000")})
		lines, pools, w = a.level2(i, self._members(), {})
		self.assertEqual(lines, {})
		self.assertIn("Thiếu quy tắc phân bổ cấp 2", w[0])
		self.assertIsNone(pools[0].rule)

	def test_thieu_quy_tac_nhung_con_lai_0_khong_canh_bao(self):
		i = inp(acc={("K1", "LABOR"): D("1")})
		_, _, w = a.level2(i, self._members(), {})
		self.assertEqual(w, [])

	def test_tong_tieu_chi_0(self):
		i = inp(acc={("K1", "DEPRECIATION"): D("1000")}, rules=[a.Rule("R", L2, "DEPRECIATION", "MACHINE_MIN")])
		lines, pools, w = a.level2(i, self._members(), {})
		self.assertEqual(lines, {})
		self.assertIn("bằng 0", w[0])
		self.assertEqual(next(p for p in pools if p.cost_category == "DEPRECIATION").driver_total, D(0))

	def test_tong_tieu_chi_0_con_lai_0_khong_canh_bao(self):
		i = inp(acc={("K1", "DEPRECIATION"): D("0")}, rules=[a.Rule("R", L2, "DEPRECIATION", "MACHINE_MIN")])
		self.assertEqual(a.level2(i, self._members(), {})[2], [])

	def test_san_luong_0_khong_nhan_va_khong_gop_tieu_chi(self):
		i = inp(acc={("K1", "LABOR"): D("1000")}, rules=[a.Rule("R", L2, "LABOR", "VOLUME")])
		lines, _, _ = a.level2(i, self._members(("0", "10")), {})
		self.assertNotIn(("S1", "D1"), lines)
		self.assertEqual(lines[("S2", "D1")][0].amount, D("90.00"))  # (1000 - 100) / 10 ca

	def test_bo_khau_hao_khi_loai_gia_khong_ket_cau(self):
		i = inp(acc={("K1", "DEPRECIATION"): D("1000")}, depr=False)
		_, pools, _ = a.level2(i, self._members(), {})
		self.assertEqual([p.cost_category for p in pools], ["LABOR"])

	def test_trung_tam_khong_dich_vu_bi_bo_qua(self):
		i = inp(acc={("K1", "LABOR"): D("1000")})
		self.assertEqual(a.level2(i, {"K1": []}, {}), ({}, [], []))


class TestAllocate(unittest.TestCase):
	def test_bo_dich_vu_loi_va_dich_vu_khong_co_trung_tam(self):
		i = inp(acc={("K1", "LABOR"): D("100")}, rules=[a.Rule("R", L2, "LABOR", "VOLUME")])
		rs = [
			result("S1"),
			result("S2", status="Lỗi"),
			result("S3"),
		]
		out = a.allocate(rs, {("S1", "D1"): drv(), ("S3", "D1"): drv("S3", center=None)}, i)
		self.assertEqual(list(out.lines), [("S1", "D1")])
		self.assertEqual(len(out.warnings), 1)
		self.assertIn("S3", out.warnings[0])

	def test_canh_bao_khong_trung_lap(self):
		i = inp(acc={("K1", "LABOR"): D("100")})
		out = a.allocate([result("S1"), result("S2")], {("S1", "D1"): drv(), ("S2", "D1"): drv("S2")}, i)
		self.assertEqual(len(out.warnings), len(set(out.warnings)))


class TestMarkVolume(unittest.TestCase):
	def test_khong_va_thieu_san_luong(self):
		for v in ("0", None):
			r = a.mark_volume(result(vol=v))
			self.assertEqual(r.message, a.VOLUME_WARNING)
			self.assertEqual(r.status, "Thành công")
		r = a.mark_volume(result(vol="0", msg="x"))
		self.assertEqual(r.message, "x; " + a.VOLUME_WARNING)

	def test_binh_thuong_va_loi_tra_nguyen(self):
		r, e = result(vol="3"), result(vol="0", status="Lỗi")
		self.assertIs(a.mark_volume(r), r)
		self.assertIs(a.mark_volume(e), e)
