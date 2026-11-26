"""Nút tạm trên form (NORM-10): phương thức máy chủ từ chối vai trò không có quyền và NC Auditor (FR-ACC-007, TC-ACC-04)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import (
	costing_run_inputs,
	make_base,
	make_param_set,
	make_procedure,
	make_user,
	publish_procedure,
)

ADMIN = "Administrator"


class TestFormActions(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user(ADMIN)
		cls.service, cls.dept, cls.job = make_base("DV-FORM-ACT", "KHOA-FORM-ACT")
		cls.users = {
			"clinician": make_user("fa.clinician@normcore.test", "NC Clinician"),
			"finance": make_user("fa.finance@normcore.test", "NC Finance"),
			"director": make_user("fa.director@normcore.test", "NC Director"),
			"auditor": make_user("fa.auditor@normcore.test", "NC Auditor"),
		}

	def tearDown(self):
		frappe.set_user(ADMIN)

	def _draft_procedure(self, version):
		return make_procedure(self.service, self.dept, version=version)

	def _published_procedure(self, version):
		proc = self._draft_procedure(version)
		proc.db_set({"decision_no": "QD-FA", "effective_date": "2026-01-01"})
		proc.reload()
		frappe.set_user(self.users["director"])
		publish_procedure(proc, "QD-FA", "2026-01-01")
		frappe.set_user(ADMIN)
		return proc

	def _draft_norm_set(self, version):
		proc = self._published_procedure(version)
		return frappe.get_doc("NC Norm Set", make_norm_set(proc.name))

	def _denied(self, user_key, fn, doctype, name, field, expected):
		frappe.set_user(self.users[user_key])
		with self.assertRaises(frappe.PermissionError):
			fn()
		frappe.set_user(ADMIN)
		self.assertEqual(frappe.db.get_value(doctype, name, field), expected)

	# publish
	def test_publish_clinician_bi_tu_choi(self):
		p = self._draft_procedure(101)
		p.db_set({"decision_no": "QD-FA", "effective_date": "2026-01-01"})
		self._denied(
			"clinician",
			lambda: frappe.get_doc("NC Clinical Procedure", p.name).publish(),
			"NC Clinical Procedure",
			p.name,
			"workflow_state",
			"Nháp",
		)

	def test_publish_auditor_bi_tu_choi(self):
		p = self._draft_procedure(102)
		p.db_set({"decision_no": "QD-FA", "effective_date": "2026-01-01"})
		self._denied(
			"auditor",
			lambda: frappe.get_doc("NC Clinical Procedure", p.name).publish(),
			"NC Clinical Procedure",
			p.name,
			"workflow_state",
			"Nháp",
		)

	# make_norm_set
	def test_make_norm_set_finance_bi_tu_choi(self):
		p = self._published_procedure(103)
		self._denied(
			"finance", lambda: make_norm_set(p.name), "NC Norm Set", {"procedure": p.name}, "name", None
		)

	def test_make_norm_set_auditor_bi_tu_choi(self):
		p = self._published_procedure(104)
		self._denied(
			"auditor", lambda: make_norm_set(p.name), "NC Norm Set", {"procedure": p.name}, "name", None
		)

	# lock
	def test_lock_clinician_bi_tu_choi(self):
		ns = self._draft_norm_set(105)
		self._denied(
			"clinician",
			lambda: frappe.get_doc("NC Norm Set", ns.name).lock(),
			"NC Norm Set",
			ns.name,
			"status",
			"Nháp",
		)

	def test_lock_auditor_bi_tu_choi(self):
		ns = self._draft_norm_set(106)
		self._denied(
			"auditor",
			lambda: frappe.get_doc("NC Norm Set", ns.name).lock(),
			"NC Norm Set",
			ns.name,
			"status",
			"Nháp",
		)

	# run_costing
	def _run(self):
		ps = make_param_set(self.job)
		run = frappe.get_doc(
			{
				"doctype": "NC Costing Run",
				"title": "Lần tính thử",
				"fiscal_year": 2026,
				"costing_date": "2026-01-01",
				"parameter_set": ps.name,
				**costing_run_inputs(),
			}
		)
		run.insert(ignore_permissions=True)
		return run

	def test_run_costing_director_bi_tu_choi(self):
		run = self._run()
		self._denied(
			"director",
			lambda: frappe.get_doc("NC Costing Run", run.name).run_costing(),
			"NC Costing Run",
			run.name,
			"status",
			"Nháp",
		)

	def test_run_costing_auditor_bi_tu_choi(self):
		run = self._run()
		self._denied(
			"auditor",
			lambda: frappe.get_doc("NC Costing Run", run.name).run_costing(),
			"NC Costing Run",
			run.name,
			"status",
			"Nháp",
		)
