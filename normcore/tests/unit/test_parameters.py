import unittest

from normcore.costing import parameters as P


def _ok(**over):
	v = dict(P.DEFAULTS)
	v.update(over)
	return v


class TestParameters(unittest.TestCase):
	def test_TC_CLS_50_mac_dinh_ba_tham_so_moi(self):
		self.assertEqual(P.DEFAULTS["expired_depreciation_mode"], "ZERO")
		self.assertEqual(P.DEFAULTS["material_recon_tolerance"], 5)
		self.assertEqual(P.DEFAULTS["volume_recon_tolerance"], 2)

	def test_mac_dinh_hop_le(self):
		self.assertEqual(P.check_ranges(P.DEFAULTS), [])

	def test_ty_le_ngoai_khoang_bi_bao(self):
		self.assertTrue(P.check_ranges(_ok(wastage_cap=101)))
		self.assertTrue(P.check_ranges(_ok(reconciliation_tolerance=-1)))

	def test_tich_luy_va_nghia_vu_phai_duoi_100(self):
		self.assertTrue(P.check_ranges(_ok(accumulation_rate=100)))
		self.assertTrue(P.check_ranges(_ok(obligation_rate=100)))
		self.assertEqual(P.check_ranges(_ok(accumulation_rate=99.9, obligation_rate=99.9)), [])

	def test_ngay_gio_don_vi_lam_tron(self):
		self.assertTrue(P.check_ranges(_ok(working_days_per_year=0)))
		self.assertTrue(P.check_ranges(_ok(working_hours_per_day=-1)))
		self.assertTrue(P.check_ranges(_ok(rounding_unit=0)))

	def test_che_do_khong_hop_le(self):
		self.assertTrue(P.check_ranges(_ok(accumulation_mode="X")))
		self.assertTrue(P.check_ranges(_ok(expired_depreciation_mode="X")))
		self.assertTrue(P.check_ranges(_ok(eqa_cost_category="X")))

	def test_gia_tri_trong_bo_qua(self):
		self.assertEqual(P.check_ranges({}), [])
		self.assertEqual(P.check_ranges({"wastage_cap": None, "accumulation_mode": ""}), [])

	def test_gia_dien_nuoc_mac_dinh_bang_khong(self):
		self.assertEqual((P.DEFAULTS["electricity_price"], P.DEFAULTS["water_price"]), (0, 0))
