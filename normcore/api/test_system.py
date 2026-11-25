"""Khối tình trạng hệ thống xét nghiệm và danh sách hệ thống của dịch vụ (FR-CLS-007, SCR-DSK-006, SCR-DSK-032)."""

import frappe
from frappe import _

from normcore.costing import test_systems


def _share_warning_message(service, department, total) -> str:
	total_txt = f"{total:g}"
	return _("Tổng tỷ trọng của dịch vụ {0} tại khoa {1} là {2}%, khác 100%").format(
		service, department, total_txt
	)


def _totals(service, department) -> dict:
	"""Tổng tỷ trọng thật của (dịch vụ, khoa) trên máy chủ, không phụ thuộc phạm vi khoa của người xem."""
	rows = frappe.get_all(
		"NC Test System",
		{"technical_service": service, "department": department},
		["name", "technical_service", "department", "volume_share_pct", "status"],
	)
	return test_systems.share_totals(rows)


def _qc_plan_values(test_system):
	"""Kế hoạch chất lượng của hệ thống (đọc thẳng CSDL: cùng khoa với hệ thống người xem đã được đọc) hoặc None."""
	name = frappe.db.get_value("NC QC Plan", {"test_system": test_system})
	if not name:
		return None
	return {
		"iqc_lines": frappe.get_all(
			"NC QC IQC Line", {"parent": name, "parenttype": "NC QC Plan"}, pluck="name"
		),
		"calibration_lines": frappe.get_all(
			"NC QC Calibration Line", {"parent": name, "parenttype": "NC QC Plan"}, pluck="name"
		),
	}


@frappe.whitelist()
def get_status(test_system: str) -> dict:
	doc = frappe.get_doc("NC Test System", test_system)
	frappe.has_permission("NC Test System", "read", doc=doc, throw=True)
	warnings = []
	if doc.status == test_systems.INACTIVE:
		warnings.append(
			{"code": "inactive", "message": _("Hệ thống đã ngừng dùng: không vào các lần tính giá mới")}
		)
	total = _totals(doc.technical_service, doc.department).get((doc.technical_service, doc.department), 0)
	if test_systems.share_warning(total):
		warnings.append(
			{
				"code": "share_total",
				"message": _share_warning_message(doc.technical_service, doc.department, total),
				"total": float(total),
			}
		)
	plan = _qc_plan_values(doc.name)
	cls_group = frappe.db.get_value("NC Technical Service", doc.technical_service, "cls_group")
	return {
		"test_system": doc.name,
		"status": doc.status,
		"items": [
			{**i, "message": _(i["message"]), "label": _(i["label"])}
			for i in test_systems.status_items(qc_plan=plan, cls_group=cls_group)
		],
		"warnings": warnings,
	}


@frappe.whitelist()
def get_service_systems(service: str) -> dict:
	svc = frappe.get_doc("NC Technical Service", service)
	frappe.has_permission("NC Technical Service", "read", doc=svc, throw=True)
	can_read = frappe.has_permission(
		"NC Test System", "read"
	)  # vai trò không có quyền đọc thì danh sách rỗng
	rows = (
		frappe.get_list(
			"NC Test System",
			{"technical_service": service},
			["name", "department", "main_equipment", "volume_share_pct", "status"],
			order_by="department asc, name asc",
		)
		if can_read
		else []
	)
	equipment_names = {
		e.name: e.equipment_name
		for e in frappe.get_all(
			"NC Equipment",
			{"name": ["in", [r.main_equipment for r in rows] or [""]]},
			["name", "equipment_name"],
		)
	}
	groups = {}
	for r in rows:
		g = groups.setdefault(r.department, [])
		g.append(
			{
				"name": r.name,
				"main_equipment": r.main_equipment,
				"equipment_name": equipment_names.get(r.main_equipment),
				"volume_share_pct": r.volume_share_pct,
				"status": r.status,
			}
		)
	departments = []
	for dept, systems in groups.items():
		total = _totals(service, dept).get((service, dept), 0)
		departments.append(
			{
				"department": dept,
				"department_name": frappe.db.get_value("NC Department", dept, "department_name"),
				"total_share": float(total),
				"warning": test_systems.share_warning(total),
				"systems": systems,
			}
		)
	return {
		"service": service,
		"is_paraclinical": bool(svc.is_paraclinical),
		"can_create": bool(frappe.has_permission("NC Test System", "create")),
		"departments": departments,
	}
