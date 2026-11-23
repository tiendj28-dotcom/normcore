"""Hồ sơ tuân thủ thiết bị: cấu hình, tác vụ hằng ngày, thông báo (FR-CMP-005, FR-ADM-006)."""

import frappe

from normcore.costing import compliance


def get_reminder_days() -> int:
	"""FR-ADM-006: số ngày nhắc hạn; trống → 30. Máy chủ đọc, không qua quyền người dùng."""
	return compliance.reminder_days(frappe.db.get_single_value("NC Settings", "compliance_reminder_days"))
