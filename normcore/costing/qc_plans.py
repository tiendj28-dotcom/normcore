"""Kế hoạch chất lượng và chương trình ngoại kiểm — hàm thuần Python, không import framework (ADR-003).

FR-QC-001..003, FR-QC-005, FR-QC-007 (một phần), FR-QC-008, FR-CLS-007 (thẻ qc_plan); DI-11, DI-12, DI-16.
ASM-032-02..05, ASM-032-08, ASM-032-10. Không có phép tính tiền: công thức BR-CLS-006..008 thuộc FEAT-034/036.
Số test ước tính khớp nhánh ước tính của `golden_cls.k_factor` (dòng 154-156).
"""

from decimal import Decimal, InvalidOperation

IQC_TYPE = "Vật liệu nội kiểm"
CAL_TYPE = "Chất chuẩn"
LAB_GROUPS = ("Hóa sinh", "Miễn dịch", "Huyết học", "Vi sinh", "Giải phẫu bệnh")  # ASM-032-05

LABELS = {
	"test_system": "Hệ thống xét nghiệm",
	"run_days_per_year": "Số ngày chạy mỗi năm",
	"qc_material": "Vật liệu nội kiểm",
	"levels": "Số mức",
	"runs_per_day": "Số lần chạy mỗi ngày",
	"qty_per_run": "Lượng dùng mỗi lần",
	"shared_parameter_count": "Số thông số dùng chung",
	"calibrator": "Chất chuẩn",
	"points": "Số điểm chuẩn",
	"replicates": "Số lần lặp",
	"calibrations_per_year": "Số lần chuẩn mỗi năm",
	"cost_per_calibration": "Chi phí chất chuẩn mỗi lần",
	"eqa_code": "Mã chương trình",
	"program_name": "Tên chương trình",
	"provider": "Đơn vị triển khai",
	"department": "Khoa tham gia",
	"rounds_per_year": "Số đợt mỗi năm",
	"samples_per_round": "Số mẫu mỗi đợt",
	"annual_fee": "Phí chương trình năm",
	"annual_shipping_fee": "Phí vận chuyển năm",
	"technical_service": "Dịch vụ",
	"share_pct": "Tỷ lệ riêng",
}

# (trường, giá trị tối thiểu, tối thiểu có được bằng không?, tối đa)
_RUN_DAYS = ("run_days_per_year", 1, True, 366)
_IQC = (
	("levels", 1, True, None),
	("runs_per_day", 0, False, None),
	("qty_per_run", 0, False, None),
	("shared_parameter_count", 1, True, None),
)
_CAL = (
	("points", 1, True, None),
	("replicates", 1, True, None),
	("calibrations_per_year", 0, False, None),
	("cost_per_calibration", 0, False, None),
)
_EQA = (
	("rounds_per_year", 1, True, None),
	("samples_per_round", 1, True, None),
	("annual_fee", 0, False, None),
)


def _blank(v) -> bool:
	return v is None or str(v).strip() == ""


def _num(v):
	"""Decimal hoặc None khi trống; ValueError khi không phải số."""
	if _blank(v):
		return None
	try:
		return Decimal(str(v))
	except InvalidOperation as e:
		raise ValueError(str(v)) from e


def _check_number(values, spec, prefix, errors):
	field, low, low_inclusive, high = spec
	label = LABELS[field]
	if _blank(values.get(field)):
		errors.append(f"{prefix}Thiếu {label}")
		return
	try:
		n = _num(values.get(field))
	except ValueError:
		errors.append(f"{prefix}{label} phải là số")
		return
	if (n < low) or (n == low and not low_inclusive):
		errors.append(f"{prefix}{label} phải {'từ' if low_inclusive else 'lớn hơn'} {low}")
	elif high is not None and n > high:
		errors.append(f"{prefix}{label} phải từ {low} đến {high}")


def _check_item(values, field, expected, item_types, prefix, errors):
	code = values.get(field)
	if _blank(code):
		errors.append(f"{prefix}Thiếu {LABELS[field]}")
		return None
	actual = item_types.get(code)
	if actual != expected:
		what = f"thuộc loại {actual}" if actual else "không tồn tại"
		errors.append(f"{prefix}mặt hàng {code} {what}, không phải {expected}")
	return code


def validate_qc_plan(values: dict, item_types: dict) -> list:
	"""Danh sách lỗi (rỗng = hợp lệ) theo technical-design 2.1. `item_types` = {mã mặt hàng: loại}."""
	errors = []
	if _blank(values.get("test_system")):
		errors.append(f"Thiếu {LABELS['test_system']}")
	_check_number(values, _RUN_DAYS, "", errors)
	for title, rows, specs, field, expected in (
		("nội kiểm", values.get("iqc_lines") or [], _IQC, "qc_material", IQC_TYPE),
		("chuẩn máy", values.get("calibration_lines") or [], _CAL, "calibrator", CAL_TYPE),
	):
		seen = set()
		for i, row in enumerate(rows, 1):
			prefix = f"Dòng {title} {i}: "
			code = _check_item(row, field, expected, item_types, prefix, errors)
			if code is not None:
				if code in seen:
					errors.append(f"{prefix}{LABELS[field]} {code} bị lặp")
				seen.add(code)
			for spec in specs:
				_check_number(row, spec, prefix, errors)
	return errors


def validate_eqa_program(values: dict, paraclinical_services) -> list:
	"""Danh sách lỗi (rỗng = hợp lệ) theo technical-design 2.2 (FR-QC-003, FR-QC-005, DI-12)."""
	errors = []
	for f in ("eqa_code", "program_name", "provider", "department"):
		if _blank(values.get(f)):
			errors.append(f"Thiếu {LABELS[f]}")
	for spec in _EQA:
		_check_number(values, spec, "", errors)
	if not _blank(values.get("annual_shipping_fee")):
		try:
			if _num(values.get("annual_shipping_fee")) < 0:
				errors.append(f"{LABELS['annual_shipping_fee']} không được âm")
		except ValueError:
			errors.append(f"{LABELS['annual_shipping_fee']} phải là số")
	rows = values.get("services") or []
	if not rows:
		errors.append("Chương trình phải có ít nhất một dịch vụ tham gia")
		return errors
	seen = set()
	shares = []
	for i, row in enumerate(rows, 1):
		prefix = f"Dòng dịch vụ {i}: "
		svc = row.get("technical_service")
		if _blank(svc):
			errors.append(f"{prefix}Thiếu {LABELS['technical_service']}")
		else:
			if svc in seen:
				errors.append(f"{prefix}dịch vụ {svc} bị lặp")
			seen.add(svc)
			if svc not in paraclinical_services:
				errors.append(f"{prefix}dịch vụ {svc} chưa được đánh dấu cận lâm sàng")
		try:
			share = _num(row.get("share_pct")) or Decimal(0)
		except ValueError:
			errors.append(f"{prefix}{LABELS['share_pct']} phải là số")
			continue
		if share < 0 or share > 100:
			errors.append(f"{prefix}{LABELS['share_pct']} phải từ 0 đến 100")
		shares.append(share)
	positive = [s for s in shares if s > 0]
	if positive and len(positive) != len(rows):
		errors.append("Tỷ lệ riêng phải nhập ở mọi dòng hoặc để trống ở mọi dòng")
	elif positive and len(shares) == len(rows) and sum(shares) != 100:
		errors.append(f"Tổng tỷ lệ riêng của các dịch vụ là {sum(shares).normalize():f}%, phải bằng 100%")
	return errors


def eqa_shares(rows) -> list:
	"""Tỷ lệ hiệu lực dạng phân số (BR-CLS-008): mọi dòng trống/0 thì chia đều 1/n."""
	vals = [_num(r.get("share_pct")) or Decimal(0) for r in rows]
	if not vals:
		return []
	if all(v == 0 for v in vals):
		return [Decimal(1) / len(vals)] * len(vals)
	return [v / 100 for v in vals]


def _opt(v):
	try:
		return _num(v)
	except ValueError:
		return None


def estimate_complete(plan) -> bool:
	"""True khi mọi số cần cho ước tính đều có."""
	if _opt(plan.get("run_days_per_year")) is None:
		return False
	for r in plan.get("iqc_lines") or []:
		if _opt(r.get("levels")) is None or _opt(r.get("runs_per_day")) is None:
			return False
	for r in plan.get("calibration_lines") or []:
		if any(_opt(r.get(f)) is None for f in ("points", "replicates", "calibrations_per_year")):
			return False
	return True


def estimated_tests(plan) -> tuple:
	"""(số test nội kiểm, số test chuẩn máy) mỗi năm; dòng thiếu số bị bỏ qua. golden_cls.py dòng 154-155."""
	days = _opt(plan.get("run_days_per_year")) or Decimal(0)
	iqc = Decimal(0)
	for r in plan.get("iqc_lines") or []:
		levels, runs = _opt(r.get("levels")), _opt(r.get("runs_per_day"))
		if levels is not None and runs is not None:
			iqc += levels * runs * days
	cal = Decimal(0)
	for r in plan.get("calibration_lines") or []:
		vals = [_opt(r.get(f)) for f in ("calibrations_per_year", "points", "replicates")]
		if None not in vals:
			cal += vals[0] * vals[1] * vals[2]
	return iqc, cal


def eqa_samples_per_year(rounds, samples) -> Decimal:
	"""golden_cls.py dòng 156."""
	return Decimal(str(rounds)) * Decimal(str(samples))


def missing_iqc_warning(cls_group, plan, test_system_code) -> str | None:
	"""FR-QC-007: cảnh báo, không bao giờ ném lỗi (không chặn khóa bộ định mức)."""
	if cls_group not in LAB_GROUPS:
		return None
	if plan and (plan.get("iqc_lines") or []):
		return None
	return f"Hệ thống {test_system_code} chưa có kế hoạch nội kiểm"


def plan_status_item(plan, cls_group=None) -> dict:
	"""Thẻ `qc_plan` của khối tình trạng khi đã có kế hoạch (ASM-032-08)."""
	n_iqc = len(plan.get("iqc_lines") or [])
	n_cal = len(plan.get("calibration_lines") or [])
	item = {"key": "qc_plan", "label": "Kế hoạch chất lượng", "source": "FEAT-032"}
	if n_iqc == 0 and cls_group in LAB_GROUPS:
		return {**item, "state": "warning", "message": f"Thiếu nội kiểm — {n_cal} dòng chuẩn máy"}
	return {**item, "state": "ok", "message": f"Có — {n_iqc} dòng nội kiểm, {n_cal} dòng chuẩn máy"}
