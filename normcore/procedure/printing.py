"""Ngữ cảnh in quy trình (FR-PROC-010, FR-PROC-011). Thuần Python, dùng chung cho PDF và DOCX."""

from datetime import date, datetime

CLOSED = ("Đã ban hành", "Đã thay thế", "Đã thu hồi")
WATERMARK = "DỰ THẢO"

TEXT_SECTIONS = (
	("Đại cương", "overview"),
	("Chỉ định", "indications"),
	("Chống chỉ định", "contraindications"),
	("Thận trọng", "cautions"),
	("Chuẩn bị", "preparation_notes"),
	("Các bước tiến hành", None),
	("Theo dõi và xử trí tai biến", "monitoring"),
	("Tài liệu tham khảo", "references"),
)
PHASES = ("Chuẩn bị", "Thực hiện", "Theo dõi", "Kết thúc")
SIGNATURE_LABELS = (
	("drafter", "Người soạn"),
	("head", "Trưởng khoa"),
	("council", "Hội đồng chuyên môn"),
	("director", "Giám đốc"),
)


def format_date(value):
	"""dd/mm/yyyy (NFR-LOC-001); chấp nhận date, datetime hoặc chuỗi ISO."""
	if not value:
		return ""
	if isinstance(value, str):
		value = datetime.fromisoformat(value[:10])
	if isinstance(value, datetime):
		value = value.date()
	return value.strftime("%d/%m/%Y")


def print_context(doc, signatures, today=None):
	"""Dựng ngữ cảnh in từ dict quy trình. `signatures`: {drafter|head|council|director: {user, date}}."""
	state = doc.get("workflow_state") or "Nháp"
	is_draft = state not in CLOSED
	sigs = signatures or {}
	steps = doc.get("steps") or []
	resources = doc.get("resources") or []
	phases = []
	for ph in PHASES:
		rows = []
		for s in steps:
			if s.get("phase") != ph:
				continue
			rows.append(
				{
					"step_id": s.get("step_id"),
					"title": s.get("step_title") or "",
					"description": s.get("description") or "",
					"minutes": s.get("reference_minutes"),
					"resources": [r for r in resources if r.get("step_id") == s.get("step_id")],
				}
			)
		if rows:
			phases.append({"phase": ph, "steps": rows})
	return {
		"title": "QUY TRÌNH KỸ THUẬT",
		"service_name": doc.get("service_name") or doc.get("technical_service") or "",
		"service_code": doc.get("service_code") or "",
		"department": doc.get("department_name") or doc.get("department") or "",
		"number": doc.get("name") or "",
		"version": f"Phiên bản {doc.get('version_no')}",
		"decision_no": doc.get("decision_no") or "",
		"effective_date": format_date(doc.get("effective_date")),
		"state": state,
		"is_draft": is_draft,
		"watermark": WATERMARK if is_draft else "",
		"status_note": state if state in ("Đã thay thế", "Đã thu hồi") else "",
		"sections": [
			{"heading": h, "key": k, "text": (doc.get(k) or "") if k else "", "is_steps": k is None}
			for h, k in TEXT_SECTIONS
		],
		"phases": phases,
		"resources": resources,
		"signatures": [
			{
				"label": label,
				"user": (sigs.get(key) or {}).get("user") or "",
				"date": format_date((sigs.get(key) or {}).get("date")),
			}
			for key, label in SIGNATURE_LABELS
		],
		"printed_on": format_date(today or date.today()),
	}
