"""NC AI Norm Suggestion: đề xuất định mức cận lâm sàng của AI (FR-AI-016..018; AMD-038-01).

Chỉ tác vụ đề xuất tạo bản ghi. Không DocType tính giá nào đọc DocType này (FR-AI-008)."""

import frappe
from frappe import _
from frappe.model.document import Document

from normcore.ai import citation

PENDING = "Đề xuất"
ACCEPTED = "Đã chấp nhận"
REJECTED = "Đã bỏ"
REL_FOLLOW = "Theo hướng dẫn"
REL_NONE = "Chưa có căn cứ"


class NCAINormSuggestion(Document):
	def validate(self):
		self.check_relation_and_quote()
		self.check_catalog_flag()
		self.check_status()

	def check_relation_and_quote(self):
		if self.relation == REL_FOLLOW and not (self.legal_section and (self.quote or "").strip()):
			frappe.throw(_("Đề xuất theo hướng dẫn phải có mục tài liệu và đoạn trích"))
		if (self.quote or "").strip():
			if not self.legal_section:
				frappe.throw(_("Đoạn trích phải kèm mục tài liệu"))
			text = frappe.db.get_value("NC Legal Section", self.legal_section, "plain_text")
			if not citation.quote_in_text(self.quote, text):
				frappe.throw(_("Đoạn trích không có nguyên văn trong mục {0}").format(self.legal_section))

	def check_catalog_flag(self):
		if self.resource:
			self.not_in_catalog = 0

	def check_status(self):
		before = None if self.is_new() else self.get_doc_before_save()
		if before is None:
			if self.status != PENDING:
				frappe.throw(_("Đề xuất mới phải ở trạng thái {0}").format(PENDING))
			return
		if before.status != self.status and before.status != PENDING:
			frappe.throw(_("Đề xuất đã được xử lý"))
