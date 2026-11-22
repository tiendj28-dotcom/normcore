import frappe
from frappe import _
from frappe.model.document import Document


class NCTechnicalService(Document):
	def validate(self):
		self.validate_departments()

	def validate_departments(self):
		"""Một khoa chỉ xuất hiện một lần trong khoa thực hiện (FR-SVC-003, ASM-056)."""
		seen = set()
		for row in self.departments or []:
			if row.department in seen:
				frappe.throw(
					_("Khoa {0} bị gán hai lần cho dịch vụ {1}").format(row.department, self.service_code)
				)
			seen.add(row.department)
