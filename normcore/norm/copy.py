"""Sao chép bộ định mức sang hệ thống khác (FR-NORM-025, ASM-034-13). Hàm thuần."""

CONFIRM_KEYS = ("confirmed_by", "confirmed_on")


def copy_lines(lines, step_ids, resource_rows, equipment_map, qc_items, inputs=None):
	"""Trả (dòng mới, dòng bỏ [{line_id, reason}]).
	step_ids: mã bước của quy trình đích; resource_rows: mã dòng nguồn lực còn ở quy trình đích;
	equipment_map: {thiết bị nguồn: thiết bị đích}; qc_items: mặt hàng kế hoạch chất lượng của hệ thống đích;
	inputs: tên trường được sao chép (mặc định mọi trường trừ xác nhận)."""
	step_ids, resource_rows, qc_items = set(step_ids or ()), set(resource_rows or ()), set(qc_items or ())
	kept, skipped = [], []
	for ln in lines:
		lid = ln.get("line_id")
		if not ln.get("service_level") and ln.get("step_id") not in step_ids:
			skipped.append(
				{"line_id": lid, "reason": f"Mã bước {ln.get('step_id')} không còn trong quy trình"}
			)
			continue
		row = ln.get("procedure_resource_row")
		if row and row not in resource_rows:  # ASM-034-26: dòng nguồn lực gốc không còn ở quy trình đích
			skipped.append({"line_id": lid, "reason": f"Dòng nguồn lực {row} không còn trong quy trình"})
			continue
		if (
			ln.get("resource")
			and ln["resource"] in qc_items
			and ln.get("resource_doctype") in (None, "", "NC Item")
		):
			skipped.append({"line_id": lid, "reason": "Mặt hàng thuộc kế hoạch chất lượng của hệ thống đích"})
			continue
		new = {k: v for k, v in ln.items() if (inputs is None or k in inputs) and k not in CONFIRM_KEYS}
		if new.get("attach_equipment") in (equipment_map or {}):
			new["attach_equipment"] = equipment_map[new["attach_equipment"]]
		kept.append(new)
	return kept, skipped
