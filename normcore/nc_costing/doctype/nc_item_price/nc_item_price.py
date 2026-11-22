import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime

VERIFIED = "Đã xác minh"
UNVERIFIED = "Chưa xác minh"
AUTO_CODE = re.compile(r"DG-\d+")
# ASM-069: các trường này bị khóa khi đơn giá đang "Đã xác minh"
LOCKED_WHEN_VERIFIED = (
	"item",
	"unit_price",
	"price_source",
	"document_no",
	"document_date",
	"valid_from",
	"valid_to",
	"attachment",
)


class NCItemPrice(Document):
	def validate(self):
		if self.unit_price is not None and self.unit_price <= 0:
			frappe.throw(_("Đơn giá phải lớn hơn 0"))
		if self.valid_to and self.valid_from and getdate(self.valid_to) < getdate(self.valid_from):
			frappe.throw(_("Ngày hết hiệu lực không được trước ngày bắt đầu hiệu lực"))
		self._check_price_code()
		self._check_locked()
		self._check_verification()

	def after_insert(self):
		if not self.price_code:  # ASM-071: để trống thì lấy bằng tên bản ghi
			self.db_set("price_code", self.name, update_modified=False)

	def _check_price_code(self):
		# mã tự đặt không được có dạng DG-<số> để không đụng mã tự sinh (AMD-005)
		if self.price_code and AUTO_CODE.fullmatch(self.price_code) and self.price_code != self.name:
			frappe.throw(
				_("Mã đơn giá {0} có dạng mã tự sinh DG-<số>, hãy đặt mã khác").format(self.price_code)
			)

	def _check_locked(self):
		"""ASM-069: đơn giá đã xác minh không đổi nội dung; phải bỏ xác minh trước (có thể cùng lượt lưu)."""
		was = self.get_doc_before_save()
		if not was or was.verification_status != VERIFIED or self.verification_status != VERIFIED:
			return
		changed = [f for f in LOCKED_WHEN_VERIFIED if self._norm(f, self.get(f)) != self._norm(f, was.get(f))]
		if changed:
			labels = ", ".join(_(self.meta.get_label(f)) for f in changed)
			frappe.throw(_("Đơn giá đã xác minh, không sửa được: {0}. Hãy bỏ xác minh trước.").format(labels))

	@staticmethod
	def _norm(fieldname, value):
		if fieldname in ("document_date", "valid_from", "valid_to"):
			return getdate(value) if value else None
		if fieldname == "unit_price":
			return flt(value, 4)
		return value or None

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
