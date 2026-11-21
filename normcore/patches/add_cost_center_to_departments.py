"""FEAT-001 (ASM-003, G2): mỗi khoa đã có được một trung tâm chi phí cùng mã, cùng tên. Chạy lại không tạo trùng."""

import frappe


def execute():
	frappe.reload_doc("nc_core", "doctype", "nc_cost_center")
	frappe.reload_doc("nc_core", "doctype", "nc_department")
	for d in frappe.get_all(
		"NC Department", fields=["name", "department_name", "department_type"], filters={"cost_center": ["is", "not set"]}
	):
		if not frappe.db.exists("NC Cost Center", d.name):
			frappe.get_doc(
				{
					"doctype": "NC Cost Center",
					"cost_center_code": d.name,
					"cost_center_name": d.department_name,
					"center_type": "Hỗ trợ" if d.department_type == "Hỗ trợ" else "Lâm sàng",
				}
			).insert(ignore_permissions=True)
		frappe.db.set_value("NC Department", d.name, "cost_center", d.name, update_modified=False)
