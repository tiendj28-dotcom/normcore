"""FEAT-005 — SCR-DSK-005, SCR-DSK-006: không mã màu cứng, chuỗi qua __() có bản dịch (NFR-USE-001)."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_procedure" / "doctype" / "nc_technical_service"
FILES = [DIR / "nc_technical_service.js", DIR / "nc_technical_service_list.js"]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(path):
	return path.read_text(encoding="utf-8")


class TestServiceUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			# bỏ liên kết neo `#nc-chain-price` (không phải màu)
			text = _text(f).replace("#nc-chain-price", "")
			self.assertIsNone(HEX.search(text), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			self.assertTrue(used, f.name)
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_du_lieu_chen_vao_html_qua_escape(self):
		text = _text(FILES[0])
		self.assertIn("frappe.utils.escape_html", text)
		self.assertNotIn("${row.name}", text)

	def test_the_gia_da_duyet_co_neo_va_tabindex(self):
		text = _text(FILES[0])
		self.assertIn('id="nc-chain-price"', text)
		self.assertIn('tabindex="-1"', text)
