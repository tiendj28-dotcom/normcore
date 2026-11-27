"""Golden FEAT-037: costing/reconcile.py khớp golden_cls.material_recon, volume_recon (TC-CLS-16..18)."""

import unittest
from decimal import Decimal as D

from normcore.costing import reconcile as r
from normcore.tests.golden import cls_fixture as f

g = f.g
PARAM = g.PARAM


def calc_glu():
	inp = f.service()
	return r.material_quantities([inp]), inp


def rows_for(issued_boxes, tol=None):
	calc, _ = calc_glu()
	return r.material_rows(
		calc,
		{("XN", "HC_GLU"): D(issued_boxes)},
		{"HC_GLU": D(g.ITEM["HC_GLU"]["units"])},
		{"HC_GLU": {"norm_required": True}},
		["XN"],
		tol if tol is not None else PARAM["material_tol"],
	)


def glu_row(rows):
	return next(x for x in rows if x.item == "HC_GLU")


class TestReconcileClsGolden(unittest.TestCase):
	def test_TC_CLS_16_V6_xuat_94_hop(self):
		calc, _ = calc_glu()
		gcalc, gissued, gpct, gover = g.material_recon("HC_GLU", 94)
		row = glu_row(rows_for(94))
		self.assertEqual(calc[("XN", "HC_GLU")], gcalc)
		self.assertEqual(row.calculated.quantize(D("0.01")), D("18185.56"))
		self.assertEqual((row.actual, row.variance_pct, row.over_tolerance), (gissued, gpct, gover))
		self.assertEqual((row.actual, row.variance_pct, row.over_tolerance), (D("18800"), D("3.27"), False))

	def test_TC_CLS_17_V6_xuat_100_hop_golden(self):
		_, gissued, gpct, gover = g.material_recon("HC_GLU", 100)
		row = glu_row(rows_for(100))
		self.assertEqual((row.actual, row.variance_pct, row.over_tolerance), (gissued, gpct, gover))
		self.assertEqual((row.variance_pct, row.over_tolerance), (D("9.07"), True))
		line = dict(recon_type=r.MATERIAL, department="XN", item="HC_GLU", over_tolerance=1, explanation="")
		self.assertEqual(r.lock_blockers([line]), ["Vật chất · XN · HC_GLU"])

	def test_TC_CLS_18_V7_san_luong(self):
		results = f.service().paraclinical  # 16.000 kết quả = tổng Qbn của GLU-A và GLU-B
		total = sum((D(s.qbn) for s in results.systems), D(0))
		self.assertEqual(total, D(16000))
		for his in (15800, 15500):
			gpct, gover = g.volume_recon(D(16000), D(his))
			row = r.volume_rows({("GLU", "XN"): total}, {("GLU", "XN"): D(his)}, PARAM["volume_tol"])[0]
			self.assertEqual((row.variance_pct, row.over_tolerance), (gpct, gover))
		warn = r.volume_rows({("GLU", "XN"): total}, {("GLU", "XN"): D(15500)}, PARAM["volume_tol"])[0]
		self.assertEqual((warn.variance_pct, warn.over_tolerance), (D("3.23"), True))
		line = dict(recon_type=r.VOLUME, over_tolerance=int(warn.over_tolerance), explanation="")
		self.assertEqual(r.lock_blockers([line]), [])
		ok = r.volume_rows({("GLU", "XN"): total}, {("GLU", "XN"): D(15800)}, PARAM["volume_tol"])[0]
		self.assertEqual((ok.variance_pct, ok.over_tolerance), (D("1.27"), False))
