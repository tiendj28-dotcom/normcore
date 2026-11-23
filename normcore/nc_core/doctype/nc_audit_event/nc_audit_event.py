from frappe.model.document import Document

from normcore.core.audit import guard_immutable, guard_insert


class NCAuditEvent(Document):
	def before_insert(self):
		guard_insert(self)

	def validate(self):
		guard_immutable(self)

	def on_trash(self):
		guard_immutable(self, force=True)
