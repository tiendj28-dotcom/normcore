"""Phiếu khảo sát giá theo Phụ lục I Thông tư 21/2024/TT-BYT (FR-BM-008). Thuần, không phụ thuộc frappe.

Mẫu biểu chính thức chưa có (TBD-01, ASM-026-10): cấu trúc là giả định. Tờ 1 có cột trùng nhãn bộ nhập
`nc_benchmark_price` để tệp điền xong nhập lại được (UC-013 1a). Tệp `templates/phu_luc_i.xlsx` thay được.
"""

import io
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from normcore.core.import_sets import NC_BENCHMARK_PRICE
from normcore.core.importer import header_label

TEMPLATE_PATH = Path(__file__).parent / "templates" / "phu_luc_i.xlsx"
SURVEY_COLUMNS = tuple(header_label(c) for c in NC_BENCHMARK_PRICE.columns)
SURVEY_SHEET = "Phiếu khảo sát"
INFO_SHEET = "Thông tin phiếu"
SURVEY_NOTE = "Cấu trúc theo Phụ lục I Thông tư 21/2024/TT-BYT — Giả định, chờ xác nhận (TBD-01)"
WIDTHS = (28, 16, 40, 16, 16, 16, 22, 30)

# Nhãn của tờ "Thông tin phiếu"; giá trị do `_info_rows` điền
INFO_LABELS = (
	"Đơn vị được khảo sát",
	"Tỉnh, thành phố",
	"Loại hình",
	"Hạng hoặc cấp chuyên môn",
	"Nhóm dịch vụ",
	"Loại giá",
	"Người lập",
	"Ngày lập",
	"Hạn gửi lại",
	"Ghi chú",
)


def make_template() -> Workbook:
	"""Mẫu dựng từ hằng: tờ 1 chỉ có dòng tiêu đề cột, tờ 2 có nhãn thông tin."""
	wb = Workbook()
	ws = wb.active
	ws.title = SURVEY_SHEET
	for c, name in enumerate(SURVEY_COLUMNS, 1):
		ws.cell(1, c, name).font = Font(bold=True)
		ws.column_dimensions[ws.cell(1, c).column_letter].width = WIDTHS[c - 1]
	ws.freeze_panes = "A2"
	info = wb.create_sheet(INFO_SHEET)
	for r, label in enumerate(INFO_LABELS, 1):
		info.cell(r, 1, label).font = Font(bold=True)
	info.column_dimensions["A"].width = 28
	info.column_dimensions["B"].width = 60
	return wb


def write_template():
	TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
	make_template().save(TEMPLATE_PATH)


def _fmt_date(d):
	if isinstance(d, datetime | date):
		return d.strftime("%d/%m/%Y")
	return d or ""


def _info_rows(facility, price_category, meta):
	return {
		"Đơn vị được khảo sát": facility.get("facility_name"),
		"Tỉnh, thành phố": facility.get("province"),
		"Loại hình": facility.get("ownership"),
		"Hạng hoặc cấp chuyên môn": facility.get("facility_level"),
		"Nhóm dịch vụ": meta.get("group") or "",
		"Loại giá": price_category or "",
		"Người lập": meta.get("author") or "",
		"Ngày lập": _fmt_date(meta.get("created")),
		"Hạn gửi lại": "",
		"Ghi chú": SURVEY_NOTE,
	}


def build_survey(facility: dict, services: list, price_category, meta: dict | None = None) -> bytes:
	"""Phiếu khảo sát `.xlsx`: mỗi dịch vụ một dòng (theo mã), Giá, Ngày hiệu lực, Nguồn để trống."""
	meta = meta or {}
	wb = load_workbook(TEMPLATE_PATH) if TEMPLATE_PATH.exists() else make_template()
	ws = wb.worksheets[0]
	ws.delete_rows(2, ws.max_row)
	for r, svc in enumerate(sorted(services, key=lambda s: s["name"]), 2):
		row = {
			"facility": facility.get("facility_name"),
			"technical_service": svc["name"],
			"service_name_raw": svc.get("service_name"),
			"price_category": price_category,
		}
		for c, col in enumerate(NC_BENCHMARK_PRICE.columns, 1):
			ws.cell(r, c, row.get(col.fieldname))
	info_ws = wb[INFO_SHEET] if INFO_SHEET in wb.sheetnames else wb.create_sheet(INFO_SHEET)
	values = _info_rows(facility, price_category, meta)
	for r, label in enumerate(INFO_LABELS, 1):
		info_ws.cell(r, 1, label).font = Font(bold=True)
		info_ws.cell(r, 2, values[label])
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()
