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
	return bool(int(value)) if isinstance(value, (int, str)) and str(value).lstrip("-").isdigit() else bool(value)


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
	text = rules._text(d["rule_code"], d["target_ref"], d.get("current_value") or "", d.get("suggested_value") or "")
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
		for s in frappe.get_all("NC Technical Service", {"name": ["in", services or [""]]}, ["name", "service_name"])
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
		counts.setdefault(d.service_cost, {"Mới": 0, "Chấp nhận": 0, "Từ chối": 0})
		if d.status in counts[d.service_cost]:
			counts[d.service_cost][d.status] += 1
	out = []
	for c in costs:
		summary, _sel, _exc = _stats_for(c, prices.get(c.technical_service, []), run_doc, filters, use_adjusted)
		out.append(
			{
				"service_cost": c.name,
				"technical_service": c.technical_service,
				"service_name": names.get(c.technical_service),
				"department": c.department,
				"calculated_price": c.calculated_price,
				**{k: summary[k] for k in ("count", "min", "median", "max", "deviation_pct", "sufficient", "label")},
				"exceeds": stats.exceeds(summary["deviation_pct"], tolerance),
				"suggestion_counts": counts.get(c.name, {"Mới": 0, "Chấp nhận": 0, "Từ chối": 0}),
			}
		)
	out.sort(key=lambda r: (r["deviation_pct"] is None, -abs(r["deviation_pct"] or 0), r["technical_service"]))
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
	sc, run_doc, tolerance, summary, selected, excluded = _detail_base(
		service_cost, provinces, levels, ownerships, use_adjusted
	)
	return {
		"stats": {**summary, "exceeds": stats.exceeds(summary["deviation_pct"], tolerance), "tolerance": tolerance},
		"prices": selected,
		"excluded": excluded,
		"breakdown": stats.breakdown(sc.as_dict()),
		"suggestions": _suggestions(sc.name),
		"can_generate": bool(frappe.has_permission(ADJ, "create")),
		"can_decide": _can_decide(sc),
	}
