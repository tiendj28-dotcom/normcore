import frappe
from frappe import _
from frappe.model.document import Document

from normcore.procedure import approval

PROCEDURE = "NC Clinical Procedure"


class NCReviewComment(Document):
	"""Ý kiến thẩm định gắn với phần hoặc bước của quy trình (FR-WF-003, ASM-007-05)."""

	def validate(self):
		if self.is_new():
			self.validate_target()
		else:
			self.validate_only_resolved_changes()

	def validate_target(self):
		if self.ref_doctype != PROCEDURE:
			frappe.throw(_("Ý kiến thẩm định chỉ gắn với quy trình kỹ thuật"))
		if not (self.comment or "").strip():
			frappe.throw(_("Cần nhập nội dung ý kiến"))
		if self.target_section and self.target_step_id:
			frappe.throw(_("Chọn phần hoặc mã bước, không chọn cả hai"))
		state, steps = frappe.db.get_value(PROCEDURE, self.ref_name, "workflow_state"), []
		if state not in approval.PENDING_STATES:
			frappe.throw(_("Chỉ ghi ý kiến khi quy trình đang chờ duyệt"))
		if self.target_step_id:
			steps = frappe.get_all("NC Procedure Step", {"parent": self.ref_name}, pluck="step_id")
			if self.target_step_id not in steps:
				frappe.throw(_("Mã bước {0} không tồn tại trong quy trình").format(self.target_step_id))
		self.review_state = state

	def validate_only_resolved_changes(self):
		prev = self.get_doc_before_save()
		if not prev:
			return
		for f in ("ref_doctype", "ref_name", "target_section", "target_step_id", "comment", "review_state"):
			if (prev.get(f) or "") != (self.get(f) or ""):
				frappe.throw(_("Chỉ được đổi trạng thái đã xử lý của ý kiến"))
