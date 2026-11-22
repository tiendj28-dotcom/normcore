"""FEAT-004 — trang nhập Excel: không mã màu cứng, chuỗi qua __(), có bản dịch (NFR-USE-001)."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_core" / "page" / "import_excel" / "import_excel.js"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


class TestImportUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		self.assertIsNone(HEX.search(JS.read_text(encoding="utf-8")))

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", JS.read_text(encoding="utf-8")))
		self.assertTrue(used)
		self.assertEqual(sorted(used - set(vi)), [])
