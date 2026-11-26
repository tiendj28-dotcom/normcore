"""Quy ước giao diện FEAT-002: không mã màu cứng, chuỗi qua __() có bản dịch vi.csv."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
FILES = [
	ROOT / "public" / "js" / "nc_chain_dots.js",
	ROOT / "nc_procedure" / "doctype" / "nc_technical_service" / "nc_technical_service_list.js",
	ROOT / "nc_core" / "doctype" / "nc_settings" / "nc_settings.js",
]
BLOCK = ROOT / "fixtures" / "custom_html_block.json"


def _texts():
	block = json.loads(BLOCK.read_text(encoding="utf-8"))[0]
	return [(p.name, p.read_text(encoding="utf-8")) for p in FILES] + [
		("custom_html_block", block["script"]),
		("custom_html_block.style", block["style"]),
		("custom_html_block.html", block["html"]),
	]


class TestHomeUi(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for name, text in _texts():
			self.assertIsNone(HEX.search(text), name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0] for row in csv.reader(f) if len(row) >= 2}
		used = set()
		for _name, text in _texts():
			used |= set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", text))
		self.assertTrue(used)
		self.assertEqual(sorted(used - vi), [])
