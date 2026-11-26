"""Đơn vị đối soát vật chất, sản lượng (FEAT-037; BR-CLS-014, 015; FR-COST-026..029)."""

import unittest
from dataclasses import replace
from decimal import Decimal as D

from normcore.costing import cls, engine
from normcore.costing import reconcile as r


def ln(lid, level, resource="IT", qty="1", apply_k=False, comp="DRUG", wastage="0", excluded=False):
	n = engine.NormLine(lid, "", comp, resource, resource, D(qty), wastage_rate=D(wastage), excluded=excluded)
	return cls.ClsNormLine(n, level, apply_k)


def system(lines, iqc=(), qbn="1000", k_actual=True):
	a = cls.AuxCounts(D(0), D(0), D(0), D(0), D(0)) if k_actual else cls.AuxCounts()
	return cls.TestSystemInput(
		code="S", norm_set=None, equipment="E", qbn=D(qbn), actual=a, run_days=D(300), batch=D(10),
		tests_per_tube=D(4), lines=tuple(lines), iqc=tuple(iqc),
	)


def service(systems, dept="XN"):
	c = cls.ClsServiceInput("Thực tế 12 tháng", 2026, tuple(systems), {})
	return engine.ServiceInput("SV", dept, "", (), {}, None, c)


class TestQuantities(unittest.TestCase):
	def q(self, lines, **kw):
		return r.material_quantities([service([system(lines, **kw)])])

	def test_result_k_va_khong_k(self):
		q = self.q([ln("L1", "RESULT", "A", "2", True), ln("L2", "RESULT", "B", "3")])
		self.assertEqual(q[("XN", "A")], D("2") * D("1000"))  # k = 1 khi không có test phụ
		self.assertEqual(q[("XN", "B")], D("3000"))

	def test_tube_batch_day_period(self):
		q = self.q(
			[
				ln("L1", "TUBE", "T", "1", wastage="0.1"),
				ln("L2", "BATCH", "B", "1"),
				ln("L3", "DAY", "D", "2"),
				ln("L4", "PERIOD", "P", "5", wastage="0.2"),
			]
		)
		self.assertEqual(q[("XN", "T")], D("1.1") * 1000 / 4)
		self.assertEqual(q[("XN", "B")], D(100))
		self.assertEqual(q[("XN", "D")], D(600))
		self.assertEqual(q[("XN", "P")], D("6.0"))

	def test_noi_kiem_va_bo_qua(self):
		iqc = [cls.IqcLine("QC", D(2), D(3), D(1), D(2))]
		q = self.q(
			[ln("L1", "RESULT", "L", comp="LABOR"), ln("L2", "RESULT", "X", excluded=True), ln("L3", "RESULT", "", )],
			iqc=iqc,
		)
		self.assertEqual(q, {("XN", "QC"): D(2) * 3 * 300 / 2 * 1})

	def test_khong_phai_can_lam_sang_va_cong_don(self):
		plain = engine.ServiceInput("SV", "XN", "", (), {}, D(1), None)
		two = [service([system([ln("L1", "RESULT", "A")])]), service([system([ln("L1", "RESULT", "A")])])]
		self.assertEqual(r.material_quantities([plain] + two), {("XN", "A"): D(2000)})


class TestRows(unittest.TestCase):
	def rows(self, calc, issued, units=None, meta=None, has=("XN",), tol=5):
		return r.material_rows(calc, issued, units or {}, meta or {}, has, tol)

	def test_TC_CLS_17_V6_xuat_100_hop(self):
		row = self.rows({("XN", "HC"): D("18185.56")}, {("XN", "HC"): D(100)}, {"HC": D(200)})[0]
		self.assertEqual((row.actual, row.variance_pct, row.over_tolerance), (D(20000), D("9.07"), True))

	def test_ngung_bang_khong_vuot(self):
		row = self.rows({("XN", "HC"): D(95)}, {("XN", "HC"): D(100)})[0]
		self.assertEqual((row.variance_pct, row.over_tolerance), (D("5.00"), False))

	def test_khoa_chua_doi_soat(self):
		rows = self.rows({("XN", "HC"): D(5), ("HH", "HC"): D(5)}, {("HH", "HC"): D(5)}, has=("HH",))
		self.assertEqual([(x.department, x.item, x.status) for x in rows], [("HH", "HC", r.RECONCILED), ("XN", None, r.UNRECONCILED)])
		self.assertFalse(rows[1].over_tolerance)

	def test_thieu_xuat_kho_hoac_don_vi(self):
		rows = self.rows(
			{("XN", "A"): D(5), ("XN", "B"): D(5), ("XN", "C"): D(0)},
			{("XN", "B"): D(1), ("XN", "Z"): D(9)},
			meta={"B": {"norm_required": True}},
		)
		self.assertEqual([(x.item, x.status) for x in rows], [("A", r.UNRECONCILED), ("B", r.UNRECONCILED)])
		self.assertEqual([x.note for x in rows], ["Không có dòng xuất kho", "Thiếu số đơn vị định mức"])
		zero = self.rows({("XN", "A"): D(5)}, {("XN", "A"): D(0)})[0]
		self.assertEqual(zero.status, r.UNRECONCILED)


class TestVolume(unittest.TestCase):
	def test_V7(self):
		a = r.volume_rows({("GLU", "XN"): D(16000)}, {("GLU", "XN"): D(15800)}, 2)[0]
		b = r.volume_rows({("GLU", "XN"): D(16000)}, {("GLU", "XN"): D(15500)}, 2)[0]
		self.assertEqual((a.variance_pct, a.over_tolerance), (D("1.27"), False))
		self.assertEqual((b.variance_pct, b.over_tolerance), (D("3.23"), True))

	def test_HIS_thieu_hoac_0(self):
		rows = r.volume_rows({("A", "XN"): D(5), ("B", "XN"): D(5)}, {("B", "XN"): D(0)}, 2)
		self.assertTrue(all(x.over_tolerance and x.variance_pct is None for x in rows))
		self.assertEqual(rows[0].note, "Thiếu sản lượng HIS")


class TestBlockers(unittest.TestCase):
	def test_luat(self):
		f = dict(cost_center="K1", cost_category="LABOR", over_tolerance=1)
		m = dict(recon_type="Vật chất", department="XN", item="HC", over_tolerance=1)
		u = dict(recon_type="Vật chất", department="XN", item=None, recon_status="Chưa đối soát")
		v = dict(recon_type="Sản lượng", over_tolerance=1)
		self.assertEqual(r.lock_blockers([f, m, u, v]), ["K1 · LABOR", "Vật chất · XN · HC", "Vật chất · XN · Chưa đối soát"])
		ok = [dict(x, explanation="  lý do ") for x in (f, m, u)]
		self.assertEqual(r.lock_blockers(ok), [])
		self.assertFalse(r.needs_explanation(dict(m, over_tolerance=0)))
		self.assertTrue(r.needs_explanation(dict(m, explanation="  ")))
