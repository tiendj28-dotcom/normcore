"""API trình soạn quy trình (CLAUDE.md mục 4; NFR-SEC-003): kiểm quyền tường minh trong từng hàm.

Mọi ghi đi qua `doc.save()` để `track_changes` ghi lịch sử (FR-PROC-009, ADR-014); hàm `update_*` sửa dòng
tại chỗ để lịch sử có giá trị trước và sau.
"""

import frappe
from frappe import _

from normcore.ai import gateway, guard
from normcore.ai.providers.base import ProviderError
from normcore.procedure import ai_draft, diff, versioning
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
CITATION_FIELDS = (
	"name",
	"target_section",
	"target_step_id",
	"relation",
	"legal_document",
	"legal_section",
	"quote",
	"deviation_reason",
)
RELATIONS = ("Theo hướng dẫn", "Khác biệt", "Chưa có căn cứ")


class ExistingProcedureError(frappe.ValidationError):
	"""Đã có quy trình cho (dịch vụ, khoa); `existing` là tên bản đó (FR-PROC-002, Q3)."""

	existing = None


class NoSourceError(frappe.ValidationError):
	"""Dịch vụ không có mục hướng dẫn đã xác nhận, còn hiệu lực; cần xác nhận soạn tiếp (FR-AI-004)."""


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
		message = (
			_("Dịch vụ đã có quy trình ban hành; tạo phiên bản mới thuộc chức năng sửa đổi")
			+ f" ({published})"
		)
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
def create_procedure(technical_service, department, doctor_request=None):
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
			"doctor_request": (doctor_request or "").strip() or None,  # giữ yêu cầu khi AI lỗi (UC-004 4a)
		}
	)
	doc.insert()
	return {"name": doc.name, "version_no": doc.version_no}


@frappe.whitelist()
def create_revision(procedure):
	"""FR-WF-009: bản nháp phiên bản kế tiếp từ quy trình "Đã ban hành" mới nhất; giữ mã bước, mã dòng nguồn lực.
	Đã có bản đang soạn/duyệt của (dịch vụ, khoa) thì trả bản đó (UC-007 1d)."""
	_require("create", message=_("Bạn không có quyền sửa đổi quy trình này"))
	_require("write", doc=procedure, message=_("Bạn không có quyền sửa đổi quy trình này"))
	src = frappe.get_doc(DT, procedure)
	draft, published, max_version, _latest = _find_existing(src.technical_service, src.department)
	if draft:
		return {"name": draft, "version_no": frappe.db.get_value(DT, draft, "version_no"), "existing": 1}
	if not versioning.can_revise(src.workflow_state):
		frappe.throw(_("Chỉ sửa đổi được quy trình đã ban hành"))
	if published != src.name:
		frappe.throw(_("Đã có phiên bản ban hành mới hơn: {0}. Sửa đổi từ phiên bản đó.").format(published))
	data = versioning.build_revision(src.as_dict(), max_version)
	doc = frappe.get_doc(data)
	doc.insert()
	doc.add_comment("Info", _("Tạo phiên bản sửa đổi từ {0}").format(src.name))
	return {"name": doc.name, "version_no": doc.version_no, "existing": 0}


@frappe.whitelist()
def list_versions(procedure):
	"""Các phiên bản cùng (dịch vụ, khoa) mà người gọi đọc được, mới nhất trước (bộ chọn SCR-DSK-011)."""
	_require("read", doc=procedure, message=_("Bạn không có quyền xem quy trình này"))
	key = frappe.db.get_value(DT, procedure, ["technical_service", "department"], as_dict=True)
	return frappe.get_list(
		DT,
		filters={"technical_service": key.technical_service, "department": key.department},
		fields=["name", "version_no", "workflow_state", "effective_date", "decision_no"],
		order_by="version_no desc",
		limit_page_length=0,
	)


def _header(doc):
	return {k: doc.get(k) for k in ("name", "version_no", "workflow_state", "effective_date")}


def _diff_input(doc):
	data = {f: doc.get(f) for f in TEXT_FIELDS}
	data["steps"] = [_dump(s, STEP_FIELDS) for s in doc.steps]
	data["resources"] = [_dump(r, RESOURCE_FIELDS) for r in doc.resources]
	return data


@frappe.whitelist()
def compare_versions(base, target):
	"""FR-WF-010: khác biệt theo phần, bước, dòng nguồn lực giữa hai phiên bản cùng (dịch vụ, khoa)."""
	for name in (base, target):
		_require("read", doc=name, message=_("Bạn không có quyền xem quy trình này"))
	a, b = frappe.get_doc(DT, base), frappe.get_doc(DT, target)
	if a.name == b.name or (a.technical_service, a.department) != (b.technical_service, b.department):
		frappe.throw(_("Chỉ so sánh hai phiên bản của cùng một quy trình (dịch vụ, khoa)"))
	result = diff.diff_procedures(_diff_input(a), _diff_input(b), SECTIONS)
	return {"base": _header(a), "target": _header(b), **result}


def _relations(citations):
	"""Quan hệ khác nhau của mỗi đích ("step:<mã>" / "section:<nhãn>") trên toàn bảng trích dẫn (FR-AI-003)."""
	out = {}
	for c in citations:
		key = f"step:{c['target_step_id']}" if c["target_step_id"] else f"section:{c['target_section']}"
		if c["relation"] not in out.setdefault(key, []):
			out[key].append(c["relation"])
	return out


def _section_labels(names):
	"""Nhãn "<số hiệu> — <số mục> <tiêu đề>" cho trích dẫn có `legal_section` là NC Legal Section thật."""
	if not names:
		return {}
	rows = frappe.db.sql(
		"SELECT s.name, d.doc_number, s.section_no, s.heading FROM `tabNC Legal Section` s"
		" JOIN `tabNC Legal Document` d ON d.name = s.legal_document WHERE s.name IN %s",
		(tuple(names),),
		as_dict=True,
	)
	return {r.name: f"{r.doc_number} — {r.section_no} {r.heading or ''}".strip() for r in rows}


@frappe.whitelist()
def get_procedure(name, step_id=None, section=None):
	"""Dữ liệu cho trình soạn. `step_id` hoặc `section` lọc bảng trích dẫn theo bước/phần đang chọn."""
	_require("read", doc=name, message=_("Bạn không có quyền xem quy trình này"))
	doc = frappe.get_doc(DT, name)
	citations = [_dump(c, CITATION_FIELDS) for c in doc.citations]
	relations = _relations(citations)
	labels = _section_labels({c["legal_section"] for c in citations if c["legal_section"]})
	for c in citations:
		c["section_label"] = labels.get(c["legal_section"])
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
		"doctor_request": doc.doctor_request,
		"ai_log": doc.ai_log,
		"relations": relations,
		"can_edit": bool(frappe.has_permission(DT, "write", doc=doc)) and doc.workflow_state == DRAFT,
		"sections": [
			{"key": key, "label": label, "value": None if key == "steps" else doc.get(key)}
			for key, label in SECTIONS
		],
		"steps": [dict(_dump(s, STEP_FIELDS), ai_suggested=s.ai_suggested) for s in doc.steps],
		"resources": [dict(_dump(r, RESOURCE_FIELDS), ai_suggested=r.ai_suggested) for r in doc.resources],
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


def _apply_citation(
	row,
	target_section,
	target_step_id,
	relation,
	quote,
	deviation_reason,
	legal_document=None,
	legal_section=None,
):
	if relation is not None and relation not in RELATIONS:
		frappe.throw(_("Quan hệ không hợp lệ: {0}").format(relation))
	for key, value in (
		("target_section", target_section),
		("target_step_id", target_step_id),
		("legal_document", legal_document),
		("legal_section", legal_section),
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
	legal_document=None,
	legal_section=None,
):
	"""FR-PROC-007: trích dẫn cho một phần hoặc một bước; quan hệ mặc định "Chưa có căn cứ" (Q1)."""
	doc = _editable(procedure)
	row = doc.append("citations", {})
	_apply_citation(
		row, target_section, target_step_id, relation, quote, deviation_reason, legal_document, legal_section
	)
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
	legal_document=None,
	legal_section=None,
):
	"""`citation` là `name` của dòng trích dẫn. Chuỗi rỗng xóa giá trị của trường."""
	doc = _editable(procedure)
	row = _row(doc, "citations", "name", citation, _("trích dẫn"))
	_apply_citation(
		row, target_section, target_step_id, relation, quote, deviation_reason, legal_document, legal_section
	)
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


# ---- FEAT-024: soạn dự thảo bằng AI (FR-AI-001..005, FR-AI-008; UC-004) ----

AI_JOB_KEY = "normcore:ai_draft:{}"
AI_JOB_TTL = 3600
MAX_REQUEST_CHARS = 5000
MAX_EXTRA_SECTIONS = 20
VALID = "Còn hiệu lực"


def _ai_access(technical_service, department=None):
	_require("create", message=_("Bạn không có quyền tạo quy trình"))
	if not frappe.has_permission("NC Technical Service", "read", doc=technical_service):
		_deny(_("Bạn không có quyền xem dịch vụ này"))
	if (
		department
	):  # phạm vi khoa (FEAT-001): hook has_permission so khoa của bản ghi tạm với khoa của người gọi
		probe = frappe.get_doc(
			{"doctype": DT, "technical_service": technical_service, "department": department}
		)
		if not frappe.has_permission(DT, "create", doc=probe):
			_deny(_("Bạn không có quyền với khoa này"))


def _doc_numbers(names):
	if not names:
		return {}
	rows = frappe.db.sql(
		"SELECT s.name, d.doc_number FROM `tabNC Legal Section` s"
		" JOIN `tabNC Legal Document` d ON d.name = s.legal_document WHERE s.name IN %s",
		(tuple(names),),
	)
	return dict(rows)


def _extra_sources(names, strict):
	"""Mục do người soạn chọn thêm: chỉ mục "Còn hiệu lực" (ASM-024-03); qua guard.build_source."""
	out = []
	for name in names:
		rec = frappe.db.get_value(
			"NC Legal Section",
			name,
			["name", "section_no", "heading", "plain_text", "validity_status"],
			as_dict=True,
		)
		if not rec or rec.validity_status != VALID:
			if strict:
				frappe.throw(_("Mục {0} không tồn tại hoặc không còn hiệu lực").format(name))
			continue
		out.append(guard.build_source("NC Legal Section", rec))
	return out


def _collect_sources(technical_service, extra_names, strict=True):
	from normcore.api.library import get_draft_sources

	sources = get_draft_sources(technical_service, valid_only=True)
	have = {s["name"] for s in sources}
	extra = [n for n in dict.fromkeys(extra_names or []) if n not in have]
	return sources + _extra_sources(extra, strict)


def _current_procedure(technical_service, department):
	"""ASM-024-04: bản "Đã ban hành" mới nhất của dịch vụ (ưu tiên cùng khoa) mà người gọi đọc được."""
	rows = frappe.get_all(
		DT,
		filters={"technical_service": technical_service, "workflow_state": PUBLISHED},
		fields=["name", "department", "version_no"],
		order_by="version_no desc",
	)
	rows.sort(key=lambda r: r.department != department)
	for r in rows:
		if frappe.has_permission(DT, "read", doc=r.name):
			return r
	return None


@frappe.whitelist()
def prepare_ai_draft(technical_service, department):
	"""SCR-DSK-008 bước 1: nguồn sẽ gửi, bản đã có, trạng thái AI (FR-AI-001, FR-AI-004)."""
	_ai_access(technical_service, department)
	from normcore.api.library import get_draft_sources

	sources = get_draft_sources(technical_service, valid_only=True)
	docs = _doc_numbers([s["name"] for s in sources])
	draft, published, _v, _n = _find_existing(technical_service, department)
	existing = draft or published
	cur = _current_procedure(technical_service, department)
	return {
		"ai_enabled": gateway.is_enabled(),
		"existing": existing,
		"existing_state": frappe.db.get_value(DT, existing, "workflow_state") if existing else None,
		"sources": [
			{
				"name": s["name"],
				"legal_document": docs.get(s["name"]),
				"doc_number": docs.get(s["name"]),
				"section_no": s["section_no"],
				"heading": s["heading"],
			}
			for s in sources
		],
		"no_sources": not sources,
		"current_procedure": {"name": cur.name, "version_no": cur.version_no} if cur else None,
	}


@frappe.whitelist()
def search_extra_sources(query, technical_service, start=0, page_length=20):
	"""Mục còn hiệu lực để chọn thêm, bỏ mục đã có trong nguồn ánh xạ (FR-AI-001, ASM-024-03)."""
	_ai_access(technical_service)
	from normcore.api.library import get_draft_sources, search_sections

	have = {s["name"] for s in get_draft_sources(technical_service, valid_only=True)}
	rows = search_sections(query, validity_status=VALID, start=start, page_length=page_length)
	rows = rows.get("rows", rows) if isinstance(rows, dict) else rows
	out = []
	for r in rows:
		if r.get("name") in have:
			continue
		out.append({k: r.get(k) for k in ("name", "doc_number", "section_no", "heading")})
	return out


def _job_set(job_id, **state):
	frappe.cache().set_value(AI_JOB_KEY.format(job_id), state, expires_in_sec=AI_JOB_TTL)
	frappe.publish_realtime(
		"normcore_ai_draft", {"job_id": job_id, "status": state.get("status")}, user=state.get("user")
	)


@frappe.whitelist()
def start_ai_draft(technical_service, department, doctor_request, extra_sections=None, confirm_no_source=0):
	"""UC-004 bước 4: kiểm điều kiện rồi xếp việc soạn vào hàng đợi `long`. Trả `{job_id}`."""
	_ai_access(technical_service, department)
	gateway.ensure_enabled()
	doctor_request = (doctor_request or "").strip()
	if not doctor_request:
		frappe.throw(_("Nhập yêu cầu soạn thảo"))
	if len(doctor_request) > MAX_REQUEST_CHARS:
		frappe.throw(_("Yêu cầu soạn thảo tối đa {0} ký tự").format(MAX_REQUEST_CHARS))
	_refuse_if_exists(technical_service, department)
	extra = frappe.parse_json(extra_sections) if isinstance(extra_sections, str) else (extra_sections or [])
	if len(extra) > MAX_EXTRA_SECTIONS:
		frappe.throw(_("Chọn thêm tối đa {0} mục").format(MAX_EXTRA_SECTIONS))
	sources = _collect_sources(technical_service, extra, strict=True)
	if not sources and not frappe.utils.cint(confirm_no_source):
		raise NoSourceError(
			_(
				"Dịch vụ chưa có mục hướng dẫn nào đã xác nhận và còn hiệu lực. Xác nhận để soạn tiếp không có căn cứ."
			)
		)
	from normcore.ai.prompts_install import ensure_draft_procedure_v2

	ensure_draft_procedure_v2()
	job_id = frappe.generate_hash(length=16)
	_job_set(job_id, status="queued", user=frappe.session.user)
	frappe.enqueue(
		"normcore.api.procedure.run_ai_draft",
		queue="long",
		timeout=gateway.get_settings().timeout_seconds + 60,
		draft_job=job_id,  # `job_id` là tham số của frappe.enqueue, không tới hàm
		now=bool(frappe.flags.in_test),
		enqueue_after_commit=True,
		technical_service=technical_service,
		department=department,
		doctor_request=doctor_request,
		extra_sections=extra,
		user=frappe.session.user,
	)
	return {"job_id": job_id}


@frappe.whitelist()
def get_ai_draft_status(job_id):
	state = frappe.cache().get_value(AI_JOB_KEY.format(job_id))
	if not state:
		return {"status": "unknown"}
	if state.get("user") != frappe.session.user and frappe.session.user != "Administrator":
		_deny(_("Bạn không có quyền xem tiến độ này"))
	return state


def _write_ai_draft(technical_service, department, doctor_request, built, log_name):
	version, latest = _refuse_if_exists(technical_service, department)
	doc = frappe.get_doc(
		{
			"doctype": DT,
			"technical_service": technical_service,
			"department": department,
			"version_no": version + 1,
			"previous_version": latest,
			"doctor_request": doctor_request,
			"ai_log": log_name,
			**built.sections,
			"steps": built.steps,
		}
	)
	doc.insert()  # controller cấp step_id (DI-01)
	step_ids = [s.step_id for s in doc.steps]
	for sid, rows in zip(step_ids, built.resources, strict=True):
		for r in rows:
			doc.append("resources", dict(r, step_id=sid))
	for target, rows in built.citations.items():
		for c in rows:
			if target[0] == "section":
				where = {"target_section": ai_draft.SECTION_KEYS[target[1]]}
			else:
				where = {"target_step_id": step_ids[target[1]]}
			doc.append("citations", dict(c, **where))
	_save(doc)
	return doc


def run_ai_draft(draft_job, technical_service, department, doctor_request, extra_sections, user):
	"""Tác vụ nền: gọi gateway, kiểm trích dẫn, ghi bản nháp. Không ném lỗi ra ngoài; mọi kết quả vào cache."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		_job_set(draft_job, status="running", user=user)
		sources = _collect_sources(technical_service, extra_sections, strict=False)
		numbers = _doc_numbers([s["name"] for s in sources])
		check_sources = [dict(s, doc_number=numbers.get(s["name"])) for s in sources]
		service = frappe.db.get_value(
			"NC Technical Service", technical_service, ["service_code", "service_name"], as_dict=True
		)
		cur = _current_procedure(technical_service, department)
		current = guard.build_source(DT, frappe.get_doc(DT, cur.name).as_dict()) if cur else None
		holder = {}

		def post(data):
			try:
				holder["built"] = ai_draft.build_rows(
					ai_draft.parse_draft(data), check_sources, doctor_request
				)
			except ai_draft.DraftError as e:
				raise ProviderError(str(e)) from e
			return data, holder["built"].rejected

		res = gateway.complete(
			"DRAFT_PROCEDURE",
			"DRAFT_PROCEDURE",
			ai_draft.request_variables(doctor_request, service, current),
			sources,
			ref_doctype="NC Technical Service",
			ref_name=technical_service,
			postprocess=post,
		)
		if not res.ok:
			return _job_set(
				draft_job, status="failed", user=user, error=res.error, log=res.log_name, ai_status=res.status
			)
		built = holder["built"]
		frappe.db.savepoint("ai_draft")
		try:
			doc = _write_ai_draft(technical_service, department, doctor_request, built, res.log_name)
		except Exception as e:
			frappe.db.rollback(save_point="ai_draft")
			state = {"status": "failed", "user": user, "error": str(e), "log": res.log_name}
			state["existing_procedure"] = getattr(e, "existing", None)
			return _job_set(draft_job, **state)
		_job_set(
			draft_job,
			status="done",
			user=user,
			procedure=doc.name,
			log=res.log_name,
			rejected=built.rejected,
			warnings=built.warnings,
		)
	except Exception as e:  # không để tác vụ nền ném lỗi; người gọi đọc trạng thái từ cache
		_job_set(draft_job, status="failed", user=user, error=f"{type(e).__name__}: {e}")
	finally:
		frappe.set_user(previous)


def _id_list(value):
	value = frappe.parse_json(value) if isinstance(value, str) else value
	return list(value or [])


@frappe.whitelist()
def accept_suggestions(procedure, step_ids=None, resource_row_ids=None, all=0):
	"""FR-AI-008: chấp nhận đề xuất AI (bỏ cờ `ai_suggested`). Chấp nhận bước không kéo theo nguồn lực (ASM-024-13)."""
	doc = _editable(procedure)
	step_ids, row_ids = _id_list(step_ids), _id_list(resource_row_ids)
	everything = frappe.utils.cint(all)
	steps = {s.step_id: s for s in doc.steps}
	rows = {r.resource_row_id: r for r in doc.resources}
	missing = [i for i in step_ids if i not in steps] + [i for i in row_ids if i not in rows]
	if missing:
		frappe.throw(_("Không thấy: {0}").format(", ".join(missing)))
	accepted_steps, accepted_rows = [], []
	for sid, s in steps.items():
		if s.ai_suggested and (everything or sid in step_ids):
			s.ai_suggested = 0
			accepted_steps.append(sid)
	for rid, r in rows.items():
		if r.ai_suggested and (everything or rid in row_ids):
			r.ai_suggested = 0
			accepted_rows.append(rid)
	_save(doc)
	remaining = sum(1 for s in doc.steps if s.ai_suggested) + sum(1 for r in doc.resources if r.ai_suggested)
	return {"accepted_steps": accepted_steps, "accepted_resources": accepted_rows, "remaining": remaining}


@frappe.whitelist()
def reject_suggestion(procedure, step_id):
	"""FR-AI-008: bỏ một bước đề xuất cùng nguồn lực và trích dẫn của nó; mã bước không tái dùng (DI-01)."""
	doc = _editable(procedure)
	row = _row(doc, "steps", "step_id", step_id, _("bước"))
	if not row.ai_suggested:
		frappe.throw(_("Bước {0} không còn là đề xuất; dùng Xóa bước").format(step_id))
	res = [r for r in doc.resources if r.step_id == step_id]
	cits = [c for c in doc.citations if c.target_step_id == step_id]
	for r in res:
		doc.remove(r)
	for c in cits:
		doc.remove(c)
	doc.remove(row)
	_save(doc)
	return {"deleted": step_id, "resources": len(res), "citations": len(cits)}
