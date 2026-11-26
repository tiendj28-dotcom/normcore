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
	}


def write_results(run, results) -> list[str]:
	"""Tạo NC Service Cost cho từng kết quả. Kết quả do máy chủ ghi, quyền đã kiểm ở `run_costing`."""
	names = []
	for r in results:
		sc = frappe.new_doc("NC Service Cost")
		sc.update(
			{
				"costing_run": run.name,
				"technical_service": r.service,
				"department": r.department,
				"norm_set": r.norm_set,
				"calc_status": r.status,
				"calc_message": r.message or None,
				"volume": _f(r.volume),
			}
		)
		for comp, field in DIRECT_FIELD.items():
			sc.set(field, float(r.direct_by_component.get(comp, 0)))
		for cat, field in ALLOC_FIELD.items():
			sc.set(field, float(r.alloc_by_category.get(cat, 0)))
		if r.price is not None:
			p = r.price
			sc.update(
				{
					"full_cost": float(p.full_cost),
					"accumulation": float(p.accumulation),
					"obligation": float(p.obligation),
					"calculated_price": float(p.calculated_price),
					"rounded_price": float(p.rounded_price),
				}
			)
		for ln in r.lines:
			sc.append("lines", _line_values(ln))
		sc.insert(ignore_permissions=True)
		names.append(sc.name)
	return names
