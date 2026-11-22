import frappe
from frappe import _
from frappe.model.document import Document

# FR-RES-018: ba loại phải khai số đơn vị định mức trong một đơn vị mua
NORM_TYPES = ("Hóa chất", "Chất chuẩn", "Vật liệu nội kiểm")


class NCItem(Document):
	def validate(self):
		if (self.reuse_count or 0) < 1:
			frappe.throw(_("Số lần dùng phải từ 1 trở lên"))
		units = self.norm_units_per_purchase_unit
		if self.item_type in NORM_TYPES and not units:
			frappe.throw(
				_("Mặt hàng loại {0} phải có số đơn vị định mức trong một đơn vị mua").format(self.item_type)
			)
		if units is not None and units < 0:
			frappe.throw(_("Số đơn vị định mức trong một đơn vị mua không được âm"))
		if units == 0 and self.item_type not in NORM_TYPES:
			self.norm_units_per_purchase_unit = 1  # mặc định 1 (ASM-072)
		for field, label in (
			("nominal_tests", "Số test danh nghĩa"),
			("open_stability_days", "Hạn dùng sau mở"),
		):
			if (self.get(field) or 0) < 0:
				frappe.throw(_("{0} không được âm").format(label))
