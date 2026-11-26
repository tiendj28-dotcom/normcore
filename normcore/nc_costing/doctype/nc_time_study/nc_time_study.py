import frappe
from frappe import _
from frappe.model.document import Document

from normcore.norm import time_study

PUBLISHED = "Đã ban hành"


class NCTimeStudy(Document):
	"""Phiếu khảo sát bấm giờ (FR-TS-001, FR-TS-002). Lớp mỏng, logic ở norm/time_study.py."""

	def before_validate(self):
		if self.is_new():
			self._resolve_procedure()
			if not self.lines:
				for ln in time_study.lines_from_procedure(*self._procedure_rows()):
					self.append("lines", ln)

	def validate(self):
		if not self.observer:
			self.observer = frappe.session.user
		steps = {s.step_id for s in frappe.get_doc("NC Clinical Procedure", self.procedure).steps}
		errors = time_study.line_errors([ln.as_dict() for ln in self.lines], steps)
		if errors:
			frappe.throw("<br>".join(errors), title=_("Dòng bấm giờ chưa hợp lệ"))

	def _resolve_procedure(self):
		if not self.procedure:
			self.procedure = frappe.db.get_value(
				"NC Clinical Procedure",
				{
					"technical_service": self.technical_service,
					"department": self.department,
					"workflow_state": PUBLISHED,
				},
				"name",
				order_by="version_no desc",
			)
			if not self.procedure:
				frappe.throw(_("Dịch vụ chưa có quy trình đã ban hành tại khoa này."))
			return
		proc = frappe.db.get_value(
			"NC Clinical Procedure",
			self.procedure,
			["workflow_state", "technical_service", "department"],
			as_dict=True,
		)
		if (
			not proc
			or proc.workflow_state != PUBLISHED
			or proc.technical_service != self.technical_service
			or proc.department != self.department
		):
			frappe.throw(_("Quy trình phải đã ban hành và khớp dịch vụ, khoa của phiếu."))

	def _procedure_rows(self):
		proc = frappe.get_doc("NC Clinical Procedure", self.procedure)
		steps = [{"step_id": s.step_id, "idx": s.idx} for s in proc.steps]
		res = [r.as_dict() for r in proc.resources]
		return steps, res
