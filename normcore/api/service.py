"""API tình trạng chuỗi của dịch vụ kỹ thuật (FR-SVC-004, FR-ACC-005; ASM-047, 048, 054, 055).

Chỉ đọc. Truy vấn bằng `frappe.get_list` (có quyền và phạm vi khoa); không chọn trường tiền.
Mục không có quyền đọc ở mức vai trò thì không truy vấn bản ghi của mục.
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from normcore.core.permissions import readable_departments
from normcore.procedure import chain

SERVICE = "NC Technical Service"


def _can_read(*doctypes):
	return all(frappe.has_permission(dt, "read") for dt in doctypes)


def _procedure_rows(service):
	return frappe.get_list(
		"NC Clinical Procedure",
		filters={"technical_service": service, "workflow_state": "Đã ban hành"},
		fields=["name", "department", "version_no", "effective_date"],
		limit_page_length=0,
	)


def _norm_rows(service):
	return frappe.get_list(
		"NC Norm Set",
		filters={"technical_service": service, "status": "Đã khóa"},
		fields=["name", "department", "version_no", "locked_on"],
		limit_page_length=0,
	)


def _cost_rows(service):
	costs = frappe.get_list(
		"NC Service Cost",
		filters={"technical_service": service},
		fields=["name", "department", "costing_run", "calc_status"],
		limit_page_length=0,
	)
	if not costs:
		return []
	fields = ["name", "status", "costing_date", "creation"]
	if frappe.get_meta("NC Costing Run").has_field("based_on_run"):  # chưa có (ASM-004)
		fields.append("based_on_run")
	runs = {
		r["name"]: r
		for r in frappe.get_list(
			"NC Costing Run",
			filters={"name": ["in", list({c["costing_run"] for c in costs})]},
			fields=fields,
			limit_page_length=0,
		)
	}
	rows = []
	for c in costs:
		run = runs.get(c["costing_run"])
		if run:
			rows.append(
				{
					**c,
					"run_status": run["status"],
					"costing_date": run["costing_date"],
					"run_creation": run["creation"],
					"based_on_run": run.get("based_on_run"),
				}
			)
	return rows


def _department_names(codes):
	if not codes:
		return {}
	return dict(
		frappe.db.get_values("NC Department", {"name": ["in", list(codes)]}, ["name", "department_name"])
	)


@frappe.whitelist()
def get_chain_status(service):
	if not frappe.has_permission(SERVICE, "read"):
		frappe.throw(_("Bạn không có quyền xem dịch vụ kỹ thuật"), frappe.PermissionError)
	if not frappe.db.exists(SERVICE, service):
		raise frappe.DoesNotExistError(_("Không có dịch vụ {0}").format(service))
	doc = frappe.get_doc(SERVICE, service)
	doc.check_permission("read")

	today = getdate(nowdate())
	procs = (
		chain.pick_procedures(_procedure_rows(service), today) if _can_read("NC Clinical Procedure") else None
	)
	norm_allowed = readable_departments("NC Norm Set")
	norms = chain.pick_norm_sets(_norm_rows(service)) if _can_read("NC Norm Set") else None
	costs = chain.pick_costs(_cost_rows(service)) if _can_read("NC Service Cost", "NC Costing Run") else None

	departments = [r.department for r in doc.departments]
	extra = set()
	for picked in (procs, norms, costs):
		extra |= set(picked or {})
	departments += sorted(extra - set(departments))
	names = _department_names(departments)

	items = []
	for key, picked, allowed in (
		("procedure", procs, None),
		("norm_set", norms, norm_allowed),
		("cost", costs, None),
	):
		if picked is None:
			items.append(chain.no_permission_item(key))
		else:
			items.append(chain.build_item(key, departments, picked, allowed, names))
	items.append(chain.price_item())
	return {"service": service, "items": items}
