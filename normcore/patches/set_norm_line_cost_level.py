"""FEAT-034 (ASM-034-19): dòng định mức có từ trước chưa có cấp phát sinh → Theo kết quả (RESULT). Chạy lại không đổi gì thêm."""

import frappe


def execute():
	frappe.reload_doc("nc_costing", "doctype", "nc_norm_line")
	frappe.reload_doc("nc_costing", "doctype", "nc_norm_set")
	frappe.db.sql(
		"UPDATE `tabNC Norm Line` SET cost_level = 'RESULT' WHERE cost_level IS NULL OR cost_level = ''"
	)
