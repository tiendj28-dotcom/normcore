"""Chọn bản ghi "hiện hành" cho tình trạng chuỗi của dịch vụ (FR-SVC-004, ASM-048, 054).

Module thuần Python, không import khung ngoài. Không có hàm nào nhận hay trả trường tiền.
Dòng vào là dict theo tên trường của DocType nguồn; dòng ra thêm `status` và `date` để hiển thị.
"""

from __future__ import annotations

from datetime import date, datetime

KEYS = ("procedure", "norm_set", "cost", "price")
LABELS = {
	"procedure": "Quy trình hiện hành",
	"norm_set": "Bộ định mức hiện hành",
	"cost": "Giá thành lần tính gần nhất",
	"price": "Giá đã duyệt",
}
DOCTYPES = {"procedure": "NC Clinical Procedure", "norm_set": "NC Norm Set", "cost": "NC Service Cost"}
COSTING_STATUSES = ("Đã tính", "Đã khóa")
NO_PERMISSION = "Không có quyền xem"
EMPTY = "Chưa có"
EMPTY_SCOPED = "Chưa có trong phạm vi khoa của bạn"
NO_PRICE = "Chưa có giá đã duyệt"
PRICE_ANCHOR = "#nc-chain-price"
ASSUMPTION = {"label": "Giả định — chờ xác nhận", "indicator": "yellow"}
INDICATORS = {
	"Đã ban hành": "green",
	"Đã khóa": "green",
	"Đã tính": "blue",
	"Chưa hiệu lực": "yellow",
	"Chưa có": "gray",
	NO_PERMISSION: "gray",
}
CALC_BADGES = {"Lỗi": "red", "Cảnh báo": "yellow"}


def _date(value):
	if value is None or value == "":
		return None
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def _iso(value):
	d = _date(value)
	return d.isoformat() if d else None


def pick_procedures(rows, today):
	"""Mỗi khoa: phiên bản lớn nhất đã tới ngày hiệu lực; không có thì bản lớn nhất, đánh dấu chưa hiệu lực."""
	today = _date(today)
	out = {}
	for dept in {r["department"] for r in rows}:
		mine = [r for r in rows if r["department"] == dept]
		active = [
			r for r in mine if _date(r.get("effective_date")) is None or _date(r["effective_date"]) <= today
		]
		best = max(active or mine, key=lambda r: r["version_no"])
		out[dept] = {
			**best,
			"status": "Đã ban hành",
			"date": _iso(best.get("effective_date")),
			"not_effective": not active,
		}
	return out


def pick_norm_sets(rows):
	"""Mỗi khoa: bộ định mức "Đã khóa" có phiên bản lớn nhất."""
	out = {}
	for r in rows:
		cur = out.get(r["department"])
		if cur is None or r["version_no"] > cur["version_no"]:
			out[r["department"]] = {**r, "status": "Đã khóa", "date": _iso(r.get("locked_on"))}
	return out


def pick_costs(rows):
	"""Mỗi khoa: lần tính "Đã tính"/"Đã khóa", không phải kịch bản, mới nhất theo (ngày tính, ngày tạo)."""
	out = {}
	for r in rows:
		if r.get("based_on_run") or r.get("run_status") not in COSTING_STATUSES:
			continue
		rank = (_iso(r.get("costing_date")) or "", str(r.get("run_creation") or ""))
		cur = out.get(r["department"])
		if cur is None or rank > cur["_rank"]:
			out[r["department"]] = {
				**r,
				"status": r["run_status"],
				"date": _iso(r.get("costing_date")),
				"_rank": rank,
			}
	for r in out.values():
		del r["_rank"]
	return out


def _route(doctype, name):
	return f"/app/{doctype.lower().replace(' ', '-')}/{name}"


def _badge(label, indicator=None):
	return {"label": label, "indicator": indicator or INDICATORS.get(label, "gray")}


def _item(key, state, message="", rows=(), badges=(), links=()):
	return {
		"key": key,
		"label": LABELS[key],
		"state": state,
		"message": message,
		"badges": list(badges),
		"rows": list(rows),
		"links": list(links),
	}


def no_permission_item(key):
	return _item(key, "no_permission", NO_PERMISSION)


def price_item():
	"""Chưa có bảng giá đã duyệt (FEAT-030 thay): luôn rỗng, liên kết tới thẻ trên form."""
	return _item("price", "empty", NO_PRICE, links=[PRICE_ANCHOR])


def _blank_row(dept, names, state, message):
	return {
		"department": dept,
		"department_name": (names or {}).get(dept, dept),
		"state": state,
		"status": message,
		"indicator": "gray",
		"date": None,
		"doctype": None,
		"name": None,
		"route": None,
		"badges": [],
	}


def build_item(key, departments, picked, allowed, names=None):
	"""Một mục tình trạng chuỗi. `allowed`: None = mọi khoa; tập mã khoa = chỉ các khoa đó (ASM-047)."""
	doctype = DOCTYPES[key]
	if allowed is not None and not allowed:
		return no_permission_item(key)
	rows = []
	for dept in departments:
		if allowed is not None and dept not in allowed:
			rows.append(_blank_row(dept, names, "no_permission", NO_PERMISSION))
			continue
		src = picked.get(dept)
		if src is None:
			rows.append(_blank_row(dept, names, "empty", EMPTY))
			continue
		badges = []
		if src.get("not_effective"):
			badges.append(_badge("Chưa hiệu lực"))
		if key == "cost" and src.get("calc_status") in CALC_BADGES:
			badges.append(_badge(src["calc_status"], CALC_BADGES[src["calc_status"]]))
		rows.append(
			{
				**_blank_row(dept, names, "ok", src["status"]),
				"indicator": INDICATORS.get(src["status"], "gray"),
				"date": src.get("date"),
				"doctype": doctype,
				"name": src["name"],
				"route": _route(doctype, src["name"]),
				"badges": badges,
			}
		)
	ok = [r for r in rows if r["state"] == "ok"]
	if ok:
		badges = [ASSUMPTION] if key == "cost" else []
		return _item(key, "ok", rows=rows, badges=badges, links=[r["route"] for r in ok])
	if rows and all(r["state"] == "no_permission" for r in rows):
		return no_permission_item(key)
	return _item(key, "empty", EMPTY if allowed is None else EMPTY_SCOPED, rows=rows)
