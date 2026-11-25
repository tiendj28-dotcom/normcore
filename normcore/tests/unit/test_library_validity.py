"""Hiệu lực văn bản và mục (FR-LIB-006, FEAT-020). Không cần site."""

from datetime import date, timedelta

from normcore.library import validity as v

TODAY = date(2026, 11, 26)
CHUA, CON, HET = "Chưa hiệu lực", "Còn hiệu lực", "Hết hiệu lực"


def test_FR_LIB_006_truoc_ngay_hieu_luc_la_chua_hieu_luc():
	assert v.compute_validity(TODAY + timedelta(days=1), None, TODAY) == CHUA


def test_FR_LIB_006_dung_ngay_hieu_luc_la_con_hieu_luc():
	assert v.compute_validity(TODAY, None, TODAY) == CON


def test_FR_LIB_006_ngay_het_hieu_luc_van_con_hieu_luc_ngay_sau_het():
	assert v.compute_validity(date(2020, 1, 1), TODAY, TODAY) == CON
	assert v.compute_validity(date(2020, 1, 1), TODAY, TODAY + timedelta(days=1)) == HET


def test_FR_LIB_006_chap_nhan_chuoi_iso():
	assert v.compute_validity("2026-11-27", None, TODAY) == CHUA
	assert v.compute_validity("2026-01-01", "2026-11-25", TODAY) == HET


def test_FR_LIB_006_muc_theo_van_ban_tru_khi_co_han_rieng():
	assert v.compute_section_validity(CHUA, None, TODAY) == CHUA
	assert v.compute_section_validity(HET, None, TODAY) == HET
	assert v.compute_section_validity(CON, None, TODAY) == CON
	assert v.compute_section_validity(CON, TODAY, TODAY) == CON
	assert v.compute_section_validity(CON, TODAY - timedelta(days=1), TODAY) == HET


def test_FR_LIB_006_changed_chi_tra_dong_doi():
	rows = [
		("A", "2026-11-27", None, CHUA),  # giữ nguyên
		("B", "2026-11-26", None, CHUA),  # sang Còn
		("C", "2020-01-01", "2026-11-25", CON),  # sang Hết
	]
	assert v.changed(rows, TODAY) == [("B", CON), ("C", HET)]


def test_FR_LIB_006_changed_cho_muc_dung_trang_thai_van_ban():
	rows = [("S1", CON, None, CON), ("S2", CHUA, None, CON), ("S3", CON, "2026-11-01", CON)]
	assert v.changed(rows, TODAY, section=True) == [("S2", CHUA), ("S3", HET)]
