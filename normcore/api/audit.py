"""Tra cứu sổ sự kiện (FR-AUD-003, UC-018)."""

import frappe
from frappe import _
from frappe.utils import add_days, getdate

FIELDS = [
	"name",
	"event_time",
	"user",
	"event_type",
	"ref_doctype",
	"ref_name",
	"from_state",
	"to_state",
	"detail",
]
MAX_LIMIT = 1000


@frappe.whitelist()
def get_events(ref_doctype=None, ref_name=None, user=None, from_time=None, to_time=None, limit=200):
	if not frappe.has_permission("NC Audit Event", "read"):
		frappe.throw(_("Không có quyền xem nhật ký"), frappe.PermissionError)
	filters = []
	for key, value in (("ref_doctype", ref_doctype), ("ref_name", ref_name), ("user", user)):
		if value:
			filters.append([key, "=", value])
	if from_time:
		filters.append(["event_time", ">=", from_time])
	if to_time:
		if len(str(to_time).strip()) <= 10:  # chỉ có ngày: lấy trọn ngày đó
			filters.append(["event_time", "<", add_days(getdate(to_time), 1)])
		else:
			filters.append(["event_time", "<=", to_time])
	limit = max(1, min(int(limit or 200), MAX_LIMIT))
	return frappe.get_list(
		"NC Audit Event",
		filters=filters,
		fields=FIELDS,
		order_by="event_time asc, creation asc",
		limit_page_length=limit,
	)
