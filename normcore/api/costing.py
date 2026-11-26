"""API lần tính giá (FEAT-015; UC-012; FR-COST-001..003, 006, 007, 010, 015, 016). Logic ở normcore.costing;
ở đây chỉ nạp dữ liệu, kiểm quyền và định dạng kết quả."""

from decimal import Decimal

import frappe
from frappe import _

from normcore.costing import allocation, cls, engine, reconcile

RUN, COST, RECON = "NC Costing Run", "NC Service Cost", "NC Reconciliation Line"
CALCULATED = "Đã tính"
CATEGORY_LABEL = {
	"LABOR": "Nhân công",
	"DRUG_SUPPLY": "Thuốc, vật tư",
	"DEPRECIATION": "Khấu hao",
	"UTILITY": "Điện, nước",
	"MANAGEMENT": "Quản lý chung",
}
NOTE_NO_DEPRECIATION = "Khấu hao bị loại (loại giá không kết cấu khấu hao)"
LEVEL_LABEL = {
	"RESULT": "Theo kết quả",
	"TUBE": "Theo ống mẫu",
	"BATCH": "Theo mẻ",
	"DAY": "Theo ngày-máy",
	"PERIOD": "Theo kỳ",
}
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
	run_doc = _run(run, "read")
	rows = frappe.get_list(
		COST,
		filters={"costing_run": run},
		fields=[
			"name",
			"technical_service as service",
			"department",
			"calc_status",
			"calc_message",
			"is_paraclinical",
			"eqa_cost",
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
	systems: dict = {}
	if rows:
		for t in frappe.get_all(
			"NC Test System Cost",
			{"parent": ["in", [r["name"] for r in rows]], "parenttype": COST},
			[
				"parent",
				"test_system",
				"norm_set",
				"patient_results",
				"share_pct",
				"k_factor",
				"k_estimated",
				"direct_cost",
				"low_volume_warning",
			],
			order_by="idx asc",
		):
			systems.setdefault(t.pop("parent"), []).append(t)
	for r in rows:
		r["test_systems"] = systems.get(r["name"], [])
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
		r["has_volume_warning"] = allocation.VOLUME_WARNING in (r.get("calc_message") or "")
		counts[r["calc_status"]] = counts.get(r["calc_status"], 0) + 1
	return {
		"results": rows,
		"counts": counts,
		"recon_blocked": len(_blockers(run)),
		"run": {
			"volume_scenario": run_doc.get("volume_scenario"),
			"compliance_allocation_mode": run_doc.get("compliance_allocation_mode"),
			"run_warnings": [x for x in (run_doc.get("run_warnings") or "").split("\n") if x],
		},
	}


def _blockers(run) -> list[str]:
	"""Dòng đối soát vượt ngưỡng chưa có giải trình (FR-COST-009)."""
	if not frappe.has_permission(RECON, "read"):
		return []
	lines = frappe.get_all(
		RECON, {"costing_run": run}, ["cost_center", "cost_category", "over_tolerance", "explanation"]
	)
	return reconcile.lock_blockers(lines)


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
		ln.test_system or "",
		ln.line_origin or "",
		ln.cost_level or "",
		d(ln.k_factor) or None,  # Float trống đọc ra 0; k luôn > 0
		ln.divisor_label or "",
		d(ln.divisor_value),
		ln.divisor_source or "",
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
		"test_system": c.test_system,
		"line_origin": c.line_origin,
		"cost_level": c.cost_level,
		"cost_level_label": _(LEVEL_LABEL.get(c.cost_level, c.cost_level)) if c.cost_level else "",
		"k_factor": None if c.k_factor is None else float(c.k_factor),
		"divisor_label": c.divisor_label,
		"divisor_value": None if c.divisor_value is None else float(c.divisor_value),
		"divisor_source": c.divisor_source,
	}
	if c.line_type == engine.LINE_ALLOC:
		out.update(
			allocation_rule=c.allocation_rule,
			driver_value=None if c.driver_value is None else float(c.driver_value),
			driver_total=None if c.driver_total is None else float(c.driver_total),
			pool_amount=None if c.pool_amount is None else float(c.pool_amount),
		)
	return out


def _groups(lines, label) -> list:
	return [
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


def _paraclinical(sc, lines, label) -> dict:
	"""FR-COST-031 (SCR-DSK-023): khối hệ thống xét nghiệm, "k được tính thế nào", dòng cấp dịch vụ."""
	rows = list(sc.test_system_costs)
	qsum = sum((Decimal(str(r.patient_results or 0)) for r in rows), Decimal(0))
	equip = _names("NC Test System", "main_equipment", {r.test_system for r in rows})
	systems = []
	for r in rows:
		qbn = Decimal(str(r.patient_results or 0))
		by_results = bool(qsum) and abs(Decimal(str(r.share_pct or 0)) - qbn / qsum * 100) < Decimal("0.0001")
		parts = [r.patient_results, r.q_iqc, r.q_calibration, r.q_rerun, r.q_eqa]
		systems.append(
			{
				"test_system": r.test_system,
				"norm_set": r.norm_set,
				"equipment": equip.get(r.test_system),
				"patient_results": r.patient_results,
				"share_pct": r.share_pct,
				"share_source": _("Từ số kết quả trả") if by_results else _("Khai tay"),
				"q_iqc": r.q_iqc,
				"q_calibration": r.q_calibration,
				"q_rerun": r.q_rerun,
				"q_eqa": r.q_eqa,
				"total_tests": sum((x or 0) for x in parts),
				"wastage_rate": r.wastage_rate,
				"k_factor": r.k_factor,
				"k_estimated": bool(r.k_estimated),
				"direct_cost": r.direct_cost,
				"low_volume_warning": bool(r.low_volume_warning),
				"groups": _groups([c for c in lines if c.test_system == r.test_system], label),
			}
		)
	weighted = sum(
		(Decimal(str(r.share_pct or 0)) / 100 * Decimal(str(r.direct_cost or 0)) for r in rows), Decimal(0)
	)
	return {
		"systems": systems,
		"service_lines": [_line_dict(c) for c in lines if not c.test_system and c.line_origin],
		"weighted_direct": float(cls.r2(weighted)),
		"eqa_cost": sc.eqa_cost,
		"direct_total": float(cls.r2(weighted) + Decimal(str(sc.eqa_cost or 0))),
	}


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
	groups = _groups(lines, label)
	paraclinical = _paraclinical(sc, lines, label) if sc.is_paraclinical else None
	if (
		paraclinical
	):  # tổng dịch vụ là bình quân gia quyền các hệ thống (BR-CLS-013), không phải cộng mọi dòng
		direct_total = Decimal(str(paraclinical["direct_total"]))
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
	allocation_lines = [_line_dict(c) for c in lines if c.line_type == engine.LINE_ALLOC]
	notes = []
	for marker, text in (
		(cls.EXPIRED_ZERO_NOTE, "Khấu hao thiết bị hết thời gian sử dụng: ZERO"),
		(cls.EXPIRED_CONTINUE_NOTE, "Khấu hao thiết bị hết thời gian sử dụng: CONTINUE"),
	):
		if any(marker in c.warning for c in lines):
			notes.append(_(text))
	if not include_depr:
		notes.append(_(NOTE_NO_DEPRECIATION))
	if not allocation_lines and sc.calc_status != "Lỗi":
		notes.append(_(NOTE_NO_ALLOCATION))
	if allocation.VOLUME_WARNING in (sc.calc_message or ""):
		notes.append(_(allocation.VOLUME_WARNING))
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
			"has_allocation": bool(allocation_lines),
			"is_paraclinical": bool(sc.is_paraclinical),
		},
		"structure": structure,
		"direct_groups": groups,
		"allocation_lines": allocation_lines,
		"notes": notes,
		"paraclinical": paraclinical,
	}


def _recon_view(row) -> dict:
	costed, acc = row.costed_amount or 0, row.accounting_amount or 0
	return {
		"name": row.name,
		"cost_center": row.cost_center,
		"cost_category": row.cost_category,
		"category_label": CATEGORY_LABEL.get(row.cost_category, row.cost_category),
		"costed_amount": costed,
		"accounting_amount": acc,
		"variance": row.variance,
		"variance_pct": row.variance_pct if acc else None,
		"remainder": max(acc - costed, 0),
		"over_tolerance": row.over_tolerance,
		"explanation": row.explanation,
		"needs_explanation": bool(row.over_tolerance and not (row.explanation or "").strip()),
	}


@frappe.whitelist()
def get_reconciliation(run):
	"""FR-COST-008, 009 (SCR-DSK-024): bảng đối soát của một lần tính."""
	doc = _run(run, "read")
	frappe.has_permission(RECON, "read", throw=True)
	rows = frappe.get_all(
		RECON,
		{"costing_run": run},
		[
			"name",
			"cost_center",
			"cost_category",
			"costed_amount",
			"accounting_amount",
			"variance",
			"variance_pct",
			"over_tolerance",
			"explanation",
		],
	)
	order = {c: i for i, c in enumerate(allocation.CATEGORIES)}
	rows.sort(key=lambda r: (r.cost_center, order.get(r.cost_category, len(order))))
	centers = _names("NC Cost Center", "cost_center_name", {r.cost_center for r in rows})
	lines = []
	for r in rows:
		v = _recon_view(r)
		v["cost_center_name"] = centers.get(r.cost_center)
		lines.append(v)
	blocked = sum(1 for v in lines if v["needs_explanation"])
	include_depr = bool(frappe.db.get_value("NC Price Category", doc.price_category, "include_depreciation"))
	tolerance = frappe.db.get_value("NC Costing Parameter Set", doc.parameter_set, "reconciliation_tolerance")
	calculated = doc.status == CALCULATED
	return {
		"run": doc.name,
		"status": doc.status,
		"tolerance": tolerance,
		"include_depreciation": include_depr,
		"partial_scope": bool(doc.scope_departments or doc.scope_services),
		"warnings": [w for w in (doc.allocation_warnings or "").split("\n") if w],
		"lines": lines,
		"blocked": blocked,
		"can_explain": calculated and bool(frappe.has_permission(RECON, "write")),
		"can_lock": calculated and bool(frappe.has_permission(RUN, "write", doc=doc)) and blocked == 0,
	}


@frappe.whitelist()
def save_explanation(line, explanation):
	"""FR-COST-009: ghi giải trình của một dòng đối soát (controller kiểm trạng thái lần tính)."""
	doc = frappe.get_doc(RECON, line)
	frappe.has_permission(RECON, "write", doc=doc, throw=True)
	doc.explanation = explanation
	doc.save()
	return {
		"name": doc.name,
		"explanation": doc.explanation,
		"needs_explanation": bool(doc.over_tolerance and not (doc.explanation or "").strip()),
		"blocked": len(_blockers(doc.costing_run)),
	}


@frappe.whitelist()
def lock_run(run):
	"""UC-012 bước 8: khóa lần tính giá; lỗi của `lock_costing` trả nguyên văn."""
	doc = _run(run, "write")
	return {"status": doc.lock_costing()}
