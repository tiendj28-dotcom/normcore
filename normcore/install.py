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


# TBD-05, ASM-074: hai loại giá mẫu, là dữ liệu cấu hình; ghi rõ là giả định
SAMPLE_PRICE_CATEGORIES = [
	{
		"category_code": "GIA-BV",
		"category_name": "Giá do bệnh viện quyết định (Giả định — chờ xác nhận)",
		"approval_authority": "Bệnh viện",
		"include_depreciation": 0,
		"include_accumulation": 1,
	},
	{
		"category_code": "GIA-NN",
		"category_name": "Giá theo cơ quan có thẩm quyền (Giả định — chờ xác nhận)",
		"approval_authority": "Cơ quan có thẩm quyền",
		"include_depreciation": 1,
		"include_accumulation": 0,
	},
]


def ensure_sample_price_categories():
	for row in SAMPLE_PRICE_CATEGORIES:
		if not frappe.db.exists("NC Price Category", row["category_code"]):
			frappe.get_doc({"doctype": "NC Price Category", **row}).insert(ignore_permissions=True)


def before_install():
	ensure_roles()


def ensure_default_account_mapping():
	"""FR-ACCT-009, ASM-118 (TBD-03): bảng ánh xạ mặc định chế độ Hành chính sự nghiệp.

	Chỉ chèn dòng (chế độ, tiền tố) chưa có: không ghi đè giá trị NC Finance đã sửa.
	"""
	from normcore.costing import accounting

	for prefix, category in accounting.DEFAULT_ACCOUNT_MAPPING:
		filters = {"accounting_regime": accounting.DEFAULT_REGIME, "account_prefix": prefix}
		if not frappe.db.exists("NC Account Mapping", filters):
			frappe.get_doc(
				{
					"doctype": "NC Account Mapping",
					**filters,
					"cost_category": category,
					"note": accounting.ASSUMPTION_NOTE,
				}
			).insert(ignore_permissions=True)


def after_install():
	from normcore.ai.prompts_install import ensure_default_templates

	ensure_roles()
	ensure_workflow_states()
	ensure_sample_price_categories()
	ensure_default_account_mapping()
	ensure_default_templates()
