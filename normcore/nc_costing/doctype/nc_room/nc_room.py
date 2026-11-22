import frappe
from frappe.model.document import Document

from normcore.costing import resources


class NCRoom(Document):
	def validate(self):
		# FR-RES-008, BR-COST-005
		errors = resources.validate_room(self.as_dict())
		if errors:
			frappe.throw("<br>".join(errors), title="Phòng chưa hợp lệ")
