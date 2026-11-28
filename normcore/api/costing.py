"""API lần tính giá (FEAT-015; UC-012; FR-COST-001..003, 006, 007, 010, 015, 016). Logic ở normcore.costing;
ở đây chỉ nạp dữ liệu, kiểm quyền và định dạng kết quả."""

from decimal import Decimal

import frappe
from frappe import _

from normcore.costing import allocation, cls, compare, engine, reconcile, resources, sensitivity, snapshot

RUN, COST, RECON = "NC Costing Run", "NC Service Cost", "NC Reconciliation Line"
CALCULATED, LOCKED = "Đã tính", "Đã khóa"
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
	recon = _recon_lines(run) if frappe.has_permission(RECON, "read") else []
	blockers = reconcile.lock_blockers(recon)
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
		"recon_blocked": len(blockers),
		"physical_unreconciled": sum(
			1
			for r in recon
			if _kind(r) == reconcile.MATERIAL
			and not r.item
			and r.recon_status == reconcile.UNRECONCILED
			and reconcile.needs_explanation(r)
		),
		"snapshot_hash": run_doc.get("snapshot_hash"),
		"can_duplicate": bool(frappe.has_permission(RUN, "create")),
		"can_verify": run_doc.status == LOCKED and bool(run_doc.get("snapshot_file")),
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
	return reconcile.lock_blockers(_recon_lines(run))


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
		"needs_explanation": reconcile.needs_explanation(row),
	}


RECON_FIELDS = [
	"name",
	"cost_center",
	"cost_category",
	"costed_amount",
	"accounting_amount",
	"variance",
	"variance_pct",
	"over_tolerance",
	"explanation",
	"recon_type",
	"recon_status",
	"department",
	"item",
	"technical_service",
	"calculated_qty",
	"actual_qty",
]


def _kind(row) -> str:
	return row.get("recon_type") or reconcile.FINANCIAL


def _recon_lines(run):
	return frappe.get_all(RECON, {"costing_run": run}, RECON_FIELDS)


@frappe.whitelist()
def get_reconciliation(run):
	"""FR-COST-008, 009 (SCR-DSK-024): bảng đối soát của một lần tính."""
	doc = _run(run, "read")
	frappe.has_permission(RECON, "read", throw=True)
	all_rows = _recon_lines(run)
	rows = [r for r in all_rows if _kind(r) == reconcile.FINANCIAL]
	order = {c: i for i, c in enumerate(allocation.CATEGORIES)}
	rows.sort(key=lambda r: (r.cost_center, order.get(r.cost_category, len(order))))
	centers = _names("NC Cost Center", "cost_center_name", {r.cost_center for r in rows})
	lines = []
	for r in rows:
		v = _recon_view(r)
		v["cost_center_name"] = centers.get(r.cost_center)
		lines.append(v)
	blocked = sum(1 for r in all_rows if reconcile.needs_explanation(r))
	material = [r for r in all_rows if _kind(r) == reconcile.MATERIAL]
	physical = {
		"available": _physical_available(doc),
		"material_blocked": sum(1 for r in material if reconcile.needs_explanation(r)),
		"unreconciled": sum(1 for r in material if r.recon_status == reconcile.UNRECONCILED),
		"volume_warnings": sum(1 for r in all_rows if _kind(r) == reconcile.VOLUME and r.over_tolerance),
	}
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
		"physical": physical,
		"blocked": blocked,
		"can_explain": calculated and bool(frappe.has_permission(RECON, "write")),
		"can_lock": calculated and bool(frappe.has_permission(RUN, "write", doc=doc)) and blocked == 0,
	}


def _physical_available(doc) -> int:
	"""ASM-037-02: chỉ lập đối soát vật chất, sản lượng khi kịch bản là "Thực tế 12 tháng"."""
	return int((doc.get("volume_scenario") or "Thực tế 12 tháng") == "Thực tế 12 tháng")


@frappe.whitelist()
def get_physical_reconciliation(run):
	"""FR-COST-026..029 (SCR-DSK-038): đối soát vật chất theo (khoa, mặt hàng), sản lượng theo (dịch vụ, khoa)."""
	doc = _run(run, "read")
	frappe.has_permission(RECON, "read", throw=True)
	rows = _recon_lines(run)
	items = _names("NC Item", "item_name", {r.item for r in rows if r.item})
	norm_uom = _names("NC Item", "norm_uom", {r.item for r in rows if r.item})
	services = _names(
		"NC Technical Service", "service_name", {r.technical_service for r in rows if r.technical_service}
	)
	depts = _names("NC Department", "department_name", {r.department for r in rows if r.department})

	def view(r):
		diff = None
		# Frappe lưu số trống thành 0: lượng thực tế 0 = thiếu số liệu (xuất kho, sản lượng HIS)
		if r.recon_status != reconcile.UNRECONCILED and r.actual_qty:
			diff = (r.actual_qty or 0) - (r.calculated_qty or 0)
		out = {
			"name": r.name,
			"department": r.department,
			"department_name": depts.get(r.department),
			"calculated_qty": r.calculated_qty,
			"actual_qty": r.actual_qty,
			"diff_qty": diff,
			"variance_pct": r.variance_pct if diff is not None else None,
			"over_tolerance": r.over_tolerance,
			"explanation": r.explanation,
			"needs_explanation": reconcile.needs_explanation(r),
		}
		if _kind(r) == reconcile.MATERIAL:
			out.update(
				item=r.item,
				item_name=items.get(r.item),
				norm_uom=norm_uom.get(r.item),
				recon_status=r.recon_status,
			)
		else:
			out.update(technical_service=r.technical_service, service_name=services.get(r.technical_service))
		return out

	material = sorted(
		(view(r) for r in rows if _kind(r) == reconcile.MATERIAL),
		key=lambda v: (v["department"] or "", v["item"] is not None, v["item"] or ""),
	)
	volume = sorted(
		(view(r) for r in rows if _kind(r) == reconcile.VOLUME),
		key=lambda v: (v["technical_service"] or "", v["department"] or ""),
	)
	blocked = sum(1 for r in rows if reconcile.needs_explanation(r))
	calculated = doc.status == CALCULATED
	tol = (
		frappe.db.get_value(
			"NC Costing Parameter Set",
			doc.parameter_set,
			["material_recon_tolerance", "volume_recon_tolerance"],
			as_dict=True,
		)
		or {}
	)
	return {
		"run": doc.name,
		"status": doc.status,
		"scenario": doc.get("volume_scenario"),
		"available": _physical_available(doc),
		"material_tolerance": tol.get("material_recon_tolerance") or 5,
		"volume_tolerance": tol.get("volume_recon_tolerance") or 2,
		"material": material,
		"volume": volume,
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
		"needs_explanation": reconcile.needs_explanation(doc.as_dict()),
		"blocked": len(_blockers(doc.costing_run)),
	}


@frappe.whitelist()
def lock_run(run):
	"""UC-012 bước 8: khóa lần tính giá; lỗi của `lock_costing` trả nguyên văn."""
	doc = _run(run, "write")
	return {"status": doc.lock_costing()}


@frappe.whitelist()
def verify_snapshot(run):
	"""NFR-REL-001: kiểm tra tái lập từ tệp ảnh chụp (đọc, không ghi)."""
	return _run(run, "read").verify_snapshot()


@frappe.whitelist()
def duplicate_run(run):
	"""FR-COST-012: nhân bản lần tính (kể cả đã khóa) thành lần tính mới ở "Nháp"."""
	return {"name": _run(run, "read").duplicate_run()}


def run_meta(doc) -> dict:
	"""Đầu vào của một lần tính, dạng dùng cho `compare.input_changes`."""
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"fiscal_year": doc.fiscal_year,
		"costing_date": str(doc.costing_date),
		"parameter_set": doc.parameter_set,
		"accounting_import": doc.accounting_import,
		"price_category": doc.price_category,
		"volume_scenario": doc.get("volume_scenario"),
		"compliance_allocation_mode": doc.get("compliance_allocation_mode"),
		"scope_departments": sorted(r.department for r in doc.scope_departments),
		"scope_services": sorted(r.technical_service for r in doc.scope_services),
	}


def _flat_costs(run):
	fields = ["technical_service", "department", "calc_status", "full_cost"]
	fields += [f for _g, f, _l in compare.COMPONENTS]
	return frappe.get_list(COST, {"costing_run": run}, fields, limit_page_length=0)


def _f2(x):
	return None if x is None else float(x)


def build_comparison(base_run, other_run, only_changed=0) -> dict:
	"""FR-COST-013: so sánh hai lần tính đã có kết quả; dùng chung cho API và Script Report."""
	if base_run == other_run:
		frappe.throw(_("Chọn hai lần tính giá khác nhau"))
	docs = [_run(n, "read") for n in (base_run, other_run)]
	for d in docs:
		if d.status not in (CALCULATED, LOCKED):
			frappe.throw(_("Lần tính giá {0} chưa có kết quả").format(d.name))
	diffs = compare.compare(_flat_costs(base_run), _flat_costs(other_run))
	summary = compare.summary(diffs)
	summary["total_diff"] = _f2(summary["total_diff"])
	if frappe.utils.cint(only_changed):
		diffs = [d for d in diffs if compare.changed(d)]
	services = _names("NC Technical Service", "service_name", {d.service for d in diffs})
	delta = lambda x: {"base": _f2(x.base), "other": _f2(x.other), "diff": _f2(x.diff), "pct": _f2(x.pct)}  # noqa: E731
	rows = [
		{
			"service": d.service,
			"service_name": services.get(d.service),
			"department": d.department,
			"presence": d.presence,
			"base_status": d.base_status,
			"other_status": d.other_status,
			"full_cost": delta(d.full_cost),
			"components": [
				{"group": c.group, "field": c.field, "label": c.label, **delta(c)} for c in d.components
			],
		}
		for d in diffs
	]
	base_meta, other_meta = run_meta(docs[0]), run_meta(docs[1])
	return {
		"base": base_meta,
		"other": other_meta,
		"input_changes": [list(x) for x in compare.input_changes(base_meta, other_meta)],
		"summary": summary,
		"rows": rows,
	}


@frappe.whitelist()
def compare_runs(base_run, other_run, only_changed=0):
	"""FR-COST-013 (SCR-DSK-022): chênh lệch = lần so sánh - lần gốc, theo dịch vụ và cấu phần."""
	return build_comparison(base_run, other_run, only_changed)


# ---------------------------------------------------------------------------
# Phân tích độ nhạy (FEAT-037; FR-COST-030, UC-024). Chỉ đọc: không insert, save, db_set, commit.
# ---------------------------------------------------------------------------

SENSITIVITY_CACHE_SECONDS = 600


def _f(x):
	return None if x is None else float(x)


def _result_view(r: engine.ServiceResult) -> dict:
	p = r.price
	return {
		"status": r.status,
		"message": r.message,
		"full_cost": _f(p.full_cost) if p else None,
		"calculated_price": _f(p.calculated_price) if p else None,
		"rounded_price": _f(p.rounded_price) if p else None,
		"direct_total": _f(r.direct_total),
		"alloc_total": _f(sum(r.alloc_by_category.values(), Decimal(0))),
		"by_component": {k: _f(v) for k, v in r.direct_by_component.items()},
		"volume": _f(r.volume),
	}


def _stored_view(sc) -> dict:
	comp = {
		k: sc.get(f) or 0
		for k, f in (
			("LABOR", "direct_labor"),
			("DRUG", "direct_drug"),
			("SUPPLY", "direct_supply"),
			("EQUIPMENT", "direct_equipment"),
			("INFRA", "direct_infra"),
			("UTILITY", "direct_utility"),
		)
	}
	alloc = sum(
		sc.get(f) or 0
		for f in (
			"alloc_labor",
			"alloc_drug_supply",
			"alloc_depreciation",
			"alloc_utility",
			"alloc_management",
		)
	)
	return {
		"status": sc.calc_status,
		"message": sc.calc_message,
		"full_cost": sc.full_cost,
		"calculated_price": sc.calculated_price,
		"rounded_price": sc.rounded_price,
		"direct_total": sum(comp.values()),
		"alloc_total": alloc,
		"by_component": comp,
		"volume": sc.volume,
	}


def _sensitivity_context(service_cost):
	sc = frappe.get_doc(COST, service_cost)
	frappe.has_permission(COST, "read", doc=sc, throw=True)
	run = frappe.get_doc(RUN, sc.costing_run)
	if run.status not in (CALCULATED, LOCKED):
		frappe.throw(_("Lần tính chưa có kết quả"))
	return sc, run


def _snapshot_for(run) -> dict:
	"""Ảnh chụp đầu vào của lần tính: tệp đã lưu (Đã khóa) hoặc dựng chỉ đọc (Đã tính); đệm 10 phút, không ghi CSDL."""
	from normcore.nc_costing.doctype.nc_costing_run import loader

	key = f"nc_sensitivity_snapshot:{run.name}:{run.modified}"
	cached = frappe.cache().get_value(key)
	if cached:
		return cached
	if run.status == LOCKED and run.get("snapshot_file"):
		content = frappe.get_doc("File", {"file_url": run.snapshot_file}).get_content()
		blob = content.encode() if isinstance(content, str) else content
		snap = snapshot.unpack(blob, run.snapshot_hash)
	else:
		snap = loader.capture_snapshot(run, loader.eligible_from_results(run))
	frappe.cache().set_value(key, snap, expires_in_sec=SENSITIVITY_CACHE_SECONDS)
	return snap


def _input_of(snap, service, department):
	for x in snap["inputs"]:
		i = snapshot.from_plain(x)
		if (i.service, i.department) == (service, department):
			return i
	frappe.throw(_("{0} không có trong lần tính này").format(service))


def _units(items) -> dict:
	rows = frappe.get_all(
		"NC Item",
		{"name": ["in", list(items) or [""]]},
		["name", "item_name", "uom", "norm_units_per_purchase_unit"],
	)
	return {r.name: r for r in rows}


@frappe.whitelist()
def get_sensitivity_base(service_cost):
	"""FR-COST-030 (SCR-DSK-040): giá thành gốc và đầu vào có thể đổi giả định của một dịch vụ."""
	sc, run = _sensitivity_context(service_cost)
	inp = _input_of(_snapshot_for(run), sc.technical_service, sc.department)
	c = inp.paraclinical
	rates = {}
	items = {x.resource for x in inp.lines if x.resource}
	for x in inp.lines:
		if x.resource and inp.rates.get(x.line_id):
			rates[x.resource] = inp.rates[x.line_id].rate
	systems, equipments = [], {}
	if c is not None:
		for s in c.systems:
			eq = c.equipment.get(s.equipment)
			systems.append(
				{
					"test_system": s.code,
					"qbn": _f(s.qbn),
					"equipment": s.equipment,
					"mode": eq.mode if eq else None,
					"contract_cost": _f(eq.contract_cost) if eq else None,
				}
			)
			for x in s.lines:
				if x.norm.resource and x.norm.component != "EQUIPMENT":
					items.add(x.norm.resource)
					if s.rates.get(x.norm.line_id):
						rates[x.norm.resource] = s.rates[x.norm.line_id].rate
			items |= {i.item for i in s.iqc}
			for i in s.iqc:
				if i.rate:
					rates[i.item] = i.rate.rate
		for code in sorted(sensitivity._used_equipment(c)):
			eq = c.equipment.get(code)
			if eq:
				equipments[code] = {"equipment": code, "mode": eq.mode, "contract_cost": _f(eq.contract_cost)}
	meta = _units(items)
	return {
		"service_cost": sc.name,
		"run": run.name,
		"run_status": run.status,
		"service": sc.technical_service,
		"service_name": frappe.db.get_value("NC Technical Service", sc.technical_service, "service_name"),
		"department": sc.department,
		"is_paraclinical": bool(sc.is_paraclinical),
		"origin": _stored_view(sc),
		"inputs": {
			"volume": _f(inp.volume),
			"systems": systems,
			"items": [
				{
					"item": i,
					"item_name": meta[i].item_name if i in meta else i,
					"uom": meta[i].uom if i in meta else None,
					"norm_units": meta[i].norm_units_per_purchase_unit if i in meta else None,
					"purchase_price": _f(
						rates.get(i, Decimal(0))
						* Decimal(str((meta[i].norm_units_per_purchase_unit if i in meta else 1) or 1))
					)
					if i in rates
					else None,
				}
				for i in sorted(items)
			],
			"equipments": list(equipments.values()),
		},
		"modes": list(resources.ACQUISITION_MODES),
	}


@frappe.whitelist()
def run_sensitivity(service_cost, overrides=None):
	"""FR-COST-030: tính thử giá thành với giả định; không ghi gì. Giả định sai → ValidationError."""
	sc, run = _sensitivity_context(service_cost)
	ov = frappe.parse_json(overrides) if overrides else {}
	if not isinstance(ov, dict):
		frappe.throw(_("Giả định không hợp lệ"))
	snap = _snapshot_for(run)
	units = {
		k: Decimal(str(v.norm_units_per_purchase_unit or 1))
		for k, v in _units(set(ov.get("prices") or {})).items()
	}
	try:
		trial = sensitivity.trial(snap, sc.technical_service, sc.department, ov, units)
	except sensitivity.InvalidAssumption as e:
		frappe.throw(_(str(e)))
	origin = _stored_view(sc)
	warnings = []
	if run.status == CALCULATED:
		base = next(
			(
				r
				for r in snapshot.recompute(snap).results
				if (r.service, r.department) == (sc.technical_service, sc.department)
			),
			None,
		)
		if base is None or base.price is None or _f(base.price.full_cost) != _f(origin["full_cost"]):
			warnings.append(_("Dữ liệu đầu vào đã đổi sau lần tính; so sánh có thể lệch"))
	t = _result_view(trial)
	diff = None
	if t["full_cost"] is not None:
		d = t["full_cost"] - (origin["full_cost"] or 0)
		diff = {
			"full_cost": round(d, 2),
			"rounded_price": round((t["rounded_price"] or 0) - (origin["rounded_price"] or 0), 2),
			"pct": round(d / origin["full_cost"] * 100, 2) if origin["full_cost"] else None,
		}
	stored_systems = {
		x.test_system: x
		for x in frappe.get_all(
			"NC Test System Cost",
			{"parent": sc.name, "parenttype": COST},
			["test_system", "k_factor", "direct_cost"],
		)
	}
	systems = [
		{
			"test_system": x.test_system,
			"k_origin": stored_systems[x.test_system].k_factor if x.test_system in stored_systems else None,
			"k_trial": _f(x.k_factor),
			"direct_origin": stored_systems[x.test_system].direct_cost
			if x.test_system in stored_systems
			else None,
			"direct_trial": _f(x.direct_cost),
		}
		for x in trial.test_system_costs
	]
	return {
		"trial": t,
		"origin": origin,
		"diff": diff,
		"systems": systems,
		"warnings": warnings,
		"note": _("Kết quả thử, không lưu"),
	}
