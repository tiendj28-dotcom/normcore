"""FEAT-029 T03: NC Procedure Change Request (FR-ADJ-007; FR-ACC-003, 007), technical-design 2.3, 2.4."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import permissions
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_base, make_user

DOCTYPE = "NC Procedure Change Request"


class TestNCProcedureChangeRequest(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user("fin.n83@normcore.test", "NC Finance")
		self.aud = make_user("aud.n83@normcore.test", "NC Auditor")
		self.head = make_user("head.n83@normcore.test", "NC Department Head")
		self.clin = make_user("clin.n83@normcore.test", "NC Clinician")
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.proc = frappe.get_value(
			"NC Clinical Procedure", {"technical_service": "DV-TEST-A", "department": self.dept}
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _make(self, **kw):
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"procedure": self.proc,
				"requested_by": self.fin,
				"proposed_change": "Quy tắc BR-ADJ-003: đổi mặt hàng",
				**kw,
			}
		)
		doc.flags.pcr_write = True
		return doc.insert(ignore_permissions=True)

	def test_quyen_clinician_khong_doc(self):
		doc = self._make()
		permissions.assign_department(self.clin, self.dept)
		frappe.set_user(self.clin)
		self.assertFalse(frappe.has_permission(DOCTYPE, "read", doc=doc))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(DOCTYPE, doc.name).check_permission("read")

	def test_quyen_auditor_chi_doc(self):
		doc = self._make()
		frappe.set_user(self.aud)
		self.assertTrue(frappe.has_permission(DOCTYPE, "read", doc=doc))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission(DOCTYPE, ptype), ptype)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				{"doctype": DOCTYPE, "procedure": self.proc, "requested_by": self.aud, "proposed_change": "x"}
			).insert()

	def test_quyen_truong_khoa_theo_khoa(self):
		doc = self._make()
		make_base("DV-N83-X", "KHOA-N83-X")
		permissions.assign_department(self.head, "KHOA-N83-X")
		frappe.set_user(self.head)
		self.assertFalse(frappe.has_permission(DOCTYPE, "read", doc=doc))
		self.assertEqual(frappe.get_list(DOCTYPE, pluck="name"), [])
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, self.dept)
		frappe.set_user(self.head)
		self.assertTrue(frappe.has_permission(DOCTYPE, "read", doc=doc))
		self.assertEqual(frappe.get_list(DOCTYPE, pluck="name"), [doc.name])
		self.assertFalse(frappe.has_permission(DOCTYPE, "write", doc=doc))
		self.assertFalse(frappe.has_permission(DOCTYPE, "delete", doc=doc))

	def test_quyen_finance_tao(self):
		frappe.set_user(self.fin)
		self.assertTrue(frappe.has_permission(DOCTYPE, "create"))
		self.assertFalse(frappe.has_permission(DOCTYPE, "delete"))
		doc = frappe.get_doc(
			{"doctype": DOCTYPE, "procedure": self.proc, "requested_by": self.fin, "proposed_change": "x"}
		)
		doc.flags.pcr_write = True
		doc.insert()
		self.assertEqual(doc.status, "Mới")
		self.assertTrue(doc.name.startswith("YCSQT-"))

	def test_sua_ngoai_api_bi_chan(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{"doctype": DOCTYPE, "procedure": self.proc, "requested_by": self.fin, "proposed_change": "x"}
			).insert(ignore_permissions=True)
		doc = self._make()
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.proposed_change = "đổi"
		with self.assertRaises(frappe.ValidationError):
			d.save(ignore_permissions=True)

	def test_chuyen_trang_thai_sai_bi_chan(self):
		doc = self._make()
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.flags.pcr_write = True
		d.status = "Đã thực hiện"  # Mới -> Đã thực hiện không hợp lệ
		with self.assertRaises(frappe.ValidationError):
			d.save(ignore_permissions=True)
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.flags.pcr_write = True
		d.status = "Đã tiếp nhận"
		d.save(ignore_permissions=True)
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.flags.pcr_write = True
		d.status = "Mới"  # không quay lại
		with self.assertRaises(frappe.ValidationError):
			d.save(ignore_permissions=True)
