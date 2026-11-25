import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from normcore.procedure.codes import next_code

DRAFT = "Nháp"
PUBLISHED = "Đã ban hành"
LABOR_TYPE = "Nhân lực"
LABOR_UOM = "phút"
CLOSED_STATES = (PUBLISHED, "Đã thay thế", "Đã thu hồi")


class NCClinicalProcedure(Document):
	def before_insert(self):
		self.validate_single_active()  # trước khi đặt tên, để báo lỗi rõ thay vì trùng khóa

	def validate(self):
		self.check_state_transition()
		self.validate_single_active()
		self.validate_citations()
		self.assign_step_ids()
		self.assign_resource_ids()
		self.validate_resources()

	def before_save(self):
		self.check_content_lock()

	def on_trash(self):
		if self.workflow_state != DRAFT:  # DI-07
			frappe.throw(_("Chỉ xóa được quy trình ở trạng thái Nháp."), title=_("Bản ghi đã khóa"))

	def check_state_transition(self):
		if not self.workflow_state:
			self.workflow_state = DRAFT
		prev = self.get_doc_before_save()
		before = prev.workflow_state if prev else DRAFT
		# Trạng thái chỉ đổi qua api.procedure_workflow.apply_action (đặt flags.workflow_action)
		if self.workflow_state != before and not self.flags.workflow_action:
			frappe.throw(_("Chỉ đổi trạng thái bằng các nút của luồng duyệt"))
		if self.is_new() and self.workflow_state != DRAFT:
			frappe.throw(_("Quy trình mới phải ở trạng thái Nháp"))

	def check_content_lock(self):
		"""FR-WF-008, DI-07, ASM-007-03: ngoài "Nháp" không sửa nội dung."""
		prev = self.get_doc_before_save()
		if not prev or prev.workflow_state == DRAFT:
			return
		if _content(prev) == _content(self) and self._header_unchanged(prev):
			return
		if prev.workflow_state in CLOSED_STATES:
			msg = _("Quy trình đã ban hành, không sửa được. Tạo phiên bản mới.")
		else:
			msg = _("Quy trình đang chờ duyệt, không sửa được. Từ chối để trả về Nháp.")
		frappe.throw(msg, title=_("Bản ghi đã khóa"))

	def _header_unchanged(self, prev):
		"""decision_no, effective_date chỉ đổi trong hành động "Ban hành"."""
		if self.flags.workflow_action == "Ban hành":
			return True
		return all((prev.get(f) or "") == (self.get(f) or "") for f in ("decision_no", "effective_date"))

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
				counter, r.step_id = next_code("S", counter, [s.step_id for s in self.steps])
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
				counter, r.resource_row_id = next_code(
					"R", counter, [x.resource_row_id for x in self.resources]
				)
		self.next_resource_seq = max(cint(counter), cint(self.next_resource_seq))

	def validate_single_active(self):
		"""DI-02: tối đa một bản đang soạn hoặc đang duyệt cho mỗi (dịch vụ, khoa)."""
		if (self.workflow_state or DRAFT) in CLOSED_STATES or self.flags.ignore_single_active:
			return
		other = frappe.db.get_value(
			"NC Clinical Procedure",
			{
				"technical_service": self.technical_service,
				"department": self.department,
				"workflow_state": ["not in", CLOSED_STATES],
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if other:
			frappe.throw(
				_("Dịch vụ này đã có bản đang soạn hoặc đang duyệt của khoa: {0}").format(other),
				title=_("Đã có bản đang soạn"),
			)

	def validate_citations(self):
		step_ids = {s.step_id for s in self.steps}
		for i, c in enumerate(self.citations, 1):
			if bool(c.target_section) == bool(c.target_step_id):
				frappe.throw(_("Trích dẫn dòng {0}: chọn đúng một trong phần hoặc mã bước").format(i))
			if c.target_step_id and c.target_step_id not in step_ids:
				frappe.throw(
					_("Trích dẫn dòng {0}: mã bước {1} không tồn tại trong quy trình").format(
						i, c.target_step_id
					)
				)
			c.relation = c.relation or "Chưa có căn cứ"

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
		"""Lớp mỏng cho nút "Ban hành" (FR-WF-005): chỉ NC Director, chỉ từ "Chờ ban hành"."""
		from normcore.api.procedure_workflow import apply_action

		if "NC Director" not in frappe.get_roles():
			frappe.throw(_("Chỉ NC Director được ban hành quy trình"), frappe.PermissionError)
		result = apply_action(
			self.name, "Ban hành", decision_no=self.decision_no, effective_date=self.effective_date
		)
		self.reload()
		return result["workflow_state"]


CONTENT_FIELDS = (
	"overview",
	"indications",
	"contraindications",
	"cautions",
	"preparation_notes",
	"monitoring",
	"references",
	"doctor_request",
	"technical_service",
	"department",
	"version_no",
	"previous_version",
	"copied_from",
	"ai_log",
	"next_step_seq",
	"next_resource_seq",
)
CONTENT_TABLES = ("steps", "resources", "citations")
_SKIP_CHILD = {"name", "modified", "creation", "modified_by", "owner", "idx", "parent", "parenttype", "parentfield", "docstatus", "doctype"}


def _norm(value):
	if value in (None, ""):
		return ""
	if isinstance(value, bool):
		return int(value)
	if isinstance(value, (int, float)):
		return float(value)
	return str(value)


def _content(doc):
	"""Bản chụp phần nội dung (trường, bảng con) để so trước và sau khi lưu."""
	out = {f: _norm(doc.get(f)) for f in CONTENT_FIELDS}
	for table in CONTENT_TABLES:
		rows = []
		for row in doc.get(table) or []:
			d = row.as_dict() if hasattr(row, "as_dict") else dict(row)
			rows.append({k: _norm(v) for k, v in d.items() if k not in _SKIP_CHILD})
		out[table] = rows
	return out
