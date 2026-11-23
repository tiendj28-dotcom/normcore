from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import allocation_rules as rules


class NCCostCenterDriver(Document):
	def validate(self):
		# FR-ACCT-010, ASM-126
		errors = []
		if not rules.valid_year(self.fiscal_year):
			errors.append(_("Năm tài chính phải từ 2000 đến 2100"))
		errors += [
			_(e)
			for e in rules.driver_errors(
				{"headcount": self.headcount, "area_m2": self.area_m2, "revenue": self.revenue}
			)
		]
		if errors:
			frappe.throw("<br>".join(errors), title=_("Tiêu chí chưa hợp lệ"))
		dup = frappe.db.exists(
			"NC Cost Center Driver",
			{"fiscal_year": self.fiscal_year, "cost_center": self.cost_center, "name": ("!=", self.name)},
		)
		if dup:
			frappe.throw(_("Đã có tiêu chí năm {0} của trung tâm {1}").format(self.fiscal_year, self.cost_center))


def on_doctype_update():
	frappe.db.add_unique(
		"NC Cost Center Driver", ["fiscal_year", "cost_center"], constraint_name="unique_nc_cost_center_driver"
	)


def get_driver_values(fiscal_year, driver) -> dict:
	"""{trung tâm: giá trị} của tiêu chí cấp 1 trong năm; bản ghi trống bị bỏ qua (FEAT-017 dùng)."""
	field = rules.DRIVER_FIELDS.get(driver)
	if field is None:
		raise ValueError(f"Tiêu chí {driver} không lưu theo trung tâm chi phí")
	rows = frappe.get_all("NC Cost Center Driver", {"fiscal_year": fiscal_year}, ["cost_center", field])
	return {r.cost_center: Decimal(str(r[field])) for r in rows if r[field] not in (None, 0, 0.0)}
