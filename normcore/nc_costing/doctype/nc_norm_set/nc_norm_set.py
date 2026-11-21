import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

DRAFT = "Nháp"
LOCKED = "Đã khóa"
REPLACED = "Đã thay thế"
PUBLISHED = "Đã ban hành"
COMPONENT_DOCTYPE = {  # DI-05
	"LABOR": {"NC Job Title"},
	"DRUG": {"NC Item"},
	"SUPPLY": {"NC Item"},
	"UTILITY": {"NC Item"},
	"EQUIPMENT": {"NC Equipment"},
	"INFRA": {"NC Room"},
}


class NCNormSet(Document):
	def validate(self):
		prev = self.get_doc_before_save()
		if prev and prev.status == LOCKED and not self.flags.allow_replace:
			frappe.throw(_("Bộ định mức đã khóa, không sửa được."), title=_("Bản ghi đã khóa"))
		if self.status == LOCKED and not self.flags.allow_lock and not (prev and prev.status == LOCKED):
			frappe.throw(_("Chỉ khóa bộ định mức bằng nút Khóa"))
		self.assign_line_ids()
		self.validate_lines()

	def on_trash(self):
		if self.status == LOCKED:
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

	def validate_lines(self):
		step_ids = {s.step_id for s in frappe.get_doc("NC Clinical Procedure", self.procedure).steps}
		for r in self.lines:
			allowed = COMPONENT_DOCTYPE.get(r.component)
			if allowed and r.resource_doctype not in allowed:  # DI-05
				frappe.throw(
					_("Dòng {0}: cấu phần {1} phải gắn {2}").format(
						r.line_id, r.component, " / ".join(allowed)
					)
				)
			if not cint(r.service_level) and r.step_id not in step_ids:  # DI-04
				frappe.throw(
					_("Dòng {0}: mã bước {1} không tồn tại trong quy trình").format(r.line_id, r.step_id)
				)

	@frappe.whitelist()
	def lock(self):
		"""Nút tạm "Khóa": chỉ NC Finance, Nháp -> Đã khóa (luồng xác nhận chuyên môn là FEAT-012)."""
		if "NC Finance" not in frappe.get_roles():
			frappe.throw(_("Chỉ NC Finance được khóa bộ định mức"), frappe.PermissionError)
		if self.status != DRAFT:
			frappe.throw(_("Chỉ khóa được bộ định mức ở trạng thái Nháp"))
		# DI-03: mỗi (dịch vụ, khoa) tối đa một bộ đã khóa; bộ cũ chuyển "Đã thay thế"
		for name in frappe.get_all(
			"NC Norm Set",
			{
				"technical_service": self.technical_service,
				"department": self.department,
				"status": LOCKED,
				"name": ["!=", self.name],
			},
			pluck="name",
		):
			frappe.db.set_value("NC Norm Set", name, "status", REPLACED)
		self.status = LOCKED
		self.locked_by = frappe.session.user
		self.locked_on = now_datetime()
		self.flags.allow_lock = True
		self.save(ignore_permissions=True)
		return self.status


@frappe.whitelist()
def make_norm_set(procedure):
	"""FR-NORM-001/002: khởi tạo bộ định mức từ quy trình "Đã ban hành"; mỗi nguồn lực Nhân lực -> một dòng LABOR."""
	frappe.has_permission("NC Norm Set", "create", throw=True)
	proc = frappe.get_doc("NC Clinical Procedure", procedure)
	if proc.workflow_state != PUBLISHED:
		frappe.throw(_("Quy trình chưa ban hành, không khởi tạo được bộ định mức"))
	version = (
		frappe.db.count(
			"NC Norm Set", {"technical_service": proc.technical_service, "department": proc.department}
		)
		+ 1
	)
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
	for r in proc.resources:
		if r.resource_type != "Nhân lực":
			continue
		if r.linked_doctype != "NC Job Title" or not r.linked_name:
			frappe.throw(_("Dòng nguồn lực {0} chưa gắn chức danh (NC Job Title)").format(r.resource_row_id))
		ns.append(
			"lines",
			{
				"step_id": r.step_id,
				"procedure_resource_row": r.resource_row_id,
				"component": "LABOR",
				"resource_doctype": "NC Job Title",
				"resource": r.linked_name,
				"headcount": r.headcount or 1,
				"hospital_qty": r.quantity,
				"uom": r.uom,
				"basis": "Quy trình",
			},
		)
	ns.insert()
	return ns.name
