"""Tách mục (FR-LIB-003, FEAT-020). Không cần site."""

import pytest

from normcore.library.extract import ExtractionError, Page, needs_ocr
from normcore.library.sections import split_sections

QTKT = [
	Page(1, "1. ĐO ĐIỆN TIM\nI. ĐẠI CƯƠNG\nĐo điện tim là kỹ thuật ghi.\n1. Bác sĩ chỉ định"),
	Page(2, "II. CHỈ ĐỊNH\nMọi người bệnh nghi ngờ."),
	Page(3, "2. SIÊU ÂM BỤNG\nI. ĐẠI CƯƠNG\nSiêu âm bụng tổng quát."),
	Page(4, "3. NỘI SOI DẠ DÀY\nI. ĐẠI CƯƠNG\nNội soi."),
]


def test_FR_LIB_003_qtkt_moi_quy_trinh_la_mot_muc_cap_1():
	s = split_sections(QTKT, True)
	assert [x.section_no for x in s] == ["1", "2", "3"]
	assert [x.heading for x in s] == ["ĐO ĐIỆN TIM", "SIÊU ÂM BỤNG", "NỘI SOI DẠ DÀY"]
	assert [(x.page_from, x.page_to) for x in s] == [(1, 2), (3, 3), (4, 4)]
	assert "Đo điện tim là kỹ thuật ghi." in s[0].plain_text
	assert "Bác sĩ chỉ định" in s[0].plain_text  # "1. Bác sĩ" không phải tiêu đề cấp 1


def test_FR_LIB_003_van_ban_dieu_n():
	pages = [Page(1, "LUẬT KHÁM BỆNH\nĐiều 1. Phạm vi\nQuy định chung.\nĐiều 2a: Giải thích\nTừ ngữ.")]
	s = split_sections(pages, False)
	assert [x.section_no for x in s] == ["0", "Điều 1", "Điều 2a"]
	assert s[0].heading == "Phần mở đầu" and s[0].plain_text == "LUẬT KHÁM BỆNH"
	assert s[1].heading == "Phạm vi"


def test_FR_LIB_003_dieu_khong_co_tieu_de_dung_so_muc():
	s = split_sections([Page(1, "Điều 7\nNội dung")], False)
	assert s[0].heading == "Điều 7"


def test_FR_LIB_003_khong_tieu_de_thi_moi_trang_mot_muc():
	s = split_sections([Page(1, "abc"), Page(2, "  "), Page(3, "def")], True)
	assert [(x.section_no, x.page_from) for x in s] == [("Trang 1", 1), ("Trang 3", 3)]


def test_FR_LIB_003_phan_mo_dau_khong_tieu_de_khong_tao_muc_0():
	s = split_sections([Page(1, "chỉ có lời nói đầu")], False)
	assert [x.section_no for x in s] == ["Trang 1"]


def test_FR_LIB_003_docx_khong_trang_thanh_mot_muc():
	s = split_sections([Page(None, "\nTên tài liệu\nNội dung")], False)
	assert len(s) == 1 and s[0].section_no == "1" and s[0].heading == "Tên tài liệu"
	assert s[0].page_from is None and s[0].page_to is None


def test_FR_LIB_003_so_muc_lap_them_hau_to():
	pages = [Page(1, "3. QUY TRÌNH A\nx"), Page(2, "3. QUY TRÌNH B\ny")]
	assert [x.section_no for x in split_sections(pages, True)] == ["3", "3-2"]


def test_FR_LIB_003_heading_cat_140_ky_tu():
	s = split_sections([Page(1, "1. " + "A" * 200 + "\nx")], True)
	assert len(s[0].heading) == 140


def test_FR_LIB_005_khong_co_chu_thi_loi():
	with pytest.raises(ExtractionError, match="Không tách được mục nào"):
		split_sections([Page(1, " \n "), Page(2, "")], True)


def test_FR_LIB_004_needs_ocr():
	assert needs_ocr([])
	assert needs_ocr([Page(1, ""), Page(2, "ab")])
	assert not needs_ocr([Page(1, "x" * 30)])
