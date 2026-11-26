"""Đơn vị costing/missing_data.py (FEAT-037; FR-OUT-012)."""

import unittest
from decimal import Decimal as D

from normcore.costing import engine
from normcore.costing import missing_data as m
from normcore.tests.golden import cls_fixture as f


def plain(service, rate=True, volume="100", excluded=False):
	line = engine.NormLine("L1", "S", "DRUG", "IT", "Thuốc", D(1), excluded=excluded)
	rates = {"L1": engine.LineRate(D(10), "s")} if rate else {"L1": None}
	return engine.ServiceInput(service, "K", "NS", (line,), rates, D(volume) if volume else None)


class TestCollect(unittest.TestCase):
	def test_khong_thieu_gi(self):
		self.assertEqual(m.collect([m.PairData("A", "K", plain("A"))]), [])
		self.assertEqual(m.collect([]), [])

	def test_nam_loai_va_thu_tu(self):
		pairs = [
			m.PairData("B", "K", plain("B", volume=None)),
			m.PairData("A", "K", plain("A", rate=False), has_time_study=False, norm_lines_basis={"L2": "Bấm giờ", "L3": "Định mức"},
				missing_compliance=(("EQ1", "Kiểm định"),)),
			m.PairData("C", "K", None, systems_without_plan=("S1",), systems_without_volume=("S2",)),
		]
		got = [(g.service, g.kind, g.detail) for g in m.collect(pairs)]
		self.assertEqual(
			got,
			[
				("A", m.PRICE, "L1 · Thuốc"),
				("A", m.TIME_STUDY, "Dòng L2"),
				("A", m.COMPLIANCE, "EQ1 · Kiểm định"),
				("B", m.VOLUME, "Sản lượng năm"),
				("C", m.VOLUME, "Hệ thống S2"),
				("C", m.QC_PLAN, "Hệ thống S1"),
			],
		)

	def test_loai_tru_khong_thieu_gia_va_khong_bam_gio_neu_khong_dong(self):
		p = m.PairData("A", "K", plain("A", rate=False, excluded=True), has_time_study=False, norm_lines_basis={"L1": "Định mức"})
		self.assertEqual(m.collect([p]), [])

	def test_chan_doan_hinh_anh_khong_can_ke_hoach(self):
		p = m.PairData("A", "K", None, systems_without_plan=("S1",), imaging=True)
		self.assertEqual(m.collect([p]), [])

	def test_can_lam_sang_thieu_don_gia_he_thong_va_noi_kiem(self):
		from dataclasses import replace

		inp = f.service()
		c = inp.paraclinical
		s0 = c.systems[0]
		rates = dict(s0.rates)
		rates["L02"] = None
		iqc = (replace(s0.iqc[0], rate=None),) + s0.iqc[1:]
		c = replace(c, systems=(replace(s0, rates=rates, iqc=iqc),) + c.systems[1:])
		inp = replace(inp, paraclinical=c)
		got = [g.detail for g in m.collect([m.PairData("GLU", "XN", inp)])]
		self.assertTrue(any(d.startswith("GLU-A · L02") for d in got), got)
		self.assertTrue(any("nội kiểm" in d for d in got), got)
		self.assertEqual(m.collect([m.PairData("GLU", "XN", f.service())]), [])
