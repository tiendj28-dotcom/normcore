import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, today

from normcore.costing import parameters
from normcore.norm import templates, validation, workflow
from normcore.norm.init_from_procedure import (
	RESOURCE_DOCTYPE_BY_COMPONENT,
	lines_from_resources,
	removed_flag,
)

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
	"cost_level",  # FEAT-034
	"apply_k",
	"attach_to",
	"attach_equipment",
	"template_item",
)
# FEAT-025: trường do tác vụ đề xuất liên kết / Chấp nhận / Bỏ ghi (cờ norm_action = "ai_link")
AI_LINK_FIELDS = ("component", "resource_doctype", "resource", "ai_suggested")
HEAD_FIELDS = ("technical_service", "department", "procedure", "version_no", "test_system", "tests_per_tube")
CONFIRM_FIELDS = ("confirmed_by", "confirmed_on")


def _norm(v):
	if v in (None, "", 0):
		return None
	if isinstance(v, (int, float)):
		return float(v)
	return v


def _inputs(row, skip=()) -> tuple:
	return tuple(_norm(row.get(f)) for f in LINE_INPUTS if f not in skip)


def guard_ai_fields(row, before, flags):
	"""FEAT-025 (TD 2.2): chỉ đường "ai_link" được đặt `ai_suggested` / `ai_confidence`. Đường khác: khôi phục
	từ dòng cũ (dòng mới: 0). Ngoại lệ: dòng trong `flags.ai_link_cleared` được 1 -> 0 (người dùng sửa liên kết)."""
	if flags.norm_action == "ai_link":
		return
	if before is None:
		row.ai_suggested, row.ai_confidence = 0, 0
	elif row.line_id in (flags.ai_link_cleared or ()) and not cint(row.ai_suggested):
		row.ai_confidence = 0
	else:
		row.ai_suggested, row.ai_confidence = before.ai_suggested, before.ai_confidence


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


def qc_items_of(test_system) -> set:
	"""ASM-034-10: mặt hàng của kế hoạch chất lượng của hệ thống (nội kiểm, chuẩn máy)."""
	if not test_system:
		return set()
	plans = frappe.get_all("NC QC Plan", {"test_system": test_system}, pluck="name")
	items = set()
	for name in plans:
		plan = frappe.get_doc("NC QC Plan", name)
		items |= {r.qc_material for r in plan.iqc_lines if r.qc_material}
		items |= {r.calibrator for r in plan.calibration_lines if r.calibrator}
	return items


def template_items_of(template) -> list[dict]:
	if not template:
		return []
	return [
		{
			"item_name": r.item_name,
			"component": r.component,
			"default_cost_level": r.default_cost_level,
			"is_mandatory": r.is_mandatory,
		}
		for r in frappe.get_doc("NC Norm Template", template).items
	]


def cls_ctx(ns) -> dict:
	"""Ngữ cảnh cận lâm sàng cho norm.validation (dùng chung controller và API)."""
	svc = frappe.db.get_value(
		"NC Technical Service", ns.technical_service, ["is_paraclinical", "cls_group"], as_dict=True
	)
	return {
		"paraclinical": bool(svc and svc.is_paraclinical),
		"cls_group": svc.cls_group if svc else None,
		"has_test_system": bool(ns.test_system),
		"qc_items": qc_items_of(ns.test_system),
		"mandatory_items": template_items_of(ns.norm_template),
		"template_items": {i["item_name"] for i in template_items_of(ns.norm_template)},
	}


class NCNormSet(Document):
	def autoname(self):
		"""ASM-034-02: bộ có hệ thống mang mã hệ thống trong tên; không có thì dùng `autoname` của JSON."""
		if self.test_system:
			self.name = f"DM-{self.technical_service}-{self.department}-{self.test_system}-v{self.version_no}"

	def validate(self):
		prev = self.get_doc_before_save()
		self.validate_frozen(prev)
		self.validate_status_change(prev)
		self.validate_test_system(prev)
		if (
			self.is_new()
			and frappe.db.get_value("NC Clinical Procedure", self.procedure, "workflow_state") != PUBLISHED
		):
			# FR-NORM-002, TC-NORM-02: kiểm ở mọi đường tạo, không chỉ make_norm_set
			frappe.throw(_("Quy trình chưa ban hành, không khởi tạo được bộ định mức"))
		self.assign_line_ids()
		if not prev or prev.status == DRAFT:
			self.validate_lines(prev)

	def validate_test_system(self, prev):
		"""DI-15 (ASM-034-01): hệ thống phải cùng dịch vụ, cùng khoa; khi tạo mới phải "Đang dùng"."""
		if not self.test_system:
			return
		ts = frappe.db.get_value(
			"NC Test System", self.test_system, ["technical_service", "department", "status"], as_dict=True
		)
		if not ts or ts.technical_service != self.technical_service or ts.department != self.department:
			frappe.throw(
				_("Hệ thống xét nghiệm {0} không thuộc dịch vụ/khoa của bộ định mức").format(self.test_system)
			)
		if not prev and ts.status != "Đang dùng":
			frappe.throw(_("Hệ thống xét nghiệm {0} đã ngừng dùng").format(self.test_system))

	# --- khóa nội dung (FR-NORM-012, ASM-012-05) ---
	def validate_frozen(self, prev):
		if not prev:
			return
		if prev.status == REPLACED or (prev.status == LOCKED and not self.flags.allow_replace):
			frappe.throw(_("Bộ định mức đã khóa, không sửa được."), title=_("Bản ghi đã khóa"))
		if prev.status == CONFIRMED:  # không thao tác nào từ đây (khóa, trả lại) được đổi nội dung
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
			# Tạo mới chỉ ở "Nháp" (FR-NORM-010, 011). Mã máy chủ tin cậy (ignore_permissions) dựng dữ liệu được
			# "Đã thay thế"; "Đã khóa" luôn cần allow_lock. Người dùng qua frappe.client/API không vượt được.
			if self.status == LOCKED and not self.flags.allow_lock:
				frappe.throw(_("Chỉ đổi trạng thái bằng nút trên lưới định mức"))
			if self.status != DRAFT and self.status != LOCKED and not self.flags.ignore_permissions:
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
		base = cls_ctx(self)
		for r in self.lines:  # ASM-034-07, 08, 09: đặt lại trường phụ thuộc trước khi so dòng cũ
			r.update(validation.normalize_line(r.as_dict(), base))
		errors = []
		creating_version = self.is_new() and self.flags.norm_action == "new_version"
		for r in self.lines:
			before = old.get(r.name)
			# FR-NORM-015, AMD-013-01: cờ chỉ do new_version đặt; mọi đường ghi khác chuẩn hóa lại
			r.step_removed = removed_flag(
				r.as_dict(), before and before.as_dict(), step_ids, creating_version
			)
			if prev:
				guard_ai_fields(r, before, self.flags)
				skip = AI_LINK_FIELDS if self.flags.norm_action == "ai_link" else ()
				changed = before is None or _inputs(before, skip) != _inputs(r, skip)
			else:  # khởi tạo từ quy trình: dòng chưa liên kết được lưu (AMD-012-01); dòng thêm tay phải đủ
				changed = not r.procedure_resource_row and not (self.flags.from_procedure and r.template_item)
			ctx = {"step_ids": step_ids, "wastage_cap": cap, "changed": changed, **base}
			errors += validation.line_errors(r.as_dict(), ctx)
			confirming = self.flags.norm_action == "confirm_line"
			if confirming:
				continue
			if changed or before is None:  # ASM-012-06; dòng tạo mới không mang xác nhận do client gửi
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
	ns.reload()  # nạp lại từ CSDL: bỏ mọi thay đổi do client gửi kèm (run_doc_method)
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
			"test_system": ns.test_system or ["is", "not set"],  # DI-03 theo hệ thống (ASM-034-14)
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


def next_version(service, department, test_system=None) -> int:
	"""ASM-034-02: version_no lớn nhất + 1 theo (dịch vụ, khoa, hệ thống)."""
	return (
		frappe.db.get_value(
			"NC Norm Set",
			{
				"technical_service": service,
				"department": department,
				"test_system": test_system or ["is", "not set"],
			},
			"max(version_no)",
		)
		or 0
	) + 1


def create_from_procedure(procedure, test_system=None):
	"""FR-NORM-001/002: bộ "Nháp" từ quy trình "Đã ban hành", mỗi dòng nguồn lực một dòng định mức.
	FEAT-034: gắn hệ thống, áp mẫu đang dùng của nhóm chuyên ngành, đặt nhân k mặc định (ASM-034-03, 04, 06)."""
	frappe.has_permission("NC Norm Set", "create", throw=True)
	proc = frappe.get_doc("NC Clinical Procedure", procedure)
	if proc.workflow_state != PUBLISHED:
		frappe.throw(_("Quy trình chưa ban hành, không khởi tạo được bộ định mức"))
	lines, errors = lines_from_resources([r.as_dict() for r in proc.resources])
	if errors:
		frappe.throw("<br>".join(errors))
	svc = frappe.db.get_value(
		"NC Technical Service", proc.technical_service, ["is_paraclinical", "cls_group"], as_dict=True
	)
	paraclinical = bool(svc and svc.is_paraclinical)
	template = None
	if paraclinical:
		rows = frappe.get_all("NC Norm Template", fields=["name", "cls_group", "is_active"])
		template = templates.pick_template(rows, svc.cls_group)
		if template:
			lines = templates.apply_template(lines, template_items_of(template), paraclinical)
	if test_system and paraclinical:
		lines = templates.default_apply_k(lines)
	ns = frappe.new_doc("NC Norm Set")
	ns.update(
		{
			"technical_service": proc.technical_service,
			"department": proc.department,
			"procedure": proc.name,
			"test_system": test_system,
			"norm_template": template,
			"version_no": next_version(proc.technical_service, proc.department, test_system),
			"status": DRAFT,
		}
	)
	if not frappe.has_permission("NC Norm Set", "create", doc=ns):  # phạm vi theo khoa (FR-ACC-003)
		frappe.throw(_("Bạn không có quyền tạo bộ định mức cho khoa này"), frappe.PermissionError)
	for ln in lines:
		ns.append("lines", ln)
	ns.flags.from_procedure = True
	ns.insert()
	return ns.name


@frappe.whitelist()
def make_norm_set(procedure):
	"""Đường cũ của nút form quy trình (FEAT-000); gọi `create_from_procedure`."""
	return create_from_procedure(procedure)
