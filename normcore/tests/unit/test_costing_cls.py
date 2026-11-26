"""Unit test FEAT-036: costing/cls.py (không cần site)."""

import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal as D

from normcore.costing import cls, engine, resources, runner
from normcore.tests.golden import cls_fixture as f


def run_service(**kw):
	return f.cost(**kw)


def with_system(code, **override):
	return f.system(code, **override)


class TestAuxAndK(unittest.TestCase):
	def test_aux_actual_va_hon_hop(self):
		s = with_system("GLU-A", actual=cls.AuxCounts(qnk=D("600"), h=D("0.03")))
		qnk, qcal, qrerun, qeqa, h, est = cls.aux_counts(s)
		self.assertEqual(
			(qnk, qcal, qrerun, qeqa, h, est), (D("600"), D("48"), D("240"), D("12"), D("0.03"), True)
		)

	def test_aux_chan_doan_hinh_anh(self):
		s = with_system("GLU-A", actual=cls.AuxCounts())
		qnk, qcal, qrerun, qeqa, h, _est = cls.aux_counts(s, imaging=True)
		self.assertEqual((qnk, qcal, qeqa, h), (D(0), D(0), D(0), D(0)))
		k, _total = cls.k_factor(s.qbn, qnk, qcal, qrerun, qeqa, h)
		self.assertEqual(k, cls.r6(D(1) + qrerun / s.qbn))

	def test_k_factor_loi(self):
		with self.assertRaises(ValueError):
			cls.k_factor(0, 0, 0, 0, 0, 0)
		with self.assertRaises(ValueError):
			cls.k_factor(10, 0, 0, 0, 0, 1)


class TestEquipment(unittest.TestCase):
	def setUp(self):
		self.inp = f.service_input()

	def test_compliance_khong_ho_so_dung_so_nhap_tay(self):
		a = replace(self.inp.equipment["EQ_A"], records=(), manual_calibration=D("5000000"))
		self.assertEqual(cls.compliance_annual(a, [a], "ASSET"), D("5000000"))

	def test_compliance_ho_so_het_han_khong_tinh(self):
		a = replace(
			self.inp.equipment["EQ_A"],
			records=(cls.RecordInput(D("8000000"), D(12), False),),
			manual_calibration=D("1"),
		)
		# FR-CMP-002, ASM-036-11: có hồ sơ mà hết hạn hết thì phần riêng = 0 (số nhập tay chỉ dùng khi không có hồ sơ nào)
		self.assertEqual(cls.compliance_annual(a, [a], "DIRECT"), D("0"))

	def test_compliance_het_han_van_o_trong_quy_asset_va_direct(self):
		"""Review NORM-42: EQ_A hết hạn (nhập tay 999), EQ_B còn hạn 6.000.000/năm; giá trị tài sản 3,6 tỷ và 1,2 tỷ."""
		e = self.inp.equipment
		a = replace(
			e["EQ_A"], records=(cls.RecordInput(D("8000000"), D(12), False),), manual_calibration=D("999")
		)
		b = replace(e["EQ_B"], records=(cls.RecordInput(D("6000000"), D(12), True),))
		peers = [a, b]
		self.assertEqual(cls.compliance_annual(a, peers, "ASSET"), D("4500000"))
		self.assertEqual(cls.compliance_annual(b, peers, "ASSET"), D("1500000"))
		self.assertEqual(cls.compliance_annual(a, peers, "DIRECT"), D("0"))
		self.assertEqual(cls.compliance_annual(b, peers, "DIRECT"), D("6000000"))

	def test_compliance_khong_ho_so_nao_ngoai_quy(self):
		"""Không có bản ghi nào: số nhập tay, tính như Gắn trực tiếp, không vào tử và mẫu của quỹ."""
		e = self.inp.equipment
		a = replace(e["EQ_A"], records=(), manual_calibration=D("999"))
		b = replace(e["EQ_B"], records=(cls.RecordInput(D("6000000"), D(12), True),))
		self.assertEqual(cls.compliance_annual(a, [a, b], "ASSET"), D("999"))
		self.assertEqual(cls.compliance_annual(b, [a, b], "ASSET"), D("6000000"))

	def test_compliance_khong_nguyen_gia_tinh_truc_tiep(self):
		a = replace(self.inp.equipment["EQ_A"], asset_value=None)
		self.assertEqual(cls.compliance_annual(a, [a, self.inp.equipment["EQ_B"]], "ASSET"), D("8000000"))

	def test_per_result_ba_tieu_chi_va_loi(self):
		inp = self.inp
		a = inp.equipment["EQ_A"]
		self.assertEqual(cls.per_result(a, D("300000"))[0], D("1.00"))
		h = replace(a, basis=resources.BASIS_HOURS, planned_hours=D("3000"), utilization=D("0.8"))
		amount, _label, value = cls.per_result(h, D("2400000"), D("30"))
		self.assertEqual((amount, value), (D("500.00"), D("2400.0")))
		with self.assertRaises(ValueError):
			cls.per_result(replace(a, qtb=None), D(1))
		with self.assertRaises(ValueError):
			cls.per_result(inp.equipment["EQ_CT"], D(1))  # thiếu m
		with self.assertRaises(ValueError):
			cls.per_result(replace(inp.equipment["EQ_CT"], mtb=None), D(1), D(1))
		with self.assertRaises(ValueError):
			cls.per_result(h, D(1))
		with self.assertRaises(ValueError):
			cls.per_result(replace(a, basis="?"), D(1))

	def test_linh_kien_gio_chay_va_dien(self):
		a = replace(
			self.inp.equipment["EQ_A"], components=(cls.ComponentInput(D("6000"), cls.LIFE_HOUR, D("100")),)
		)
		self.assertEqual(cls.part_per_result(a, D("30")), D("30.00"))
		with self.assertRaises(ValueError):
			cls.part_per_result(a)
		dat = replace(
			a,
			mode=resources.VENDOR,
			components=(cls.ComponentInput(D("6000"), cls.LIFE_RESULT, D("100"), True),),
		)
		self.assertEqual(cls.part_per_result(dat), D(0))
		b = self.inp.equipment["EQ_B"]
		self.assertEqual(cls.power_per_result(b, D(300), D(3000)), (D(0), "", D(0)))
		a2 = replace(
			self.inp.equipment["EQ_A"], power=replace(self.inp.equipment["EQ_A"].power, continuous=False)
		)
		self.assertEqual(
			cls.power_per_result(a2, D("300"), D("3000"))[0],
			cls.r2(D("1.2") * 0 + (D(2) * 8 + D("0.5") * 16) * 3000 * 300 / 300000),
		)


class TestNormLines(unittest.TestCase):
	def line(self, level, comp="SUPPLY", res="CUVET", attach="", attach_eq="", w="0", qty="1", **kw):
		return cls.ClsNormLine(
			engine.NormLine("X", "S1", comp, res, res, D(qty), wastage_rate=D(w)),
			level,
			False,
			attach,
			attach_eq,
			**kw,
		)

	def cost(self, line, rate=D("1200"), **sys_kw):
		s = with_system("GLU-A", **sys_kw)
		return cls.norm_line_cost(
			s, line, D("1.1"), engine.LineRate(rate, "p", warnings=("w1",)), f.service_input()
		)

	def test_cac_cap_phat_sinh(self):
		self.assertEqual(self.cost(self.line(cls.TUBE, w="0.5")).amount, D("450.00"))  # 1*1.5*1200/4
		self.assertEqual(self.cost(self.line(cls.BATCH)).amount, D("30.00"))
		self.assertEqual(self.cost(self.line(cls.DAY)).amount, D("30.00"))  # 1200*300/12000
		self.assertEqual(self.cost(self.line(cls.PERIOD)).amount, D("0.10"))
		self.assertEqual(self.cost(self.line(cls.RESULT)).amount, D("1200.00"))
		self.assertEqual(self.cost(self.line(cls.RESULT)).warning, "w1")
		l = self.cost(self.line(cls.DAY, attach=cls.ATTACH_EQUIP, attach_eq="EQ_B"))
		self.assertEqual((l.amount, l.divisor_label), (D("3.60"), "Qtb"))

	def test_dong_loai_tru_va_thanh_toan_rieng(self):
		s = with_system("GLU-A")
		ln = cls.ClsNormLine(
			engine.NormLine("X", "", "SUPPLY", "R", "R", D(1), excluded=True, exclude_reason="x"), cls.RESULT
		)
		self.assertEqual(cls.norm_line_cost(s, ln, D(1), None, f.service_input()).amount, D(0))
		l2 = self.line(cls.RESULT)
		out = cls.norm_line_cost(
			s, l2, D(1), engine.LineRate(D(5), "p", billed_separately=True), f.service_input()
		)
		self.assertEqual(out.amount, D(0))

	def test_thue_va_lien_doanh_loai_chi_phi(self):
		inp = f.service_input(rental_category="RENT_CAT", jv_category="JV_CAT")
		s = with_system("GLU-A")
		eqline = cls.ClsNormLine(engine.NormLine("L", "", "EQUIPMENT", "EQ_C", "EQ_C", D(1)), cls.RESULT)
		out = cls.norm_line_cost(s, eqline, D(1), None, inp)
		self.assertEqual((out.amount, out.cost_category), (D("1500.00"), "RENT_CAT"))
		inp2 = replace(
			inp, equipment={**inp.equipment, "EQ_C": replace(inp.equipment["EQ_C"], mode=resources.JOINT)}
		)
		self.assertEqual(cls.norm_line_cost(s, eqline, D(1), None, inp2).cost_category, "JV_CAT")

	def test_gio_ke_hoach(self):
		inp = f.service_input()
		a = replace(
			inp.equipment["EQ_A"], basis=resources.BASIS_HOURS, planned_hours=D("3000"), utilization=D("0.8")
		)
		inp = replace(inp, equipment={**inp.equipment, "EQ_A": a})
		s = with_system("GLU-A")
		ln = cls.ClsNormLine(engine.NormLine("L", "", "EQUIPMENT", "", "", D("30")), cls.RESULT)
		out = cls.norm_line_cost(s, ln, D(1), None, inp)
		self.assertEqual(out.divisor_label, "Giờ kế hoạch × hệ số sử dụng")  # noqa: RUF001


class TestSharesEqaLow(unittest.TestCase):
	def test_shares(self):
		a, b = with_system("GLU-A"), with_system("GLU-B")
		sh, src = cls.shares([a, b])
		self.assertEqual((sh["GLU-A"], src), (D("0.75"), cls.SHARE_FROM_RESULTS))
		a2 = replace(a, qbn=None, manual_share_pct=D(60))
		b2 = replace(b, qbn=None, manual_share_pct=D(40))
		sh, src = cls.shares([a2, b2])
		self.assertEqual((sh["GLU-A"], src), (D("0.6"), cls.SHARE_MANUAL))
		self.assertEqual(cls.shares([a2])[0], {"GLU-A": D(1)})

	def test_eqa_va_low_volume(self):
		self.assertEqual(
			cls.eqa_per_result([cls.EqaInput("E", D("24000000"), D("1200000"), D(1) / 21)], D("16000")),
			D("75.00"),
		)
		self.assertEqual(cls.eqa_per_result([], D(1)), D(0))
		self.assertFalse(cls.low_volume(D("12900"), (D(200), D(30))))
		self.assertFalse(cls.low_volume(D("4740"), (D(200), D(30))))
		self.assertTrue(cls.low_volume(D("1900"), (D(200), D(30))))
		self.assertEqual(cls.open_tests(D("1900"), D(30)), D("156.16"))
		self.assertEqual(cls.vn(D("1234.5")), "1.234,50")


class TestValidate(unittest.TestCase):
	def err(self, inp):
		return cls.validate(inp, "GLU", "XN")

	def test_hop_le(self):
		self.assertEqual(self.err(f.service_input()), [])

	def test_TC_CLS_15_a_thieu_san_luong(self):
		inp = f.service_input(
			systems=(f.system("GLU-A"), f.system("GLU-B", qbn=None, has_volume=False, manual_share_pct=D(25)))
		)
		inp = replace(inp, systems=(replace(inp.systems[0], manual_share_pct=D(75)), inp.systems[1]))
		r = f.cost(inp=inp)
		self.assertEqual(r.status, "Lỗi")
		self.assertIn("Hệ thống GLU-B thiếu sản lượng năm 2026, kịch bản Thực tế 12 tháng", r.message)

	def test_TC_CLS_15_b_qbn_bang_0(self):
		inp = f.service_input(
			systems=(
				f.system("GLU-A", qbn=D(0), manual_share_pct=D(75)),
				f.system("GLU-B", manual_share_pct=D(25)),
			)
		)
		r = f.cost(inp=inp)
		self.assertEqual(r.status, "Lỗi")
		self.assertIn("Hệ thống GLU-A có số kết quả trả bằng 0", r.message)

	def test_TC_CLS_15_c_thieu_co_me(self):
		inp = f.service_input(systems=(f.system("GLU-A", batch=None), f.system("GLU-B")))
		r = f.cost(inp=inp)
		self.assertEqual(r.status, "Lỗi")
		self.assertIn("Hệ thống GLU-A có dòng Theo mẻ (L04) nhưng thiếu cỡ mẻ bình quân", r.message)

	def test_TC_CLS_15_d_tong_ty_trong_90(self):
		a = f.system("GLU-A", qbn=None, has_volume=False, manual_share_pct=D(60))
		b = f.system("GLU-B", qbn=None, has_volume=False, manual_share_pct=D(30))
		r = f.cost(inp=f.service_input(systems=(a, b)))
		self.assertEqual(r.status, "Lỗi")
		self.assertIn(
			"Tổng tỷ trọng sản lượng các hệ thống của dịch vụ GLU tại khoa XN là 90%, khác 100%", r.message
		)

	def test_cac_loi_khac(self):
		inp = f.service_input()
		a = f.system("GLU-A")
		cases = {
			"chưa có bộ định mức Đã khóa": f.system("GLU-A", norm_set=None),
			"Theo ống mẫu nhưng thiếu số xét nghiệm": f.system("GLU-A", tests_per_tube=None),
			"thiếu số ngày chạy máy": f.system("GLU-A", run_days=None),
			"dòng thiếu đơn giá: L02": f.system(
				"GLU-A", rates={k: v for k, v in a.rates.items() if k != "L02"}
			),
			"vật liệu nội kiểm QC_L thiếu đơn giá": f.system("GLU-A", iqc=(replace(a.iqc[0], rate=None),)),
			"hao hụt từ 100%": f.system("GLU-A", actual=cls.AuxCounts(h=D(1))),
		}
		for text, s in cases.items():
			self.assertTrue(any(text in e for e in self.err(replace(inp, systems=(s,)))), text)

	def test_loi_thiet_bi(self):
		inp = f.service_input(systems=(f.system("GLU-A"),))
		e = inp.equipment
		for text, eq in (
			("thiếu Qtb", replace(e["EQ_A"], qtb=None)),
			("thiếu giờ khai thác kế hoạch", replace(e["EQ_A"], basis=resources.BASIS_HOURS)),
			("thiếu phút khai thác (Mtb)", replace(e["EQ_A"], basis=resources.BASIS_MINUTE, mtb=None)),
		):
			errs = self.err(replace(inp, equipment={**e, "EQ_A": eq}))
			self.assertTrue(any(text in x for x in errs), text)
		errs = self.err(
			replace(inp, equipment={**e, "EQ_A": replace(e["EQ_A"], basis=resources.BASIS_MINUTE, mtb=D(5))})
		)
		self.assertTrue(any("thiếu số phút chiếm máy một ca" in x for x in errs))
		self.assertTrue(any("không có dữ liệu" in x for x in self.err(replace(inp, equipment={}))))

	def test_loi_du_lieu_thiet_bi_hong_la_loi_dich_vu(self):
		inp = f.service_input(systems=(f.system("GLU-A"),))
		bad = replace(inp.equipment["EQ_A"], life_years=D(0))
		r = f.cost(inp=replace(inp, equipment={**inp.equipment, "EQ_A": bad}))
		self.assertEqual(r.status, "Lỗi")
		self.assertTrue(r.message.startswith("Thiết bị:"))


class TestCostService(unittest.TestCase):
	def test_TC_CLS_37_V8_san_luong_thap(self):
		for total_qbn, low in ((D("12000"), False), (D("1000"), True)):
			s = f.system("GLU-A", qbn=total_qbn, actual=cls.AuxCounts(D(0), D(0), D(0), D(0), D(0)))
			r = f.cost(inp=f.service_input(systems=(s,)))
			self.assertEqual(r.test_system_costs[0].low_volume_warning, low)
			self.assertEqual(r.status, "Cảnh báo" if low else "Thành công")
		self.assertIn("Sản lượng thấp: GLU-A", r.message)
		self.assertTrue(cls.low_volume(D("1900"), (D(200), D(30))))

	def test_TC_CLS_51_san_luong_16000(self):
		r = f.cost()
		self.assertEqual(r.volume, D("16000"))
		inp = replace(f.service(), volume=D("15800"))
		self.assertEqual(engine.cost_service(inp, f.PARAMS).volume, D("16000"))
		seen = {}

		def allocate(costed):
			seen.update({x.service: x.volume for x in costed})
			return {}

		out = runner.run(
			[{"service": "GLU", "department": "XN", "norm_set": ""}],
			lambda e: inp,
			f.PARAMS,
			allocate=allocate,
		)
		self.assertEqual(seen["GLU"], D("16000"))
		self.assertEqual(out[0].volume, D("16000"))
		self.assertTrue(out[0].is_paraclinical)

	def test_ngoai_kiem_va_loai_chi_phi(self):
		inp = f.service_input(eqa_category="UTILITY")
		r = f.cost(inp=inp)
		self.assertEqual(
			r.direct_by_category["UTILITY"] - f.cost().direct_by_category.get("UTILITY", D(0)), D("75.00")
		)
		self.assertEqual(sum(r.direct_by_component.values()), r.direct_total)
		self.assertTrue(any(x.line_origin == cls.ORIGIN_EQA for x in r.lines))

	def test_khong_ngoai_kiem(self):
		r = f.cost(inp=f.service_input(eqa=()))
		self.assertEqual(r.eqa_cost, D(0))
		self.assertFalse(any(x.line_origin == cls.ORIGIN_EQA for x in r.lines))

	def test_group_by_system(self):
		groups = cls.group_by_system(f.cost().lines)
		self.assertEqual([g["test_system"] for g in groups], ["GLU-A", "GLU-B", ""])

	def test_engine_cost_category_va_dich_vu_thuong(self):
		ln = engine.CostLine(engine.LINE_DIRECT, "DRUG", D(5), cost_category="UTILITY")
		res = engine.cost_service(engine.ServiceInput("S", "D", "N", (), {}), f.PARAMS, lambda inp: [ln])
		self.assertEqual(res.direct_by_category, {"UTILITY": D(5)})
		self.assertFalse(res.is_paraclinical)
		fin = engine.finish_service(f.cost(), [], f.PARAMS)
		self.assertTrue(fin.is_paraclinical)
		self.assertEqual(len(fin.test_system_costs), 2)


if __name__ == "__main__":
	unittest.main()
