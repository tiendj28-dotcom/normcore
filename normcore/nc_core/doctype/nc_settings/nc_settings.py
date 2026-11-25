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
		if self.approval_reminder_days is not None and int(self.approval_reminder_days) <= 0:
			frappe.throw(_("Số ngày nhắc duyệt phải lớn hơn 0"))
		# AMD-007-01: thư ký hội đồng phải có vai trò NC Council Member
		if self.council_secretary and "NC Council Member" not in frappe.get_roles(self.council_secretary):
			frappe.throw(_("Thư ký hội đồng phải là người dùng có vai trò NC Council Member"))

	def on_update(self):
		# TC-CLS-28: đổi số ngày nhắc thì trạng thái hồ sơ tính lại ngay (ASM-101)
		before = self.get_doc_before_save()
		if before is not None and before.compliance_reminder_days == self.compliance_reminder_days:
			return
		from normcore.api.compliance import refresh_all_statuses

		refresh_all_statuses()
