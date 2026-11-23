import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import allocation_rules as rules

KEY = ("fiscal_year", "technical_service", "department", "scenario")


class NCServiceVolume(Document):
	def validate(self):
		# FR-ACCT-007, ASM-125
		errors = []
		if not rules.valid_year(self.fiscal_year):
			errors.append(_("Năm tài chính phải từ 2000 đến 2100"))
		errors += [_(e) for e in rules.volume_errors(self.volume)]
		if errors:
			frappe.throw("<br>".join(errors), title=_("Sản lượng chưa hợp lệ"))
		dup = frappe.db.exists(
			"NC Service Volume", {**{k: self.get(k) for k in KEY}, "name": ("!=", self.name)}
		)
		if dup:
			frappe.throw(
				_("Đã có sản lượng năm {0} của {1} tại khoa {2}, kịch bản {3}").format(
					self.fiscal_year, self.technical_service, self.department, self.scenario
				)
			)


def on_doctype_update():
	frappe.db.add_unique("NC Service Volume", list(KEY), constraint_name="unique_nc_service_volume")
