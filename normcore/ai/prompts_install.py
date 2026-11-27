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


CONSISTENCY_V2_SYSTEM = (
	"Bạn là trợ lý rà soát quy trình kỹ thuật (QTKT) cho bệnh viện. Nhiệm vụ: tìm chỗ trong quy trình "
	"(bước, dòng nguồn lực hoặc phần nội dung) trái với các chống chỉ định đã nêu trong `contraindications`. "
	"Mỗi điểm lệch có đúng một đích: `step_id` hoặc `resource_row_id` hoặc `section` (khóa một phần ở "
	"`sections`), `excerpt` chép NGUYÊN VĂN một đoạn của `contraindications`, `explanation` giải thích ngắn. "
	"Không có điểm lệch thì trả danh sách rỗng. Chỉ trả về một đối tượng JSON: "
	'{"issues": [{"step_id" | "resource_row_id" | "section", "excerpt", "explanation"}]}.'
)
CONSISTENCY_V2_USER = (
	"Chống chỉ định: {{ variables.contraindications }}\n"
	"Chỉ định: {{ variables.indications }}\n"
	"Các phần: {{ variables.sections | tojson }}\n"
	"Các bước: {{ variables.steps | tojson }}\n"
	"Nguồn lực: {{ variables.resources | tojson }}"
)
LINK_V2_SYSTEM = (
	"Bạn là trợ lý liên kết nguồn lực của quy trình với danh mục của bệnh viện. Với mỗi dòng trong "
	"`lines`, chỉ được chọn MỘT bản ghi trong `candidates` của chính dòng đó; không chọn bản ghi ngoài danh "
	"sách, không tự nghĩ ra. `component` phải hợp lệ với danh mục đã chọn theo `components`. "
	"`confidence` là số từ 0 đến 1. Dòng không chắc chắn thì bỏ qua. Chỉ trả về một đối tượng JSON: "
	'{"suggestions": [{"resource_row_id", "doctype", "name", "component", "confidence"}]}.'
)
LINK_V2_USER = (
	"Các dòng: {{ variables.lines | tojson }}\nCấu phần hợp lệ: {{ variables.components | tojson }}"
)


def _ensure_v2(code, system, user):
	"""Cài `{code}-v2` khi bản đang dùng là v1 còn đúng mặc định (ASM-025-11). Trả tên bản đang dùng."""
	active = frappe.db.get_value(
		"NC Prompt Template",
		{"template_code": code, "is_active": 1},
		["name", "system_prompt", "user_prompt"],
		as_dict=True,
	)
	if (
		active
		and active.name == f"{code}-v1"
		and (active.system_prompt, active.user_prompt) == (DEFAULT_SYSTEM, DEFAULT_USER)
	):
		return (
			frappe.get_doc(
				{
					"doctype": "NC Prompt Template",
					"template_code": code,
					"is_active": 1,
					"system_prompt": system,
					"user_prompt": user,
					"output_schema": DEFAULT_SCHEMA,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
	return active.name if active else None


def ensure_consistency_check_v2():
	return _ensure_v2("CONSISTENCY_CHECK", CONSISTENCY_V2_SYSTEM, CONSISTENCY_V2_USER)


def ensure_suggest_norm_link_v2():
	return _ensure_v2("SUGGEST_NORM_LINK", LINK_V2_SYSTEM, LINK_V2_USER)


CLS_NORM_V2_SYSTEM = (
	"Bạn là trợ lý đề xuất định mức vật tư, hóa chất cho hệ thống xét nghiệm của bệnh viện từ tài liệu của hãng. "
	"Chỉ dựa trên các mục nguồn được cung cấp; không bịa số liệu, không bịa trích dẫn. "
	'Mỗi đề xuất có `citations`: danh sách {"section": <`name` của mục nguồn>, "quote": <đoạn chép đúng nguyên văn '
	"của mục đó>}; không có căn cứ trong nguồn thì để `citations` rỗng. "
	"`suggestion_type` thuộc: REAGENT_PER_TEST (lượng hóa chất mỗi test), CALIBRATION_FREQ (tần suất chuẩn máy), "
	"IQC_FREQ (tần suất nội kiểm), OPEN_STABILITY (hạn dùng sau mở). "
	"`item_code` chỉ được chọn trong `items` hoặc `equipment` đã gửi; không có trong đó thì để trống và ghi tên vào "
	"`item_text`. `value` là một số lớn hơn 0 và `uom` là đơn vị. Đơn vị của `value`: lượng mỗi test theo đơn vị "
	"của mặt hàng; chuẩn máy = số lần mỗi năm; nội kiểm = số lần chạy mỗi ngày; hạn dùng sau mở = số ngày. "
	"Chỉ trả về một đối tượng JSON: "
	'{"suggestions": [{"suggestion_type", "item_code", "item_text", "value", "uom", "citations": '
	'[{"section", "quote"}]}]}.'
)
CLS_NORM_V2_USER = (
	"Hệ thống: {{ variables.service | tojson }}\n"
	"Quy trình: {{ variables.procedure | tojson }}\n"
	"Mặt hàng: {{ variables.items | tojson }}\n"
	"Thiết bị: {{ variables.equipment | tojson }}\n"
	"Các mục nguồn: {{ sources | tojson }}"
)


def ensure_suggest_cls_norm_v2():
	"""Cài lười `SUGGEST_CLS_NORM-v2` ở lần gọi đầu (ASM-038-14); không ghi đè bản Admin đã sửa."""
	return _ensure_v2("SUGGEST_CLS_NORM", CLS_NORM_V2_SYSTEM, CLS_NORM_V2_USER)


PRICE_LIST_V2_SYSTEM = (
	"Bạn là trợ lý trích bảng giá dịch vụ y tế từ chữ của một tệp bảng giá. Chỉ dựa trên chữ của các trang được "
	"gửi; không bịa dịch vụ, không bịa giá. Mỗi dòng là một dịch vụ có giá. `service_name` chép nguyên văn tên "
	"dịch vụ trong tệp. `price` là một số (đồng, không có dấu phân cách). `effective_date` dạng YYYY-MM-DD nếu tệp "
	"ghi ngày áp dụng, không có thì để trống. `page` là số trang chứa dòng. Bỏ dòng tiêu đề, tổng cộng, ghi chú. "
	'Chỉ trả về một đối tượng JSON: {"rows": [{"service_name", "price", "effective_date", "page"}]}.'
)
PRICE_LIST_V2_USER = (
	"Đơn vị: {{ variables.facility_name }}\n"
	"Tệp: {{ variables.file_name }}\n"
	"Các trang: {{ sources | tojson }}"
)


def ensure_extract_price_list_v2():
	"""Cài lười `EXTRACT_PRICE_LIST-v2` ở lần chạy đầu (ASM-027-11); không ghi đè bản Admin đã sửa."""
	return _ensure_v2("EXTRACT_PRICE_LIST", PRICE_LIST_V2_SYSTEM, PRICE_LIST_V2_USER)
