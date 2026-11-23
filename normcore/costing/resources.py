"""Thiết bị và phòng — hàm thuần Python, không import framework (ADR-003).

BR-COST-004, BR-COST-005, BR-CLS-009, BR-CLS-010 (phần linh kiện tính theo tháng).
Đối chiếu: docs/golden/golden_engine.py `equip_rate`, `room_rate`; docs/golden/golden_cls.py
`machine_annual`, `equipment_annual`. Chỉ đơn giá giờ làm tròn 4 số lẻ HALF_UP; số năm giữ nguyên Decimal.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

BUY = "Mua"
RENT = "Thuê"
VENDOR = "Đặt theo hóa chất"
JOINT = "Liên doanh, liên kết"
ACQUISITION_MODES = (BUY, RENT, VENDOR, JOINT)
BASIS_HOURS = "Giờ kế hoạch"
BASIS_RESULT = "Số kết quả"
BASIS_MINUTE = "Phút chiếm máy"
ALLOCATION_BASES = (BASIS_HOURS, BASIS_RESULT, BASIS_MINUTE)
ZERO = "ZERO"
CONTINUE = "CONTINUE"
LIFE_MONTH = "Tháng"

_Q4 = Decimal("0.0001")
_NON_NEGATIVE = {
	"original_cost": "Nguyên giá",
	"annual_contract_cost": "Chi phí năm theo hợp đồng",
	"contract_asset_value": "Giá trị ghi trên hợp đồng",
	"annual_maintenance_cost": "Bảo trì năm",
	"annual_calibration_cost": "Kiểm định, hiệu chuẩn năm",
	"power_kw": "Công suất khi chạy",
	"power_standby_kw": "Công suất khi chờ",
	"run_hours_per_day": "Số giờ chạy mỗi ngày",
	"standby_hours_per_day": "Số giờ chờ mỗi ngày",
}


def _d(x) -> Decimal:
	return Decimal(0) if x is None or x == "" else Decimal(str(x))


def _r4(x: Decimal) -> Decimal:
	return x.quantize(_Q4, rounding=ROUND_HALF_UP)


def is_expired(in_service: date, life_years, on: date) -> bool:
	"""Hết thời gian sử dụng: ngày tính giá >= ngày đưa vào sử dụng + int(số năm) (golden).

	Số năm lẻ cắt về số nguyên (như golden). Đưa vào sử dụng 29/02 mà năm đích không nhuận thì lấy 28/02 (ASM-083).
	"""
	year = in_service.year + int(_d(life_years))
	day = in_service.day
	if in_service.month == 2 and day == 29 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
		day = 28
	return on >= date(year, in_service.month, day)


def machine_annual(
	mode: str,
	original_cost=None,
	life_years=None,
	in_service: date | None = None,
	contract_cost=None,
	on: date | None = None,
	expired_mode: str | None = ZERO,
	include_depr: bool = True,
) -> Decimal:
	"""BR-CLS-009 chi phí máy năm: Đặt = 0; Thuê, Liên doanh = hợp đồng; Mua = khấu hao năm (BR-COST-004)."""
	if mode == VENDOR:
		return Decimal(0)
	if mode in (RENT, JOINT):
		return _d(contract_cost)
	if mode != BUY:
		raise ValueError(f"Hình thức có máy không hợp lệ: {mode}")
	if not include_depr:  # BR-COST-016
		return Decimal(0)
	life = _d(life_years)
	if life <= 0:
		raise ValueError("Thời gian sử dụng phải lớn hơn 0")
	if expired_mode not in (None, ZERO, CONTINUE):
		raise ValueError(f"Lựa chọn khấu hao khi hết thời gian sử dụng không hợp lệ: {expired_mode}")
	if in_service is not None and on is not None and is_expired(in_service, life, on):
		if expired_mode != CONTINUE:
			return Decimal(0)
	return _d(original_cost) / life


def equipment_annual(
	machine: Decimal,
	maintenance=None,
	calibration=None,
	components=(),
	mode: str = BUY,
	maintenance_vendor_paid: bool = False,
	dept_share=1,
) -> Decimal:
	"""BR-CLS-009, BR-CLS-010: (máy + bảo trì + linh kiện tính theo tháng + kiểm định) * tỷ lệ khoa.

	components: dãy (replacement_cost, life_basis, life_value, vendor_paid). Khi Đặt theo hóa chất, bảo trì
	và linh kiện "nhà cung cấp chịu" = 0.
	"""
	vendor = mode == VENDOR
	maint = Decimal(0) if (vendor and maintenance_vendor_paid) else _d(maintenance)
	parts = Decimal(0)
	for cost, basis, life, vendor_paid in components:
		if basis != LIFE_MONTH or (vendor and vendor_paid):
			continue
		if _d(life) <= 0:
			raise ValueError("Tuổi thọ linh kiện phải lớn hơn 0")
		parts += _d(cost) * 12 / _d(life)
	return (Decimal(machine) + maint + parts + _d(calibration)) * _d(dept_share)


def machine_hourly_rate(annual_cost: Decimal, planned_hours, utilization) -> Decimal:
	"""BR-COST-004: đơn giá giờ máy = chi phí năm / (giờ kế hoạch * hệ số sử dụng), 4 số lẻ HALF_UP."""
	denominator = _d(planned_hours) * _d(utilization)
	if denominator <= 0:
		raise ValueError("Giờ khai thác kế hoạch và hệ số sử dụng phải lớn hơn 0")
	return _r4(Decimal(annual_cost) / denominator)


def room_hourly_rate(annual_cost, available_hours) -> Decimal:
	"""BR-COST-005: đơn giá giờ phòng = chi phí hạ tầng năm / giờ khai thác năm, 4 số lẻ HALF_UP."""
	hours = _d(available_hours)
	if hours <= 0:
		raise ValueError("Số giờ khai thác năm phải lớn hơn 0")
	return _r4(_d(annual_cost) / hours)


def validate_allocations(rows) -> list[str]:
	"""DI-10, FR-RES-025: rows là dãy (khoa, share_pct); trống hợp lệ; tổng phải bằng 100."""
	rows = list(rows)
	if not rows:
		return []
	errors = []
	depts = [d for d, _ in rows]
	if len(set(depts)) != len(depts):
		errors.append("Một khoa chỉ được khai một dòng tỷ lệ phân bổ")
	if any(_d(s) < 0 for _, s in rows):
		errors.append("Tỷ lệ phân bổ không được âm")
	total = sum((_d(s) for _, s in rows), Decimal(0))
	if total != 100:
		errors.append(f"Tổng tỷ lệ phân bổ theo khoa phải bằng 100%, hiện là {total.normalize():f}%")
	return errors


def validate_equipment(f: dict) -> list[str]:
	"""FR-RES-005, 019, 020, 021, 022: trường bắt buộc theo hình thức có máy và tiêu chí chia."""
	errors = []
	mode = f.get("acquisition_mode")
	basis = f.get("allocation_basis")
	if mode not in ACQUISITION_MODES:
		errors.append("Phải chọn hình thức có máy hợp lệ")
	if basis not in ALLOCATION_BASES:
		errors.append("Phải chọn tiêu chí chia chi phí hợp lệ")
	if mode == BUY:
		if _d(f.get("original_cost")) <= 0:
			errors.append("Thiết bị hình thức Mua phải có nguyên giá lớn hơn 0")
		if _d(f.get("useful_life_years")) <= 0:
			errors.append("Thiết bị hình thức Mua phải có thời gian sử dụng (năm) lớn hơn 0")
	elif mode in (RENT, JOINT) and _d(f.get("annual_contract_cost")) <= 0:
		errors.append("Thiết bị Thuê hoặc Liên doanh, liên kết phải có chi phí năm theo hợp đồng")
	if basis == BASIS_HOURS:
		if _d(f.get("planned_hours_per_year")) <= 0:
			errors.append("Tiêu chí chia Giờ kế hoạch phải có số giờ khai thác kế hoạch năm lớn hơn 0")
		u = _d(f.get("utilization_rate"))
		if not (0 < u <= 1):
			errors.append("Tiêu chí chia Giờ kế hoạch phải có hệ số sử dụng trong khoảng (0, 1]")
	for key, label in _NON_NEGATIVE.items():
		if _d(f.get(key)) < 0:
			errors.append(f"{label} không được âm")
	return errors


def validate_room(f: dict) -> list[str]:
	"""FR-RES-008: chi phí hạ tầng năm và giờ khai thác năm bắt buộc (CF-003: diện tích không bắt buộc)."""
	errors = []
	if f.get("annual_infrastructure_cost") in (None, ""):
		errors.append("Phòng phải có chi phí hạ tầng năm")
	elif _d(f.get("annual_infrastructure_cost")) < 0:
		errors.append("Chi phí hạ tầng năm không được âm")
	if _d(f.get("available_hours_per_year")) <= 0:
		errors.append("Phòng phải có số giờ khai thác năm lớn hơn 0")
	return errors
