import frappe
from frappe import _
from frappe.model.document import Document

from normcore.benchmark import rules

STATUS_NEW, STATUS_ACCEPTED, STATUS_REJECTED = "Mới", "Chấp nhận", "Từ chối"
STATUS_FORWARDED = "Đã chuyển yêu cầu sửa quy trình"
DECIDED = (STATUS_ACCEPTED, STATUS_REJECTED, STATUS_FORWARDED)


class NCAdjustmentSuggestion(Document):
	"""Gợi ý điều chỉnh do quy tắc sinh (FR-ADJ-005); quyết định qua API (FR-ADJ-008, ASM-028-09).

	`flags.adj_system`: máy chủ sinh/cập nhật gợi ý; `flags.adj_decision`: API quyết định đặt.
	"""

	def validate(self):
		if self.rule_code not in rules.RULE_CODES:
			frappe.throw(_("Quy tắc {0} không hợp lệ").format(self.rule_code))
		if self.is_new():
			if not (self.flags.adj_system or self.flags.adj_decision):
				self.status = STATUS_NEW
			if self.status in DECIDED and not self.flags.adj_decision:
				frappe.throw(_("Quyết định gợi ý qua Bàn so sánh giá"))
		else:
			before = self.get_doc_before_save()
			if before and before.status in DECIDED:
				frappe.throw(_("Gợi ý đã có quyết định, không sửa được"))
			if not (self.flags.adj_system or self.flags.adj_decision):
				frappe.throw(_("Quyết định gợi ý qua Bàn so sánh giá"))
		if self.status == STATUS_REJECTED and not (self.decision_reason or "").strip():
			frappe.throw(_("Từ chối gợi ý phải nêu lý do"))
