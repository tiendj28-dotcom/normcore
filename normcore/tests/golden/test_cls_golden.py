"""Golden FEAT-036: costing/cls.py khớp docs/golden/golden_cls.py (TC-CLS-01..14) và số mục 2A của test-cases.md."""

import unittest
from datetime import date
from decimal import Decimal as D

from normcore.costing import cls, engine, resources
from normcore.tests.golden import cls_fixture as f

g = f.g


def by_id(result, system):
	return {x.norm_line_id: x for x in result.lines if x.test_system == system}


def golden_by_id(code, mode="ASSET", **kw):
	lines = g.system_lines(code, mode, **kw)[0]
	out, n = {}, {}
	for lid, _level, _comp, _res, amt, _note in lines:
		n[lid] = n.get(lid, 0) + 1
		out[
			lid
			if lid in ("L01", "L02", "L03", "L04", "L05", "L06", "L07", "EQ-P", "EQ-E")
			else f"{lid}{n[lid]}"
		] = amt
	return out


class TestClsGolden(unittest.TestCase):
	def test_TC_CLS_01_k_GLU_A(self):
		s = f.system("GLU-A")
		inp = f.service_input()
		qnk, qcal, qrerun, qeqa, h, est = cls.aux_counts(s)
		k, total = cls.k_factor(s.qbn, qnk, qcal, qrerun, qeqa, h)
		self.assertEqual((k, total, est), (D("1.108247"), D("12900"), False))
		self.assertEqual(k, g.k_factor("GLU-A")[0])
		# chạy lại cho cùng giá trị
		r1, r2 = cls.cost_service(f.service(inp), f.PARAMS), cls.cost_service(f.service(inp), f.PARAMS)
		self.assertEqual(r1.test_system_costs[0].k_factor, D("1.108247"))
		self.assertEqual(r1, r2)

	def test_TC_CLS_02_k_GLU_B_uoc_tinh(self):
		s = f.system("GLU-B")
		qnk, qcal, qrerun, qeqa, h, est = cls.aux_counts(s)
		self.assertEqual((qnk, qcal, qrerun, qeqa), (D("600"), D("48"), D("80"), D("12")))
		k, total = cls.k_factor(s.qbn, qnk, qcal, qrerun, qeqa, h)
		self.assertEqual((k, total, est), (D("1.221649"), D("4740"), True))
		r = f.cost()
		lines = by_id(r, "GLU-B")
		self.assertEqual(lines["L02"].divisor_source, "Ước tính từ kế hoạch")
		self.assertEqual(lines["L01"].divisor_source, "Thực tế")
		self.assertTrue(r.test_system_costs[1].k_estimated)

	def test_TC_CLS_03_dong_nhan_k_khong_hao_hut(self):
		r = f.cost()
		for sysc, l2, l3 in (("GLU-A", "33247.41", "1329.90"), ("GLU-B", "36649.47", "1465.98")):
			self.assertEqual(by_id(r, sysc)["L02"].amount, D(l2))
			self.assertEqual(by_id(r, sysc)["L03"].amount, D(l3))
		# hao hụt của dòng không áp cho dòng nhân k
		f.service_input()
		s = f.system("GLU-A")
		lines = tuple(
			cls.ClsNormLine(
				engine.NormLine(
					x.norm.line_id,
					"",
					x.norm.component,
					x.norm.resource,
					x.norm.resource_label,
					x.norm.hospital_qty,
					wastage_rate=D("0.05"),
				),
				x.cost_level,
				x.apply_k,
				x.attach,
				x.attach_equipment,
				x.is_main_reagent,
				x.nominal_tests,
				x.open_days,
			)
			for x in s.lines
		)
		s2 = f.system("GLU-A", lines=lines)
		r2 = f.cost(inp=f.service_input(systems=(s2,)))
		self.assertEqual(by_id(r2, "GLU-A")["L02"].amount, D("33247.41"))

	def test_TC_CLS_04_ong_mau_va_me(self):
		r = f.cost()
		for sysc in ("GLU-A", "GLU-B"):
			self.assertEqual(by_id(r, sysc)["L01"].amount, D("1500.00"))
			self.assertEqual(by_id(r, sysc)["L04"].amount, D("1250.00"))

	def test_TC_CLS_05_ngay_may_gan_thiet_bi(self):
		r = f.cost()
		self.assertEqual(by_id(r, "GLU-A")["L05"].amount, D("120.00"))
		self.assertEqual(by_id(r, "GLU-B")["L05"].amount, D("360.00"))

	def test_TC_CLS_06_noi_kiem_chat_chuan(self):
		r = f.cost()
		a, b = by_id(r, "GLU-A"), by_id(r, "GLU-B")
		self.assertEqual((a["QC-N1"].amount, b["QC-N1"].amount), (D("90.00"), D("270.00")))
		self.assertEqual((a["QC-C1"].amount, b["QC-C1"].amount), (D("400.00"), D("1200.00")))
		self.assertEqual(a["QC-N1"].line_origin, "Kế hoạch chất lượng")

	def test_TC_CLS_07_theo_gia_tri_tai_san(self):
		inp = f.service_input()
		a, b = inp.equipment["EQ_A"], inp.equipment["EQ_B"]
		self.assertEqual(cls.compliance_annual(a, cls._peers(a, inp), "ASSET"), D("10500000"))
		self.assertEqual(cls.compliance_annual(b, cls._peers(b, inp), "ASSET"), D("3500000"))
		self.assertEqual(cls.equipment_annual(a, inp)[0], D("514500000"))
		self.assertEqual(cls.equipment_annual(b, inp)[0], D("3500000"))
		r = f.cost(inp=inp)
		self.assertEqual(by_id(r, "GLU-A")["L07"].amount, D("1715.00"))
		self.assertEqual(by_id(r, "GLU-B")["L07"].amount, D("35.00"))

	def test_TC_CLS_08_V1_gan_truc_tiep(self):
		inp = f.service_input(mode=cls.ALLOC_DIRECT)
		a, b = inp.equipment["EQ_A"], inp.equipment["EQ_B"]
		self.assertEqual(cls.compliance_annual(a, [], "DIRECT"), D("8000000"))
		self.assertEqual(cls.compliance_annual(b, [], "DIRECT"), D("6000000"))
		r = f.cost(inp=inp)
		self.assertEqual(by_id(r, "GLU-A")["L07"].amount, D("1706.67"))
		self.assertEqual(by_id(r, "GLU-B")["L07"].amount, D("60.00"))
		self.assertEqual(r.direct_total, g.service_direct(mode="DIRECT")[3])
		self.assertEqual(r.direct_total, D("42278.67"))

	def test_TC_CLS_09_linh_kien_dien(self):
		r = by_id(f.cost(), "GLU-A")
		self.assertEqual(r["EQ-P"].amount, D("300.00"))
		self.assertEqual(r["EQ-E"].amount, D("87.60"))

	def test_TC_CLS_10_dich_vu_GLU(self):
		r = f.cost()
		per, weighted, eqa, direct, qsum = g.service_direct()
		self.assertEqual([t.direct_cost for t in r.test_system_costs], [D("41531.03"), D("44221.57")])
		self.assertEqual([t.direct_cost for t in r.test_system_costs], [per["GLU-A"], per["GLU-B"]])
		self.assertEqual([t.share_pct for t in r.test_system_costs], [D("75"), D("25")])
		self.assertEqual(r.test_system_costs[0].share_source, "Từ số kết quả trả")
		self.assertEqual((weighted, eqa, direct), (D("42203.67"), D("75.00"), D("42278.67")))
		self.assertEqual(r.eqa_cost, eqa)
		self.assertEqual(r.direct_total, direct)
		self.assertEqual(sum(r.direct_by_component.values()), direct)
		self.assertEqual(sum(r.direct_by_category.values()), direct)
		self.assertEqual(r.volume, qsum)

	def test_TC_CLS_11_V2_het_thoi_gian_su_dung(self):
		late = date(2033, 1, 1)
		for mode, expect in (("ZERO", "515.00"), ("CONTINUE", "1715.00")):
			r = f.cost(on=late, expired_mode=mode)
			l7 = by_id(r, "GLU-A")["L07"]
			self.assertEqual(l7.amount, D(expect))
			self.assertEqual(
				l7.amount, g.per_result("EQ_A", g.equipment_annual("EQ_A", on=late, expired_mode=mode))
			)
			self.assertIn(f"({mode})", l7.warning)

	def test_TC_CLS_12_V3_may_thue(self):
		inp = f.service_input()
		eq = inp.equipment["EQ_C"]
		amount, label, value = cls.per_result(eq, cls.equipment_annual(eq, inp)[0])
		self.assertEqual(amount, D("1500.00"))
		self.assertEqual((label, value), ("Qtb", D("300000")))
		self.assertEqual(cls.equipment_annual(eq, inp)[1], [])

	def test_TC_CLS_13_V4_phut_chiem_may(self):
		inp = f.service_input()
		eq = inp.equipment["EQ_CT"]
		annual = cls.equipment_annual(eq, inp)[0]
		self.assertEqual(annual, D("3640000000"))
		self.assertEqual(cls.r4(annual / eq.mtb), D("20222.2222"))
		self.assertEqual(cls.per_result(eq, annual, D("10"))[0], D("202222.22"))
		self.assertEqual(cls.per_result(eq, annual, D("20"))[0], D("404444.44"))

	def test_TC_CLS_14_V5_khong_khau_hao(self):
		inp = f.service_input(include_depr=False)
		a = inp.equipment["EQ_A"]
		annual, notes = cls.equipment_annual(a, inp)
		self.assertEqual(cls.per_result(a, annual)[0], D("515.00"))
		self.assertEqual(notes, [engine.DEPR_EXCLUDED_WARNING])
		c = inp.equipment["EQ_C"]
		self.assertEqual(cls.per_result(c, cls.equipment_annual(c, inp)[0])[0], D("1500.00"))
		r = f.cost(inp=inp)
		self.assertIn("Khấu hao bị loại", by_id(r, "GLU-A")["L07"].warning)

	def test_khop_tung_dong_golden(self):
		r = f.cost()
		for code in ("GLU-A", "GLU-B"):
			got = {k: v.amount for k, v in by_id(r, code).items()}
			want = {}
			for lid, _level, _comp, _res, amt, _note in g.system_lines(code)[0]:
				if lid in ("EQ-P", "EQ-E") and amt == 0:
					continue  # golden ghi dòng 0; mã không sinh dòng khi không có linh kiện hay công suất
				want["QC-N1" if lid == "QC-N" else "QC-C1" if lid == "QC-C" else lid] = amt
			self.assertEqual(got, want)

	def test_nguon_mau_so_moi_dong(self):
		for ln in f.cost().lines:
			self.assertTrue(
				ln.cost_level and ln.divisor_label and ln.divisor_value is not None and ln.divisor_source
			)


if __name__ == "__main__":
	unittest.main()
