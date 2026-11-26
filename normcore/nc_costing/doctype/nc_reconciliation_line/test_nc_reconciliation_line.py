"""FEAT-037: mở rộng NC Reconciliation Line (recon_type, department, item, technical_service, qty, recon_status)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.patches import backfill_reconciliation_type as patch
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user

CLIN = "clin.recon37@normcore.test"
AUD = "aud.recon37@normcore.test"
DT = "NC Reconciliation Line"


class TestNCReconciliationLine(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		make_user(CLIN, "NC Clinician")
		make_user(AUD, "NC Auditor")
		self.params, self.dept, _ = cf.make_golden_world()
		self.run = cf.make_golden_run(self.params)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _insert(self, **kw):
		doc = frappe.get_doc({"doctype": DT, "costing_run": self.run.name, **kw})
		doc.flags.from_costing = True
		return doc.insert(ignore_permissions=True)

	def test_tai_chinh_bat_buoc_trung_tam_loai(self):
		with self.assertRaises(frappe.ValidationError):
			self._insert(recon_type="Tài chính")
		with self.assertRaises(frappe.ValidationError):
			self._insert()  # thiếu recon_type = Tài chính (mặc định)
		ok = self._insert(cost_center="K01", cost_category="LABOR")
		self.assertEqual((ok.recon_type, ok.recon_status), ("Tài chính", "Đã đối soát"))

	def test_vat_chat_khong_can_trung_tam(self):
		line = self._insert(
			recon_type="Vật chất", department=self.dept_name(), calculated_qty=5, recon_status="Chưa đối soát"
		)
		self.assertEqual((line.recon_type, line.cost_center, line.cost_category), ("Vật chất", None, None))

	def dept_name(self):
		return frappe.db.get_value("NC Department", {}, "name") or self.dept

	def test_patch_backfill_reconciliation_type(self):
		line = self._insert(cost_center="K01", cost_category="LABOR")
		frappe.db.sql(f"UPDATE `tab{DT}` SET recon_type = NULL, recon_status = NULL WHERE name = %s", line.name)
		patch.execute()
		patch.execute()  # chạy lại không đổi gì thêm
		got = frappe.db.get_value(DT, line.name, ["recon_type", "recon_status"])
		self.assertEqual(tuple(got), ("Tài chính", "Đã đối soát"))

	def test_quyen_clinician_khong_doc_auditor_doc_khong_sua(self):
		line = self._insert(cost_center="K01", cost_category="LABOR")
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission(DT, "read", doc=line))
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission(DT, "read", doc=line))
		self.assertFalse(frappe.has_permission(DT, "write", doc=line))
