"""Lớp ghi CSDL của lần tính giá (AMD-015-02): ghi NC Service Cost và dòng giải trình từ kết quả thuần."""

import frappe

from normcore.costing import engine

DIRECT_FIELD = {
	"LABOR": "direct_labor",
	"DRUG": "direct_drug",
	"SUPPLY": "direct_supply",
	"EQUIPMENT": "direct_equipment",
	"INFRA": "direct_infra",
	"UTILITY": "direct_utility",
}
ALLOC_FIELD = {
	"LABOR": "alloc_labor",
	"DRUG_SUPPLY": "alloc_drug_supply",
	"DEPRECIATION": "alloc_depreciation",
	"UTILITY": "alloc_utility",
	"MANAGEMENT": "alloc_management",
}


HEADER_FIELDS = (
	"costing_run",
	"technical_service",
	"department",
	"norm_set",
	"calc_status",
	"calc_message",
	"volume",
	"is_paraclinical",
	"eqa_cost",
	*DIRECT_FIELD.values(),
	*ALLOC_FIELD.values(),
	"full_cost",
	"accumulation",
	"obligation",
	"calculated_price",
	"rounded_price",
)
RECON_FIELDS = (
	"costing_run",
	"cost_center",
	"cost_category",
	"costed_amount",
	"accounting_amount",
	"variance",
	"variance_pct",
	"over_tolerance",
)
LINE_DT, SYSTEM_DT, RECON_DT = "NC Service Cost Line", "NC Test System Cost", "NC Reconciliation Line"


def _f(x):
	return None if x is None else float(x)


def _line_values(ln: engine.CostLine) -> dict:
	return {
		"line_type": ln.line_type,
		"component": ln.component,
		"step_id": ln.step_id or None,
		"norm_line_id": ln.norm_line_id or None,
		"resource_label": ln.resource_label or None,
		"applied_qty": _f(ln.applied_qty),
		"unit_rate": _f(ln.unit_rate),
		"amount": float(ln.amount),
		"rate_source": ln.rate_source or None,
		"warning": ln.warning or None,
		"allocation_rule": ln.allocation_rule,
		"driver_value": _f(ln.driver_value),
		"driver_total": _f(ln.driver_total),
		"pool_amount": _f(ln.pool_amount),
		"test_system": ln.test_system or None,
		"line_origin": ln.line_origin or None,
		"cost_level": ln.cost_level or None,
		"k_factor": _f(ln.k_factor),
		"divisor_label": ln.divisor_label or None,
		"divisor_value": _f(ln.divisor_value),
		"divisor_source": ln.divisor_source or None,
	}


def _system_values(t) -> dict:
	return {
		"test_system": t.test_system,
		"norm_set": t.norm_set,
		"patient_results": _f(t.patient_results),
		"share_pct": _f(t.share_pct),
		"q_iqc": _f(t.q_iqc),
		"q_calibration": _f(t.q_calibration),
		"q_rerun": _f(t.q_rerun),
		"q_eqa": _f(t.q_eqa),
		"wastage_rate": _f(t.wastage_rate),
		"k_factor": _f(t.k_factor),
		"k_estimated": 1 if t.k_estimated else 0,
		"direct_cost": _f(t.direct_cost),
		"low_volume_warning": 1 if t.low_volume_warning else 0,
	}


LINE_FIELDS = (
	"line_type",
	"component",
	"step_id",
	"norm_line_id",
	"resource_label",
	"applied_qty",
	"unit_rate",
	"amount",
	"rate_source",
	"warning",
	"allocation_rule",
	"driver_value",
	"driver_total",
	"pool_amount",
	"test_system",
	"line_origin",
	"cost_level",
	"k_factor",
	"divisor_label",
	"divisor_value",
	"divisor_source",
)
SYSTEM_FIELDS = (
	"test_system",
	"norm_set",
	"patient_results",
	"share_pct",
	"q_iqc",
	"q_calibration",
	"q_rerun",
	"q_eqa",
	"wastage_rate",
	"k_factor",
	"k_estimated",
	"direct_cost",
	"low_volume_warning",
)


def service_cost_values(run_name, r) -> tuple[dict, list[dict], list[dict]]:
	"""Giá trị ghi của một kết quả: (trường NC Service Cost, dòng `lines`, dòng `test_system_costs`)."""
	header = {
		"costing_run": run_name,
		"technical_service": r.service,
		"department": r.department,
		"norm_set": r.norm_set or None,
		"calc_status": r.status,
		"calc_message": r.message or None,
		"volume": _f(r.volume),
		"is_paraclinical": 1 if r.is_paraclinical else 0,
		"eqa_cost": _f(r.eqa_cost),
	}
	for comp, field in DIRECT_FIELD.items():
		header[field] = float(r.direct_by_component.get(comp, 0))
	for cat, field in ALLOC_FIELD.items():
		header[field] = float(r.alloc_by_category.get(cat, 0))
	if r.price is not None:
		p = r.price
		header.update(
			{
				"full_cost": float(p.full_cost),
				"accumulation": float(p.accumulation),
				"obligation": float(p.obligation),
				"calculated_price": float(p.calculated_price),
				"rounded_price": float(p.rounded_price),
			}
		)
	return header, [_line_values(ln) for ln in r.lines], [_system_values(t) for t in r.test_system_costs]


def recon_values(run_name, row) -> dict:
	return {
		"costing_run": run_name,
		"cost_center": row.cost_center,
		"cost_category": row.cost_category,
		"costed_amount": _f(row.costed),
		"accounting_amount": _f(row.accounting),
		"variance": _f(row.variance),
		"variance_pct": _f(row.variance_pct),
		"over_tolerance": 1 if row.over_tolerance else 0,
	}


def canonical(doctype, values) -> dict:
	"""Cùng một dạng cho giá trị sắp ghi và giá trị đọc lại: trường số rỗng = 0 (Frappe lưu None thành 0)."""
	meta = frappe.get_meta(doctype)
	numeric = ("Float", "Currency", "Int", "Percent", "Check")
	out = {}
	for k, v in values.items():
		df = meta.get_field(k)
		out[k] = 0 if v is None and df is not None and df.fieldtype in numeric else v
	return out


def expected_rows(run_name, results, recon_rows) -> list[dict]:
	"""Bản ghi phẳng `snapshot.diff_rows` của kết quả tính lại, cùng dạng `loader.stored_rows`."""
	rows = []
	for r in results:
		header, lines, systems = service_cost_values(run_name, r)
		rows.append(
			{"key": ("cost", r.service, r.department), "values": canonical("NC Service Cost", header)}
		)
		for i, v in enumerate(lines, 1):
			rows.append({"key": ("line", r.service, r.department, i), "values": canonical(LINE_DT, v)})
		for i, v in enumerate(systems, 1):
			rows.append({"key": ("system", r.service, r.department, i), "values": canonical(SYSTEM_DT, v)})
	for row in recon_rows:
		if row.skipped:
			continue
		rows.append(
			{
				"key": ("recon", row.cost_center, row.cost_category),
				"values": canonical(RECON_DT, recon_values(run_name, row)),
			}
		)
	return rows


def write_results(run, results) -> list[str]:
	"""Tạo NC Service Cost cho từng kết quả. Kết quả do máy chủ ghi, quyền đã kiểm ở `run_costing`."""
	names = []
	for r in results:
		header, lines, systems = service_cost_values(run.name, r)
		sc = frappe.new_doc("NC Service Cost")
		sc.update(header)
		for v in systems:
			sc.append("test_system_costs", v)
		for v in lines:
			sc.append("lines", v)
		sc.insert(ignore_permissions=True)
		names.append(sc.name)
	return names


def write_reconciliation(run, rows) -> list[str]:
	"""Tạo NC Reconciliation Line từ kết quả đối soát (bỏ hàng `skipped`). Máy chủ ghi, quyền đã kiểm ở `run_costing`."""
	names = []
	for r in rows:
		if r.skipped:
			continue
		doc = frappe.new_doc("NC Reconciliation Line")
		doc.update(recon_values(run.name, r))
		doc.flags.from_costing = True
		doc.insert(ignore_permissions=True)
		names.append(doc.name)
	return names
