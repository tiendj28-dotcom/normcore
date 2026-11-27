"""AI đề xuất định mức cận lâm sàng từ tài liệu của hãng (FR-AI-016..018, UC-025; TD 3.1).

Module thuần, không phụ thuộc framework. Máy chủ dựng phạm vi và nguồn gửi (qua `ai.guard`); module này
lọc phạm vi, kiểm đầu ra của AI và lập kế hoạch chấp nhận. Không công thức tính giá nào ở đây (FR-AI-008).
"""

import math

from normcore.ai import citation

MANUFACTURER_DOC_TYPE = "Tài liệu của hãng"
VALID = "Còn hiệu lực"
INDEXED = "Đã lập"

TYPE_LABELS = {
	"REAGENT_PER_TEST": "Lượng hóa chất mỗi test",
	"CALIBRATION_FREQ": "Tần suất chuẩn máy",
	"IQC_FREQ": "Tần suất nội kiểm",
	"OPEN_STABILITY": "Hạn dùng sau mở",
}
TYPE_ORDER = tuple(TYPE_LABELS.values())
TYPE_CODE = {v: k for k, v in TYPE_LABELS.items()}

REL_FOLLOW = citation.REL_FOLLOW
REL_NONE = citation.REL_NONE
CATALOG_DOCTYPES = ("NC Item", "NC Equipment")
NO_BASIS_REF = "AI — Chưa có căn cứ"


def system_resources(main_equipment, norm_lines, iqc_lines, calibration_lines):
	"""Tập khóa (doctype, name) của hệ thống xét nghiệm (ASM-038-03)."""
	keys = set()
	if main_equipment:
		keys.add(("NC Equipment", main_equipment))
	for ln in norm_lines or []:
		if ln.get("resource") and ln.get("resource_doctype") in CATALOG_DOCTYPES:
			keys.add((ln["resource_doctype"], ln["resource"]))
	for ln in iqc_lines or []:
		if ln.get("qc_material"):
			keys.add(("NC Item", ln["qc_material"]))
	for ln in calibration_lines or []:
		if ln.get("calibrator"):
			keys.add(("NC Item", ln["calibrator"]))
	return keys


def docs_in_scope(docs, resource_keys):
	"""Tên các tài liệu của hãng đủ điều kiện gửi AI cho hệ thống (ADR-007 [1.1], ASM-038-04), theo thứ tự tên."""
	keys = set(resource_keys or ())
	out = []
	for d in docs or []:
		if d.get("doc_type") != MANUFACTURER_DOC_TYPE:
			continue
		if d.get("validity_status") != VALID or d.get("index_status") != INDEXED:
			continue
		linked = {(r.get("linked_doctype"), r.get("linked_name")) for r in d.get("related_resources") or []}
		if linked & keys:
			out.append(d["name"])
	return sorted(out)


def request_variables(service, procedure, items, equipment):
	"""`variables` của lời gọi AI. Đầu vào đã qua `guard.build_source` (FR-AI-011); chỉ bốn khóa này."""
	return {
		"service": service,
		"procedure": procedure,
		"items": list(items or []),
		"equipment": list(equipment or []),
	}


def _positive_number(v):
	if isinstance(v, bool) or not isinstance(v, int | float):
		return False
	return math.isfinite(v) and v > 0


def parse_suggestions(data, sources, catalog):
	"""Kiểm đầu ra AI (FR-AI-005, FR-AI-017, FR-AI-018, ASM-038-06). Trả `(rows, rejected)`.

	`catalog`: dict mã → doctype ("NC Item" | "NC Equipment") của mặt hàng, thiết bị có thật.
	`rejected` = số trích dẫn bị loại + số đề xuất sai cấu trúc.
	"""
	raw = (data or {}).get("suggestions") if isinstance(data, dict) else None
	if raw is None:
		return [], 0
	if not isinstance(raw, list):
		return [], 1
	catalog = catalog or {}
	rows, rejected = [], 0
	for item in raw:
		if (
			not isinstance(item, dict)
			or item.get("suggestion_type") not in TYPE_LABELS
			or not _positive_number(item.get("value"))
		):
			rejected += 1
			continue
		cites = item.get("citations")
		cites = [c for c in cites if isinstance(c, dict)] if isinstance(cites, list) else []
		res = citation.check_citations(cites, sources)
		rejected += len(res.rejected)
		row = {
			"suggestion_type": TYPE_LABELS[item["suggestion_type"]],
			"value": float(item["value"]),
			"uom": (item.get("uom") or "").strip() or None,
		}
		if res.kept:
			first = res.kept[0]
			row.update(relation=REL_FOLLOW, legal_section=first["section"], quote=first["quote"])
		else:
			row.update(relation=REL_NONE, legal_section=None, quote=None)
		code = item.get("item_code")
		text = (item.get("item_text") or "").strip()
		if code and code in catalog:
			row.update(
				resource_doctype=catalog[code],
				resource=code,
				not_in_catalog=0,
				resource_text=text or code,
			)
		else:
			row.update(
				resource_doctype=None,
				resource=None,
				not_in_catalog=1,
				resource_text=text or (code or "").strip() or "—",
			)
		rows.append(row)
	return rows, rejected


def basis_ref(doc_number, section_no):
	if doc_number and section_no:
		return f"{doc_number} mục {section_no}"
	return NO_BASIS_REF


def _matching(lines, field, resource):
	return [ln for ln in lines if ln.get(field) == resource]


def plan_accept(suggestion, norm_lines, iqc_lines, calibration_lines):
	"""Hành động thuần khi chấp nhận một đề xuất (TD 3.4, ASM-038-08).

	`norm_lines` là `None` khi hệ thống chưa có bộ định mức Nháp; `iqc_lines`, `calibration_lines` là `None`
	khi chưa có kế hoạch chất lượng. Trả dict có `target` hoặc `{"error": <chuỗi>}`.
	"""
	resource = suggestion.get("resource")
	if suggestion.get("not_in_catalog") or not resource:
		return {"error": "Liên kết mặt hàng hoặc thiết bị trong danh mục trước khi chấp nhận"}
	kind = suggestion.get("suggestion_type")
	doctype = suggestion.get("resource_doctype")
	value = suggestion.get("value")
	system = suggestion.get("test_system")
	if kind == TYPE_LABELS["REAGENT_PER_TEST"]:
		if doctype != "NC Item":
			return {"error": "Lượng mỗi test chỉ áp cho hóa chất"}
		if norm_lines is None:
			return {
				"error": f"Chưa có bộ định mức Nháp cho hệ thống {system}. Tạo phiên bản mới rồi chấp nhận lại"
			}
		found = [
			ln
			for ln in norm_lines
			if ln.get("resource_doctype") == "NC Item"
			and ln.get("resource") == resource
			and (ln.get("cost_level") or "RESULT") == "RESULT"
			and not ln.get("is_excluded")
		]
		if len(found) > 1:
			return {"error": f"Có {len(found)} dòng cùng hóa chất; sửa trực tiếp trên lưới"}
		return {"target": "norm_line", "line_id": found[0]["line_id"] if found else None, "value": value}
	if kind == TYPE_LABELS["CALIBRATION_FREQ"]:
		rows = _matching(calibration_lines or [], "calibrator", resource)
		if not rows:
			return {
				"error": f"Kế hoạch chất lượng chưa có dòng chuẩn máy cho {resource}; thêm dòng rồi chấp nhận lại"
			}
		return {"target": "calibration", "row": rows[0].get("name") or rows[0].get("idx"), "value": value}
	if kind == TYPE_LABELS["IQC_FREQ"]:
		rows = _matching(iqc_lines or [], "qc_material", resource)
		if not rows:
			return {
				"error": f"Kế hoạch chất lượng chưa có dòng nội kiểm cho {resource}; thêm dòng rồi chấp nhận lại"
			}
		return {"target": "iqc", "row": rows[0].get("name") or rows[0].get("idx"), "value": value}
	if kind == TYPE_LABELS["OPEN_STABILITY"]:
		if doctype != "NC Item":
			return {"error": "Hạn dùng sau mở chỉ áp cho mặt hàng"}
		return {"target": "item", "value": int(math.floor(value + 0.5))}
	return {"error": "Loại đề xuất không hợp lệ"}
