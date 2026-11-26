"""NORM-67: quyền đọc bản ghi NC Service Cost (FR-ACC-007, FR-ACC-003) trên dữ liệu lần tính thật."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import costing as api
from normcore.tests import costing_fixtures as cf
from normcore.core import permissions
from normcore.tests.utils import make_base, make_user

COST = "NC Service Cost"


class TestServiceCostPermission(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user("fin.n67@normcore.test", "NC Finance")
		self.aud = make_user("aud.n67@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n67@normcore.test", "NC Director")
		self.clin = make_user("clin.n67@normcore.test", "NC Clinician")
		self.head = make_user("head.n67@normcore.test", "NC Department Head")
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.run = cf.make_golden_run(self.params)
		frappe.set_user(self.fin)
		api.start_costing(self.run.name)
		frappe.set_user("Administrator")
		self.cost = frappe.get_value(COST, {"costing_run": self.run.name, "technical_service": "DV-TEST-A"})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_auditor_director_finance_doc_duoc_ban_ghi(self):
		for user in (self.aud, self.dir, self.fin):
			frappe.set_user(user)
			doc = frappe.get_doc(COST, self.cost)
			self.assertTrue(frappe.has_permission(COST, "read", doc=doc), user)
			self.assertTrue(frappe.has_permission(COST, "read", doc=self.cost), user)
			self.assertTrue(api.get_explanation(self.cost)["header"], user)

	def test_auditor_khong_ghi_duoc(self):
		frappe.set_user(self.aud)
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission(COST, ptype, doc=self.cost), ptype)

	def test_truong_khoa_chi_doc_khoa_minh(self):
		# FR-ACC-003: NC Department Head đọc dịch vụ của khoa được gán, không đọc khoa khác
		other, _, _ = make_base("DV-N67-X", "KHOA-N67-X")
		self.assertNotEqual(other, self.dept)
		permissions.assign_department(self.head, "KHOA-N67-X")
		frappe.set_user(self.head)
		self.assertFalse(frappe.has_permission(COST, "read", doc=self.cost))
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, self.dept)
		frappe.set_user(self.head)
		self.assertTrue(frappe.has_permission(COST, "read", doc=self.cost))
		self.assertFalse(frappe.has_permission(COST, "write", doc=self.cost))

	def test_clinician_khong_co_quyen_doc_bang_giai_trinh(self):
		# Quyết định Lead Q2 (ASM-015-22): NC Service Cost không cấp quyền cho NC Clinician
		frappe.set_user("Administrator")
		permissions.assign_department(self.clin, self.dept)
		frappe.set_user(self.clin)
		self.assertFalse(frappe.has_permission(COST, "read", doc=self.cost))

	def test_auditor_kem_vai_tro_theo_khoa_van_doc_moi_khoa(self):
		# Vai trò khác (NC Auditor) cấp đọc thì phạm vi khoa không hẹp lại (G4)
		both = make_user("aud.clin.n67@normcore.test", "NC Auditor", "NC Clinician")
		make_base("DV-N67-X", "KHOA-N67-X")
		permissions.assign_department(both, "KHOA-N67-X")
		frappe.set_user(both)
		self.assertTrue(frappe.has_permission(COST, "read", doc=self.cost))
