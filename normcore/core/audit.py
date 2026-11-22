"""Sổ sự kiện nghiệp vụ (ADR-014, FR-AUD-001..004).

Lớp thứ nhất là `track_changes` (Version, theo trường). Lớp thứ hai là NC Audit Event: chỉ ghi qua hàm
ở đây, không ai sửa hay xóa được, kể cả Administrator (ASM-064).
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

EVENT = "NC Audit Event"
SKIP = {"NC Audit Event", "NC AI Log"}
STATE_FIELDS = {"NC Norm Set": "status"}  # mặc định: workflow_state
LOCKED_STATES = {"Đã khóa"}


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
	event_type, ref_doctype=None, ref_name=None, from_state=None, to_state=None, detail=None, user=None
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
		}
	)
	doc.flags.from_audit = True
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
	log_event(etype, doc.doctype, doc.name, before, after)


def on_doc_insert(doc, method=None):
	field = _state_field(doc)
	if field and doc.get(field):
		_log_state(doc, "", doc.get(field))


def on_doc_update(doc, method=None):
	field = _state_field(doc)
	if not field:
		return
	prev = doc.get_doc_before_save()
	if prev is None:
		return
	before, after = prev.get(field) or "", doc.get(field) or ""
	if before != after:
		_log_state(doc, before, after)
