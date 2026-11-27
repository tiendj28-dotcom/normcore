"""Đề xuất liên kết dòng định mức với danh mục (FR-AI-007, UC-009 bước 3).

Module thuần, không phụ thuộc framework. Máy chủ lọc ứng viên bằng quy tắc; AI chỉ chọn trong danh sách đó.
"""

import unicodedata

from normcore.ai import citation
from normcore.norm.init_from_procedure import COMPONENT_BY_RESOURCE_TYPE

COMPONENTS_BY_DOCTYPE = {"NC Item": ("DRUG", "SUPPLY", "UTILITY"), "NC Equipment": ("EQUIPMENT",)}
_POOLS = {
	"Thuốc": ("NC Item",),
	"Hóa chất": ("NC Item",),
	"Dịch truyền": ("NC Item",),
	"Vật tư": ("NC Item",),
	"Thiết bị": ("NC Equipment",),
	"Khác": ("NC Item", "NC Equipment"),
}


def pools_for(resource_type):
	return _POOLS.get(resource_type, ())


def _tokens(text):
	t = citation.normalize(text).casefold().replace("đ", "d")
	t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
	return set(t.split())


def shortlist(text, candidates, limit=10):
	want = _tokens(text)
	scored = []
	for c in candidates:
		have = _tokens(c.get("label"))
		union = want | have
		score = len(want & have) / len(union) if union else 0
		if score > 0:
			scored.append((score, c))
	scored.sort(key=lambda sc: (-sc[0], sc[1]["name"]))
	return [c for _, c in scored[:limit]]


def pending_lines(lines):
	return [
		ln
		for ln in lines
		if ln.get("procedure_resource_row")
		and not ln.get("resource")
		and not ln.get("ai_suggested")
		and not ln.get("is_excluded")
		and not ln.get("step_removed")
	]


def request_variables(pending, resources_by_row, shortlists):
	out = []
	for ln in pending:
		row = ln["procedure_resource_row"]
		cands = shortlists.get(row) or []
		r = resources_by_row.get(row)
		if not cands or not r:
			continue
		out.append(
			{
				"resource_row_id": row,
				"resource_type": r.get("resource_type"),
				"resource_text": r.get("resource_text"),
				"quantity": r.get("quantity"),
				"uom": r.get("uom"),
				"component": ln.get("component"),
				"candidates": [{k: c.get(k) for k in ("doctype", "name", "label", "uom")} for c in cands],
			}
		)
	return {"lines": out, "components": {k: list(v) for k, v in COMPONENTS_BY_DOCTYPE.items()}}


def _conf(v):
	if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1:
		return None
	return v


def parse_suggestions(data, offered):
	items = data.get("suggestions") if isinstance(data, dict) else None
	if not isinstance(items, list):
		return {}, 0
	out, rejected = {}, 0
	for it in items:
		ok = isinstance(it, dict)
		if ok:
			row = it.get("resource_row_id")
			cands = offered.get(row) if isinstance(row, str) else None
			conf = _conf(it.get("confidence"))
			ok = (
				cands is not None
				and any(
					c.get("doctype") == it.get("doctype") and c.get("name") == it.get("name") for c in cands
				)
				and it.get("component") in COMPONENTS_BY_DOCTYPE.get(it.get("doctype"), ())
				and conf is not None
				and row not in out
			)
		if not ok:
			rejected += 1
			continue
		out[row] = {
			"resource_doctype": it["doctype"],
			"resource": it["name"],
			"component": it["component"],
			"ai_confidence": round(conf * 100),
		}
	return out, rejected


def apply_suggestions(lines, accepted):
	todo = {id(ln) for ln in pending_lines(lines)}
	done = []
	for ln in lines:
		s = accepted.get(ln.get("procedure_resource_row"))
		if s and id(ln) in todo:
			ln.update({**s, "ai_suggested": 1})
			done.append(ln.get("line_id"))
	return done


def original_component(resource_type):
	return COMPONENT_BY_RESOURCE_TYPE.get(resource_type, "SUPPLY")
