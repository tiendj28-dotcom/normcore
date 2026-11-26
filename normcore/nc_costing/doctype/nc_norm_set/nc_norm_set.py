import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, today

from normcore.costing import parameters
from normcore.norm import validation, workflow
from normcore.norm.init_from_procedure import RESOURCE_DOCTYPE_BY_COMPONENT, lines_from_resources

DRAFT = workflow.DRAFT
CONFIRMED = workflow.CONFIRMED
LOCKED = workflow.LOCKED
REPLACED = workflow.REPLACED
PUBLISHED = "Đã ban hành"
COMPONENT_DOCTYPE = {k: {v} for k, v in RESOURCE_DOCTYPE_BY_COMPONENT.items()}  # DI-05 (giữ tên cũ)

# Trường nhập của dòng (không gồm xác nhận): đổi một trong các trường này là "sửa dòng".
LINE_INPUTS = (
	"line_id",
	"step_id",
	"service_level",
	"procedure_resource_row",
	"component",
	"resource_doctype",
	"resource",
	"headcount",
	"hospital_qty",
	"authority_qty",
	"authority_ref",
	"uom",
	"wastage_rate",
	"wastage_reason",
	"basis",
	"basis_ref",
	"is_excluded",
	"exclude_reason",
	"ai_suggested",
)
HEAD_FIELDS = ("technical_service", "department", "procedure", "version_no")
CONFIRM_FIELDS = ("confirmed_by", "confirmed_on")


def _norm(v):
	if v in (None, "", 0):
		return None
	if isinstance(v, (int, float)):
		return float(v)
	return v


def _inputs(row) -> tuple:
	return tuple(_norm(row.get(f)) for f in LINE_INPUTS)


def effective_wastage_cap(on=None):
	"""ASM-012-10: trần hao hụt (%) của bộ tham số hiệu lực; (giá trị, tên bộ hoặc None)."""
	rows = frappe.get_all(
		"NC Costing Parameter Set", fields=["name", "effective_from", "wastage_cap"], order_by="name"
	)
	for r in rows:
		r["effective_from"] = getdate(r["effective_from"]) if r.get("effective_from") else None
	chosen = validation.effective_parameter_set(rows, getdate(on or today()))
	if not chosen:
		return parameters.DEFAULTS["wastage_cap"], None
	return float(chosen["wastage_cap"] or 0), chosen["name"]


class NCNormSet(Document):
	def validate(self):
		prev = self.get_doc_before_save()
		self.validate_frozen(prev)
		self.validate_status_change(prev)
		if (
			self.is_new()
			and frappe.db.get_value("NC Clinical Procedure", self.procedure, "workflow_state") != PUBLISHED
		):
			# FR-NORM-002, TC-NORM-02: kiểm ở mọi đường tạo, không chỉ make_norm_set
			frappe.throw(_("Quy trình chưa ban hành, không khởi tạo được bộ định mức"))
		self.assign_line_ids()
		if not prev or prev.status == DRAFT:
			self.validate_lines(prev)

	# --- khóa nội dung (FR-NORM-012, ASM-012-05) ---
	def validate_frozen(self, prev):
		if not prev:
			return
		if prev.status == REPLACED or (prev.status == LOCKED and not self.flags.allow_replace):
			frappe.throw(_("Bộ định mức đã khóa, không sửa được."), title=_("Bản ghi đã khóa"))
		if prev.status == CONFIRMED and not self.flags.norm_action:
			changed_head = any(_norm(self.get(f)) != _norm(prev.get(f)) for f in HEAD_FIELDS)
			old = [_inputs(r) for r in prev.lines]
			new = [_inputs(r) for r in self.lines]
			if changed_head or old != new:
				frappe.throw(
					_("Bộ định mức đã xác nhận chuyên môn, không sửa được. Cần NC Finance trả lại về Nháp."),
					title=_("Bản ghi đã khóa"),
				)

	def validate_status_change(self, prev):
		if prev is None:
			if self.status == LOCKED and not self.flags.allow_lock:
				frappe.throw(_("Chỉ đổi trạng thái bằng nút trên lưới định mức"))
			return
		if self.status == prev.status:
			return
		action = self.flags.norm_action
		ok = (
			(action and workflow.next_status(prev.status, action) == self.status)
			or (self.flags.allow_lock and self.status == LOCKED)
			or (self.flags.allow_replace and self.status == REPLACED)
		)
		if not ok:
			frappe.throw(_("Chỉ đổi trạng thái bằng nút trên lưới định mức"))

	def on_trash(self):
		if self.status in (LOCKED, REPLACED):
			frappe.throw(_("Bộ định mức đã khóa, không xóa được."), title=_("Bản ghi đã khóa"))

	def assign_line_ids(self):
		prev = self.get_doc_before_save()
		if prev:
			old = {r.name: r.line_id for r in prev.lines}
			for r in self.lines:
				if r.name in old and r.line_id != old[r.name]:
					frappe.throw(_("Mã dòng {0} bất biến, không đổi được").format(old[r.name]))
		used = [int(r.line_id[1:]) for r in self.lines if r.line_id and r.line_id[1:].isdigit()]
		counter = max([cint(self.next_line_seq), *used])
		for r in self.lines:
			if not r.line_id:
				counter += 1
				r.line_id = f"L{counter:03d}"
		self.next_line_seq = counter

	def validate_lines(self, prev):
		"""FR-NORM-003..005, 008, 013, DI-04, DI-05 qua norm.validation.line_errors; gom mọi lỗi một lần."""
		step_ids = {s.step_id for s in frappe.get_doc("NC Clinical Procedure", self.procedure).steps}
		cap, _source = effective_wastage_cap()
		old = {r.name: r for r in prev.lines} if prev else {}
		errors = []
		for r in self.lines:
			before = old.get(r.name)
			if prev:
				changed = before is None or _inputs(before) != _inputs(r)
			else:  # khởi tạo từ quy trình: dòng chưa liên kết được lưu (AMD-012-01); dòng thêm tay phải đủ
				changed = not r.procedure_resource_row
			ctx = {"step_ids": step_ids, "wastage_cap": cap, "changed": changed}
			errors += validation.line_errors(r.as_dict(), ctx)
			confirming = self.flags.norm_action == "confirm_line"
			if confirming:
				continue
			if changed:  # ASM-012-06: sửa dòng thì xóa xác nhận của dòng đó
				r.confirmed_by = r.confirmed_on = None
			elif before is not None:  # không cho đổi xác nhận bằng đường khác
				for f in CONFIRM_FIELDS:
					r.set(f, before.get(f))
		if errors:
			frappe.throw("<br>".join(errors), title=_("Dòng định mức chưa hợp lệ"))

	@frappe.whitelist()
	def lock(self):
		"""Khóa (FR-NORM-011): chỉ NC Finance, chỉ từ "Đã xác nhận chuyên môn" (ASM-012-04)."""
		return lock_norm_set(self)


def lock_norm_set(ns):
	"""Thân của `lock` và `api.norm.lock_set`. Kiểm vai trò trước kiểm trạng thái."""
	if "NC Finance" not in frappe.get_roles():
		frappe.throw(_("Chỉ NC Finance được khóa bộ định mức"), frappe.PermissionError)
	if ns.status != CONFIRMED:
		frappe.throw(_("Chỉ khóa được bộ định mức Đã xác nhận chuyên môn"))
	# DI-03: mỗi (dịch vụ, khoa) tối đa một bộ đã khóa; bộ cũ chuyển "Đã thay thế"
	for name in frappe.get_all(
		"NC Norm Set",
		{
			"technical_service": ns.technical_service,
			"department": ns.department,
			"status": LOCKED,
			"name": ["!=", ns.name],
		},
		pluck="name",
	):
		old = frappe.get_doc("NC Norm Set", name)
		old.status = REPLACED
		old.flags.allow_replace = True  # qua save() để track_changes ghi lịch sử
		old.flags.norm_action = "replace"
		old.save(ignore_permissions=True)
	ns.status = LOCKED
	ns.locked_by = frappe.session.user
	ns.locked_on = now_datetime()
	ns.flags.norm_action = "lock_set"
	ns.save(ignore_permissions=True)
	return ns.status


def create_from_procedure(procedure):
	"""FR-NORM-001/002: bộ "Nháp" từ quy trình "Đã ban hành", mỗi dòng nguồn lực một dòng định mức."""
	frappe.has_permission("NC Norm Set", "create", throw=True)
	proc = frappe.get_doc("NC Clinical Procedure", procedure)
	if proc.workflow_state != PUBLISHED:
		frappe.throw(_("Quy trình chưa ban hành, không khởi tạo được bộ định mức"))
	lines, errors = lines_from_resources([r.as_dict() for r in proc.resources])
	if errors:
		frappe.throw("<br>".join(errors))
	version = (
		frappe.db.get_value(
			"NC Norm Set",
			{"technical_service": proc.technical_service, "department": proc.department},
			"max(version_no)",
		)
		or 0
	) + 1
	ns = frappe.new_doc("NC Norm Set")
	ns.update(
		{
			"technical_service": proc.technical_service,
			"department": proc.department,
			"procedure": proc.name,
			"version_no": version,
			"status": DRAFT,
		}
	)
	if not frappe.has_permission("NC Norm Set", "create", doc=ns):  # phạm vi theo khoa (FR-ACC-003)
		frappe.throw(_("Bạn không có quyền tạo bộ định mức cho khoa này"), frappe.PermissionError)
	for ln in lines:
		ns.append("lines", ln)
	ns.insert()
	return ns.name


@frappe.whitelist()
def make_norm_set(procedure):
	"""Đường cũ của nút form quy trình (FEAT-000); gọi `create_from_procedure`."""
	return create_from_procedure(procedure)
