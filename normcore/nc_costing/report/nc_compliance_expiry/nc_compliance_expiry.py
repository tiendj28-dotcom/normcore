"""Script Report SCR-DSK-036: hồ sơ hết hạn, sắp hết hạn và thiết bị bắt buộc thiếu hồ sơ (FR-CMP-007)."""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from normcore.api.compliance import get_reminder_days
from normcore.costing import compliance

STATUS_INDICATOR = {
	compliance.EXPIRED: "red",
	compliance.DUE: "orange",
	compliance.MISSING: "red",
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	on = getdate(filters.get("as_of") or nowdate())
	reminder = get_reminder_days()

	types = {
		t.name: t.compliance_required
		for t in frappe.get_all("NC Equipment Type", fields=["name", "compliance_required"])
	}
	equipments = [
		{**e, "compliance_required": types.get(e.equipment_type)}
		for e in frappe.get_list("NC Equipment", fields=["name", "department", "equipment_type"])
	]
	by_equipment = {e["name"]: e for e in equipments}
	records = frappe.get_list(
		"NC Equipment Compliance",
		fields=[
			"name",
			"record_code",
			"equipment",
			"department",
			"record_type",
			"provider",
			"performed_on",
			"expiry_date",
		],
	)
	for r in records:
		r["equipment_type"] = (by_equipment.get(r.equipment) or {}).get("equipment_type")
	grouped = {}
	for r in records:
		grouped.setdefault(r.equipment, []).append(r)
	missing = compliance.missing_required(equipments, grouped, on)
	rows = compliance.build_expiry_report(
		records, missing, on, reminder, department=filters.get("department"), status=filters.get("status")
	)
	return get_columns(), rows, None, None, get_summary(rows, reminder)


def get_columns():
	return [
		{
			"fieldname": "department",
			"label": _("Khoa"),
			"fieldtype": "Link",
			"options": "NC Department",
			"width": 140,
		},
		{
			"fieldname": "equipment",
			"label": _("Thiết bị"),
			"fieldtype": "Link",
			"options": "NC Equipment",
			"width": 160,
		},
		{
			"fieldname": "equipment_type",
			"label": _("Loại thiết bị"),
			"fieldtype": "Link",
			"options": "NC Equipment Type",
			"width": 130,
		},
		{
			"fieldname": "record",
			"label": _("Hồ sơ"),
			"fieldtype": "Link",
			"options": "NC Equipment Compliance",
			"width": 150,
		},
		{"fieldname": "record_type", "label": _("Loại hồ sơ"), "fieldtype": "Data", "width": 130},
		{"fieldname": "provider", "label": _("Đơn vị thực hiện"), "fieldtype": "Data", "width": 160},
		{"fieldname": "performed_on", "label": _("Ngày thực hiện"), "fieldtype": "Date", "width": 110},
		{"fieldname": "expiry_date", "label": _("Ngày hết hạn"), "fieldtype": "Date", "width": 110},
		{"fieldname": "days_left", "label": _("Còn (ngày)"), "fieldtype": "Int", "width": 90},
		{"fieldname": "status", "label": _("Trạng thái"), "fieldtype": "Data", "width": 150},
	]


def get_summary(rows, reminder):
	count = lambda st: sum(1 for r in rows if r["status"] == st)  # noqa: E731
	return [
		{"value": count(compliance.EXPIRED), "label": _("Hết hạn"), "datatype": "Int", "indicator": "red"},
		{"value": count(compliance.DUE), "label": _("Sắp hết hạn"), "datatype": "Int", "indicator": "orange"},
		{
			"value": count(compliance.MISSING),
			"label": _("Thiếu hồ sơ còn hạn"),
			"datatype": "Int",
			"indicator": "red",
		},
		{"value": reminder, "label": _("Số ngày nhắc hạn"), "datatype": "Int", "indicator": "blue"},
	]
