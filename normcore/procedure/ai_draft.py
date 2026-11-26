"""Đọc kết quả AI soạn dự thảo quy trình và dựng các dòng của bản nháp (FR-AI-002..005).

Module thuần: không phụ thuộc framework, test bằng pytest không cần site.
"""

from collections import namedtuple
from html import escape

from normcore.ai import citation

SECTION_KEYS = {
	"overview": "Đại cương",
	"indications": "Chỉ định",
	"contraindications": "Chống chỉ định",
	"cautions": "Thận trọng",
	"preparation_notes": "Chuẩn bị",
	"monitoring": "Theo dõi và xử trí tai biến",
	"references": "Tài liệu tham khảo",
}
PHASES = ("Chuẩn bị", "Thực hiện", "Theo dõi", "Kết thúc")
DEFAULT_PHASE = "Thực hiện"
RESOURCE_TYPES = ("Nhân lực", "Thuốc", "Hóa chất", "Dịch truyền", "Vật tư", "Thiết bị", "Phòng", "Khác")
DEFAULT_RESOURCE_TYPE = "Khác"
LABOR = "Nhân lực"
LABOR_UOM = "phút"
MAX_REASON = 1000

Draft = namedtuple("Draft", ["sections", "steps", "warnings"])
BuildResult = namedtuple(
	"BuildResult", ["sections", "steps", "resources", "citations", "rejected", "rejected_reasons", "warnings"]
)


class DraftError(Exception):
	pass


def _cits(value):
	return [c for c in (value or []) if isinstance(c, dict)]


def _number(value):
	if isinstance(value, bool):
		return None
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def parse_draft(data):
	if not isinstance(data, dict):
		raise DraftError("Kết quả AI không phải đối tượng JSON.")
	errors, warnings = [], []
	raw_sections = data.get("sections")
	raw_steps = data.get("steps")
	if not isinstance(raw_sections, dict):
		errors.append("thiếu 'sections'")
	if not isinstance(raw_steps, list) or not raw_steps:
		errors.append("thiếu 'steps' hoặc 'steps' rỗng")
	if errors:
		raise DraftError("Kết quả AI sai cấu trúc: " + "; ".join(errors) + ".")

	sections = {}
	for key in SECTION_KEYS:
		sec = raw_sections.get(key)
		sec = sec if isinstance(sec, dict) else {}
		sections[key] = {"text": str(sec.get("text") or "").strip(), "citations": _cits(sec.get("citations"))}

	steps = []
	for i, st in enumerate(raw_steps, 1):
		if not isinstance(st, dict) or not str(st.get("step_title") or "").strip() or not str(st.get("description") or "").strip():
			errors.append(f"bước {i} thiếu tên hoặc mô tả")
			continue
		phase = st.get("phase")
		if phase not in PHASES:
			warnings.append(f"Bước {i}: giai đoạn '{phase}' không hợp lệ, đặt '{DEFAULT_PHASE}'.")
			phase = DEFAULT_PHASE
		minutes = _number(st.get("reference_minutes"))
		if minutes is not None and minutes < 0:
			minutes = None
		resources = []
		for j, r in enumerate(st.get("resources") or [], 1):
			if not isinstance(r, dict):
				continue
			qty = _number(r.get("quantity"))
			if qty is None or qty <= 0:
				warnings.append(f"Bước {i}, nguồn lực {j}: số lượng không hợp lệ, bỏ dòng.")
				continue
			rtype = r.get("resource_type")
			if rtype not in RESOURCE_TYPES:
				warnings.append(f"Bước {i}, nguồn lực {j}: loại '{rtype}' không hợp lệ, đặt '{DEFAULT_RESOURCE_TYPE}'.")
				rtype = DEFAULT_RESOURCE_TYPE
			head = _number(r.get("headcount"))
			text = str(r.get("resource_text") or "").strip()
			uom = LABOR_UOM if rtype == LABOR else str(r.get("uom") or "").strip()
			if not text or not uom:
				warnings.append(f"Bước {i}, nguồn lực {j}: thiếu tên hoặc đơn vị, bỏ dòng.")
				continue
			resources.append(
				{
					"resource_type": rtype,
					"resource_text": text,
					"quantity": qty,
					"uom": uom,
					"headcount": int(head) if head and head > 0 else None,
				}
			)
		steps.append(
			{
				"phase": phase,
				"step_title": str(st["step_title"]).strip(),
				"description": str(st["description"]).strip(),
				"reference_minutes": minutes,
				"resources": resources,
				"citations": _cits(st.get("citations")),
			}
		)
	if errors:
		raise DraftError("Kết quả AI sai cấu trúc: " + "; ".join(errors) + ".")
	return Draft(sections, steps, warnings)


def resolve_deviation_reason(excerpt, doctor_request):
	excerpt = (excerpt or "").strip()
	if excerpt and citation.quote_in_text(excerpt, doctor_request or ""):
		return excerpt[:MAX_REASON]
	return (doctor_request or "").strip()[:MAX_REASON]


def _html(text):
	text = (text or "").strip()
	if not text:
		return ""
	return "".join(f"<p>{escape(p.strip())}</p>" for p in text.split("\n") if p.strip())


def build_rows(draft, sources, doctor_request):
	items, order = [], []
	for key in SECTION_KEYS:
		order.append(("section", key))
	for i in range(len(draft.steps)):
		order.append(("step", i))
	for key, sec in draft.sections.items():
		items += [dict(c, target=("section", key)) for c in sec["citations"]]
	for i, st in enumerate(draft.steps):
		items += [dict(c, target=("step", i)) for c in st["citations"]]

	res = citation.check_citations(items, sources)
	by_name = {s.get("name"): s for s in sources or []}
	citations = {t: [] for t in order}
	for it in res.kept:
		src = by_name.get(it["section"], {})
		rel = citation.REL_DEVIATION if it.get("relation") == citation.REL_DEVIATION else citation.REL_FOLLOW
		citations[it["target"]].append(
			{
				"relation": rel,
				"legal_section": it["section"],
				"legal_document": src.get("doc_number") or "",
				"quote": it["quote"],
				"deviation_reason": resolve_deviation_reason(it.get("request_excerpt"), doctor_request)
				if rel == citation.REL_DEVIATION
				else "",
			}
		)
	kept_targets = [{"target": t} for t, rows in citations.items() if rows]
	for lab in citation.label_unsupported(order, kept_targets):
		citations[lab["target"]].append({"relation": citation.REL_NONE})

	sections = {k: _html(draft.sections[k]["text"]) for k in SECTION_KEYS}
	steps = [
		{
			"phase": s["phase"],
			"step_title": s["step_title"],
			"description": s["description"],
			"reference_minutes": s["reference_minutes"],
			"ai_suggested": 1,
		}
		for s in draft.steps
	]
	resources = [[dict(r, ai_suggested=1) for r in s["resources"]] for s in draft.steps]
	reasons = {}
	for _it, why in res.rejected:
		reasons[why] = reasons.get(why, 0) + 1
	return BuildResult(sections, steps, resources, citations, len(res.rejected), reasons, list(draft.warnings))


def request_variables(doctor_request, service, current):
	return {
		"doctor_request": doctor_request,
		"service": {"service_code": service.get("service_code"), "service_name": service.get("service_name")},
		"current_procedure": current,
		"phases": list(PHASES),
		"resource_types": list(RESOURCE_TYPES),
		"section_keys": list(SECTION_KEYS),
	}
