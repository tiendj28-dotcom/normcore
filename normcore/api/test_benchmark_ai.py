"""FEAT-027: trích bảng giá PDF bằng AI. Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import prompts, prompts_install


class TestPromptTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def _reset_v1(self):
		for name in frappe.get_all("NC Prompt Template", {"template_code": "EXTRACT_PRICE_LIST"}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)
		prompts_install.ensure_default_templates()

	def test_FR_AI_014_mau_lenh_trich_bang_gia(self):
		self._reset_v1()
		self.assertEqual(prompts_install.ensure_extract_price_list_v2(), "EXTRACT_PRICE_LIST-v2")
		self.assertEqual(prompts_install.ensure_extract_price_list_v2(), "EXTRACT_PRICE_LIST-v2")
		self.assertEqual(
			frappe.get_all(
				"NC Prompt Template", {"template_code": "EXTRACT_PRICE_LIST"}, pluck="name", order_by="name"
			),
			["EXTRACT_PRICE_LIST-v1", "EXTRACT_PRICE_LIST-v2"],
		)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "EXTRACT_PRICE_LIST-v1", "is_active"), 0)
		tpl = frappe.get_doc("NC Prompt Template", "EXTRACT_PRICE_LIST-v2")
		out = prompts.render(
			tpl.user_prompt, {"facility_name": "BV Mẫu", "file_name": "bg.pdf"}, [{"page": 1, "text": "Glucose"}]
		)
		self.assertIn("BV Mẫu", out)
		self.assertIn("Glucose", out)

	def test_FR_AI_014_mau_lenh_trich_bang_gia_khong_ghi_de_ban_admin(self):
		self._reset_v1()
		custom = frappe.get_doc(
			{
				"doctype": "NC Prompt Template",
				"template_code": "EXTRACT_PRICE_LIST",
				"is_active": 1,
				"system_prompt": "Lệnh do Admin sửa",
				"user_prompt": "Dữ liệu: {{ variables | tojson }}",
				"output_schema": '{"type": "object"}',
			}
		).insert(ignore_permissions=True)
		self.assertEqual(prompts_install.ensure_extract_price_list_v2(), custom.name)
		self.assertEqual(frappe.db.count("NC Prompt Template", {"template_code": "EXTRACT_PRICE_LIST"}), 2)
