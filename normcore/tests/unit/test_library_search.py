"""Chuẩn hóa và tìm kiếm (FR-LIB-002, FR-LIB-010, FEAT-020). Không cần site."""

from normcore.library import search as s


def test_FR_LIB_002_so_hieu_khong_phan_biet_hoa_thuong_va_khoang_trang():
	a = s.normalize_doc_number("123/qđ-byt")
	assert a == s.normalize_doc_number("123/QĐ-BYT") == s.normalize_doc_number(" 123 / QĐ-BYT ")
	assert a != s.normalize_doc_number("124/QĐ-BYT")


def test_FR_LIB_002_so_hieu_nfc_va_none():
	nfd = "123/Q\u0110-BYT"
	assert s.normalize_doc_number(None) == ""
	assert s.normalize_doc_number(nfd) == s.normalize_doc_number("123/qđ-byt")
	# chữ có dấu dạng tổ hợp (NFD) bằng dạng dựng sẵn (NFC)
	assert s.normalize_doc_number("e\u0302") == s.normalize_doc_number("\u00ea")


def test_FR_LIB_010_tokenize_bo_ky_tu_boolean():
	assert s.tokenize('+đo -điện "tim" (nhanh)*') == ["đo", "điện", "tim", "nhanh"]


def test_FR_LIB_010_build_fulltext_query_chi_giu_tu_dai():
	assert s.build_fulltext_query("đo điện tim") == "+điện +tim"
	assert s.build_fulltext_query("đo ok") is None
	assert s.build_fulltext_query("siêu âm", min_token=2) == "+siêu +âm"


def test_FR_LIB_010_matches_phrase():
	assert s.matches_phrase("Quy trình ĐO điện tim cơ bản", "đo  điện tim")
	assert not s.matches_phrase("điện tim đo", "đo điện tim")
	assert not s.matches_phrase("abc", "")


def test_FR_LIB_010_make_snippet():
	text = "a" * 300 + " điện tim " + "b" * 300
	sn = s.make_snippet(text, "điện tim", width=60)
	assert "điện tim" in sn and sn.startswith("…") and sn.endswith("…")
	short = s.make_snippet("Điện tim đồ", "điện")
	assert short == "Điện tim đồ"
	assert s.make_snippet("x" * 300, "zzz", width=50) == "x" * 50 + "…"


def test_FR_LIB_010_section_matches_service():
	assert s.section_matches_service("12. ĐO ĐIỆN TIM THƯỜNG QUY", "Đo điện tim thường quy")
	assert not s.section_matches_service("13. SIÊU ÂM", "Đo điện tim")
	assert not s.section_matches_service("x", "")


def test_FR_LIB_010_rank_hieu_luc_roi_so_hieu_roi_so_muc_tu_nhien():
	rows = [
		{"doc_number": "B", "section_no": "10", "validity_status": "Còn hiệu lực"},
		{"doc_number": "B", "section_no": "2", "validity_status": "Còn hiệu lực"},
		{"doc_number": "A", "section_no": "Điều 1", "validity_status": "Hết hiệu lực"},
		{"doc_number": "A", "section_no": "3", "validity_status": "Chưa hiệu lực"},
		{"doc_number": "B", "section_no": "Điều 2", "validity_status": "Còn hiệu lực"},
	]
	got = [(r["doc_number"], r["section_no"]) for r in s.rank(rows)]
	assert got == [("B", "2"), ("B", "10"), ("B", "Điều 2"), ("A", "3"), ("A", "Điều 1")]
