import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import ai
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.ai import gateway
from normcore.tests.utils import make_base, make_procedure, make_user, publish_procedure


def _set(**kw):
	s = frappe.get_doc("NC AI Settings")
	s.update(kw)
	s.save(ignore_permissions=True)


class TestAIApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_set(enabled=0, protocol="Anthropic Messages", model="m", monthly_token_budget=0, api_key="K-1")

	def tearDown(self):
		frappe.flags.pop("normcore_ai_transport", None)
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_AI_07_tat_ai_an_nut_van_chay_thu_cong(self):
		boot = frappe._dict()
		ai.boot_session(boot)
		self.assertFalse(boot.normcore_ai_enabled)
		self.assertEqual(ai.get_ai_status(), {"enabled": False})
		with self.assertRaises(frappe.ValidationError):
			gateway.ensure_enabled()
		# luồng thủ công: quy trình, bộ định mức, khóa
		service, dept, _job = make_base()
		proc = make_procedure(service, dept)
		publish_procedure(proc)
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		fin = make_user("fin.ai7@normcore.test", "NC Finance")
		frappe.set_user(fin)
		self.assertEqual(ns.lock(), "Đã khóa")
		frappe.set_user("Administrator")
		# bật lại
		_set(enabled=1)
		boot = frappe._dict()
		ai.boot_session(boot)
		self.assertTrue(boot.normcore_ai_enabled)
		self.assertEqual(ai.get_ai_status(), {"enabled": True})
		gateway.ensure_enabled()

	def test_get_ai_status_moi_nguoi_dung(self):
		frappe.set_user(make_user("clin.ai@normcore.test", "NC Clinician"))
		self.assertEqual(ai.get_ai_status(), {"enabled": False})

	def test_test_connection_admin(self):
		frappe.set_user(make_user("admin.ai7@normcore.test", "NC Admin"))
		res = ai.test_connection()
		self.assertTrue(res["ok"])
		self.assertEqual(res["status"], "Thành công")
		self.assertEqual(int(frappe.db.get_single_value("NC AI Settings", "enabled")), 0)

	def test_get_ai_usage(self):
		_set(monthly_token_budget=1000)
		frappe.get_doc(
			{"doctype": "NC AI Log", "purpose": "DRAFT_PROCEDURE", "status": "Thành công", "tokens_in": 900, "tokens_out": 200}
		).insert(ignore_permissions=True)
		frappe.set_user(make_user("auditor.ai7@normcore.test", "NC Auditor"))
		u = ai.get_ai_usage()
		self.assertEqual(u["budget"], 1000)
		self.assertGreaterEqual(u["used"], 1100)
		self.assertTrue(u["blocked"])
		self.assertRegex(u["month"], r"^\d\d/\d{4}$")

	def test_new_prompt_version(self):
		frappe.set_user(make_user("admin.ai7b@normcore.test", "NC Admin"))
		old = frappe.get_doc("NC Prompt Template", "DRAFT_PROCEDURE-v1").system_prompt
		r = ai.new_prompt_version("DRAFT_PROCEDURE", "sys2", "{{ variables | tojson }}", '{"type": "object"}')
		self.assertEqual(r, {"name": "DRAFT_PROCEDURE-v2", "version": 2})
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "DRAFT_PROCEDURE-v1", "is_active"), 0)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "DRAFT_PROCEDURE-v1", "system_prompt"), old)
		frappe.set_user("Administrator")
		self.assertEqual(gateway._active_template("DRAFT_PROCEDURE").name, "DRAFT_PROCEDURE-v2")
		frappe.set_user(make_user("admin.ai7b@normcore.test", "NC Admin"))
		with self.assertRaises(frappe.ValidationError):
			ai.new_prompt_version("DRAFT_PROCEDURE", "s", "{% if %}", '{"type": "object"}')
		with self.assertRaises(frappe.ValidationError):
			ai.new_prompt_version("DRAFT_PROCEDURE", "s", "x", "[1]")

	def test_quyen_tung_ham(self):
		clin = make_user("clin.ai7@normcore.test", "NC Clinician")
		auditor = make_user("auditor.ai7c@normcore.test", "NC Auditor")
		frappe.set_user(clin)
		for fn, args in (
			(ai.test_connection, ()),
			(ai.get_ai_usage, ()),
			(ai.new_prompt_version, ("DRAFT_PROCEDURE", "s", "x", "{}")),
		):
			with self.assertRaises(frappe.PermissionError, msg=fn.__name__):
				fn(*args)
		frappe.set_user(auditor)
		self.assertIn("used", ai.get_ai_usage())
		with self.assertRaises(frappe.PermissionError):
			ai.test_connection()
		with self.assertRaises(frappe.PermissionError):
			ai.new_prompt_version("DRAFT_PROCEDURE", "s", "x", "{}")
