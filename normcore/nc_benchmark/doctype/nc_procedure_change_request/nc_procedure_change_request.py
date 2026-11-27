import frappe
from frappe import _
from frappe.model.document import Document

NEW, ACCEPTED, REJECTED, DONE = "Mới", "Đã tiếp nhận", "Từ chối", "Đã thực hiện"
# Luồng trạng thái (FR-ADJ-007, ASM-029-11)
TRANSITIONS = {NEW: (ACCEPTED, REJECTED), ACCEPTED: (REJECTED, DONE), REJECTED: (), DONE: ()}


class NCProcedureChangeRequest(Document):
	"""Yêu cầu sửa đổi quy trình từ Bàn so sánh giá (FR-ADJ-007).

	Tạo và đổi trạng thái chỉ qua API (`flags.pcr_write`, ASM-029-10/11).
	"""

	def validate(self):
		if not self.flags.pcr_write:
			frappe.throw(_("Yêu cầu sửa quy trình chỉ tạo và xử lý qua Bàn so sánh giá"))
		if self.is_new():
			self.status = self.status or NEW
			if self.status != NEW:
				frappe.throw(_("Yêu cầu mới phải ở trạng thái {0}").format(NEW))
			return
		before = self.get_doc_before_save()
		if before is None:
			return
		if before.status != self.status and self.status not in TRANSITIONS.get(before.status, ()):
			frappe.throw(_("Không chuyển được yêu cầu từ {0} sang {1}").format(before.status, self.status))
		for f in ("procedure", "requested_by", "source_suggestion", "proposed_change"):
			if (self.get(f) or None) != (before.get(f) or None):
				frappe.throw(_("Không sửa nội dung yêu cầu, chỉ đổi trạng thái"))
