"""FEAT-003 — SCR-DSK-030: không mã màu cứng, chỉ đọc (NFR-USE-001); nhãn là giá trị tiếng Việt của `event_type`, không chuỗi `__()`."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_core" / "doctype" / "nc_audit_event" / "nc_audit_event_list.js"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


class TestAuditUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		self.assertIsNone(HEX.search(JS.read_text(encoding="utf-8")))

	def test_khong_co_nut_tao_hay_sua(self):
		text = JS.read_text(encoding="utf-8")
		self.assertNotIn("primary_action", text)
		self.assertNotIn("set_value", text)
