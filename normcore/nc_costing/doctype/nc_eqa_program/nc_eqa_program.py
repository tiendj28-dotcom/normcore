import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import qc_plans


class NCEQAProgram(Document):
	def validate(self):
		self.eqa_code = (self.eqa_code or "").strip()
		values = {f: self.get(f) for f in qc_plans.LABELS if f not in ("technical_service", "share_pct")}
		values["services"] = [r.as_dict() for r in self.services]
		codes = [r.technical_service for r in self.services if r.technical_service]
		paraclinical = set()
		if codes:
			paraclinical = set(
				frappe.get_all(
					"NC Technical Service", {"name": ["in", codes], "is_paraclinical": 1}, pluck="name"
				)
			)
		errors = qc_plans.validate_eqa_program(values, paraclinical)
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors))
