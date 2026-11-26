"""Unit test FEAT-018 T02: costing/compare.py (FR-COST-013)."""

import unittest
from decimal import Decimal as D

from normcore.costing import compare


def row(service="S", dept="D", status="Đã tính", full=100, **comp):
	r = {
		"technical_service": service,
		"department": dept,
		"calc_status": status,
		"full_cost": full,
		"direct_labor": 60,
		"direct_equipment": 20,
		"alloc_labor": 20,
		"accumulation": 5,
		"obligation": 1,
		"calculated_price": 106,
		"rounded_price": 110,
	}
	r.update(comp)
	return r


def comps(d):
	return {c.field: c for c in d.components}


class TestCompare(unittest.TestCase):
	def test_giong_nhau_khong_chenh(self):
		out = compare.compare([row()], [row()])
		self.assertEqual(len(out), 1)
		self.assertEqual(out[0].presence, "both")
		self.assertEqual(out[0].full_cost.diff, D("0.00"))
		self.assertFalse(compare.changed(out[0]))

	def test_chenh_la_so_sanh_tru_goc_theo_cau_phan(self):
		base = row(full=100, direct_equipment=20, alloc_labor=20)
		other = row(full=84.5, direct_equipment=10.25, alloc_labor=14.25)
		d = compare.compare([base], [other])[0]
		self.assertEqual(d.full_cost.diff, D("-15.50"))
		self.assertEqual(d.full_cost.pct, D("-15.50"))
		c = comps(d)
		self.assertEqual(c["direct_equipment"].diff, D("-9.75"))
		self.assertEqual(c["direct_equipment"].pct, D("-48.75"))
		self.assertEqual(c["alloc_labor"].diff, D("-5.75"))
		self.assertEqual(c["direct_labor"].diff, D("0.00"))
		self.assertTrue(compare.changed(d))
		direct_alloc = sum(
			x.diff for x in d.components if x.diff is not None and x.group in ("Trực tiếp", "Phân bổ")
		)
		self.assertEqual(direct_alloc, d.full_cost.diff)

	def test_base_bang_0_pct_none(self):
		d = compare.compare([row(direct_equipment=0)], [row(direct_equipment=5)])[0]
		c = comps(d)["direct_equipment"]
		self.assertEqual(c.diff, D("5.00"))
		self.assertIsNone(c.pct)

	def test_chi_co_o_mot_ben(self):
		out = compare.compare([row("A"), row("B")], [row("B"), row("C")])
		self.assertEqual(
			[(d.service, d.presence) for d in out], [("A", "base_only"), ("B", "both"), ("C", "other_only")]
		)
		a, c = out[0], out[2]
		self.assertIsNone(a.full_cost.other)
		self.assertIsNone(a.full_cost.diff)
		self.assertEqual(a.full_cost.base, D("100.00"))
		self.assertIsNone(c.full_cost.base)
		self.assertTrue(compare.changed(a) and compare.changed(c))
		self.assertFalse(compare.changed(out[1]))

	def test_mot_ben_loi(self):
		d = compare.compare([row()], [row(status="Lỗi", full=None)])[0]
		self.assertEqual((d.base_status, d.other_status), ("Đã tính", "Lỗi"))
		self.assertIsNone(d.full_cost.other)
		self.assertIsNone(d.full_cost.diff)
		self.assertIsNone(comps(d)["direct_labor"].other)
		self.assertTrue(compare.changed(d))

	def test_hai_ben_loi_khong_doi(self):
		d = compare.compare([row(status="Lỗi", full=None)], [row(status="Lỗi", full=None)])[0]
		self.assertFalse(compare.changed(d))
		self.assertIsNone(d.full_cost.diff)

	def test_khac_khoa_la_hai_dong(self):
		out = compare.compare([row(dept="K1")], [row(dept="K2")])
		self.assertEqual(
			[(d.department, d.presence) for d in out], [("K1", "base_only"), ("K2", "other_only")]
		)

	def test_cau_phan_eqa_chi_hien_khi_co(self):
		d = compare.compare([row()], [row()])[0]
		self.assertNotIn("eqa_cost", comps(d))
		d = compare.compare([row(eqa_cost=3)], [row(eqa_cost=5)])[0]
		self.assertEqual(comps(d)["eqa_cost"].diff, D("2.00"))
		self.assertEqual(comps(d)["eqa_cost"].group, "Trực tiếp")

	def test_changed_chi_do_trang_thai_hoac_cau_phan(self):
		d = compare.compare([row()], [row(status="Đã khóa")])[0]
		self.assertTrue(compare.changed(d))
		d = compare.compare([row()], [row(rounded_price=120)])[0]
		self.assertEqual(d.full_cost.diff, D("0.00"))
		self.assertTrue(compare.changed(d))

	def test_summary(self):
		out = compare.compare(
			[row("A"), row("B", full=100), row("D")], [row("B", full=90), row("C"), row("D")]
		)
		s = compare.summary(out)
		self.assertEqual(
			s, {"services": 4, "changed": 3, "base_only": 1, "other_only": 1, "total_diff": D("-10.00")}
		)

	def test_summary_rong(self):
		self.assertEqual(
			compare.summary([]),
			{"services": 0, "changed": 0, "base_only": 0, "other_only": 0, "total_diff": D("0.00")},
		)

	def test_input_changes(self):
		a = {
			"fiscal_year": "2026",
			"price_category": "PC1",
			"scope_departments": ["K2", "K1"],
			"scope_services": [],
			"parameter_set": "P",
		}
		b = {
			"fiscal_year": "2026",
			"price_category": "PC2",
			"scope_departments": ["K1", "K2"],
			"scope_services": ["S"],
			"parameter_set": "P",
		}
		self.assertEqual(
			compare.input_changes(a, b),
			[("Loại giá", "PC1", "PC2"), ("Phạm vi dịch vụ", "", "S")],
		)
		self.assertEqual(compare.input_changes(a, a), [])
		c = dict(a, volume_scenario="X")
		self.assertEqual(compare.input_changes(a, c), [("Kịch bản sản lượng", "", "X")])
