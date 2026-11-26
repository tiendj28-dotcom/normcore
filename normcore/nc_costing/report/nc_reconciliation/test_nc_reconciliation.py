import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.report.nc_reconciliation.nc_reconciliation import execute
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user


class TestNCReconciliationReport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.params, self.dept, _ = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)
		self.run = cf.make_golden_run(self.params, accounting_import=self.imp)
		self.run.run_costing()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_bao_cao_doi_soat_cot_va_quyen(self):
		cols, rows = execute({})
		self.assertEqual(rows, [])
		self.assertEqual(
			[c["fieldname"] for c in cols],
			[
				"cost_center_label",
				"category_label",
				"costed_amount",
				"accounting_amount",
				"variance",
				"variance_pct",
				"remainder",
				"state",
				"explanation",
			],
		)
		fin = make_user("fin.rpt17@normcore.test", "NC Finance")
		aud = make_user("aud.rpt17@normcore.test", "NC Auditor")
		clin = make_user("clin.rpt17@normcore.test", "NC Clinician")
		for user in (fin, aud):
			frappe.set_user(user)
			_, rows = execute({"costing_run": self.run.name})
			self.assertEqual(
				[r["cost_category"] for r in rows], ["LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY"]
			)
			self.assertEqual(rows[0]["cost_center_label"], "K01 · Trung tâm K01")
			self.assertEqual(
				[r["state"] for r in rows],
				["Theo dõi", "Vượt ngưỡng · cần giải trình", "Theo dõi", "Theo dõi"],
			)
			_, only = execute({"costing_run": self.run.name, "only_over": 1})
			self.assertEqual([r["cost_category"] for r in only], ["DRUG_SUPPLY"])
			_, none = execute({"costing_run": self.run.name, "cost_center": "K02"})
			self.assertEqual(none, [])
		frappe.set_user(clin)
		with self.assertRaises(frappe.PermissionError):
			execute({"costing_run": self.run.name})
		roles = frappe.get_all(
			"Has Role", {"parent": "NC Reconciliation", "parenttype": "Report"}, pluck="role"
		)
		self.assertEqual(sorted(roles), ["NC Admin", "NC Auditor", "NC Director", "NC Finance"])
