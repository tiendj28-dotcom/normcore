import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing.pricing import NORM_ITEM_TYPES


class NCItem(Document):
	def validate(self):
		if (self.reuse_count or 0) < 1:
			frappe.throw(_("Số lần dùng phải từ 1 trở lên"))
		self._check_norm_units()
		for field, label in (
			("nominal_tests", "Số test danh nghĩa"),
			("open_stability_days", "Hạn dùng sau mở"),
		):
			if (self.get(field) or 0) < 0:
				frappe.throw(_("{0} không được âm").format(label))

	def _check_norm_units(self):
		"""FR-RES-018, ASM-094: ba loại hóa chất phải khai số đơn vị định mức > 0 (không có mặc định);
		loại khác để trống thì tính là 1."""
		units = self.norm_units_per_purchase_unit
		if self.item_type in NORM_ITEM_TYPES:
			if not units or units <= 0:
				frappe.throw(
					_("Mặt hàng loại {0} phải có số đơn vị định mức trong một đơn vị mua lớn hơn 0").format(
						self.item_type
					)
				)
		elif not units:
			self.norm_units_per_purchase_unit = 1
		elif units < 0:
			frappe.throw(_("Số đơn vị định mức trong một đơn vị mua không được âm"))
