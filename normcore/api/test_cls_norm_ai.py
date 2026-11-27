"""FEAT-038: AI đề xuất định mức từ tài liệu của hãng (FR-LIB-013, FR-AI-016..018, UC-025).

Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import prompts, prompts_install


class TestPromptTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def _reset_v1(self):
		for name in frappe.get_all("NC Prompt Template", {"template_code": "SUGGEST_CLS_NORM"}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)
		prompts_install.ensure_default_templates()

	def test_mau_lenh_suggest_cls_norm_v2(self):
		self._reset_v1()
		self.assertEqual(prompts_install.ensure_suggest_cls_norm_v2(), "SUGGEST_CLS_NORM-v2")
		self.assertEqual(prompts_install.ensure_suggest_cls_norm_v2(), "SUGGEST_CLS_NORM-v2")
		self.assertEqual(
			frappe.get_all("NC Prompt Template", {"template_code": "SUGGEST_CLS_NORM"}, pluck="name", order_by="name"),
			["SUGGEST_CLS_NORM-v1", "SUGGEST_CLS_NORM-v2"],
		)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "SUGGEST_CLS_NORM-v1", "is_active"), 0)
		tpl = frappe.get_doc("NC Prompt Template", "SUGGEST_CLS_NORM-v2")
		out = prompts.render(
			tpl.user_prompt,
			{"service": {"service_code": "GLU"}, "procedure": None, "items": [], "equipment": []},
			[{"name": "LS-1"}],
		)
		self.assertIn("LS-1", out)

	def test_mau_lenh_suggest_cls_norm_v2_khong_cai_khi_admin_da_doi(self):
		self._reset_v1()
		# Admin đã tạo phiên bản mới của riêng mình: không cài đè
		custom = frappe.get_doc(
			{
				"doctype": "NC Prompt Template",
				"template_code": "SUGGEST_CLS_NORM",
				"is_active": 1,
				"system_prompt": "Lệnh do Admin sửa",
				"user_prompt": "Dữ liệu: {{ variables | tojson }}",
				"output_schema": '{"type": "object"}',
			}
		).insert(ignore_permissions=True)
		self.assertEqual(prompts_install.ensure_suggest_cls_norm_v2(), custom.name)
		self.assertEqual(frappe.db.count("NC Prompt Template", {"template_code": "SUGGEST_CLS_NORM"}), 2)
