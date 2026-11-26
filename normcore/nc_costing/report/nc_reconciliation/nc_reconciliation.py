"""Script Report SCR-DSK-024 "Bảng đối soát" (FEAT-017; FR-COST-008, FR-COST-009; BR-COST-015).

Dữ liệu lấy từ `normcore.api.costing.get_reconciliation` (kiểm quyền đọc NC Costing Run)."""

import frappe
from frappe import _

from normcore.api import costing as api


def _columns():
	money = {"fieldtype": "Currency", "width": 150}
	return [
		{"fieldname": "cost_center_label", "label": _("Cost center"), "fieldtype": "Data", "width": 200},
		{"fieldname": "category_label", "label": _("Cost category"), "fieldtype": "Data", "width": 150},
		{"fieldname": "costed_amount", "label": _("Costed amount"), **money},
		{"fieldname": "accounting_amount", "label": _("Accounting amount (incl. level 1)"), **money},
		{"fieldname": "variance", "label": _("Variance"), **money},
		{"fieldname": "variance_pct", "label": _("Variance (%)"), "fieldtype": "Percent", "width": 110},
		{"fieldname": "remainder", "label": _("Remainder"), **money},
		{"fieldname": "state", "label": _("State"), "fieldtype": "Data", "width": 200},
		{"fieldname": "explanation", "label": _("Explanation"), "fieldtype": "Small Text", "width": 220},
	]


def _state(line) -> str:
	if not line["over_tolerance"]:
		return "Theo dõi"
	return "Vượt ngưỡng · cần giải trình" if line["needs_explanation"] else "Vượt ngưỡng · đã giải trình"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("costing_run"):
		return _columns(), []
	info = api.get_reconciliation(filters.costing_run)
	rows = []
	for ln in info["lines"]:
		if filters.get("cost_center") and ln["cost_center"] != filters.cost_center:
			continue
		if frappe.utils.cint(filters.get("only_over")) and not ln["over_tolerance"]:
			continue
		rows.append(
			{
				**ln,
				"cost_center_label": f"{ln['cost_center']} · {ln['cost_center_name'] or ''}".strip(" ·"),
				"state": _state(ln),
			}
		)
	return _columns(), rows
