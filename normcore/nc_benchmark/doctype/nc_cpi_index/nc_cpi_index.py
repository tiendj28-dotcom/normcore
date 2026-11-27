import frappe
from frappe import _
from frappe.model.document import Document

from normcore.benchmark.reference import month_start


class NCCPIIndex(Document):
	"""Chỉ số giá tiêu dùng theo tháng (FR-BM-006). Nguồn chỉ số: TBD-11, ASM-026-09."""

	def validate(self):
		if self.month:
			self.month = month_start(self.month)
		if self.index_value is not None and self.index_value <= 0:
			frappe.throw(_("Chỉ số giá phải lớn hơn 0"))
		if self.month and frappe.db.exists("NC CPI Index", {"month": self.month, "name": ["!=", self.name]}):
			frappe.throw(_("Đã có chỉ số giá tháng {0}").format(self.month.strftime("%m/%Y")))
