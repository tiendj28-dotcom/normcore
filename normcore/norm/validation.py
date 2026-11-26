"""Kiểm dòng định mức (FR-NORM-003..014, DI-04, DI-05). Hàm thuần, nhận dict dòng; không đổi dữ liệu.
FEAT-034 nối thêm luật vào cùng hàm, giữ chữ ký."""

from datetime import date

from normcore.costing import parameters
from normcore.norm.init_from_procedure import RESOURCE_DOCTYPE_BY_COMPONENT

COMPONENTS = ("LABOR", "DRUG", "SUPPLY", "EQUIPMENT", "INFRA", "UTILITY")
BASIS_VALUES = ("Quy trình", "Bấm giờ", "Tiêu hao thực tế", "Định mức ban hành", "Ước tính")
EXCLUDE_REASONS = (
	"Thanh toán riêng",
	"Ngân sách nhà nước bảo đảm",
	"Đã tính trong dịch vụ khác",
	"Không áp dụng",
	"Khác",
)
MATERIAL = ("DRUG", "SUPPLY")


def _num(v) -> float:
	return float(v) if v not in (None, "") else 0.0


def line_errors(line: dict, ctx: dict) -> list[str]:
	"""ctx: step_ids (tập mã bước của quy trình), wastage_cap (phần trăm), changed (dòng mới hoặc bị sửa)."""
	lid = line.get("line_id") or "dòng mới"
	errors: list[str] = []
	component = line.get("component")
	excluded = bool(line.get("is_excluded"))
	missing = []
	if not component:
		missing.append("Cấu phần")
	if ctx.get("changed") and not line.get("resource"):
		missing.append("Nguồn lực")
	if not line.get("uom"):
		missing.append("Đơn vị")
	if component == "LABOR":
		if _num(line.get("headcount")) < 1:
			missing.append("Số người")
		if _num(line.get("hospital_qty")) <= 0 and not excluded:
			missing.append("Số phút")
	elif _num(line.get("hospital_qty")) <= 0 and not excluded:
		missing.append("Định mức của bệnh viện")  # ASM-012-12
	if missing:
		errors.append(f"Dòng {lid} thiếu: {', '.join(missing)}")
	if component and component not in COMPONENTS:
		errors.append(f"Dòng {lid}: cấu phần {component} không hợp lệ")

	wastage = _num(line.get("wastage_rate"))
	if wastage < 0 or wastage > 100:
		errors.append(f"Dòng {lid}: hao hụt phải trong khoảng 0..100%")
	elif (
		component in MATERIAL
		and wastage > _num(ctx.get("wastage_cap", parameters.DEFAULTS["wastage_cap"]))
		and not (line.get("wastage_reason") or "").strip()
	):
		errors.append(f"Dòng {lid}: hao hụt {wastage:g}% vượt trần, cần nhập Lý do vượt trần")  # FR-NORM-004
	if _num(line.get("authority_qty")) < 0:
		errors.append(f"Dòng {lid}: định mức ban hành không được âm")

	if not line.get("procedure_resource_row"):  # FR-NORM-005
		has_step, general = bool(line.get("step_id")), bool(line.get("service_level"))
		if has_step == general:
			errors.append(f'Dòng {lid}: chọn mã bước hoặc "Chung cho cả dịch vụ" (một trong hai)')
	if (
		line.get("step_id")
		and not line.get("service_level")
		and not line.get("step_removed")  # AMD-013-01
		and line["step_id"] not in ctx.get("step_ids", ())
	):
		errors.append(f"Dòng {lid}: mã bước {line['step_id']} không tồn tại trong quy trình")  # DI-04

	expected = RESOURCE_DOCTYPE_BY_COMPONENT.get(component)
	if expected and line.get("resource_doctype") != expected:
		errors.append(f"Dòng {lid}: cấu phần {component} phải gắn {expected}")  # DI-05

	if line.get("basis") and line["basis"] not in BASIS_VALUES:
		errors.append(f"Dòng {lid}: căn cứ {line['basis']} không thuộc danh sách")  # FR-NORM-008
	if excluded and line.get("exclude_reason") not in EXCLUDE_REASONS:
		errors.append(f"Dòng {lid}: chọn Lý do loại trừ thuộc danh sách")  # FR-NORM-013
	return errors


def _group_key(line: dict):
	return (
		"service" if line.get("service_level") else line.get("step_id"),
		line.get("resource_doctype"),
		line.get("resource"),
	)


def duplicates(lines) -> dict[str, list[str]]:
	"""FR-NORM-014: line_id -> các line_id trùng (cùng bước hoặc cùng chung, cùng nguồn lực)."""
	groups: dict = {}
	for ln in lines:
		if not ln.get("resource") or ln.get("is_excluded"):
			continue
		groups.setdefault(_group_key(ln), []).append(ln.get("line_id"))
	out = {}
	for ids in groups.values():
		if len(ids) > 1:
			for i in ids:
				out[i] = [j for j in ids if j != i]
	return out


def confirm_blockers(lines) -> list[dict]:
	"""FR-NORM-010: mỗi dòng cản một mục, lý do theo thứ tự cố định."""
	out = []
	for ln in lines:
		reasons = []
		if not ln.get("confirmed_by"):
			reasons.append("Chưa xác nhận")
		if not ln.get("resource"):
			reasons.append("Chưa liên kết danh mục")
		if ln.get("step_removed"):
			reasons.append("Thuộc bước đã bỏ")  # FR-NORM-015, AMD-013-01
		if ln.get("ai_suggested"):
			reasons.append("Còn đề xuất AI chưa xử lý")
		if reasons:
			out.append({"line_id": ln.get("line_id"), "reasons": reasons})
	return out


def effective_parameter_set(rows, today: date):
	"""ASM-012-10: bộ tham số có effective_from <= hôm nay lớn nhất, hòa thì name lớn nhất; không có → None."""
	ok = [r for r in rows if r.get("effective_from") and r["effective_from"] <= today]
	if not ok:
		return None
	return max(ok, key=lambda r: (r["effective_from"], r.get("name") or ""))
