"""Lớp đọc CSDL của lần tính giá (AMD-015-02): đọc DocType rồi dựng dữ liệu cho `normcore.costing`.

Nạp một lần theo lô (đơn giá, mặt hàng, thiết bị, phòng, sản lượng), không truy vấn từng dòng (technical-design 4.4).
"""

from decimal import Decimal

import frappe
from frappe.utils import cint, flt, getdate

from normcore.costing import (
	allocation,
	cls,
	compliance,
	engine,
	pricing,
	qc_plans,
	rates,
	resources,
	runner,
	snapshot,
	test_systems,
)
from normcore.nc_costing.doctype.nc_cost_center_driver.nc_cost_center_driver import get_driver_values
from normcore.nc_costing.doctype.nc_costing_run import writer

LOCKED_NORM = "Đã khóa"
VOLUME_SCENARIO = "Thực tế 12 tháng"  # mặc định; lần tính dùng `run.volume_scenario` (FR-COST-017)
IMAGING_GROUP = "Chẩn đoán hình ảnh"
ALLOC_MODE = {"Theo giá trị tài sản": cls.ALLOC_ASSET, "Gắn trực tiếp thiết bị": cls.ALLOC_DIRECT}
ATTACH = {"Hệ thống xét nghiệm": cls.ATTACH_SYSTEM, "Thiết bị": cls.ATTACH_EQUIP}
NAME_FIELD = {
	"NC Job Title": "job_title_name",
	"NC Item": "item_name",
	"NC Equipment": "equipment_name",
	"NC Room": "room_name",
}


def scope_values(run) -> tuple[list, list]:
	return [r.technical_service for r in run.scope_services], [r.department for r in run.scope_departments]


def scope_info(run) -> dict:
	"""FR-COST-001, FR-COST-002, ASM-015-03: cặp đủ điều kiện (bộ "Đã khóa") và cặp chưa đủ trong phạm vi."""
	ss, sd = scope_values(run)
	active = set(frappe.get_all("NC Technical Service", {"is_active": 1}, pluck="name"))
	rows = frappe.get_all(
		"NC Service Department",
		filters={"parenttype": "NC Technical Service"},
		fields=["parent", "department"],
	)
	pairs = {(r.parent, r.department) for r in rows if r.parent in active}
	fields = ["name", "technical_service", "department"]
	if frappe.get_meta("NC Norm Set").has_field("test_system"):  # trường do FEAT-034 thêm
		fields.append("test_system")
	norm_sets = frappe.get_all("NC Norm Set", {"status": LOCKED_NORM}, fields, order_by="name")
	send_out = frappe.get_all("NC Technical Service", {"is_send_out": 1, "is_paraclinical": 1}, pluck="name")
	test_system_rows = frappe.get_all("NC Test System", fields=["name", "status"])
	norm_sets = test_systems.norm_sets_to_cost(
		norm_sets, test_systems.in_costing_scope(test_system_rows), send_out
	)
	# FEAT-036: dịch vụ cận lâm sàng có hệ thống "Đang dùng" cùng khoa → một mục cho cả dịch vụ (4.8)
	cls_groups = _cls_groups(
		frappe.get_all(
			"NC Norm Set",
			{"status": LOCKED_NORM, "test_system": ["is", "set"]},
			["name", "test_system", "version_no"],
		)
	)
	norm_sets = [n for n in norm_sets if (n["technical_service"], n["department"]) not in cls_groups]
	pairs |= {(n["technical_service"], n["department"]) for n in norm_sets}
	pairs |= set(cls_groups)
	pairs = runner.scope_pairs(pairs, ss, sd)
	locked = {}
	for n in norm_sets:
		locked.setdefault((n["technical_service"], n["department"]), n["name"])
	for key in cls_groups:
		locked[key] = "cls"  # có bộ "Đã khóa": đủ điều kiện; mục dựng bên dưới
	_, ineligible = runner.eligibility(pairs, locked, ss, sd)
	in_scope = set(pairs)
	eligible = [
		{"service": n["technical_service"], "department": n["department"], "norm_set": n["name"]}
		for n in norm_sets
		if (n["technical_service"], n["department"]) in in_scope
	]
	eligible += [
		{"service": k[0], "department": k[1], "norm_set": "", "test_systems": v}
		for k, v in cls_groups.items()
		if k in in_scope
	]
	eligible.sort(key=lambda e: (e["service"], e["department"], e["norm_set"]))
	return {"eligible": eligible, "ineligible": ineligible}


def _cls_groups(norm_sets_all) -> dict:
	"""{(dịch vụ, khoa): [{"test_system", "norm_set"|""}]}: mọi hệ thống "Đang dùng" của dịch vụ cận lâm sàng,
	norm_set = bộ "Đã khóa" mới nhất của hệ thống (ASM-036-02)."""
	paraclinical = set(frappe.get_all("NC Technical Service", {"is_paraclinical": 1}, pluck="name"))
	best: dict = {}
	for n in sorted(norm_sets_all, key=lambda r: (cint(r.version_no), r.name)):
		best[n.test_system] = n.name
	groups: dict = {}
	rows = frappe.get_all(
		"NC Test System",
		{"status": test_systems.ACTIVE},
		["name", "technical_service", "department"],
		order_by="name",
	)
	for r in rows:
		if r.technical_service in paraclinical:
			groups.setdefault((r.technical_service, r.department), []).append(
				{"test_system": r.name, "norm_set": best.get(r.name, "")}
			)
	# Không hệ thống nào có bộ "Đã khóa": để đường FEAT-015 xử lý (bộ không gắn hệ thống, hoặc "chưa đủ điều kiện")
	# — ASM-036-26, giữ nguyên hành vi đã có của FEAT-031.
	return {k: v for k, v in groups.items() if any(x["norm_set"] for x in v)}


def pricing_params(run) -> engine.PricingParams:
	ps = frappe.get_doc("NC Costing Parameter Set", run.parameter_set)
	cat = frappe.db.get_value(
		"NC Price Category",
		run.price_category,
		["include_depreciation", "include_accumulation"],
		as_dict=True,
	)
	return engine.PricingParams.from_values(ps.as_dict(), cat)


def _label(doctype, name, cache):
	key = (doctype, name)
	if key not in cache:
		field = NAME_FIELD.get(doctype)
		title = frappe.db.get_value(doctype, name, field) if field else None
		cache[key] = f"{name} — {title}" if title else name
	return cache[key]


def _price_label(r) -> str:
	text = f"{r.name} · {r.price_source}"
	if r.document_no:
		text += f" {r.document_no}"
	if r.document_date:
		text += f" ngày {getdate(r.document_date).strftime('%d/%m/%Y')}"
	return text


class Context:
	"""Dữ liệu đã nạp của một lần tính."""


def load_context(run, eligible) -> Context:
	ctx = Context()
	ctx.run = run
	ctx.on = getdate(run.costing_date)
	ctx.params = frappe.get_doc("NC Costing Parameter Set", run.parameter_set)
	ctx.pricing = pricing_params(run)
	ctx.job_rates = {r.job_title: r.rate_per_hour for r in ctx.params.job_title_rates}
	ctx.scenario = run.get("volume_scenario") or VOLUME_SCENARIO
	ctx.norm_sets = {
		e["norm_set"]: frappe.get_doc("NC Norm Set", e["norm_set"]) for e in eligible if e["norm_set"]
	}
	for e in eligible:
		for t in e.get("test_systems") or []:
			if t["norm_set"] and t["norm_set"] not in ctx.norm_sets:
				ctx.norm_sets[t["norm_set"]] = frappe.get_doc("NC Norm Set", t["norm_set"])
	_load_cls(ctx, eligible)
	items = {
		ln.resource
		for ns in ctx.norm_sets.values()
		for ln in ns.lines
		if ln.component in ("DRUG", "SUPPLY", "UTILITY") and ln.resource
	} | ctx.cls_items
	ctx.items = {
		r.name: r
		for r in frappe.get_all(
			"NC Item",
			filters={"name": ["in", list(items)]} if items else {"name": ["in", [""]]},
			fields=[
				"name",
				"item_type",
				"uom",
				"norm_units_per_purchase_unit",
				"reuse_count",
				"billed_separately",
				"is_main_reagent",
				"nominal_tests",
				"open_stability_days",
			],
		)
	}
	ctx.prices, ctx.price_labels = {}, {}
	if items:
		for r in frappe.get_all(
			"NC Item Price",
			filters={"item": ["in", list(items)]},
			fields=[
				"name",
				"item",
				"unit_price",
				"price_source",
				"document_no",
				"document_date",
				"valid_from",
				"valid_to",
				"verification_status",
			],
		):
			ctx.prices.setdefault(r.item, []).append(
				pricing.PriceRecord(
					r.name,
					Decimal(str(r.unit_price)),
					r.price_source,
					getdate(r.document_date),
					getdate(r.valid_from),
					getdate(r.valid_to) if r.valid_to else None,
					r.verification_status == "Đã xác minh",
				)
			)
			ctx.price_labels[r.name] = _price_label(r)
	ctx.rooms = {
		r.name: r
		for r in frappe.get_all(
			"NC Room", fields=["name", "annual_infrastructure_cost", "available_hours_per_year"]
		)
	}
	ctx.equipment = {}
	ctx.labels = {}
	ctx.volumes = {
		(r.technical_service, r.department): Decimal(str(r.volume))
		for r in frappe.get_all(
			"NC Service Volume",
			{"fiscal_year": run.fiscal_year, "scenario": ctx.scenario},
			["technical_service", "department", "volume"],
		)
		if r.volume is not None
	}
	return ctx


def _equipment_rate(ctx, code):
	if code not in ctx.equipment:
		if not frappe.db.exists("NC Equipment", code):
			ctx.equipment[code] = None
		else:
			ctx.equipment[code] = frappe.get_doc("NC Equipment", code)
	eq = ctx.equipment[code]
	if eq is None:
		return None
	include = ctx.pricing.include_depreciation
	try:
		hourly = eq.indicative(ctx.on, ctx.params.expired_depreciation_mode, include)["hourly_rate"]
	except ValueError:
		return None
	return rates.equipment_rate(
		hourly, include, eq.acquisition_mode == resources.BUY, f"{code} · {eq.acquisition_mode}"
	)


def _material(ctx, res):
	meta = ctx.items.get(res)
	if not meta:
		return None
	return rates.material_rate(
		ctx.prices.get(res, []),
		ctx.on,
		meta.norm_units_per_purchase_unit or None,
		meta.item_type,
		cint(meta.reuse_count) or 1,
		bool(meta.billed_separately),
		ctx.price_labels,
	)


def _line_rate(ctx, line):
	comp, res = line.component, line.resource
	if not res:
		return None
	if comp == "LABOR":
		r = ctx.job_rates.get(res)
		return rates.labor_rate(r, ctx.params.name) if r else None  # G5: không bịa đơn giá
	if comp in ("DRUG", "SUPPLY"):
		return _material(ctx, res)
	if comp == "UTILITY":
		meta = ctx.items.get(res)
		if not meta:
			return None
		return rates.utility_rate(
			meta.uom,
			ctx.params.electricity_price,
			ctx.params.water_price,
			ctx.params.name,
			_material(ctx, res),
		)
	if comp == "EQUIPMENT":
		return _equipment_rate(ctx, res)
	if comp == "INFRA":
		room = ctx.rooms.get(res)
		if not room:
			return None
		try:
			return rates.room_rate(
				room.annual_infrastructure_cost,
				room.available_hours_per_year,
				ctx.pricing.include_depreciation,
				res,
			)
		except ValueError:
			return None
	return None


def load_service(ctx, e) -> engine.ServiceInput:
	"""Dựng ServiceInput của một cặp đủ điều kiện (ASM-013: authority_qty 0 = chưa có)."""
	if e.get("test_systems"):
		return _load_cls_service(ctx, e)
	ns = ctx.norm_sets[e["norm_set"]]
	lines, rts = [], {}
	for ln in ns.lines:
		lines.append(
			engine.NormLine(
				line_id=ln.line_id,
				step_id="" if cint(ln.service_level) else (ln.step_id or ""),
				component=ln.component,
				resource=ln.resource or "",
				resource_label=_label(ln.resource_doctype, ln.resource, ctx.labels) if ln.resource else "",
				hospital_qty=Decimal(str(ln.hospital_qty or 0)),
				authority_qty=Decimal(str(ln.authority_qty)) if ln.authority_qty else None,
				headcount=cint(ln.headcount) or 1,
				wastage_rate=Decimal(str(flt(ln.wastage_rate))) / 100,
				excluded=bool(ln.is_excluded),
				exclude_reason=ln.exclude_reason,
			)
		)
		rts[ln.line_id] = None if ln.is_excluded else _line_rate(ctx, ln)
	return engine.ServiceInput(
		e["service"],
		e["department"],
		ns.name,
		tuple(lines),
		rts,
		ctx.volumes.get((e["service"], e["department"])),
	)


# ---------------------------------------------------------------------------
# FEAT-036: dữ liệu cận lâm sàng (nạp theo lô) và dựng đầu vào cho costing/cls.py
# ---------------------------------------------------------------------------

_VOLUME_FIELDS = [
	"name",
	"test_system",
	"department",
	"patient_results",
	"iqc_tests",
	"calibration_tests",
	"rerun_tests",
	"eqa_tests",
	"wastage_rate",
	"avg_batch_size",
	"run_days",
]


def _d(x) -> Decimal:
	return Decimal(str(x or 0))


def _dn(x) -> Decimal | None:
	return None if x is None else Decimal(str(x))


def _load_cls(ctx, eligible):
	"""Nạp một lần dữ liệu cho mọi mục cận lâm sàng của lần tính (không truy vấn từng dòng)."""
	ctx.cls_items = set()
	ctx.ts, ctx.ts_vol, ctx.plans, ctx.eqa, ctx.eq_docs = {}, {}, {}, [], {}
	ctx.qtb, ctx.usage, ctx.compliance, ctx.eq_type_required, ctx.svc_group = {}, {}, {}, {}, {}
	entries = [e for e in eligible if e.get("test_systems")]
	if not entries:
		return
	run = ctx.run
	names = sorted({t["test_system"] for e in entries for t in e["test_systems"]})
	all_ts = frappe.get_all(
		"NC Test System",
		fields=[
			"name",
			"technical_service",
			"department",
			"main_equipment",
			"volume_share_pct",
			"est_rerun_rate",
			"est_wastage_rate",
			"machine_minutes_per_case",
		],
	)
	ctx.ts = {r.name: r for r in all_ts if r.name in names}
	main_of = {r.name: (r.main_equipment, r.department) for r in all_ts}
	vols = frappe.get_all(
		"NC Test System Volume",
		{"fiscal_year": run.fiscal_year, "scenario": ctx.scenario},
		_VOLUME_FIELDS,
		order_by="name",
	)
	for v in vols:
		if v.test_system in names:
			ctx.ts_vol[v.test_system] = v
		eq, dept = main_of.get(v.test_system, (None, None))
		if (
			eq and v.patient_results is not None
		):  # Qtb = Σ kết quả các hệ thống cùng máy, cùng khoa (ASM-036-10)
			key = (eq, v.department or dept)
			ctx.qtb[key] = ctx.qtb.get(key, Decimal(0)) + _d(v.patient_results)
	for r in frappe.get_all(
		"NC Equipment Usage",
		{"fiscal_year": run.fiscal_year, "scenario": ctx.scenario},
		["equipment", "department", "total_minutes"],
	):
		ctx.usage[(r.equipment, r.department)] = _dn(r.total_minutes)
	for n in names:
		if frappe.db.exists("NC QC Plan", {"test_system": n}):
			plan = frappe.get_doc("NC QC Plan", {"test_system": n})
			ctx.plans[n] = plan
			ctx.cls_items |= {r.qc_material for r in plan.iqc_lines if r.qc_material}
	ctx.eqa = [
		frappe.get_doc("NC EQA Program", n)
		for n in frappe.get_all("NC EQA Program", pluck="name", order_by="name")
	]
	depts = {e["department"] for e in entries}
	codes = set(frappe.get_all("NC Equipment", {"department": ["in", sorted(depts)]}, pluck="name"))
	for t in ctx.ts.values():
		if t.main_equipment:
			codes.add(t.main_equipment)
	for ns in ctx.norm_sets.values():
		for ln in ns.lines:
			if ln.component == "EQUIPMENT" and ln.resource:
				codes.add(ln.resource)
			if ln.attach_equipment:
				codes.add(ln.attach_equipment)
	for c in sorted(codes):
		if frappe.db.exists("NC Equipment", c):
			doc = frappe.get_doc("NC Equipment", c)
			ctx.eq_docs[c] = doc
			ctx.eq_type_required[c] = (
				cint(frappe.db.get_value("NC Equipment Type", doc.equipment_type, "compliance_required"))
				if doc.equipment_type
				else 0
			)
	for r in frappe.get_all(
		"NC Equipment Compliance",
		{"equipment": ["in", sorted(ctx.eq_docs) or [""]]},
		["equipment", "cost_per_time", "cycle_months", "performed_on", "expiry_date"],
		order_by="name",
	):
		ctx.compliance.setdefault(r.equipment, []).append(r)
	for s in {e["service"] for e in entries}:
		ctx.svc_group[s] = frappe.db.get_value("NC Technical Service", s, "cls_group")


def _equipment_input(ctx, code, dept) -> cls.EquipmentInput:
	doc = ctx.eq_docs[code]
	allocs = [r for r in doc.department_allocations]
	share = Decimal(1)
	if allocs:
		share = sum((_d(r.share_pct) for r in allocs if r.department == dept), Decimal(0)) / 100
	mode = doc.acquisition_mode
	asset = doc.original_cost if mode == resources.BUY else doc.contract_asset_value
	power = None
	if doc.power_kw or doc.power_standby_kw:
		power = cls.PowerInput(
			_d(doc.power_kw),
			_d(doc.run_hours_per_day),
			_d(doc.power_standby_kw),
			_d(doc.standby_hours_per_day),
			bool(doc.continuous_power),
		)
	return cls.EquipmentInput(
		code=code,
		department=doc.department,
		mode=mode,
		basis=doc.allocation_basis,
		original_cost=_dn(doc.original_cost),
		life_years=_dn(doc.useful_life_years),
		in_service=getdate(doc.in_service_date) if doc.in_service_date else None,
		contract_cost=_dn(doc.annual_contract_cost),
		maintenance=_d(doc.annual_maintenance_cost),
		maintenance_vendor_paid=bool(doc.maintenance_vendor_paid),
		components=tuple(
			cls.ComponentInput(_d(c.replacement_cost), c.life_basis, _d(c.life_value), bool(c.vendor_paid))
			for c in doc.components
		),
		dept_share=share,
		asset_value=_dn(asset) if asset else None,
		power=power,
		manual_calibration=_d(doc.annual_calibration_cost),
		records=tuple(
			cls.RecordInput(_d(r.cost_per_time), _d(r.cycle_months), compliance.is_valid_on(r, ctx.on))
			for r in ctx.compliance.get(code, [])
		),
		planned_hours=_dn(doc.planned_hours_per_year),
		utilization=_dn(doc.utilization_rate),
		qtb=ctx.qtb.get((code, dept)),
		mtb=ctx.usage.get((code, dept)),
		compliance_required=bool(ctx.eq_type_required.get(code)),
	)


def _cls_norm_lines(ctx, ns):
	lines, rts = [], {}
	for ln in ns.lines:
		meta = ctx.items.get(ln.resource) if ln.component in ("DRUG", "SUPPLY") else None
		nl = engine.NormLine(
			line_id=ln.line_id,
			step_id="" if cint(ln.service_level) else (ln.step_id or ""),
			component=ln.component,
			resource=ln.resource or "",
			resource_label=_label(ln.resource_doctype, ln.resource, ctx.labels) if ln.resource else "",
			hospital_qty=_d(ln.hospital_qty),
			authority_qty=Decimal(str(ln.authority_qty)) if ln.authority_qty else None,
			headcount=cint(ln.headcount) or 1,
			wastage_rate=Decimal(str(flt(ln.wastage_rate))) / 100,
			excluded=bool(ln.is_excluded),
			exclude_reason=ln.exclude_reason,
		)
		lines.append(
			cls.ClsNormLine(
				nl,
				ln.cost_level or cls.RESULT,
				bool(ln.apply_k),
				ATTACH.get(ln.attach_to, ""),
				ln.attach_equipment or "",
				bool(meta and meta.is_main_reagent),
				_dn(meta.nominal_tests) if meta and meta.is_main_reagent else None,
				_dn(meta.open_stability_days) if meta and meta.is_main_reagent else None,
			)
		)
		rts[ln.line_id] = None if (ln.is_excluded or ln.component == "EQUIPMENT") else _line_rate(ctx, ln)
	return tuple(lines), rts


def _plan_numbers(plan):
	if plan is None:
		return Decimal(0), Decimal(0), None
	iqc, cal = qc_plans.estimated_tests(plan.as_dict())
	return iqc, cal, _dn(plan.run_days_per_year)


def _cls_system(ctx, dept, service, t) -> cls.TestSystemInput:
	ts = ctx.ts[t["test_system"]]
	v = ctx.ts_vol.get(t["test_system"])
	ns = ctx.norm_sets.get(t["norm_set"]) if t["norm_set"] else None
	plan = ctx.plans.get(t["test_system"])
	est_iqc, est_cal, plan_days = _plan_numbers(plan)
	lines, rts = _cls_norm_lines(ctx, ns) if ns is not None else ((), {})
	iqc = tuple(
		cls.IqcLine(
			r.qc_material,
			_d(r.levels),
			_d(r.runs_per_day),
			_d(r.qty_per_run),
			_d(r.shared_parameter_count) or Decimal(1),
			_material(ctx, r.qc_material),
		)
		for r in (plan.iqc_lines if plan else [])
	)
	cal = tuple(
		cls.CalLine(_d(r.points), _d(r.replicates), _d(r.calibrations_per_year), _d(r.cost_per_calibration))
		for r in (plan.calibration_lines if plan else [])
	)
	eqa_tests = sum(
		(
			qc_plans.eqa_samples_per_year(p.rounds_per_year, p.samples_per_round)
			for p in ctx.eqa
			if any(r.technical_service == service for r in p.services)
			and (not p.department or p.department == dept)
		),
		Decimal(0),
	)
	return cls.TestSystemInput(
		code=ts.name,
		norm_set=ns.name if ns is not None else None,
		equipment=ts.main_equipment,
		qbn=_dn(v.patient_results) if v else None,
		has_volume=v is not None,
		actual=cls.AuxCounts(
			_dn(v.iqc_tests) if v else None,
			_dn(v.calibration_tests) if v else None,
			_dn(v.rerun_tests) if v else None,
			_dn(v.eqa_tests) if v else None,
			(_dn(v.wastage_rate) / 100) if v and v.wastage_rate is not None else None,
		),
		est_rerun_rate=_d(ts.est_rerun_rate) / 100,
		est_h=_d(ts.est_wastage_rate) / 100,
		est_qnk=est_iqc,
		est_qcal=est_cal,
		eqa_tests_est=eqa_tests,
		run_days=_dn(v.run_days) if v and v.run_days else None,
		plan_run_days=plan_days,
		batch=_dn(v.avg_batch_size) if v and v.avg_batch_size else None,
		tests_per_tube=_dn(ns.tests_per_tube) if ns is not None and ns.tests_per_tube else None,
		manual_share_pct=_dn(ts.volume_share_pct),
		minutes_per_case=_dn(ts.machine_minutes_per_case) if ts.machine_minutes_per_case else None,
		lines=lines,
		rates=rts,
		iqc=iqc,
		cal=cal,
	)


def _eqa_inputs(ctx, service, dept):
	out = []
	for p in ctx.eqa:
		if p.department and p.department != dept:
			continue  # ASM-036-22
		rows = list(p.services)
		for i, r in enumerate(rows):
			if r.technical_service == service:
				share = qc_plans.eqa_shares([{"share_pct": x.share_pct} for x in rows])[i]
				out.append(cls.EqaInput(p.name, _d(p.annual_fee), _d(p.annual_shipping_fee), share))
	return tuple(out)


def _load_cls_service(ctx, e) -> engine.ServiceInput:
	dept, service = e["department"], e["service"]
	systems = tuple(_cls_system(ctx, dept, service, t) for t in e["test_systems"])
	codes = {c for c, d in ctx.eq_docs.items() if d.department == dept}
	for s in systems:
		codes.add(s.equipment)
		for ln in s.lines:
			if ln.attach_equipment:
				codes.add(ln.attach_equipment)
			if ln.norm.component == "EQUIPMENT" and ln.norm.resource in ctx.eq_docs:
				codes.add(ln.norm.resource)
	params = ctx.params
	inp = cls.ClsServiceInput(
		scenario=ctx.scenario,
		fiscal_year=ctx.run.fiscal_year,
		systems=systems,
		equipment={c: _equipment_input(ctx, c, dept) for c in sorted(codes) if c in ctx.eq_docs},
		eqa=_eqa_inputs(ctx, service, dept),
		allocation_mode=ALLOC_MODE.get(ctx.run.get("compliance_allocation_mode"), cls.ALLOC_ASSET),
		expired_mode=params.expired_depreciation_mode,
		on=ctx.on,
		include_depr=ctx.pricing.include_depreciation,
		electricity_price=_d(params.electricity_price),
		imaging=ctx.svc_group.get(service) == IMAGING_GROUP,
		eqa_category=params.get("eqa_cost_category") or None,
		rental_category=params.get("rental_cost_category") or None,
		jv_category=params.get("jv_cost_category") or None,
	)
	volume = sum((s.qbn for s in systems if s.qbn), Decimal(0))
	return engine.ServiceInput(service, dept, "", (), {}, volume or None, inp)


def run_warnings(ctx, eligible) -> list[str]:
	"""FR-CMP-006 (phần lần tính, AMD-036-01): thiết bị thuộc loại bắt buộc không có hồ sơ còn hạn."""
	codes = sorted(
		{
			ctx.ts[t["test_system"]].main_equipment
			for e in eligible
			for t in e.get("test_systems") or []
			if t["norm_set"] and t["test_system"] in ctx.ts
		}
	)
	equipments = [
		{
			"name": c,
			"compliance_required": ctx.eq_type_required.get(c),
			"type": ctx.eq_docs[c].equipment_type or "",
		}
		for c in codes
		if c in ctx.eq_docs
	]
	records = {
		c: [{"performed_on": r.performed_on, "expiry_date": r.expiry_date} for r in ctx.compliance.get(c, [])]
		for c in codes
	}
	day = ctx.on.strftime("%d/%m/%Y")
	return [
		f"Thiết bị {e['name']} ({e['type'] or '—'}) không có hồ sơ tuân thủ còn hạn tại {day}"
		for e in compliance.missing_required(equipments, records, ctx.on)
	]


def capture_snapshot(run, eligible) -> dict:
	"""FR-COST-011, FR-COST-032: ảnh chụp đầu vào đã phân giải (định mức, đơn giá, tham số, kế toán, phân bổ,
	sản lượng, nguồn cận lâm sàng) và `meta` của lần tính. FEAT-018 gọi khi khóa."""
	ctx = load_context(run, eligible)
	inputs = [load_service(ctx, e) for e in eligible]
	sources = {
		"test_systems": [dict(r) for r in ctx.ts.values()],
		"test_system_volumes": [dict(r) for r in ctx.ts_vol.values()],
		"qc_plans": {k: v.as_dict() for k, v in ctx.plans.items()},
		"eqa_programs": [p.as_dict() for p in ctx.eqa],
		"equipment": {k: v.as_dict() for k, v in ctx.eq_docs.items()},
		"compliance": {k: [dict(r) for r in v] for k, v in ctx.compliance.items()},
		"equipment_usage": {f"{k[0]}|{k[1]}": str(v) for k, v in ctx.usage.items()},
		"qtb": {f"{k[0]}|{k[1]}": str(v) for k, v in ctx.qtb.items()},
		"warnings": run_warnings(ctx, eligible),
	}
	sources = frappe.parse_json(frappe.as_json(sources))
	actx = allocation_context(run, ctx)
	ss, sd = scope_values(run)
	meta = {
		"run": run.name,
		"title": run.title,
		"fiscal_year": run.fiscal_year,
		"costing_date": getdate(run.costing_date),
		"parameter_set": run.parameter_set,
		"accounting_import": run.accounting_import,
		"price_category": run.price_category,
		"scope_services": sorted(ss),
		"scope_departments": sorted(sd),
		"volume_scenario": run.get("volume_scenario"),
		"compliance_allocation_mode": run.get("compliance_allocation_mode"),
	}
	alloc = {"input": actx.input, "dept_center": actx.dept_center, "tolerance": repr(actx.tolerance)}
	return snapshot.build(inputs, ctx.pricing, sources, allocation=alloc, meta=meta)


def eligible_from_results(run) -> list[dict]:
	"""Dựng lại danh sách `eligible` của lần tính đã chạy từ NC Service Cost đã lưu, không gọi `scope_info`
	(phạm vi sống có thể đã đổi, ASM-018-02). Dịch vụ cận lâm sàng có `test_systems` theo `idx`."""
	rows = frappe.get_all(
		"NC Service Cost",
		{"costing_run": run.name},
		["name", "technical_service", "department", "norm_set"],
	)
	systems: dict = {}
	if rows:
		for t in frappe.get_all(
			"NC Test System Cost",
			{"parent": ["in", [r.name for r in rows]], "parenttype": "NC Service Cost"},
			["parent", "test_system", "norm_set"],
			order_by="parent, idx",
		):
			systems.setdefault(t.parent, []).append({"test_system": t.test_system, "norm_set": t.norm_set or ""})
	out = []
	for r in rows:
		e = {"service": r.technical_service, "department": r.department, "norm_set": r.norm_set or ""}
		if r.name in systems:
			e["test_systems"] = systems[r.name]
		out.append(e)
	out.sort(key=lambda e: (e["service"], e["department"], e["norm_set"]))
	return out


def stored_rows(run) -> list[dict]:
	"""Bản ghi phẳng của kết quả và đối soát đã lưu, cùng dạng `writer.expected_rows`."""
	costs = frappe.get_all("NC Service Cost", {"costing_run": run.name}, list(writer.HEADER_FIELDS) + ["name"])
	by_name = {c.name: c for c in costs}
	rows = []
	for c in costs:
		values = {k: c[k] for k in writer.HEADER_FIELDS}
		rows.append(
			{
				"key": ("cost", c.technical_service, c.department),
				"values": writer.canonical("NC Service Cost", values),
			}
		)
	if by_name:
		for dt, kind, fields in (
			(writer.LINE_DT, "line", writer.LINE_FIELDS),
			(writer.SYSTEM_DT, "system", writer.SYSTEM_FIELDS),
		):
			for ch in frappe.get_all(
				dt,
				{"parent": ["in", list(by_name)], "parenttype": "NC Service Cost"},
				["parent", "idx", *fields],
			):
				c = by_name[ch.parent]
				rows.append(
					{
						"key": (kind, c.technical_service, c.department, ch.idx),
						"values": writer.canonical(dt, {k: ch[k] for k in fields}),
					}
				)
	for r in frappe.get_all("NC Reconciliation Line", {"costing_run": run.name}, list(writer.RECON_FIELDS)):
		rows.append(
			{
				"key": ("recon", r.cost_center, r.cost_category),
				"values": writer.canonical(writer.RECON_DT, {k: r[k] for k in writer.RECON_FIELDS}),
			}
		)
	return rows


class AllocCtx:
	"""Dữ liệu phân bổ, đối soát của một lần tính (FEAT-017); đọc một lần."""


def allocation_context(run, ctx) -> AllocCtx:
	"""technical-design 4.1. `drivers` điền dần khi nạp từng dịch vụ, `outcome` do `allocate_pools` đặt."""
	a = AllocCtx()
	totals = frappe.get_all(
		"NC Accounting Import Total",
		{"parent": run.accounting_import, "parenttype": "NC Accounting Import"},
		["cost_center", "cost_category", "amount"],
	)
	accounting = {(r.cost_center, r.cost_category): Decimal(str(r.amount or 0)) for r in totals}
	center_types = {
		r.name: r.center_type for r in frappe.get_all("NC Cost Center", fields=["name", "center_type"])
	}
	a.dept_center = {
		r.name: r.cost_center for r in frappe.get_all("NC Department", fields=["name", "cost_center"])
	}
	center_drivers: dict = {}
	for drv in allocation.CENTER_DRIVERS:
		for center, value in get_driver_values(run.fiscal_year, drv).items():
			center_drivers.setdefault(center, {})[drv] = value
	rules = tuple(
		allocation.Rule(r.name, r.level, r.cost_category, r.driver, r.cost_center or None)
		for r in frappe.get_all(
			"NC Allocation Rule", fields=["name", "level", "cost_category", "driver", "cost_center"]
		)
	)
	a.accounting = accounting
	a.include_depreciation = ctx.pricing.include_depreciation
	a.input = allocation.AllocationInput(
		accounting, center_types, center_drivers, rules, a.include_depreciation
	)
	a.tolerance = flt(ctx.params.reconciliation_tolerance)
	a.drivers = {}
	a.outcome = None
	return a
