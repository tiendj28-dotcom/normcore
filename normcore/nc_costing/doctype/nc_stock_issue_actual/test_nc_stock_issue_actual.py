"""FEAT-035: NC Stock Issue Actual (FR-ACCT-015)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.tests.utils import ensure, make_base, make_user

DT = "NC Stock Issue Actual"


class TestNCStockIssueActual(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_, self.dept, _ = make_base()
		ensure(
			"NC Item",
			"item_code",
			"HC_GLU",
			item_name="Hóa chất glucose",
			item_type="Hóa chất",
			uom="Hộp",
			norm_uom="Test",
			norm_units_per_purchase_unit=200,
			nominal_tests=200,
		)
		self.fin = make_user("fin.sia@normcore.test", "NC Finance")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _s(self, **kw):
		return frappe.get_doc(
			{
				"doctype": DT,
				"fiscal_year": 2026,
				"department": self.dept,
				"item": "HC_GLU",
				"issued_qty": 94,
				**kw,
			}
		)

	def test_luu_va_trung_nam_khoa_mat_hang(self):
		frappe.set_user(self.fin)
		self.assertEqual(self._s().insert().issued_qty, 94)
		with self.assertRaisesRegex(frappe.ValidationError, "Đã có xuất kho năm 2026"):
			self._s().insert()
		self.assertTrue(self._s(fiscal_year=2025).insert().name)

	def test_luong_am(self):
		with self.assertRaises(frappe.ValidationError):
			self._s(issued_qty=-1).insert()

	def test_quyen(self):
		doc = self._s().insert()
		roles = ("NC Clinician", "NC Consultant", "NC Resource Manager")
		none = [make_user(f"sia.no{i}@normcore.test", r) for i, r in enumerate(roles)]
		director = make_user("sia.dir@normcore.test", "NC Director")
		frappe.set_user(make_user("sia.aud@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission(DT, "read", doc=doc))
		with self.assertRaises(frappe.PermissionError):
			self._s(fiscal_year=2025).insert()
		for user in none:
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission(DT, "read"), user)
		frappe.set_user(director)
		self.assertTrue(frappe.has_permission(DT, "read"))
		self.assertFalse(frappe.has_permission(DT, "write", doc=doc))

	def test_quyen_truong_khoa_chi_doc_khoa_minh(self):
		"""QA: NC Department Head chỉ thấy khoa được gán; khoa khác bị chặn, không ghi được."""
		own = self._s().insert(ignore_permissions=True)
		make_base(department="KHOA-KHAC")
		other = self._s(department="KHOA-KHAC").insert(ignore_permissions=True)
		head = make_user("sia.head@normcore.test", "NC Department Head")
		access.assign_department(head, self.dept)
		frappe.set_user(head)
		names = frappe.get_list(DT, pluck="name")
		self.assertIn(own.name, names)
		self.assertNotIn(other.name, names)
		self.assertTrue(frappe.has_permission(DT, "read", doc=own))
		self.assertFalse(frappe.has_permission(DT, "read", doc=other))
		self.assertFalse(frappe.has_permission(DT, "create"))
		self.assertFalse(frappe.has_permission(DT, "write", doc=own))
		frappe.set_user("Administrator")
		frappe.set_user(make_user("sia.aud2@normcore.test", "NC Auditor"))
		self.assertEqual({own.name, other.name} - set(frappe.get_list(DT, pluck="name")), set())
