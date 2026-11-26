"""FEAT-020 — SCR-DSK-002, SCR-DSK-003: không mã màu cứng, chuỗi qua __() có bản dịch, chỉ báo dùng lớp Desk."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "nc_library" / "doctype"
DOC = LIB / "nc_legal_document"
SEC = LIB / "nc_legal_section"
FILES = [
	DOC / "nc_legal_document.js",
	DOC / "nc_legal_document_list.js",
	SEC / "nc_legal_section.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(path):
	return path.read_text(encoding="utf-8")


class TestLibraryUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			self.assertTrue(used, f.name)
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_chi_bao_dung_lop_desk(self):
		lst = _text(FILES[1])
		for status, color in (("Còn hiệu lực", "green"), ("Chưa hiệu lực", "blue"), ("Hết hiệu lực", "gray")):
			self.assertIn(f'"{status}": "{color}"', lst)
		for status, color in (
			("Chưa lập", "gray"),
			("Đang lập", "orange"),
			("Đã lập", "green"),
			("Lỗi", "red"),
		):
			self.assertIn(f'"{status}": "{color}"', _text(FILES[0]).replace("Lỗi:", '"Lỗi":'))
		self.assertIn("indicator-pill", lst)
		self.assertIn("get_indicator", lst)

	def test_goi_dung_api(self):
		self.assertIn("normcore.api.library.search_sections", _text(FILES[1]))
		self.assertIn("normcore.api.library.get_sections", _text(FILES[0]))
		self.assertIn("normcore.api.library.reindex", _text(FILES[0]))
		self.assertIn("normcore.api.library.get_source_view", _text(FILES[2]))

	def test_nut_tim_chi_khi_doc_duoc_muc_va_co_phim_tat(self):
		lst = _text(FILES[1])
		self.assertIn('frappe.model.can_read("NC Legal Section")', lst)
		self.assertIn("ctrl+shift+f", lst)

	def test_nut_lap_lai_chi_muc_chi_khi_co_quyen_ghi(self):
		js = _text(FILES[0])
		self.assertIn("frm.perm[0].write", js)
		self.assertIn('"Đang lập"', js)

	def test_du_lieu_chen_html_qua_escape(self):
		for f in FILES:
			self.assertIn("escape_html", _text(f), f.name)

	def test_khung_trang_goc_mo_dung_trang(self):
		js = _text(FILES[2])
		self.assertIn("#page=", js)
		self.assertIn("<iframe", js)

	def test_hai_truong_html_khong_co_cot_csdl_va_bo_cuc_hai_cot(self):
		sec = json.loads(_text(SEC / "nc_legal_section.json"))
		order = sec["field_order"]
		self.assertLess(order.index("plain_text"), order.index("col_source"))
		self.assertLess(order.index("col_source"), order.index("source_view_html"))
		doc = json.loads(_text(DOC / "nc_legal_document.json"))
		self.assertIn("sections_html", doc["field_order"])
		self.assertEqual(
			{f["fieldtype"] for f in doc["fields"] if f["fieldname"] == "sections_html"}, {"HTML"}
		)

	def test_workspace_co_van_ban_phap_ly(self):
		ws = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		for link in ("NC Legal Document", "NC Legal Section"):
			self.assertIn(f'"link_to": "{link}"', ws)
		self.assertIn("Văn bản pháp lý", ws)


class TestMappingUI(unittest.TestCase):
	"""FEAT-022 SCR-DSK-004: bảng ánh xạ trong form văn bản và lưới trong form mục."""

	def test_goi_dung_sau_api_anh_xa(self):
		js = _text(FILES[0])
		for m in (
			"get_mappings",
			"confirm_mappings",
			"confirm_exact",
			"save_mapping",
			"remove_mapping",
			"suggest_mappings",
		):
			self.assertIn(f'"{m}"', js)
		self.assertIn('"normcore.api.library." + method', js)

	def test_chi_bao_anh_xa_dung_lop_desk(self):
		js = _text(FILES[0])
		self.assertIn('"Đề xuất": "gray"', js)
		self.assertIn('"Đã xác nhận": "green"', js)
		self.assertIn("indicator-pill", js)
		self.assertNotIn("purple", js)  # đề xuất theo quy tắc, không phải của AI

	def test_nut_ghi_chi_khi_co_quyen_ghi_va_du_lieu_qua_escape(self):
		js = _text(FILES[0])
		self.assertIn("frm.perm[0].write", js)
		self.assertIn("can_write", js)
		self.assertGreaterEqual(js.count("escape_html"), 6)

	def test_luoi_chi_chon_dich_vu_dang_dung(self):
		js = _text(FILES[2])
		self.assertIn('frm.set_query("technical_service", "service_mappings"', js)
		self.assertIn("is_active: 1", js)

	def test_truong_html_va_bang_con_o_dung_cho(self):
		sec = json.loads(_text(SEC / "nc_legal_section.json"))
		self.assertLess(sec["field_order"].index("validity_status"), sec["field_order"].index("mapping_section"))
		self.assertLess(sec["field_order"].index("service_mappings"), sec["field_order"].index("compare_section"))
		doc = json.loads(_text(DOC / "nc_legal_document.json"))
		f = {x["fieldname"]: x for x in doc["fields"]}
		self.assertEqual(f["mapping_html"]["fieldtype"], "HTML")
		self.assertEqual(f["mapping_doc_section"]["depends_on"], "eval:doc.is_procedure_guideline")
