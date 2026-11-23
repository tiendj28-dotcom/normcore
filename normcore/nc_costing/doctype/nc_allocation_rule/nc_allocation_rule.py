import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import allocation_rules as rules


class NCAllocationRule(Document):
	def validate(self):
		# FR-ACCT-008, BR-COST-009, ASM-127
		center_type = (
			frappe.db.get_value("NC Cost Center", self.cost_center, "center_type")
			if self.cost_center
			else None
		)
		errors = rules.rule_errors(self.level, self.cost_category, self.driver, center_type)
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors), title=_("Quy tắc chưa hợp lệ"))
		same = frappe.get_all(
			"NC Allocation Rule",
			{"level": self.level, "cost_category": self.cost_category, "name": ("!=", self.name)},
			["cost_center"],
		)
		if any((r.cost_center or "") == (self.cost_center or "") for r in same):
			where = _("trung tâm {0}").format(self.cost_center) if self.cost_center else _("mọi trung tâm")
			frappe.throw(
				_("Đã có quy tắc {0} cho {1} áp cho {2}").format(self.level, self.cost_category, where)
			)
