import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

VERIFIED = "Đã xác minh"
UNVERIFIED = "Chưa xác minh"


class NCItemPrice(Document):
	def validate(self):
		if self.unit_price is not None and self.unit_price <= 0:
			frappe.throw(_("Đơn giá phải lớn hơn 0"))
		if self.valid_to and self.valid_from and self.valid_to < self.valid_from:
			frappe.throw(_("Ngày hết hiệu lực không được trước ngày bắt đầu hiệu lực"))
		self._check_verification()

	def _check_verification(self):
		"""FR-RES-016: Đã xác minh cần tệp chứng từ; người xác minh và thời điểm do hệ thống ghi."""
		if self.verification_status != VERIFIED:
			self.verified_by = None
			self.verified_on = None
			return
		if not self.attachment:
			frappe.throw(_("Chưa thể xác minh đơn giá: cần đính kèm tệp chứng từ"))
		was = self.get_doc_before_save()
		if was and was.verification_status == VERIFIED:
			self.verified_by, self.verified_on = was.verified_by, was.verified_on  # không tự sửa
		else:
			self.verified_by = frappe.session.user
			self.verified_on = now_datetime()
