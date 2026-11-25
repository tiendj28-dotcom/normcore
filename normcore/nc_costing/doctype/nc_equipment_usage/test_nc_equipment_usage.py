"""FEAT-035: NC Equipment Usage (FR-ACCT-013, ASM-035-05)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.tests.utils import make_base, make_cls_data, make_user

DT = "NC Equipment Usage"


class TestNCEquipmentUsage(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()
		frappe.db.set_value("NC Equipment", "EQ_A", "allocation_basis", "Phút chiếm máy")
		self.fin = make_user("fin.eu@normcore.test", "NC Finance")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _u(self, equipment="EQ_A", **kw):
		return frappe.get_doc(
			{
				"doctype": DT,
				"fiscal_year": 2026,
				"equipment": equipment,
				"department": self.dept,
				"total_minutes": 120000,
				**kw,
			}
		)

	def test_thiet_bi_phut_chiem_may_luu_duoc_va_mac_dinh_kich_ban(self):
		frappe.set_user(self.fin)
		self.assertEqual(self._u().insert().scenario, "Thực tế 12 tháng")

	def test_thiet_bi_so_ket_qua_bi_tu_choi(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Số kết quả"):
			self._u("EQ_B").insert()

	def test_trung_bon_truong(self):
		self._u().insert()
		with self.assertRaisesRegex(frappe.ValidationError, "Đã có phút khai thác"):
			self._u().insert()
		self.assertTrue(self._u(scenario="Công suất").insert().name)

	def test_phut_am_hoac_nam_sai(self):
		for kw in ({"total_minutes": -1}, {"fiscal_year": 1999}):
			with self.assertRaises(frappe.ValidationError):
				self._u(**kw).insert()

	def test_quyen_auditor_clinician_head(self):
		doc = self._u().insert()
		aud = make_user("eu.aud@normcore.test", "NC Auditor")
		clin = make_user("eu.clin@normcore.test", "NC Clinician")
		head = make_user("eu.head@normcore.test", "NC Department Head")
		access.assign_department(head, self.dept)
		frappe.set_user(aud)
		self.assertTrue(frappe.has_permission(DT, "read", doc=doc))
		with self.assertRaises(frappe.PermissionError):
			self._u(scenario="Kế hoạch").insert()
		frappe.set_user(clin)
		self.assertFalse(frappe.has_permission(DT, "read"))
		frappe.set_user(head)
		self.assertIn(doc.name, frappe.get_list(DT, pluck="name"))
		self.assertFalse(frappe.has_permission(DT, "create"))

	def test_quyen_truong_khoa_chi_doc_khoa_minh(self):
		"""QA: NC Department Head chỉ thấy phút khai thác của khoa được gán."""
		own = self._u().insert(ignore_permissions=True)
		make_base(department="KHOA-KHAC")
		other = self._u(department="KHOA-KHAC").insert(ignore_permissions=True)
		head = make_user("eu.head2@normcore.test", "NC Department Head")
		access.assign_department(head, self.dept)
		frappe.set_user(head)
		names = frappe.get_list(DT, pluck="name")
		self.assertIn(own.name, names)
		self.assertNotIn(other.name, names)
		self.assertFalse(frappe.has_permission(DT, "read", doc=other))
		self.assertFalse(frappe.has_permission(DT, "write", doc=own))
		frappe.set_user("Administrator")
		frappe.set_user(make_user("eu.aud2@normcore.test", "NC Auditor"))
		names = frappe.get_list(DT, pluck="name")
		self.assertTrue({own.name, other.name} <= set(names))
