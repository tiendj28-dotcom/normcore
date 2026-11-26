"""Bảng giải trình PDF (FR-OUT-005). Thuần, không phụ thuộc frappe. Không làm tròn lại số đã lưu."""

from decimal import Decimal

MINUS = "−"


def _dec(x):
	return x if isinstance(x, Decimal) else Decimal(str(x))


def _group(s: str) -> str:
	return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt(x, places):
	if x is None or x == "":
		return ""
	d = _dec(x)
	neg = d < 0
	s = _group(f"{abs(d):,.{places}f}")
	return (MINUS if neg else "") + s


def money(x) -> str:
	"""287745.46 -> "287.745,46"; âm dùng dấu "−"."""
	return _fmt(x, 2)


def money0(x) -> str:
	"""302100 -> "302.100"."""
	return _fmt(x, 0)


def qty(x) -> str:
	"""Lượng: bỏ số 0 thừa ở cuối phần thập phân."""
	if x is None or x == "":
		return ""
	d = _dec(x)
	s = f"{d:f}"
	if "." in s:
		s = s.rstrip("0").rstrip(".")
	neg = s.startswith("-")
	s = s.lstrip("-")
	ip, _, fp = s.partition(".")
	out = _group(f"{int(ip):,}") + ("," + fp if fp else "")
	return (MINUS if neg else "") + out
