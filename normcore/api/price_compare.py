"""API Bàn so sánh giá (FEAT-028, SCR-DSK-026). Logic thuần ở `normcore/benchmark/stats.py`, `rules.py`.

Kiểm quyền tường minh trong từng hàm. Giá tham chiếu lấy qua `api/benchmark.comparable_prices_bulk`
(chỉ dòng "Đã xác nhận", FEAT-026). Giả định ASM-028-01..11 (docs/decisions/assumptions/FEAT-028.md).
"""

from decimal import Decimal

import frappe
from frappe import _

from normcore.api import benchmark as benchmark_api
from normcore.benchmark import rules, stats
from normcore.core import settings

RUN, COST, ADJ = "NC Costing Run", "NC Service Cost", "NC Adjustment Suggestion"
RUN_STATUSES = ("Đã tính", "Đã khóa")
DECIDERS = ("NC Finance", "NC Director", "NC Department Head")  # ASM-028-11


def _list(value):
	if isinstance(value, str):
		value = frappe.parse_json(value) if value.strip() else []
	return list(value or [])


def _flag(value) -> bool:
	return (
		bool(int(value))
		if isinstance(value, (int, str)) and str(value).lstrip("-").isdigit()
		else bool(value)
	)


def _run_info(run_name):
	# Trưởng khoa không có quyền đọc NC Costing Run: quyền xem dựa trên NC Service Cost (phạm vi khoa tự áp)
	frappe.has_permission(COST, "read", throw=True)
	run = frappe.get_doc(RUN, run_name)
	if run.status not in RUN_STATUSES:
		frappe.throw(_("Lần tính chưa có kết quả"))
	tolerance = frappe.db.get_value("NC Costing Parameter Set", run.parameter_set, "comparison_tolerance")
	return run, Decimal(str(tolerance if tolerance is not None else 10))


def _run_view(run, tolerance):
	return {
		"name": run.name,
		"title": run.title,
		"status": run.status,
		"costing_date": run.costing_date,
		"price_category": run.price_category,
		"parameter_set": run.parameter_set,
		"based_on_run": run.get("based_on_run"),
		"tolerance": tolerance,
		"window_months": settings.get("benchmark_window_months"),
		"min_facilities": settings.get("min_benchmark_facilities"),
	}


def _stats_for(sc, rows, run, filters, use_adjusted):
	"""Thống kê một dịch vụ: lọc đơn vị, chọn giá trong cửa sổ, tính (FR-ADJ-001..004)."""
	window, minimum = settings.get("benchmark_window_months"), settings.get("min_benchmark_facilities")
	rows = stats.filter_rows(rows, **filters)
	selected, excluded = stats.select_prices(rows, run.costing_date, window, with_excluded=True)
	summary = stats.summarize(sc["calculated_price"], selected, minimum, use_adjusted)
	return summary, selected, excluded


def _filters(provinces, levels, ownerships):
	return {
		"provinces": _list(provinces),
		"levels": _list(levels),
		"ownerships": _list(ownerships),
	}


def _suggestion_view(d) -> dict:
	text = rules._text(
		d["rule_code"], d["target_ref"], d.get("current_value") or "", d.get("suggested_value") or ""
	)
	return {**d, "text": text}


def _suggestions(service_cost) -> list:
	rows = frappe.get_all(
		ADJ,
		{"service_cost": service_cost},
		[
			"name",
			"rule_code",
			"direction",
			"component",
			"target_ref",
			"current_value",
			"suggested_value",
			"estimated_impact",
			"requires_procedure_change",
			"status",
			"decision_reason",
			"decided_by",
			"decided_on",
		],
	)
	out = [_suggestion_view(r) for r in rows]
	out.sort(
		key=lambda r: (
			r["estimated_impact"] is None,
			-abs(Decimal(str(r["estimated_impact"] or 0))),
			r["rule_code"],
			r["target_ref"],
		)
	)
	return out


def _empty_counts() -> dict:
	return {"Mới": 0, "Chấp nhận": 0, "Từ chối": 0, "Đã chuyển yêu cầu sửa quy trình": 0}


def _is_scenario_cost(sc_doc) -> bool:
	return bool(frappe.db.get_value(RUN, sc_doc.costing_run, "based_on_run"))


def _can_decide(sc_doc) -> bool:
	"""Quyền quyết định gợi ý (ASM-028-11): NC Finance, NC Director, Trưởng khoa của khoa dịch vụ."""
	user = frappe.session.user
	if user == "Administrator":
		return True
	roles = set(frappe.get_roles(user))
	if not roles & set(DECIDERS):
		return False
	return bool(frappe.has_permission(COST, "read", doc=sc_doc))


@frappe.whitelist()
def get_comparison(run, provinces=None, levels=None, ownerships=None, use_adjusted=0):
	"""Danh sách dịch vụ của lần tính với thấp nhất, trung vị, cao nhất, độ lệch (SCR-DSK-026)."""
	run_doc, tolerance = _run_info(run)
	use_adjusted = _flag(use_adjusted)
	filters = _filters(provinces, levels, ownerships)
	costs = frappe.get_list(
		COST,
		{"costing_run": run_doc.name, "calc_status": ["!=", "Lỗi"]},
		["name", "technical_service", "department", "calculated_price"],
		limit_page_length=0,
	)
	services = [c.technical_service for c in costs]
	names = {
		s.name: s.service_name
		for s in frappe.get_all(
			"NC Technical Service", {"name": ["in", services or [""]]}, ["name", "service_name"]
		)
	}
	prices = benchmark_api.comparable_prices_bulk(services, run_doc.price_category, run_doc.costing_date)
	all_rows = [r for rows in prices.values() for r in rows]
	options = {
		"provinces": sorted({r["province"] for r in all_rows if r.get("province")}),
		"levels": sorted({r["facility_level"] for r in all_rows if r.get("facility_level")}),
		"ownerships": sorted({r["ownership"] for r in all_rows if r.get("ownership")}),
	}
	counts = {}
	for d in frappe.get_all(
		ADJ, {"service_cost": ["in", [c.name for c in costs] or [""]]}, ["service_cost", "status"]
	):
		counts.setdefault(d.service_cost, _empty_counts())
		if d.status in counts[d.service_cost]:
			counts[d.service_cost][d.status] += 1
	out = []
	for c in costs:
		summary, _sel, _exc = _stats_for(
			c, prices.get(c.technical_service, []), run_doc, filters, use_adjusted
		)
		out.append(
			{
				"service_cost": c.name,
				"technical_service": c.technical_service,
				"service_name": names.get(c.technical_service),
				"department": c.department,
				"calculated_price": c.calculated_price,
				**{
					k: summary[k]
					for k in ("count", "min", "median", "max", "deviation_pct", "sufficient", "label")
				},
				"exceeds": stats.exceeds(summary["deviation_pct"], tolerance),
				"suggestion_counts": counts.get(c.name, _empty_counts()),
			}
		)
	out.sort(
		key=lambda r: (r["deviation_pct"] is None, -abs(r["deviation_pct"] or 0), r["technical_service"])
	)
	return {"run": _run_view(run_doc, tolerance), "filter_options": options, "rows": out}


def _detail_base(service_cost, provinces, levels, ownerships, use_adjusted):
	sc = frappe.get_doc(COST, service_cost)
	frappe.has_permission(COST, "read", doc=sc, throw=True)
	run_doc, tolerance = _run_info(sc.costing_run)
	use_adjusted = _flag(use_adjusted)
	filters = _filters(provinces, levels, ownerships)
	rows = benchmark_api.comparable_prices_bulk(
		[sc.technical_service], run_doc.price_category, run_doc.costing_date
	).get(sc.technical_service, [])
	summary, selected, excluded = _stats_for(sc.as_dict(), rows, run_doc, filters, use_adjusted)
	return sc, run_doc, tolerance, summary, selected, excluded


@frappe.whitelist()
def get_service_detail(service_cost, provinces=None, levels=None, ownerships=None, use_adjusted=0):
	"""Chi tiết một dịch vụ: giá tham chiếu, giá bị loại, cơ cấu giá, gợi ý (FR-ADJ-001, 010)."""
	sc, _run_doc, tolerance, summary, selected, excluded = _detail_base(
		service_cost, provinces, levels, ownerships, use_adjusted
	)
	is_scenario = _is_scenario_cost(sc)
	suggestions = _suggestions(sc.name)
	requests = {
		r.source_suggestion: r.name
		for r in frappe.get_all(
			"NC Procedure Change Request",
			{"source_suggestion": ["in", [x["name"] for x in suggestions] or [""]]},
			["name", "source_suggestion"],
		)
	}
	for x in suggestions:
		x["change_request"] = requests.get(x["name"])
	return {
		"stats": {
			**summary,
			"exceeds": stats.exceeds(summary["deviation_pct"], tolerance),
			"tolerance": tolerance,
		},
		"prices": selected,
		"excluded": excluded,
		"breakdown": stats.breakdown(sc.as_dict()),
		"suggestions": suggestions,
		"is_scenario": is_scenario,
		"can_generate": bool(frappe.has_permission(ADJ, "create")) and not is_scenario,
		"can_decide": _can_decide(sc) and not is_scenario,
		"can_request_change": _can_decide(sc) and not is_scenario,
	}


# --- gợi ý điều chỉnh (FR-ADJ-005, 008) ------------------------------------------------


def _time_study_medians(technical_service, department):
	"""ASM-028-08: trung vị bấm giờ của quy trình đã ban hành, chỉ khi đủ `min_time_study_cases` ca."""
	from normcore.norm import time_study

	procedure = frappe.db.get_value(
		"NC Clinical Procedure",
		{"technical_service": technical_service, "department": department, "workflow_state": "Đã ban hành"},
		"name",
		order_by="version_no desc",
	)
	if not procedure:
		return {}
	heads = frappe.get_all(
		"NC Time Study",
		{"technical_service": technical_service, "department": department, "procedure": procedure},
		["name", "observed_on"],
		order_by="observed_on asc, name asc",
	)
	if not heads:
		return {}
	lines = frappe.get_all(
		"NC Time Study Line",
		{"parent": ["in", [h.name for h in heads]], "parenttype": "NC Time Study"},
		["parent", "step_id", "job_title", "headcount", "labor_minutes", "equipment", "machine_minutes"],
		order_by="idx asc",
	)
	by_parent = {}
	for ln in lines:
		by_parent.setdefault(ln.parent, []).append(ln)
	cases = [{"observed_on": h.observed_on, "lines": by_parent.get(h.name, [])} for h in heads]
	summary = time_study.summarize(cases, settings.get("min_time_study_cases"), {})
	if not summary["sufficient"]:
		return {}
	return {
		(r["step_id"], r["resource"]): Decimal(str(r["median_minutes"]))
		for r in summary["rows"]
		if r["kind"] == "labor"
	}


def _price_records(items):
	from frappe.utils import getdate

	from normcore.costing import pricing

	out = {}
	for r in frappe.get_all(
		"NC Item Price",
		{"item": ["in", list(items) or [""]]},
		[
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
		out.setdefault(r.item, []).append(
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
	return out


def _equipment_facts(codes, run):
	from frappe.utils import getdate

	from normcore.costing import resources
	from normcore.nc_costing.doctype.nc_costing_run import loader

	include = loader.pricing_params(run).include_depreciation
	mode = frappe.db.get_value("NC Costing Parameter Set", run.parameter_set, "expired_depreciation_mode")
	out = {}
	for code in codes:
		if not frappe.db.exists("NC Equipment", code):
			continue
		eq = frappe.get_doc("NC Equipment", code)
		if eq.allocation_basis != resources.BASIS_HOURS:
			continue
		try:
			annual = eq.indicative(getdate(run.costing_date), mode, include)["annual_equipment_cost"]
		except ValueError:
			continue
		out[code] = {
			"annual_cost": Decimal(str(annual)),
			"planned_hours": Decimal(str(eq.planned_hours_per_year or 0)),
			"utilization": Decimal(str(eq.utilization_rate or 0)),
			"maintenance": Decimal(str(eq.annual_maintenance_cost or 0)),
		}
	return {c: v for c, v in out.items() if v["planned_hours"] > 0 and v["utilization"] > 0}


def _material_facts(norm_lines, rates, run):
	"""Mặt hàng tương đương rẻ hơn (BR-ADJ-003) và đơn giá cũ (BR-ADJ-007), theo dòng định mức."""
	from frappe.utils import cint, getdate

	from normcore.costing import pricing
	from normcore.costing import rates as costing_rates

	as_of = getdate(run.costing_date)
	lines = [
		ln
		for ln in norm_lines
		if ln.component in ("DRUG", "SUPPLY", "UTILITY") and ln.resource and not ln.excluded
	]
	items = {
		i.name: i
		for i in frappe.get_all(
			"NC Item",
			{"name": ["in", [ln.resource for ln in lines] or [""]]},
			["name", "equivalent_group"],
		)
	}
	groups = {i.equivalent_group for i in items.values() if i.equivalent_group}
	candidates = {}
	if groups:
		for c in frappe.get_all(
			"NC Item",
			{"equivalent_group": ["in", list(groups)], "is_active": 1},
			[
				"name",
				"equivalent_group",
				"item_type",
				"norm_units_per_purchase_unit",
				"reuse_count",
				"billed_separately",
			],
		):
			candidates.setdefault(c.equivalent_group, []).append(c)
	prices = _price_records(
		{ln.resource for ln in lines} | {c.name for cs in candidates.values() for c in cs}
	)
	stale, equivalents = {}, {}
	for ln in lines:
		chosen = pricing.select_price(prices.get(ln.resource, []), as_of)
		if chosen:
			stale[ln.line_id] = {"item": ln.resource, "valid_from": chosen.valid_from}
		group = items.get(ln.resource) and items[ln.resource].equivalent_group
		if ln.component == "UTILITY" or not group:
			continue
		options = []
		for c in candidates.get(group, []):
			if c.name == ln.resource:
				continue
			r = costing_rates.material_rate(
				prices.get(c.name, []),
				as_of,
				c.norm_units_per_purchase_unit or None,
				c.item_type,
				cint(c.reuse_count) or 1,
				bool(c.billed_separately),
				{},
			)
			if r is not None and not r.billed_separately:
				options.append((c.name, r))
		if options:
			equivalents[ln.line_id] = options
	return stale, equivalents


def _facts(sc, run) -> rules.ServiceFacts:
	"""Dữ kiện của quy tắc cho một kết quả dịch vụ (ASM-028-08). Chỉ đọc."""
	from frappe.utils import getdate

	from normcore.api import costing as costing_api
	from normcore.nc_costing.doctype.nc_costing_run import loader

	inp = costing_api._input_of(costing_api._snapshot_for(run), sc.technical_service, sc.department)
	pricing_params = loader.pricing_params(run)
	alloc_fields = (
		"alloc_labor",
		"alloc_drug_supply",
		"alloc_depreciation",
		"alloc_utility",
		"alloc_management",
	)
	alloc = {f: Decimal(str(sc.get(f) or 0)) for f in alloc_fields}
	direct_total = Decimal(str(sc.full_cost or 0)) - sum(alloc.values(), Decimal(0))
	norm_lines = tuple(inp.lines)
	rates_by_line = {k: v for k, v in inp.rates.items() if v is not None}
	norm_lines = tuple(ln for ln in norm_lines if ln.line_id in rates_by_line or ln.excluded)
	stale, equivalents = _material_facts(norm_lines, rates_by_line, run)
	params = frappe.db.get_value(
		"NC Costing Parameter Set", run.parameter_set, ["wastage_cap", "effective_from"], as_dict=True
	)
	latest = frappe.get_all(
		"NC Costing Parameter Set",
		{"effective_from": ["<=", getdate(run.costing_date)]},
		["name", "effective_from"],
		order_by="effective_from desc, name desc",
		limit=1,
	)
	return rules.ServiceFacts(
		direct_total=direct_total,
		alloc_by_category=alloc,
		pricing=pricing_params,
		norm_lines=norm_lines,
		line_rates=rates_by_line,
		costing_date=run.costing_date,
		price_valid_months=settings.get("price_valid_months"),
		equipment=_equipment_facts({ln.resource for ln in norm_lines if ln.component == "EQUIPMENT"}, run),
		time_study=_time_study_medians(sc.technical_service, sc.department),
		wastage_cap=Decimal(str(params.wastage_cap or 0)) / 100,
		equivalents=equivalents,
		stale_prices=stale,
		latest_parameter_set=latest[0].name if latest else None,
		parameter_set=run.parameter_set,
	)


@frappe.whitelist()
def generate_suggestions(service_cost, provinces=None, levels=None, ownerships=None, use_adjusted=0):
	"""FR-ADJ-005: sinh gợi ý bằng quy tắc, lưu NC Adjustment Suggestion. Chưa đủ dữ liệu/trong ngưỡng: `[]`."""
	if not frappe.has_permission(ADJ, "create"):
		frappe.throw(_("Bạn không có quyền sinh gợi ý điều chỉnh"), frappe.PermissionError)
	sc, run_doc, tolerance, summary, _sel, _exc = _detail_base(
		service_cost, provinces, levels, ownerships, use_adjusted
	)
	if run_doc.based_on_run:
		frappe.throw(_("Kịch bản không sinh gợi ý; mở lần tính gốc"))
	found = rules.generate(_facts(sc, run_doc), summary["deviation_pct"], tolerance)
	existing = {
		(d.rule_code, d.target_ref): d
		for d in frappe.get_all(ADJ, {"service_cost": sc.name}, ["name", "rule_code", "target_ref", "status"])
	}
	keep = set()
	for s in found:
		key = (s.rule_code, s.target_ref)
		prior = existing.get(key)
		if prior and prior.status != "Mới":
			keep.add(key)  # bản đã quyết giữ nguyên, không tạo thêm (ASM-028-09)
			continue
		values = {
			"direction": s.direction,
			"component": s.component,
			"current_value": s.current_value,
			"suggested_value": s.suggested_value,
			"estimated_impact": s.estimated_impact,
			"requires_procedure_change": 1 if s.requires_procedure_change else 0,
		}
		if prior:
			doc = frappe.get_doc(ADJ, prior.name)
			doc.update(values)
		else:
			doc = frappe.get_doc(
				{
					"doctype": ADJ,
					"service_cost": sc.name,
					"rule_code": s.rule_code,
					"target_ref": s.target_ref,
					"status": "Mới",
					**values,
				}
			)
		doc.flags.adj_system = True
		doc.save(ignore_permissions=True)
		keep.add(key)
	for key, prior in existing.items():
		if key not in keep and prior.status == "Mới":
			frappe.delete_doc(ADJ, prior.name, ignore_permissions=True, force=True)
	return _suggestions(sc.name)


@frappe.whitelist()
def decide_suggestion(name, decision, reason=None):
	"""FR-ADJ-008, UC-014 4a: Chấp nhận / Từ chối một gợi ý "Mới" (ASM-028-09, 11)."""
	if decision not in ("Chấp nhận", "Từ chối"):
		frappe.throw(_("Quyết định phải là Chấp nhận hoặc Từ chối"))
	doc = frappe.get_doc(ADJ, name)
	sc = frappe.get_doc(COST, doc.service_cost)
	if not _can_decide(sc):
		frappe.throw(_("Bạn không có quyền quyết định gợi ý này"), frappe.PermissionError)
	if doc.status != "Mới":
		frappe.throw(_("Gợi ý đã có quyết định"))
	reason = (reason or "").strip()
	if decision == "Từ chối" and not reason:
		frappe.throw(_("Từ chối gợi ý phải nêu lý do"))
	if decision == "Chấp nhận" and doc.requires_procedure_change:
		frappe.throw(_("Gợi ý cần sửa quy trình, không áp trực tiếp được: dùng Chuyển yêu cầu sửa quy trình"))
	if decision == "Chấp nhận":  # FR-ADJ-006: mọi đường chấp nhận đều ghi vào kịch bản (ASM-029-09)
		from normcore.api import scenario

		scenario._accept(doc, sc, reason)
		return _suggestion_view(frappe.get_doc(ADJ, name).as_dict())
	doc.status = decision
	doc.decision_reason = reason or None
	doc.decided_by = frappe.session.user
	doc.decided_on = frappe.utils.now_datetime()
	doc.flags.adj_decision = True
	doc.save(ignore_permissions=True)
	return _suggestion_view(doc.as_dict())
