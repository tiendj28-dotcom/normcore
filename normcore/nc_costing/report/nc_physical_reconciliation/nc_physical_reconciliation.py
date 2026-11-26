"""Script Report SCR-DSK-038 "Đối soát vật chất và sản lượng" (FEAT-037; FR-COST-026..029, BR-CLS-014, 015).

Dữ liệu lấy từ `normcore.api.costing.get_physical_reconciliation` (kiểm quyền đọc NC Costing Run)."""

import frappe
from frappe import _

from normcore.api import costing as api

MATERIAL, VOLUME = "Vật chất", "Sản lượng"


def _qty(width=140):
	return {"fieldtype": "Float", "precision": 2, "width": width}


def _columns(table):
	if table == VOLUME:
		return [
			{"fieldname": "service_label", "label": _("Service"), "fieldtype": "Data", "width": 240},
			{"fieldname": "department_label", "label": _("Department"), "fieldtype": "Data", "width": 180},
			{"fieldname": "calculated_qty", "label": _("Results returned"), **_qty()},
			{"fieldname": "actual_qty", "label": _("HIS volume"), **_qty()},
			{"fieldname": "diff_qty", "label": _("Difference"), **_qty()},
			{"fieldname": "variance_pct", "label": _("Variance (%)"), "fieldtype": "Percent", "width": 110},
			{"fieldname": "state", "label": _("State"), "fieldtype": "Data", "width": 210},
			{"fieldname": "explanation", "label": _("Note"), "fieldtype": "Small Text", "width": 220},
		]
	return [
		{"fieldname": "department_label", "label": _("Department"), "fieldtype": "Data", "width": 180},
		{"fieldname": "item_label", "label": _("Item"), "fieldtype": "Data", "width": 220},
		{"fieldname": "calculated_qty", "label": _("Calculated quantity"), **_qty(150)},
		{"fieldname": "actual_qty", "label": _("Actual stock issue"), **_qty(150)},
		{"fieldname": "diff_qty", "label": _("Difference"), **_qty()},
		{"fieldname": "variance_pct", "label": _("Variance (%)"), "fieldtype": "Percent", "width": 110},
		{"fieldname": "state", "label": _("State"), "fieldtype": "Data", "width": 230},
		{"fieldname": "explanation", "label": _("Explanation"), "fieldtype": "Small Text", "width": 220},
	]


def _material_state(x) -> str:
	if x.get("recon_status") == "Chưa đối soát":
		return "Chưa đối soát · cần giải trình" if x["needs_explanation"] else "Chưa đối soát · đã xác nhận"
	if not x["over_tolerance"]:
		return "Trong ngưỡng"
	return "Vượt ngưỡng · cần giải trình" if x["needs_explanation"] else "Vượt ngưỡng · đã giải trình"


def _attention(x, table) -> bool:
	if table == VOLUME:
		return bool(x["over_tolerance"])
	return bool(x["over_tolerance"]) or x.get("recon_status") == "Chưa đối soát"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	table = filters.get("table") or MATERIAL
	if not filters.get("costing_run"):
		return _columns(table), []
	info = api.get_physical_reconciliation(filters.costing_run)
	rows = []
	for x in info["volume" if table == VOLUME else "material"]:
		if filters.get("department") and x["department"] != filters.department:
			continue
		if frappe.utils.cint(filters.get("only_attention")) and not _attention(x, table):
			continue
		row = {**x, "department_label": f"{x['department']} · {x.get('department_name') or ''}".strip(" ·")}
		if table == VOLUME:
			row["service_label"] = f"{x['technical_service']} · {x.get('service_name') or ''}".strip(" ·")
			row["state"] = "Cảnh báo lệch sản lượng" if x["over_tolerance"] else "Trong ngưỡng"
		else:
			row["item_label"] = f"{x['item']} · {x.get('item_name') or ''}" if x.get("item") else "— (cả khoa)"
			row["state"] = _material_state(x)
		rows.append(row)
	return _columns(table), rows
