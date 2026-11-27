"""NORM-66: hook phạm vi khoa ghi Error Log khi từ chối (chẩn đoán 403 trên staging), không đổi kết quả quyền."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import permissions
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user

COST = "NC Service Cost"
TITLE = permissions.DENY_LOG_TITLE


class TestPermissionDiagnostic(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.aud = make_user("aud.n66@normcore.test", "NC Auditor")
		self.head = make_user("head.n66@normcore.test", "NC Department Head")
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.cost = frappe.get_doc(
			{"doctype": COST, "department": self.dept, "technical_service": "DV-TEST-A"}
		)
		frappe.db.delete("Error Log", {"method": TITLE})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _logs(self):
		return frappe.get_all("Error Log", {"method": TITLE}, ["method", "error"], order_by="creation desc")

	def test_tu_choi_ghi_log_day_du(self):
		frappe.set_user(self.head)  # Dept Head chưa gán khoa: bị từ chối đọc
		self.assertIs(permissions.has_permission(self.cost, "read", self.head), False)
		logs = self._logs()
		self.assertEqual(len(logs), 1)
		info = json.loads(logs[0].error)
		self.assertEqual(info["user"], self.head)
		self.assertEqual(info["ptype"], "read")
		self.assertEqual(info["doctype"], COST)
		self.assertIn("NC Department Head", info["roles"])
		self.assertEqual(info["departments"], [])

	def test_cho_phep_khong_ghi_log_va_ket_qua_khong_doi(self):
		self.assertIsNone(permissions.has_permission(self.cost, "read", self.aud))
		frappe.set_user(self.aud)
		self.assertTrue(frappe.has_permission(COST, "read", doc=self.cost))
		self.assertEqual(self._logs(), [])
