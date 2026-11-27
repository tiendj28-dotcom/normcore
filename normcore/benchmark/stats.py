"""Thống kê so sánh giá (FEAT-028): logic thuần, không phụ thuộc framework.

FR-ADJ-001..004, 010; BR-ADJ-008. Giả định ASM-028-01..04, 10 (docs/decisions/assumptions/FEAT-028.md).
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from normcore.costing import compare

LABEL_INSUFFICIENT = "Chưa đủ dữ liệu so sánh"
REASON_OUTSIDE_WINDOW = "Ngoài cửa sổ 24 tháng"
REASON_SUPERSEDED = "Cũ hơn giá khác của đơn vị"
REASON_AFTER_DATE = "Sau ngày tính giá"
_Q2 = Decimal("0.01")


def _d(value) -> date:
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def _dec(value) -> Decimal:
	return Decimal(str(value))


def window_start(costing_date, months: int) -> date:
	"""Cùng ngày của `months` tháng trước; ngày không có trong tháng đích thì kẹp về cuối tháng (ASM-028-01)."""
	d = _d(costing_date)
	idx = d.year * 12 + (d.month - 1) - int(months)
	year, month = divmod(idx, 12)
	month += 1
	return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def select_prices(rows, costing_date, months, with_excluded=False):
	"""FR-ADJ-001: mỗi đơn vị một dòng mới nhất trong [window_start, costing_date]; sắp theo giá tăng.

	`with_excluded=True` trả thêm danh sách dòng bị loại kèm lý do.
	"""
	end, start = _d(costing_date), window_start(costing_date, months)
	best, excluded = {}, []
	for r in rows:
		eff = _d(r["effective_date"])
		if eff > end:
			excluded.append({**r, "reason": REASON_AFTER_DATE})
		elif eff < start:
			excluded.append({**r, "reason": REASON_OUTSIDE_WINDOW})
		else:
			cur = best.get(r["facility"])
			# mới hơn thắng; hòa ngày thì `name` nhỏ hơn thắng
			if cur is None or (-eff.toordinal(), r.get("name") or "") < (
				-_d(cur["effective_date"]).toordinal(),
				cur.get("name") or "",
			):
				if cur is not None:
					excluded.append({**cur, "reason": REASON_SUPERSEDED})
				best[r["facility"]] = r
			else:
				excluded.append({**r, "reason": REASON_SUPERSEDED})
	selected = sorted(best.values(), key=lambda r: (_dec(r["price"]), r["facility"]))
	return (selected, excluded) if with_excluded else selected


def filter_rows(rows, provinces=None, levels=None, ownerships=None):
	"""FR-ADJ-004: OR trong một bộ lọc, AND giữa các bộ lọc; bộ lọc rỗng bỏ qua."""
	checks = (("province", provinces), ("facility_level", levels), ("ownership", ownerships))
	out = []
	for r in rows:
		if all(not wanted or r.get(field) in wanted for field, wanted in checks):
			out.append(r)
	return out


def median(values) -> Decimal:
	"""BR-ADJ-008: n lẻ giá trị giữa; n chẵn trung bình hai giá trị giữa, không làm tròn."""
	vals = sorted(_dec(v) for v in values)
	if not vals:
		raise ValueError("Không có giá để tính trung vị")
	mid = len(vals) // 2
	return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def deviation_pct(calc_price, median_price):
	"""BR-ADJ-008: (giá tính toán - trung vị) / trung vị x 100, 2 số lẻ ROUND_HALF_UP (ASM-028-03)."""
	m = _dec(median_price)
	if m == 0:
		return None
	return ((_dec(calc_price) - m) / m * 100).quantize(_Q2, rounding=ROUND_HALF_UP)


def _price_of(row, use_adjusted):
	if use_adjusted:
		adj = (row.get("adjusted") or {}).get("adjusted_price")
		if adj is not None:
			return _dec(adj), False
		return _dec(row["price"]), True
	return _dec(row["price"]), False


def summarize(calc_price, rows, min_facilities, use_adjusted=False):
	"""FR-ADJ-002, 003: thấp nhất, trung vị, cao nhất, độ lệch %; dưới ngưỡng thì chỉ có nhãn."""
	prices, missing = [], 0
	for r in rows:
		p, miss = _price_of(r, use_adjusted)
		prices.append(p)
		missing += miss
	count = len(prices)
	out = {"count": count, "adjusted_missing": missing if use_adjusted else 0}
	if count < int(min_facilities) or count == 0:
		return {
			**out,
			"min": None,
			"median": None,
			"max": None,
			"deviation_pct": None,
			"sufficient": False,
			"label": LABEL_INSUFFICIENT,
		}
	med = median(prices)
	return {
		**out,
		"min": min(prices),
		"median": med,
		"max": max(prices),
		"deviation_pct": deviation_pct(calc_price, med),
		"sufficient": True,
		"label": None,
	}


def exceeds(dev_pct, tolerance) -> bool:
	"""ASM-028-04: vượt ngưỡng khi |độ lệch| > ngưỡng; chưa có độ lệch thì không vượt."""
	if dev_pct is None:
		return False
	return abs(_dec(dev_pct)) > _dec(tolerance)


def breakdown(service_cost) -> dict:
	"""FR-ADJ-010: giá trị và tỷ trọng từng cấu phần trực tiếp, phân bổ trong giá thành toàn bộ (ASM-028-10)."""
	full = service_cost.get("full_cost")
	full_d = _dec(full) if full is not None else None
	rows, total = [], Decimal(0)
	for group, field, label in compare.COMPONENTS:
		if group not in (compare.DIRECT, compare.ALLOC):
			continue
		value = service_cost.get(field)
		if not value and field in compare.OPTIONAL:  # None hoặc 0: không có ngoại kiểm
			continue
		v = _dec(value or 0)
		total += v
		share = (v / full_d * 100).quantize(_Q2, rounding=ROUND_HALF_UP) if full_d else None
		rows.append({"group": group, "field": field, "label": label, "value": v, "share_pct": share})
	return {"rows": rows, "total": total, "full_cost": full_d}
