"""So sánh phiên bản quy trình (FEAT-008; TC-WF-07, FR-WF-010)."""

import frappe

from normcore.api import procedure as api
from normcore.api.test_procedure_revision import RevisionBase, make_v1
from normcore.tests.utils import make_base

DT = "NC Clinical Procedure"


class TestCompare(RevisionBase):
	def setUp(self):
		super().setUp()
		v2 = frappe.get_doc(DT, self.revise(self.clin)["name"])
		v2.steps = [s for s in v2.steps if s.step_id != "S002"]
		v2.resources = [r for r in v2.resources if r.step_id != "S002"]
		v2.append("steps", {"phase": "Thực hiện", "step_title": "Mới", "description": "m"})
		for r in v2.resources:
			if r.step_id == "S003":
				r.quantity = 9
		v2.indications = "Chỉ định v2"
		v2.save(ignore_permissions=True)
		self.v2 = v2

	def call(self, user, a, b):
		frappe.set_user(user)
		try:
			return api.compare_versions(a, b)
		finally:
			frappe.set_user("Administrator")

	def test_TC_WF_07_so_sanh_phien_ban(self):
		r = self.call(self.clin, self.v1.name, self.v2.name)
		self.assertEqual((r["base"]["version_no"], r["target"]["version_no"]), (1, 2))
		sec = {s["key"]: s["status"] for s in r["sections"]}
		self.assertEqual(sec["indications"], "changed")
		self.assertTrue(all(v == "same" for k, v in sec.items() if k != "indications"))
		st = {s["step_id"]: s["status"] for s in r["steps"]}
		self.assertEqual(
			st, {"S001": "same", "S002": "removed", "S003": "same", "S004": "same", "S005": "added"}
		)
		res = {x["step_id"]: x for x in r["resources"] if x["status"] != "same"}
		self.assertEqual(res["S002"]["status"], "removed")
		self.assertEqual(res["S003"]["status"], "changed")
		self.assertEqual(res["S003"]["fields"], ["quantity"])
		self.assertEqual(r["summary"]["steps"], {"added": 1, "removed": 1, "changed": 0})
		self.assertEqual(r["summary"]["resources"], {"added": 0, "removed": 1, "changed": 1})
		self.assertEqual(r["summary"]["sections"]["changed"], 1)

	def test_so_sanh_kiem_quyen_va_cung_quy_trinh(self):
		# NC Auditor đọc được
		self.assertEqual(self.call(self.auditor, self.v1.name, self.v2.name)["base"]["name"], self.v1.name)
		# Clinician khoa khác không đọc được bản Nháp
		with self.assertRaises(frappe.PermissionError):
			self.call(self.clin_other, self.v1.name, self.v2.name)
		# khác dịch vụ/khoa
		other_service = make_base(service="DV-TEST-B")[0]
		other = make_v1(other_service, self.dept)
		with self.assertRaises(frappe.ValidationError):
			self.call(self.clin, self.v1.name, other.name)
		# cùng một bản
		with self.assertRaises(frappe.ValidationError):
			self.call(self.clin, self.v1.name, self.v1.name)
