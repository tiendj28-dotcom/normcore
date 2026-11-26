import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai.prompts_install import TEMPLATE_CODES, ensure_default_templates


def _user_with_role(email, role):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	frappe.get_doc("User", email).add_roles(role)
	return email


def _new(code="DRAFT_PROCEDURE", **kw):
	d = {
		"doctype": "NC Prompt Template",
		"template_code": code,
		"system_prompt": "sys",
		"user_prompt": "{{ variables | tojson }}",
		"output_schema": '{"type": "object"}',
		"is_active": 1,
	}
	d.update(kw)
	return frappe.get_doc(d).insert()


class TestNCPromptTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_mac_dinh_cai_san_bay_ma_mot_ban_dang_dung(self):
		ensure_default_templates()
		for code in TEMPLATE_CODES:
			active = frappe.get_all(
				"NC Prompt Template", {"template_code": code, "is_active": 1}, pluck="name"
			)
			self.assertEqual(active, [f"{code}-v1"], code)

	def test_FR_AI_014_ban_da_tao_khong_sua_duoc(self):
		ensure_default_templates()
		t = frappe.get_doc("NC Prompt Template", "DRAFT_PROCEDURE-v1")
		t.system_prompt = "đổi"
		self.assertRaises(frappe.ValidationError, t.save)

	def test_FR_AI_014_ban_moi_tu_cap_version_va_thoi_dung_ban_cu(self):
		ensure_default_templates()
		t2 = _new("DRAFT_PROCEDURE", system_prompt="mới")
		self.assertEqual(t2.name, "DRAFT_PROCEDURE-v2")
		self.assertEqual(t2.version, 2)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "DRAFT_PROCEDURE-v1", "is_active"), 0)
		self.assertNotEqual(
			frappe.db.get_value("NC Prompt Template", "DRAFT_PROCEDURE-v1", "system_prompt"), "mới"
		)
		self.assertEqual(
			frappe.get_all(
				"NC Prompt Template", {"template_code": "DRAFT_PROCEDURE", "is_active": 1}, pluck="name"
			),
			["DRAFT_PROCEDURE-v2"],
		)

	def test_FR_AI_014_cu_phap_va_luoc_do_sai_bi_tu_choi(self):
		self.assertRaises(
			frappe.ValidationError, _new, "SUGGEST_CLS_NORM", user_prompt="{% if %}", version=50
		)
		self.assertRaises(frappe.ValidationError, _new, "SUGGEST_CLS_NORM", output_schema="[1]", version=51)

	def test_FR_AI_014_trung_phien_ban_bi_tu_choi(self):
		ensure_default_templates()
		self.assertRaises(frappe.ValidationError, _new, "DRAFT_PROCEDURE", version=1)

	def test_quyen_prompt_template_auditor_chi_doc_clinician_khong_doc(self):
		ensure_default_templates()
		auditor = _user_with_role("auditor.pt@normcore.test", "NC Auditor")
		clin = _user_with_role("clin.pt@normcore.test", "NC Clinician")
		name = "DRAFT_PROCEDURE-v1"
		frappe.set_user(auditor)
		self.assertTrue(frappe.has_permission("NC Prompt Template", "read", name))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Prompt Template", ptype, name), ptype)
		frappe.set_user(clin)
		self.assertFalse(frappe.has_permission("NC Prompt Template", "read", name))
