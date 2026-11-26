"""FEAT-037: report "NC Physical Reconciliation" (SCR-DSK-038) trên site."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.report.nc_physical_reconciliation.nc_physical_reconciliation import execute
from normcore.tests import cls_fixtures as fx
from normcore.tests.utils import make_user

FIN = "fin.rpt37@normcore.test"
AUD = "aud.rpt37@normcore.test"
CLIN = "clin.rpt37@normcore.test"


class TestNCPhysicalReconciliationReport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.world = fx.make_cls_golden()
		frappe.db.set_value("NC Stock Issue Actual", {"item": "HC_GLU"}, "issued_qty", 100)
		frappe.db.set_value("NC Service Volume", {"technical_service": "GLU"}, "volume", 15500)
		self.run = fx.make_run(self.world)
		self.run.run_costing(confirm_ineligible=1)
		for u, r in ((FIN, "NC Finance"), (AUD, "NC Auditor"), (CLIN, "NC Clinician")):
			make_user(u, r)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_cot_va_dong_vat_chat(self):
		cols, rows = execute({})
		self.assertEqual(rows, [])
		cols, rows = execute({"costing_run": self.run.name})
		self.assertEqual(
			[c["fieldname"] for c in cols],
			[
				"department_label",
				"item_label",
				"calculated_qty",
				"actual_qty",
				"diff_qty",
				"variance_pct",
				"state",
				"explanation",
			],
		)
		glu = next(r for r in rows if r["item"] == "HC_GLU")
		self.assertEqual((glu["variance_pct"], glu["state"]), (9.07, "Vượt ngưỡng · cần giải trình"))
		_c, only = execute({"costing_run": self.run.name, "only_attention": 1})
		self.assertEqual([r["item"] for r in only], ["HC_GLU"])
		_c, none = execute({"costing_run": self.run.name, "department": "KHOA-KHAC"})
		self.assertEqual(none, [])

	def test_bang_san_luong(self):
		cols, rows = execute({"costing_run": self.run.name, "table": "Sản lượng"})
		self.assertEqual(cols[0]["fieldname"], "service_label")
		self.assertEqual(
			[(r["technical_service"], r["variance_pct"], r["state"]) for r in rows],
			[("GLU", 3.23, "Cảnh báo lệch sản lượng")],
		)

	def test_quyen(self):
		frappe.set_user(AUD)
		self.assertTrue(execute({"costing_run": self.run.name})[1])
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			execute({"costing_run": self.run.name})
		self.assertFalse(frappe.get_doc("Report", "NC Physical Reconciliation").is_permitted())

	def test_query_report_run_theo_vai_tro(self):
		from frappe.desk.query_report import run

		for user in (FIN, AUD):
			frappe.set_user(user)
			res = run("NC Physical Reconciliation", filters={"costing_run": self.run.name})
			self.assertTrue(res["result"], user)
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			run("NC Physical Reconciliation", filters={"costing_run": self.run.name})
