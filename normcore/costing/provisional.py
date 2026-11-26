"""Chi phí trực tiếp tạm tính của bộ định mức (FR-NORM-016). Hàm thuần Python (ADR-003).

Chỉ để xem trên lưới định mức; lần tính giá là FEAT-015. Mỗi nhánh dẫn chiếu `direct_lines`
của docs/golden/golden_engine.py. Lượng áp dụng luôn qua engine.applied_qty (BR-COST-007).
"""

from decimal import ROUND_HALF_UP, Decimal

from normcore.costing import engine

_Q2 = Decimal("0.01")
MATERIAL = ("DRUG", "SUPPLY")


def _r2(x: Decimal) -> Decimal:
	return x.quantize(_Q2, rounding=ROUND_HALF_UP)


def line_amount(
	component: str,
	applied_qty,
	rate,
	headcount: int = 1,
	wastage_rate=0,
	reuse_count: int = 1,
) -> Decimal:
	"""Thành tiền một dòng, 2 số lẻ HALF_UP. `wastage_rate` là phân số (Percent ÷ 100).
	LABOR BR-COST-002; DRUG/SUPPLY BR-COST-003; EQUIPMENT BR-COST-004; INFRA BR-COST-005; UTILITY BR-COST-006."""
	q, rate = Decimal(applied_qty), Decimal(rate)
	if q < 0 or rate < 0:
		raise ValueError("Lượng áp dụng và đơn giá không được âm")
	if component == "LABOR":
		return engine.labor_line(q, None, headcount, rate).amount
	if component in MATERIAL:
		wastage = Decimal(wastage_rate)
		if wastage < 0 or reuse_count < 1:
			raise ValueError("Hao hụt không được âm; số lần dùng phải từ 1 trở lên")
		return _r2(q * (1 + wastage) * rate / reuse_count)
	if component in ("EQUIPMENT", "INFRA"):
		return _r2(q / 60 * rate)
	if component == "UTILITY":
		return _r2(q * rate)
	raise ValueError(f"Cấu phần không hợp lệ: {component}")


def summarize(rows) -> dict:
	"""rows: (step_key, component, amount | None, excluded). Dòng loại trừ = 0 (như golden);
	amount None (thiếu đơn giá, chưa liên kết) không cộng và bật `incomplete`."""
	by_sc: dict = {}
	by_c: dict = {}
	total = Decimal("0")
	incomplete = False
	for step_key, component, amount, excluded in rows:
		if excluded:
			amount = Decimal("0")
		elif amount is None:
			incomplete = True
			continue
		by_sc.setdefault(step_key, {})
		by_sc[step_key][component] = by_sc[step_key].get(component, Decimal("0")) + amount
		by_c[component] = by_c.get(component, Decimal("0")) + amount
		total += amount
	return {"by_step_component": by_sc, "by_component": by_c, "total": total, "incomplete": incomplete}
