import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from normcore.api.compliance import get_reminder_days
from normcore.costing import compliance

AUTO_CODE = re.compile(r"HSTT-.+")
_FIELDS = (
	"equipment",
	"record_type",
	"cycle_months",
	"provider",
	"cost_per_time",
	"performed_on",
	"expiry_date",
	"attachment",
)


class NCEquipmentCompliance(Document):
	def validate(self):
		# FR-CMP-001, UC-020 1b; ASM-102
		errors = compliance.validate_record({k: self.get(k) for k in _FIELDS})
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors), frappe.ValidationError)
		if not frappe.db.exists("File", {"file_url": self.attachment, "is_private": 1}):
			frappe.throw(
				_("Tệp chứng từ {0} chưa được tải lên hoặc không phải tệp riêng tư").format(self.attachment)
			)
		self._check_record_code()
		# ASM-101: trạng thái do hệ thống tính, người dùng không sửa
		self.status = compliance.compute_status(self.expiry_date, getdate(nowdate()), get_reminder_days())

	def _check_record_code(self):
		if not self.record_code:  # để trống thì lấy bằng tên bản ghi (cùng cách price_code, ASM-093)
			self.record_code = self.name
		elif AUTO_CODE.fullmatch(self.record_code) and self.record_code != self.name:
			frappe.throw(
				_("Mã hồ sơ {0} có dạng mã tự sinh HSTT-<…>, hãy đặt mã khác").format(self.record_code)
			)
