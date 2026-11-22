"""FEAT-011 — SCR-DSK-019: không mã màu cứng, chuỗi qua __() có bản dịch (NFR-USE-001)."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
	ROOT / "nc_costing" / "doctype" / "nc_costing_parameter_set" / "nc_costing_parameter_set.js",
	ROOT / "nc_costing" / "doctype" / "nc_price_category" / "nc_price_category.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


class TestParameterUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(f.read_text(encoding="utf-8")), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as fh:
			vi = {row[0]: row[1] for row in csv.reader(fh) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", f.read_text(encoding="utf-8")))
			self.assertTrue(used, f.name)
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_nut_nhan_ban_goi_duplicate(self):
		self.assertIn('method: "duplicate"', FILES[0].read_text(encoding="utf-8"))
