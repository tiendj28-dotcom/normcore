"""Thay thế văn bản: hàm thuần (FR-LIB-007, FR-LIB-008). Không cần site."""

from datetime import date, datetime

from normcore.library import supersession as s


def test_parse_sections_tach_bo_trung_sap_tu_nhien():
	assert s.parse_sections("10, 2, 5, 2, ") == ["2", "5", "10"]
	assert s.parse_sections("A; a") == ["A"]
	assert s.parse_sections(None) == [] and s.parse_sections("") == []


def test_format_sections():
	assert s.format_sections(["2", "5"]) == "2, 5"


def test_expiry_for_ngay_lien_truoc():
	assert s.expiry_for(date(2026, 7, 1)) == date(2026, 6, 30)
	assert s.expiry_for("2026-03-01") == date(2026, 2, 28)
	assert s.expiry_for(datetime(2026, 1, 1, 5)) == date(2025, 12, 31)


def test_plan_expiry_chi_keo_som_hon():
	assert s.plan_expiry(None, date(2026, 7, 1)) == date(2026, 6, 30)
	assert s.plan_expiry("", "2026-07-01") == date(2026, 6, 30)
	assert s.plan_expiry(date(2026, 6, 30), date(2026, 7, 1)) is None
	assert s.plan_expiry(date(2026, 1, 1), date(2026, 7, 1)) is None
	assert s.plan_expiry(date(2026, 12, 31), date(2026, 7, 1)) == date(2026, 6, 30)


def test_plan_section_expiry_chi_muc_duoc_chon():
	secs = [("S1", "1", None), ("S2", "2", None), ("S3", "3", None), ("S5", "5", date(2026, 1, 1))]
	out = s.plan_section_expiry(secs, ["2", "5", "7"], date(2026, 7, 1))
	assert out == [("S2", date(2026, 6, 30))]
	assert s.plan_section_expiry(secs, [], date(2026, 7, 1)) == []
	assert s.plan_section_expiry([("X", None, None)], ["2"], date(2026, 7, 1)) == []


def test_covers():
	assert s.covers({"scope": s.ALL}, "9")
	row = {"scope": s.PART, "superseded_sections": "2, 5"}
	assert s.covers(row, "2") and s.covers(row, " 5 ")
	assert not s.covers(row, "3")


def _targets():
	return {"B": {"effective_date": date(2026, 1, 2), "doc_number": "1/QĐ", "section_nos": ["1", "2", "3"]}}


def test_row_errors_hop_le():
	rows = [{"idx": 1, "superseded_document": "B", "scope": s.PART, "superseded_sections": "2",
		"from_date": date(2026, 7, 1)}]
	assert s.row_errors(rows, "A", _targets()) == []
	assert s.row_errors([{"idx": 1, "superseded_document": None}], "A", _targets()) == []


def test_row_errors_tu_thay_chinh_no():
	rows = [{"idx": 1, "superseded_document": "A", "scope": s.ALL, "from_date": date(2026, 7, 1)}]
	assert s.row_errors(rows, "A", {}) == ["Dòng 1: Văn bản không thể thay thế chính nó"]


def test_row_errors_trung_va_ngay_va_muc():
	base = {"superseded_document": "B", "scope": s.ALL}
	rows = [
		{**base, "idx": 1, "from_date": date(2026, 1, 2)},
		{**base, "idx": 2, "from_date": date(2026, 7, 1)},
		{"idx": 3, "superseded_document": "C", "scope": s.PART, "superseded_sections": "",
			"from_date": "2026-07-01"},
		{**base, "idx": 4, "superseded_document": "B", "scope": s.PART, "superseded_sections": "2, 9, 8",
			"from_date": date(2026, 7, 1)},
	]
	targets = {**_targets(), "C": {}}
	errs = s.row_errors(rows, "A", targets)
	assert any("Dòng 1: Ngày bắt đầu thay thế phải sau ngày hiệu lực của 1/QĐ (02/01/2026)" == e for e in errs)
	assert "Dòng 2: Văn bản B đã được khai báo thay thế ở dòng 1" in errs
	assert "Dòng 3: Chọn ít nhất một mục bị thay thế" in errs
	assert "Dòng 4: Văn bản 1/QĐ không có mục: 8, 9" in errs
	# B chưa có chỉ mục
	rows = [{"idx": 1, "superseded_document": "C", "scope": s.PART, "superseded_sections": "1",
		"from_date": date(2026, 7, 1)}]
	assert s.row_errors(rows, "A", {"C": {}}) == ["Dòng 1: Văn bản C không có mục: 1"]


def test_normalize_rows():
	rows = [
		{"scope": s.ALL, "superseded_sections": "2, 5"},
		{"scope": s.PART, "superseded_sections": "5;2\n10, 2"},
	]
	s.normalize_rows(rows)
	assert rows[0]["superseded_sections"] == ""
	assert rows[1]["superseded_sections"] == "2, 5, 10"
