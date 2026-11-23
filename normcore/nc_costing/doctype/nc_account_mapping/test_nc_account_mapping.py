import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user

FIN = "finance-map@test.local"
AUD = "auditor-map@test.local"
CLIN = "clinician-map@test.local"


def _m(prefix, cat="LABOR", **kw):
	return frappe.get_doc(
		{
			"doctype": "NC Account Mapping",
			"accounting_regime": "Hành chính sự nghiệp",
			"account_prefix": prefix,
			"cost_category": cat,
			**kw,
		}
	)


class TestNCAccountMapping(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_chuan_hoa_tien_to_va_chan_trung(self):
		frappe.set_user(FIN)
		doc = _m(" 7.77 x ").insert()
		self.assertEqual(doc.account_prefix, "777X")
		with self.assertRaisesRegex(frappe.ValidationError, "777X"):
			_m("777x", "UTILITY").insert()
		_m("777X", "UTILITY", accounting_regime="Doanh nghiệp").insert()  # chế độ khác thì được

	def test_tien_to_rong_bi_tu_choi(self):
		with self.assertRaises(frappe.ValidationError):
			_m(" . ").insert()

	def test_quyen_theo_ma_tran(self):
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission("NC Account Mapping", "read"))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Account Mapping", ptype), ptype)
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission("NC Account Mapping", "read"))
		frappe.set_user(FIN)
		self.assertTrue(frappe.has_permission("NC Account Mapping", "create"))
		self.assertFalse(frappe.has_permission("NC Account Mapping", "delete"))
