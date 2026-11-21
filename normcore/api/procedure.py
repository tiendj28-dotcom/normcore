"""API trình soạn quy trình (CLAUDE.md mục 4; NFR-SEC-003): kiểm quyền tường minh trong từng hàm.

Mọi ghi đi qua `doc.save()` để `track_changes` ghi lịch sử (FR-PROC-009, ADR-014); hàm `update_*` sửa dòng
tại chỗ để lịch sử có giá trị trước và sau.
"""

import frappe
from frappe import _

from normcore.procedure.copying import copy_structure
from normcore.procedure.steps import reorder

DT = "NC Clinical Procedure"
DRAFT = "Nháp"
PUBLISHED = "Đã ban hành"
CLOSED_STATES = (PUBLISHED, "Đã thay thế", "Đã thu hồi")
LABOR = "Nhân lực"
LABOR_UOM = "phút"
# 8 phần cố định của FR-PROC-001 theo thứ tự; "steps" là bảng các bước
SECTIONS = [
	("overview", "Đại cương"),
	("indications", "Chỉ định"),
	("contraindications", "Chống chỉ định"),
	("cautions", "Thận trọng"),
	("preparation_notes", "Chuẩn bị"),
	("steps", "Các bước tiến hành"),
	("monitoring", "Theo dõi và xử trí tai biến"),
	("references", "Tài liệu tham khảo"),
]
TEXT_FIELDS = [k for k, _label in SECTIONS if k != "steps"]
STEP_FIELDS = ("step_id", "phase", "step_title", "description", "reference_minutes")
RESOURCE_FIELDS = (
	"resource_row_id",
	"step_id",
	"resource_type",
	"resource_text",
	"linked_doctype",
	"linked_name",
	"quantity",
	"uom",
	"headcount",
)
CITATION_FIELDS = ("name", "target_section", "target_step_id", "relation", "quote", "deviation_reason")
RELATIONS = ("Theo hướng dẫn", "Khác biệt", "Chưa có căn cứ")


class ExistingProcedureError(frappe.ValidationError):
	"""Đã có quy trình cho (dịch vụ, khoa); `existing` là tên bản đó (FR-PROC-002, Q3)."""

	existing = None


def _deny(message):
	frappe.throw(message, frappe.PermissionError)


def _require(ptype, doc=None, message=None):
	if not frappe.has_permission(DT, ptype, doc=doc):
		_deny(message or _("Bạn không có quyền thực hiện thao tác này"))


def _editable(procedure):
	"""Tải quy trình để sửa: kiểm quyền ghi, rồi từ chối nếu không ở "Nháp" (DI-07, FR-WF-008)."""
	_require("write", doc=procedure, message=_("Bạn không có quyền sửa quy trình này"))
	doc = frappe.get_doc(DT, procedure)
	if doc.workflow_state != DRAFT:
		frappe.throw(_("Quy trình không ở trạng thái Nháp, không sửa được"))
	return doc


def _save(doc):
	# FR-PROC-009: luôn ghi lịch sử. Frappe mặc định tắt Version khi chạy test (flags.in_test), nên chỉ rõ.
	doc.save(ignore_version=False)


def _row(doc, table, key, value, label):
	for r in doc.get(table):
		if r.get(key) == value:
			return r
	frappe.throw(_("Không thấy {0} {1}").format(label, value))


def _dump(row, fields):
	return {f: row.get(f) for f in fields}


def _find_existing(technical_service, department):
	rows = frappe.get_all(
		DT,
		filters={"technical_service": technical_service, "department": department},
		fields=["name", "workflow_state", "version_no"],
		order_by="version_no desc",
	)
	draft = next((r.name for r in rows if r.workflow_state not in CLOSED_STATES), None)
	published = next((r.name for r in rows if r.workflow_state == PUBLISHED), None)
	return draft, published, (rows[0].version_no if rows else 0), (rows[0].name if rows else None)


def _refuse_if_exists(technical_service, department):
	draft, published, version, latest = _find_existing(technical_service, department)
	if published:
		message = _("Dịch vụ đã có quy trình ban hành; tạo phiên bản mới thuộc chức năng sửa đổi") + f" ({published})"
		existing = published
	elif draft:
		message = _("Dịch vụ này đã có bản đang soạn hoặc đang duyệt của khoa: {0}").format(draft)
		existing = draft
	else:
		return version, latest
	frappe.msgprint(message, title=_("Đã có quy trình"), indicator="red")
	frappe.local.response["existing_procedure"] = existing
	err = ExistingProcedureError(message)
	err.existing = existing
	raise err


@frappe.whitelist()
def list_procedures(state=None, department=None, needs_review=None):
	"""Quy trình mà người dùng đọc được (frappe.get_list đã lọc theo quyền)."""
	frappe.has_permission(DT, "read", throw=True)
	filters = {}
	if state:
		filters["workflow_state"] = state
	if department:
		filters["department"] = department
	if needs_review not in (None, "", "0", 0, False):
		filters["needs_review"] = 1
	return frappe.get_list(
		DT,
		filters=filters,
		fields=["name", "technical_service", "department", "version_no", "workflow_state", "needs_review"],
		order_by="modified desc",
		limit_page_length=100,
	)


@frappe.whitelist()
def find_existing(technical_service, department):
	"""Tên bản đang soạn/duyệt và bản đã ban hành của (dịch vụ, khoa), để giao diện dẫn tới."""
	frappe.has_permission(DT, "read", throw=True)
	draft, published, _v, _n = _find_existing(technical_service, department)
	return {"draft": draft, "published": published}


@frappe.whitelist()
def create_procedure(technical_service, department):
	"""FR-PROC-001/002: bản nháp phiên bản 1 (hoặc kế tiếp) với 8 phần cố định; Q3: từ chối khi đã ban hành."""
	_require("create", message=_("Bạn không có quyền tạo quy trình"))
	version, latest = _refuse_if_exists(technical_service, department)
	doc = frappe.get_doc(
		{
			"doctype": DT,
			"technical_service": technical_service,
			"department": department,
			"version_no": version + 1,
			"previous_version": latest,
		}
	)
	doc.insert()
	return {"name": doc.name, "version_no": doc.version_no}


@frappe.whitelist()
def get_procedure(name, step_id=None, section=None):
	"""Dữ liệu cho trình soạn. `step_id` hoặc `section` lọc bảng trích dẫn theo bước/phần đang chọn."""
	_require("read", doc=name, message=_("Bạn không có quyền xem quy trình này"))
	doc = frappe.get_doc(DT, name)
	citations = [_dump(c, CITATION_FIELDS) for c in doc.citations]
	if step_id:
		citations = [c for c in citations if c["target_step_id"] == step_id]
	elif section:
		citations = [c for c in citations if c["target_section"] == section]
	return {
		"name": doc.name,
		"technical_service": doc.technical_service,
		"department": doc.department,
		"version_no": doc.version_no,
		"workflow_state": doc.workflow_state,
		"needs_review": doc.needs_review,
		"copied_from": doc.copied_from,
		"previous_version": doc.previous_version,
		"can_edit": bool(frappe.has_permission(DT, "write", doc=doc)) and doc.workflow_state == DRAFT,
		"sections": [
			{"key": key, "label": label, "value": None if key == "steps" else doc.get(key)}
			for key, label in SECTIONS
		],
		"steps": [_dump(s, STEP_FIELDS) for s in doc.steps],
		"resources": [_dump(r, RESOURCE_FIELDS) for r in doc.resources],
		"citations": citations,
	}


@frappe.whitelist()
def save_sections(procedure, sections):
	"""Lưu các phần văn bản (7 trường); khóa ngoài danh sách bị từ chối."""
	sections = frappe.parse_json(sections) if isinstance(sections, str) else sections
	doc = _editable(procedure)
	unknown = [k for k in sections if k not in TEXT_FIELDS]
	if unknown:
		frappe.throw(_("Phần không hợp lệ: {0}").format(", ".join(unknown)))
	for key, value in sections.items():
		doc.set(key, value)
	_save(doc)
	return {k: doc.get(k) for k in sections}


def _check_step_values(phase, step_title, description):
	missing = [
		label
		for label, value in ((_("Giai đoạn"), phase), (_("Tên bước"), step_title), (_("Mô tả"), description))
		if not (value or "").strip()
	]
	if missing:
		frappe.throw(_("Thiếu: {0}").format(", ".join(missing)))


@frappe.whitelist()
def add_step(procedure, phase, step_title, description):
	"""FR-PROC-003: thêm bước vào quy trình Nháp; mã bước do máy chủ cấp (DI-01)."""
	doc = _editable(procedure)
	_check_step_values(phase, step_title, description)
	row = doc.append(
		"steps", {"phase": phase, "step_title": step_title.strip(), "description": description.strip()}
	)
	_save(doc)
	return _dump(row, STEP_FIELDS[:4])


@frappe.whitelist()
def update_step(procedure, step_id, phase, step_title, description):
	doc = _editable(procedure)
	_check_step_values(phase, step_title, description)
	row = _row(doc, "steps", "step_id", step_id, _("bước"))
	row.phase, row.step_title, row.description = phase, step_title.strip(), description.strip()
	_save(doc)
	return _dump(row, STEP_FIELDS[:4])


@frappe.whitelist()
def delete_step(procedure, step_id):
	"""Xóa bước; mã không tái dùng. Từ chối nếu còn nguồn lực hoặc trích dẫn gắn bước (ASM-018)."""
	doc = _editable(procedure)
	row = _row(doc, "steps", "step_id", step_id, _("bước"))
	n_res = sum(1 for r in doc.resources if r.step_id == step_id)
	n_cit = sum(1 for c in doc.citations if c.target_step_id == step_id)
	if n_res or n_cit:
		frappe.throw(
			_("Bước {0} còn {1} nguồn lực và {2} trích dẫn; xóa chúng trước").format(step_id, n_res, n_cit)
		)
	doc.remove(row)
	_save(doc)
	return {"deleted": step_id}


@frappe.whitelist()
def reorder_steps(procedure, order):
	"""FR-PROC-006: đổi thứ tự hiển thị, giữ nguyên mã bước. `order` là hoán vị đầy đủ các mã bước."""
	order = frappe.parse_json(order) if isinstance(order, str) else order
	doc = _editable(procedure)
	try:
		ordered = reorder([{"step_id": s.step_id, "row": s} for s in doc.steps], order)
	except ValueError:
		frappe.throw(_("Thứ tự phải gồm đúng các mã bước hiện có, mỗi mã một lần"))
	doc.set("steps", [x["row"] for x in ordered])
	for i, row in enumerate(doc.steps, 1):
		row.idx = i
	_save(doc)
	return [s.step_id for s in doc.steps]


def _apply_resource(doc, row, values):
	rtype = values.get("resource_type") or row.resource_type
	if values.get("step_id") is not None:
		row.step_id = values["step_id"]
	if values.get("resource_type"):
		row.resource_type = rtype
	if values.get("resource_text") is not None:
		row.resource_text = values["resource_text"].strip()
	if values.get("quantity") is not None:
		row.quantity = values["quantity"]
	if rtype == LABOR:
		row.uom = values.get("uom") or row.uom or LABOR_UOM
		if values.get("headcount") is not None:
			row.headcount = values["headcount"]
		row.headcount = row.headcount or 1
	else:
		if values.get("uom") is not None:
			row.uom = values["uom"]
		if values.get("headcount") is not None:
			row.headcount = values["headcount"]
	linked_name = values.get("linked_name")
	if linked_name is not None:
		if not linked_name:
			row.linked_doctype = row.linked_name = None
		elif rtype == LABOR:  # G2: chỉ có danh mục chức danh
			row.linked_doctype, row.linked_name = "NC Job Title", linked_name
		else:
			frappe.throw(_("Danh mục cho loại {0} chưa có; để trống liên kết").format(rtype))
	if not (row.resource_text or "").strip() or row.quantity is None or not (row.uom or "").strip():
		frappe.throw(_("Thiếu: tên, số lượng hoặc đơn vị của nguồn lực"))


@frappe.whitelist()
def add_resource(
	procedure,
	step_id,
	resource_type,
	resource_text,
	quantity,
	uom=None,
	linked_doctype=None,
	linked_name=None,
	headcount=None,
):
	"""FR-PROC-004: nguồn lực có cấu trúc gắn mã bước; mã dòng `R###` do máy chủ cấp, bất biến."""
	doc = _editable(procedure)
	row = doc.append("resources", {"resource_type": resource_type})
	_apply_resource(
		doc,
		row,
		{
			"step_id": step_id,
			"resource_text": resource_text,
			"quantity": quantity,
			"uom": uom,
			"headcount": headcount,
			"linked_name": linked_name or "",
		},
	)
	_save(doc)
	return _dump(row, RESOURCE_FIELDS)


@frappe.whitelist()
def update_resource(
	procedure,
	resource_row_id,
	step_id=None,
	resource_text=None,
	quantity=None,
	uom=None,
	linked_name=None,
	headcount=None,
):
	"""Sửa tại chỗ (None = giữ nguyên; linked_name "" = bỏ liên kết); mã dòng không đổi."""
	doc = _editable(procedure)
	row = _row(doc, "resources", "resource_row_id", resource_row_id, _("dòng nguồn lực"))
	_apply_resource(
		doc,
		row,
		{
			"step_id": step_id,
			"resource_text": resource_text,
			"quantity": quantity,
			"uom": uom,
			"headcount": headcount,
			"linked_name": linked_name,
		},
	)
	_save(doc)
	return _dump(row, RESOURCE_FIELDS)


@frappe.whitelist()
def delete_resource(procedure, resource_row_id):
	doc = _editable(procedure)
	doc.remove(_row(doc, "resources", "resource_row_id", resource_row_id, _("dòng nguồn lực")))
	_save(doc)
	return {"deleted": resource_row_id}


@frappe.whitelist()
def suggest_catalog(resource_type, text):
	"""FR-PROC-005: gợi ý bản ghi danh mục theo tên. Chỉ Nhân lực (NC Job Title); loại khác trả rỗng (G2).
	Dùng get_all vì NC Clinician không có quyền đọc NC Job Title nhưng phải chọn được chức danh."""
	frappe.has_permission(DT, "read", throw=True)
	text = (text or "").strip()
	if resource_type != LABOR or not text:
		return []
	rows = frappe.get_all(
		"NC Job Title",
		or_filters=[["name", "like", f"%{text}%"], ["job_title_name", "like", f"%{text}%"]],
		fields=["name", "job_title_name"],
		limit_page_length=10,
	)
	return [{"doctype": "NC Job Title", "name": r.name, "label": r.job_title_name} for r in rows]


def _apply_citation(row, target_section, target_step_id, relation, quote, deviation_reason):
	if relation is not None and relation not in RELATIONS:
		frappe.throw(_("Quan hệ không hợp lệ: {0}").format(relation))
	for key, value in (
		("target_section", target_section),
		("target_step_id", target_step_id),
		("quote", quote),
		("deviation_reason", deviation_reason),
	):
		if value is not None:
			row.set(key, value or None)
	row.relation = relation or row.relation or "Chưa có căn cứ"


@frappe.whitelist()
def add_citation(
	procedure,
	target_section=None,
	target_step_id=None,
	relation=None,
	quote=None,
	deviation_reason=None,
):
	"""FR-PROC-007: trích dẫn cho một phần hoặc một bước; quan hệ mặc định "Chưa có căn cứ" (Q1)."""
	doc = _editable(procedure)
	row = doc.append("citations", {})
	_apply_citation(row, target_section, target_step_id, relation, quote, deviation_reason)
	_save(doc)
	return _dump(doc.citations[-1], CITATION_FIELDS)


@frappe.whitelist()
def update_citation(
	procedure,
	citation,
	target_section=None,
	target_step_id=None,
	relation=None,
	quote=None,
	deviation_reason=None,
):
	"""`citation` là `name` của dòng trích dẫn. Chuỗi rỗng xóa giá trị của trường."""
	doc = _editable(procedure)
	row = _row(doc, "citations", "name", citation, _("trích dẫn"))
	_apply_citation(row, target_section, target_step_id, relation, quote, deviation_reason)
	_save(doc)
	return _dump(row, CITATION_FIELDS)


@frappe.whitelist()
def delete_citation(procedure, citation):
	doc = _editable(procedure)
	doc.remove(_row(doc, "citations", "name", citation, _("trích dẫn")))
	_save(doc)
	return {"deleted": citation}


@frappe.whitelist()
def copy_procedure(source, technical_service, department):
	"""FR-PROC-013: bản nháp mới từ quy trình khác; mã bước và mã dòng cấp mới, ghi `copied_from` (G4).
	Đích qua cùng kiểm tra của create_procedure (FR-PROC-002, Q3)."""
	_require("create", message=_("Bạn không có quyền tạo quy trình"))
	_require("read", doc=source, message=_("Bạn không có quyền xem quy trình nguồn"))
	version, latest = _refuse_if_exists(technical_service, department)
	src = frappe.get_doc(DT, source)
	copied = copy_structure(
		[_dump(s, STEP_FIELDS) for s in src.steps],
		[_dump(r, RESOURCE_FIELDS) for r in src.resources],
		[_dump(c, CITATION_FIELDS[1:]) for c in src.citations],
	)
	doc = frappe.get_doc(
		{
			"doctype": DT,
			"technical_service": technical_service,
			"department": department,
			"version_no": version + 1,
			"previous_version": latest,
			"copied_from": src.name,
			**{k: src.get(k) for k in TEXT_FIELDS},
			"steps": copied["steps"],
			"resources": [{**r, "ai_suggested": 0} for r in copied["resources"]],
			"citations": copied["citations"],
			"next_step_seq": copied["next_step_seq"],
			"next_resource_seq": copied["next_resource_seq"],
		}
	)
	doc.insert()
	return {"name": doc.name, "version_no": doc.version_no}
