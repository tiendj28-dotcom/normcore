"""API và tác vụ nền của thư viện văn bản (FEAT-020).

Kiểm quyền tường minh trong từng hàm whitelisted. Thông báo dùng Notification Log (ASM-020-11).
"""

import frappe
from frappe.utils import getdate, today

from normcore.library import validity


def enqueue_index(name, user=None):
	"""Xếp tác vụ lập chỉ mục sau khi giao dịch lưu thành công (FR-LIB-003)."""
	frappe.enqueue(
		"normcore.api.library.index_document",
		queue="long",
		timeout=1800,
		enqueue_after_commit=True,
		name=name,
		notify_user=user,
	)


def refresh_section_validity(legal_document, on=None):
	"""Tính lại hiệu lực các mục của một văn bản (FR-LIB-006)."""
	on = getdate(on or today())
	doc_status = frappe.db.get_value("NC Legal Document", legal_document, "validity_status")
	rows = frappe.get_all(
		"NC Legal Section",
		filters={"legal_document": legal_document},
		fields=["name", "expiry_date", "validity_status"],
	)
	todo = validity.changed(
		[(r.name, doc_status, r.expiry_date, r.validity_status) for r in rows], on, section=True
	)
	for name, status in todo:
		frappe.db.set_value("NC Legal Section", name, "validity_status", status, update_modified=False)
	return len(todo)
