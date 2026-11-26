import frappe

from normcore.core.settings import DEFAULTS, is_unset


def execute():
	"""FEAT-002 (FR-ADM-003): đặt mặc định cho tham số vận hành còn trống; không ghi đè giá trị đã có."""
	for field in (
		"min_time_study_cases",
		"price_valid_months",
		"benchmark_window_months",
		"min_benchmark_facilities",
		"accounting_regime",
	):
		if is_unset(field, frappe.db.get_single_value("NC Settings", field)):
			frappe.db.set_single_value("NC Settings", field, DEFAULTS[field])
