"""Tạo bản nháp phiên bản kế tiếp từ quy trình đã ban hành (FR-WF-009, UC-007). Thuần Python."""

PUBLISHED = "Đã ban hành"
TEXT_FIELDS = (
	"overview",
	"indications",
	"contraindications",
	"cautions",
	"preparation_notes",
	"monitoring",
	"references",
)
STEP_FIELDS = ("step_id", "phase", "step_title", "description", "reference_minutes")
RESOURCE_FIELDS = (
	"resource_row_id",
	"step_id",
	"resource_type",
	"resource_text",
	"linked_doctype",
	"linked_name",
	"quantity",
	"uom",
	"headcount",
)
CITATION_FIELDS = (
	"target_section",
	"target_step_id",
	"relation",
	"legal_document",
	"legal_section",
	"quote",
	"deviation_reason",
)


def can_revise(state):
	return state == PUBLISHED


def _pick(row, fields):
	return {f: row.get(f) for f in fields}


def build_revision(src, max_version):
	"""Dict cho `frappe.get_doc` của bản nháp `max_version + 1`: giữ `step_id`, `resource_row_id` và hai bộ đếm;
	không sao chép trạng thái, số quyết định, ngày hiệu lực, `copied_from`, `ai_log`."""
	doc = {
		"doctype": "NC Clinical Procedure",
		"technical_service": src["technical_service"],
		"department": src["department"],
		"version_no": int(max_version) + 1,
		"previous_version": src["name"],
		"doctor_request": src.get("doctor_request"),
		"needs_review": src.get("needs_review") or 0,
		"next_step_seq": src.get("next_step_seq") or 0,
		"next_resource_seq": src.get("next_resource_seq") or 0,
		"steps": [{**_pick(s, STEP_FIELDS), "ai_suggested": 0} for s in src.get("steps") or []],
		"resources": [{**_pick(r, RESOURCE_FIELDS), "ai_suggested": 0} for r in src.get("resources") or []],
		"citations": [_pick(c, CITATION_FIELDS) for c in src.get("citations") or []],
	}
	for f in TEXT_FIELDS:
		doc[f] = src.get(f)
	return doc
