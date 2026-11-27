"""Sinh tệp mẫu cho test FEAT-027. Chạy lại khi cần tái tạo (kết quả đã commit, test chỉ đọc):

	scripts/with_bench.sh 'bench --site normcore.test execute \
		normcore.nc_benchmark.doctype.nc_benchmark_price.test_files.make_samples.run'
"""

import os

HERE = os.path.dirname(__file__)

# 4 dịch vụ có giá, 1 dòng tiêu đề, 1 dòng "Tổng cộng", 2 trang.
PAGE1 = [("Định lượng Glucose máu", "25.000"), ("Siêu âm ổ bụng tổng quát", "120.000")]
PAGE2 = [("Chụp X-quang ngực thẳng", "90.000"), ("Đo điện tim thường", "40.000")]


def _html():
	def table(rows, extra=""):
		body = "".join(f"<tr><td>{n}</td><td>{p}</td></tr>" for n, p in rows)
		return f"<table>{body}{extra}</table>"

	p1 = "<p>BẢNG GIÁ DỊCH VỤ KỸ THUẬT BỆNH VIỆN THỬ</p>" + table(PAGE1)
	p2 = table(PAGE2, "<tr><td>Tổng cộng</td><td></td></tr>")
	return (
		"<html><head><meta charset='utf-8'></head><body>"
		f"<div style='page-break-after: always;'>{p1}</div><div>{p2}</div></body></html>"
	)


def run():
	from frappe.utils.pdf import get_pdf

	with open(os.path.join(HERE, "bang_gia_4_dong.pdf"), "wb") as f:
		f.write(get_pdf(_html()))
