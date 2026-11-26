"""Kiểm tra nhất quán quy trình (FR-AI-006, UC-005 bước 6).

Module thuần, không phụ thuộc framework. Mục (1)(2) kiểm bằng quy tắc; mục (3) do AI đề xuất,
`parse_contra` chỉ lọc kết quả AI.
"""

from normcore.ai import citation
from normcore.procedure.ai_draft import LABOR, SECTION_KEYS

PREP_PHASE = "Chuẩn bị"
PREP_CHECK_TYPES = ("Thuốc", "Hóa chất", "Dịch truyền", "Vật tư", "Thiết bị", "Phòng", "Khác")
MAX_EXPLANATION = 500
CONTRA_SECTIONS = tuple(k for k in SECTION_KEYS if k != "contraindications")


def resource_key(r):
	if r.get("linked_doctype") and r.get("linked_name"):
		return ("link", r["linked_doctype"], r["linked_name"])
	return ("text", r.get("resource_type"), citation.normalize(r.get("resource_text")).casefold())


def _ordered_steps(steps):
	return sorted(steps or [], key=lambda s: (s.get("idx") or 0))


def _step_rank(steps):
	return {s["step_id"]: i for i, s in enumerate(_ordered_steps(steps))}


def preparation_gaps(steps, resources):
	rank = _step_rank(steps)
	prep_ids = {s["step_id"] for s in steps or [] if s.get("phase") == PREP_PHASE}
	if not prep_ids:
		return [{"kind": "no_preparation_step"}]
	rows = sorted(
		(r for r in resources or [] if r.get("step_id") in rank and r.get("resource_type") in PREP_CHECK_TYPES),
		key=lambda r: (rank[r["step_id"]], str(r.get("resource_row_id") or "")),
	)
	in_prep, elsewhere = {}, {}
	for r in rows:
		target = in_prep if r["step_id"] in prep_ids else elsewhere
		g = target.setdefault(resource_key(r), {"rows": [], "steps": [], "label": r.get("resource_text")})
		g["rows"].append(r.get("resource_row_id"))
		if r["step_id"] not in g["steps"]:
			g["steps"].append(r["step_id"])
	out = []
	for key, g in elsewhere.items():
		if key not in in_prep:
			out.append(("missing_in_preparation", g))
	for key, g in in_prep.items():
		if key not in elsewhere:
			out.append(("unused_in_steps", g))
	out.sort(key=lambda kg: rank[kg[1]["steps"][0]])
	return [
		{"kind": k, "resource_row_ids": g["rows"], "step_ids": g["steps"], "label": g["label"]}
		for k, g in out
	]


def steps_without_performer(steps, resources):
	has = {r.get("step_id") for r in resources or [] if r.get("resource_type") == LABOR}
	return [
		{"kind": "no_performer", "step_ids": [s["step_id"]], "label": s.get("step_title")}
		for s in _ordered_steps(steps)
		if s["step_id"] not in has
	]


def _message(i):
	ids = ", ".join(i.get("step_ids") or [])
	kind = i["kind"]
	if kind == "missing_in_preparation":
		return f'Nguồn lực "{i["label"]}" dùng ở bước {ids} nhưng chưa có ở phần chuẩn bị'
	if kind == "unused_in_steps":
		return f'Nguồn lực "{i["label"]}" có ở phần chuẩn bị ({ids}) nhưng không dùng ở bước nào'
	if kind == "no_preparation_step":
		return "Quy trình chưa có bước nào ở giai đoạn Chuẩn bị"
	return f'Bước {ids} "{i["label"]}" chưa có người thực hiện (nguồn lực Nhân lực)'


def rule_issues(steps, resources):
	issues = preparation_gaps(steps, resources) + steps_without_performer(steps, resources)
	return [{**i, "message": _message(i)} for i in issues]


def contra_variables(doc):
	return {
		"contraindications": doc.get("contraindications") or "",
		"indications": doc.get("indications") or "",
		"sections": {k: doc.get(k) or "" for k in CONTRA_SECTIONS if k != "indications" and k != "references"},
		"steps": doc.get("steps") or [],
		"resources": doc.get("resources") or [],
	}


def parse_contra(data, step_ids, row_ids, contraindications):
	items = data.get("issues") if isinstance(data, dict) else None
	if not isinstance(items, list):
		return [], 0
	step_ids, row_ids = set(step_ids or []), set(row_ids or [])
	out, rejected = [], 0
	for it in items:
		if not isinstance(it, dict):
			rejected += 1
			continue
		targets = {k: it[k] for k in ("step_id", "resource_row_id", "section") if it.get(k)}
		explanation = it.get("explanation")
		ok = len(targets) == 1 and isinstance(explanation, str) and explanation.strip()
		if ok:
			k, v = next(iter(targets.items()))
			ok = (
				(k == "step_id" and v in step_ids)
				or (k == "resource_row_id" and v in row_ids)
				or (k == "section" and v in CONTRA_SECTIONS)
			)
		if ok:
			ok = isinstance(it.get("excerpt"), str) and citation.quote_in_text(it["excerpt"], contraindications)
		if not ok:
			rejected += 1
			continue
		out.append({**targets, "excerpt": it["excerpt"], "explanation": explanation.strip()[:MAX_EXPLANATION]})
	return out, rejected
