"""Lớp đọc CSDL của lần tính giá (AMD-015-02): đọc DocType rồi dựng dữ liệu cho `normcore.costing`.

Nạp một lần theo lô (đơn giá, mặt hàng, thiết bị, phòng, sản lượng), không truy vấn từng dòng (technical-design 4.4).
"""

from decimal import Decimal

import frappe
from frappe.utils import cint, flt, getdate

from normcore.costing import engine, pricing, rates, resources, runner, test_systems

LOCKED_NORM = "Đã khóa"
VOLUME_SCENARIO = "Thực tế 12 tháng"
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
	pairs |= {(n["technical_service"], n["department"]) for n in norm_sets}
	pairs = runner.scope_pairs(pairs, ss, sd)
	locked = {}
	for n in norm_sets:
		locked.setdefault((n["technical_service"], n["department"]), n["name"])
	_, ineligible = runner.eligibility(pairs, locked, ss, sd)
	in_scope = set(pairs)
	eligible = [
		{"service": n["technical_service"], "department": n["department"], "norm_set": n["name"]}
		for n in norm_sets
		if (n["technical_service"], n["department"]) in in_scope
	]
	eligible.sort(key=lambda e: (e["service"], e["department"], e["norm_set"]))
	return {"eligible": eligible, "ineligible": ineligible}


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
	ctx.norm_sets = {e["norm_set"]: frappe.get_doc("NC Norm Set", e["norm_set"]) for e in eligible}
	items = {
		ln.resource
		for ns in ctx.norm_sets.values()
		for ln in ns.lines
		if ln.component in ("DRUG", "SUPPLY", "UTILITY") and ln.resource
	}
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
			{"fiscal_year": run.fiscal_year, "scenario": VOLUME_SCENARIO},
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
