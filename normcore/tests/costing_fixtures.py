"""Dữ liệu vàng FEAT-015 trên site: dựng từ docs/golden/golden_engine.py (không chép số)."""

import sys
from pathlib import Path

import frappe

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs" / "golden"))
import golden_engine as g

from normcore.tests.utils import costing_run_inputs, ensure, make_base, make_procedure, publish_procedure

ITEM_TYPE = {
	"GANG": "Vật tư tiêu hao",
	"THUOCX": "Thuốc",
	"DUNGCU": "Vật tư dùng nhiều lần",
	"DIEN": "Tiện ích",
	"THUOCY": "Thuốc",
}


def make_price_category(code="PC-GOLD", include_depreciation=1, include_accumulation=1):
	return ensure(
		"NC Price Category",
		"category_code",
		code,
		category_name="Loại giá thử",
		approval_authority="Bệnh viện",
		include_depreciation=include_depreciation,
		include_accumulation=include_accumulation,
	)


def make_golden_params():
	"""Bộ tham số theo golden PARAM và JOB (đơn giá giờ công do controller tính)."""
	P = g.PARAM
	for code in g.JOB:
		ensure("NC Job Title", "job_title_code", code, job_title_name=code, job_group="Điều dưỡng")
	ps = frappe.get_doc(
		{
			"doctype": "NC Costing Parameter Set",
			"title": "Bộ tham số vàng FEAT-015",
			"effective_from": "2026-01-01",
			"base_salary": float(P["base_salary"]),
			"employer_contribution_rate": float(P["contribution"] * 100),
			"working_days_per_year": float(P["days"]),
			"working_hours_per_day": float(P["hours"]),
			"accumulation_mode": P["accumulation_mode"],
			"accumulation_rate": float(P["accumulation_rate"] * 100),
			"obligation_rate": float(P["obligation_rate"] * 100),
			"rounding_unit": int(P["rounding_unit"]),
			"electricity_price": float(P["electricity_price"]),
			"job_title_rates": [
				{
					"job_title": c,
					"salary_coefficient": float(j["coef"]),
					"allowance_coefficient": float(j["allow"]),
				}
				for c, j in g.JOB.items()
			],
		}
	)
	ps.insert(ignore_permissions=True)
	return ps


def make_golden_resources(department, skip_price=()):
	for code, it in g.ITEM.items():
		ensure(
			"NC Item",
			"item_code",
			code,
			item_name=code,
			item_type=ITEM_TYPE[code],
			uom="kWh" if code == "DIEN" else "cái",
			reuse_count=it["reuse"],
		)
		if code in skip_price:
			continue
		frappe.get_doc(
			{
				"doctype": "NC Item Price",
				"price_code": f"DG-{code}",
				"item": code,
				"unit_price": float(it["price"]),
				"price_source": "Hợp đồng",
				"document_no": "HD-1",
				"document_date": "2026-01-01",
				"valid_from": "2026-01-01",
			}
		).insert(ignore_permissions=True).db_set("verification_status", "Đã xác minh")  # dựng dữ liệu
	e = g.EQUIP["EQ1"]
	frappe.get_doc(
		{
			"doctype": "NC Equipment",
			"equipment_code": "EQ1",
			"equipment_name": "Thiết bị EQ1",
			"department": department,
			"acquisition_mode": "Mua",
			"allocation_basis": "Giờ kế hoạch",
			"original_cost": float(e["cost"]),
			"useful_life_years": float(e["life"]),
			"in_service_date": e["in_service"].isoformat(),
			"funding_source": "Ngân sách",
			"annual_maintenance_cost": float(e["maint"]),
			"annual_calibration_cost": float(e["calib"]),
			"planned_hours_per_year": float(e["hours"]),
			"utilization_rate": float(e["util"]),
		}
	).insert(ignore_permissions=True)
	r = g.ROOM["R1"]
	frappe.get_doc(
		{
			"doctype": "NC Room",
			"room_code": "R1",
			"room_name": "Phòng R1",
			"department": department,
			"annual_infrastructure_cost": float(r["annual"]),
			"available_hours_per_year": float(r["hours"]),
		}
	).insert(ignore_permissions=True)


RESOURCE_DOCTYPE = {
	"LABOR": "NC Job Title",
	"DRUG": "NC Item",
	"SUPPLY": "NC Item",
	"UTILITY": "NC Item",
	"EQUIPMENT": "NC Equipment",
	"INFRA": "NC Room",
}


def make_locked_norm_set(service, department, golden_service="DV-TEST-A"):
	"""Bộ định mức "Đã khóa" của `service` có đúng các dòng golden NORMS[golden_service]."""
	proc = make_procedure(service, department)
	proc.steps = []
	for title in ("Bước 1", "Bước 2", "Bước 3"):
		proc.append("steps", {"phase": "Thực hiện", "step_title": title, "description": title})
	proc.resources = []
	proc.flags.ignore_single_active = True
	proc.save(ignore_permissions=True)
	step_of = {f"S00{i + 1}": s.step_id for i, s in enumerate(proc.steps)}
	publish_procedure(proc, "QĐ-G", "2026-01-01")
	lines = []
	for l in g.NORMS[golden_service]:
		lines.append(
			{
				"line_id": l.line_id,
				"step_id": step_of.get(l.step) if l.step else None,
				"service_level": 0 if l.step else 1,
				"procedure_resource_row": "x",
				"component": l.comp,
				"resource_doctype": RESOURCE_DOCTYPE[l.comp],
				"resource": l.res,
				"headcount": l.headcount,
				"hospital_qty": float(l.qty),
				"authority_qty": float(l.authority) if l.authority is not None else 0,
				"wastage_rate": float(l.wastage * 100),
				"is_excluded": 1 if l.excluded else 0,
				"exclude_reason": "Thanh toán riêng" if l.excluded else None,
				"basis": "Quy trình",
				"uom": "phút" if l.comp in ("LABOR", "EQUIPMENT", "INFRA") else "đơn vị",
			}
		)
	ns = frappe.get_doc(
		{
			"doctype": "NC Norm Set",
			"technical_service": service,
			"department": department,
			"procedure": proc.name,
			"version_no": 1,
			"status": "Đã khóa",
			"lines": lines,
		}
	)
	ns.flags.allow_lock = True
	ns.insert(ignore_permissions=True)
	return ns


def make_golden_run(params, price_category="PC-GOLD", **extra):
	run = frappe.get_doc(
		{
			"doctype": "NC Costing Run",
			"title": "Lần tính vàng",
			"fiscal_year": 2026,
			"costing_date": g.COSTING_DATE.isoformat(),
			"parameter_set": params.name,
			**costing_run_inputs(),
			"price_category": price_category,
			**extra,
		}
	)
	run.insert(ignore_permissions=True)
	return run


def make_golden_world(skip_price=()):
	"""DV-TEST-A và DV-TEST-B ở khoa KHOA-TEST, đủ nguồn lực; trả (params, department, [bộ định mức A, B])."""
	_, dept, _ = make_base("DV-TEST-A", "KHOA-TEST")
	ensure("NC Technical Service", "service_code", "DV-TEST-B", service_name="Dịch vụ thử B")
	make_price_category()
	params = make_golden_params()
	make_golden_resources(dept, skip_price)
	for svc, vol in g.VOLUME.items():
		frappe.get_doc(
			{
				"doctype": "NC Service Volume",
				"fiscal_year": 2026,
				"technical_service": svc,
				"department": dept,
				"scenario": "Thực tế 12 tháng",
				"volume": float(vol),
			}
		).insert(ignore_permissions=True)
	sets = [make_locked_norm_set(s, dept, s) for s in ("DV-TEST-A", "DV-TEST-B")]
	return params, dept, sets
