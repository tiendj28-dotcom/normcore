"""Tiện ích test của FEAT-020 (không phải test)."""

import os

import frappe

FILES = os.path.join(os.path.dirname(__file__), "test_files")


def read_sample(name):
	with open(os.path.join(FILES, name), "rb") as f:
		return f.read()


def make_legal_file(filename, content=None):
	"""Tệp private mới; trả file_url. Mặc định là PDF hợp lệ (Frappe từ chối PDF hỏng khi tải lên)."""
	if content is None:
		content = read_sample("qtkt_3_quy_trinh.pdf") if filename.endswith(".pdf") else b"x"
	doc = frappe.get_doc(
		{"doctype": "File", "file_name": filename, "is_private": 1, "content": content}
	).insert(ignore_permissions=True)
	return doc.file_url


def legal_values(doc_number="123/QĐ-BYT", file_url=None, **kw):
	values = {
		"doctype": "NC Legal Document",
		"doc_number": doc_number,
		"title": "Hướng dẫn quy trình kỹ thuật thử",
		"doc_type": "Quyết định",
		"issuer": "Bộ Y tế",
		"issue_date": "2026-01-01",
		"effective_date": "2026-01-02",
		"is_procedure_guideline": 1,
		"file": file_url or make_legal_file("van-ban-thu.pdf"),
	}
	values.update(kw)
	return values


def make_legal_document(doc_number="123/QĐ-BYT", **kw):
	return frappe.get_doc(legal_values(doc_number, **kw)).insert(ignore_permissions=True)


def make_corrupt_file(filename="hong.pdf"):
	"""Tệp hỏng: Frappe không cho tải PDF hỏng lên, nên tải một PDF hợp lệ có nội dung riêng (để không dùng chung
	tệp trên đĩa với tệp khác) rồi ghi đè nội dung trên đĩa bằng byte hỏng."""
	import io

	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=123, height=456)  # kích thước lạ: nội dung riêng
	buf = io.BytesIO()
	writer.write(buf)
	url = make_legal_file(filename, buf.getvalue())
	f = frappe.get_doc("File", {"file_url": url})
	with open(f.get_full_path(), "wb") as fh:
		fh.write(read_sample("hong.pdf"))
	return url
