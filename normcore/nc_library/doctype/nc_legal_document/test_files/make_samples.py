"""Sinh tệp mẫu cho test FEAT-020. Chạy lại khi cần tái tạo (kết quả đã commit, test chỉ đọc):

	scripts/with_bench.sh 'bench --site normcore.test execute \
		normcore.nc_library.doctype.nc_legal_document.test_files.make_samples.run'
"""

import os

HERE = os.path.dirname(__file__)

_PROC = {
	1: (
		"ĐO ĐIỆN TIM",
		"Đo điện tim là kỹ thuật ghi hoạt động điện của tim.",
		"Người bệnh nằm yên, bộc lộ ngực và cổ chân.",
	),
	2: ("SIÊU ÂM BỤNG", "Siêu âm bụng tổng quát đánh giá gan, mật, tụy, lách, thận."),
	3: ("NỘI SOI DẠ DÀY", "Nội soi dạ dày ống mềm quan sát thực quản, dạ dày, tá tràng."),
}


def _html():
	pages = []
	p1 = "<p>1. ĐO ĐIỆN TIM</p><p>I. ĐẠI CƯƠNG</p><p>" + _PROC[1][1] + "</p>"
	p2 = "<p>II. CHỈ ĐỊNH</p><p>" + _PROC[1][2] + "</p>"
	p3 = "<p>2. SIÊU ÂM BỤNG</p><p>I. ĐẠI CƯƠNG</p><p>" + _PROC[2][1] + "</p>"
	p4 = "<p>3. NỘI SOI DẠ DÀY</p><p>I. ĐẠI CƯƠNG</p><p>" + _PROC[3][1] + "</p>"
	for i, body in enumerate([p1, p2, p3, p4]):
		style = "page-break-after: always;" if i < 3 else ""
		pages.append(f'<div style="{style}">{body}</div>')
	return "<html><head><meta charset='utf-8'></head><body>" + "".join(pages) + "</body></html>"


def run():
	import io

	from docx import Document
	from frappe.utils.pdf import get_pdf
	from pypdf import PdfWriter

	def w(name, data):
		with open(os.path.join(HERE, name), "wb") as f:
			f.write(data)

	w("qtkt_3_quy_trinh.pdf", get_pdf(_html()))
	doc = Document()
	doc.add_paragraph("QUY TRÌNH KỸ THUẬT MẪU")
	doc.add_paragraph("Nội dung quy trình mẫu bằng DOCX để thử tách mục.")
	buf = io.BytesIO()
	doc.save(buf)
	w("qtkt_mau.docx", buf.getvalue())
	blank = PdfWriter()
	blank.add_blank_page(width=595, height=842)
	buf = io.BytesIO()
	blank.write(buf)
	w("khong_lop_van_ban.pdf", buf.getvalue())
	w("hong.pdf", b"%PDF-1.4\n" + b"\x00\xffrac hong khong phai pdf" * 20)
