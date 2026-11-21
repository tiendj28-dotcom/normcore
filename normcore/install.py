"""Cài đặt dữ liệu nền: 10 vai trò (FR-ACC-002), Workflow State của skeleton."""

import frappe

ROLES = [
	"NC Clinician",
	"NC Department Head",
	"NC Council Member",
	"NC Finance",
	"NC Resource Manager",
	"NC Document Controller",
	"NC Director",
	"NC Consultant",
	"NC Admin",
	"NC Auditor",
]

WORKFLOW_STATES = ["Nháp", "Đã ban hành"]


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def ensure_workflow_states():
	for state in WORKFLOW_STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(
				ignore_permissions=True
			)


def before_install():
	ensure_roles()


def after_install():
	ensure_roles()
	ensure_workflow_states()
