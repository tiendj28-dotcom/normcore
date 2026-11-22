import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user


def _new(code="CK-T01", name="Chuyên khoa thử"):
	return frappe.get_doc({"doctype": "NC Specialty", "specialty_code": code, "specialty_name": name})


class TestNCSpecialty(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_SVC_001_thieu_ten_bi_tu_choi(self):
		doc = frappe.get_doc({"doctype": "NC Specialty", "specialty_code": "CK-T02"})
		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_FR_SVC_001_trung_ma_bi_tu_choi(self):
		_new().insert()
		self.assertRaises(frappe.DuplicateEntryError, _new().insert)

	def test_FR_ACC_002_dat_ten_theo_ma(self):
		self.assertEqual(_new("CK-T03").insert().name, "CK-T03")

	def test_FR_ACC_002_vai_tro_chi_doc_khong_ghi(self):
		users = {
			r: make_user(f"sp.ro{i}@normcore.test", r)
			for i, r in enumerate(("NC Finance", "NC Clinician", "NC Director"))
		}
		for role, email in users.items():
			frappe.set_user(email)
			self.assertTrue(frappe.has_permission("NC Specialty", "read"), role)
			self.assertFalse(frappe.has_permission("NC Specialty", "create"), role)
			self.assertFalse(frappe.has_permission("NC Specialty", "write"), role)

	def test_FR_ACC_007_auditor_chi_doc(self):
		frappe.set_user(make_user("sp.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Specialty", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("NC Specialty", ptype), ptype)
		self.assertRaises(frappe.PermissionError, _new("CK-T04").insert)

	def test_FR_SVC_001_vai_tro_ngoai_ma_tran_khong_doc(self):
		frappe.set_user(make_user("sp.noroles@normcore.test"))
		self.assertFalse(frappe.has_permission("NC Specialty", "read"))
