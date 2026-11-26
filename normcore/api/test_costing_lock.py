"""FEAT-018: API khóa, ảnh chụp, nhân bản, so sánh hai lần tính (technical-design 5, 6 #6, #9)."""

import sys

import frappe
from frappe.tests.utils import FrappeTestCase

sys.path.insert(0, frappe.get_app_path("normcore", "..", "docs", "golden"))
import golden_engine as g

from normcore.api import costing as api
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user

FIN = "fin.lock18@normcore.test"
AUD = "aud.lock18@normcore.test"
CLIN = "clin.lock18@normcore.test"
DIR = "dir.lock18@normcore.test"


class TestCostingLockApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		for email, role in ((FIN, "NC Finance"), (AUD, "NC Auditor"), (CLIN, "NC Clinician"), (DIR, "NC Director")):
			make_user(email, role)
		self.params, self.dept, _ = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _run(self, **kw):
		run = cf.make_golden_run(self.params, accounting_import=self.imp, **kw)
		frappe.set_user(FIN)
		api.start_costing(run.name)
		frappe.set_user("Administrator")
		return run

	def _locked(self):
		run = self._run()
		name = frappe.db.get_value(
			"NC Reconciliation Line", {"costing_run": run.name, "cost_category": "DRUG_SUPPLY"}
		)
		frappe.db.set_value("NC Reconciliation Line", name, "explanation", "Nhập thuốc chưa xuất kho")
		frappe.set_user(FIN)
		self.assertEqual(api.lock_run(run.name), {"status": "Đã khóa"})
		frappe.set_user("Administrator")
		return run

	def test_TC_COST_18_so_sanh_goc_voi_V1(self):
		base = self._run()
		cf.make_price_category_no_depr()
		v1 = self._run(price_category="PC-GOLD-V1")
		frappe.set_user(FIN)
		out = api.compare_runs(base.name, v1.name)
		rows = {r["service"]: r for r in out["rows"]}
		a = rows["DV-TEST-A"]
		g_base, g_v1 = g.run()[0], g.run(False)[0]
		self.assertEqual(a["full_cost"]["diff"], float(g_v1["DV-TEST-A"]["full"] - g_base["DV-TEST-A"]["full"]))
		self.assertEqual(a["full_cost"]["diff"], -63636.36)
		c = {x["field"]: x["diff"] for x in a["components"]}
		self.assertEqual((c["direct_equipment"], c["direct_infra"], c["alloc_depreciation"]), (-47348.48, -12500.0, -3787.88))
		for f in ("direct_labor", "direct_drug", "direct_supply", "direct_utility", "alloc_labor", "alloc_drug_supply", "alloc_utility", "alloc_management"):
			self.assertEqual(c[f], 0, f)
		self.assertEqual(
			round(sum(x["diff"] for x in a["components"] if x["group"] in ("Trực tiếp", "Phân bổ")), 2), -63636.36
		)
		self.assertEqual(rows["DV-TEST-B"]["full_cost"]["diff"], 0)
		self.assertIn("Loại giá", [x[0] for x in out["input_changes"]])
		self.assertEqual(out["summary"]["changed"], 1)
		only = api.compare_runs(base.name, v1.name, 1)
		self.assertEqual([r["service"] for r in only["rows"]], ["DV-TEST-A"])
		with self.assertRaises(frappe.ValidationError):
			api.compare_runs(base.name, base.name)

	def test_so_sanh_lan_chua_co_ket_qua(self):
		base = self._run()
		draft = cf.make_golden_run(self.params, accounting_import=self.imp)
		frappe.set_user(FIN)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.compare_runs(base.name, draft.name)
		self.assertIn("chưa có kết quả", str(cm.exception))

	def test_lock_run_get_run_results_co_hash_va_co_the(self):
		run = self._locked()
		frappe.set_user(FIN)
		r = api.get_run_results(run.name)
		self.assertEqual(len(r["snapshot_hash"]), 64)
		self.assertTrue(r["can_verify"])
		self.assertTrue(r["can_duplicate"])
		frappe.set_user(AUD)
		self.assertFalse(api.get_run_results(run.name)["can_duplicate"])

	def test_quyen_khoa_nhan_ban_so_sanh_theo_vai_tro(self):
		run = self._locked()
		other = self._run()
		frappe.set_user(CLIN)
		for call in (
			lambda: api.verify_snapshot(run.name),
			lambda: api.duplicate_run(run.name),
			lambda: api.compare_runs(run.name, other.name),
		):
			with self.assertRaises(frappe.PermissionError):
				call()
		frappe.set_user(AUD)
		self.assertTrue(api.verify_snapshot(run.name)["ok"])
		self.assertEqual(api.compare_runs(run.name, other.name)["summary"]["services"], 2)
		with self.assertRaises(frappe.PermissionError):
			api.duplicate_run(run.name)
		with self.assertRaises(frappe.PermissionError):
			api.lock_run(other.name)
		file = frappe.get_doc("File", {"file_url": frappe.db.get_value("NC Costing Run", run.name, "snapshot_file")})
		self.assertTrue(frappe.has_permission("File", doc=file))
		frappe.set_user(DIR)
		self.assertEqual(api.compare_runs(run.name, other.name)["summary"]["services"], 2)
		with self.assertRaises(frappe.PermissionError):
			api.duplicate_run(run.name)
		frappe.set_user(FIN)
		new = api.duplicate_run(run.name)["name"]
		self.assertEqual(frappe.db.get_value("NC Costing Run", new, "status"), "Nháp")
