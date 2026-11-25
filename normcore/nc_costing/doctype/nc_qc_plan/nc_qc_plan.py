import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import qc_plans


class NCQCPlan(Document):
	def validate(self):
		values = {
			"test_system": self.test_system,
			"run_days_per_year": self.run_days_per_year,
			"iqc_lines": [r.as_dict() for r in self.iqc_lines],
			"calibration_lines": [r.as_dict() for r in self.calibration_lines],
		}
		codes = {r.get(f) for rows, f in ((self.iqc_lines, "qc_material"), (self.calibration_lines, "calibrator")) for r in rows}
		codes.discard(None)
		item_types = {}
		if codes:
			item_types = {
				i.name: i.item_type
				for i in frappe.get_all("NC Item", {"name": ["in", list(codes)]}, ["name", "item_type"])
			}
		errors = qc_plans.validate_qc_plan(values, item_types)
		if self.test_system:
			filters = {"test_system": self.test_system}
			if not self.is_new():
				filters["name"] = ["!=", self.name]
			other = frappe.db.get_value("NC QC Plan", filters)
			if other:
				errors.append(f"Hệ thống {self.test_system} đã có kế hoạch chất lượng {other}")
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors))
