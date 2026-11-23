"""FEAT-031: hàm thuần hệ thống xét nghiệm (FR-CLS-001, 005, 006, 007; TC-CLS-20, TC-CLS-23)."""

import unittest
from decimal import Decimal as D

from normcore.costing import test_systems as ts

OK = dict(
	test_system_code="GLU-A",
	technical_service="GLU",
	department="HS",
	main_equipment="EQ_A",
	volume_share_pct=75,
	machine_minutes_per_case=None,
	est_rerun_rate=2,
	est_wastage_rate=3,
	status="Đang dùng",
)


def errs(allocation_basis="Số kết quả", paraclinical=True, **kw):
	return ts.validate_test_system({**OK, **kw}, allocation_basis, paraclinical)


class TestValidate(unittest.TestCase):
	def test_hop_le(self):
		self.assertEqual(errs(), [])

	def test_thieu_truong_bat_buoc(self):
		for f in (
			"test_system_code",
			"technical_service",
			"department",
			"main_equipment",
			"volume_share_pct",
		):
			for empty in (None, "", "  "):
				self.assertTrue(any(f in e or ts.LABELS[f] in e for e in errs(**{f: empty})), f)

	def test_dich_vu_khong_can_lam_sang(self):
		self.assertTrue(any("cận lâm sàng" in e for e in errs(paraclinical=False)))

	def test_ty_trong(self):
		for bad in (0, -1, 100.01, 101):
			self.assertTrue(errs(volume_share_pct=bad), bad)
		self.assertEqual(errs(volume_share_pct=100), [])
		self.assertEqual(errs(volume_share_pct="0.5"), [])

	def test_ty_le_uoc_tinh(self):
		self.assertTrue(errs(est_rerun_rate=-1))
		self.assertTrue(errs(est_rerun_rate=100.5))
		self.assertEqual(errs(est_rerun_rate=100), [])
		self.assertTrue(errs(est_wastage_rate=100))
		self.assertTrue(errs(est_wastage_rate=-0.1))
		self.assertEqual(errs(est_wastage_rate=99.99), [])
		self.assertEqual(errs(est_rerun_rate=None, est_wastage_rate=None), [])

	def test_phut_chiem_may(self):
		self.assertTrue(errs("Phút chiếm máy", machine_minutes_per_case=None))
		self.assertTrue(errs("Phút chiếm máy", machine_minutes_per_case=0))
		self.assertEqual(errs("Phút chiếm máy", machine_minutes_per_case=15), [])
		self.assertEqual(errs("Số kết quả", machine_minutes_per_case=None), [])
		self.assertEqual(errs("Số kết quả", machine_minutes_per_case=0), [])
		self.assertTrue(errs("Số kết quả", machine_minutes_per_case=-2))

	def test_trang_thai(self):
		self.assertTrue(errs(status="Khác"))
		self.assertEqual(errs(status="Ngừng dùng"), [])

	def test_gia_tri_khong_phai_so(self):
		self.assertTrue(errs(volume_share_pct="abc"))


SYS = [
	dict(name="GLU-A", technical_service="GLU", department="HS", volume_share_pct=75, status="Đang dùng"),
	dict(name="GLU-B", technical_service="GLU", department="HS", volume_share_pct=25, status="Ngừng dùng"),
	dict(name="UR-A", technical_service="UR", department="HS", volume_share_pct=100, status="Đang dùng"),
]


class TestScope(unittest.TestCase):
	def test_in_costing_scope(self):
		self.assertEqual(ts.in_costing_scope(SYS), ["GLU-A", "UR-A"])
		self.assertEqual(ts.in_costing_scope([]), [])

	def test_TC_CLS_23_norm_sets_to_cost(self):
		nsets = [
			dict(name="N1", test_system=None, technical_service="X"),
			dict(name="N2", test_system="GLU-A", technical_service="GLU"),
			dict(name="N3", test_system="GLU-B", technical_service="GLU"),
			dict(name="N4", technical_service="X"),
			dict(name="N5", test_system="", technical_service="SO"),
		]
		out = ts.norm_sets_to_cost(nsets, ["GLU-A"], ["SO"])
		self.assertEqual([n["name"] for n in out], ["N1", "N2", "N4"])

	def test_share_totals(self):
		t = ts.share_totals(SYS)
		self.assertEqual(t[("GLU", "HS")], D("75"))
		self.assertEqual(t[("UR", "HS")], D("100"))
		self.assertTrue(ts.share_warning(t[("GLU", "HS")]))
		self.assertFalse(ts.share_warning(t[("UR", "HS")]))
		self.assertFalse(ts.share_warning(D("100.0")))

	def test_share_totals_tinh_ca_hai(self):
		s = [{**SYS[1], "status": "Đang dùng"}, SYS[0]]
		self.assertEqual(ts.share_totals(s)[("GLU", "HS")], D("100"))

	def test_status_items(self):
		items = ts.status_items()
		self.assertEqual([i["key"] for i in items], ["norm_set", "qc_plan", "volume", "latest_cost"])
		for i in items:
			self.assertEqual(i["state"], "empty")
			self.assertEqual(i["message"], "Chưa có")
			self.assertTrue(i["label"] and i["source"])
