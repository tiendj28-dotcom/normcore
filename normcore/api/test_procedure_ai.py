"""FEAT-024: AI soạn dự thảo quy trình. Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import gateway, prompts_install
from normcore.ai.providers.base import ProviderResponse


class FakeProvider:
	def __init__(self, data=None, exc=None, text=None):
		self.data, self.exc, self.text, self.calls = data, exc, text, []

	def complete(self, purpose, template_code, variables, sources, *, system=None, user=None):
		self.calls.append({"variables": variables, "sources": sources, "user": user})
		if self.exc:
			raise self.exc
		text = self.text if self.text is not None else json.dumps(self.data, ensure_ascii=False)
		return ProviderResponse(text=text, tokens_in=3, tokens_out=2)


def enable_ai(on=1):
	s = frappe.get_doc("NC AI Settings")
	s.update(dict(enabled=on, protocol="Anthropic Messages", model="m", api_key="SK-T", timeout_seconds=30,
		max_output_tokens=1000, monthly_token_budget=0))
	s.save(ignore_permissions=True)


class TestGatewayPostprocess(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		enable_ai()

	def tearDown(self):
		frappe.db.rollback()

	def _run(self, post, provider=None):
		return gateway.complete(
			"DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [], provider=provider or FakeProvider({"a": 1}), postprocess=post
		)

	def test_FR_AI_005_gateway_postprocess(self):
		res = self._run(lambda d: (d, 2))
		self.assertTrue(res.ok)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "rejected_citations"), 2)
		res = self._run(lambda d: (_ for _ in ()).throw(ValueError("hỏng")))
		self.assertFalse(res.ok)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "status"), "Lỗi")
		res = self._run(None)
		self.assertTrue(res.ok)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "rejected_citations"), 0)


class TestPromptV2(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def test_mau_lenh_draft_procedure_v2(self):
		prompts_install.ensure_default_templates()
		for name in frappe.get_all("NC Prompt Template", {"template_code": "DRAFT_PROCEDURE"}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)
		prompts_install.ensure_default_templates()
		self.assertEqual(prompts_install.ensure_draft_procedure_v2(), "DRAFT_PROCEDURE-v2")
		self.assertEqual(prompts_install.ensure_draft_procedure_v2(), "DRAFT_PROCEDURE-v2")
		self.assertEqual(
			frappe.get_all("NC Prompt Template", {"template_code": "DRAFT_PROCEDURE"}, pluck="name", order_by="name"),
			["DRAFT_PROCEDURE-v1", "DRAFT_PROCEDURE-v2"],
		)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "DRAFT_PROCEDURE-v1", "is_active"), 0)
