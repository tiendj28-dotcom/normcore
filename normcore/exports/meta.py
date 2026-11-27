"""Trang thông tin và chân trang truy vết của mọi tệp xuất (FR-OUT-008). Thuần, không phụ thuộc frappe."""

from openpyxl.styles import Font

INFO_SHEET = "Thông tin xuất"
TEMPLATE_NOTE = "Mẫu biểu: Giả định — chờ xác nhận (TBD-01)"
NO_RUN = "Không gắn lần tính giá"
DASH = "—"


def _fmt(dt, seconds=True):
	if dt is None:
		return ""
	return dt.strftime("%d/%m/%Y %H:%M:%S" if seconds else "%d/%m/%Y %H:%M")


def _parameter_set(meta):
	ps = meta.get("parameter_set")
	if not ps:
		return DASH
	title = meta.get("parameter_set_title")
	return f"{ps} — {title}" if title else ps


def _by(meta):
	name, user = meta.get("exported_by_name"), meta.get("exported_by") or ""
	return f"{name} ({user})" if name else user


def info_rows(meta: dict) -> list[tuple[str, str]]:
	rows = [
		("Loại tệp", meta.get("file_type") or ""),
		("Bản ghi nguồn", meta.get("source") or ""),
		("Mã lần tính giá", meta.get("run") or NO_RUN),
		("Bộ tham số", _parameter_set(meta)),
		("Thời điểm xuất", _fmt(meta.get("exported_at"))),
		("Người xuất", _by(meta)),
	]
	rows.extend((k, v) for k, v in meta.get("extra") or ())
	if meta.get("template_note"):
		rows.append(("Ghi chú mẫu biểu", meta["template_note"]))
	return rows


def footer_text(meta: dict) -> str:
	run = meta.get("run") or NO_RUN
	name = meta.get("exported_by_name") or meta.get("exported_by") or ""
	return (
		f"Lần tính {run} · Bộ tham số {meta.get('parameter_set') or DASH} · "
		f"Xuất {_fmt(meta.get('exported_at'), False)} · {name}"
	)


def add_info_sheet(wb, meta: dict):
	"""Thêm trang cuối `INFO_SHEET`; đặt chân trang cho mọi trang tính."""
	ws = wb.create_sheet(INFO_SHEET)
	for label, value in info_rows(meta):
		ws.append([label, value])
		ws.cell(ws.max_row, 1).font = Font(bold=True)
	ws.column_dimensions["A"].width = 28
	ws.column_dimensions["B"].width = 70
	text = footer_text(meta)
	for sheet in wb.worksheets:
		sheet.oddFooter.center.text = text
