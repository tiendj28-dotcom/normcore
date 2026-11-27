"""FEAT-026 T07: phiếu khảo sát giá theo Phụ lục I (FR-BM-008, ASM-026-10). Thuần, không cần site."""

import io
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from openpyxl import load_workbook

from normcore.core.import_sets import NC_BENCHMARK_PRICE
from normcore.core.importer import header_label
from normcore.exports import price_survey as ps

FACILITY = {
	"facility_name": "BV Khảo sát",
	"province": "Hà Nội",
	"ownership": "Công lập",
	"facility_level": "Hạng I",
}
SERVICES = [
	{"name": "DV-002", "service_name": "Siêu âm ổ bụng"},
	{"name": "DV-001", "service_name": "Định lượng Glucose"},
]
META = {
	"price_category": "LG-01",
	"group": "Xét nghiệm",
	"author": "Nguyễn Văn A",
	"created": date(2026, 5, 20),
}


def _wb(**kw):
	args = {"facility": FACILITY, "services": SERVICES, "price_category": "LG-01", "meta": META}
	args.update(kw)
	return load_workbook(io.BytesIO(ps.build_survey(**args)))


class TestPriceSurvey(unittest.TestCase):
	def test_FR_BM_008_cot_trung_bo_nhap(self):
		labels = [header_label(c) for c in NC_BENCHMARK_PRICE.columns]
		assert list(ps.SURVEY_COLUMNS) == labels

	def test_FR_BM_008_phieu_khao_sat(self):
		wb = _wb()
		ws = wb.worksheets[0]
		assert tuple(c.value for c in ws[1]) == ps.SURVEY_COLUMNS
		rows = [[c.value for c in r] for r in ws.iter_rows(min_row=2)]
		assert len(rows) == 2
		# sắp theo mã; điền sẵn đơn vị, mã, tên, loại giá; giá, ngày, nguồn để trống
		assert [r[1] for r in rows] == ["DV-001", "DV-002"]
		assert rows[0][0] == "BV Khảo sát" and rows[0][2] == "Định lượng Glucose" and rows[0][4] == "LG-01"
		assert rows[0][3] is None and rows[0][5] is None and rows[0][6] is None

	def test_FR_BM_008_to_thong_tin_phieu(self):
		wb = _wb()
		assert len(wb.worksheets) == 2
		info = {r[0].value: r[1].value for r in wb.worksheets[1].iter_rows(min_row=1) if r[0].value}
		assert info["Đơn vị được khảo sát"] == "BV Khảo sát"
		assert info["Tỉnh, thành phố"] == "Hà Nội"
		assert info["Nhóm dịch vụ"] == "Xét nghiệm"
		assert info["Người lập"] == "Nguyễn Văn A"
		assert info["Ngày lập"] == "20/05/2026"
		assert "TBD-01" in info["Ghi chú"] and "Phụ lục I" in info["Ghi chú"]

	def test_FR_BM_008_khong_co_mau_thi_dung_tu_hang(self):
		with (
			tempfile.TemporaryDirectory() as d,
			mock.patch.object(ps, "TEMPLATE_PATH", Path(d) / "khong-co.xlsx"),
		):
			wb = _wb()
		assert tuple(c.value for c in wb.worksheets[0][1]) == ps.SURVEY_COLUMNS

	def test_FR_BM_008_mau_thay_duoc(self):
		with tempfile.TemporaryDirectory() as d:
			tpl = Path(d) / "mau.xlsx"
			ps.make_template().save(tpl)
			wb = load_workbook(tpl)
			wb.worksheets[0].title = "Mẫu chính thức"
			wb.save(tpl)
			with mock.patch.object(ps, "TEMPLATE_PATH", tpl):
				assert _wb().worksheets[0].title == "Mẫu chính thức"

	def test_FR_BM_008_mau_trong_repo_dung_cau_truc(self):
		assert ps.TEMPLATE_PATH.exists()
		wb = load_workbook(ps.TEMPLATE_PATH)
		assert tuple(c.value for c in wb.worksheets[0][1]) == ps.SURVEY_COLUMNS
