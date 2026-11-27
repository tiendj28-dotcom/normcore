"""Tài liệu của hãng sản xuất (FR-LIB-013). Hàm thuần, không phụ thuộc frappe."""

MANUFACTURER_DOC_TYPE = "Tài liệu của hãng"
LINKABLE = ("NC Item", "NC Equipment")


def resource_link_errors(doc_type, rows):
	"""Lỗi của bảng `related_resources` (TD 2.1). Loại khác "Tài liệu của hãng": giữ bảng, không báo lỗi (ASM-038-02)."""
	if doc_type != MANUFACTURER_DOC_TYPE:
		return []
	rows = list(rows or [])
	if not rows:
		return ["Tài liệu của hãng phải gắn ít nhất một mặt hàng hoặc thiết bị"]
	errors = []
	seen = {}
	for i, r in enumerate(rows, start=1):
		idx = r.get("idx") or i
		if r.get("linked_doctype") not in LINKABLE:
			errors.append(f"Dòng {idx}: Chỉ gắn được mặt hàng hoặc thiết bị")
			continue
		key = (r.get("linked_doctype"), r.get("linked_name"))
		if key in seen:
			errors.append(f"Dòng {idx} trùng với dòng {seen[key]}")
		else:
			seen[key] = idx
	return errors
