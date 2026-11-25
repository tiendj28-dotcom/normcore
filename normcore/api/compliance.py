"""Hồ sơ tuân thủ thiết bị: cấu hình, tác vụ hằng ngày, thông báo (FR-CMP-005, FR-ADM-006).

Thông báo dùng Notification Log của Frappe (ASM-100) vì `core/notify.py` (FEAT-002) chưa có.
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from normcore.costing import compliance

DOCTYPE = "NC Equipment Compliance"
ROLE_RESOURCE_MANAGER = "NC Resource Manager"


def get_reminder_days() -> int:
	"""FR-ADM-006: số ngày nhắc hạn; trống → 30. Máy chủ đọc, không qua quyền người dùng."""
	# Đọc thẳng bảng Singles: chưa từng lưu NC Settings thì không có dòng → mặc định 30
	rows = frappe.db.sql(
		"select value from `tabSingles` where doctype=%s and field=%s",
		("NC Settings", "compliance_reminder_days"),
	)
	return compliance.reminder_days(rows[0][0] if rows else None)


def _today(today):
	return getdate(today or nowdate())


def refresh_all_statuses(today=None) -> int:
	"""Tính lại trạng thái mọi hồ sơ; trả số hồ sơ đổi trạng thái. Chạy quyền hệ thống."""
	today, reminder, changed = _today(today), get_reminder_days(), 0
	for r in frappe.get_all(DOCTYPE, fields=["name", "expiry_date", "status"]):
		new = compliance.compute_status(r.expiry_date, today, reminder)
		if new != r.status:
			frappe.db.set_value(DOCTYPE, r.name, "status", new, update_modified=False)
			changed += 1
	return changed


def _resource_managers() -> list[str]:
	users = frappe.get_all(
		"Has Role",
		filters={"role": ROLE_RESOURCE_MANAGER, "parenttype": "User"},
		pluck="parent",
	)
	if not users:
		return []
	return frappe.get_all(
		"User",
		filters={"name": ["in", users], "enabled": 1, "user_type": "System User"},
		pluck="name",
	)


def _enabled(user) -> str | None:
	return user if user and frappe.db.get_value("User", user, "enabled") else None


def send_reminders(today=None) -> int:
	"""Gửi Notification Log cho NC Resource Manager và trưởng khoa; bỏ qua nếu đã gửi cùng tiêu đề."""
	today = _today(today)
	records = frappe.get_all(
		DOCTYPE,
		fields=["name", "record_code", "equipment", "department", "expiry_date"],
	)
	managers = [u for u in _resource_managers() if u not in ("Administrator", "Guest")]
	created = 0
	for r in compliance.due_for_reminder(records, today, get_reminder_days()):
		head = (
			_enabled(frappe.db.get_value("NC Department", r.department, "head_user"))
			if r.department
			else None
		)
		subject = compliance.reminder_subject(r)
		for user in compliance.recipients(managers, head):
			if frappe.db.exists(
				"Notification Log", {"for_user": user, "document_name": r.name, "subject": subject}
			):
				continue
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"type": "Alert",
					"document_type": DOCTYPE,
					"document_name": r.name,
					"subject": subject,
					"for_user": user,
					"from_user": "Administrator",
				}
			).insert(ignore_permissions=True)
			created += 1
	return created


def daily_job():
	"""Scheduler hằng ngày (FR-CMP-005): tính lại trạng thái rồi gửi nhắc."""
	refresh_all_statuses()
	send_reminders()


@frappe.whitelist()
def run_compliance_check():
	"""Nút "Kiểm hạn ngay": cần quyền ghi hồ sơ tuân thủ (NC Auditor, NC Finance bị từ chối)."""
	if not frappe.has_permission(DOCTYPE, "write"):
		frappe.throw(_("Bạn không có quyền kiểm hạn hồ sơ tuân thủ"), frappe.PermissionError)
	return {"updated": refresh_all_statuses(), "notified": send_reminders()}
