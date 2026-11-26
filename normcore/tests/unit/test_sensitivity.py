"""Đơn vị costing/sensitivity.py (FEAT-037; FR-COST-030, TC-CLS-40 phần thuần)."""

import unittest
from decimal import Decimal as D

from normcore.costing import cls, resources, snapshot
from normcore.costing import sensitivity as s
from normcore.tests.golden import cls_fixture as f


def snap():
	return snapshot.build([f.service()], f.PARAMS)


def total(r):
	return r.price.full_cost


class TestSensitivity(unittest.TestCase):
	def run_(self, **ov):
		return s.trial(snap(), "GLU", "XN", ov, {"HC_GLU": D(200)})

	def test_Qbn_GLU_A_6000_khac_goc_va_dau_vao_khong_doi(self):
		sn = snap()
		before = snapshot.dumps(sn)
		base = snapshot.reproduce(sn)[0]
		t = s.trial(sn, "GLU", "XN", {"system_volumes": {"GLU-A": 6000}}, {})
		self.assertNotEqual(total(t), total(base))
		self.assertEqual(t.volume, D(6000) + D(f.system("GLU-B").qbn))
		self.assertEqual(snapshot.dumps(sn), before)

	def test_san_luong_0_bao_loi(self):
		for bad in (0, -1, "abc", "nan"):
			with self.assertRaisesRegex(s.InvalidAssumption, "Sản lượng giả định phải lớn hơn 0"):
				self.run_(system_volumes={"GLU-A": bad})

	def test_gia_cao_hon_tang_gia_thanh(self):
		base = total(snapshot.reproduce(snap())[0])
		hi = total(self.run_(prices={"HC_GLU": 100000000}))
		self.assertGreater(hi, base)

	def test_loi_gia_dinh(self):
		cases = [
			({}, "Nhập ít nhất một giả định"),
			({"prices": {"HC_GLU": -1}}, "Đơn giá giả định không được âm"),
			({"prices": {"ZZZ": 1}}, "ZZZ không thuộc dịch vụ này"),
			({"system_volumes": {"ZZZ": 5}}, "ZZZ không thuộc dịch vụ này"),
			({"equipment_modes": {"EQ_A": {"mode": "Khác"}}}, "Hình thức có máy không hợp lệ"),
			({"equipment_modes": {"EQ_A": {"mode": resources.RENT}}}, "Nhập chi phí năm theo hợp đồng"),
			({"equipment_modes": {"ZZ": {"mode": resources.BUY}}}, "ZZ không thuộc dịch vụ này"),
			({"volume": 5}, "nhập sản lượng theo hệ thống"),
		]
		for ov, msg in cases:
			with self.assertRaisesRegex(s.InvalidAssumption, msg):
				self.run_(**ov)

	def test_hinh_thuc_co_may_thue(self):
		base = total(snapshot.reproduce(snap())[0])
		t = self.run_(equipment_modes={"EQ_A": {"mode": resources.RENT, "contract_cost": 900000000}})
		self.assertNotEqual(total(t), base)

	def test_mua_thieu_nguyen_gia(self):
		inp = f.service()
		c = inp.paraclinical
		eqs = dict(c.equipment)
		from dataclasses import replace

		eqs["EQ_A"] = replace(eqs["EQ_A"], original_cost=None, mode=resources.RENT, contract_cost=D(1))
		inp = replace(inp, paraclinical=replace(c, equipment=eqs))
		with self.assertRaisesRegex(s.InvalidAssumption, "chưa có nguyên giá"):
			s.apply(inp, {"equipment_modes": {"EQ_A": {"mode": resources.BUY}}}, {})

	def test_dich_vu_thuong_va_khong_co(self):
		from normcore.costing import engine

		plain = engine.ServiceInput(
			"SV",
			"K",
			"NS",
			(engine.NormLine("L1", "S", "DRUG", "IT", "Thuốc", D(1)),),
			{"L1": engine.LineRate(D(10), "src")},
			D(100),
		)
		out = s.apply(plain, {"volume": 50, "prices": {"IT": 20}}, {"IT": D(2)})
		self.assertEqual((out.volume, out.rates["L1"].rate), (D(50), D("10.0000")))
		self.assertIn("giả định", out.rates["L1"].source)
		self.assertEqual(plain.volume, D(100))
		with self.assertRaisesRegex(s.InvalidAssumption, "không có trong lần tính"):
			s.trial(snap(), "XX", "YY", {"volume": 1}, {})
