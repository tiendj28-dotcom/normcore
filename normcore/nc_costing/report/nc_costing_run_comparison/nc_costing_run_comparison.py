"""Script Report "So sánh hai lần tính giá" (FEAT-018; FR-COST-013, SCR-DSK-022).

Dữ liệu lấy từ `normcore.api.costing.build_comparison` (kiểm quyền đọc cả hai lần tính). Chênh lệch = lần so
sánh − lần gốc."""

import frappe
from frappe import _
from frappe.utils import escape_html

from normcore.api import costing as api


def _columns():
	money = {"fieldtype": "Currency", "width": 150}
	return [
		{"fieldname": "label", "label": _("Service / component"), "fieldtype": "Data", "width": 300},
		{"fieldname": "base_value", "label": _("Base run"), **money},
		{"fieldname": "other_value", "label": _("Compared run"), **money},
		{"fieldname": "diff", "label": _("Difference"), **money},
		{"fieldname": "diff_pct", "label": _("Difference (%)"), "fieldtype": "Percent", "width": 110},
		{"fieldname": "note", "label": _("Note"), "fieldtype": "Data", "width": 220},
	]


def _note(row) -> str:
	if row["presence"] == "base_only":
		return "Chỉ ở lần gốc"
	if row["presence"] == "other_only":
		return "Chỉ ở lần so sánh"
	if row["base_status"] == "Lỗi":
		return "Lỗi ở lần gốc"
	if row["other_status"] == "Lỗi":
		return "Lỗi ở lần so sánh"
	if row["base_status"] != row["other_status"]:
		return f"Trạng thái: {row['base_status']} → {row['other_status']}"
	return ""


def _service_rows(row, service_names):
	node = f"{row['service']}|{row['department']}"
	fc = row["full_cost"]
	out = [
		{
			"node": node,
			"parent_node": None,
			"indent": 0,
			"label": f"{row['service']} — {row['service_name'] or ''} · {row['department']}",
			"base_value": fc["base"],
			"other_value": fc["other"],
			"diff": fc["diff"],
			"diff_pct": fc["pct"],
			"note": _note(row),
			"is_service": 1,
		}
	]
	for c in row["components"]:
		out.append(
			{
				"node": f"{node}|{c['field']}",
				"parent_node": node,
				"indent": 1,
				"label": f"{c['group']} · {c['label']}",
				"base_value": c["base"],
				"other_value": c["other"],
				"diff": c["diff"],
				"diff_pct": c["pct"],
				"note": "",
			}
		)
	return out


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("base_run") or not filters.get("other_run"):
		return _columns(), [], _("Select two costing runs to compare.")
	info = api.build_comparison(filters.base_run, filters.other_run, filters.get("only_changed", 1))
	rows = []
	for r in info["rows"]:
		if filters.get("technical_service") and r["service"] != filters.technical_service:
			continue
		rows.extend(_service_rows(r, None))
	b, o = info["base"], info["other"]
	message = (
		f"{_('Base run')} {escape_html(b['name'])} ({escape_html(b['status'])}) · {_('Compared run')} "
		f"{escape_html(o['name'])} ({escape_html(o['status'])}). {_('Difference = compared run − base run.')}"
	)
	if info["input_changes"]:
		items = "".join(
			f"<li>{escape_html(a)}: {escape_html(x)} → {escape_html(y)}</li>" for a, x, y in info["input_changes"]
		)
		message += f'<div class="alert alert-info" role="status"><b>{_("Inputs differ")}</b><ul>{items}</ul></div>'
	if not rows:
		message += f"<div>{_('The two costing runs give the same result for every service.')}</div>"
	s = info["summary"]
	summary = [
		{"label": _("Services"), "value": s["services"], "indicator": "gray"},
		{"label": _("With difference"), "value": s["changed"], "indicator": "red" if s["changed"] else "green"},
		{"label": _("Only in base run"), "value": s["base_only"], "indicator": "gray"},
		{"label": _("Only in compared run"), "value": s["other_only"], "indicator": "gray"},
		{
			"label": _("Total full cost difference"),
			"value": s["total_diff"],
			"datatype": "Currency",
			"indicator": "red" if s["total_diff"] else "green",
		},
	]
	return _columns(), rows, message, None, summary
