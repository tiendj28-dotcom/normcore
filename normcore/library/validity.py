"""Hiệu lực văn bản và mục (FR-LIB-006, ASM-020-07). Hàm thuần."""

from datetime import date, datetime

CHUA = "Chưa hiệu lực"
CON = "Còn hiệu lực"
HET = "Hết hiệu lực"


def _d(value):
	if value in (None, ""):
		return None
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def compute_validity(effective_date, expiry_date, today):
	"""Trước ngày hiệu lực: Chưa; sau ngày hết hiệu lực: Hết; còn lại: Còn."""
	today, eff, exp = _d(today), _d(effective_date), _d(expiry_date)
	if eff and today < eff:
		return CHUA
	if exp and today > exp:
		return HET
	return CON


def compute_section_validity(doc_status, section_expiry_date, today):
	"""Mục kế thừa văn bản; văn bản còn hiệu lực mà mục có hạn riêng đã qua thì Hết."""
	if doc_status != CON:
		return doc_status
	exp = _d(section_expiry_date)
	if exp and _d(today) > exp:
		return HET
	return CON


def changed(rows, today, section=False):
	"""Trả [(name, trạng_thái_mới)] cho các dòng cần đổi.

	Văn bản: dòng (name, effective_date, expiry_date, status).
	Mục (section=True): dòng (name, doc_status, expiry_date, status).
	"""
	out = []
	for name, a, expiry, current in rows:
		new = (
			compute_section_validity(a, expiry, today) if section else compute_validity(a, expiry, today)
		)
		if new != current:
			out.append((name, new))
	return out
