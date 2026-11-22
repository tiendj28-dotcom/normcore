"""FEAT-009 — SCR-DSK-017: không mã màu cứng, chuỗi qua __() có bản dịch, dữ liệu qua escape (NFR-USE-001)."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "nc_costing" / "doctype"
FILES = [
	DOC / "nc_item" / "nc_item.js",
	DOC / "nc_item_price" / "nc_item_price.js",
	DOC / "nc_item_price" / "nc_item_price_list.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


class TestItemUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(f.read_text(encoding="utf-8")), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", f.read_text(encoding="utf-8")))
			self.assertTrue(used, f.name)
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_du_lieu_chen_vao_html_qua_escape(self):
		text = FILES[0].read_text(encoding="utf-8")
		self.assertIn("frappe.utils.escape_html", text)
		self.assertNotIn("${r.name}", text)
		self.assertNotIn("${r.document_no}", text)

	def test_nut_xac_minh_goi_api_xac_minh(self):
		text = FILES[1].read_text(encoding="utf-8")
		self.assertIn("normcore.api.item.verify_price", text)
		self.assertIn("can_write", text)
