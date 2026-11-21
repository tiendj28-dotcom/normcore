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
