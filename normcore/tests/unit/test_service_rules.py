"""FEAT-031: hàm thuần dịch vụ cận lâm sàng (FR-SVC-008..011, DI-09; TC-CLS-20, TC-CLS-21)."""

import unittest

from normcore.procedure import service_rules as sr


class TestCodes(unittest.TestCase):
	def test_normalize_code(self):
		self.assertEqual(sr.normalize_code(" l100 "), "l100")
		self.assertEqual(sr.normalize_code(None), "")

	def test_TC_CLS_21_duplicate_codes(self):
		rows = [
			dict(source_system="LIS", external_code="L100"),
			dict(source_system="HIS", external_code="L100"),
			dict(source_system="LIS", external_code=" l100 "),
			dict(source_system="LIS", external_code="L200"),
		]
		self.assertEqual(sr.duplicate_codes(rows), [("LIS", "L100")])
		self.assertEqual(sr.duplicate_codes(rows[:2]), [])
		self.assertEqual(sr.duplicate_codes([]), [])

	def test_code_key(self):
		self.assertEqual(sr.code_key("LIS", " l100"), ("LIS", "L100"))


def base(**kw):
	v = dict(
		service_code="GLU",
		is_paraclinical=1,
		cls_group="Hóa sinh",
		result_unit="Kết quả xét nghiệm",
		is_panel=0,
		panel_components=[],
		is_send_out=0,
		send_out_price=0,
	)
	v.update(kw)
	return v


class TestClsErrors(unittest.TestCase):
	def test_hop_le(self):
		self.assertEqual(sr.cls_errors(base()), [])

	def test_TC_CLS_20_thieu_nhom_don_vi(self):
		e = sr.cls_errors(base(cls_group=None))
		self.assertEqual(len(e), 1)
		self.assertIn("Nhóm chuyên ngành", e[0])
		e = sr.cls_errors(base(result_unit=""))
		self.assertIn("Đơn vị kết quả", e[0])
		self.assertEqual(len(sr.cls_errors(base(cls_group=None, result_unit=None))), 2)

	def test_khong_can_lam_sang_khong_bat_buoc(self):
		v = base(is_paraclinical=0, cls_group=None, result_unit=None, is_panel=1, is_send_out=1)
		self.assertEqual(sr.cls_errors(v), [])

	def test_FR_SVC_010_bo(self):
		self.assertTrue(sr.cls_errors(base(is_panel=1)))
		comps = [dict(parameter_code="NA"), dict(parameter_code="K")]
		self.assertEqual(sr.cls_errors(base(is_panel=1, panel_components=comps)), [])
		dup = [dict(parameter_code="NA"), dict(parameter_code=" na ")]
		self.assertTrue(any("lặp" in e for e in sr.cls_errors(base(is_panel=1, panel_components=dup))))
		self_ref = [dict(parameter_code="NA", technical_service="GLU")]
		self.assertTrue(any("chính" in e for e in sr.cls_errors(base(is_panel=1, panel_components=self_ref))))

	def test_FR_SVC_011_gui_ngoai(self):
		self.assertTrue(sr.cls_errors(base(is_send_out=1, send_out_price=None)))
		self.assertTrue(sr.cls_errors(base(is_send_out=1, send_out_price=0)))
		self.assertTrue(sr.cls_errors(base(is_send_out=1, send_out_price=-5)))
		self.assertEqual(sr.cls_errors(base(is_send_out=1, send_out_price=120000)), [])
