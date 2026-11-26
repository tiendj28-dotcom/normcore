"""Xuất bộ định mức ra Excel (FR-OUT-006 phần Excel, FR-OUT-011; ASM-034-15, 16). Chỉ dùng openpyxl."""

import io

from openpyxl import Workbook
from openpyxl.styles import Font

NO_RUN = "Chưa có lần tính giá"
NO_PLAN = "Chưa có kế hoạch chất lượng"
ESTIMATED = "Ước tính từ kế hoạch"
K_FORMAT = "0.000000"
CLS_COLUMNS = ("Cấp phát sinh", "Nhân k", "Gắn với")

# (nhãn cột, khóa trong dòng, thuộc cột cận lâm sàng)
LINE_COLUMNS = (
	("Bước", "step_id", False),
	("Tên bước", "step_title", False),
	("Mã dòng", "line_id", False),
	("Cấu phần", "component", False),
	("Nguồn lực", "resource_label", False),
	("Cấp phát sinh", "cost_level_label", True),
	("Nhân k", "apply_k_label", True),
	("Gắn với", "attach_label", True),
	("Số người", "headcount", False),
	("Định mức BV", "hospital_qty", False),
	("Định mức ban hành", "authority_qty", False),
	("Lượng áp dụng", "applied_qty", False),
	("Đơn vị", "uom", False),
	("Hao hụt %", "wastage_rate", False),
	("Căn cứ", "basis", False),
	("Tham chiếu căn cứ", "basis_ref", False),
	("Loại trừ", "excluded_label", False),
	("Lý do loại trừ", "exclude_reason", False),
	("Người xác nhận", "confirmed_by", False),
	("Thời điểm xác nhận", "confirmed_on", False),
)
HEAD_ROWS = (
	("Bộ định mức", "name"),
	("Dịch vụ", "technical_service_label"),
	("Khoa", "department"),
	("Phiên bản", "version_no"),
	("Trạng thái", "status"),
	("Quy trình", "procedure"),
	("Hệ thống xét nghiệm", "test_system"),
	("Số xét nghiệm mỗi ống mẫu", "tests_per_tube"),
	("Người khóa", "locked_by"),
	("Thời điểm khóa", "locked_on"),
)


def latest_k(rows):
	"""ASM-034-16: k của lần tính giá "Đã tính"/"Đã khóa" gần nhất (ngày lớn nhất, hòa thì tên lớn nhất).
	rows: [{run, costing_date, status, k_factor, k_estimated}] -> dict hoặc None."""
	ok = [r for r in rows or () if r.get("status") in ("Đã tính", "Đã khóa") and r.get("k_factor") is not None]
	if not ok:
		return None
	return max(ok, key=lambda r: (str(r.get("costing_date") or ""), str(r.get("run") or "")))


def _text(v):
	return "" if v is None else v


def _bold(ws, row):
	for c in ws[row]:
		c.font = Font(bold=True)


def _table(ws, headers, rows):
	ws.append(list(headers))
	_bold(ws, ws.max_row)
	for r in rows:
		ws.append(list(r))


def build_workbook(data: dict) -> bytes:
	wb = Workbook()
	ws = wb.active
	ws.title = "Bộ định mức"
	head = data.get("head") or {}
	for label, key in HEAD_ROWS:
		if key in ("test_system", "tests_per_tube") and not data.get("has_test_system"):
			continue
		ws.append([label, _text(head.get(key))])
		ws.cell(ws.max_row, 1).font = Font(bold=True)
	ws.append([])
	cols = [c for c in LINE_COLUMNS if data.get("has_test_system") or not c[2]]
	_table(ws, [c[0] for c in cols], [[_text(ln.get(c[1])) for c in cols] for ln in data.get("lines") or ()])
	if data.get("has_test_system"):
		_quality_sheets(wb, data)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def _quality_sheets(wb, data):
	plan = data.get("qc_plan")
	run_days = (plan or {}).get("run_days_per_year")
	ws = wb.create_sheet("Nội kiểm")
	if plan:
		_table(
			ws,
			("Vật liệu", "Số mức", "Lần/ngày", "Lượng/lần", "Số thông số dùng chung", "Ngày chạy/năm"),
			[
				(r.get("qc_material"), r.get("levels"), r.get("runs_per_day"), r.get("qty_per_run"),
				 r.get("shared_parameter_count"), run_days)
				for r in plan.get("iqc_lines") or ()
			],
		)
	else:
		ws.append([NO_PLAN])
	ws = wb.create_sheet("Chuẩn máy")
	if plan:
		_table(
			ws,
			("Chất chuẩn", "Số điểm", "Số lần lặp", "Lần/năm", "Chi phí/lần"),
			[
				(r.get("calibrator"), r.get("points"), r.get("replicates"), r.get("calibrations_per_year"),
				 r.get("cost_per_calibration"))
				for r in plan.get("calibration_lines") or ()
			],
		)
	else:
		ws.append([NO_PLAN])
	ws = wb.create_sheet("Ngoại kiểm")
	if data.get("eqa"):
		_table(
			ws,
			("Mã", "Tên chương trình", "Nhà cung cấp", "Đợt/năm", "Mẫu/đợt", "Phí năm", "Phí vận chuyển",
			 "Tỷ lệ của dịch vụ (%)"),
			[
				(r.get("eqa_code"), r.get("program_name"), r.get("provider"), r.get("rounds_per_year"),
				 r.get("samples_per_round"), r.get("annual_fee"), r.get("annual_shipping_fee"), r.get("share_pct"))
				for r in data["eqa"]
			],
		)
	else:
		ws.append(["Chưa có chương trình ngoại kiểm"])
	ws = wb.create_sheet("Hệ số k")
	k = data.get("k")
	ws.append(["Hệ thống", "Lần tính giá", "Ngày tính", "Hệ số k", "Ghi chú"])
	_bold(ws, 1)
	system = (data.get("head") or {}).get("test_system")
	if k:
		ws.append([system, k.get("run"), _text(k.get("costing_date")), float(k["k_factor"]),
		           ESTIMATED if k.get("k_estimated") else ""])
		ws.cell(ws.max_row, 4).number_format = K_FORMAT
	else:
		ws.append([system, None, None, NO_RUN, ""])
