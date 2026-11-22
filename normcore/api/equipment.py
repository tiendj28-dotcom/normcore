"""Giá trị tạm tính của thiết bị, phòng cho form (FR-RES-006, 007, 008). Không ghi dữ liệu."""

import frappe
from frappe import _
from frappe.utils import getdate

from normcore.costing import resources


def expired_mode_on(on) -> str:
	"""Lựa chọn khấu hao hết thời gian sử dụng của bộ tham số mới nhất có hiệu lực tại `on` (mặc định ZERO, ASM-063)."""
	value = frappe.db.get_value(
		"NC Costing Parameter Set",
		{"effective_from": ("<=", on)},
		"expired_depreciation_mode",
		order_by="effective_from desc, creation desc",
	)
	return value or resources.ZERO


@frappe.whitelist()
def get_indicative_rate(equipment: str, on: str | None = None) -> dict:
	doc = frappe.get_doc("NC Equipment", equipment)
	if not frappe.has_permission("NC Equipment", "read", doc=doc):
		frappe.throw(_("Bạn không có quyền xem thiết bị này"), frappe.PermissionError)
	day = getdate(on) if on else getdate()
	mode = expired_mode_on(day)
	result = doc.indicative(day, mode)
	result["expired_mode"] = mode
	result["on"] = str(day)
	return result


@frappe.whitelist()
def get_room_rate(room: str) -> dict:
	doc = frappe.get_doc("NC Room", room)
	if not frappe.has_permission("NC Room", "read", doc=doc):
		frappe.throw(_("Bạn không có quyền xem phòng này"), frappe.PermissionError)
	rate = resources.room_hourly_rate(doc.annual_infrastructure_cost, doc.available_hours_per_year)
	return {"hourly_rate": float(rate)}
