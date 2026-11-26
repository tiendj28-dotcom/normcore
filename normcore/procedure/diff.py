"""So sánh hai phiên bản quy trình theo phần, bước, dòng nguồn lực (FR-WF-010) và liệt kê bước thêm, bỏ, đổi
(FR-WF-011). Thuần Python."""

STEP_COMPARE = ("phase", "step_title", "description", "reference_minutes")
RESOURCE_COMPARE = (
	"step_id",
	"resource_type",
	"resource_text",
	"linked_doctype",
	"linked_name",
	"quantity",
	"uom",
	"headcount",
)
EMPTY_NOTE = "Không có bước thêm, bỏ, đổi"


def _norm(v):
	"""None và chuỗi rỗng bằng nhau; số so bằng float; chuỗi strip."""
	if v is None:
		return ""
	if isinstance(v, (bool, int, float)):
		return float(v)
	return str(v).strip()


def _status(old, new):
	o, n = _norm(old), _norm(new)
	if o == n:
		return "same"
	if o == "":
		return "added"
	if n == "":
		return "removed"
	return "changed"


def _changed_fields(a, b, fields):
	return [f for f in fields if _norm(a.get(f)) != _norm(b.get(f))]


def diff_sections(old, new, sections):
	out = []
	for key, label in sections:
		if key == "steps":
			continue
		o, n = old.get(key), new.get(key)
		out.append({"key": key, "label": label, "status": _status(o, n), "old": o, "new": n})
	return out


def diff_steps(old_steps, new_steps):
	old_by = {s["step_id"]: (i, s) for i, s in enumerate(old_steps)}
	new_ids = {s["step_id"] for s in new_steps}
	removed_after = {}  # id bước đứng trước ở bản cũ -> các bước bị bỏ
	prev = None
	for s in old_steps:
		if s["step_id"] not in new_ids:
			removed_after.setdefault(prev, []).append(s)
		else:
			prev = s["step_id"]

	def removed_item(s):
		return {
			"step_id": s["step_id"],
			"status": "removed",
			"fields": [],
			"old": s,
			"new": None,
			"old_idx": old_by[s["step_id"]][0],
			"new_idx": None,
		}

	out = [removed_item(s) for s in removed_after.get(None, [])]
	for i, s in enumerate(new_steps):
		sid = s["step_id"]
		if sid not in old_by:
			out.append(
				{"step_id": sid, "status": "added", "fields": [], "old": None, "new": s, "old_idx": None, "new_idx": i}
			)
		else:
			oi, o = old_by[sid]
			fields = _changed_fields(o, s, STEP_COMPARE)
			item = {
				"step_id": sid,
				"status": "changed" if fields else "same",
				"fields": fields,
				"old": o,
				"new": s,
				"old_idx": oi,
				"new_idx": i,
			}
			if not fields and oi != i:
				item["moved"] = True
			out.append(item)
		out.extend(removed_item(r) for r in removed_after.get(sid, []))
	return out


def diff_resources(old_res, new_res):
	old_by = {r["resource_row_id"]: r for r in old_res}
	new_by = {r["resource_row_id"]: r for r in new_res}
	out = []
	for r in new_res:
		rid = r["resource_row_id"]
		o = old_by.get(rid)
		if o is None:
			out.append(
				{"resource_row_id": rid, "step_id": r.get("step_id"), "status": "added", "fields": [], "old": None, "new": r}
			)
			continue
		fields = _changed_fields(o, r, RESOURCE_COMPARE)
		out.append(
			{
				"resource_row_id": rid,
				"step_id": r.get("step_id"),
				"status": "changed" if fields else "same",
				"fields": fields,
				"old": o,
				"new": r,
			}
		)
	for rid, o in old_by.items():
		if rid not in new_by:
			out.append(
				{"resource_row_id": rid, "step_id": o.get("step_id"), "status": "removed", "fields": [], "old": o, "new": None}
			)
	return out


def _count(items):
	return {k: sum(1 for i in items if i["status"] == k) for k in ("added", "removed", "changed")}


def diff_procedures(old, new, sections):
	secs = diff_sections(old, new, sections)
	steps = diff_steps(old.get("steps") or [], new.get("steps") or [])
	res = diff_resources(old.get("resources") or [], new.get("resources") or [])
	return {
		"sections": secs,
		"steps": steps,
		"resources": res,
		"summary": {"sections": _count(secs), "steps": _count(steps), "resources": _count(res)},
	}


def step_changes(old, new):
	"""Mã bước thêm, bỏ, đổi (FR-WF-011). Bước "đổi" = trường bước đổi hoặc có dòng nguồn lực thêm, bỏ, đổi
	gắn bước đó; dòng nguồn lực của bước bị bỏ hoặc mới thêm không làm bước đó thành "đổi"."""
	steps = diff_steps(old.get("steps") or [], new.get("steps") or [])
	added = {s["step_id"] for s in steps if s["status"] == "added"}
	removed = {s["step_id"] for s in steps if s["status"] == "removed"}
	changed = {s["step_id"] for s in steps if s["status"] == "changed"}
	for r in diff_resources(old.get("resources") or [], new.get("resources") or []):
		if r["status"] == "same":
			continue
		for side in ("old", "new"):
			row = r[side]
			if row and row.get("step_id"):
				changed.add(row["step_id"])
	changed -= added | removed
	return {"added": sorted(added), "removed": sorted(removed), "changed": sorted(changed)}


def format_step_note(changes):
	parts = []
	for key, label in (("added", "thêm"), ("removed", "bỏ"), ("changed", "đổi")):
		if changes.get(key):
			parts.append(f"{label} {', '.join(changes[key])}")
	return "; ".join(parts) if parts else EMPTY_NOTE
