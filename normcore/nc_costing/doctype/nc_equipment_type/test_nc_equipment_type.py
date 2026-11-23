import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user


def _type(code="LT1"):
	return frappe.get_doc({"doctype": "NC Equipment Type", "type_code": code, "type_name": "Máy X-quang"})


class TestNCEquipmentType(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_RES_005_tao_va_trung_ma(self):
		self.assertEqual(_type().insert().name, "LT1")
		self.assertRaises(frappe.DuplicateEntryError, _type().insert)
		self.assertEqual(_type("LT2").insert().compliance_required, 0)  # TBD-18: mặc định trống

	def test_FR_ACC_002_resource_manager_ghi_finance_chi_doc(self):
		rm, fin = (
			make_user("et.rm@normcore.test", "NC Resource Manager"),
			make_user("et.fin@normcore.test", "NC Finance"),
		)
		frappe.set_user(rm)
		self.assertTrue(frappe.has_permission("NC Equipment Type", "create"))
		frappe.set_user(fin)
		self.assertTrue(frappe.has_permission("NC Equipment Type", "read"))
		self.assertFalse(frappe.has_permission("NC Equipment Type", "create"))

	def test_FR_ACC_002_vai_tro_khong_quyen(self):
		frappe.set_user(make_user("et.none@normcore.test", "NC Council Member"))
		self.assertFalse(frappe.has_permission("NC Equipment Type", "read"))

	def test_FR_ACC_007_auditor_chi_doc(self):
		frappe.set_user(make_user("et.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Equipment Type", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("NC Equipment Type", ptype), ptype)
		self.assertRaises(frappe.PermissionError, _type("LT3").insert)
