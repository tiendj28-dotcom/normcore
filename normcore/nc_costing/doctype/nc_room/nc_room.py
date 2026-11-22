import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import resources


class NCRoom(Document):
	def validate(self):
		# FR-RES-008, BR-COST-005
		errors = resources.validate_room(self.as_dict())
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors), title=_("Phòng chưa hợp lệ"))
