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
	# Fixture của test cũ tạo nhiều bản nháp cùng (dịch vụ, khoa); DI-02 có test riêng nên bỏ qua ở đây.
	proc.flags.ignore_single_active = True
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


def make_chain_data(service, department, job="DD"):
	"""Quy trình ban hành, bộ định mức khóa và lần tính "Đã tính" của một (dịch vụ, khoa) — cho test FEAT-005."""
	from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set

	proc = make_procedure(service, department, job=job)
	proc.workflow_state = "Đã ban hành"
	proc.decision_no = "QĐ-CH"
	proc.effective_date = "2026-01-01"
	proc.flags.allow_publish = True
	proc.save(ignore_permissions=True)
	ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
	ns.status = "Đã khóa"
	ns.flags.allow_lock = True
	ns.save(ignore_permissions=True)
	run = frappe.get_doc(
		{
			"doctype": "NC Costing Run",
			"title": "Lần tính chuỗi",
			"fiscal_year": 2026,
			"costing_date": "2026-10-01",
			"parameter_set": make_param_set(job=job).name,
			"status": "Đã tính",
		}
	)
	run.insert(ignore_permissions=True)
	cost = frappe.get_doc(
		{
			"doctype": "NC Service Cost",
			"costing_run": run.name,
			"technical_service": service,
			"department": department,
			"norm_set": ns.name,
			"calc_status": "Thành công",
		}
	)
	cost.insert(ignore_permissions=True)
	return frappe._dict(procedure=proc.name, norm_set=ns.name, cost=cost.name, run=run.name)


def make_equipment(code="TB-HS01", department=None, equipment_type=None, **values):
	"""Thiết bị tối thiểu cho test hồ sơ tuân thủ (FEAT-033)."""
	if department is None:
		_, department, _ = make_base()
	data = dict(
		equipment_name="Thiết bị thử",
		acquisition_mode="Mua",
		allocation_basis="Giờ kế hoạch",
		original_cost=1200000000,
		useful_life_years=8,
		in_service_date="2022-01-01",
		funding_source="Ngân sách",
		planned_hours_per_year=2112,
		utilization_rate=0.5,
	)
	if equipment_type:
		data["equipment_type"] = equipment_type
	data.update(values)
	return ensure("NC Equipment", "equipment_code", code, department=department, **data)


def make_private_file(name="chung-tu.txt"):
	"""Tệp private đã tải lên; trả đường dẫn /private/files/…"""
	file_url = f"/private/files/{name}"
	if not frappe.db.exists("File", {"file_url": file_url}):
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": name,
				"is_private": 1,
				"content": b"chung tu thu",
			}
		).insert(ignore_permissions=True)
	return frappe.db.get_value("File", {"file_name": name, "is_private": 1}, "file_url")


def make_cls_data(department="HS-CLS", service="GLU"):
	"""FEAT-031: khoa Hóa sinh, dịch vụ cận lâm sàng GLU, thiết bị EQ_A (Mua) và EQ_B (Đặt theo hóa chất), cùng tiêu chí Số kết quả."""
	_, dept, _ = make_base(department=department)
	frappe.db.set_value(
		"NC Technical Service",
		ensure_service(service),
		{"is_paraclinical": 1, "cls_group": "Hóa sinh", "result_unit": "Kết quả xét nghiệm"},
	)
	eqs = []
	for code, mode in (("EQ_A", "Mua"), ("EQ_B", "Đặt theo hóa chất")):
		ensure(
			"NC Equipment",
			"equipment_code",
			code,
			equipment_name=f"Máy {code}",
			department=dept,
			acquisition_mode=mode,
			allocation_basis="Số kết quả",
			original_cost=1200000000,
			useful_life_years=8,
			in_service_date="2022-01-01",
			funding_source="Ngân sách",
			planned_hours_per_year=2112,
			utilization_rate=0.5,
		)
		eqs.append(code)
	return service, dept, eqs


def ensure_service(code):
	ensure("NC Technical Service", "service_code", code, service_name=f"Dịch vụ {code}")
	return code


def make_test_system(code, service, department, equipment, share, **kw):
	doc = frappe.get_doc(
		{
			"doctype": "NC Test System",
			"test_system_code": code,
			"technical_service": service,
			"department": department,
			"main_equipment": equipment,
			"volume_share_pct": share,
			**kw,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def make_qc_items():
	"""FEAT-032: QC_L (Vật liệu nội kiểm), CAL (Chất chuẩn), HC_GLU (Hóa chất)."""
	for code, typ in (("QC_L", "Vật liệu nội kiểm"), ("CAL", "Chất chuẩn"), ("HC_GLU", "Hóa chất")):
		ensure("NC Item", "item_code", code, item_name=f"Mặt hàng {code}", item_type=typ, uom="ml", norm_units_per_purchase_unit=100)


def qc_plan_values(test_system, **kw):
	"""Kế hoạch GLU-A của golden_cls.py: D = 300, nội kiểm QC_L, chuẩn máy CAL."""
	values = {
		"doctype": "NC QC Plan",
		"test_system": test_system,
		"run_days_per_year": 300,
		"iqc_lines": [
			dict(qc_material="QC_L", levels=2, runs_per_day=1, qty_per_run=0.2, shared_parameter_count=20)
		],
		"calibration_lines": [
			dict(calibrator="CAL", points=2, replicates=2, calibrations_per_year=12, cost_per_calibration=400000)
		],
	}
	values.update(kw)
	return values


def make_qc_plan(test_system, **kw):
	doc = frappe.get_doc(qc_plan_values(test_system, **kw))
	doc.insert(ignore_permissions=True)
	return doc


def make_eqa_program(code="EQA-HS", department="HS-CLS", services=("GLU",), **kw):
	values = {
		"doctype": "NC EQA Program",
		"eqa_code": code,
		"program_name": "Ngoại kiểm hóa sinh",
		"provider": "Trung tâm kiểm chuẩn",
		"department": department,
		"rounds_per_year": 3,
		"samples_per_round": 4,
		"annual_fee": 24000000,
		"annual_shipping_fee": 1200000,
		"services": [dict(technical_service=s) for s in services],
	}
	values.update(kw)
	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	return doc
