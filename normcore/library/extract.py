"""Tách văn bản theo trang từ PDF/DOCX (FR-LIB-003, FR-LIB-004, FR-LIB-005). Không import frappe.

`pypdf` và `python-docx` import bên trong hàm để các module thuần khác chạy được không cần gói ngoài.
"""

import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

OCR_CHARS_PER_PAGE = 20  # ASM-020-05


class ExtractionError(Exception):
	"""Thông điệp tiếng Việt, dùng làm `index_error`."""


@dataclass
class Page:
	number: int | None
	text: str


def file_kind(filename):
	name = (filename or "").lower()
	if name.endswith(".pdf"):
		return "pdf"
	if name.endswith(".docx"):
		return "docx"
	raise ExtractionError("Chỉ nhận tệp PDF hoặc DOCX")


def needs_ocr(pages):
	"""PDF mà tổng ký tự chữ < 20 × số trang."""
	if not pages:
		return True
	chars = sum(len("".join(p.text.split())) for p in pages)
	return chars < OCR_CHARS_PER_PAGE * len(pages)


def _pdf_pages(content):
	from pypdf import PdfReader

	try:
		reader = PdfReader(io.BytesIO(content))
		if reader.is_encrypted:
			raise ExtractionError("Không đọc được tệp: tệp PDF được mã hóa")
		pages = [Page(i + 1, (p.extract_text() or "").replace("\t", " ")) for i, p in enumerate(reader.pages)]
	except ExtractionError:
		raise
	except Exception as e:
		raise ExtractionError(f"Không đọc được tệp: {str(e)[:120] or type(e).__name__}") from e
	if not pages:
		raise ExtractionError("Không đọc được tệp: tệp PDF không có trang nào")
	return pages


def _docx_pages(content):
	try:
		from docx import Document

		doc = Document(io.BytesIO(content))
		lines = [p.text for p in doc.paragraphs]
		for table in doc.tables:
			for row in table.rows:
				lines.append(" | ".join(c.text for c in row.cells))
	except Exception as e:
		raise ExtractionError(f"Không đọc được tệp: {str(e)[:120] or type(e).__name__}") from e
	return [Page(None, "\n".join(lines))]


def extract_pages(content, filename, ocr=None):
	kind = file_kind(filename)
	if kind == "docx":
		return _docx_pages(content)
	pages = _pdf_pages(content)
	if not needs_ocr(pages):
		return pages
	if ocr is None:
		raise ExtractionError(
			"Tệp PDF không có lớp văn bản và máy chủ chưa có bộ nhận dạng ký tự"
		)
	try:
		result = ocr(content)
	except Exception as e:
		raise ExtractionError(f"Nhận dạng ký tự thất bại: {str(e)[:120] or type(e).__name__}") from e
	if not result or needs_ocr(result):
		raise ExtractionError("Nhận dạng ký tự thất bại: không nhận được chữ nào")
	return result


def tesseract_ocr(content, timeout=600):
	"""Bộ mặc định: pdftoppm -r 300 rồi tesseract -l vie, từng trang."""
	with tempfile.TemporaryDirectory() as tmp:
		pdf = os.path.join(tmp, "in.pdf")
		with open(pdf, "wb") as f:
			f.write(content)
		subprocess.run(
			["pdftoppm", "-r", "300", "-png", pdf, os.path.join(tmp, "p")],
			check=True,
			timeout=timeout,
			capture_output=True,
		)
		images = sorted(n for n in os.listdir(tmp) if n.startswith("p") and n.endswith(".png"))
		pages = []
		for i, name in enumerate(images):
			out = subprocess.run(
				["tesseract", os.path.join(tmp, name), "-", "-l", "vie"],
				check=True,
				timeout=timeout,
				capture_output=True,
			)
			pages.append(Page(i + 1, out.stdout.decode("utf-8", "replace")))
		return pages


def available_ocr():
	if shutil.which("tesseract") and shutil.which("pdftoppm"):
		return tesseract_ocr
	return None
