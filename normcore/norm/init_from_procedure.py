"""FR-NORM-001: dòng định mức sinh từ dòng nguồn lực của quy trình (ASM-012-02, ASM-012-03). Hàm thuần."""

COMPONENT_BY_RESOURCE_TYPE = {
	"Nhân lực": "LABOR",
	"Thuốc": "DRUG",
	"Hóa chất": "DRUG",
	"Dịch truyền": "DRUG",
	"Vật tư": "SUPPLY",
	"Thiết bị": "EQUIPMENT",
	"Phòng": "INFRA",
	"Khác": "SUPPLY",
}
RESOURCE_DOCTYPE_BY_COMPONENT = {  # DI-05
	"LABOR": "NC Job Title",
	"DRUG": "NC Item",
	"SUPPLY": "NC Item",
	"UTILITY": "NC Item",
	"EQUIPMENT": "NC Equipment",
	"INFRA": "NC Room",
}


def lines_from_resources(resources) -> tuple[list[dict], list[str]]:
	"""Mỗi dòng nguồn lực một dòng định mức, giữ thứ tự. Trả (dòng, lỗi).
	Lỗi: dòng Nhân lực chưa gắn NC Job Title (ASM-012-03, Quyết định Lead Q2)."""
	lines, errors = [], []
	for r in resources:
		component = COMPONENT_BY_RESOURCE_TYPE.get(r.get("resource_type"), "SUPPLY")
		doctype = RESOURCE_DOCTYPE_BY_COMPONENT[component]
		linked = r.get("linked_name") if r.get("linked_doctype") == doctype else None
		if component == "LABOR" and not linked:
			errors.append(f"Dòng nguồn lực {r.get('resource_row_id')} chưa gắn chức danh (NC Job Title)")
		lines.append(
			{
				"step_id": r.get("step_id"),
				"procedure_resource_row": r.get("resource_row_id"),
				"component": component,
				"resource_doctype": doctype,
				"resource": linked or None,
				"headcount": (r.get("headcount") or 1) if component == "LABOR" else None,
				"hospital_qty": r.get("quantity"),
				"uom": r.get("uom"),
				"basis": "Quy trình",
				"ai_suggested": 0,
			}
		)
	return lines, errors


# FEAT-013, FR-NORM-015: mang dòng sang phiên bản theo quy trình mới (TC-NORM-08, AMD-013-01).
_NOT_CARRIED = ("confirmed_by", "confirmed_on")


def carry_lines(old_lines, step_ids) -> dict:
	"""Giữ thứ tự dòng nguồn. Dòng Chung hoặc có bước còn trong quy trình mới: mang sang;
	dòng có bước đã bỏ: mang sang kèm step_removed = 1. Không mang xác nhận. Không đổi đầu vào."""
	valid = set(step_ids)
	lines, carried, removed, removed_steps = [], [], [], []
	for old in old_lines:
		line = {k: v for k, v in old.items() if k not in _NOT_CARRIED}
		step = line.get("step_id")
		if line.get("service_level") or step in valid or not step:
			line["step_removed"] = 0
			carried.append(line.get("line_id"))
		else:
			line["step_removed"] = 1
			removed.append(line.get("line_id"))
			if step not in removed_steps:
				removed_steps.append(step)
		lines.append(line)
	return {
		"lines": lines,
		"carried": carried,
		"removed": removed,
		"removed_steps": removed_steps,
		"step_order": list(step_ids),
	}


def steps_without_lines(step_ids, lines) -> list[str]:
	"""Bước của quy trình chưa có dòng nào (dòng loại trừ vẫn là có dòng; dòng Chung, dòng cờ bước đã bỏ không tính)."""
	have = {
		ln.get("step_id")
		for ln in lines
		if ln.get("step_id") and not ln.get("service_level") and not ln.get("step_removed")
	}
	return [s for s in step_ids if s not in have]


def removed_flag(row, before, step_ids, creating_version) -> int:
	"""Chuẩn hóa step_removed (technical-design 2.3): giữ 1 chỉ khi bước không còn, không Chung,
	và dòng cũ đã có cờ hoặc bộ đang được tạo bởi new_version."""
	step = row.get("step_id")
	if not step or row.get("service_level") or step in step_ids:
		return 0
	return 1 if (creating_version or (before or {}).get("step_removed")) else 0


def format_note(res, missing) -> str:
	"""Ghi chú Comment cho bộ mới theo quy trình mới."""

	def part(items):
		return ", ".join(items) if items else "không có"

	removed_by_line = {ln.get("line_id"): ln.get("step_id") for ln in res["lines"] if ln.get("step_removed")}
	carried_steps = {
		ln.get("step_id")
		for ln in res["lines"]
		if not ln.get("step_removed") and not ln.get("service_level") and ln.get("step_id")
	}
	order = [s for s in res.get("step_order", []) if s in carried_steps]
	order += sorted(carried_steps - set(order))
	removed_txt = [f"{removed_by_line[lid]} ({lid})" for lid in res["removed"] if lid in removed_by_line]
	return (
		f"Theo quy trình mới: mang sang {part(order)}; "
		f"đánh dấu bước đã bỏ {part(removed_txt)}; bước chưa có dòng {part(list(missing))}"
	)
