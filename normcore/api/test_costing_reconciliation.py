"""FEAT-017: API đối soát (get_reconciliation, save_explanation, lock_run). NC Clinician không có quyền, NC Auditor chỉ đọc."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import costing as api
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user

FIN = "fin.recon17@normcore.test"
AUD = "aud.recon17@normcore.test"
CLIN = "clin.recon17@normcore.test"


class TestCostingReconciliationApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")
		self.params, self.dept, _ = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)
		self.run = cf.make_golden_run(self.params, accounting_import=self.imp)
		frappe.set_user(FIN)
		api.start_costing(self.run.name)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _drug_line(self):
		r = api.get_reconciliation(self.run.name)
		return next(x for x in r["lines"] if x["cost_category"] == "DRUG_SUPPLY")

	def test_get_reconciliation_can_lock_va_blocked(self):
		r = api.get_reconciliation(self.run.name)
		self.assertEqual(
			[x["cost_category"] for x in r["lines"]], ["LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY"]
		)
		self.assertEqual(
			(r["status"], r["blocked"], r["can_explain"], r["can_lock"]), ("Đã tính", 1, True, False)
		)
		self.assertEqual(
			(r["tolerance"], r["partial_scope"], r["include_depreciation"], r["warnings"]),
			(10, False, True, []),
		)
		d = self._drug_line()
		self.assertEqual((d["variance_pct"], d["over_tolerance"], d["needs_explanation"]), (-28.08, 1, True))
		self.assertEqual(d["remainder"], 73000000)
		self.assertEqual(d["cost_center_name"], "Trung tâm K01")
		self.assertEqual(api.get_run_results(self.run.name)["recon_blocked"], 1)
		with self.assertRaisesRegex(frappe.ValidationError, "DRUG_SUPPLY"):
			api.lock_run(self.run.name)
		out = api.save_explanation(d["name"], "  Thuốc nhập chưa xuất  ")
		self.assertEqual(
			out,
			{
				"name": d["name"],
				"explanation": "Thuốc nhập chưa xuất",
				"needs_explanation": False,
				"blocked": 0,
			},
		)
		r = api.get_reconciliation(self.run.name)
		self.assertEqual((r["blocked"], r["can_lock"]), (0, True))
		self.assertEqual(api.lock_run(self.run.name), {"status": "Đã khóa"})
		r = api.get_reconciliation(self.run.name)
		self.assertEqual((r["status"], r["can_explain"], r["can_lock"]), ("Đã khóa", False, False))
		with self.assertRaises(frappe.ValidationError):
			api.save_explanation(d["name"], "Sửa sau khóa")

	def test_quyen_doi_soat_clinician_bi_tu_choi(self):
		line = self._drug_line()["name"]
		frappe.set_user(CLIN)
		for call in (
			lambda: api.get_reconciliation(self.run.name),
			lambda: api.save_explanation(line, "x"),
			lambda: api.lock_run(self.run.name),
		):
			with self.assertRaises(frappe.PermissionError):
				call()
		self.assertFalse(frappe.has_permission("NC Reconciliation Line", "read"))

	def test_quyen_doi_soat_auditor_chi_doc(self):
		line = self._drug_line()["name"]
		frappe.set_user(AUD)
		r = api.get_reconciliation(self.run.name)
		self.assertEqual(len(r["lines"]), 4)
		self.assertEqual((r["can_explain"], r["can_lock"]), (False, False))
		with self.assertRaises(frappe.PermissionError):
			api.save_explanation(line, "x")
		with self.assertRaises(frappe.PermissionError):
			api.lock_run(self.run.name)

	def test_ghi_chu_khi_san_luong_bang_0(self):
		frappe.set_user("Administrator")
		frappe.db.set_value(
			"NC Service Volume", {"technical_service": "DV-TEST-B", "fiscal_year": 2026}, "volume", 0
		)
		self.run.reload()
		self.run.run_costing()
		frappe.set_user(FIN)
		res = {x["service"]: x for x in api.get_run_results(self.run.name)["results"]}
		self.assertEqual(
			(res["DV-TEST-A"]["has_volume_warning"], res["DV-TEST-B"]["has_volume_warning"]), (False, True)
		)
		sc = frappe.get_value(
			"NC Service Cost", {"costing_run": self.run.name, "technical_service": "DV-TEST-B"}, "name"
		)
		self.assertTrue(any("Sản lượng bằng 0" in n for n in api.get_explanation(sc)["notes"]))
