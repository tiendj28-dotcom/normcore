"""Quy tắc dịch vụ cận lâm sàng — hàm thuần Python, không import framework (ADR-003).

FR-SVC-008..011, DI-09, ASM-107, ASM-108, ASM-110.
"""


def normalize_code(code) -> str:
	return (code or "").strip()


def code_key(source_system, external_code) -> tuple:
	"""Khóa so sánh mã ngoài: cắt khoảng trắng, không phân biệt hoa thường (ASM-110)."""
	return (source_system, normalize_code(external_code).upper())


def duplicate_codes(rows) -> list:
	"""Cặp (hệ thống nguồn, mã ngoài) lặp trong cùng một dịch vụ (DI-09)."""
	seen, dups = set(), []
	for r in rows:
		k = code_key(r.get("source_system"), r.get("external_code"))
		if k in seen and k not in dups:
			dups.append(k)
		seen.add(k)
	return dups


def _blank(v) -> bool:
	return v is None or str(v).strip() == ""


def cls_errors(values: dict) -> list:
	"""Lỗi trường cận lâm sàng của một dịch vụ (rỗng = hợp lệ)."""
	if not values.get("is_paraclinical"):
		return []
	errors = []
	if _blank(values.get("cls_group")):
		errors.append("Thiếu Nhóm chuyên ngành: dịch vụ thuộc khối cận lâm sàng phải có nhóm chuyên ngành")
	if _blank(values.get("result_unit")):
		errors.append("Thiếu Đơn vị kết quả: dịch vụ thuộc khối cận lâm sàng phải có đơn vị kết quả")
	if values.get("is_panel"):
		comps = values.get("panel_components") or []
		if not comps:
			errors.append("Dịch vụ bộ phải có ít nhất một thông số thành phần")
		seen = set()
		for c in comps:
			code = normalize_code(c.get("parameter_code")).upper()
			if code in seen:
				errors.append(f"Mã thông số {c.get('parameter_code')} bị lặp trong bộ")
			seen.add(code)
			if c.get("technical_service") and c.get("technical_service") == values.get("service_code"):
				errors.append("Thông số thành phần không được trỏ chính dịch vụ bộ")
	if values.get("is_send_out"):
		price = values.get("send_out_price")
		if _blank(price) or float(price) <= 0:
			errors.append("Dịch vụ gửi ngoài phải có Giá hợp đồng gửi mẫu lớn hơn 0")
	return errors
