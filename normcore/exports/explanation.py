"""Bảng giải trình PDF (FR-OUT-005). Thuần, không phụ thuộc frappe. Không làm tròn lại số đã lưu."""

from decimal import Decimal

from normcore.exports import meta as meta_mod

MINUS = "−"  # noqa: RUF001 (dấu trừ U+2212, NFR-LOC-001)


def _dec(x):
	return x if isinstance(x, Decimal) else Decimal(str(x))


def _group(s: str) -> str:
	return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt(x, places):
	if x is None or x == "":
		return ""
	d = _dec(x)
	neg = d < 0
	s = _group(f"{abs(d):,.{places}f}")
	return (MINUS if neg else "") + s


def money(x) -> str:
	"""287745.46 -> "287.745,46"; âm dùng dấu trừ U+2212."""
	return _fmt(x, 2)


def money0(x) -> str:
	"""302100 -> "302.100"."""
	return _fmt(x, 0)


def qty(x) -> str:
	"""Lượng: bỏ số 0 thừa ở cuối phần thập phân."""
	if x is None or x == "":
		return ""
	d = _dec(x)
	s = f"{d:f}"
	if "." in s:
		s = s.rstrip("0").rstrip(".")
	neg = s.startswith("-")
	s = s.lstrip("-")
	ip, _, fp = s.partition(".")
	out = _group(f"{int(ip):,}") + ("," + fp if fp else "")
	return (MINUS if neg else "") + out


def _line(ln):
	return {
		"line": ln.get("norm_line_id") or "",
		"resource": ln.get("resource_label") or "",
		"qty": qty(ln.get("applied_qty")),
		"rate": money(ln.get("unit_rate")),
		"amount": money(ln.get("amount")),
		"source": ln.get("rate_source") or "",
		"warning": ln.get("warning") or "",
	}


def pdf_context(expl: dict, meta: dict) -> dict:
	"""Ngữ cảnh Jinja từ kết quả `get_explanation` (giữ thứ tự cấu phần, bước của engine.group_explanation)."""
	h = expl.get("header") or {}
	groups = [
		{
			"label": g["label"],
			"total": money(g["total"]),
			"steps": [
				{
					"label": s["step_label"],
					"total": money(s["total"]),
					"lines": [_line(x) for x in s["lines"]],
				}
				for s in g["steps"]
			],
		}
		for g in expl.get("direct_groups") or ()
	]
	alloc = [
		{
			"component": a.get("component") or "",
			"rule": a.get("allocation_rule") or "",
			"driver": qty(a.get("driver_value")),
			"driver_total": qty(a.get("driver_total")),
			"pool": money(a.get("pool_amount")),
			"amount": money(a.get("amount")),
		}
		for a in expl.get("allocation_lines") or ()
	]
	totals = [
		("Chi phí trực tiếp", money(h.get("direct_total"))),
		("Chi phí phân bổ", money(h.get("alloc_total"))),
		("Giá thành toàn bộ", money(h.get("full_cost"))),
		("Tích lũy", money(h.get("accumulation"))),
		("Nghĩa vụ tài chính", money(h.get("obligation"))),
		("Giá tính toán", money(h.get("calculated_price"))),
		("Giá làm tròn", money0(h.get("rounded_price"))),
	]
	structure = [
		{"label": s["label"], "amount": money(s["amount"]), "share": money(s.get("share_pct"))}
		for s in expl.get("structure") or ()
	]
	pc = expl.get("paraclinical")
	return {
		"header": {
			"service": f"{h.get('service') or ''} — {h.get('service_name') or ''}",
			"department": h.get("department") or "",
			"costing_run": h.get("costing_run") or "",
			"price_category": h.get("price_category") or "",
			"volume": qty(h.get("volume")),
		},
		"direct_groups": groups,
		"allocation_lines": alloc,
		"structure": structure,
		"notes": list(expl.get("notes") or ()),
		"paraclinical": pc,
		"totals": totals,
		"full_cost": money(h.get("full_cost")),
		"info": meta_mod.info_rows(meta),
		"footer": meta_mod.footer_text(meta),
	}
