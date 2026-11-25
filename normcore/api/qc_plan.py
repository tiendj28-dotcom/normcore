"""API kế hoạch chất lượng và ngoại kiểm (FR-QC-001, 005, 007; SCR-DSK-032..034). Logic ở costing/qc_plans.py."""

import json

import frappe
from frappe import _

from normcore.costing import qc_plans


def _as_dict(value) -> dict:
	return json.loads(value) if isinstance(value, str) else (value or {})


@frappe.whitelist()
def estimate_tests(plan) -> dict:
	"""Số test ước tính mỗi năm từ form chưa lưu (không đọc CSDL)."""
	frappe.has_permission("NC QC Plan", "read", throw=True)
	plan = _as_dict(plan)
	iqc, cal = qc_plans.estimated_tests(plan)
	return {
		"iqc_tests": float(iqc),
		"calibration_tests": float(cal),
		"complete": qc_plans.estimate_complete(plan),
	}


@frappe.whitelist()
def missing_iqc_warning(test_system: str) -> dict:
	"""Cảnh báo hệ thống chưa có kế hoạch nội kiểm (FR-QC-007). Chỉ cảnh báo, không chặn khóa."""
	doc = frappe.get_doc("NC Test System", test_system)
	frappe.has_permission("NC Test System", "read", doc=doc, throw=True)
	cls_group = frappe.db.get_value("NC Technical Service", doc.technical_service, "cls_group")
	plan = None
	name = frappe.db.get_value("NC QC Plan", {"test_system": test_system})
	if name:
		plan = {
			"iqc_lines": frappe.get_all("NC QC IQC Line", {"parent": name, "parenttype": "NC QC Plan"}, pluck="name")
		}
	message = qc_plans.missing_iqc_warning(cls_group, plan, test_system)
	return {"warning": message is not None, "message": _(message) if message else None}


@frappe.whitelist()
def eqa_summary(program) -> dict:
	"""Số mẫu mỗi năm và tỷ lệ hiệu lực từng dịch vụ từ form chưa lưu (không đọc CSDL)."""
	frappe.has_permission("NC EQA Program", "read", throw=True)
	program = _as_dict(program)
	rows = program.get("services") or []
	paraclinical = {r.get("technical_service") for r in rows}  # mục này không kiểm cận lâm sàng: chỉ tóm tắt
	errors = qc_plans.validate_eqa_program({**program, "services": rows}, paraclinical)
	share_errors = [e for e in errors if "Tỷ lệ riêng" in e or "Tổng tỷ lệ" in e]
	positive = [r for r in rows if _num(r.get("share_pct")) > 0]
	total = sum(_num(r.get("share_pct")) for r in rows)
	mode = "invalid" if share_errors else ("custom" if positive else "equal")
	shares = qc_plans.eqa_shares(rows) if mode != "invalid" else []
	try:
		samples = float(qc_plans.eqa_samples_per_year(program.get("rounds_per_year") or 0, program.get("samples_per_round") or 0))
	except Exception:
		samples = 0.0
	return {
		"samples_per_year": samples,
		"mode": mode,
		"shares": [
			{"technical_service": r.get("technical_service"), "share_pct": float(s * 100)}
			for r, s in zip(rows, shares, strict=False)
		],
		"total_pct": float(total),
		"message": _(share_errors[0]) if share_errors else None,
	}


def _num(v):
	try:
		return float(v or 0)
	except (TypeError, ValueError):
		return 0.0
