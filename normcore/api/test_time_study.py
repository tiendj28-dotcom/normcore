import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import time_study as api
from normcore.nc_costing.doctype.nc_time_study.test_nc_time_study import make_four_step_procedure
from normcore.tests.utils import make_base, make_user


class TestTimeStudyApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _job = make_base("DV-BG", "K01")
		self.proc = make_four_step_procedure(self.service, self.dept)
		self.doc = frappe.get_doc(
			{"doctype": "NC Time Study", "technical_service": self.service, "department": self.dept}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_get_entry_co_buoc_va_nhan(self):
		r = api.get_entry(self.doc.name)
		self.assertEqual(len(r["steps"]), 4)
		self.assertEqual([s["step_title"] for s in r["steps"]], ["B1", "B2", "B3", "B4"])
		self.assertEqual(r["doc"]["procedure"], self.proc.name)
		labels = {(ln["job_title"], ln["equipment"]): (ln["job_title_label"], ln["equipment_label"]) for ln in r["lines"]}
		self.assertEqual(labels[("BS", None)][0], "Bác sĩ")
		self.assertEqual(labels[(None, "EQ1")][1], "Thiết bị thử")
		self.assertTrue(r["can_write"])

	def test_get_entry_auditor_khong_ghi_duoc(self):
		frappe.set_user(make_user("auditor.tsapi@normcore.test", "NC Auditor"))
		r = api.get_entry(self.doc.name)
		self.assertFalse(r["can_write"])

	def test_get_entry_council_bi_tu_choi(self):
		frappe.set_user(make_user("council.tsapi@normcore.test", "NC Council Member"))
		self.assertRaises(frappe.PermissionError, api.get_entry, self.doc.name)
