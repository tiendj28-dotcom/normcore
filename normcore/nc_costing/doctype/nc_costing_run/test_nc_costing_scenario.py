"""FEAT-029 T02: NC Costing Run làm kịch bản điều chỉnh (technical-design 2.1, ASM-029-07)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests import costing_fixtures as cf


class TestCostingScenario(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)
		self.base = cf.make_golden_run(self.params, accounting_import=self.imp)
		self.assertEqual(self.base.run_costing(), "Đã tính")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _scenario(self, **kw):
		doc = frappe.get_doc(
			{
				"doctype": "NC Costing Run",
				"title": "Kịch bản",
				"fiscal_year": self.base.fiscal_year,
				"costing_date": self.base.costing_date,
				"parameter_set": self.base.parameter_set,
				"accounting_import": self.base.accounting_import,
				"price_category": self.base.price_category,
				"based_on_run": self.base.name,
				**kw,
			}
		)
		return doc

	def _make(self):
		doc = self._scenario()
		doc.flags.scenario_write = True
		doc.insert(ignore_permissions=True)
		return frappe.get_doc("NC Costing Run", doc.name)  # đối tượng mới: không mang flags

	def test_kich_ban_chi_sua_qua_api(self):
		# tạo kịch bản ngoài API bị chặn
		with self.assertRaises(frappe.ValidationError):
			self._scenario().insert(ignore_permissions=True)
		sc = self._make()
		self.assertTrue(sc.is_scenario)
		self.assertFalse(self.base.is_scenario)
		# không lồng kịch bản
		nested = self._scenario(based_on_run=sc.name)
		nested.flags.scenario_write = True
		with self.assertRaises(frappe.ValidationError):
			nested.insert(ignore_permissions=True)
		# lần gốc phải đã tính: lần Nháp không làm gốc được
		draft = cf.make_golden_run(self.params, accounting_import=self.imp)
		bad = self._scenario(based_on_run=draft.name)
		bad.flags.scenario_write = True
		with self.assertRaises(frappe.ValidationError):
			bad.insert(ignore_permissions=True)
		# sửa scenario_changes ngoài API bị chặn
		sc.reload()
		sc.append(
			"scenario_changes",
			{"change_type": "Tham số", "target_ref": "PS", "field": "accumulation_rate", "new_value": "4"},
		)
		with self.assertRaises(frappe.ValidationError):
			sc.save(ignore_permissions=True)
		sc.reload()
		sc.append(
			"scenario_changes",
			{"change_type": "Tham số", "target_ref": "PS", "field": "accumulation_rate", "new_value": "4"},
		)
		sc.flags.scenario_write = True  # như API
		sc.save(ignore_permissions=True)
		sc.flags.scenario_write = False
		self.assertEqual(len(sc.reload().scenario_changes), 1)
		# đổi based_on_run ngoài API bị chặn
		sc.based_on_run = None
		with self.assertRaises(frappe.ValidationError):
			sc.save(ignore_permissions=True)
		sc.reload()
		# chạy, khóa, nhân bản trực tiếp bị chặn
		for method in ("run_costing", "lock_costing", "duplicate_run"):
			with self.subTest(method=method), self.assertRaises(frappe.ValidationError):
				getattr(sc, method)()
		# lần tính thường không đổi hành vi
		self.assertEqual(self.base.reload().status, "Đã tính")
		self.assertTrue(self.base.duplicate_run())
