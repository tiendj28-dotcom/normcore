"""Hồ sơ tuân thủ thiết bị — hàm thuần Python, không import framework (ADR-003).

FR-CMP-001, FR-CMP-005, FR-CMP-006 (phần dữ liệu), FR-CMP-007, FR-ADM-006. Không có phép tính tiền.
Quy tắc biên: ASM-101 (d = hạn trừ hôm nay; d < 0 Hết hạn; 0 ≤ d ≤ N Sắp hết hạn; d > N Còn hạn).
"""

from datetime import date, datetime

VALID = "Còn hạn"
DUE = "Sắp hết hạn"
EXPIRED = "Hết hạn"
MISSING = "Thiếu hồ sơ còn hạn"
DEFAULT_REMINDER_DAYS = 30
_ORDER = {EXPIRED: 0, DUE: 1, MISSING: 2}

_REQUIRED = (
	("equipment", "Thiết bị"),
	("record_type", "Loại hồ sơ"),
	("cycle_months", "Chu kỳ (tháng)"),
	("provider", "Đơn vị thực hiện"),
	("cost_per_time", "Chi phí mỗi lần"),
	("performed_on", "Ngày thực hiện"),
	("expiry_date", "Ngày hết hạn"),
	("attachment", "Tệp chứng từ"),
)


def _date(x) -> date | None:
	if x is None or x == "":
		return None
	if isinstance(x, datetime):
		return x.date()
	if isinstance(x, date):
		return x
	return date.fromisoformat(str(x)[:10])


def _blank(x) -> bool:
	return x is None or x == ""


def reminder_days(value) -> int:
	"""FR-ADM-006: trống → 30; âm là lỗi."""
	if _blank(value):
		return DEFAULT_REMINDER_DAYS
	n = int(value)
	if n < 0:
		raise ValueError("Số ngày nhắc hạn không được âm")
	return n


def compute_status(expiry_date, today, reminder) -> str:
	d = (_date(expiry_date) - _date(today)).days
	if d < 0:
		return EXPIRED
	if d <= reminder:
		return DUE
	return VALID


def validate_record(values) -> list[str]:
	"""FR-CMP-001, UC-020 1b: danh sách lỗi tiếng Việt, rỗng nếu hợp lệ."""
	errors = []
	for field, label in _REQUIRED:
		if _blank(values.get(field)):
			errors.append(f"Thiếu trường bắt buộc: {label}")
	cycle = values.get("cycle_months")
	if not _blank(cycle) and cycle <= 0:
		errors.append("Chu kỳ (tháng) phải lớn hơn 0")
	cost = values.get("cost_per_time")
	if not _blank(cost) and cost < 0:
		errors.append("Chi phí mỗi lần không được âm")
	done, expiry = _date(values.get("performed_on")), _date(values.get("expiry_date"))
	if done and expiry and expiry <= done:
		errors.append("Ngày hết hạn phải sau ngày thực hiện")
	attachment = values.get("attachment")
	if not _blank(attachment) and not str(attachment).startswith("/private/files/"):
		errors.append("Tệp chứng từ phải là tệp riêng tư")
	return errors


def is_valid_on(record, on) -> bool:
	"""FR-CMP-006: thực hiện ≤ ngày ≤ hết hạn."""
	return _date(record["performed_on"]) <= _date(on) <= _date(record["expiry_date"])


def has_valid_record(records, on) -> bool:
	return any(is_valid_on(r, on) for r in records)


def missing_required(equipments, records_by_equipment, on) -> list:
	"""Thiết bị thuộc loại bắt buộc mà không có hồ sơ còn hạn tại `on`."""
	return [
		e
		for e in equipments
		if e.get("compliance_required") and not has_valid_record(records_by_equipment.get(e["name"], []), on)
	]


def due_for_reminder(records, today, reminder) -> list:
	return [r for r in records if compute_status(r["expiry_date"], today, reminder) == DUE]


def recipients(resource_managers, head_user) -> list[str]:
	return sorted({u for u in [*resource_managers, head_user] if not _blank(u)})


def reminder_subject(record) -> str:
	code = record.get("record_code") or record["name"]
	expiry = _date(record["expiry_date"]).strftime("%d/%m/%Y")
	return f"Hồ sơ tuân thủ {code} của thiết bị {record['equipment']} sắp hết hạn vào {expiry}"


def build_expiry_report(records, missing, on, reminder, department=None, status=None) -> list[dict]:
	"""FR-CMP-007: Hết hạn, Sắp hết hạn và thiết bị bắt buộc thiếu hồ sơ; sắp theo khoa, trạng thái, hạn."""
	today = _date(on)
	rows = []
	for r in records:
		st = compute_status(r["expiry_date"], today, reminder)
		if st == VALID:
			continue
		rows.append(
			{
				"department": r.get("department"),
				"equipment": r["equipment"],
				"equipment_type": r.get("equipment_type"),
				"record": r["name"],
				"record_type": r.get("record_type"),
				"provider": r.get("provider"),
				"performed_on": _date(r.get("performed_on")),
				"expiry_date": _date(r["expiry_date"]),
				"days_left": (_date(r["expiry_date"]) - today).days,
				"status": st,
			}
		)
	for e in missing:
		rows.append(
			{
				"department": e.get("department"),
				"equipment": e["name"],
				"equipment_type": e.get("equipment_type"),
				"record": None,
				"record_type": None,
				"provider": None,
				"performed_on": None,
				"expiry_date": None,
				"days_left": None,
				"status": MISSING,
			}
		)
	if department:
		rows = [r for r in rows if r["department"] == department]
	if status:
		rows = [r for r in rows if r["status"] == status]
	rows.sort(
		key=lambda r: (
			r["department"] or "",
			_ORDER[r["status"]],
			r["expiry_date"] or date.max,
			r["equipment"],
		)
	)
	return rows
