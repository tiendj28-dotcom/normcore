"""FEAT-025: kiểm tra nhất quán quy trình (FR-AI-006). Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import prompts_install
from normcore.ai.providers.base import ProviderError, ProviderTimeout
from normcore.api import access
from normcore.api import procedure as api
from normcore.api.test_procedure_ai import FakeProvider, enable_ai
from normcore.tests.utils import make_base, make_procedure, make_user, publish_procedure

CONTRA = "<p>Không dùng cho người dị ứng lidocain.</p>"


def make_consistency_procedure(service, dept):
	"""B01 Chuẩn bị (Găng tay, Bơm tiêm; Nhân lực), B02 Thực hiện (Găng tay, Lidocain; không Nhân lực)."""
	proc = make_procedure(service, dept)
	b01 = proc.steps[0]
	b01.phase = "Chuẩn bị"
	proc.contraindications = CONTRA
	proc.append("steps", {"phase": "Thực hiện", "step_title": "Tiêm", "description": "Tiêm thuốc"})
	proc.save(ignore_permissions=True)
	b02 = proc.steps[1]
	for step, text, rtype in (
		(b01, "Găng tay", "Vật tư"),
		(b01, "Bơm tiêm 5ml", "Vật tư"),
		(b02, "Găng tay", "Vật tư"),
		(b02, "Lidocain 2%", "Thuốc"),
	):
		proc.append(
			"resources",
			{"step_id": step.step_id, "resource_type": rtype, "resource_text": text, "quantity": 1, "uom": "cái"},
		)
	proc.save(ignore_permissions=True)
	return proc


def issues_payload(proc, good=True):
	b02 = proc.steps[1].step_id
	items = [{"step_id": b02, "excerpt": "dị ứng lidocain", "explanation": "Bước tiêm lidocain"}]
	items.append({"step_id": b02, "excerpt": "câu bịa", "explanation": "x"})
	return {"issues": items}


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


class TestCheckConsistency(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		enable_ai(1)
		self.service, self.dept, self.job = make_base()
		self.proc = make_consistency_procedure(self.service, self.dept)
		self.clin = make_user("clin.cons@normcore.test", "NC Clinician")
		access.assign_department(self.clin, self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _logs(self):
		return frappe.get_all("NC AI Log", {"ref_doctype": "NC Clinical Procedure"}, pluck="name")

	def _check(self, provider):
		with patch("normcore.ai.gateway.get_provider", return_value=provider):
			return api.check_consistency(self.proc.name)

	def test_FR_AI_006_kiem_tra_nhat_quan_co_ai(self):
		modified = frappe.db.get_value("NC Clinical Procedure", self.proc.name, "modified")
		before = len(self._logs())
		prov = FakeProvider(issues_payload(self.proc))
		out = self._check(prov)
		kinds = sorted((i["kind"], i["label"]) for i in out["rule_issues"])
		self.assertEqual(
			kinds,
			[
				("missing_in_preparation", "Lidocain 2%"),
				("no_performer", "Tiêm"),
				("unused_in_steps", "Bơm tiêm 5ml"),
			],
		)
		self.assertEqual(out["ai"]["status"], "done")
		self.assertEqual(len(out["ai"]["issues"]), 1)
		self.assertEqual(out["ai"]["rejected"], 1)
		self.assertIn("Có thể trái chống chỉ định", out["ai"]["issues"][0]["message"])
		logs = self._logs()
		self.assertEqual(len(logs) - before, 1)
		self.assertEqual(frappe.db.get_value("NC AI Log", out["ai"]["log"], "rejected_citations"), 1)
		self.assertEqual(frappe.db.get_value("NC Clinical Procedure", self.proc.name, "modified"), modified)
		self.assertEqual(frappe.db.get_value("NC AI Log", out["ai"]["log"], "ref_name"), self.proc.name)

	def test_UC005_6a_ai_khong_kha_dung_van_kiem_quy_tac(self):
		for exc in (ProviderTimeout("quá hạn"), ProviderError("lỗi")):
			out = self._check(FakeProvider(exc=exc))
			self.assertEqual(len(out["rule_issues"]), 3)
			self.assertEqual(out["ai"]["status"], "failed")
			self.assertTrue(out["ai"]["message"].startswith("Phần kiểm tra bằng AI chưa thực hiện"))

	def test_FR_AI_006_ai_tat_hoac_khong_co_chong_chi_dinh(self):
		before = len(self._logs())
		enable_ai(0)
		prov = FakeProvider({"issues": []})
		out = self._check(prov)
		self.assertEqual(out["ai"]["status"], "disabled")
		self.assertEqual(len(out["rule_issues"]), 3)
		enable_ai(1)
		self.proc.contraindications = "<p> </p>"
		self.proc.save(ignore_permissions=True)
		out = self._check(prov)
		self.assertEqual(out["ai"]["status"], "skipped")
		self.assertEqual(prov.calls, [])
		self.assertEqual(len(self._logs()), before)

	def test_FR_AI_006_quyen_kiem_tra_nhat_quan(self):
		other = make_user("clin.other@normcore.test", "NC Clinician")
		other_dept = make_base(department="KHOA-KHAC")[1]
		access.assign_department(other, other_dept)
		users = (
			make_user("aud.cons@normcore.test", "NC Auditor"),
			make_user("fin.cons@normcore.test", "NC Finance"),
			other,
		)
		frappe.set_user(self.clin)
		self.assertEqual(self._check(FakeProvider({"issues": []}))["ai"]["status"], "done")
		for user in users:
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.check_consistency(self.proc.name)
		frappe.set_user("Administrator")
		publish_procedure(self.proc)
		with self.assertRaises(frappe.ValidationError):
			api.check_consistency(self.proc.name)

	def test_FR_AI_011_payload_kiem_tra_va_de_xuat(self):
		prov = FakeProvider({"issues": []})
		self._check(prov)
		blob = json.dumps(prov.calls[0], ensure_ascii=False)
		for forbidden in ("unit_price", "NC Norm", "NC Room", "hospital_qty", "price"):
			self.assertNotIn(forbidden, blob)
		self.assertIn("dị ứng lidocain", blob)
		self.assertNotIn("<p>", json.dumps(prov.calls[0]["variables"], ensure_ascii=False))
