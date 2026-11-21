import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

DRAFT = "Nháp"
PUBLISHED = "Đã ban hành"
LABOR_TYPE = "Nhân lực"
LABOR_UOM = "phút"


def _next_code(prefix, counter, existing_codes):
	"""Cấp mã bất biến từ bộ đếm trên bản ghi cha, không tái dùng mã đã xóa (DI-01, ADR-002)."""
	used = [
		int(c[len(prefix) :])
		for c in existing_codes
		if c and c.startswith(prefix) and c[len(prefix) :].isdigit()
	]
	nxt = max([cint(counter), *used]) + 1
	return nxt, f"{prefix}{nxt:03d}"


class NCClinicalProcedure(Document):
	def validate(self):
		self.check_state_transition()
		self.assign_step_ids()
		self.assign_resource_ids()
		self.validate_resources()

	def before_save(self):
		prev = self.get_doc_before_save()
		if prev and prev.workflow_state == PUBLISHED:
			frappe.throw(
				_("Quy trình đã ban hành, không sửa được. Tạo phiên bản mới."), title=_("Bản ghi đã khóa")
			)

	def on_trash(self):
		if self.workflow_state == PUBLISHED:
			frappe.throw(_("Quy trình đã ban hành, không xóa được."), title=_("Bản ghi đã khóa"))

	def check_state_transition(self):
		if not self.workflow_state:
			self.workflow_state = DRAFT
		prev = self.get_doc_before_save()
		before = prev.workflow_state if prev else DRAFT
		if self.workflow_state != before and not self.flags.allow_publish:
			frappe.throw(_("Chỉ đổi trạng thái bằng nút Ban hành"))
		if self.is_new() and self.workflow_state != DRAFT:
			frappe.throw(_("Quy trình mới phải ở trạng thái Nháp"))

	def assign_step_ids(self):
		prev = self.get_doc_before_save()
		if prev:  # mã bước đã cấp không được đổi (DI-01)
			old = {r.name: r.step_id for r in prev.steps}
			for r in self.steps:
				if r.name in old and r.step_id != old[r.name]:
					frappe.throw(_("Mã bước {0} bất biến, không đổi được").format(old[r.name]))
		seen = set()
		for r in self.steps:
			if r.step_id:
				if r.step_id in seen:
					frappe.throw(_("Mã bước {0} bị trùng").format(r.step_id))
				seen.add(r.step_id)
		counter = self.next_step_seq
		for r in self.steps:
			if not r.step_id:
				counter, r.step_id = _next_code("S", counter, [s.step_id for s in self.steps])
		self.next_step_seq = max(cint(counter), cint(self.next_step_seq))

	def assign_resource_ids(self):
		prev = self.get_doc_before_save()
		if prev:
			old = {r.name: r.resource_row_id for r in prev.resources}
			for r in self.resources:
				if r.name in old and r.resource_row_id != old[r.name]:
					frappe.throw(_("Mã dòng {0} bất biến, không đổi được").format(old[r.name]))
		counter = self.next_resource_seq
		for r in self.resources:
			if not r.resource_row_id:
				counter, r.resource_row_id = _next_code(
					"R", counter, [x.resource_row_id for x in self.resources]
				)
		self.next_resource_seq = max(cint(counter), cint(self.next_resource_seq))

	def validate_resources(self):
		step_ids = {s.step_id for s in self.steps}
		for r in self.resources:
			if r.step_id not in step_ids:  # data-model 3.3: step_id phải tồn tại trong steps
				frappe.throw(
					_("Dòng nguồn lực {0}: mã bước {1} không tồn tại trong quy trình").format(
						r.resource_row_id, r.step_id
					)
				)
			if r.resource_type == LABOR_TYPE and (r.uom or "").strip() != LABOR_UOM:
				frappe.throw(
					_('Dòng nguồn lực {0}: nguồn lực nhân lực phải tính bằng phút (đơn vị "{1}")').format(
						r.resource_row_id, LABOR_UOM
					)
				)

	@frappe.whitelist()
	def publish(self):
		"""Nút tạm "Ban hành" (FEAT-007 sẽ thay bằng Workflow, dữ liệu không đổi). Chỉ NC Director; FR-WF-005."""
		if "NC Director" not in frappe.get_roles():
			frappe.throw(_("Chỉ NC Director được ban hành quy trình"), frappe.PermissionError)
		if self.workflow_state == PUBLISHED:
			frappe.throw(_("Quy trình đã ban hành"))
		if not self.decision_no or not self.effective_date:
			frappe.throw(_("Cần nhập số quyết định ban hành và ngày hiệu lực trước khi ban hành"))
		self.workflow_state = PUBLISHED
		self.flags.allow_publish = True
		self.save(ignore_permissions=True)
		return self.workflow_state
