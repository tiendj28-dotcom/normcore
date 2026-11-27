"""FEAT-030 T06: bảng so sánh giá (FR-OUT-007), logic dựng tệp thuần."""

import io
from datetime import date, datetime
from decimal import Decimal

from openpyxl import load_workbook

from normcore.exports import meta as meta_mod
from normcore.exports import price_comparison as pc

META = {
	"run": "TG-2026-001",
	"parameter_set": "BTS-1",
	"parameter_set_title": "Bộ vàng",
	"exported_at": datetime(2026, 11, 27, 10, 0, 0),
	"exported_by": "fin@x",
	"exported_by_name": "Tài chính",
	"file_type": "Bảng so sánh giá",
	"source": "NC Costing Run TG-2026-001",
}


def _data(proposal=None):
	return {
		"proposal": proposal,
		"services": [
			{
				"service_code": "DV-TEST-A",
				"service_name": "Dịch vụ A",
				"department": "KHOA-TEST",
				"calculated_price": Decimal("301950.00"),
				"rounded_price": Decimal("302100"),
				"proposed_price": Decimal("295000"),
				"count": 3,
				"min": Decimal("280000"),
				"median": Decimal("300000"),
				"max": Decimal("320000"),
				"deviation_pct": Decimal("0.65"),
				"label": None,
			},
			{
				"service_code": "DV-TEST-B",
				"service_name": "Dịch vụ B",
				"department": "KHOA-TEST",
				"calculated_price": Decimal("92500"),
				"rounded_price": Decimal("92600"),
				"proposed_price": Decimal("92600"),
				"count": 1,
				"min": None,
				"median": None,
				"max": None,
				"deviation_pct": None,
				"label": "Chưa đủ dữ liệu so sánh",
			},
		],
		"prices": [
			{
				"service_code": "DV-TEST-A",
				"service_name": "Dịch vụ A",
				"facility_name": "BV Một",
				"province": "Hà Nội",
				"facility_level": "Hạng I",
				"ownership": "Công lập",
				"price_category": "PC-GOLD",
				"price": Decimal("300000"),
				"effective_date": date(2026, 6, 1),
				"source_doc_no": "QD-12",
				"source_url": None,
			},
			{
				"service_code": "DV-TEST-A",
				"service_name": "Dịch vụ A",
				"facility_name": "BV Hai",
				"price_category": "PC-GOLD",
				"price": Decimal("280000"),
				"effective_date": "2026-05-01",
				"source_doc_no": None,
				"source_url": "https://x.vn/g",
			},
		],
	}


def _wb(data):
	return load_workbook(io.BytesIO(pc.build_workbook(data, META)))


def test_TC_OUT_05_cot_va_du_lieu_tu_lan_tinh():
	wb = _wb(_data())
	assert wb.sheetnames == [pc.SUMMARY_SHEET, pc.PRICES_SHEET, meta_mod.INFO_SHEET]
	ws = wb[pc.SUMMARY_SHEET]
	assert [c.value for c in ws[1]] == list(pc.summary_columns(False))
	assert pc.PROPOSED_COLUMN not in [c.value for c in ws[1]]
	a, b = ws[2], ws[3]
	assert a[0].value == "DV-TEST-A"
	assert [c.value for c in a[4:10]] == [302100.0, 3, 280000.0, 300000.0, 320000.0, 0.65]
	assert a[10].value in (None, "")
	assert all(b[i].value is None for i in (6, 7, 8, 9))  # chưa đủ đơn vị: không có thống kê
	assert b[10].value == "Chưa đủ dữ liệu so sánh"
	wp = wb[pc.PRICES_SHEET]
	assert [c.value for c in wp[1]] == list(pc.PRICE_COLUMNS)
	assert [c.value for c in wp[2]][2:] == ["BV Một", "Hà Nội", "Hạng I", "Công lập", "PC-GOLD", 300000.0, datetime(2026, 6, 1), "QD-12"]
	assert wp.cell(3, 10).value == "https://x.vn/g"  # nguồn: link khi không có số văn bản
	assert wp.cell(3, 9).value == datetime(2026, 5, 1)


def test_TC_OUT_05_nguon_phuong_an_co_cot_gia_de_xuat_va_thong_tin():
	wb = _wb(_data({"name": "PAG-2026-001", "title": "Phương án thử"}))
	ws = wb[pc.SUMMARY_SHEET]
	header = [c.value for c in ws[1]]
	assert header == list(pc.summary_columns(True))
	assert ws.cell(2, header.index(pc.PROPOSED_COLUMN) + 1).value == 295000.0
	info = {r[0].value: r[1].value for r in wb[meta_mod.INFO_SHEET].iter_rows()}
	assert info["Mã lần tính giá"] == "TG-2026-001"
	assert "PAG-2026-001" in info["Phương án giá"]
	for sheet in wb.worksheets:
		assert "TG-2026-001" in sheet.oddFooter.center.text


def test_dinh_dang_tien_ngay():
	wb = _wb(_data())
	assert wb[pc.SUMMARY_SHEET].cell(2, 4).number_format == pc.MONEY_FMT
	assert wb[pc.PRICES_SHEET].cell(2, 9).number_format == pc.DATE_FMT


def test_khong_co_gia_tham_chieu_van_xuat_duoc():
	d = _data()
	d["prices"] = []
	wb = _wb(d)
	assert wb[pc.PRICES_SHEET].max_row == 1
