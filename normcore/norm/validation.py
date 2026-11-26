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
COST_LEVELS = ("RESULT", "TUBE", "BATCH", "DAY", "PERIOD")  # FR-NORM-018
COST_LEVEL_LABELS = {
	"RESULT": "Theo kết quả",
	"TUBE": "Theo ống mẫu",
	"BATCH": "Theo mẻ",
	"DAY": "Theo ngày-máy",
	"PERIOD": "Theo kỳ",
}
ATTACH_TO = ("Hệ thống xét nghiệm", "Thiết bị")  # ASM-034-09
ATTACH_SYSTEM, ATTACH_EQUIPMENT = ATTACH_TO


def _num(v) -> float:
	return float(v) if v not in (None, "") else 0.0


def is_placeholder(line: dict) -> bool:
	"""ASM-034-05: dòng giữ chỗ của mẫu: có khoản mục mẫu, không từ quy trình, chưa có lượng, không loại trừ."""
	return bool(
		line.get("template_item")
		and not line.get("procedure_resource_row")
		and _num(line.get("hospital_qty")) <= 0
		and not line.get("is_excluded")
	)


def _level(line: dict) -> str:
	return line.get("cost_level") or "RESULT"


def qc_conflict(line: dict, ctx: dict) -> bool:
	"""ASM-034-10: dòng dùng mặt hàng của kế hoạch nội kiểm/chuẩn máy của hệ thống."""
	return bool(
		line.get("resource")
		and line.get("resource") in (ctx.get("qc_items") or ())
		and line.get("resource_doctype") in (None, "", "NC Item")
	)


def normalize_line(line: dict, ctx: dict) -> dict:
	"""ASM-034-07, 08, 09: đặt lại trường phụ thuộc, không báo lỗi. Trả bản sao. ctx: paraclinical, has_test_system."""
	out = dict(line)
	if not ctx.get("paraclinical"):
		out["cost_level"] = "RESULT"
		out["apply_k"] = 0
		out["attach_to"] = None
		out["attach_equipment"] = None
		return out
	if out.get("cost_level") not in COST_LEVELS:
		out["cost_level"] = out.get("cost_level") or "RESULT"
	if out["cost_level"] not in ("DAY", "PERIOD"):
		out["attach_to"] = None
		out["attach_equipment"] = None
	if out.get("attach_to") != ATTACH_EQUIPMENT:
		out["attach_equipment"] = None
	if (
		out.get("apply_k")
		and out["cost_level"] == "RESULT"
		and out.get("component") in MATERIAL
		and ctx.get("has_test_system")
	):
		out["wastage_rate"] = 0  # TC-CLS-30: bật k thì hao hụt về 0
		out["wastage_reason"] = None
	return out


def line_errors(line: dict, ctx: dict) -> list[str]:
	"""ctx: step_ids (tập mã bước của quy trình), wastage_cap (phần trăm), changed (dòng mới hoặc bị sửa).
	FEAT-034: paraclinical, has_test_system, qc_items, template_items (đều tùy chọn)."""
	lid = line.get("line_id") or "dòng mới"
	errors: list[str] = []
	component = line.get("component")
	excluded = bool(line.get("is_excluded"))
	holder = is_placeholder(line) and not ctx.get("changed")  # ASM-034-05
	missing = []
	if not component:
		missing.append("Cấu phần")
	if ctx.get("changed") and not line.get("resource"):
		missing.append("Nguồn lực")
	if not line.get("uom") and not holder:
		missing.append("Đơn vị")
	if component == "LABOR":
		if _num(line.get("headcount")) < 1 and not holder:
			missing.append("Số người")
		if _num(line.get("hospital_qty")) <= 0 and not excluded and not holder:
			missing.append("Số phút")
	elif _num(line.get("hospital_qty")) <= 0 and not excluded and not holder:
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
	errors += _cls_errors(line, ctx, lid, component)
	return errors


def _cls_errors(line: dict, ctx: dict, lid: str, component) -> list[str]:
	"""FEAT-034: cấp phát sinh, DI-17, gắn với, nội kiểm (FR-NORM-024), khoản mục mẫu."""
	errors: list[str] = []
	level = _level(line)
	if level not in COST_LEVELS:
		errors.append(f"Dòng {lid}: cấp phát sinh {level} không thuộc danh sách")
	if line.get("apply_k"):  # DI-17
		if level != "RESULT":
			errors.append(f"Dòng {lid}: chỉ bật Nhân k ở dòng Theo kết quả")
		elif component not in MATERIAL:
			errors.append(f"Dòng {lid}: chỉ bật Nhân k ở dòng thuốc, hóa chất, vật tư")
		elif not ctx.get("has_test_system"):
			errors.append(f"Dòng {lid}: chỉ bật Nhân k ở bộ có hệ thống xét nghiệm")
	if level in ("DAY", "PERIOD"):  # ASM-034-09
		attach = line.get("attach_to")
		if not attach:
			errors.append(f"Dòng {lid} thiếu: Gắn với")
		elif attach not in ATTACH_TO:
			errors.append(f"Dòng {lid}: Gắn với {attach} không thuộc danh sách")
		elif attach == ATTACH_SYSTEM and not ctx.get("has_test_system"):
			errors.append(f"Dòng {lid}: chỉ gắn với Hệ thống xét nghiệm ở bộ có hệ thống xét nghiệm")
		elif attach == ATTACH_EQUIPMENT and not line.get("attach_equipment"):
			errors.append(f"Dòng {lid} thiếu: Thiết bị được gắn")
	if ctx.get("changed") and qc_conflict(line, ctx):  # FR-NORM-024, TC-CLS-31
		errors.append(
			f"Dòng {lid}: {line['resource']} đã có trong kế hoạch nội kiểm/chuẩn máy của hệ thống xét nghiệm, "
			"không làm dòng định mức (tính từ kế hoạch chất lượng)"
		)
	item = line.get("template_item")
	if item and item not in (ctx.get("template_items") or ()):  # ASM-034-23
		errors.append(f"Dòng {lid}: khoản mục {item} không thuộc mẫu định mức của bộ")
	return errors


def _satisfied(item_name: str, lines) -> bool:
	"""ASM-034-11: có dòng mang khoản mục, có lượng hoặc đã loại trừ với lý do hợp lệ."""
	for ln in lines:
		if ln.get("template_item") != item_name:
			continue
		if ln.get("is_excluded"):
			if ln.get("exclude_reason") in EXCLUDE_REASONS:
				return True
		elif _num(ln.get("hospital_qty")) > 0:
			return True
	return False


def mandatory_status(items, lines) -> list[dict]:
	"""FR-NORM-023: mỗi khoản mục của mẫu đã được đáp ứng chưa."""
	lines = list(lines)
	return [
		{"item_name": it.get("item_name"), "satisfied": _satisfied(it.get("item_name"), lines)}
		for it in items or ()
	]


def set_blockers(head: dict, lines, ctx: dict) -> list[str]:
	"""Lỗi cấp bộ chặn "Xác nhận chuyên môn" (FR-NORM-020, 023, 024, ASM-034-01).
	head: test_system, tests_per_tube. ctx: ts_required, qc_items, mandatory_items (dict có item_name, is_mandatory)."""
	lines = list(lines)
	out: list[str] = []
	if ctx.get("ts_required") and not head.get("test_system"):
		out.append("Chưa gắn hệ thống xét nghiệm")
	if _num(head.get("tests_per_tube")) <= 0:
		tube = [ln.get("line_id") for ln in lines if _level(ln) == "TUBE" and not ln.get("is_excluded")]
		if tube:
			out.append(
				"Chưa nhập Số xét nghiệm bình quân trên một ống mẫu "
				f"(dòng Theo ống mẫu: {', '.join(str(t) for t in tube)})"
			)
	mandatory = [it for it in ctx.get("mandatory_items") or () if it.get("is_mandatory", True)]
	missing = [s["item_name"] for s in mandatory_status(mandatory, lines) if not s["satisfied"]]
	if missing:
		out.append(f"Thiếu khoản mục bắt buộc của mẫu: {', '.join(missing)}")
	for ln in lines:
		if not ln.get("is_excluded") and qc_conflict(ln, ctx):
			out.append(f"Dòng {ln.get('line_id')} dùng mặt hàng của kế hoạch chất lượng: {ln['resource']}")
	return out


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
