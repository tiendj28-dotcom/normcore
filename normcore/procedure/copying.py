"""Sao chép cấu trúc quy trình với mã mới (FR-PROC-013, giả định G4). Thuần Python."""

from normcore.procedure.codes import next_code


def copy_structure(steps, resources, citations):
	"""Cấp lại mã bước từ S001 theo thứ tự hiển thị và mã dòng từ R001; ánh xạ `step_id` của nguồn lực
	và trích dẫn theo mã mới. Trả dict `steps`, `resources`, `citations`, `next_step_seq`, `next_resource_seq`."""
	step_map, new_steps, counter = {}, [], 0
	for s in steps:
		counter, code = next_code("S", counter, [])
		step_map[s["step_id"]] = code
		new_steps.append({**s, "step_id": code})
	new_resources, rcounter = [], 0
	for r in resources:
		rcounter, code = next_code("R", rcounter, [])
		new_resources.append({**r, "resource_row_id": code, "step_id": step_map[r["step_id"]]})
	new_citations = [
		{**c, "target_step_id": step_map[c["target_step_id"]] if c.get("target_step_id") else None}
		for c in citations
	]
	return {
		"steps": new_steps,
		"resources": new_resources,
		"citations": new_citations,
		"next_step_seq": counter,
		"next_resource_seq": rcounter,
	}
