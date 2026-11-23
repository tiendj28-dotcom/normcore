"""Sửa trạng thái vận hành sau cài đặt/migrate (NORM-9)."""

import frappe


def fix_home_page():
	"""Bất biến: không đồng thời is_setup_complete = true và desktop:home_page = setup-wizard.

	Frappe tự bật is_setup_complete khi đã có System User (installed_applications.update_versions),
	nhưng desktop:home_page vẫn là setup-wizard → /app tải lại vô hạn.
	"""
	if frappe.is_setup_complete() and frappe.db.get_default("desktop:home_page") == "setup-wizard":
		frappe.db.set_default("desktop:home_page", "workspace")
		frappe.clear_cache()


# SCR-DSK-007 (FEAT-006, L1): Desk giới hạn 4 cột ở màn ≤ 1366px, trong đó Tag và Trạng thái chiếm 2,
# nên Khoa chủ trì và Phiên bản bị cắt. Đặt List View Settings của DocType để hiện đủ 6 cột.
LIST_VIEW_TOTAL_FIELDS = {"NC Clinical Procedure": "6"}


def ensure_list_view_settings():
	for doctype, total in LIST_VIEW_TOTAL_FIELDS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		if frappe.db.exists("List View Settings", doctype):
			frappe.db.set_value("List View Settings", doctype, "total_fields", total)
		else:
			frappe.get_doc({"doctype": "List View Settings", "name": doctype, "total_fields": total}).insert(
				ignore_permissions=True
			)
	frappe.db.commit()
