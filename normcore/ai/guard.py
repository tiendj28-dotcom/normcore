"""Danh sách cho phép nguồn gửi AI (FR-AI-011, NFR-SEC-005, ADR-007). Thuần: không phụ thuộc frappe.

Chỉ DocType trong ALLOWED_SOURCES, và chỉ các trường liệt kê, được đưa vào nội dung gửi AI.
Thêm nguồn = sửa mã có test, không phải cấu hình.
"""

from collections.abc import Iterable, Mapping


class GuardError(Exception):
	"""Nguồn hoặc trường không được phép gửi cho AI."""


def _fs(*names):
	return frozenset(names)


ALLOWED_SOURCES: dict[str, frozenset[str]] = {
	"NC Legal Section": _fs("name", "section_no", "heading", "plain_text"),
	"NC Technical Service": _fs("service_code", "service_name"),
	"NC Clinical Procedure": _fs(
		"name",
		"technical_service",
		"doctor_request",
		"overview",
		"indications",
		"contraindications",
		"cautions",
		"preparation_notes",
		"monitoring",
		"references",
	),
	"NC Item": _fs("item_code", "item_name", "uom"),
	"NC Equipment": _fs("equipment_code", "equipment_name"),
}

ALLOWED_CHILDREN: dict[str, dict[str, frozenset[str]]] = {
	"NC Clinical Procedure": {
		"steps": _fs("step_id", "phase", "step_title", "description", "reference_minutes"),
		"resources": _fs(
			"resource_row_id",
			"step_id",
			"resource_type",
			"resource_text",
			"quantity",
			"uom",
			"headcount",
		),
	},
}

FORBIDDEN_DOCTYPES: frozenset[str] = frozenset(
	{
		"NC Item Price",
		"NC Costing Parameter Set",
		"NC Job Title Rate",
		"NC Price Category",
		"NC Account Mapping",
		"NC Accounting Import",
		"NC Accounting Import Line",
		"NC Accounting Import Total",
		"NC Cost Center",
		"NC Cost Center Driver",
		"NC Allocation Rule",
		"NC Service Volume",
		"NC Test System Volume",
		"NC Equipment Usage",
		"NC Stock Issue Actual",
		"NC Costing Run",
		"NC Scenario Change",
		"NC Service Cost",
		"NC Service Cost Line",
		"NC Test System Cost",
		"NC Reconciliation Line",
		"NC Benchmark Price",
		"NC CPI Index",
		"NC Adjustment Suggestion",
		"NC Price Proposal",
		"NC Price Proposal Item",
		"NC Norm Set",
		"NC Norm Line",
		"NC Room",
		"NC Equipment Component",
		"NC Equipment Allocation",
		"NC AI Settings",
	}
)


def is_allowed(doctype: str) -> bool:
	return doctype in ALLOWED_SOURCES


def build_source(doctype: str, record: Mapping, fields: Iterable[str] | None = None) -> dict:
	"""Dựng nội dung gửi AI từ một bản ghi. Không bao giờ sao chép khóa lạ của `record`."""
	if doctype not in ALLOWED_SOURCES:
		raise GuardError(f"Không được gửi dữ liệu của {doctype} cho AI")
	allowed = ALLOWED_SOURCES[doctype]
	children = ALLOWED_CHILDREN.get(doctype, {})
	if fields is not None:
		fields = list(fields)
		bad = [f for f in fields if f not in allowed and f not in children]
		if bad:
			raise GuardError(f"Không được gửi trường {', '.join(bad)} của {doctype} cho AI")
		wanted = set(fields)
	else:
		wanted = None
	out: dict = {}
	for f in allowed:
		if (wanted is None or f in wanted) and f in record:
			out[f] = record[f]
	for table, child_allowed in children.items():
		if (wanted is None or table in wanted) and table in record:
			out[table] = [
				{k: v for k, v in row.items() if k in child_allowed} for row in (record[table] or [])
			]
	return out


MANUFACTURER_DOC_TYPE = "Tài liệu của hãng"


def manufacturer_sections(sections, doc_names_in_scope):
	"""Mục của tài liệu của hãng gửi AI (FR-AI-016, ADR-007 [1.1]): chỉ mục của tài liệu trong phạm vi.

	Mục của tài liệu khác, kể cả tài liệu của hãng không gắn với hệ thống, không bao giờ vào nguồn."""
	allowed = set(doc_names_in_scope or ())
	return [build_source("NC Legal Section", s) for s in sections or [] if s.get("legal_document") in allowed]


def budget_exceeded(used: int, budget: int) -> bool:
	"""FR-AI-013: chặn khi lũy kế VƯỢT hạn mức (Lead, ASM-023-04). Hạn mức 0 = không giới hạn."""
	return budget > 0 and used > budget


def price_list_pages(pages) -> list[dict]:
	"""Nguồn gửi AI cho FR-BM-003: chữ tách từ tệp bảng giá do người dùng nạp, `[{"page", "text"}]`.

	Căn cứ ghi chú FR-BM-003: bảng giá công khai không thuộc dữ liệu cấm của FR-AI-011. Chỉ nhận đối tượng
	kiểu `Page` (có `number`, `text`); dict hoặc mapping bất kỳ (bản ghi DocType) bị từ chối. Không đổi
	`ALLOWED_SOURCES`, `FORBIDDEN_DOCTYPES`."""
	out = []
	for i, p in enumerate(pages or [], start=1):
		if isinstance(p, Mapping) or not (hasattr(p, "number") and hasattr(p, "text")):
			raise GuardError("Chỉ gửi chữ của tệp bảng giá cho AI")
		if isinstance(p.text, str) and p.text.strip():
			out.append({"page": p.number or i, "text": p.text})
	return out
