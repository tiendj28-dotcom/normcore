from frappe.model.document import Document

from normcore.core.audit import guard_immutable


class NCAILog(Document):
	def validate(self):
		guard_immutable(self)

	def on_trash(self):
		guard_immutable(self, force=True)
