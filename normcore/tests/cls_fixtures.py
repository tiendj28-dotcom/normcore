"""Bộ dữ liệu vàng 2A (golden_cls.py) trên site: FEAT-036. Dựng từ golden, không chép số."""

import sys
from pathlib import Path

import frappe

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs" / "golden"))
import golden_cls as gc

from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import (
	ensure,
	ensure_service,
	make_eqa_program,
	make_private_file,
	make_procedure,
	make_qc_plan,
	make_test_system,
	publish_procedure,
)

DEPT = "XN"
ITEM_TYPE = {
	"HC_GLU": "Hóa chất",
	"ONG": "Vật tư tiêu hao",
	"CUVET": "Vật tư tiêu hao",
	"DD_RUA": "Hóa chất",
	"HC_PT": "Hóa chất",
	"QC_L": "Vật liệu nội kiểm",
}
RESOURCE_DOCTYPE = {"LABOR": "NC Job Title", "EQUIPMENT": "NC Equipment"}
MODE = {"MUA": "Mua", "DAT": "Đặt theo hóa chất", "THUE": "Thuê", "LDLK": "Liên doanh, liên kết"}
BASIS = {"RESULT": "Số kết quả", "MINUTE": "Phút chiếm máy"}
LIFE = {"MONTH": "Tháng", "RESULT": "Số kết quả", "HOUR": "Giờ chạy"}
ATTACH = {"EQUIP": "Thiết bị"}


def _items():
	for code, it in gc.ITEM.items():
		values = dict(
			item_name=code,
			item_type=ITEM_TYPE[code],
			uom="ml",
			norm_units_per_purchase_unit=float(it["units"]),
		)
		if code == "HC_GLU":
			values.update(
				nominal_tests=int(it["nominal"]), open_stability_days=int(it["open_days"]), is_main_reagent=1
			)
		ensure("NC Item", "item_code", code, **values)
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
		).insert(ignore_permissions=True).db_set("verification_status", "Đã xác minh")
	ensure(
		"NC Item",
		"item_code",
		"CAL",
		item_name="CAL",
		item_type="Chất chuẩn",
		uom="ml",
		norm_units_per_purchase_unit=1,
	)


def _equipment(code):
	e = gc.EQUIP[code]
	values = dict(
		equipment_name=f"Máy {code}",
		department=e["dept"] if e["dept"] == DEPT else DEPT,
		acquisition_mode=MODE[e["mode"]],
		allocation_basis=BASIS[e["basis"]],
		funding_source="Ngân sách",
		in_service_date="2022-01-01",
		annual_maintenance_cost=float(e["maint"]),
		maintenance_vendor_paid=1 if e["maint_vendor"] else 0,
		components=[
			dict(
				component_name=p["name"],
				replacement_cost=float(p["cost"]),
				life_basis=LIFE[p["basis"]],
				life_value=float(p["life"]),
				vendor_paid=1 if p["vendor"] else 0,
			)
			for p in e["parts"]
		],
	)
	if e["mode"] == "MUA":
		values.update(
			original_cost=float(e["cost"]),
			useful_life_years=e["life"],
			in_service_date=e["in_service"].isoformat(),
		)
	else:
		values.update(
			contract_asset_value=float(e["asset_value"] or 0),
			annual_contract_cost=float(e.get("contract") or 0),
		)
	if e["power"]:
		p = e["power"]
		values.update(
			power_kw=float(p["run_kw"]),
			run_hours_per_day=float(p["run_h"]),
			power_standby_kw=float(p["standby_kw"]),
			standby_hours_per_day=float(p["standby_h"]),
			continuous_power=1 if p["continuous"] else 0,
		)
	if e["mode"] == "DAT":
		values.update(maintenance_vendor_paid=1)
	return ensure("NC Equipment", "equipment_code", code, **values)


def _compliance(code):
	for c in gc.EQUIP[code]["compliance"]:
		frappe.get_doc(
			{
				"doctype": "NC Equipment Compliance",
				"equipment": code,
				"record_type": "Kiểm định",
				"cycle_months": int(c["cycle"]),
				"provider": "Trung tâm kiểm định",
				"cost_per_time": float(c["cost"]),
				"performed_on": "2026-06-01",
				"expiry_date": "2027-06-01",
				"attachment": make_private_file(),
			}
		).insert(ignore_permissions=True)


def _norm_set(system, proc):
	s = gc.SYSTEMS[system]
	lines = []
	for lid, level, comp, res, qty, apply_k, attach in gc.NORM:
		resource = res or s["equip"]
		if comp == "LABOR":
			resource = "DD"
		lines.append(
			{
				"line_id": lid,
				"service_level": 1,
				"procedure_resource_row": "x",
				"component": comp,
				"resource_doctype": RESOURCE_DOCTYPE.get(comp, "NC Item"),
				"resource": resource,
				"headcount": 1,
				"hospital_qty": float(qty),
				"wastage_rate": 0,
				"basis": "Quy trình",
				"uom": "phút" if comp in ("LABOR", "EQUIPMENT") else "đơn vị",
				"cost_level": level,
				"apply_k": 1 if apply_k else 0,
				"attach_to": ATTACH.get(attach, ""),
				"attach_equipment": s["equip"] if attach == "EQUIP" else None,
			}
		)
	ns = frappe.get_doc(
		{
			"doctype": "NC Norm Set",
			"technical_service": s["service"],
			"department": DEPT,
			"procedure": proc,
			"version_no": 1,
			"status": "Đã khóa",
			"test_system": system,
			"tests_per_tube": float(s["tests_per_tube"]),
			"lines": lines,
		}
	)
	ns.flags.allow_lock = True
	ns.insert(ignore_permissions=True)
	return ns


def make_stock_issues(boxes=None):
	"""FEAT-037 (ASM-037-19): xuất kho năm 2026 của khoa XN khớp lượng tính được của bộ 2A (lệch 0%), riêng
	HC_GLU xuất 94 hộp (biến thể V6, lệch 3,27%, không vượt). `boxes` ghi đè số hộp theo mặt hàng."""
	from decimal import Decimal

	from normcore.costing import reconcile
	from normcore.tests.golden import cls_fixture as cf36

	calc = reconcile.material_quantities([cf36.service()])
	for (dept, item), qty in sorted(calc.items()):
		n = (boxes or {}).get(item, 94 if item == "HC_GLU" else qty / Decimal(str(gc.ITEM[item]["units"])))
		frappe.get_doc(
			{
				"doctype": "NC Stock Issue Actual",
				"fiscal_year": 2026,
				"department": DEPT,
				"item": item,
				"issued_qty": float(n),
			}
		).insert(ignore_permissions=True)


def make_cls_golden(stock_issue=True):
	"""Bộ 2A trên site. Trả frappe._dict(params, dept, other_dept, run_kwargs, systems, norm_sets).
	`stock_issue` False: không có số liệu xuất kho (TC-CLS-19).

	Qtb = 300.000 (EQ_A), 100.000 (EQ_B) nhờ hệ thống phụ "Ngừng dùng" (ASM-036-10)."""
	params, other_dept, other_sets = cf.make_golden_world()
	ensure(
		"NC Cost Center", "cost_center_code", DEPT, cost_center_name="Khoa xét nghiệm", center_type="Lâm sàng"
	)
	ensure(
		"NC Department",
		"department_code",
		DEPT,
		department_name="Khoa xét nghiệm",
		department_type="Lâm sàng",
		cost_center=DEPT,
	)
	frappe.db.set_value(
		"NC Costing Parameter Set", params.name, "electricity_price", float(gc.PARAM["electricity_price"])
	)
	_items()
	ensure_service("GLU")
	frappe.db.set_value(
		"NC Technical Service",
		"GLU",
		{"is_paraclinical": 1, "cls_group": "Hóa sinh", "result_unit": "Kết quả xét nghiệm"},
	)
	ensure_service("PHU")
	frappe.db.set_value(
		"NC Technical Service",
		"PHU",
		{"is_paraclinical": 1, "cls_group": "Hóa sinh", "result_unit": "Kết quả xét nghiệm"},
	)
	for code in ("EQ_A", "EQ_B"):
		_equipment(code)
		_compliance(code)
	make_test_system("GLU-A", "GLU", DEPT, "EQ_A", 75, est_rerun_rate=2, est_wastage_rate=3)
	make_test_system("GLU-B", "GLU", DEPT, "EQ_B", 25, est_rerun_rate=2, est_wastage_rate=3)
	make_test_system("PHU-A", "PHU", DEPT, "EQ_A", 100, status="Ngừng dùng")
	make_test_system("PHU-B", "PHU", DEPT, "EQ_B", 100, status="Ngừng dùng")
	for code, s in gc.SYSTEMS.items():
		act = s["actual"] or {}
		frappe.get_doc(
			{
				"doctype": "NC Test System Volume",
				"fiscal_year": 2026,
				"scenario": "Thực tế 12 tháng",
				"test_system": code,
				"patient_results": float(s["qbn"]),
				"iqc_tests": float(act["qnk"]) if act else None,
				"calibration_tests": float(act["qcal"]) if act else None,
				"rerun_tests": float(act["qrerun"]) if act else None,
				"eqa_tests": float(act["qeqa"]) if act else None,
				"wastage_rate": float(act["h"] * 100) if act else None,
				"avg_batch_size": float(s["batch"]),
				"run_days": int(s["run_days"]),
			}
		).insert(ignore_permissions=True)
	for code, qtb in (
		("PHU-A", gc.USAGE["EQ_A"]["qtb"] - gc.SYSTEMS["GLU-A"]["qbn"]),
		("PHU-B", gc.USAGE["EQ_B"]["qtb"] - gc.SYSTEMS["GLU-B"]["qbn"]),
	):
		frappe.get_doc(
			{
				"doctype": "NC Test System Volume",
				"fiscal_year": 2026,
				"scenario": "Thực tế 12 tháng",
				"test_system": code,
				"patient_results": float(qtb),
			}
		).insert(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "NC Service Volume",
			"fiscal_year": 2026,
			"technical_service": "GLU",
			"department": DEPT,
			"scenario": "Thực tế 12 tháng",
			"volume": 15800,
		}
	).insert(ignore_permissions=True)
	for code in ("GLU-A", "GLU-B"):
		make_qc_plan(code)
	others = [f"XN{i:02d}" for i in range(20)]
	for o in others:
		ensure_service(o)
		frappe.db.set_value(
			"NC Technical Service",
			o,
			{"is_paraclinical": 1, "cls_group": "Hóa sinh", "result_unit": "Kết quả xét nghiệm"},
		)
	make_eqa_program(code="EQA-GOLD", department=DEPT, services=["GLU", *others])
	proc = make_procedure("GLU", DEPT)
	publish_procedure(proc, "QĐ-CLS", "2026-01-01")
	norm_sets = {c: _norm_set(c, proc.name) for c in ("GLU-A", "GLU-B")}
	if stock_issue:
		make_stock_issues()
	return frappe._dict(
		params=params, dept=DEPT, other_dept=other_dept, other_sets=other_sets, norm_sets=norm_sets
	)


def make_run(world, **extra):
	return cf.make_golden_run(world.params, **extra)
