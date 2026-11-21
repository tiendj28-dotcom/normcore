"""Cấp mã bất biến từ bộ đếm trên bản ghi cha, không tái dùng mã đã xóa (DI-01, ADR-002). Thuần Python."""


def next_code(prefix, counter, existing_codes):
	"""Trả `(số mới, mã mới)`. Số mới lớn hơn cả bộ đếm lẫn mọi mã đang có, nên mã đã xóa không bị cấp lại."""
	used = [
		int(c[len(prefix) :])
		for c in existing_codes
		if c and c.startswith(prefix) and c[len(prefix) :].isdigit()
	]
	nxt = max([int(counter or 0), *used]) + 1
	return nxt, f"{prefix}{nxt:03d}"
