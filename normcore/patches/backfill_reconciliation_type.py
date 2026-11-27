"""FEAT-037 (FR-COST-026..029): dòng đối soát có từ FEAT-017 mặc định recon_type = Tài chính, recon_status = Đã đối soát.
Select `default` không áp vào dòng đã có; chạy lại không đổi gì thêm."""

import frappe


def execute():
	frappe.reload_doc("nc_costing", "doctype", "nc_reconciliation_line")
	frappe.db.sql(
		"UPDATE `tabNC Reconciliation Line` SET recon_type = 'Tài chính' WHERE recon_type IS NULL OR recon_type = ''"
	)
	frappe.db.sql(
		"UPDATE `tabNC Reconciliation Line` SET recon_status = 'Đã đối soát' "
		"WHERE recon_status IS NULL OR recon_status = ''"
	)
