"""FEAT-017 trên site: phân bổ hai cấp, đối soát, khóa theo đối soát (technical-design 6, mục 5, 10)."""

import sys

import frappe
from frappe.tests.utils import FrappeTestCase

sys.path.insert(0, frappe.get_app_path("normcore", "..", "docs", "golden"))
import golden_engine as g

from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user


class TestCostingRunAllocation(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)  # setUp lỗi giữa chừng cũng không để lại dữ liệu
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _run(self):
		run = cf.make_golden_run(self.params, accounting_import=self.imp)
		self.assertEqual(run.run_costing(), "Đã tính")
		return run

	def _lines(self, run):
		return {
			r.cost_category: r
			for r in frappe.get_all(
				"NC Reconciliation Line",
				{"costing_run": run.name},
				[
					"name",
					"cost_category",
					"costed_amount",
					"accounting_amount",
					"variance_pct",
					"over_tolerance",
				],
			)
		}

	def test_doi_soat_tren_site_khop_golden(self):
		run = self._run()
		_, g_recon, _ = g.run()
		lines = self._lines(run)
		self.assertEqual(sorted(lines), sorted(c[0] for c in g_recon if c[0] != "MANAGEMENT"))
		for cat, costed, pool_in, _rem, pct, over in g_recon:
			if cat == "MANAGEMENT":
				continue
			ln = lines[cat]
			self.assertEqual(
				(ln.costed_amount, ln.accounting_amount, ln.variance_pct, ln.over_tolerance),
				(float(costed), float(pool_in), float(pct), int(over)),
			)
		self.assertEqual([c for c, ln in lines.items() if ln.over_tolerance], ["DRUG_SUPPLY"])
		costs = {
			c.technical_service: c
			for c in frappe.get_all(
				"NC Service Cost", {"costing_run": run.name}, ["technical_service", "full_cost"]
			)
		}
		self.assertEqual(costs["DV-TEST-A"].full_cost, 287745.46)
		self.assertEqual(costs["DV-TEST-B"].full_cost, 88169.70)
		self.assertIsNone(frappe.db.get_value("NC Costing Run", run.name, "allocation_warnings"))
		sc = frappe.get_doc("NC Service Cost", {"costing_run": run.name, "technical_service": "DV-TEST-A"})
		alloc = [ln for ln in sc.lines if ln.line_type == "Phân bổ"]
		self.assertEqual(len(alloc), 5)
		self.assertTrue(all(ln.allocation_rule and ln.driver_total is not None for ln in alloc))

	def test_TC_COST_10_khoa_khi_DRUG_SUPPLY_chua_giai_trinh(self):
		run = self._run()
		fin = make_user("fin.lock17@normcore.test", "NC Finance")
		frappe.set_user(fin)
		run.reload()
		with self.assertRaises(frappe.ValidationError) as cm:
			run.lock_costing()
		self.assertIn("DRUG_SUPPLY", str(cm.exception))
		self.assertEqual(frappe.db.get_value("NC Costing Run", run.name, "status"), "Đã tính")
		line = frappe.get_doc("NC Reconciliation Line", self._lines(run)["DRUG_SUPPLY"].name)
		line.explanation = "  Nhập thuốc chưa xuất kho  "
		line.save()
		self.assertEqual(
			frappe.db.get_value("NC Reconciliation Line", line.name, "explanation"),
			"Nhập thuốc chưa xuất kho",
		)
		self.assertEqual(run.lock_costing(), "Đã khóa")
		self.assertEqual(frappe.db.get_value("NC Costing Run", run.name, "status"), "Đã khóa")
		line.reload()
		line.explanation = "Sửa sau khóa"
		with self.assertRaises(frappe.ValidationError):
			line.save()
		run.reload()
		with self.assertRaises(frappe.ValidationError):
			run.run_costing()

	def test_tinh_lai_xoa_dong_doi_soat_cu(self):
		run = self._run()
		old = {r.name for r in self._lines(run).values()}
		line = frappe.get_doc("NC Reconciliation Line", self._lines(run)["DRUG_SUPPLY"].name)
		line.explanation = "Giải trình cũ"
		line.save()
		self.assertEqual(run.run_costing(), "Đã tính")
		new = {r.name for r in self._lines(run).values()}
		self.assertEqual(len(new), 4)
		self.assertFalse(old & new)
		self.assertIsNone(
			frappe.db.get_value("NC Reconciliation Line", self._lines(run)["DRUG_SUPPLY"].name, "explanation")
		)

	def test_thieu_quy_tac_ghi_allocation_warnings(self):
		for n in frappe.get_all(
			"NC Allocation Rule", {"level": "Cấp 2", "cost_category": "LABOR"}, pluck="name"
		):
			frappe.delete_doc("NC Allocation Rule", n, force=True)
		run = self._run()
		text = frappe.db.get_value("NC Costing Run", run.name, "allocation_warnings")
		self.assertIn("Thiếu quy tắc phân bổ cấp 2", text)
		self.assertIn("K01 · LABOR", text)
		sc = frappe.get_doc("NC Service Cost", {"costing_run": run.name, "technical_service": "DV-TEST-A"})
		self.assertFalse([ln for ln in sc.lines if ln.line_type == "Phân bổ" and ln.component == "LABOR"])

	def test_TC_COST_16_phan_con_lai_am_tren_site(self):
		cf.set_accounting_total(self.imp, "K01", "DEPRECIATION", 200000000)
		run = self._run()
		ln = self._lines(run)["DEPRECIATION"]
		self.assertEqual((ln.variance_pct, ln.over_tolerance), (42.42, 1))

	def test_quyen_doi_soat_khong_tao_tay_khong_sua_so(self):
		run = self._run()
		fin = make_user("fin.perm17@normcore.test", "NC Finance")
		frappe.set_user(fin)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "NC Reconciliation Line",
					"costing_run": run.name,
					"cost_center": "K01",
					"cost_category": "LABOR",
				}
			).insert()
		name = self._lines(run)["LABOR"].name
		with self.assertRaises(frappe.ValidationError):
			frappe.client.set_value("NC Reconciliation Line", name, "costed_amount", 1)
		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc("NC Reconciliation Line", name)
		frappe.set_user("Administrator")
		self.assertNotEqual(frappe.db.get_value("NC Reconciliation Line", name, "costed_amount"), 1)
