"""Hệ thống xét nghiệm — hàm thuần Python, không import framework (ADR-003).

FR-CLS-001, FR-CLS-005, FR-CLS-006, FR-CLS-007 (khối tình trạng), FR-SVC-011 (lọc bộ định mức).
ASM-111 (miền giá trị), ASM-112 (cảnh báo tổng tỷ trọng), ASM-114, ASM-115.
Không có phép tính tiền và không có công thức hệ số k (BR-CLS-001 thuộc FEAT-036).
"""

from decimal import Decimal, InvalidOperation

from normcore.costing import qc_plans

ACTIVE = "Đang dùng"
INACTIVE = "Ngừng dùng"
STATUSES = (ACTIVE, INACTIVE)
BASIS_MINUTE = "Phút chiếm máy"

LABELS = {
	"test_system_code": "Mã hệ thống",
	"technical_service": "Dịch vụ",
	"department": "Khoa",
	"main_equipment": "Thiết bị chính",
	"volume_share_pct": "Tỷ trọng sản lượng",
	"machine_minutes_per_case": "Phút chiếm máy một ca",
	"est_rerun_rate": "Tỷ lệ chạy lại ước tính",
	"est_wastage_rate": "Tỷ lệ hao hụt ước tính",
	"status": "Trạng thái",
}
_REQUIRED = ("test_system_code", "technical_service", "department", "main_equipment", "volume_share_pct")


def _blank(v) -> bool:
	return v is None or str(v).strip() == ""


def _num(v):
	"""Decimal hoặc None khi trống; ValueError khi không phải số."""
	if _blank(v):
		return None
	try:
		return Decimal(str(v))
	except InvalidOperation as e:
		raise ValueError(str(v)) from e


def validate_test_system(values: dict, allocation_basis, service_is_paraclinical) -> list:
	"""Danh sách lỗi (rỗng = hợp lệ) theo technical-design 2.2."""
	errors = []
	for f in _REQUIRED:
		if _blank(values.get(f)):
			errors.append(f"Thiếu {LABELS[f]}")
	if not _blank(values.get("technical_service")) and not service_is_paraclinical:
		errors.append("Dịch vụ chưa được đánh dấu thuộc khối cận lâm sàng")

	def get(f):
		try:
			return _num(values.get(f))
		except ValueError:
			errors.append(f"{LABELS[f]} phải là số")
			return None

	share = get("volume_share_pct")
	if share is not None and not (0 < share <= 100):
		errors.append(f"{LABELS['volume_share_pct']} phải lớn hơn 0 và không quá 100")
	rerun = get("est_rerun_rate")
	if rerun is not None and not (0 <= rerun <= 100):
		errors.append(f"{LABELS['est_rerun_rate']} phải từ 0 đến 100")
	waste = get("est_wastage_rate")
	if waste is not None and not (0 <= waste < 100):
		errors.append(f"{LABELS['est_wastage_rate']} phải từ 0 đến dưới 100")
	minutes = get("machine_minutes_per_case")
	if allocation_basis == BASIS_MINUTE:
		if minutes is None or minutes <= 0:
			errors.append(
				f"{LABELS['machine_minutes_per_case']} là bắt buộc và phải lớn hơn 0 khi thiết bị chia theo Phút chiếm máy"
			)
	elif minutes is not None and minutes < 0:
		errors.append(f"{LABELS['machine_minutes_per_case']} phải lớn hơn 0")
	status = values.get("status")
	if not _blank(status) and status not in STATUSES:
		errors.append(f"{LABELS['status']} phải là Đang dùng hoặc Ngừng dùng")
	return errors


def in_costing_scope(systems) -> list:
	"""Mã các hệ thống đang dùng, sắp theo mã (FR-CLS-006, DI-06)."""
	return sorted(s["name"] for s in systems if s.get("status") == ACTIVE)


def norm_sets_to_cost(norm_sets, active_systems, send_out_services) -> list:
	"""Giữ bộ định mức không gắn hệ thống hoặc gắn hệ thống đang dùng, và dịch vụ không gửi ngoài."""
	active, send_out = set(active_systems), set(send_out_services)
	out = []
	for ns in norm_sets:
		if ns.get("technical_service") in send_out:
			continue
		sysname = ns.get("test_system")
		if sysname and sysname not in active:
			continue
		out.append(ns)
	return out


def share_totals(systems) -> dict:
	"""Tổng tỷ trọng các hệ thống đang dùng theo (dịch vụ, khoa) (ASM-112)."""
	totals = {}
	for s in systems:
		if s.get("status") != ACTIVE:
			continue
		key = (s["technical_service"], s["department"])
		totals[key] = totals.get(key, Decimal(0)) + Decimal(str(s["volume_share_pct"]))
	return totals


def share_warning(total) -> bool:
	return Decimal(str(total)) != 100


def status_items(volume=None, qc_plan=None, cls_group=None) -> list:
	"""Bốn mục khối tình trạng FR-CLS-007. Mục `volume` lấy từ FEAT-035 (ASM-035-10); mục `qc_plan` từ FEAT-032
	(ASM-032-08, thay khi đã có kế hoạch chất lượng); hai mục còn lại thuộc FEAT khác nên 'Chưa có' (ASM-115)."""
	spec = (
		("norm_set", "Bộ định mức hiện hành", "FEAT-034"),
		("qc_plan", "Kế hoạch chất lượng", "FEAT-032"),
		("volume", "Sản lượng kịch bản mặc định", "FEAT-035"),
		("latest_cost", "Hệ số k và giá thành lần tính gần nhất", "FEAT-036"),
	)
	out = []
	for k, lb, src in spec:
		st = {"state": "empty", "message": "Chưa có"}
		if k == "volume" and volume:
			from normcore.costing.cls_volume import volume_status

			st = volume_status(volume)
		out.append({"key": k, "label": lb, "source": src, **st})
	if qc_plan is not None:
		out[1] = qc_plans.plan_status_item(qc_plan, cls_group)
	return out
