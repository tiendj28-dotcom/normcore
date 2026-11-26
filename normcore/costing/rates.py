"""Dựng đơn giá một dòng (`LineRate`) từ dữ liệu đã nạp. Hàm thuần Python, không import frappe (ADR-003).

BR-COST-001 (LABOR), BR-COST-003 (DRUG/SUPPLY), BR-COST-004 (EQUIPMENT), BR-COST-005 và 016 (INFRA),
BR-COST-006 (UTILITY). Đối chiếu: docs/golden/golden_engine.py `direct_lines`.
"""

from datetime import date
from decimal import Decimal

from normcore.costing import pricing, resources
from normcore.costing.engine import DEPR_EXCLUDED_WARNING, LineRate

ELECTRICITY_UOM = ("kWh", "kwh", "KWH")
WATER_UOM = ("m3", "m³", "M3")


def labor_rate(hourly_rate, source: str) -> LineRate | None:
	"""`hourly_rate` = NC Job Title Rate.rate_per_hour của bộ tham số (BR-COST-001). None → thiếu."""
	if hourly_rate is None:
		return None
	return LineRate(Decimal(str(hourly_rate)), source)


def material_rate(
	prices,
	as_of: date,
	norm_units,
	item_type: str | None,
	reuse_count: int,
	billed_separately: bool,
	labels: dict,
) -> LineRate | None:
	"""BR-COST-003, BR-CLS-002, FR-RES-004, FR-RES-014. None khi không có đơn giá hiệu lực (FR-COST-016)."""
	if billed_separately:
		return LineRate(Decimal(0), pricing.EXCLUDED_REASON, billed_separately=True)
	price = pricing.select_price(prices, as_of)
	if price is None:
		return None
	if not norm_units:
		if item_type in pricing.NORM_ITEM_TYPES:
			return None
		norm_units = 1
	rate = pricing.unit_price_per_norm(price.unit_price, Decimal(str(norm_units)))
	return LineRate(
		rate,
		labels.get(price.name, price.name),
		max(int(reuse_count or 1), 1),
		pricing.price_warnings(price, as_of),
	)


def utility_rate(uom, electricity_price, water_price, param_name: str, material: LineRate | None) -> LineRate | None:
	"""BR-COST-006 (ASM-015-05): kWh lấy giá điện, m³ lấy giá nước của bộ tham số; còn lại như vật chất."""
	if uom in ELECTRICITY_UOM and electricity_price:
		return LineRate(Decimal(str(electricity_price)), f"{param_name} · Giá điện")
	if uom in WATER_UOM and water_price:
		return LineRate(Decimal(str(water_price)), f"{param_name} · Giá nước")
	return material


def room_rate(annual_cost, hours, include_depr: bool, source: str) -> LineRate:
	"""BR-COST-005, BR-COST-016: loại giá không kết cấu khấu hao → 0 kèm cảnh báo."""
	if not include_depr:
		return LineRate(Decimal(0), source, warnings=(DEPR_EXCLUDED_WARNING,))
	return LineRate(resources.room_hourly_rate(annual_cost, hours), source)


def equipment_rate(hourly_rate, include_depr: bool, is_buy: bool, source: str) -> LineRate | None:
	"""BR-COST-004. `hourly_rate` do NCEquipment.indicative(include_depr=…) trả; None → thiếu đơn giá."""
	if hourly_rate is None:
		return None
	warnings = (DEPR_EXCLUDED_WARNING,) if (not include_depr and is_buy) else ()
	return LineRate(Decimal(str(hourly_rate)), source, warnings=warnings)
