"""FEAT-022 T01: hàm thuần ánh xạ mục hướng dẫn với dịch vụ (FR-SVC-005, FR-SVC-006)."""

import time

import pytest

from normcore.library import mapping as m


def test_normalize_title_bo_so_thu_tu_va_dau_cau():
	assert m.normalize_title("1. Chụp X-quang, ngực!") == "chụp x quang ngực"
	assert m.normalize_title("  IV) Siêu  âm ") == "siêu âm"


def test_title_tokens():
	assert m.title_tokens("2. Siêu âm bụng") == frozenset({"siêu", "âm", "bụng"})


def test_code_in_heading_ranh_gioi():
	assert m.code_in_heading("1. Quy trình 01.01 chụp", "01.01")
	assert m.code_in_heading("MÃ ab-12", "AB-12")
	assert not m.code_in_heading("Mã 01.011", "01.01")
	assert not m.code_in_heading("Mã 101.01", "01.01")
	assert not m.code_in_heading("abc", "")


def test_name_confidence():
	assert m.name_confidence("1. Siêu âm bụng", "siêu âm bụng") == 95
	assert m.name_confidence("abc", "xyz") == 0
	assert m.name_confidence("", "xyz") == 0
	# Dice = 2*1/(2+2)=0.5 -> 47.5 -> 48 (half-up)
	assert m.name_confidence("siêu âm", "siêu bụng") == 48
	assert m.name_confidence("siêu âm bụng", "siêu âm") == 76  # 2*2/5=0.8*95=76


SERVICES = [
	("01.01", "Chụp X-quang ngực"),
	("02.05", "Siêu âm bụng"),
	("03.01", "Siêu âm tim"),
	("04.01", "Siêu âm bụng tổng quát"),
	("05.01", "Siêu âm bụng"),
]


def test_suggest_khop_ma_100_bo_khop_ten():
	out = m.suggest_for_section("1. Quy trình 01.01 Chụp X-quang ngực", SERVICES)
	assert out[0] == ("01.01", 100)
	assert [c for c, _ in out].count("01.01") == 1


def test_suggest_sap_xep_va_toi_da_3():
	out = m.suggest_for_section("Siêu âm bụng", SERVICES)
	assert out == [("02.05", 95), ("05.01", 95), ("04.01", 71)]
	assert len(out) <= m.MAX_SUGGESTIONS


def test_suggest_bo_duoi_nguong():
	assert m.suggest_for_section("Siêu âm", [("03.01", "Siêu âm tim")]) == [("03.01", 76)]
	assert m.suggest_for_section("Điện tim", SERVICES) == []


def test_suggest_voi_index_giong_khong_index():
	idx = m.build_token_index(SERVICES)
	for h in ("Siêu âm bụng", "Chụp X-quang ngực 01.01", "Không liên quan"):
		assert m.suggest_for_section(h, SERVICES, idx) == m.suggest_for_section(h, SERVICES)


def test_merge_suggestions():
	existing = [
		{"technical_service": "A", "mapping_status": m.CONFIRMED, "confidence": 100},
		{"technical_service": "B", "mapping_status": m.SUGGESTED, "confidence": 60},
	]
	out = m.merge_suggestions(existing, [("A", 100), ("C", 80)])
	assert out == [
		{"technical_service": "A", "mapping_status": m.CONFIRMED, "confidence": 100},
		{"technical_service": "C", "mapping_status": m.SUGGESTED, "confidence": 80},
	]


def row(**kw):
	d = {"name": None, "technical_service": "A", "mapping_status": m.SUGGESTED}
	d.update(kw)
	return d


def test_stamp_dong_moi_da_xac_nhan():
	rows = [row(mapping_status=m.CONFIRMED)]
	m.stamp_rows(rows, [], "u@x", "T1")
	assert rows[0]["confirmed_by"] == "u@x" and rows[0]["confirmed_on"] == "T1"


def test_stamp_de_xuat_len_xac_nhan():
	before = [row(name="r1", confirmed_by=None)]
	rows = [row(name="r1", mapping_status=m.CONFIRMED)]
	m.stamp_rows(rows, before, "u", "T")
	assert rows[0]["confirmed_by"] == "u"


def test_stamp_giu_nguyen_khi_khong_doi():
	before = [row(name="r1", mapping_status=m.CONFIRMED, confirmed_by="old", confirmed_on="T0")]
	rows = [row(name="r1", mapping_status=m.CONFIRMED, confirmed_by="old", confirmed_on="T0")]
	m.stamp_rows(rows, before, "u", "T")
	assert rows[0]["confirmed_by"] == "old" and rows[0]["confirmed_on"] == "T0"


def test_stamp_doi_dich_vu_dong_dau_lai():
	before = [row(name="r1", mapping_status=m.CONFIRMED, confirmed_by="old", confirmed_on="T0")]
	rows = [row(name="r1", technical_service="B", mapping_status=m.CONFIRMED, confirmed_by="old")]
	m.stamp_rows(rows, before, "u", "T")
	assert rows[0]["confirmed_by"] == "u" and rows[0]["confirmed_on"] == "T"


def test_stamp_de_xuat_xoa_dau_va_giu_confidence():
	rows = [row(confirmed_by="x", confirmed_on="y", confidence=100)]
	m.stamp_rows(rows, [], "u", "T")
	assert rows[0]["confirmed_by"] is None and rows[0]["confirmed_on"] is None
	assert rows[0]["confidence"] == 100


def test_stamp_trung_dich_vu():
	with pytest.raises(m.MappingError):
		m.stamp_rows([row(), row(name="r2")], [], "u", "T")


def test_is_draft_source_va_mappable():
	assert m.is_draft_source({"mapping_status": m.CONFIRMED})
	assert not m.is_draft_source({"mapping_status": m.SUGGESTED})
	assert not m.is_mappable_section("0")
	assert m.is_mappable_section("1.2")


def test_hieu_nang_5000_dich_vu_300_muc():
	# tên dịch vụ giả: 4 từ lấy từ bộ 300 từ (giống phân bố từ vựng thực), 5.000 dịch vụ × 300 mục
	vocab = [f"từ{j}" for j in range(300)]
	services = [
		(f"{i:05d}", " ".join(vocab[(i * k + k * k) % 300] for k in (1, 7, 13, 29)) + f" số{i}")
		for i in range(5000)
	]
	idx = m.build_token_index(services)
	t = time.time()
	for i in range(300):
		m.suggest_for_section(f"{i}. {services[i * 13][1]}", services, idx)
	assert time.time() - t < 5
