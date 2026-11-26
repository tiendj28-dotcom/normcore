"""API lần tính giá (FEAT-015; UC-012; FR-COST-001..003, 006, 007, 010, 015, 016). Logic ở normcore.costing;
ở đây chỉ nạp dữ liệu, kiểm quyền và định dạng kết quả."""

from decimal import Decimal

import frappe
from frappe import _

from normcore.costing import engine

RUN, COST = "NC Costing Run", "NC Service Cost"
NOTE_NO_DEPRECIATION = "Khấu hao bị loại (loại giá không kết cấu khấu hao)"
NOTE_NO_ALLOCATION = "Chưa gồm chi phí phân bổ chung (phân bổ cấp 1, cấp 2 làm ở FEAT-017)"


def _run(name, perm):
	doc = frappe.get_doc(RUN, name)
	frappe.has_permission(RUN, perm, doc=doc, throw=True)
	return doc


def _names(doctype, field, names):
	rows = frappe.get_all(doctype, {"name": ["in", list(names) or [""]]}, ["name", field])
	return {r["name"]: r[field] for r in rows}


@frappe.whitelist()
def check_scope(run):
	"""FR-COST-002: cặp đủ điều kiện, cặp chưa có bộ định mức "Đã khóa", có chạy nền không."""
	doc = _run(run, "write")
	info = doc.scope()
	services = _names(
		"NC Technical Service",
		"service_name",
		{e["service"] for e in info["eligible"]} | {s for s, _d in info["ineligible"]},
	)
	depts = _names(
		"NC Department",
		"department_name",
		{e["department"] for e in info["eligible"]} | {d for _s, d in info["ineligible"]},
	)
	return {
		"eligible": [
			{
				"service": e["service"],
				"service_name": services.get(e["service"]),
				"department": e["department"],
				"department_name": depts.get(e["department"]),
				"norm_set": e["norm_set"],
			}
			for e in info["eligible"]
		],
		"ineligible": [
			{
				"service": s,
				"service_name": services.get(s),
				"department": d,
				"department_name": depts.get(d),
			}
			for s, d in info["ineligible"]
		],
		"background": info["background"],
	}


@frappe.whitelist()
def start_costing(run, confirm_ineligible=0):
	"""FR-COST-002, 003, 015: chạy lần tính; có dịch vụ chưa đủ điều kiện thì phải xác nhận."""
	doc = _run(run, "write")
	info = doc.scope()
	status = doc.run_costing(confirm_ineligible)
	return {"status": status, "enqueued": status == "Đang tính", "skipped": len(info["ineligible"])}


@frappe.whitelist()
def get_progress(run):
	doc = _run(run, "read")
	return {"status": doc.status, "progress": doc.progress or 0}


@frappe.whitelist()
def get_run_results(run):
	"""Danh sách NC Service Cost của lần tính mà người dùng đọc được (kể cả phạm vi khoa)."""
	_run(run, "read")
	rows = frappe.get_list(
		COST,
		filters={"costing_run": run},
		fields=[
			"name",
			"technical_service as service",
			"department",
			"calc_status",
			"calc_message",
			"full_cost",
			"calculated_price",
			"rounded_price",
			"alloc_labor",
			"alloc_drug_supply",
			"alloc_depreciation",
			"alloc_utility",
			"alloc_management",
		],
		order_by="technical_service asc, department asc",
		limit_page_length=0,
	)
	services = _names("NC Technical Service", "service_name", {r["service"] for r in rows})
	depts = _names("NC Department", "department_name", {r["department"] for r in rows})
	counts: dict = {}
	for r in rows:
		r["service_name"] = services.get(r["service"])
		r["department_name"] = depts.get(r["department"])
		r["has_allocation"] = bool(
			sum(
				r.pop(k) or 0
				for k in (
					"alloc_labor",
					"alloc_drug_supply",
					"alloc_depreciation",
					"alloc_utility",
					"alloc_management",
				)
			)
		)
		counts[r["calc_status"]] = counts.get(r["calc_status"], 0) + 1
	return {"results": rows, "counts": counts}


def _cost_line(ln) -> engine.CostLine:
	d = lambda x: None if x is None else Decimal(str(x))  # noqa: E731
	return engine.CostLine(
		ln.line_type,
		ln.component,
		Decimal(str(ln.amount or 0)),
		ln.step_id or "",
		ln.norm_line_id or "",
		ln.resource_label or "",
		d(ln.applied_qty),
		d(ln.unit_rate),
		ln.rate_source or "",
		ln.warning or "",
		ln.allocation_rule,
		d(ln.driver_value),
		d(ln.driver_total),
		d(ln.pool_amount),
	)


def _line_dict(c: engine.CostLine, step_label=None) -> dict:
	out = {
		"line_type": c.line_type,
		"component": c.component,
		"step_id": c.step_id,
		"step_label": step_label if c.step_id else _("Chung"),
		"norm_line_id": c.norm_line_id,
		"resource_label": c.resource_label,
		"applied_qty": None if c.applied_qty is None else float(c.applied_qty),
		"unit_rate": None if c.unit_rate is None else float(c.unit_rate),
		"amount": float(c.amount),
		"rate_source": c.rate_source,
		"warning": c.warning,
	}
	if c.line_type == engine.LINE_ALLOC:
		out.update(
			allocation_rule=c.allocation_rule,
			driver_value=None if c.driver_value is None else float(c.driver_value),
			driver_total=None if c.driver_total is None else float(c.driver_total),
			pool_amount=None if c.pool_amount is None else float(c.pool_amount),
		)
	return out


@frappe.whitelist()
def get_explanation(service_cost):
	"""FR-COST-010, FR-COST-007, NFR-CPL-001 (SCR-DSK-023): bảng giải trình của một dịch vụ."""
	sc = frappe.get_doc(COST, service_cost)
	frappe.has_permission(COST, "read", doc=sc, throw=True)
	run = frappe.db.get_value(RUN, sc.costing_run, ["status", "price_category", "name"], as_dict=True)
	include_depr = bool(frappe.db.get_value("NC Price Category", run.price_category, "include_depreciation"))
	lines = [_cost_line(ln) for ln in sc.lines]
	step_titles = {}
	if sc.norm_set:
		procedure = frappe.db.get_value("NC Norm Set", sc.norm_set, "procedure")
		if procedure:
			step_titles = {
				s.step_id: s.step_title for s in frappe.get_doc("NC Clinical Procedure", procedure).steps
			}
	label = lambda sid: f"{sid} — {step_titles[sid]}" if sid in step_titles else sid  # noqa: E731
	direct_total = sum((c.amount for c in lines if c.line_type == engine.LINE_DIRECT), Decimal(0))
	alloc_total = sum((c.amount for c in lines if c.line_type == engine.LINE_ALLOC), Decimal(0))
	groups = [
		{
			"component": g["component"],
			"label": g["label"],
			"total": float(g["total"]),
			"steps": [
				{
					"step_id": s["step_id"],
					"step_label": label(s["step_id"]) if s["step_id"] else _("Chung"),
					"total": float(s["total"]),
					"lines": [_line_dict(c, label(c.step_id)) for c in s["lines"]],
				}
				for s in g["steps"]
			],
		}
		for g in engine.group_explanation(lines)
	]
	structure = []
	for field, name in (
		("direct_labor", "LABOR"),
		("direct_drug", "DRUG"),
		("direct_supply", "SUPPLY"),
		("direct_equipment", "EQUIPMENT"),
		("direct_infra", "INFRA"),
		("direct_utility", "UTILITY"),
	):
		amount = sc.get(field) or 0
		if amount:
			structure.append(
				{
					"component": name,
					"label": engine.COMPONENT_LABEL[name],
					"amount": amount,
					"share_pct": round(float(amount) / float(sc.full_cost) * 100, 2) if sc.full_cost else 0,
				}
			)
	allocation = [_line_dict(c) for c in lines if c.line_type == engine.LINE_ALLOC]
	notes = []
	if not include_depr:
		notes.append(_(NOTE_NO_DEPRECIATION))
	if not allocation and sc.calc_status != "Lỗi":
		notes.append(_(NOTE_NO_ALLOCATION))
	return {
		"header": {
			"service": sc.technical_service,
			"service_name": frappe.db.get_value("NC Technical Service", sc.technical_service, "service_name"),
			"department": sc.department,
			"costing_run": sc.costing_run,
			"run_status": run.status,
			"calc_status": sc.calc_status,
			"calc_message": sc.calc_message,
			"volume": sc.volume,
			"price_category": run.price_category,
			"include_depreciation": include_depr,
			"direct_total": float(direct_total),
			"alloc_total": float(alloc_total),
			"full_cost": sc.full_cost,
			"accumulation": sc.accumulation,
			"obligation": sc.obligation,
			"calculated_price": sc.calculated_price,
			"rounded_price": sc.rounded_price,
			"has_allocation": bool(allocation),
		},
		"structure": structure,
		"direct_groups": groups,
		"allocation_lines": allocation,
		"notes": notes,
	}
