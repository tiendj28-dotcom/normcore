"""Đọc tham số vận hành NC Settings (FR-ADM-003). Không cache ở tiến trình: đổi rồi áp ngay."""

import frappe

DEFAULTS = {
	"min_time_study_cases": 5,
	"approval_reminder_days": 7,
	"price_valid_months": 24,
	"benchmark_window_months": 24,
	"min_benchmark_facilities": 3,
	"accounting_regime": "Hành chính sự nghiệp",
	"compliance_reminder_days": 30,
}


# Tham số phải ≥ 1: Frappe trả 0 cho Int chưa đặt, nên 0 nghĩa là trống (validate chặn ≤ 0)
POSITIVE = (
	"min_time_study_cases",
	"approval_reminder_days",
	"price_valid_months",
	"benchmark_window_months",
	"min_benchmark_facilities",
)


def is_unset(fieldname, value):
	return value in (None, "") or (fieldname in POSITIVE and not value)


def get(fieldname):
	"""Giá trị NC Settings hiện hành; trống thì mặc định. Trường lạ → KeyError (lỗi lập trình)."""
	default = DEFAULTS[fieldname]
	value = frappe.db.get_single_value("NC Settings", fieldname)
	return default if is_unset(fieldname, value) else value
