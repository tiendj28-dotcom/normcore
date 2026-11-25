import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import cls_volume

KEY = ("fiscal_year", "department", "item")


class NCStockIssueActual(Document):
	def validate(self):
		# FR-ACCT-015
		errors = [_(m) for _f, m in cls_volume.stock_errors(self.get)]
		if errors:
			frappe.throw("<br>".join(errors), title=_("Xuất kho chưa hợp lệ"))
		dup = frappe.db.exists(
			"NC Stock Issue Actual", {**{k: self.get(k) for k in KEY}, "name": ("!=", self.name)}
		)
		if dup:
			frappe.throw(
				_("Đã có xuất kho năm {0} của mặt hàng {1} tại khoa {2}").format(
					self.fiscal_year, self.item, self.department
				)
			)


def on_doctype_update():
	frappe.db.add_unique("NC Stock Issue Actual", list(KEY), constraint_name="unique_nc_stock_issue_actual")
