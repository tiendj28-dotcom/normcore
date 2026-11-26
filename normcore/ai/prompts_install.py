"""Mẫu lệnh mặc định (UC-017 bước 1, ASM-023-06). Chỉ tạo khi mã chưa có bản nào; không ghi đè bản Admin đã sửa."""

import json

import frappe

TEMPLATE_CODES = [
	"DRAFT_PROCEDURE",
	"CONSISTENCY_CHECK",
	"SUGGEST_NORM_LINK",
	"MAP_SECTION_SERVICE",
	"EXTRACT_PRICE_LIST",
	"MATCH_SERVICE_NAME",
	"SUGGEST_CLS_NORM",
]

DEFAULT_SYSTEM = (
	"Bạn là trợ lý soạn thảo cho bệnh viện. Chỉ trả về một đối tượng JSON hợp lệ theo lược đồ yêu cầu. "
	"Chỉ dựa trên các mục nguồn được cung cấp; không bịa trích dẫn."
)
DEFAULT_USER = "Dữ liệu: {{ variables | tojson }}\nCác mục nguồn: {{ sources | tojson }}"
DEFAULT_SCHEMA = json.dumps({"type": "object"})


def ensure_default_templates():
	for code in TEMPLATE_CODES:
		if frappe.db.exists("NC Prompt Template", {"template_code": code}):
			continue
		frappe.get_doc(
			{
				"doctype": "NC Prompt Template",
				"template_code": code,
				"version": 1,
				"is_active": 1,
				"system_prompt": DEFAULT_SYSTEM,
				"user_prompt": DEFAULT_USER,
				"output_schema": DEFAULT_SCHEMA,
			}
		).insert(ignore_permissions=True)


DRAFT_V2_SYSTEM = (
	"Bạn là trợ lý soạn quy trình kỹ thuật (QTKT) cho bệnh viện theo hướng dẫn của Bộ Y tế. "
	"Chỉ dùng các mục nguồn được cung cấp; không bịa. Mỗi phần và mỗi bước kèm trích dẫn nguyên văn: "
	"`section` là `name` của mục nguồn, `quote` chép đúng nguyên văn một đoạn của mục đó. "
	'Nơi nội dung khác hướng dẫn do yêu cầu của người soạn thì `relation` = "Khác biệt" và `request_excerpt` '
	'chép nguyên văn đoạn yêu cầu; còn lại `relation` = "Theo hướng dẫn". '
	"Không có nguồn thì để `citations` rỗng. Chỉ trả về một đối tượng JSON đúng cấu trúc: "
	'{"sections": {<section_keys>: {"text": "...", "citations": [...]}}, '
	'"steps": [{"phase", "step_title", "description", "reference_minutes", '
	'"resources": [{"resource_type", "resource_text", "quantity", "uom", "headcount"}], "citations": [...]}]}.'
)
DRAFT_V2_USER = (
	"Yêu cầu của người soạn: {{ variables.doctor_request }}\n"
	"Dịch vụ: {{ variables.service | tojson }}\n"
	"Quy trình hiện hành: {{ variables.current_procedure | tojson }}\n"
	"Giai đoạn hợp lệ: {{ variables.phases | tojson }}\n"
	"Loại nguồn lực hợp lệ: {{ variables.resource_types | tojson }}\n"
	"Khóa các phần: {{ variables.section_keys | tojson }}\n"
	"Các mục nguồn: {{ sources | tojson }}"
)


def ensure_draft_procedure_v2():
	"""Cài `DRAFT_PROCEDURE-v2` khi bản đang dùng còn là v1 mặc định (ASM-024-11, ASM-024-15).

	Gọi lười từ `start_ai_draft`, không từ patch: test cũ của FEAT-023 đòi bản dùng là v1 sau cài đặt.
	Trả tên bản đang dùng.
	"""
	active = frappe.db.get_value(
		"NC Prompt Template",
		{"template_code": "DRAFT_PROCEDURE", "is_active": 1},
		["name", "system_prompt", "user_prompt"],
		as_dict=True,
	)
	if (
		active
		and active.name == "DRAFT_PROCEDURE-v1"
		and (active.system_prompt, active.user_prompt)
		== (
			DEFAULT_SYSTEM,
			DEFAULT_USER,
		)
	):
		return (
			frappe.get_doc(
				{
					"doctype": "NC Prompt Template",
					"template_code": "DRAFT_PROCEDURE",
					"is_active": 1,
					"system_prompt": DRAFT_V2_SYSTEM,
					"user_prompt": DRAFT_V2_USER,
					"output_schema": DEFAULT_SCHEMA,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
	return active.name if active else None
