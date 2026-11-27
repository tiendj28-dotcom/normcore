"""NORM-76: hook has_permission không trả None (Frappe v16 coi None là từ chối → 403 đọc bản ghi).

Gọi thẳng hook trên bản ghi chưa lưu, nên chạy đúng cả trên Frappe v15 (CI) lẫn v16 (staging).
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import permissions
from normcore.tests.utils import ensure, make_user

DOCTYPES = ("NC Clinical Procedure", "NC Service Cost", "NC Norm Set")


class TestPermissionHookNoneIsDeny(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure(
			"NC Cost Center", "cost_center_code", "KHOA-N76-A", cost_center_name="A", center_type="Lâm sàng"
		)
		ensure(
			"NC Cost Center", "cost_center_code", "KHOA-N76-B", cost_center_name="B", center_type="Lâm sàng"
		)
		for code in ("KHOA-N76-A", "KHOA-N76-B"):
			ensure(
				"NC Department",
				"department_code",
				code,
				department_name=code,
				department_type="Lâm sàng",
				cost_center=code,
			)
		self.users = {
			role: make_user(f"{role.split()[-1].lower()}.n76@normcore.test", role)
			for role in ("NC Auditor", "NC Finance", "NC Director")
		}
		self.clin = make_user("clin.n76@normcore.test", "NC Clinician")
		permissions.assign_department(self.clin, "KHOA-N76-A")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _doc(self, doctype, dept):
		return frappe.get_doc({"doctype": doctype, "department": dept})

	def test_vai_khong_gioi_han_khoa_nhan_true(self):
		for user in self.users.values():
			for dt in DOCTYPES:
				for dept in ("KHOA-N76-A", "KHOA-N76-B"):
					for ptype in ("read", "write"):
						res = permissions.has_permission(self._doc(dt, dept), ptype, user)
						self.assertIs(res, True, (user, dt, dept, ptype))

	def test_clinician_dung_khoa_true_khac_khoa_false(self):
		for dt in DOCTYPES:
			self.assertIs(
				permissions.has_permission(self._doc(dt, "KHOA-N76-A"), "read", self.clin), True, dt
			)
			self.assertIs(
				permissions.has_permission(self._doc(dt, "KHOA-N76-A"), "write", self.clin), True, dt
			)
			self.assertIs(
				permissions.has_permission(self._doc(dt, "KHOA-N76-B"), "read", self.clin), False, dt
			)
			self.assertIs(
				permissions.has_permission(self._doc(dt, "KHOA-N76-B"), "write", self.clin), False, dt
			)
