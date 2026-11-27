"""FEAT-026 T01: logic thuần của kho giá tham chiếu (không import frappe)."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from normcore.benchmark import reference as ref

SERVICES = [
	{"name": "DV-002", "service_name": "Định lượng Glucose máu"},
	{"name": "DV-001", "service_name": "Định lượng Glucose máu"},
	{"name": "DV-003", "service_name": "Siêu âm ổ bụng tổng quát"},
]


def test_TC_BM_04_gia_hieu_chinh():
	# TC-BM-04 / BR-ADJ-009: 200.000 x 104 / 100 = 208.000
	assert ref.adjusted_price(200000, 100, 104) == Decimal("208000.00")


def test_adjusted_price_lam_tron_half_up():
	# 100 x 101 / 3 = 3366.666... -> 3366.67 ; 1 x 1 / 8 = 0.125 -> 0.13
	assert ref.adjusted_price(100, 3, 101) == Decimal("3366.67")
	assert ref.adjusted_price(1, 8, 1) == Decimal("0.13")


@pytest.mark.parametrize("eff,tgt", [(0, 104), (-1, 104), (None, 104), (100, 0), (100, None)])
def test_adjusted_price_chi_so_khong_hop_le(eff, tgt):
	with pytest.raises(ValueError):
		ref.adjusted_price(200000, eff, tgt)


def test_month_start():
	assert ref.month_start(date(2026, 3, 17)) == date(2026, 3, 1)
	assert ref.month_start(datetime(2026, 3, 17, 9, 0)) == date(2026, 3, 1)
	assert ref.month_start("2026-03-17") == date(2026, 3, 1)


def test_adjust_du_chi_so():
	row = {"price": 200000, "effective_date": "2026-01-15"}
	cpi = {date(2026, 1, 1): 100.0, date(2026, 4, 1): 104.0}
	out = ref.adjust(row, cpi, date(2026, 4, 20))
	assert out["adjusted_price"] == Decimal("208000.00")
	assert out["index_effective"] == 100.0
	assert out["index_target"] == 104.0
	assert out["target_month"] == date(2026, 4, 1)


def test_FR_BM_006_thieu_chi_so():
	row = {"price": 200000, "effective_date": "2026-01-15"}
	out = ref.adjust(row, {date(2026, 4, 1): 104.0}, date(2026, 4, 1))
	assert out["adjusted_price"] is None
	assert out["missing"] == [date(2026, 1, 1)]
	out = ref.adjust(row, {}, date(2026, 4, 1))
	assert out["missing"] == [date(2026, 1, 1), date(2026, 4, 1)]
	# chỉ số bằng 0 coi như thiếu
	out = ref.adjust(row, {date(2026, 1, 1): 0, date(2026, 4, 1): 104.0}, date(2026, 4, 1))
	assert out["adjusted_price"] is None and out["missing"] == [date(2026, 1, 1)]


def test_FR_BM_004_so_khop_ten():
	assert ref.normalize_name(None) == ""
	assert ref.normalize_name("  Định-lượng  GLUCOSE, máu! ") == "dinh luong glucose mau"
	# trùng hệt sau chuẩn hóa; hòa điểm lấy mã nhỏ nhất
	assert ref.suggest_service("DINH LUONG glucose mau", SERVICES) == "DV-001"
	# Jaccard: 3/4 từ chung = 0.75
	assert ref.suggest_service("Định lượng Glucose", SERVICES) == "DV-001"
	# dưới ngưỡng
	assert ref.suggest_service("Chụp X-quang phổi", SERVICES) is None
	assert ref.suggest_service("", SERVICES) is None
	assert ref.suggest_service("Glucose", []) is None
	# dịch vụ không có tên bị bỏ qua
	assert ref.suggest_service("abc", [{"name": "X", "service_name": None}]) is None


def test_initial_status():
	assert ref.initial_status(False, False, False) == ref.STATUS_PROPOSED
	assert ref.initial_status(True, False, False) == ref.STATUS_CONFIRMED
	assert ref.initial_status(True, True, False) == ref.STATUS_PROPOSED
	assert ref.initial_status(True, False, True) == ref.STATUS_PROPOSED


def test_initial_status_tat_cau_hinh(monkeypatch):
	monkeypatch.setattr(ref, "CONFIRM_CODED_ROWS", False)
	assert ref.initial_status(True, False, False) == ref.STATUS_PROPOSED


def _row(**kw):
	base = {
		"name": "A",
		"facility": "F",
		"price_category": "PC",
		"effective_date": "2026-01-01",
		"technical_service": "DV-001",
		"service_name_raw": "Glucose",
		"status": ref.STATUS_PROPOSED,
	}
	base.update(kw)
	return base


def test_FR_BM_007_khoa_trung():
	a = _row()
	assert ref.duplicate_key_matches(a, _row(name="B"))
	# khác mã nhưng cùng tên gốc chuẩn hóa -> trùng
	assert ref.duplicate_key_matches(
		_row(technical_service=None, service_name_raw="GLUCOSE"),
		_row(technical_service="DV-009", service_name_raw="glucose"),
	)
	# khác mã, khác tên
	assert not ref.duplicate_key_matches(a, _row(technical_service="DV-002", service_name_raw="Khác"))
	# khác facility/loại giá/ngày
	assert not ref.duplicate_key_matches(a, _row(facility="G"))
	assert not ref.duplicate_key_matches(a, _row(price_category="X"))
	assert not ref.duplicate_key_matches(a, _row(effective_date="2026-02-01"))
	# ngày dạng date và chuỗi coi như bằng
	assert ref.duplicate_key_matches(a, _row(effective_date=date(2026, 1, 1)))


def test_FR_BM_007_find_duplicate():
	cands = [_row(name="B", status=ref.STATUS_REJECTED), _row(name="A"), _row(name="C")]
	assert ref.find_duplicate(_row(name="Z"), cands) == "A"
	assert ref.find_duplicate(_row(name="A"), cands) == "C"  # bỏ chính nó
	assert ref.find_duplicate(_row(name="Z"), [cands[0]]) is None  # dòng Loại bỏ không tính
	assert ref.find_duplicate(_row(name="Z", price_category="X"), cands) is None


def test_FR_BM_005_loc_gia_da_xac_nhan():
	rows = [
		_row(name=str(i), status=s)
		for i, s in enumerate(
			[
				ref.STATUS_CONFIRMED,
				ref.STATUS_PROPOSED,
				ref.STATUS_CONFIRMED,
				ref.STATUS_REJECTED,
				ref.STATUS_CONFIRMED,
			]
		)
	]
	assert [r["name"] for r in ref.comparable_prices(rows)] == ["0", "2", "4"]
