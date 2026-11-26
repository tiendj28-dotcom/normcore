"""Mẫu định mức (FR-NORM-021, 022; ASM-034-03, 04, 06, 18, 21). Hàm thuần."""

import copy

from normcore.norm.init_from_procedure import RESOURCE_DOCTYPE_BY_COMPONENT
from normcore.norm.validation import COMPONENTS, COST_LEVELS, MATERIAL

DEFAULT_ITEMS = (  # ASM-034-18: (tên, cấu phần, cấp mặc định, bắt buộc)
	("Vật tư lấy mẫu", "SUPPLY", "TUBE", 1),
	("Hóa chất chính", "DRUG", "RESULT", 1),
	("Hóa chất phụ trợ", "DRUG", "DAY", 0),
	("Vật tư tiêu hao theo test", "SUPPLY", "RESULT", 1),
	("Nhân lực", "LABOR", "RESULT", 1),
	("Thiết bị", "EQUIPMENT", "RESULT", 1),
	("Điện nước", "UTILITY", "DAY", 0),
	("Xử lý chất thải", "UTILITY", "PERIOD", 0),
)


def _default(code: str, group: str) -> dict:
	return {
		"template_code": code,
		"cls_group": group,
		"is_active": 0,
		"items": [
			{"item_name": n, "component": c, "default_cost_level": lv, "is_mandatory": m}
			for n, c, lv, m in DEFAULT_ITEMS
		],
	}


DEFAULT_TEMPLATES = (_default("MDM-HOA-SINH", "Hóa sinh"), _default("MDM-MIEN-DICH", "Miễn dịch"))


def template_errors(values: dict, other_active) -> list[str]:
	"""ASM-034-21, 03. values: template_code, cls_group, is_active, items; other_active: tên mẫu khác đang dùng cùng nhóm."""
	errors: list[str] = []
	if not (values.get("template_code") or "").strip():
		errors.append("Thiếu: Mã mẫu")
	if not values.get("cls_group"):
		errors.append("Thiếu: Nhóm chuyên ngành")
	items = values.get("items") or []
	seen: set[str] = set()
	for i, it in enumerate(items, 1):
		name = (it.get("item_name") or "").strip()
		if not name:
			errors.append(f"Khoản mục dòng {i} thiếu: Tên khoản mục")
		elif name.casefold() in seen:
			errors.append(f"Khoản mục {name} bị trùng trong mẫu")
		seen.add(name.casefold())
		if it.get("component") not in COMPONENTS:
			errors.append(f"Khoản mục {name or i}: cấu phần không hợp lệ")
		if (it.get("default_cost_level") or "RESULT") not in COST_LEVELS:
			errors.append(f"Khoản mục {name or i}: cấp phát sinh mặc định không hợp lệ")
	if values.get("is_active"):
		if not items:
			errors.append("Mẫu đang dùng phải có ít nhất một khoản mục")
		if other_active:
			errors.append(
				f"Nhóm {values.get('cls_group')} đã có mẫu đang dùng: {', '.join(sorted(other_active))}"
			)
	return errors


def pick_template(rows, cls_group) -> str | None:
	"""ASM-034-03: mẫu đang dùng của nhóm (đã bảo đảm tối đa một)."""
	for r in rows or ():
		if r.get("is_active") and r.get("cls_group") == cls_group:
			return r.get("name") or r.get("template_code")
	return None


def apply_template(lines, items, paraclinical: bool) -> list[dict]:
	"""ASM-034-04: gán khoản mục cho dòng đầu tiên chưa gán cùng cấu phần; khoản mục bắt buộc không khớp thêm
	dòng giữ chỗ (chung cho cả dịch vụ). Không đổi đầu vào."""
	out = [copy.deepcopy(dict(ln)) for ln in lines]
	assigned = {i for i, ln in enumerate(out) if ln.get("template_item")}
	placeholders = []
	for it in items or ():
		level = (it.get("default_cost_level") or "RESULT") if paraclinical else "RESULT"
		hit = next(
			(
				i
				for i, ln in enumerate(out)
				if i not in assigned and ln.get("component") == it.get("component")
			),
			None,
		)
		if hit is not None:
			assigned.add(hit)
			out[hit]["template_item"] = it["item_name"]
			if paraclinical:
				out[hit]["cost_level"] = level
		elif it.get("is_mandatory"):
			placeholders.append(
				{
					"service_level": 1,
					"step_id": None,
					"component": it["component"],
					"resource_doctype": RESOURCE_DOCTYPE_BY_COMPONENT.get(it["component"]),
					"resource": None,
					"hospital_qty": None,
					"uom": None,
					"basis": "Ước tính",
					"cost_level": level,
					"template_item": it["item_name"],
					"ai_suggested": 0,
				}
			)
	return out + placeholders


def default_apply_k(lines) -> list[dict]:
	"""ASM-034-06: dòng Theo kết quả của thuốc, vật tư được bật nhân k (bộ có hệ thống)."""
	out = [dict(ln) for ln in lines]
	for ln in out:
		if (ln.get("cost_level") or "RESULT") == "RESULT" and ln.get("component") in MATERIAL:
			ln["apply_k"] = 1
	return out
