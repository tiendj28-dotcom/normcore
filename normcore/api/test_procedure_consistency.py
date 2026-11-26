"""FEAT-025: kiểm tra nhất quán quy trình (FR-AI-006). Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import prompts_install


class TestPromptV2Feat025(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def _reset(self, code):
		for name in frappe.get_all("NC Prompt Template", {"template_code": code}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)

	def test_mau_lenh_feat_025_v2(self):
		for code, fn in (
			("CONSISTENCY_CHECK", prompts_install.ensure_consistency_check_v2),
			("SUGGEST_NORM_LINK", prompts_install.ensure_suggest_norm_link_v2),
		):
			self._reset(code)
			prompts_install.ensure_default_templates()
			self.assertEqual(
				frappe.get_all("NC Prompt Template", {"template_code": code}, pluck="name"), [f"{code}-v1"]
			)
			self.assertEqual(fn(), f"{code}-v2")
			self.assertEqual(fn(), f"{code}-v2")
			self.assertEqual(
				frappe.get_all("NC Prompt Template", {"template_code": code}, pluck="name", order_by="name"),
				[f"{code}-v1", f"{code}-v2"],
			)
			self.assertEqual(frappe.db.get_value("NC Prompt Template", f"{code}-v1", "is_active"), 0)
		# v1 Admin đã sửa: không tạo v2
		self._reset("CONSISTENCY_CHECK")
		frappe.get_doc(
			{
				"doctype": "NC Prompt Template",
				"template_code": "CONSISTENCY_CHECK",
				"is_active": 1,
				"system_prompt": "Admin tự soạn",
				"user_prompt": "{{ variables | tojson }}",
				"output_schema": '{"type": "object"}',
			}
		).insert(ignore_permissions=True)
		self.assertEqual(prompts_install.ensure_consistency_check_v2(), "CONSISTENCY_CHECK-v1")
		self.assertEqual(
			frappe.get_all("NC Prompt Template", {"template_code": "CONSISTENCY_CHECK"}, pluck="name"),
			["CONSISTENCY_CHECK-v1"],
		)
