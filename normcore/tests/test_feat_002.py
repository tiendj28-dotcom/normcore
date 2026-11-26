"""FEAT-002: Workspace Normcore có block trang chủ, giữ lối tắt cũ (SCR-DSK-001)."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHomeWorkspace(FrappeTestCase):
	def test_workspace_co_block_trang_chu(self):
		ws = frappe.get_doc("Workspace", "Normcore")
		content = json.loads(ws.content)
		self.assertEqual(content[0]["type"], "header")
		self.assertEqual(content[1]["type"], "custom_block")  # đứng đầu, trước mọi lối tắt
		self.assertEqual(content[1]["data"]["custom_block_name"], "NC Trang chủ")
		self.assertEqual([c.custom_block_name for c in ws.custom_blocks], ["NC Trang chủ"])
		# mọi lối tắt cũ còn đủ
		labels = {s.label for s in ws.shortcuts}
		for label in ("Dịch vụ kỹ thuật", "Tham số vận hành", "Nhập dữ liệu từ Excel", "Nhật ký"):
			self.assertIn(label, labels)
		self.assertEqual(
			len([b for b in content if b["type"] == "shortcut"]), len(ws.shortcuts)
		)

	def test_block_trang_chu_goi_get_home_va_cong_khai(self):
		block = frappe.get_doc("Custom HTML Block", "NC Trang chủ")
		self.assertEqual(block.private, 0)
		self.assertIn("normcore.api.home.get_home", block.script)
