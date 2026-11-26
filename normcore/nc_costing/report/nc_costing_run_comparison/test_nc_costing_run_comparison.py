import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.report.nc_costing_run_comparison.nc_costing_run_comparison import execute
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user


class TestNCCostingRunComparisonReport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.params, self.dept, _ = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)
		self.base = cf.make_golden_run(self.params, accounting_import=self.imp)
		cf.make_price_category_no_depr()
		self.v1 = cf.make_golden_run(self.params, accounting_import=self.imp, price_category="PC-GOLD-V1")
		self.base.run_costing()
		self.v1.run_costing()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_bao_cao_so_sanh_cot_cay_va_quyen(self):
		cols, rows, msg = execute({})
		self.assertEqual(rows, [])
		self.assertTrue(msg)
		self.assertEqual(
			[c["fieldname"] for c in cols], ["label", "base_value", "other_value", "diff", "diff_pct", "note"]
		)
		filters = {"base_run": self.base.name, "other_run": self.v1.name, "only_changed": 1}
		fin = make_user("fin.rpt18@normcore.test", "NC Finance")
		aud = make_user("aud.rpt18@normcore.test", "NC Auditor")
		clin = make_user("clin.rpt18@normcore.test", "NC Clinician")
		frappe.set_user(aud)
		_, rows, msg, _chart, summary = execute(filters)
		services = [r for r in rows if r["indent"] == 0]
		self.assertEqual(len(services), 1)
		a = services[0]
		self.assertTrue(a["label"].startswith("DV-TEST-A"))
		self.assertEqual(a["diff"], -63636.36)
		self.assertTrue(all(r["indent"] == 1 and r["parent_node"] == a["node"] for r in rows[1:]))
		comp = {r["node"].rsplit("|", 1)[1]: r["diff"] for r in rows[1:]}
		self.assertEqual(comp["direct_equipment"], -47348.48)
		self.assertIn("Loại giá", msg)
		self.assertEqual([s["value"] for s in summary if s["label"] == "With difference"], [1])
		_, all_rows, *_ = execute({**filters, "only_changed": 0})
		self.assertEqual(len([r for r in all_rows if r["indent"] == 0]), 2)
		frappe.set_user(fin)
		self.assertEqual(execute(filters)[1][0]["diff"], -63636.36)
		frappe.set_user(clin)
		with self.assertRaises(frappe.PermissionError):
			execute(filters)
