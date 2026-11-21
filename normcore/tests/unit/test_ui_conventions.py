"""Quy ước giao diện (design.md mục 2, 7): không mã màu cứng; chuỗi qua __(); có bản dịch vi.csv."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "public" / "js" / "procedure_editor"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


class TestUIConventions(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for p in UI_DIR.glob("*"):
			text = p.read_text(encoding="utf-8")
			self.assertIsNone(HEX.search(text), p.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		used = set()
		for p in UI_DIR.glob("*"):
			used |= set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", p.read_text(encoding="utf-8")))
		page_js = (ROOT / "nc_procedure" / "page" / "procedure_editor" / "procedure_editor.js").read_text(
			encoding="utf-8"
		)
		used |= set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", page_js))
		self.assertTrue(used)
		self.assertEqual(sorted(used - set(vi)), [])
