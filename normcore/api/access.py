"""API gán người dùng vào khoa (FR-ACC-006, UC-017 bước 3). Kiểm vai trò NC Admin trong từng hàm (G3)."""

import frappe

from normcore.core import permissions


@frappe.whitelist()
def assign_department(user, department):
	return permissions.assign_department(user, department)


@frappe.whitelist()
def unassign_department(user, department):
	return permissions.unassign_department(user, department)


@frappe.whitelist()
def list_department_users(department):
	permissions.assert_can_assign()
	return frappe.get_all(
		"User Permission", {"allow": permissions.DEPARTMENT, "for_value": department}, pluck="user"
	)
