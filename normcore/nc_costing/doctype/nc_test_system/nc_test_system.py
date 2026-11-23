import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import test_systems


class NCTestSystem(Document):
	def validate(self):
		self.test_system_code = (self.test_system_code or "").strip()
		basis = None
		if self.main_equipment:
			basis = frappe.db.get_value("NC Equipment", self.main_equipment, "allocation_basis")
		paraclinical = bool(
			self.technical_service
			and frappe.db.get_value("NC Technical Service", self.technical_service, "is_paraclinical")
		)
		values = {f: self.get(f) for f in test_systems.LABELS}
		errors = test_systems.validate_test_system(values, basis, paraclinical)
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors))
