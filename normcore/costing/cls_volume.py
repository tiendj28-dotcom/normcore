"""Sản lượng cận lâm sàng, phút khai thác, xuất kho thực tế — hàm thuần Python (ADR-003).

FR-ACCT-012..015, FR-SVC-009 (đổi mã ngoài), FR-QC-006 (ô test phụ trống), FR-CLS-007 (mục sản lượng).
ASM-035-02..05, ASM-035-10. Không có phép tính tiền hay hệ số k (thuộc FEAT-036).
"""

from decimal import Decimal, InvalidOperation

from normcore.costing.allocation_rules import valid_year
from normcore.costing.test_systems import BASIS_MINUTE

AUX_FIELDS = ("iqc_tests", "calibration_tests", "rerun_tests", "eqa_tests")
NON_NEGATIVE = ("patient_results", *AUX_FIELDS, "wastage_rate", "avg_batch_size", "run_days")
LABELS = {
	"fiscal_year": "Năm tài chính",
	"scenario": "Kịch bản sản lượng",
	"test_system": "Mã hệ thống xét nghiệm",
	"service_code": "Mã dịch vụ",
	"department": "Mã khoa",
	"patient_results": "Số kết quả trả",
	"iqc_tests": "Số test nội kiểm",
	"calibration_tests": "Số test chuẩn máy",
	"rerun_tests": "Số test chạy lại",
	"eqa_tests": "Số test ngoại kiểm",
	"wastage_rate": "Tỷ lệ hao hụt (%)",
	"avg_batch_size": "Cỡ mẻ bình quân",
	"run_days": "Số ngày chạy máy",
	"equipment": "Mã thiết bị",
	"total_minutes": "Tổng số phút khai thác",
	"item": "Mã mặt hàng",
	"issued_qty": "Lượng xuất (đơn vị mua)",
}


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


def _year_error(get, errors):
	if not valid_year(get("fiscal_year")):
		errors.append(("fiscal_year", f"{LABELS['fiscal_year']} phải từ 2000 đến 2100"))


def _number(get, field, errors):
	try:
		return _num(get(field))
	except ValueError:
		errors.append((field, f"{LABELS[field]} phải là số"))
		return None


def volume_errors(get) -> list:
	"""Lỗi (trường, thông báo) của một dòng sản lượng cận lâm sàng; `get(field)` trả giá trị hoặc None."""
	errors = []
	_year_error(get, errors)
	if _blank(get("patient_results")):
		errors.append(("patient_results", f"{LABELS['patient_results']} là bắt buộc"))
	for f in NON_NEGATIVE:
		n = _number(get, f, errors)
		if n is None:
			continue
		if n < 0:
			errors.append((f, f"{LABELS[f]} không được âm"))
		elif f == "wastage_rate" and n > 100:
			errors.append((f, f"{LABELS[f]} không quá 100"))
		elif f == "avg_batch_size" and n == 0:
			errors.append((f, f"{LABELS[f]} phải lớn hơn 0"))
		elif f == "run_days" and not (1 <= n <= 366):
			errors.append((f, f"{LABELS[f]} phải từ 1 đến 366"))
	return errors


def resolve_service(source_system, code, map_lookup, service_exists) -> str:
	"""Đổi mã ngoài (LIS/RIS/HIS) sang mã dịch vụ (FR-SVC-009); nguồn trống = mã nội bộ."""
	if _blank(source_system):
		if service_exists(code):
			return code
		raise ValueError(f'"{code}" không tồn tại trong NC Technical Service')
	service = map_lookup(source_system, code)
	if not service:
		raise ValueError(f'Mã dịch vụ "{code}" không có trong ánh xạ mã {source_system}')
	if not service_exists(service):
		raise ValueError(f'"{service}" không tồn tại trong NC Technical Service')
	return service


def system_mismatch(system, service, department) -> list:
	"""Dịch vụ, khoa của dòng phải khớp hệ thống xét nghiệm (ASM-035-02)."""
	errors = []
	if service != system.get("technical_service"):
		errors.append(
			("service_code", f"Hệ thống thuộc dịch vụ {system.get('technical_service')}, dòng ghi {service}")
		)
	if not _blank(department) and department != system.get("department"):
		errors.append(("department", f"Hệ thống thuộc khoa {system.get('department')}, dòng ghi {department}"))
	return errors


def blank_aux(get) -> list:
	"""Các trường test phụ đang trống (hiển thị 'Sẽ ước tính từ kế hoạch'); 0 không phải trống."""
	return [f for f in AUX_FIELDS if _blank(get(f))]


def usage_errors(get, allocation_basis) -> list:
	errors = []
	_year_error(get, errors)
	if allocation_basis != BASIS_MINUTE:
		errors.append(
			("equipment", f"Thiết bị chia chi phí theo {allocation_basis}, không cần phút khai thác")
		)
	n = _number(get, "total_minutes", errors)
	if _blank(get("total_minutes")):
		errors.append(("total_minutes", f"{LABELS['total_minutes']} là bắt buộc"))
	elif n is not None and n < 0:
		errors.append(("total_minutes", f"{LABELS['total_minutes']} không được âm"))
	return errors


def stock_errors(get) -> list:
	errors = []
	_year_error(get, errors)
	n = _number(get, "issued_qty", errors)
	if _blank(get("issued_qty")):
		errors.append(("issued_qty", f"{LABELS['issued_qty']} là bắt buộc"))
	elif n is not None and n < 0:
		errors.append(("issued_qty", f"{LABELS['issued_qty']} không được âm"))
	return errors


def _fmt(n) -> str:
	"""Định dạng số kiểu Việt Nam: 12.000 (NFR-LOC-001)."""
	d = Decimal(str(n))
	text = f"{d:,.0f}" if d == d.to_integral() else f"{d:,.2f}".rstrip("0").rstrip(".")
	return text.replace(",", "X").replace(".", ",").replace("X", ".")


def volume_status(rec) -> dict:
	"""Mục `volume` của khối tình trạng (FR-CLS-007, ASM-035-10)."""
	if not rec:
		return {"state": "empty", "message": "Chưa có"}
	msg = f"Năm {rec.get('fiscal_year')}: {_fmt(rec.get('patient_results') or 0)} kết quả trả"
	if blank_aux(rec.get):
		return {"state": "estimated", "message": msg + " — số test phụ sẽ ước tính từ kế hoạch"}
	return {"state": "ok", "message": msg}
