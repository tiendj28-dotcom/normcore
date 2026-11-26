"""Khảo sát bấm giờ (FR-TS-001..005, UC-010). Hàm thuần, không import frappe, không đổi dữ liệu đầu vào."""

import statistics
from datetime import date

BASIS = "Bấm giờ"
LABOR_DOCTYPE = "NC Job Title"
EQUIPMENT_DOCTYPE = "NC Equipment"


def _num(v) -> float:
	return float(v) if v not in (None, "") else 0.0


def lines_from_procedure(steps: list[dict], resources: list[dict]) -> list[dict]:
	"""Nạp dòng phiếu theo thứ tự bước của quy trình (FR-TS-001, ASM-014-02)."""
	out: list[dict] = []
	for step in sorted(steps, key=lambda s: s.get("idx") or 0):
		sid = step["step_id"]
		added = False
		for r in resources:
			if r.get("step_id") != sid:
				continue
			if r.get("resource_type") == "Nhân lực":
				out.append(
					{"step_id": sid, "job_title": r.get("linked_name"), "headcount": r.get("headcount") or 1}
				)
				added = True
			elif r.get("resource_type") == "Thiết bị":
				out.append({"step_id": sid, "equipment": r.get("linked_name")})
				added = True
		if not added:
			out.append({"step_id": sid})
	return out


def line_errors(lines: list[dict], step_ids) -> list[str]:
	"""Kiểm dòng phiếu (FR-TS-002, ASM-014-07). Rỗng = hợp lệ."""
	step_ids = set(step_ids)
	errors: list[str] = []
	seen: set[tuple] = set()
	for i, ln in enumerate(lines, start=1):
		tag = f"Dòng {i}"
		sid = ln.get("step_id")
		job, eq = ln.get("job_title"), ln.get("equipment")
		labor, machine = _num(ln.get("labor_minutes")), _num(ln.get("machine_minutes"))
		if sid not in step_ids:
			errors.append(f"{tag}: mã bước {sid} không có trong quy trình.")
		if job and eq:
			errors.append(f"{tag}: một dòng chỉ có chức danh hoặc thiết bị, không có cả hai.")
		if labor < 0 or machine < 0:
			errors.append(f"{tag}: số phút không được âm.")
		if labor > 0 and not job:
			errors.append(f"{tag}: có số phút nhân lực nhưng chưa chọn chức danh.")
		if machine > 0 and not eq:
			errors.append(f"{tag}: có số phút máy nhưng chưa chọn thiết bị.")
		if labor > 0 and _num(ln.get("headcount")) < 1:
			errors.append(f"{tag}: số người phải từ 1 trở lên khi có số phút nhân lực.")
		key = (sid, job) if job else (sid, "eq", eq) if eq else None
		if key:
			if key in seen:
				errors.append(f"{tag}: trùng bước và chức danh/thiết bị với dòng trước.")
			seen.add(key)
	return errors


def median(values: list[float]) -> float:
	return statistics.median(values)


def collect(cases: list[dict]) -> dict:
	"""Gom số phút theo (bước, loại, nguồn lực); bỏ giá trị ≤ 0 (UC-010 2a, ASM-014-03)."""
	groups: dict[tuple, list[float]] = {}
	for case in cases:
		for ln in case.get("lines") or []:
			sid = ln.get("step_id")
			if ln.get("job_title") and _num(ln.get("labor_minutes")) > 0:
				groups.setdefault((sid, "labor", ln["job_title"]), []).append(_num(ln["labor_minutes"]))
			if ln.get("equipment") and _num(ln.get("machine_minutes")) > 0:
				groups.setdefault((sid, "equipment", ln["equipment"]), []).append(_num(ln["machine_minutes"]))
	return groups


def summarize(cases: list[dict], min_cases: int, step_order: dict) -> dict:
	groups = collect(cases)
	dates = [c["observed_on"] for c in cases if c.get("observed_on")]
	rows = [
		{
			"step_id": sid,
			"kind": kind,
			"resource": res,
			"median_minutes": median(vals),
			"n": len(vals),
		}
		for (sid, kind, res), vals in groups.items()
	]
	rows.sort(key=lambda r: (step_order.get(r["step_id"], 1 << 30), r["kind"] != "labor", r["resource"]))
	return {
		"n_cases": len(cases),
		"min_cases": min_cases,
		"sufficient": len(cases) >= min_cases,
		"first_date": min(dates) if dates else None,
		"last_date": max(dates) if dates else None,
		"rows": rows,
	}


def _fmt(d) -> str:
	if isinstance(d, str):
		d = date.fromisoformat(d[:10])
	return d.strftime("%d/%m/%Y")


def basis_ref(n_cases: int, first_date, last_date) -> str:
	if not first_date or not last_date:
		return f"{n_cases} ca bấm giờ"
	return f"{n_cases} ca bấm giờ, {_fmt(first_date)}–{_fmt(last_date)}"


def plan_apply(norm_lines: list[dict], rows: list[dict], ref: str) -> tuple[list[dict], list[dict]]:
	"""Ghép kết quả với dòng LABOR/EQUIPMENT của bộ định mức (FR-TS-004, ASM-014-06)."""
	updates: list[dict] = []
	unmatched: list[dict] = []
	for row in rows:
		doctype = LABOR_DOCTYPE if row["kind"] == "labor" else EQUIPMENT_DOCTYPE
		hits = [
			ln
			for ln in norm_lines
			if not ln.get("service_level")
			and ln.get("step_id") == row["step_id"]
			and ln.get("resource_doctype") == doctype
			and ln.get("resource") == row["resource"]
		]
		if not hits:
			unmatched.append({"step_id": row["step_id"], "kind": row["kind"], "resource": row["resource"]})
		for ln in hits:
			updates.append(
				{
					"line_id": ln["line_id"],
					"hospital_qty": row["median_minutes"],
					"basis": BASIS,
					"basis_ref": ref,
				}
			)
	return updates, unmatched
