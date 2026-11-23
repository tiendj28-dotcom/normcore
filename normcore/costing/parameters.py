"""Kiểm giá trị bộ tham số tính giá (FR-RES-009). Hàm thuần Python (ADR-003).

Mặc định: ASM-063, ASM-064; ba tham số [1.1] theo FR-RES-009 (ZERO, 5%, 2%).
"""

ACCUMULATION_MODES = ("NONE", "ON_COST", "ON_PRICE")
EXPIRED_MODES = ("ZERO", "CONTINUE")
COST_CATEGORIES = ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT", "EXCLUDED")

DEFAULTS = {
	"wastage_cap": 10,
	"accumulation_mode": "ON_COST",
	"accumulation_rate": 5,
	"obligation_rate": 0,
	"electricity_price": 0,
	"water_price": 0,
	"rounding_unit": 100,
	"reconciliation_tolerance": 10,
	"comparison_tolerance": 10,
	"expired_depreciation_mode": "ZERO",
	"material_recon_tolerance": 5,
	"volume_recon_tolerance": 2,
	"eqa_cost_category": "DRUG_SUPPLY",
	"rental_cost_category": "DEPRECIATION",
	"jv_cost_category": "DEPRECIATION",
}

_PERCENT_LABELS = {
	"employer_contribution_rate": "Tỷ lệ đóng góp của đơn vị",
	"wastage_cap": "Trần hao hụt",
	"reconciliation_tolerance": "Ngưỡng đối soát",
	"comparison_tolerance": "Ngưỡng lệch so sánh",
	"material_recon_tolerance": "Ngưỡng đối soát vật chất",
	"volume_recon_tolerance": "Ngưỡng đối soát sản lượng",
}
# Engine (BR-COST-013) yêu cầu tỷ lệ trong [0, 1): ở đây là phần trăm nên < 100
_BELOW_100 = {"accumulation_rate": "Tỷ lệ tích lũy", "obligation_rate": "Tỷ lệ nghĩa vụ tài chính"}
_POSITIVE = {"working_days_per_year": "Số ngày làm việc năm", "working_hours_per_day": "Số giờ làm việc ngày"}
_CHOICES = {
	"accumulation_mode": ("Cách tính tích lũy", ACCUMULATION_MODES),
	"expired_depreciation_mode": ("Khấu hao thiết bị hết thời gian sử dụng", EXPIRED_MODES),
	"eqa_cost_category": ("Loại chi phí của phí ngoại kiểm", COST_CATEGORIES),
	"rental_cost_category": ("Loại chi phí của tiền thuê máy", COST_CATEGORIES),
	"jv_cost_category": ("Loại chi phí của hợp đồng liên doanh, liên kết", COST_CATEGORIES),
}


def _num(values, key):
	v = values.get(key)
	return None if v in (None, "") else float(v)


def check_ranges(values: dict) -> list[str]:
	"""Trả danh sách lỗi tiếng Việt; giá trị trống bị bỏ qua (kiểm bắt buộc là việc của DocType)."""
	errors = []
	for key, label in _PERCENT_LABELS.items():
		v = _num(values, key)
		if v is not None and not 0 <= v <= 100:
			errors.append(f"{label} phải trong khoảng 0 đến 100%")
	for key, label in _BELOW_100.items():
		v = _num(values, key)
		if v is not None and not 0 <= v < 100:
			errors.append(f"{label} phải từ 0 đến dưới 100%")
	for key, label in _POSITIVE.items():
		v = _num(values, key)
		if v is not None and v <= 0:
			errors.append(f"{label} phải lớn hơn 0")
	v = _num(values, "rounding_unit")
	if v is not None and v < 1:
		errors.append("Đơn vị làm tròn phải từ 1 trở lên")
	for key, (label, allowed) in _CHOICES.items():
		v = values.get(key)
		if v not in (None, "") and v not in allowed:
			errors.append(f"{label}: giá trị không hợp lệ ({v})")
	return errors
