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
