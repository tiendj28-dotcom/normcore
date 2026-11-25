"""Quy tắc phân bổ, sản lượng, tiêu chí (FEAT-016; FR-ACCT-007, 008, 010; BR-COST-009).

Module thuần Python: không phụ thuộc framework.
"""

from __future__ import annotations

from decimal import Decimal

from normcore.costing.accounting import ALLOCATABLE

DRIVERS = ("LABOR_MIN", "MACHINE_MIN", "VOLUME", "DIRECT_COST", "REVENUE", "HEADCOUNT", "AREA")
LEVEL1_ONLY = ("REVENUE", "HEADCOUNT", "AREA")
LEVEL1, LEVEL2 = "Cấp 1", "Cấp 2"
SUPPORT, CLINICAL = "Hỗ trợ", "Lâm sàng"
DRIVER_FIELDS = {"HEADCOUNT": "headcount", "AREA": "area_m2", "REVENUE": "revenue"}
MIN_YEAR, MAX_YEAR = 2000, 2100


def rule_errors(level, cost_category, driver, center_type=None) -> list[str]:
	"""Lỗi của một quy tắc phân bổ (BR-COST-009, ASM-127). `center_type` None = mọi trung tâm."""
	errors = []
	if cost_category not in ALLOCATABLE:
		errors.append(f"Loại chi phí {cost_category} không dùng để phân bổ")
	if level == LEVEL2 and driver in LEVEL1_ONLY:
		errors.append(f"Tiêu chí {driver} chỉ dùng ở cấp 1 (BR-COST-009)")
	if center_type:
		want = SUPPORT if level == LEVEL1 else CLINICAL
		if center_type != want:
			errors.append(f"Quy tắc {level} chỉ áp cho trung tâm loại {want}")
	return errors


def driver_errors(values) -> list[str]:
	"""Số âm ở headcount, area_m2, revenue (ASM-126). `values`: dict fieldname → số."""
	return [f"{k} không được âm" for k, v in values.items() if v is not None and Decimal(str(v)) < 0]


def volume_errors(volume) -> list[str]:
	if volume is not None and Decimal(str(volume)) < 0:
		return ["Sản lượng không được âm"]
	return []


def valid_year(year) -> bool:
	try:
		return MIN_YEAR <= int(year) <= MAX_YEAR
	except (TypeError, ValueError):
		return False


def driver_shares(values: dict) -> dict:
	"""Tỷ lệ = giá trị / tổng, không làm tròn (khớp golden)."""
	total = sum((Decimal(str(v)) for v in values.values()), Decimal(0))
	if not values or total == 0:
		raise ValueError("Tổng tiêu chí bằng 0")
	return {k: Decimal(str(v)) / total for k, v in values.items()}
