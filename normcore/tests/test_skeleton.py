import frappe
from frappe.tests.utils import FrappeTestCase

MODULES = ["NC Core", "NC Library", "NC Procedure", "NC AI", "NC Costing", "NC Benchmark"]


class TestSkeleton(FrappeTestCase):
	def test_six_module_defs(self):
		for m in MODULES:
			self.assertTrue(frappe.db.exists("Module Def", m), m)
			self.assertEqual(frappe.db.get_value("Module Def", m, "app_name"), "normcore")

	def test_no_required_apps(self):
		self.assertEqual(frappe.get_hooks("required_apps"), [])
