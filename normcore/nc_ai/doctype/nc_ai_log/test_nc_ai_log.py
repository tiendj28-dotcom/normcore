import json

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import gateway
from normcore.ai.providers.mock import MOCK_RESPONSE


def _user_with_role(email, role):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.add_roles(role)
	return email


class TestNCAILog(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_gateway_mock_tra_json_co_dinh_va_ghi_mot_log(self):
		before = frappe.db.count("NC AI Log")
		res = gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {"a": 1}, ["MS-1", "MS-2"])
		self.assertTrue(res.ok)
		self.assertEqual(res.data, MOCK_RESPONSE)
		self.assertEqual(frappe.db.count("NC AI Log"), before + 1)
		log = frappe.get_doc("NC AI Log", res.log_name)
		self.assertEqual(log.purpose, "DRAFT_PROCEDURE")
		self.assertEqual(log.user, "Administrator")
		self.assertEqual(log.status, "Thành công")
		self.assertEqual(json.loads(log.response), MOCK_RESPONSE)
		self.assertEqual(log.source_sections, "MS-1\nMS-2")
		self.assertEqual(len(log.request_hash), 64)
		self.assertIsNotNone(log.tokens_in)
		self.assertIsNotNone(log.tokens_out)
		self.assertIsNotNone(log.duration_ms)
		self.assertEqual(log.rejected_citations, 0)

	def test_loi_van_ghi_mot_log_va_khong_lo_khoa(self):
		from normcore.ai.providers import anthropic as anth

		def bad_post(url, headers, payload, timeout):
			raise RuntimeError("boom SECRET-KEY")

		provider = anth.AnthropicProvider(api_key="SECRET-KEY", model="m", post=bad_post)
		before = frappe.db.count("NC AI Log")
		res = gateway.complete("DRAFT_PROCEDURE", "T", {}, [], provider=provider)
		self.assertFalse(res.ok)
		self.assertEqual(frappe.db.count("NC AI Log"), before + 1)
		log = frappe.get_doc("NC AI Log", res.log_name)
		self.assertEqual(log.status, "Lỗi")
		self.assertNotIn("SECRET-KEY", log.response or "")
		self.assertNotIn("SECRET-KEY", json.dumps(log.as_dict(), default=str))

	def test_quyen_nc_ai_log(self):
		res = gateway.complete("DRAFT_PROCEDURE", "T", {}, [])
		auditor = _user_with_role("auditor.ai@normcore.test", "NC Auditor")
		clinician = _user_with_role("clin.ai@normcore.test", "NC Clinician")
		frappe.set_user(auditor)
		self.assertTrue(frappe.has_permission("NC AI Log", "read", res.log_name))
		self.assertFalse(frappe.has_permission("NC AI Log", "write", res.log_name))
		self.assertFalse(frappe.has_permission("NC AI Log", "create"))
		self.assertFalse(frappe.has_permission("NC AI Log", "delete", res.log_name))
		frappe.set_user(clinician)
		self.assertFalse(frappe.has_permission("NC AI Log", "read", res.log_name))
