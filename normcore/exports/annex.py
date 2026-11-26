"""Phụ lục II–V Thông tư 21/2024/TT-BYT (FR-OUT-001..004, NFR-CPL-002). Thuần, không phụ thuộc frappe.

Cấu trúc cột nằm ở MỘT chỗ (các hằng `ANNEX_*_COLUMNS`); tệp mẫu `.xlsx` trong `templates/` được sinh từ
các hằng này và thay được khi có mẫu chính thức (TBD-01, ASM-019-01). Chỉ ghi giá trị đã lưu, không làm tròn lại.
"""

import io
import sys
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from normcore.costing import engine
from normcore.exports import meta as meta_mod

TEMPLATE_DIR = Path(__file__).parent / "templates"
MONEY_FMT = "#,##0.00"
MONEY0_FMT = "#,##0"
ZERO = Decimal(0)

ANNEX_II_COLUMNS = ("STT", "Nội dung chi phí", "Thành tiền (đồng)", "Tỷ trọng (%)", "Ghi chú")
ANNEX_III_COLUMNS = (
	"STT",
	"Mã dịch vụ",
	"Tên dịch vụ",
	"Khoa",
	"Sản lượng",
	"Nhân công",
	"Thuốc và vật tư",
	"Khấu hao",
	"Tiện ích",
	"Quản lý",
	"Giá thành toàn bộ",
	"Ghi chú",
)
ANNEX_IV_COLUMNS = (
	"STT",
	"Nội dung",
	"Loại chi phí",
	"Quy tắc phân bổ",
	"Tiêu chí của dịch vụ",
	"Tổng tiêu chí",
	"Quỹ chi phí",
	"Thành tiền",
)
ANNEX_V_COLUMNS = (
	"STT",
	"Mã dịch vụ",
	"Tên dịch vụ",
	"Mã trên HIS",
	"Khoa",
	"Loại giá",
	"Giá thành toàn bộ",
	"Giá tính toán",
	"Giá đề nghị",
	"Ghi chú",
)

ANNEX = {
	"II": {
		"title": "PHƯƠNG ÁN GIÁ DỊCH VỤ KHÁM BỆNH, CHỮA BỆNH",
		"template": "phu_luc_ii.xlsx",
		"header_row": 6,
		"columns": ANNEX_II_COLUMNS,
		"widths": (8, 44, 20, 14, 40),
	},
	"III": {
		"title": "BẢNG TÍNH GIÁ THÀNH THEO YẾU TỐ CHI PHÍ",
		"template": "phu_luc_iii.xlsx",
		"header_row": 5,
		"columns": ANNEX_III_COLUMNS,
		"widths": (6, 16, 36, 14, 12, 16, 16, 16, 16, 16, 18, 40),
	},
	"IV": {
		"title": "BẢNG TÍNH GIÁ THÀNH THEO PHƯƠNG PHÁP PHÂN BỔ",
		"template": "phu_luc_iv.xlsx",
		"header_row": 5,
		"columns": ANNEX_IV_COLUMNS,
		"widths": (8, 40, 16, 22, 18, 18, 20, 20),
	},
	"V": {
		"title": "DANH MỤC DỊCH VỤ ĐỀ NGHỊ ĐỊNH GIÁ",
		"template": "phu_luc_v.xlsx",
		"header_row": 5,
		"columns": ANNEX_V_COLUMNS,
		"widths": (6, 16, 36, 16, 14, 16, 18, 18, 16, 40),
	},
}

# Phụ lục II: (STT, nội dung, khóa trường hoặc None = tổng nhóm, cấp)
ANNEX_II_ROWS = (
	("I", "Chi phí trực tiếp", "@direct", 0),
	("1", "Nhân công", "direct_labor", 1),
	("2", "Thuốc", "direct_drug", 1),
	("3", "Vật tư", "direct_supply", 1),
	("4", "Thiết bị", "direct_equipment", 1),
	("5", "Hạ tầng", "direct_infra", 1),
	("6", "Tiện ích", "direct_utility", 1),
	("II", "Chi phí phân bổ", "@alloc", 0),
	("1", "Nhân công", "alloc_labor", 1),
	("2", "Thuốc và vật tư", "alloc_drug_supply", 1),
	("3", "Khấu hao", "alloc_depreciation", 1),
	("4", "Tiện ích", "alloc_utility", 1),
	("5", "Quản lý", "alloc_management", 1),
	("III", "Giá thành toàn bộ (I + II)", "full_cost", 0),
	("IV", "Tích lũy", "accumulation", 0),
	("V", "Nghĩa vụ tài chính", "obligation", 0),
	("VI", "Giá tính toán", "calculated_price", 0),
	("VII", "Giá đề nghị (đã làm tròn)", "rounded_price", 0),
)
DIRECT_FIELDS = tuple(k for _, _, k, lv in ANNEX_II_ROWS[:7] if lv == 1)
ALLOC_FIELDS = tuple(k for _, _, k, lv in ANNEX_II_ROWS[7:13] if lv == 1)
PARACLINICAL_NOTE = "Bình quân gia quyền theo hệ thống xét nghiệm"
MISMATCH_TOLERANCE = Decimal("0.01")

# Yếu tố chi phí của Phụ lục III: (nhãn, loại golden, trường trực tiếp, trường phân bổ)
_ELEMENT_DIRECT = {
	"LABOR": ("direct_labor",),
	"DRUG_SUPPLY": ("direct_drug", "direct_supply"),
	"DEPRECIATION": ("direct_equipment", "direct_infra"),
	"UTILITY": ("direct_utility",),
	"MANAGEMENT": (),
}
_ELEMENT_ALLOC = {
	"LABOR": "alloc_labor",
	"DRUG_SUPPLY": "alloc_drug_supply",
	"DEPRECIATION": "alloc_depreciation",
	"UTILITY": "alloc_utility",
	"MANAGEMENT": "alloc_management",
}
ELEMENT_ORDER = ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT")
ELEMENT_LABEL = {
	"LABOR": "Nhân công",
	"DRUG_SUPPLY": "Thuốc và vật tư",
	"DEPRECIATION": "Khấu hao",
	"UTILITY": "Tiện ích",
	"MANAGEMENT": "Quản lý",
}
# Phân loại thành phần golden -> yếu tố, lấy từ engine (không gõ lại, mục 3.2)
for _comp, _cat in engine.COMPONENT_CATEGORY.items():
	_f = "direct_" + {"DRUG": "drug", "SUPPLY": "supply", "EQUIPMENT": "equipment", "INFRA": "infra"}.get(
		_comp, _comp.lower()
	)
	assert _f in _ELEMENT_DIRECT[_cat], (_comp, _cat)


def _d(x) -> Decimal:
	if x is None or x == "":
		return ZERO
	return x if isinstance(x, Decimal) else Decimal(str(x))


def _is_error(svc) -> bool:
	return svc.get("calc_status") == "Lỗi"


def elements(sc: dict) -> dict[str, Decimal]:
	"""Năm yếu tố chi phí = trực tiếp + phân bổ."""
	return {
		k: sum((_d(sc.get(f)) for f in _ELEMENT_DIRECT[k]), ZERO) + _d(sc.get(_ELEMENT_ALLOC[k]))
		for k in ELEMENT_ORDER
	}


def _direct(sc):
	return sum((_d(sc.get(f)) for f in DIRECT_FIELDS), ZERO)


def _alloc(sc):
	return sum((_d(sc.get(f)) for f in ALLOC_FIELDS), ZERO)


def _share(value, full):
	return None if not full else (value / full * 100).quantize(Decimal("0.01"))


def annex_rows_ii(svc: dict) -> list[list]:
	"""[STT, nội dung, thành tiền, tỷ trọng %, ghi chú]."""
	full = _d(svc.get("full_cost"))
	paraclinical = bool(svc.get("is_paraclinical"))
	eqa = _d(svc.get("eqa_cost"))
	rows = []
	for stt, label, key, level in ANNEX_II_ROWS:
		if key == "@direct":
			value = _direct(svc)
		elif key == "@alloc":
			value = _alloc(svc)
		else:
			value = _d(svc.get(key))
		share = _share(value, full) if key in ("@direct", "@alloc") or level == 1 else None
		note = ""
		if key == "@direct" and paraclinical:
			note = PARACLINICAL_NOTE
		if key == "full_cost":
			diff = _direct(svc) + _alloc(svc) - full
			if abs(diff) > MISMATCH_TOLERANCE:
				note = f"Lệch {diff:,.2f} so với tổng cấu phần"
		rows.append([stt, label, value, share, note])
		if key == "direct_utility" and eqa:
			rows.append(["7", "Ngoại kiểm", eqa, _share(eqa, full), ""])
	return rows


def annex_rows_iii(svc: dict) -> list:
	"""[mã, tên, khoa, sản lượng, 5 yếu tố…, giá thành toàn bộ, ghi chú] (chưa có STT)."""
	el = elements(svc)
	full = _d(svc.get("full_cost"))
	note = ""
	diff = sum(el.values(), ZERO) - full
	if abs(diff) > MISMATCH_TOLERANCE:
		note = f"Chênh {diff:,.2f} với giá thành toàn bộ: chi phí ngoại kiểm"
	return [
		svc.get("service_code"),
		svc.get("service_name"),
		svc.get("department"),
		svc.get("volume"),
		*[el[k] for k in ELEMENT_ORDER],
		full,
		note,
	]


def annex_rows_iv(svc: dict) -> list[list]:
	"""Một khối: tiêu đề, trực tiếp, các dòng phân bổ, giá thành. Dòng = 8 cột ANNEX_IV_COLUMNS (STT đặt sau)."""
	head = f"{svc.get('service_code')} — {svc.get('service_name')} ({svc.get('department')}, SL {svc.get('volume')})"
	rows = [["", head, "", "", "", "", "", ""]]
	rows.append(["", "Chi phí trực tiếp", "Trực tiếp", "", "", "", "", _direct(svc)])
	alloc = svc.get("alloc_lines") or []
	if not alloc:
		rows.append(["", "Không có chi phí phân bổ", "", "", "", "", "", ""])
	for ln in alloc:
		rows.append(
			[
				"",
				ln.get("component"),
				"Phân bổ",
				ln.get("allocation_rule"),
				ln.get("driver_value"),
				ln.get("driver_total"),
				ln.get("pool_amount"),
				_d(ln.get("amount")),
			]
		)
	rows.append(["", "Giá thành toàn bộ", "", "", "", "", "", _d(svc.get("full_cost"))])
	return rows


def annex_row_v(svc: dict) -> list:
	"""[mã, tên, mã HIS, khoa, loại giá, giá thành, giá tính toán, giá đề nghị, ghi chú] (chưa có STT)."""
	err = _is_error(svc)
	note = ""
	if err:
		note = f"Tính lỗi: {svc.get('calc_message') or ''}"
	elif svc.get("calc_status") == "Cảnh báo":
		note = svc.get("calc_message") or ""
	price = lambda k: None if err else _d(svc.get(k))  # noqa: E731
	return [
		svc.get("service_code"),
		svc.get("service_name"),
		svc.get("his_code") or "",
		svc.get("department"),
		svc.get("price_category") or "",
		price("full_cost"),
		price("calculated_price"),
		price("rounded_price"),
		note,
	]


# ---------------- Mẫu ----------------


def template_path(code: str) -> Path:
	return TEMPLATE_DIR / ANNEX[code]["template"]


def make_template(code: str) -> Workbook:
	spec = ANNEX[code]
	wb = Workbook()
	ws = wb.active
	ws.title = f"Phụ lục {code}"
	ws["A1"] = ""  # tên đơn vị, bệnh viện điền
	ws["A2"] = f"Phụ lục {code} — Thông tư 21/2024/TT-BYT"
	ws["A3"] = spec["title"]
	ws["A4"] = ""  # dòng "Lần tính giá … · Ngày tính giá … · Loại giá …"
	for c, name in enumerate(spec["columns"], 1):
		cell = ws.cell(spec["header_row"], c, name)
		cell.font = Font(bold=True)
	for c, w in enumerate(spec["widths"], 1):
		ws.column_dimensions[ws.cell(1, c).column_letter].width = w
	ws["A2"].font = Font(bold=True)
	ws["A3"].font = Font(bold=True, size=12)
	return wb


def load_template(code: str) -> Workbook:
	p = template_path(code)
	return load_workbook(p) if p.exists() else make_template(code)


def header_of(ws, code: str) -> tuple:
	row = ANNEX[code]["header_row"]
	return tuple(ws.cell(row, c).value for c in range(1, len(ANNEX[code]["columns"]) + 1))


def write_templates():
	TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
	for code in ANNEX:
		make_template(code).save(template_path(code))


# ---------------- Dựng tệp ----------------


def _sorted_services(data, include_errors):
	rows = [s for s in data.get("services") or () if include_errors or not _is_error(s)]
	return sorted(rows, key=lambda s: (s.get("service_code") or "", s.get("department") or ""))


def _run_line(data):
	run = data.get("run") or {}
	cd = run.get("costing_date")
	cd = cd.strftime("%d/%m/%Y") if hasattr(cd, "strftime") else (cd or "")
	return f"Lần tính giá {run.get('name') or ''} · Ngày tính giá {cd} · Loại giá {run.get('price_category') or ''}"


def _sheet_name(base, used):
	name = (base or "Dịch vụ")[:31]
	for ch in '[]:*?/\\':
		name = name.replace(ch, "-")
	cand, n = name, 2
	while cand.lower() in used:
		suffix = f"-{n}"
		cand = name[: 31 - len(suffix)] + suffix
		n += 1
	used.add(cand.lower())
	return cand


def _fill_header(ws, data):
	ws["A1"] = data.get("unit") or ""
	ws["A4"] = _run_line(data)


def _finish(wb, code, data, errors):
	m = dict(data.get("meta") or {})
	m["template_note"] = meta_mod.TEMPLATE_NOTE
	if errors:
		m["extra"] = list(m.get("extra") or ()) + [
			("Dịch vụ tính lỗi, không xuất", ", ".join(s.get("service_code") or "" for s in errors))
		]
	meta_mod.add_info_sheet(wb, m)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def _put(ws, row, values, money_cols=(), money0_cols=()):
	for c, v in enumerate(values, 1):
		cell = ws.cell(row, c, v)
		if c in money_cols and v is not None and v != "":
			cell.number_format = MONEY_FMT
		if c in money0_cols and v is not None and v != "":
			cell.number_format = MONEY0_FMT


def _errors(data):
	return [s for s in _sorted_services(data, True) if _is_error(s)]


def build_annex_ii(data: dict) -> bytes:
	wb = load_template("II")
	tmpl = wb.active
	spec = ANNEX["II"]
	used: set = set()
	services = _sorted_services(data, False)
	for svc in services:
		ws = wb.copy_worksheet(tmpl)
		ws.title = _sheet_name(svc.get("service_code"), used)
		_fill_header(ws, data)
		ws["A5"] = (
			f"Mã dịch vụ: {svc.get('service_code')} · Tên dịch vụ: {svc.get('service_name')} · "
			f"Khoa: {svc.get('department')} · Sản lượng: {svc.get('volume')}"
		)
		r = spec["header_row"] + 1
		for row in annex_rows_ii(svc):
			_put(ws, r, row, money_cols=(3, 4))
			if row[0] in ("I", "II", "III", "IV", "V", "VI", "VII"):
				for c in range(1, 4):
					ws.cell(r, c).font = Font(bold=True)
			r += 1
	if services or len(wb.sheetnames) > 1:
		wb.remove(tmpl)
	return _finish(wb, "II", data, _errors(data))


def build_annex_iii(data: dict) -> bytes:
	wb = load_template("III")
	ws = wb.active
	_fill_header(ws, data)
	r = ANNEX["III"]["header_row"] + 1
	for i, svc in enumerate(_sorted_services(data, False), 1):
		row = annex_rows_iii(svc)
		_put(ws, r, [i, *row], money_cols=(6, 7, 8, 9, 10, 11))
		r += 1
	return _finish(wb, "III", data, _errors(data))


def build_annex_iv(data: dict) -> bytes:
	wb = load_template("IV")
	ws = wb.active
	_fill_header(ws, data)
	r = ANNEX["IV"]["header_row"] + 1
	for i, svc in enumerate(_sorted_services(data, False), 1):
		for j, row in enumerate(annex_rows_iv(svc)):
			if j == 0:
				row = [i, *row[1:]]
				ws.cell(r, 2).font = Font(bold=True)
			_put(ws, r, row, money_cols=(5, 6, 7, 8))
			if j == 0:
				ws.cell(r, 2).font = Font(bold=True)
			r += 1
	return _finish(wb, "IV", data, _errors(data))


def build_annex_v(data: dict) -> bytes:
	wb = load_template("V")
	ws = wb.active
	_fill_header(ws, data)
	r = ANNEX["V"]["header_row"] + 1
	for i, svc in enumerate(_sorted_services(data, True), 1):
		row = annex_row_v(svc)
		_put(ws, r, [i, *row], money_cols=(7, 8), money0_cols=(9,))
		r += 1
	return _finish(wb, "V", data, [])


if __name__ == "__main__":
	if "--write-templates" in sys.argv:
		write_templates()
		print("Đã ghi", ", ".join(ANNEX[c]["template"] for c in ANNEX))
