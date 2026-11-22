"""FEAT-003 — SCR-DSK-030: không mã màu cứng, chuỗi qua __() có bản dịch (NFR-USE-001)."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_core" / "doctype" / "nc_audit_event" / "nc_audit_event_list.js"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


class TestAuditUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		self.assertIsNone(HEX.search(JS.read_text(encoding="utf-8")))

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0] for row in csv.reader(f) if len(row) >= 2}
		used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", JS.read_text(encoding="utf-8")))
		self.assertEqual(sorted(used - vi), [])

	def test_khong_co_nut_tao_hay_sua(self):
		text = JS.read_text(encoding="utf-8")
		self.assertNotIn("primary_action", text)
		self.assertNotIn("set_value", text)
