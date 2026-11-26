"""Tách văn bản từ PDF/DOCX (FR-LIB-003..005, FEAT-020). Chạy trên site vì cần pypdf, python-docx (ASM-020-10)."""

import os

from frappe.tests.utils import FrappeTestCase

from normcore.library import extract
from normcore.library.extract import ExtractionError, Page

FILES = os.path.join(os.path.dirname(__file__), "test_files")


def _read(name):
	with open(os.path.join(FILES, name), "rb") as f:
		return f.read()


class TestExtract(FrappeTestCase):
	def test_FR_LIB_003_pdf_dung_so_trang_va_chu_tieng_viet(self):
		pages = extract.extract_pages(_read("qtkt_3_quy_trinh.pdf"), "qtkt_3_quy_trinh.pdf")
		self.assertEqual([p.number for p in pages], [1, 2, 3, 4])
		self.assertIn("ĐO ĐIỆN TIM", pages[0].text)
		self.assertIn("SIÊU ÂM BỤNG", pages[2].text)
		self.assertNotIn("\t", pages[0].text)

	def test_FR_LIB_003_docx_mot_trang_khong_so_trang(self):
		pages = extract.extract_pages(_read("qtkt_mau.docx"), "qtkt_mau.docx")
		self.assertEqual(len(pages), 1)
		self.assertIsNone(pages[0].number)
		self.assertIn("QUY TRÌNH KỸ THUẬT MẪU", pages[0].text)

	def test_FR_LIB_005_pdf_hong_bao_loi(self):
		with self.assertRaises(ExtractionError) as cm:
			extract.extract_pages(_read("hong.pdf"), "hong.pdf")
		self.assertIn("Không đọc được tệp", str(cm.exception))

	def test_FR_LIB_005_docx_hong_bao_loi(self):
		with self.assertRaises(ExtractionError):
			extract.extract_pages(b"khong phai docx", "x.docx")

	def test_FR_LIB_001_dinh_dang_khong_ho_tro(self):
		with self.assertRaisesRegex(ExtractionError, "PDF hoặc DOCX"):
			extract.file_kind("bang.xlsx")
		self.assertEqual(extract.file_kind("A.PDF"), "pdf")

	def test_FR_LIB_004_pdf_trang_khong_co_ocr_bao_khong_co_lop_van_ban(self):
		with self.assertRaisesRegex(ExtractionError, "không có lớp văn bản"):
			extract.extract_pages(_read("khong_lop_van_ban.pdf"), "k.pdf", ocr=None)

	def test_FR_LIB_004_pdf_trang_voi_ocr_gia_tra_trang(self):
		def fake(content):
			return [Page(1, "Văn bản nhận dạng được " * 5)]

		pages = extract.extract_pages(_read("khong_lop_van_ban.pdf"), "k.pdf", ocr=fake)
		self.assertIn("nhận dạng", pages[0].text)

	def test_FR_LIB_004_ocr_loi_hoac_van_rong_bao_that_bai(self):
		def boom(content):
			raise RuntimeError("tesseract chết")

		with self.assertRaisesRegex(ExtractionError, "Nhận dạng ký tự thất bại"):
			extract.extract_pages(_read("khong_lop_van_ban.pdf"), "k.pdf", ocr=boom)
		with self.assertRaisesRegex(ExtractionError, "Nhận dạng ký tự thất bại"):
			extract.extract_pages(_read("khong_lop_van_ban.pdf"), "k.pdf", ocr=lambda c: [Page(1, "")])

	def test_FR_LIB_004_available_ocr_theo_lenh_he_thong(self):
		import shutil

		have = shutil.which("tesseract") and shutil.which("pdftoppm")
		self.assertEqual(extract.available_ocr() is not None, bool(have))

	def test_FR_LIB_003_pdf_ma_hoa_bi_tu_choi(self):
		import io

		from pypdf import PdfWriter

		w = PdfWriter()
		w.add_blank_page(width=100, height=100)
		w.encrypt("mat-khau")
		buf = io.BytesIO()
		w.write(buf)
		with self.assertRaisesRegex(ExtractionError, "mã hóa"):
			extract.extract_pages(buf.getvalue(), "m.pdf")
