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


def _published_procedure(technical_service, department):
	return frappe.db.get_value(
		"NC Clinical Procedure",
		{"technical_service": technical_service, "department": department, "workflow_state": "Đã ban hành"},
		"name",
		order_by="version_no desc",
	)


def _cases(technical_service, department, procedure):
	"""Các ca (áp phạm vi khoa của người gọi) cùng dịch vụ, khoa, quy trình."""
	heads = frappe.get_list(
		TS,
		filters={"technical_service": technical_service, "department": department, "procedure": procedure},
		fields=["name", "observed_on"],
		order_by="observed_on asc, name asc",
		limit_page_length=0,
	)
	if not heads:
		return []
	lines = frappe.get_all(
		"NC Time Study Line",
		filters={"parent": ["in", [h.name for h in heads]], "parenttype": TS},
		fields=[
			"parent",
			"step_id",
			"job_title",
			"headcount",
			"labor_minutes",
			"equipment",
			"machine_minutes",
		],
		order_by="idx asc",
		limit_page_length=0,
	)
	by_parent = {}
	for ln in lines:
		by_parent.setdefault(ln.parent, []).append(ln)
	return [{"observed_on": h.observed_on, "lines": by_parent.get(h.name, [])} for h in heads]


def _summary(technical_service, department, procedure):
	from normcore.core import settings
	from normcore.norm import time_study

	proc = frappe.get_doc("NC Clinical Procedure", procedure)
	order = {s.step_id: s.idx for s in proc.steps}
	cases = _cases(technical_service, department, procedure)
	# min_time_study_cases đọc qua core.settings mỗi lần gọi, không cache (ASM-014-01)
	summary = time_study.summarize(cases, settings.get("min_time_study_cases"), order)
	return proc, summary


@frappe.whitelist()
def get_result(technical_service, department, procedure=None):
	"""Trung vị số phút theo (bước, chức danh/thiết bị) của các ca bấm giờ (SCR-DSK-016, FR-TS-003)."""
	frappe.has_permission(TS, "read", throw=True)
	procedure = procedure or _published_procedure(technical_service, department)
	if not procedure:
		frappe.throw(_("Dịch vụ chưa có quy trình đã ban hành tại khoa này."))
	proc, summary = _summary(technical_service, department, procedure)
	titles = {s.step_id: s.step_title for s in proc.steps}
	doctype = {"labor": "NC Job Title", "equipment": "NC Equipment"}
	for row in summary["rows"]:
		row["step_title"] = titles.get(row["step_id"])
		row["resource_label"] = _label(doctype[row["kind"]], row["resource"])
	summary["procedure"] = procedure
	return summary


@frappe.whitelist()
def apply_to_norm_set(norm_set, confirm=0):
	"""Áp trung vị vào bộ định mức Nháp (FR-TS-004, FR-TS-005)."""
	from frappe.utils import cint

	from normcore.norm import time_study

	ns = frappe.get_doc("NC Norm Set", norm_set)
	frappe.has_permission("NC Norm Set", "write", doc=ns, throw=True)
	frappe.has_permission(TS, "read", throw=True)
	if ns.status != "Nháp":
		frappe.throw(_("Chỉ áp được vào bộ định mức Nháp."))
	_proc, summary = _summary(ns.technical_service, ns.department, ns.procedure)
	if not summary["n_cases"]:
		frappe.throw(_("Chưa có ca bấm giờ nào."))
	if not summary["sufficient"] and cint(confirm) != 1:
		return {
			"applied": False,
			"needs_confirm": True,
			"n_cases": summary["n_cases"],
			"min_cases": summary["min_cases"],
			"message": _("Mới có {0} ca, ít hơn mức tối thiểu {1}.").format(
				summary["n_cases"], summary["min_cases"]
			),
		}
	ref = time_study.basis_ref(summary["n_cases"], summary["first_date"], summary["last_date"])
	norm_lines = [ln.as_dict() for ln in ns.lines]
	updates, unmatched = time_study.plan_apply(norm_lines, summary["rows"], ref)
	by_id = {ln.line_id: ln for ln in ns.lines}
	for u in updates:
		row = by_id[u["line_id"]]
		row.hospital_qty = u["hospital_qty"]
		row.basis = u["basis"]
		row.basis_ref = u["basis_ref"]
	if updates:
		ns.save()
	return {
		"applied": True,
		"updated": [u["line_id"] for u in updates],
		"unmatched": unmatched,
		"n_cases": summary["n_cases"],
	}
