import frappe
from frappe import _
from frappe.model.document import Document

from normcore.core import settings


POSITIVE = (
	("min_time_study_cases", "Số ca bấm giờ tối thiểu"),
	("price_valid_months", "Hạn tham chiếu đơn giá (tháng)"),
	("benchmark_window_months", "Cửa sổ giá tham chiếu (tháng)"),
	("min_benchmark_facilities", "Số đơn vị tham chiếu tối thiểu"),
)


class NCSettings(Document):
	def validate(self):
		from normcore.costing import compliance

		try:
			compliance.reminder_days(self.compliance_reminder_days)  # FR-ADM-006: không âm
		except ValueError:
			frappe.throw(_("Số ngày nhắc hạn hồ sơ tuân thủ không được âm"))
		for field, label in POSITIVE:
			value = self.get(field)
			if value in (None, ""):  # chưa đặt (site cũ): lưu mặc định, tránh lưu 0 làm hỏng lần lưu sau
				value = settings.DEFAULTS[field]
				self.set(field, value)
			if value is not None and int(value) <= 0:
				frappe.throw(_("{0} phải lớn hơn 0").format(_(label)))
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
