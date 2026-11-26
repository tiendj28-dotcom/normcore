"""Trang chủ Normcore: việc chờ xử lý và số dịch vụ theo tình trạng chuỗi (FR-NOTI-003, FR-OUT-010, FEAT-002).

Quyền đọc từng DocType nguồn và phạm vi khoa do `frappe.get_list` áp (ASM-047, ASM-002-07).
"""

import json

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from normcore.core import notify
from normcore.core import permissions as scope
from normcore.procedure import chain

SERVICE = "NC Technical Service"
MAX_SERVICES = 500
SOURCES = {
	"procedure": ("NC Clinical Procedure",),
	"norm_locked": ("NC Norm Set",),
	"costed": ("NC Service Cost", "NC Costing Run"),
}


def _can_read(*doctypes):
	return all(frappe.has_permission(dt, "read") for dt in doctypes)


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Bạn cần đăng nhập"), frappe.PermissionError)


def _scope_departments():
	"""Phạm vi khoa của người bị hẹp theo khoa; None nếu không bị hẹp."""
	for dt in ("NC Clinical Procedure", "NC Norm Set", "NC Service Cost"):
		allowed = scope.readable_departments(dt)
		if allowed is not None:
			return set(allowed)
	return None


def _check_department(department, allowed):
	if not department:
		return
	if not frappe.db.exists("NC Department", department):
		raise frappe.DoesNotExistError(_("Không có khoa {0}").format(department))
	if allowed is not None and department not in allowed:
		frappe.throw(_("Khoa này ngoài phạm vi của bạn"), frappe.PermissionError)


def readable_stages():
	"""Các mức tình trạng chuỗi người gọi có quyền thấy (ASM-047)."""
	out = ["no_procedure"]
	for stage, doctypes in SOURCES.items():
		if _can_read(*doctypes):
			out.append(stage)
	out.append("price_approved")  # R1: luôn 0 (ASM-002-06)
	return tuple(s for s in chain.STAGES if s in out)


def _service_flags(department=None):
	"""[(service, has_procedure, has_norm, has_cost, has_price)] cho dịch vụ đang hoạt động trong phạm vi."""
	if not frappe.has_permission(SERVICE, "read"):
		return []
	allowed = _scope_departments()
	_check_department(department, allowed)
	services = frappe.get_list(SERVICE, {"is_active": 1}, ["name"], limit_page_length=0, pluck="name")
	if not services:
		return []
	by_service = {}
	for row in frappe.get_all(
		"NC Service Department",
		{"parent": ["in", services], "parenttype": SERVICE},
		["parent", "department"],
		limit_page_length=0,
	):
		by_service.setdefault(row.parent, set()).add(row.department)
	limit = {department} if department else allowed
	if limit is not None:
		services = [s for s in services if by_service.get(s, set()) & limit]

	def keep(rows):
		return [r for r in rows if limit is None or r["department"] in limit]

	today = getdate(nowdate())
	has_p, has_n, has_c = {}, {}, {}
	if _can_read(*SOURCES["procedure"]):
		rows = keep(
			frappe.get_list(
				"NC Clinical Procedure",
				{"workflow_state": "Đã ban hành"},
				["technical_service", "department", "version_no", "effective_date"],
				limit_page_length=0,
			)
		)
		for svc, group in _group(rows):
			picked = chain.pick_procedures(group, today)
			has_p[svc] = any(not p["not_effective"] for p in picked.values())
	if _can_read(*SOURCES["norm_locked"]):
		for r in keep(
			frappe.get_list(
				"NC Norm Set", {"status": "Đã khóa"}, ["technical_service", "department"], limit_page_length=0
			)
		):
			has_n[r["technical_service"]] = True
	if _can_read(*SOURCES["costed"]):
		costs = keep(
			frappe.get_list(
				"NC Service Cost",
				fields=["technical_service", "department", "costing_run"],
				limit_page_length=0,
			)
		)
		runs = {}
		if costs:
			fields = ["name", "status", "costing_date", "creation"]
			if frappe.get_meta("NC Costing Run").has_field("based_on_run"):
				fields.append("based_on_run")
			runs = {
				r["name"]: r for r in frappe.get_list("NC Costing Run", fields=fields, limit_page_length=0)
			}
		rows = []
		for c in costs:
			run = runs.get(c["costing_run"])
			if run:
				rows.append(
					{
						**c,
						"name": c["costing_run"],
						"run_status": run["status"],
						"costing_date": run["costing_date"],
						"run_creation": run["creation"],
						"based_on_run": run.get("based_on_run"),
					}
				)
		for svc, group in _group(rows):
			if chain.pick_costs(group):
				has_c[svc] = True
	return [(s, has_p.get(s, False), has_n.get(s, False), has_c.get(s, False), False) for s in services]


def _group(rows):
	grouped = {}
	for r in rows:
		grouped.setdefault(r["technical_service"], []).append(r)
	return grouped.items()


def _flags_by_service(department=None):
	readable = readable_stages()
	out = {}
	for svc, p, n, c, price in _service_flags(department):
		out[svc] = (
			p and "procedure" in readable,
			n and "norm_locked" in readable,
			c and "costed" in readable,
			price and "price_approved" in readable,
		)
	return out


def _stage_by_service(department=None):
	return {svc: chain.stage_of(*flags) for svc, flags in _flags_by_service(department).items()}


def _dots(flags, readable):
	"""Bốn chấm quy trình → định mức → giá thành → giá duyệt (thành phần Thẻ tình trạng chuỗi)."""
	spec = (
		("procedure", "procedure", "green"),
		("norm_set", "norm_locked", "green"),
		("cost", "costed", "blue"),
		("price", "price_approved", "green"),
	)
	dots = []
	for (key, stage, color), has in zip(spec, flags, strict=True):
		if stage not in readable:
			dots.append({"key": key, "state": "no_permission", "indicator": "gray"})
		else:
			dots.append(
				{"key": key, "state": "ok" if has else "empty", "indicator": color if has else "gray"}
			)
	return dots


@frappe.whitelist()
def get_home(department=None):
	"""Việc chờ của người gọi + số dịch vụ theo tình trạng chuỗi trong phạm vi khoa (UC-018)."""
	_require_login()
	department = department or None
	allowed = _scope_departments()
	_check_department(department, allowed)
	if frappe.has_permission(SERVICE, "read"):
		stages = chain.count_stages(_service_flags(department), readable_stages())
		filters = {"name": ["in", list(allowed)]} if allowed is not None else {}
		departments = frappe.get_list(
			"NC Department", filters, ["name", "department_name"], order_by="name", limit_page_length=0
		)
	else:
		stages, departments = [], []
	return {
		"pending": notify.pending_for(frappe.session.user),
		"stages": stages,
		"departments": departments,
		"department": department,
	}


@frappe.whitelist()
def get_service_stages(services):
	"""Mức tình trạng chuỗi từng dịch vụ cho cột SCR-DSK-005 (AMD-004). Dịch vụ không đọc được bị bỏ."""
	_require_login()
	codes = json.loads(services) if isinstance(services, str) else list(services or [])
	if len(codes) > MAX_SERVICES:
		frappe.throw(_("Tối đa {0} dịch vụ mỗi lần").format(MAX_SERVICES), frappe.ValidationError)
	flags = _flags_by_service()
	readable = readable_stages()
	out = {}
	for code in codes:
		if code in flags:
			stage = chain.stage_of(*flags[code])
			out[code] = {
				"stage": stage,
				"label": chain.STAGE_LABELS[stage],
				"dots": _dots(flags[code], readable),
			}
	return out


@frappe.whitelist()
def services_in_stage(stage, department=None):
	"""Mã dịch vụ ở đúng mức `stage` (bộ lọc SCR-DSK-005)."""
	_require_login()
	if stage not in chain.STAGES:
		frappe.throw(_("Mức tình trạng chuỗi không hợp lệ"), frappe.ValidationError)
	if stage not in readable_stages():
		return []
	return sorted(s for s, st in _stage_by_service(department or None).items() if st == stage)
