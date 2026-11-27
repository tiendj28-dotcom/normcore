"""Bảng so sánh giá (FR-OUT-007; TC-OUT-05). Thuần, không phụ thuộc frappe.

Hai trang: "Tổng hợp" (giá của bệnh viện và thống kê so sánh theo dịch vụ) và "Giá tham chiếu" (từng đơn vị, giá,
ngày hiệu lực, nguồn). Trang thông tin và chân trang theo `exports/meta.py`. Chỉ ghi giá trị đã lưu (ASM-030-13, 14).
"""

import io
from datetime import date, datetime

from openpyxl import Workbook
from openpyxl.styles import Font

from normcore.exports import meta as meta_mod

SUMMARY_SHEET = "Tổng hợp"
PRICES_SHEET = "Giá tham chiếu"
MONEY_FMT = "#,##0.00"
PCT_FMT = "0.00"
DATE_FMT = "dd/mm/yyyy"
INSUFFICIENT_NOTE = "Chưa đủ dữ liệu so sánh"

BASE_COLUMNS = ("Mã dịch vụ", "Tên dịch vụ", "Khoa", "Giá tính toán", "Giá làm tròn")
PROPOSED_COLUMN = "Giá đề xuất"
STAT_COLUMNS = ("Số đơn vị", "Thấp nhất", "Trung vị", "Cao nhất", "Độ lệch (%)", "Ghi chú")
PRICE_COLUMNS = (
	"Mã dịch vụ",
	"Tên dịch vụ",
	"Đơn vị tham chiếu",
	"Tỉnh, thành phố",
	"Hạng",
	"Loại hình",
	"Loại giá",
	"Giá",
	"Ngày hiệu lực",
	"Nguồn",
)


def summary_columns(with_proposed: bool) -> tuple:
	return BASE_COLUMNS + ((PROPOSED_COLUMN,) if with_proposed else ()) + STAT_COLUMNS


def _date(value):
	if value is None or value == "":
		return None
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def _num(value):
	return None if value is None else float(value)


def summary_rows(data: dict) -> list[list]:
	with_proposed = bool(data.get("proposal"))
	rows = []
	for s in data["services"]:
		row = [
			s["service_code"],
			s.get("service_name") or s["service_code"],
			s.get("department") or "",
			_num(s.get("calculated_price")),
			_num(s.get("rounded_price")),
		]
		if with_proposed:
			row.append(_num(s.get("proposed_price")))
		count = s.get("count") or 0
		sufficient = s.get("median") is not None
		row += [
			count,
			_num(s.get("min")),
			_num(s.get("median")),
			_num(s.get("max")),
			_num(s.get("deviation_pct")),
			"" if sufficient else (s.get("label") or INSUFFICIENT_NOTE),
		]
		rows.append(row)
	return rows


def price_rows(data: dict) -> list[list]:
	return [
		[
			p["service_code"],
			p.get("service_name") or p["service_code"],
			p.get("facility_name") or p.get("facility") or "",
			p.get("province") or "",
			p.get("facility_level") or "",
			p.get("ownership") or "",
			p.get("price_category") or "",
			_num(p.get("price")),
			_date(p.get("effective_date")),
			p.get("source_doc_no") or p.get("source_url") or "",
		]
		for p in data["prices"]
	]


def _write(ws, columns, rows, money_cols=(), pct_cols=(), date_cols=(), widths=()):
	ws.append(list(columns))
	for c in range(1, len(columns) + 1):
		ws.cell(1, c).font = Font(bold=True)
	for r in rows:
		ws.append(r)
	for row in ws.iter_rows(min_row=2):
		for cell in row:
			if cell.column in money_cols and cell.value is not None:
				cell.number_format = MONEY_FMT
			elif cell.column in pct_cols and cell.value is not None:
				cell.number_format = PCT_FMT
			elif cell.column in date_cols and cell.value is not None:
				cell.number_format = DATE_FMT
	for i, w in enumerate(widths, 1):
		ws.column_dimensions[ws.cell(1, i).column_letter].width = w
	ws.freeze_panes = "A2"


def build_workbook(data: dict, meta: dict) -> bytes:
	"""`data`: {"proposal": {"name","title"} | None, "services": [...], "prices": [...]}; trả nội dung xlsx."""
	with_proposed = bool(data.get("proposal"))
	meta = dict(meta)
	if with_proposed:
		label = f"{data['proposal']['name']} — {data['proposal'].get('title') or ''}"
		meta["extra"] = [*(meta.get("extra") or ()), ("Phương án giá", label)]
	wb = Workbook()
	ws = wb.active
	ws.title = SUMMARY_SHEET
	cols = summary_columns(with_proposed)
	n_base = len(BASE_COLUMNS) + (1 if with_proposed else 0)
	money = set(range(4, n_base + 1)) | {n_base + 2, n_base + 3, n_base + 4}
	_write(
		ws,
		cols,
		summary_rows(data),
		money_cols=money,
		pct_cols={n_base + 5},
		widths=(16, 36, 16, 18, 18) + ((18,) if with_proposed else ()) + (10, 18, 18, 18, 12, 28),
	)
	wp = wb.create_sheet(PRICES_SHEET)
	_write(
		wp,
		PRICE_COLUMNS,
		price_rows(data),
		money_cols={8},
		date_cols={9},
		widths=(16, 36, 36, 18, 14, 16, 16, 18, 16, 30),
	)
	meta_mod.add_info_sheet(wb, meta)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()
