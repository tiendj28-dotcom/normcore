import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import cls_volume

KEY = ("fiscal_year", "scenario", "equipment", "department")


class NCEquipmentUsage(Document):
	def validate(self):
		# FR-ACCT-013, ASM-035-05
		basis = (
			frappe.db.get_value("NC Equipment", self.equipment, "allocation_basis")
			if self.equipment
			else None
		)
		errors = [_(m) for _f, m in cls_volume.usage_errors(self.get, basis)]
		if errors:
			frappe.throw("<br>".join(errors), title=_("Phút khai thác chưa hợp lệ"))
		dup = frappe.db.exists(
			"NC Equipment Usage", {**{k: self.get(k) for k in KEY}, "name": ("!=", self.name)}
		)
		if dup:
			frappe.throw(
				_("Đã có phút khai thác năm {0}, kịch bản {1} của thiết bị {2} tại khoa {3}").format(
					self.fiscal_year, self.scenario, self.equipment, self.department
				)
			)


def on_doctype_update():
	frappe.db.add_unique("NC Equipment Usage", list(KEY), constraint_name="unique_nc_equipment_usage")
