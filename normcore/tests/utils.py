"""Tiện ích dùng chung cho test trên site."""

import frappe

GOLDEN_PARAM = dict(
	base_salary=2500000,
	employer_contribution_rate=23.5,
	working_days_per_year=264,
	working_hours_per_day=8,
)


def make_user(email, *roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.add_roles(*roles)
	return email


def ensure(doctype, name_field, name, **values):
	if frappe.db.exists(doctype, name):
		return frappe.get_doc(doctype, name)
	doc = frappe.get_doc({"doctype": doctype, name_field: name, **values})
	doc.insert(ignore_permissions=True)
	return doc


def make_base(service="DV-TEST-A", department="KHOA-TEST", job="DD"):
	"""Khoa, dịch vụ, chức danh DD dùng chung."""
	ensure(
		"NC Cost Center", "cost_center_code", department, cost_center_name="Khoa thử", center_type="Lâm sàng"
	)
	ensure(
		"NC Department",
		"department_code",
		department,
		department_name="Khoa thử",
		department_type="Lâm sàng",
		cost_center=department,
	)
	ensure("NC Technical Service", "service_code", service, service_name="Dịch vụ thử")
	ensure("NC Job Title", "job_title_code", job, job_title_name="Điều dưỡng", job_group="Điều dưỡng")
	return service, department, job


def make_param_set(job="DD", coef=3.0, allow=0.4):
	ps = frappe.get_doc(
		{
			"doctype": "NC Costing Parameter Set",
			"title": "Bộ tham số vàng",
			"effective_from": "2026-01-01",
			**GOLDEN_PARAM,
			"job_title_rates": [
				{"job_title": job, "salary_coefficient": coef, "allowance_coefficient": allow}
			],
		}
	)
	ps.insert(ignore_permissions=True)
	return ps


def make_procedure(service, department, minutes=10, job="DD", version=1):
	proc = frappe.get_doc(
		{
			"doctype": "NC Clinical Procedure",
			"technical_service": service,
			"department": department,
			"version_no": version,
			"steps": [{"phase": "Thực hiện", "step_title": "Bước 1", "description": "Thực hiện"}],
		}
	)
	proc.insert(ignore_permissions=True)
	proc.append(
		"resources",
		{
			"step_id": proc.steps[0].step_id,
			"resource_type": "Nhân lực",
			"resource_text": "Điều dưỡng",
			"linked_doctype": "NC Job Title",
			"linked_name": job,
			"quantity": minutes,
			"uom": "phút",
			"headcount": 1,
		},
	)
	proc.save(ignore_permissions=True)
	return proc
