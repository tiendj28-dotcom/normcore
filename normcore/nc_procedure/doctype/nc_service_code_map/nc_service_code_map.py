import frappe
from frappe.model.document import Document


class NCServiceCodeMap(Document):
	pass


def on_doctype_update():
	"""DI-09: chỉ mục duy nhất (hệ thống nguồn, mã ngoài) khi hai người lưu đồng thời (ASM-110)."""
	frappe.db.add_unique(
		"NC Service Code Map", ["source_system", "external_code"], constraint_name="unique_source_code"
	)
