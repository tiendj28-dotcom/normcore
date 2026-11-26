"""Golden FEAT-012: lượng áp dụng (TC-NORM-03, BR-COST-007) và chi phí tạm tính DV01 (FR-NORM-016, BR-COST-002..006).
Số lấy từ docs/golden/golden_engine.py, không chép vào test."""

import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing import engine
from normcore.costing.provisional import line_amount, summarize

SVC = "DV-TEST-A"  # dịch vụ DV01 của bộ dữ liệu vàng (11 dòng L01..L11)


def _by_id(svc):
	return {ln.line_id: ln for ln in g.NORMS[svc]}


def _rate(ln):
	"""Đơn giá một đơn vị định mức lấy từ các hàm đơn giá của golden."""
	if ln.comp == "LABOR":
		return g.job_rate(ln.res)[1]
	if ln.comp in ("DRUG", "SUPPLY", "UTILITY"):
		return g.ITEM[ln.res]["price"]
	if ln.comp == "EQUIPMENT":
		return g.equip_rate(ln.res)[1]
	return g.room_rate(ln.res)


def _amount(ln):
	q = engine.applied_qty(ln.qty, ln.authority)
	reuse = g.ITEM[ln.res]["reuse"] if ln.comp in ("DRUG", "SUPPLY") else 1
	return line_amount(
		ln.comp, q, _rate(ln), headcount=ln.headcount, wastage_rate=ln.wastage, reuse_count=reuse
	)


class TestNormGolden(unittest.TestCase):
	def test_TC_NORM_03_luong_ap_dung_L03_L09_L01(self):
		d = _by_id(SVC)
		self.assertEqual(engine.applied_qty(d["L03"].qty, d["L03"].authority), D("20"))
		self.assertEqual(engine.applied_qty(d["L09"].qty, d["L09"].authority), D("10"))
		self.assertEqual(engine.applied_qty(d["L01"].qty, d["L01"].authority), D("10"))
		for ln in g.NORMS[SVC]:
			self.assertEqual(engine.applied_qty(ln.qty, ln.authority), g.applied_qty(ln))

	def test_FR_NORM_016_11_dong_khop_direct_lines(self):
		golden = g.direct_lines(SVC)
		self.assertEqual(len(golden), 11)
		for ln, _q, _rate, amt in golden:
			if ln.excluded:
				self.assertEqual(amt, D("0"))
			else:
				self.assertEqual(_amount(ln), amt, ln.line_id)

	def test_FR_NORM_016_tong_theo_buoc_cau_phan(self):
		rows = [
			(ln.step or "service", ln.comp, None if ln.excluded else _amount(ln), ln.excluded)
			for ln in g.NORMS[SVC]
		]
		s = summarize(rows)
		expect_total = sum(a for *_x, a in g.direct_lines(SVC))
		self.assertEqual(s["total"], expect_total)
		self.assertFalse(s["incomplete"])
		by_c = {}
		for ln, _q, _r, a in g.direct_lines(SVC):
			by_c[ln.comp] = by_c.get(ln.comp, D("0")) + a
		self.assertEqual(s["by_component"], by_c)

	def test_FR_NORM_016_dich_vu_B(self):
		for ln, _q, _r, amt in g.direct_lines("DV-TEST-B"):
			self.assertEqual(_amount(ln), amt)


if __name__ == "__main__":
	unittest.main()
