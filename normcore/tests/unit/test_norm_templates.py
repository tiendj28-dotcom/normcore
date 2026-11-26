"""FEAT-034 T01: mẫu định mức (norm.templates)."""

import copy
import unittest

from normcore.norm.templates import (
	DEFAULT_TEMPLATES,
	apply_template,
	default_apply_k,
	pick_template,
	template_errors,
)

ITEMS = [
	{"item_name": "Vật tư lấy mẫu", "component": "SUPPLY", "default_cost_level": "TUBE", "is_mandatory": 1},
	{"item_name": "Hóa chất chính", "component": "DRUG", "default_cost_level": "RESULT", "is_mandatory": 1},
	{"item_name": "Thiết bị", "component": "EQUIPMENT", "default_cost_level": "RESULT", "is_mandatory": 1},
	{"item_name": "Điện nước", "component": "UTILITY", "default_cost_level": "DAY", "is_mandatory": 0},
]


def line(lid, component, **kw):
	return {"line_id": lid, "component": component, "resource": "X", "hospital_qty": 1, **kw}


class TestTemplateErrors(unittest.TestCase):
	def ok(self, **kw):
		return {"template_code": "M1", "cls_group": "Hóa sinh", "is_active": 0, "items": ITEMS, **kw}

	def test_hop_le(self):
		self.assertEqual(template_errors(self.ok(), []), [])
		self.assertEqual(template_errors(self.ok(is_active=1), []), [])

	def test_thieu_ma_va_nhom(self):
		e = template_errors(self.ok(template_code=" ", cls_group=None), [])
		self.assertEqual(e, ["Thiếu: Mã mẫu", "Thiếu: Nhóm chuyên ngành"])

	def test_trung_ten(self):
		items = [*ITEMS, {**ITEMS[0], "item_name": " vật tư LẤY MẪU "}]
		self.assertTrue(any("bị trùng" in x for x in template_errors(self.ok(items=items), [])))

	def test_thieu_ten_cau_phan_cap(self):
		items = [{"item_name": "", "component": "X", "default_cost_level": "Y"}]
		e = template_errors(self.ok(items=items), [])
		self.assertEqual(len(e), 3)

	def test_cap_mac_dinh_trong_la_result(self):
		items = [{"item_name": "A", "component": "DRUG"}]
		self.assertEqual(template_errors(self.ok(items=items), []), [])

	def test_dang_dung_khong_co_khoan_muc(self):
		self.assertIn("ít nhất một khoản mục", template_errors(self.ok(is_active=1, items=[]), [])[0])
		self.assertEqual(template_errors(self.ok(items=[]), []), [])

	def test_hai_mau_dang_dung(self):
		e = template_errors(self.ok(is_active=1), ["MDM-HOA-SINH"])
		self.assertEqual(e, ["Nhóm Hóa sinh đã có mẫu đang dùng: MDM-HOA-SINH"])
		self.assertEqual(template_errors(self.ok(is_active=0), ["MDM-HOA-SINH"]), [])


class TestPick(unittest.TestCase):
	def test_pick(self):
		rows = [
			{"name": "A", "cls_group": "Hóa sinh", "is_active": 0},
			{"name": "B", "cls_group": "Hóa sinh", "is_active": 1},
			{"name": "C", "cls_group": "Miễn dịch", "is_active": 1},
		]
		self.assertEqual(pick_template(rows, "Hóa sinh"), "B")
		self.assertEqual(pick_template(rows, "Miễn dịch"), "C")
		self.assertIsNone(pick_template(rows, "Huyết học"))
		self.assertIsNone(pick_template(None, "Hóa sinh"))


class TestApplyTemplate(unittest.TestCase):
	def test_TC_CLS_29_ghep_theo_cau_phan_va_them_dong_giu_cho(self):
		lines = [line("L001", "DRUG"), line("L002", "LABOR")]
		before = copy.deepcopy(lines)
		out = apply_template(lines, ITEMS, True)
		self.assertEqual(lines, before)  # không đổi đầu vào
		self.assertEqual(out[0]["template_item"], "Hóa chất chính")
		self.assertEqual(out[0]["cost_level"], "RESULT")
		self.assertNotIn("template_item", out[1])
		holders = out[2:]
		self.assertEqual([h["template_item"] for h in holders], ["Vật tư lấy mẫu", "Thiết bị"])
		for h in holders:
			self.assertEqual(h["service_level"], 1)
			self.assertIsNone(h["resource"])
			self.assertIsNone(h["hospital_qty"])
			self.assertEqual(h["basis"], "Ước tính")
		self.assertEqual(holders[0]["cost_level"], "TUBE")
		self.assertEqual(holders[0]["resource_doctype"], "NC Item")
		self.assertEqual(holders[1]["resource_doctype"], "NC Equipment")

	def test_khoan_muc_khong_bat_buoc_khong_them(self):
		out = apply_template([], ITEMS, True)
		self.assertNotIn("Điện nước", [o["template_item"] for o in out])

	def test_khoan_muc_khong_bat_buoc_van_ghep_neu_co_dong(self):
		out = apply_template([line("L001", "UTILITY")], ITEMS, True)
		self.assertEqual(out[0]["template_item"], "Điện nước")
		self.assertEqual(out[0]["cost_level"], "DAY")

	def test_moi_dong_chi_gan_mot_khoan_muc(self):
		items = [ITEMS[1], {**ITEMS[1], "item_name": "Hóa chất phụ trợ", "default_cost_level": "DAY"}]
		out = apply_template([line("L001", "DRUG"), line("L002", "DRUG")], items, True)
		self.assertEqual([o["template_item"] for o in out], ["Hóa chất chính", "Hóa chất phụ trợ"])
		self.assertEqual(out[1]["cost_level"], "DAY")

	def test_dong_da_co_khoan_muc_khong_gan_lai(self):
		out = apply_template([line("L001", "DRUG", template_item="Khác")], [ITEMS[1]], True)
		self.assertEqual(out[0]["template_item"], "Khác")
		self.assertEqual(len(out), 2)  # dòng giữ chỗ cho khoản mục bắt buộc

	def test_khong_can_lam_sang_giu_result(self):
		out = apply_template([], [ITEMS[0]], False)
		self.assertEqual(out[0]["cost_level"], "RESULT")
		out = apply_template([line("L001", "SUPPLY")], [ITEMS[0]], False)
		self.assertNotIn("cost_level", out[0])


class TestDefaultK(unittest.TestCase):
	def test_chi_result_thuoc_vat_tu(self):
		lines = [
			line("L01", "SUPPLY", cost_level="TUBE"),
			line("L02", "DRUG", cost_level="RESULT"),
			line("L03", "SUPPLY"),
			line("L04", "DRUG", cost_level="BATCH"),
			line("L06", "LABOR", cost_level="RESULT"),
			line("L07", "EQUIPMENT", cost_level="RESULT"),
		]
		out = default_apply_k(lines)
		self.assertEqual([bool(o.get("apply_k")) for o in out], [False, True, True, False, False, False])
		self.assertNotIn("apply_k", lines[1])


class TestDefaultTemplates(unittest.TestCase):
	def test_hai_mau_chua_bat(self):
		self.assertEqual([t["cls_group"] for t in DEFAULT_TEMPLATES], ["Hóa sinh", "Miễn dịch"])
		for t in DEFAULT_TEMPLATES:
			self.assertEqual(t["is_active"], 0)
			self.assertEqual(len(t["items"]), 8)
			self.assertEqual(template_errors({**t, "is_active": 1}, []), [])
