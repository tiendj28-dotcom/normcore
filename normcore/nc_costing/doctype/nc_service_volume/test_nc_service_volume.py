import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_base, make_user

FIN = "finance-vol@test.local"
AUD = "auditor-vol@test.local"
CLIN = "clinician-vol@test.local"


def _v(service, dept, **kw):
	return frappe.get_doc(
		{"doctype": "NC Service Volume", "fiscal_year": 2026, "technical_service": service, "department": dept, "volume": 4000, **kw}
	)


class TestNCServiceVolume(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_base()
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ACCT_05_mac_dinh_kich_ban_va_trung_bon_truong(self):
		frappe.set_user(FIN)
		v = _v(self.service, self.dept).insert()
		self.assertEqual(v.scenario, "Thực tế 12 tháng")
		with self.assertRaisesRegex(frappe.ValidationError, "Đã có sản lượng năm 2026"):
			_v(self.service, self.dept).insert()
		self.assertTrue(_v(self.service, self.dept, scenario="Kế hoạch").insert().name)

	def test_san_luong_am_va_nam_sai(self):
		frappe.set_user(FIN)
		with self.assertRaises(frappe.ValidationError):
			_v(self.service, self.dept, volume=-1).insert()
		with self.assertRaises(frappe.ValidationError):
			_v(self.service, self.dept, fiscal_year=1999).insert()
		self.assertTrue(_v(self.service, self.dept, volume=0).insert().name)

	def test_quyen(self):
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission("NC Service Volume", "read"))
		for p in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Service Volume", p), p)
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission("NC Service Volume", "read"))
		frappe.set_user(FIN)
		self.assertTrue(frappe.has_permission("NC Service Volume", "create"))
		self.assertFalse(frappe.has_permission("NC Service Volume", "delete"))
