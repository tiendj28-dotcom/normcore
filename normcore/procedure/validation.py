"""Điều kiện gửi duyệt quy trình (FR-PROC-008, FR-PROC-012). Thuần Python, không phụ thuộc frappe.

Đầu vào là danh sách dict có khóa như trường của DocType con. Liệt kê hết lỗi một lần, thứ tự cố định.
"""


def _blank(value):
	return value is None or not str(value).strip()


def submit_errors(steps, resources, citations):
	"""Trả danh sách lỗi (chuỗi tiếng Việt); rỗng nghĩa là hợp lệ để gửi duyệt."""
	errors = []
	# (1) FR-PROC-012: phải có bước ở giai đoạn "Thực hiện"
	if not any(s.get("phase") == "Thực hiện" for s in steps):
		errors.append("Quy trình chưa có bước nào ở giai đoạn 'Thực hiện'")
	# (2) bước thiếu mô tả
	for s in steps:
		if _blank(s.get("description")):
			errors.append(f"Bước {s.get('step_id')} thiếu mô tả")
	# (3) nguồn lực thiếu số lượng, đơn vị
	for r in resources:
		qty = r.get("quantity")
		if qty is None or qty <= 0:
			errors.append(f"Dòng nguồn lực {r.get('resource_row_id')} thiếu số lượng")
		if _blank(r.get("uom")):
			errors.append(f"Dòng nguồn lực {r.get('resource_row_id')} thiếu đơn vị")
	# (4) FR-PROC-008: trích dẫn "Khác biệt" trống lý do
	for i, c in enumerate(citations, 1):
		if c.get("relation") == "Khác biệt" and _blank(c.get("deviation_reason")):
			where = c.get("target_step_id") or c.get("target_section") or "chung"
			errors.append(f"Trích dẫn dòng {i} ({where}) thuộc loại Khác biệt nhưng chưa có lý do")
	# (5) đề xuất AI chưa xử lý (UC-006 tiền điều kiện, ASM-007-11)
	for s in steps:
		if s.get("ai_suggested"):
			errors.append(f"Bước {s.get('step_id')} còn là đề xuất AI chưa xử lý")
	for r in resources:
		if r.get("ai_suggested"):
			errors.append(f"Dòng nguồn lực {r.get('resource_row_id')} còn là đề xuất AI chưa xử lý")
	return errors
