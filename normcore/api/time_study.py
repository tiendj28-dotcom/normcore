"""API khảo sát bấm giờ (FEAT-014; UC-010; FR-TS-001..005). Logic ở normcore.norm.time_study; ở đây nạp dữ liệu,
kiểm quyền và lưu."""

import frappe
from frappe import _

from normcore.api.norm import NAME_FIELD

TS = "NC Time Study"


def _label(doctype, name):
	if not name:
		return None
	return frappe.db.get_value(doctype, name, NAME_FIELD[doctype]) or name


def _load(name):
	doc = frappe.get_doc(TS, name)
	frappe.has_permission(TS, "read", doc=doc, throw=True)
	return doc


@frappe.whitelist()
def get_entry(name):
	"""Dữ liệu cho bảng ghi theo bước (SCR-DSK-015). Nhãn chức danh/thiết bị đọc ở máy chủ."""
	doc = _load(name)
	proc = frappe.get_doc("NC Clinical Procedure", doc.procedure)
	return {
		"doc": {
			k: doc.get(k)
			for k in ("name", "technical_service", "department", "procedure", "observed_on", "observer")
		},
		"steps": [
			{"step_id": s.step_id, "step_title": s.step_title, "phase": s.phase, "idx": s.idx}
			for s in proc.steps
		],
		"lines": [
			{
				"name": ln.name,
				"idx": ln.idx,
				"step_id": ln.step_id,
				"job_title": ln.job_title,
				"job_title_label": _label("NC Job Title", ln.job_title),
				"headcount": ln.headcount,
				"labor_minutes": ln.labor_minutes,
				"equipment": ln.equipment,
				"equipment_label": _label("NC Equipment", ln.equipment),
				"machine_minutes": ln.machine_minutes,
			}
			for ln in doc.lines
		],
		"can_write": bool(frappe.has_permission(TS, "write", doc=doc)),
	}
