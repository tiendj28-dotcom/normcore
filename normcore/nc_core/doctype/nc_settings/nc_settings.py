import frappe
from frappe import _
from frappe.model.document import Document


class NCSettings(Document):
	def validate(self):
		from normcore.costing import compliance

		try:
			compliance.reminder_days(self.compliance_reminder_days)  # FR-ADM-006: không âm
		except ValueError:
			frappe.throw(_("Số ngày nhắc hạn hồ sơ tuân thủ không được âm"))

	def on_update(self):
		# TC-CLS-28: đổi số ngày nhắc thì trạng thái hồ sơ tính lại ngay (ASM-101)
		before = self.get_doc_before_save()
		if before is not None and before.compliance_reminder_days == self.compliance_reminder_days:
			return
		from normcore.api.compliance import refresh_all_statuses

		refresh_all_statuses()
