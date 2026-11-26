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
