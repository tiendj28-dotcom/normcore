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

	def _service_dung(self, code="CK-T10"):
		_new(code).insert()
		frappe.get_doc(
			{
				"doctype": "NC Technical Service",
				"service_code": "DV-T10",
				"service_name": "DV thử",
				"specialty": code,
			}
		).insert()

	def test_FR_ADM_005_xoa_khi_dang_duoc_tham_chieu_bi_chan(self):
		self._service_dung()
		frappe.set_user(make_user("sp.admin@normcore.test", "NC Admin"))
		with self.assertRaises(frappe.LinkExistsError) as ctx:
			frappe.delete_doc("NC Specialty", "CK-T10")
		self.assertIn("DV-T10", str(ctx.exception))

	def test_FR_ADM_005_xoa_duoc_khi_khong_tham_chieu(self):
		_new("CK-T11").insert()
		frappe.set_user(make_user("sp.admin2@normcore.test", "NC Admin"))
		frappe.delete_doc("NC Specialty", "CK-T11")
		self.assertFalse(frappe.db.exists("NC Specialty", "CK-T11"))

	def test_FR_ACC_002_doc_controller_khong_xoa(self):
		_new("CK-T12").insert()
		frappe.set_user(make_user("sp.dc@normcore.test", "NC Document Controller"))
		self.assertRaises(frappe.PermissionError, frappe.delete_doc, "NC Specialty", "CK-T12")
