"""Sổ sự kiện nghiệp vụ (ADR-014, FR-AUD-001..004).

Lớp thứ nhất là `track_changes` (Version, theo trường). Lớp thứ hai là NC Audit Event: chỉ ghi qua hàm
ở đây, không ai sửa hay xóa được, kể cả Administrator (ASM-066).
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

EVENT = "NC Audit Event"
SKIP = {"NC Audit Event", "NC AI Log"}
STATE_FIELDS = {
	"NC Norm Set": "status",
	"NC Costing Run": "status",
	"NC Accounting Import": "status",
}  # mặc định: workflow_state
# DocType không lưu giá trị trước khi xóa (ASM-069): nhóm "Cấu hình AI, mẫu lệnh"
NO_BEFORE_VALUE = set()
LOCKED_STATES = {"Đã khóa", "Đã chốt"}


def _deny(message):
	frappe.throw(message, frappe.PermissionError)


def guard_immutable(doc, force=False):
	"""Từ chối sửa bản ghi đã có và mọi thao tác xóa (FR-AUD-002)."""
	if force or not doc.is_new():
		_deny(_("Nhật ký không được sửa hoặc xóa"))


def guard_insert(doc):
	"""NC Audit Event chỉ tạo qua `log_event` (FR-AUD-002)."""
	if not doc.flags.from_audit:
		_deny(_("Sổ sự kiện chỉ ghi qua mã máy chủ"))


def log_event(
	event_type,
	ref_doctype=None,
	ref_name=None,
	from_state=None,
	to_state=None,
	detail=None,
	user=None,
	before_value=None,
	ignore_links=False,
):
	doc = frappe.get_doc(
		{
			"doctype": EVENT,
			"event_time": now_datetime(),
			"user": user or frappe.session.user,
			"event_type": event_type,
			"ref_doctype": ref_doctype,
			"ref_name": ref_name,
			"from_state": from_state or "",
			"to_state": to_state or "",
			"detail": detail,
			"before_value": before_value,
		}
	)
	doc.flags.from_audit = True
	doc.flags.ignore_links = ignore_links  # bản ghi nguồn đã bị xóa
	doc.insert(ignore_permissions=True)
	return doc


def log_export(file_type, ref_doctype, ref_name, file_name=None):
	"""FR-AUD-004: điểm ghi việc xuất tệp; luồng xuất là FEAT-019."""
	detail = f"{file_type}: {file_name}" if file_name else file_type
	return log_event("Xuất tệp", ref_doctype, ref_name, detail=detail)


def _state_field(doc):
	if doc.doctype in SKIP or not doc.doctype.startswith("NC "):
		return None
	field = STATE_FIELDS.get(doc.doctype, "workflow_state")
	return field if doc.meta.has_field(field) else None


def _log_state(doc, before, after):
	etype = "Khóa" if after in LOCKED_STATES else "Chuyển trạng thái"
	log_event(etype, doc.doctype, doc.name, before, after, detail=doc.flags.get("audit_detail"))


def on_doc_validate(doc, method=None):
	"""Mỗi lần lưu bắt đầu lại từ trạng thái trong CSDL (xóa mốc của lần trước)."""
	doc.flags.pop("audit_state", None)


def on_doc_change(doc, method=None):
	"""Hook `on_change` chạy cả khi `save()` lẫn `db_set()` (NC Costing Run đổi trạng thái bằng `db_set`).

	Mốc so sánh là `flags.audit_state` (trạng thái đã xét ở lần gọi trước trên cùng đối tượng), nên hai lần
	`db_set` liên tiếp không ghi trùng và không bỏ sót.
	"""
	if doc.flags.get("in_delete"):  # Frappe gọi on_change trước khi kiểm liên kết; chưa chắc bị xóa
		return
	field = _state_field(doc)
	if not field:
		return
	current = doc.get(field) or ""
	if "audit_state" in doc.flags:
		before = doc.flags.audit_state
	else:
		prev = doc.get_doc_before_save()
		before = (prev.get(field) or "") if prev else ("" if doc.flags.in_insert else current)
	doc.flags.audit_state = current
	if before != current:
		_log_state(doc, before, current)


def snapshot(doc):
	"""Giá trị bản ghi, bảng con, owner, creation và các Version để lưu khi xóa (AMD-006); bỏ trường Password."""

	def clean(row, meta):
		skip = {df.fieldname for df in meta.fields if df.fieldtype == "Password"}
		return {k: v for k, v in row.items() if k not in skip}

	data = clean(doc.as_dict(no_nulls=True), doc.meta)
	for df in doc.meta.get_table_fields():
		child_meta = frappe.get_meta(df.options)
		data[df.fieldname] = [clean(r, child_meta) for r in data.get(df.fieldname) or []]
	versions = frappe.get_all(
		"Version",
		{"ref_doctype": doc.doctype, "docname": doc.name},
		["owner", "creation", "data"],
		order_by="creation asc",
	)
	out = {"doc": data, "owner": doc.owner, "creation": doc.creation, "versions": versions}
	return json.dumps(out, default=str, ensure_ascii=False)


def on_doc_delete(doc, method=None):
	"""FR-AUD-001: xóa bản ghi để lại một sự kiện "Xóa" kèm giá trị trước (AMD-006).

	Chạy ở `after_delete`: sau kiểm liên kết (xóa bị chặn thì không có sự kiện), trước khi Frappe xóa Version.
	"""
	if doc.doctype in SKIP or not doc.doctype.startswith("NC ") or doc.meta.istable:
		return
	before = None if doc.doctype in NO_BEFORE_VALUE else snapshot(doc)
	log_event("Xóa", doc.doctype, doc.name, before_value=before, ignore_links=True)
