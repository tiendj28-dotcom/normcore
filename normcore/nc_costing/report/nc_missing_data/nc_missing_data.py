"""Script Report SCR-DSK-039 "Báo cáo thiếu dữ liệu" (FEAT-037; FR-OUT-012, UC-024).

Chạy được trước khi có lần tính giá: dựng NC Costing Run tạm (không lưu) từ bộ lọc rồi dùng lại `loader`.
Chỉ đọc. Quy tắc thiếu ở `normcore.costing.missing_data` (thuần)."""

import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate

from normcore.costing import compliance, engine, missing_data
from normcore.nc_costing.doctype.nc_costing_run import loader

ROLES = ("NC Finance", "NC Director", "NC Admin", "NC Auditor", "NC Department Head")
FULL_SCOPE_ROLES = ("NC Finance", "NC Director", "NC Admin", "NC Auditor", "System Manager", "Administrator")
IMAGING = "Chẩn đoán hình ảnh"
TIMED = "Bấm giờ"


def _columns():
	return [
		{"fieldname": "service_label", "label": _("Service"), "fieldtype": "Data", "width": 260},
		{"fieldname": "department_label", "label": _("Department"), "fieldtype": "Data", "width": 200},
		{"fieldname": "kind", "label": _("Missing"), "fieldtype": "Data", "width": 200},
		{"fieldname": "detail", "label": _("Detail"), "fieldtype": "Data", "width": 320},
	]


def _allowed_departments(user=None):
	"""None = mọi khoa; không thì tập khoa được phân (NC Department Head, ASM-037-13)."""
	roles = set(frappe.get_roles(user))
	if roles & set(FULL_SCOPE_ROLES):
		return None
	perms = frappe.permissions.get_user_permissions(user or frappe.session.user) or {}
	return {p["doc"] for p in perms.get("NC Department", [])}


def _temp_run(filters, departments):
	run = frappe.new_doc("NC Costing Run")
	run.fiscal_year = cint(filters.get("fiscal_year"))
	run.costing_date = filters.get("costing_date") or nowdate()
	run.parameter_set = filters.get("parameter_set")
	run.price_category = filters.get("price_category")
	run.volume_scenario = filters.get("volume_scenario") or loader.VOLUME_SCENARIO
	run.compliance_allocation_mode = filters.get("compliance_allocation_mode") or "Theo giá trị tài sản"
	for d in departments:
		run.append("scope_departments", {"department": d})
	if filters.get("technical_service"):
		run.append("scope_services", {"technical_service": filters.get("technical_service")})
	return run


def _equipment_codes(ctx, e):
	codes = set()
	sets = [e["norm_set"]] if e.get("norm_set") else []
	sets += [t["norm_set"] for t in e.get("test_systems") or [] if t.get("norm_set")]
	for n in sets:
		for ln in ctx.norm_sets[n].lines:
			if ln.component == "EQUIPMENT" and ln.resource:
				codes.add(ln.resource)
			if ln.get("attach_equipment"):
				codes.add(ln.attach_equipment)
	for t in e.get("test_systems") or []:
		ts = ctx.ts.get(t["test_system"])
		if ts and ts.main_equipment:
			codes.add(ts.main_equipment)
	return codes


def _compliance_data(all_codes):
	rows = frappe.get_all(
		"NC Equipment",
		{"name": ["in", sorted(all_codes) or [""]]},
		["name", "equipment_type"],
	)
	types = {
		r.name: cint(r.compliance_required)
		for r in frappe.get_all("NC Equipment Type", fields=["name", "compliance_required"])
	}
	eq = {r.name: {"name": r.name, "type": r.equipment_type, "compliance_required": types.get(r.equipment_type, 0)} for r in rows}
	recs: dict = {}
	for r in frappe.get_all(
		"NC Equipment Compliance",
		{"equipment": ["in", sorted(eq) or [""]]},
		["equipment", "performed_on", "expiry_date"],
	):
		if r.performed_on and r.expiry_date:
			recs.setdefault(r.equipment, []).append({"performed_on": r.performed_on, "expiry_date": r.expiry_date})
	return eq, recs


def collect(filters):
	"""(danh sách Gap, số cặp chưa đủ điều kiện, số cặp đã kiểm). Chỉ đọc."""
	allowed = _allowed_departments()
	wanted = {filters.get("department")} if filters.get("department") else set()
	if allowed is None:
		departments = sorted(wanted)
	else:
		departments = sorted((wanted & allowed) if wanted else allowed)
		if not departments:
			return [], 0, 0
	run = _temp_run(filters, departments)
	info = loader.scope_info(run)
	eligible = info["eligible"]
	ctx = loader.load_context(run, eligible)
	on = getdate(run.costing_date)
	studied = {(r.technical_service, r.department) for r in frappe.get_all("NC Time Study", fields=["technical_service", "department"])}
	codes = {c for e in eligible for c in _equipment_codes(ctx, e)}
	eq_docs, eq_records = _compliance_data(codes)
	pairs = []
	for e in eligible:
		key = (e["service"], e["department"])
		try:
			inp = loader.load_service(ctx, e)
		except (KeyError, ValueError, ZeroDivisionError):
			inp = None
		sets = [e["norm_set"]] if e.get("norm_set") else []
		sets += [t["norm_set"] for t in e.get("test_systems") or [] if t.get("norm_set")]
		basis = {
			ln.line_id: ln.basis
			for n in sets
			for ln in ctx.norm_sets[n].lines
			if ln.component == "LABOR" and not ln.is_excluded
		}
		no_plan, no_vol = [], []
		for t in e.get("test_systems") or []:
			name = t["test_system"]
			if name not in ctx.plans:
				no_plan.append(name)
			v = ctx.ts_vol.get(name)
			if v is None or not v.patient_results or v.patient_results <= 0:
				no_vol.append(name)
		used = [eq_docs[c] for c in sorted(_equipment_codes(ctx, e)) if c in eq_docs]
		lacking = compliance.missing_required(used, eq_records, on)
		pairs.append(
			missing_data.PairData(
				e["service"],
				e["department"],
				inp,
				basis,
				key in studied,
				tuple(no_plan),
				tuple(no_vol),
				tuple((x["name"], x.get("type") or "") for x in lacking),
				ctx.svc_group.get(e["service"]) == IMAGING,
				ctx.scenario,
			)
		)
	return missing_data.collect(pairs), len(info["ineligible"]), len(pairs)


def execute(filters=None):
	if not set(frappe.get_roles()) & {*ROLES, "System Manager"}:  # `frappe.only_for` bỏ qua khi chạy test
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	filters = frappe._dict(filters or {})
	if not (filters.get("fiscal_year") and filters.get("parameter_set") and filters.get("price_category")):
		return _columns(), [], None, None, []
	gaps, skipped, scanned = collect(filters)
	names = {r.name: r.service_name for r in frappe.get_all("NC Technical Service", {"name": ["in", sorted({g.service for g in gaps}) or [""]]}, ["name", "service_name"])}
	depts = {r.name: r.department_name for r in frappe.get_all("NC Department", {"name": ["in", sorted({g.department for g in gaps}) or [""]]}, ["name", "department_name"])}
	rows = [
		{
			"service": g.service,
			"service_label": f"{g.service} · {names.get(g.service) or ''}".strip(" ·"),
			"department": g.department,
			"department_label": f"{g.department} · {depts.get(g.department) or ''}".strip(" ·"),
			"kind": g.kind,
			"detail": g.detail,
		}
		for g in gaps
	]
	if filters.get("kind"):
		rows = [r for r in rows if r["kind"] == filters.kind]
	summary = [
		{"label": k, "value": sum(1 for g in gaps if g.kind == k), "indicator": "red" if any(g.kind == k for g in gaps) else "green", "datatype": "Int"}
		for k in missing_data.KINDS
	]
	message = (
		_("Nothing is missing in this scope ({0} service-department pairs checked).").format(scanned)
		if not gaps
		else None
	)
	if skipped:
		note = _("{0} service-department pairs have no locked norm set and are not checked.").format(skipped)
		message = f"{message} {note}" if message else note
	return _columns(), rows, message, None, summary
