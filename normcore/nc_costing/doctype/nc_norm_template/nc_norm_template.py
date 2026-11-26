import frappe
from frappe import _
from frappe.model.document import Document

from normcore.norm import templates


class NCNormTemplate(Document):
	def validate(self):
		"""FR-NORM-021: ASM-034-03, 21 qua norm.templates.template_errors."""
		self.template_code = (self.template_code or "").strip()
		other = []
		if self.is_active and self.cls_group:
			other = frappe.get_all(
				"NC Norm Template",
				{"cls_group": self.cls_group, "is_active": 1, "name": ["!=", self.name or ""]},
				pluck="name",
			)
		values = {
			"template_code": self.template_code,
			"cls_group": self.cls_group,
			"is_active": self.is_active,
			"items": [r.as_dict() for r in self.items],
		}
		errors = templates.template_errors(values, other)
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors), title=_("Mẫu định mức chưa hợp lệ"))
