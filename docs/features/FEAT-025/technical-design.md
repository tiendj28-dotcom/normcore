# FEAT-025 — Kiểm tra nhất quán và đề xuất liên kết định mức — Thiết kế kỹ thuật

Issue NORM-71. Bản phát hành R2. Phụ thuộc FEAT-024, FEAT-012 (đều có `DONE` trên `develop`); dùng lại gateway, mẫu lệnh, nhật ký AI của FEAT-023.

Nguồn: `srs.md` FR-AI-006, FR-AI-007 (cùng FR-AI-008, 009, 011, 015 đã có); `use-cases.md` UC-005 bước 6, 6a; UC-009 bước 2–4, 8a; `data-model.md` 3.3 (NC Procedure Resource, NC Procedure Step), 3.5 (NC Norm Line), mục 4 (dòng "Quy trình", "Bộ định mức"); `ux-foundations.md` SCR-DSK-009, SCR-DSK-014; As-Built FEAT-012, FEAT-023, FEAT-024.

`test-cases.md` chưa có TC nào gắn FR-AI-006, FR-AI-007 (ASM-025-01): test mang mã FR/UC, ví dụ `test_FR_AI_006_nguon_luc_thieu_o_chuan_bi`. Không thêm TC vào `test-cases.md` (chỉ đọc).

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-AI-006 | Đủ | (1) nguồn lực có ở bước nhưng thiếu ở chuẩn bị và ngược lại, (2) bước thiếu người thực hiện: kiểm bằng quy tắc, Python thuần, không gọi AI. (3) nội dung trái chống chỉ định: AI đề xuất qua gateway. AI lỗi/quá hạn/hết hạn mức: vẫn trả (1)(2), báo phần AI chưa thực hiện (UC-005 6a) |
| FR-AI-007 | Đủ | Khởi tạo bộ định mức từ quy trình đã ban hành → tác vụ nền đề xuất cho mỗi dòng chưa liên kết một bản ghi danh mục và cấu phần, kèm độ tin cậy, `ai_suggested = 1`. Chấp nhận/Bỏ/sửa trên lưới. Chặn xác nhận dòng và chuyển "Đã xác nhận chuyên môn" khi còn đề xuất (đã có ở FEAT-012 `confirm_blockers`, `confirm_line`; FEAT-025 thêm test) |

Ngoài phạm vi: lưu lịch sử kết quả kiểm tra nhất quán (ASM-025-05); đề xuất liên kết cho NC Room và NC Job Title (ASM-025-09); đề xuất khi tạo phiên bản mới bằng `new_version` (dùng nút "Đề xuất liên kết" thủ công, ASM-025-12); AI tự sửa quy trình.

## 2. DocType

### 2.1 NC Norm Line (đã có, FEAT-012) — thêm một trường (AMD-025-01)

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `ai_confidence` | Độ tin cậy của đề xuất | Percent | | `read_only = 1`, `precision = 0`. 0–100. Chỉ do tác vụ đề xuất ghi; về 0 khi đề xuất được chấp nhận, bỏ hoặc sửa liên kết. Không nằm trong `LINE_INPUTS` (không phải trường nhập) |

Không tạo DocType mới. NC Procedure Resource, NC Procedure Step, NC Clinical Procedure: không đổi trường (FR-AI-006 chỉ đọc). Chỉ thêm trường: `bench migrate` tự thêm cột, không cần patch dữ liệu (ASM-025-02). `docs/data-model.md` 3.5 do Dev áp ở T01 theo AMD-025-01.

### 2.2 Controller NC Norm Set — đường ghi của đề xuất

`validate_lines` hiện coi mọi đổi trong `LINE_INPUTS` là "sửa dòng" → buộc `resource` (AMD-012-01). Bỏ đề xuất phải trả dòng về trống, nên thêm:

- `AI_LINK_FIELDS = ("component", "resource_doctype", "resource", "ai_suggested")`.
- Khi `self.flags.norm_action == "ai_link"`: một dòng có cũ (`before`) chỉ khác ở `AI_LINK_FIELDS` thì `changed = False` (không buộc nguồn lực, không coi là sửa); dòng khác ngoài các trường đó vẫn theo luật cũ. Xác nhận giữ nguyên như nhánh `elif before is not None` (dòng đề xuất vốn chưa xác nhận được).
- Cờ `"ai_link"` không đổi `status` (`validate_status_change` đã chặn đổi trạng thái khi cờ khác `confirm_set`…; Dev kiểm `TRANSITIONS` không nhận "ai_link").
- `ai_confidence` ngoài `LINE_INPUTS` nên không làm "sửa dòng". Mọi đường ghi khác (form, `frappe.client`, `save_line`) không được đặt `ai_suggested` 0→1 hay sửa `ai_confidence`: với bộ đã lưu (`prev` khác None), controller khôi phục hai trường này từ `before` khi cờ khác `"ai_link"` (dòng thêm mới vào bộ đã có: `ai_suggested = 0`, `ai_confidence = 0`). Bộ mới (`insert` từ `create_from_procedure`, `new_version`, `copy_norm_set`) giữ giá trị mã máy chủ đặt, để `new_version` vẫn mang đề xuất chưa xử lý sang như hiện nay. Ngoại lệ: dòng trong `ns.flags.ai_link_cleared` được phép 1→0 (xem `save_line` ở 3.5).

### 2.3 Quyền (data-model mục 4, không đổi ma trận)

| Thao tác | Ai được | Kiểm |
| :-- | :-- | :-- |
| `check_consistency` | Người có quyền **ghi** quy trình (Clinician/Dept Head đúng khoa), quy trình ở "Nháp" | `_editable(procedure)` của `api/procedure.py` |
| Đề xuất, chấp nhận, bỏ đề xuất liên kết | Người có quyền **ghi** bộ định mức (Clinician/Dept Head đúng khoa), bộ ở "Nháp" | `_load(norm_set, "write")` + `_need_draft` |
| Xem độ tin cậy, nhãn "Đề xuất" | Ai đọc được bộ định mức | `get_norm_set` |

NC Auditor, NC Finance, NC Council, Clinician khoa khác: bị từ chối ở mọi API ghi của FEAT này (`frappe.PermissionError`). Bảng con theo quyền DocType cha.

## 3. Thành phần

### 3.1 `normcore/procedure/consistency.py` — thuần, không import `frappe`

Dữ liệu vào: `steps` (list dict `step_id`, `phase`, `step_title`, `idx`), `resources` (list dict trường `RESOURCE_FIELDS` của FEAT-006).

| Hàm | Kết quả |
| :-- | :-- |
| `resource_key(r) -> tuple` | Có liên kết: `("link", linked_doctype, linked_name)`. Không: `("text", resource_type, chuẩn hóa resource_text)` — chuẩn hóa = `ai.citation.normalize` rồi `casefold()` (ASM-025-03) |
| `preparation_gaps(steps, resources) -> list[dict]` | FR-AI-006 (1). Bước "Chuẩn bị" = `phase == "Chuẩn bị"`. Chỉ xét loại trong `PREP_CHECK_TYPES` = mọi loại trừ "Nhân lực" (ASM-025-04). Mỗi khóa nguồn lực dùng ở bước không phải Chuẩn bị mà không có ở bước Chuẩn bị nào → `{"kind": "missing_in_preparation", "resource_row_ids": [...], "step_ids": [...], "label": <resource_text đầu tiên>}`; mỗi khóa có ở Chuẩn bị mà không dùng ở bước nào khác → `{"kind": "unused_in_steps", ...}`. Quy trình không có bước Chuẩn bị nào → đúng một mục `{"kind": "no_preparation_step"}` và bỏ hai loại trên. Thứ tự theo `idx` bước rồi `resource_row_id` |
| `steps_without_performer(steps, resources) -> list[dict]` | FR-AI-006 (2). Mỗi bước (mọi giai đoạn, ASM-025-04) không có dòng nguồn lực "Nhân lực" → `{"kind": "no_performer", "step_ids": [step_id], "label": step_title}`. Theo `idx` |
| `rule_issues(steps, resources) -> list[dict]` | `preparation_gaps + steps_without_performer`, mỗi mục thêm `message` tiếng Việt (bảng 3.1a) |
| `contra_variables(doc: dict) -> dict` | Biến gửi AI: `contraindications`, `indications`, `sections` (overview, cautions, preparation_notes, monitoring), `steps`, `resources` — dict `doc` phải dựng bằng `guard.build_source("NC Clinical Procedure", …)` ở API |
| `parse_contra(data, step_ids, row_ids, contraindications) -> (issues, rejected)` | FR-AI-006 (3). `data = {"issues": [{"step_id"?, "resource_row_id"?, "section"?, "excerpt", "explanation"}]}`. Nhận một mục khi: đúng **một** đích trong `step_id` (có trong `step_ids`), `resource_row_id` (có trong `row_ids`), `section` (thuộc `SECTION_KEYS` của `ai_draft`, trừ `contraindications`); `excerpt` khớp nguyên văn trong `contraindications` theo `ai.citation.quote_in_text` (ASM-024-07); `explanation` chuỗi không rỗng, cắt 500 ký tự. Sai → bỏ, đếm `rejected`. Không có khóa `issues` hoặc không phải list → `([], 0)` (MockProvider trả `{"mock": true}`) |

3.1a Thông báo (máy chủ, tiếng Việt):

| kind | message |
| :-- | :-- |
| `missing_in_preparation` | "Nguồn lực "{label}" dùng ở bước {step_ids} nhưng chưa có ở phần chuẩn bị" |
| `unused_in_steps` | "Nguồn lực "{label}" có ở phần chuẩn bị ({step_ids}) nhưng không dùng ở bước nào" |
| `no_preparation_step` | "Quy trình chưa có bước nào ở giai đoạn Chuẩn bị" |
| `no_performer` | "Bước {step_id} "{label}" chưa có người thực hiện (nguồn lực Nhân lực)" |
| AI | "Có thể trái chống chỉ định: {explanation}" (kèm `excerpt`) |

### 3.2 `normcore/norm/ai_link.py` — thuần, không import `frappe`

| Hàm / hằng | Kết quả |
| :-- | :-- |
| `COMPONENTS_BY_DOCTYPE = {"NC Item": ("DRUG", "SUPPLY", "UTILITY"), "NC Equipment": ("EQUIPMENT",)}` | Cấu phần hợp lệ của từng danh mục (DI-05) |
| `pools_for(resource_type) -> tuple[str, ...]` | Danh mục để tìm: Thuốc, Hóa chất, Dịch truyền, Vật tư → `("NC Item",)`; Thiết bị → `("NC Equipment",)`; Khác → `("NC Item", "NC Equipment")`; Nhân lực, Phòng → `()` (ASM-025-09) |
| `shortlist(text, candidates, limit=10) -> list[dict]` | Ứng viên cho một dòng: điểm = Jaccard giữa tập từ của `text` và của `label` (chuẩn hóa: `ai.citation.normalize`, `casefold`, bỏ dấu tiếng Việt bằng NFD bỏ nhóm `Mn`, "đ"→"d"); bỏ điểm 0; sắp điểm giảm dần rồi `name`; tối đa `limit` (ASM-025-07). `candidates`: `{"doctype", "name", "label", "uom"?}` |
| `pending_lines(lines) -> list[dict]` | Dòng cần đề xuất: có `procedure_resource_row`, `resource` trống, `ai_suggested` = 0, không `is_excluded`, không `step_removed` |
| `request_variables(pending, resources_by_row, shortlists) -> dict` | `{"lines": [{"resource_row_id", "resource_type", "resource_text", "quantity", "uom", "component", "candidates": [{"doctype","name","label","uom"}]}], "components": COMPONENTS_BY_DOCTYPE}`. Dòng không có ứng viên: không gửi |
| `parse_suggestions(data, offered) -> (dict, rejected)` | `data = {"suggestions": [{"resource_row_id", "doctype", "name", "component", "confidence"}]}`; `offered = {resource_row_id: [candidate…]}`. Nhận khi: dòng có trong `offered`; (`doctype`, `name`) thuộc ứng viên đã gửi của dòng đó (không nhận bản ghi AI tự nghĩ ra); `component ∈ COMPONENTS_BY_DOCTYPE[doctype]`; `confidence` là số trong [0, 1]. Trùng dòng: giữ mục đầu. Trả `{row_id: {"resource_doctype", "resource", "component", "ai_confidence": round(confidence*100)}}` |
| `apply_suggestions(lines, accepted) -> list[str]` | Cập nhật tại chỗ các dòng vẫn còn trong `pending_lines` (dòng người dùng đã liên kết trong lúc chờ: bỏ qua, ASM-025-10): đặt `component`, `resource_doctype`, `resource`, `ai_confidence`, `ai_suggested = 1`. Trả `line_id` đã đặt |
| `original_component(resource_type) -> str` | Dùng `COMPONENT_BY_RESOURCE_TYPE` của `init_from_procedure` để trả dòng về như lúc khởi tạo khi "Bỏ" |

### 3.3 Mẫu lệnh — `ai/prompts_install.py` (mở rộng)

`CONSISTENCY_CHECK-v1`, `SUGGEST_NORM_LINK-v1` đã cài ở FEAT-023 với nội dung mặc định. Như ASM-024-11/15: `test_nc_prompt_template` đòi mọi mã chỉ có `-v1` đang dùng sau cài đặt, nên **không** patch, không `after_install`. Thêm:

- `_ensure_v2(code, system, user)`: nếu bản đang dùng của `code` là `{code}-v1` còn đúng `DEFAULT_SYSTEM`/`DEFAULT_USER` thì tạo `{code}-v2` (`is_active = 1`, `output_schema = DEFAULT_SCHEMA`), trả tên bản đang dùng. Không đụng `ensure_draft_procedure_v2` (không refactor tiện tay).
- `ensure_consistency_check_v2()`, `ensure_suggest_norm_link_v2()` gọi `_ensure_v2` với lệnh riêng; gọi lười từ API ở 3.4, 3.5. Admin đã sửa mẫu → giữ bản của Admin.
- Lệnh hệ thống mô tả đúng lược đồ ở 3.1 (`issues`) và 3.2 (`suggestions`), yêu cầu chỉ chọn trong `candidates`, `excerpt` chép nguyên văn từ `contraindications`, trả JSON. `output_schema` giữ `{"type": "object"}`; kiểm cấu trúc ở `parse_contra`, `parse_suggestions` (ASM-024-11).

### 3.4 API kiểm tra nhất quán — `normcore/api/procedure.py` (mở rộng)

`@frappe.whitelist() check_consistency(procedure) -> dict` — đồng bộ (ASM-025-06), không ghi gì vào quy trình.

1. `doc = _editable(procedure)` (quyền ghi + "Nháp"; Auditor, Finance, khoa khác → `PermissionError`; không ở Nháp → lỗi).
2. `rules = consistency.rule_issues(steps, resources)`.
3. Phần AI (`ai`):
   - `gateway.is_enabled()` sai → `{"status": "disabled"}`, không gọi gateway (FR-AI-015, ASM-025-08).
   - `contraindications` trống (sau bỏ thẻ HTML) → `{"status": "skipped", "message": "Quy trình chưa ghi chống chỉ định; không có gì để đối chiếu"}`, không gọi gateway.
   - Còn lại: `ensure_consistency_check_v2()`; `gateway.complete(purpose="Kiểm tra nhất quán quy trình", template_code="CONSISTENCY_CHECK", variables=consistency.contra_variables(guard.build_source("NC Clinical Procedure", doc_dict)), sources=[], ref_doctype="NC Clinical Procedure", ref_name=doc.name, postprocess=…)`; `postprocess` gọi `parse_contra` để số mục bị loại vào `rejected_citations` của NC AI Log.
     - `res.ok` → `{"status": "done", "issues": [...], "rejected": n, "log": res.log_name}`.
     - Không ok (Lỗi, Quá hạn, Bị chặn hạn mức) → `{"status": "failed", "message": "Phần kiểm tra bằng AI chưa thực hiện: " + res.error, "log": res.log_name}` (UC-005 6a). Không ném lỗi.
4. Trả `{"procedure": name, "checked_on": now, "rule_issues": rules, "ai": ai}`.

Văn bản Text Editor gửi AI dạng chữ thuần (`frappe.utils.strip_html`), như FEAT-024.

### 3.5 API đề xuất liên kết — `normcore/api/norm.py` (mở rộng)

| Hàm | Tham số | Kết quả | Lỗi |
| :-- | :-- | :-- | :-- |
| `create_norm_set` (đã có) | không đổi | Thêm `link_job` (mã tác vụ) khi `gateway.is_enabled()` và bộ mới có dòng `pending_lines`; không thì `link_job = None`. Đường cũ `{"name", "message"}` khi đã có bộ đang soạn: không khởi tác vụ | như cũ |
| `start_link_suggestion(norm_set)` | tên bộ | `{"job_id"}`; `{"job_id": None, "message": "Không có dòng nào cần đề xuất"}` khi không có dòng chờ | Không quyền ghi / không "Nháp" → lỗi; AI tắt → `gateway.ensure_enabled()` ném lỗi |
| `run_link_suggestion(link_job, norm_set, user)` | tác vụ nền | Không trả; ghi cache | Không ném ra ngoài |
| `get_link_suggestion_status(job_id)` | mã | `{"status": "queued|running|done|failed", "suggested": n, "rejected": n, "message"?}` | Chỉ người tạo đọc (như `get_ai_draft_status`) |
| `accept_link_suggestions(norm_set, line_ids=None, all=0)` | danh sách `line_id` hoặc tất cả | `get_norm_set(...)` mới | dòng không có → lỗi nêu mã; dòng không còn đề xuất: bỏ qua |
| `reject_link_suggestion(norm_set, line_id)` | một dòng | `get_norm_set(...)` mới | dòng không phải đề xuất → lỗi "Dòng {0} không còn là đề xuất" |

Chi tiết:

- `_start_job(ns)`: `job_id = frappe.generate_hash(16)`; cache `normcore:ai_link:<job_id>` TTL 1 giờ (`status="queued"`, `user`); `frappe.enqueue("normcore.api.norm.run_link_suggestion", queue="long", timeout=timeout_seconds + 60, now=frappe.flags.in_test, enqueue_after_commit=True, link_job=…, norm_set=…, user=…)` — cùng cách ASM-024-14.
- `run_link_suggestion`: `frappe.set_user(user)`; nạp bộ, dừng nếu không ở "Nháp"; `pending = ai_link.pending_lines(...)`; nạp quy trình (`ns.procedure`) lấy dòng nguồn lực theo `procedure_resource_row`; dựng ứng viên ở máy chủ: NC Item `is_active = 1` và `item_type` không thuộc ("Chất chuẩn", "Vật liệu nội kiểm") (FR-NORM-024), NC Equipment mọi bản ghi — mỗi bản ghi qua `guard.build_source` (chỉ `item_code/item_name/uom`, `equipment_code/equipment_name`); `shortlist` từng dòng; không dòng nào có ứng viên → `done`, `suggested = 0`, không gọi gateway. Gọi `ensure_suggest_norm_link_v2()`, rồi `gateway.complete(purpose="Đề xuất liên kết định mức", template_code="SUGGEST_NORM_LINK", variables=request_variables(...), sources=[], ref_doctype="NC Norm Set", ref_name=ns.name, postprocess=…)`. `res.ok` → `ns.reload()` (người dùng có thể đã sửa), `apply_suggestions`, `ns.flags.norm_action = "ai_link"`, `ns.save()`; cache `done` + số dòng. Không ok → cache `failed` + `res.error`; bộ không đổi. `publish_realtime("normcore_ai_link", {...}, user=user)`.
- `accept_link_suggestions`: mỗi dòng đã chọn có `ai_suggested = 1` → `ai_suggested = 0`, `ai_confidence = 0`, giữ `resource`; `flags.norm_action = "ai_link"`.
- `reject_link_suggestion`: dòng → `resource = None`, `component = original_component(resource_type của dòng nguồn)`, `resource_doctype = RESOURCE_DOCTYPE_BY_COMPONENT[component]`, `ai_suggested = 0`, `ai_confidence = 0`; `flags.norm_action = "ai_link"`. Dòng trở lại "Chưa liên kết".
- `save_line` (đã có): dòng có `ai_suggested = 1` mà `values` đổi `resource`, `resource_doctype` hoặc `component` → máy chủ đặt `ai_suggested = 0`, `ai_confidence = 0` (người dùng đã "sửa liên kết" = đã xử lý, UC-009 bước 4). Sửa trường khác (lượng, căn cứ…) giữ đề xuất (cùng tinh thần ASM-024-13). Đường này vẫn là "sửa dòng" bình thường (luật FEAT-012). Cờ đặt bằng `row.flags`/biến cục bộ để controller không khôi phục (2.2): Dev đặt `ns.flags.ai_link_cleared = {line_id…}` và controller cho phép 1→0 với các dòng đó.
- `get_norm_set` (đã có): mỗi dòng thêm `ai_confidence`; gốc thêm `ai_pending` (số dòng `ai_suggested`), `ai_enabled` (`gateway.is_enabled()`); `_actions` thêm `"suggest_links"` khi bộ "Nháp", có quyền ghi và AI bật; `"accept_link"` khi có quyền ghi và bộ "Nháp".
- Chặn (UC-009 8a, FR-AI-008): `confirm_line` đã từ chối dòng `ai_suggested`; `confirm_set` đã liệt kê "Còn đề xuất AI chưa xử lý" qua `validation.confirm_blockers`. Không đổi mã; thêm test.

### 3.6 Guard (FR-AI-011)

Không đổi `ai/guard.py`. Chỉ gửi: NC Clinical Procedure (trường, bảng con đã cho phép), NC Item (`item_code`, `item_name`, `uom`), NC Equipment (`equipment_code`, `equipment_name`). Không gửi NC Norm Set/Line (bị cấm), đơn giá, NC Room, NC Job Title. `variables` của SUGGEST_NORM_LINK lấy `component` của dòng (giá trị Select, không phải dữ liệu tính giá) và `quantity`, `uom` từ dòng nguồn lực của quy trình, không từ NC Norm Line.

### 3.7 Giao diện

Xem `ui-design.md`: SCR-DSK-009 nút "Kiểm tra nhất quán" + bảng kết quả; SCR-DSK-014 nhãn "Đề xuất" + độ tin cậy, "Chấp nhận", "Bỏ", "Chấp nhận tất cả", dải tiến độ đề xuất, nút "Đề xuất liên kết".

## 4. Tiêu chí nghiệm thu

Provider giả lập tiêm bằng `unittest.mock.patch("normcore.ai.gateway.get_provider", …)`; không gọi mạng (CLAUDE.md 3.6). Test thuần ở `normcore/tests/unit/`, test site ở `normcore/api/test_procedure_consistency.py`, `normcore/api/test_norm_ai_link.py`.

| # | Điều kiện kiểm được | Test | FR/UC |
| :-: | :-- | :-- | :-- |
| 1 | Quy trình có B01 (Chuẩn bị: "Găng tay", "Bơm tiêm 5ml"), B02 (Thực hiện: "Găng tay", "Lidocain 2%"): đúng 2 mục — `missing_in_preparation` "Lidocain 2%" (B02), `unused_in_steps` "Bơm tiêm 5ml" (B01); "Găng tay" không báo; khóa liên kết cùng (`NC Item`, X) ở hai bước dù `resource_text` khác → coi là một | `test_FR_AI_006_nguon_luc_thieu_o_chuan_bi` (unit) | FR-AI-006 (1) |
| 2 | Không có bước Chuẩn bị → đúng một mục `no_preparation_step` | `test_FR_AI_006_khong_co_buoc_chuan_bi` (unit) | FR-AI-006 (1) |
| 3 | B02 không có dòng "Nhân lực", B01 có → đúng một mục `no_performer` cho B02; nguồn lực Nhân lực không vào kiểm (1) | `test_FR_AI_006_buoc_thieu_nguoi_thuc_hien` (unit) | FR-AI-006 (2) |
| 4 | `parse_contra`: mục đúng nhận; `excerpt` không nguyên văn, đích lạ, hai đích, `explanation` rỗng → bỏ, `rejected` đúng số; `{"mock": true}` → `([], 0)` | `test_FR_AI_006_loc_de_xuat_chong_chi_dinh` (unit) | FR-AI-006 (3) |
| 5 | `check_consistency` với provider giả trả 1 mục hợp lệ + 1 sai: `rule_issues` như #1/#3, `ai.status = "done"`, 1 mục, `rejected = 1`; đúng một NC AI Log mới `ref_doctype = "NC Clinical Procedure"`, `rejected_citations = 1`; quy trình không đổi `modified` | `test_FR_AI_006_kiem_tra_nhat_quan_co_ai` | FR-AI-006, FR-AI-009 |
| 6 | Provider ném `ProviderTimeout` (và một lần `ProviderError`): vẫn trả `rule_issues` đủ; `ai.status = "failed"`, `message` bắt đầu "Phần kiểm tra bằng AI chưa thực hiện"; không ném lỗi | `test_UC005_6a_ai_khong_kha_dung_van_kiem_quy_tac` | UC-005 6a |
| 7 | AI tắt: `ai.status = "disabled"`, không NC AI Log mới; chống chỉ định trống: `ai.status = "skipped"`, không log | `test_FR_AI_006_ai_tat_hoac_khong_co_chong_chi_dinh` | FR-AI-015 |
| 8 | Quyền `check_consistency`: NC Auditor, NC Finance, Clinician khoa khác → `PermissionError`; quy trình "Đã ban hành" → lỗi | `test_FR_AI_006_quyen_kiem_tra_nhat_quan` | data-model mục 4 |
| 9 | Payload gửi AI (bắt ở provider giả) chỉ chứa khóa được guard cho phép; không có khóa đơn giá, NC Norm Line, NC Room | `test_FR_AI_011_payload_kiem_tra_va_de_xuat` | FR-AI-011 |
| 10 | `shortlist`: chuẩn hóa không dấu/hoa thường, bỏ điểm 0, tối đa 10, thứ tự ổn định; `pools_for` theo 3.2 | `test_FR_AI_007_loc_ung_vien` (unit) | FR-AI-007 |
| 11 | `parse_suggestions`: nhận mục đúng; bỏ bản ghi ngoài ứng viên, cấu phần trái danh mục (NC Equipment + SUPPLY), `confidence` 1.2 hay chuỗi, dòng lạ, dòng trùng; `ai_confidence` = round(×100); `apply_suggestions` bỏ qua dòng đã liên kết | `test_FR_AI_007_loc_de_xuat_lien_ket` (unit) | FR-AI-007 |
| 12 | `create_norm_set` từ quy trình đã ban hành có 3 dòng chưa liên kết (Thuốc, Vật tư, Thiết bị), AI bật, provider giả đề xuất đủ: trả `link_job`; sau tác vụ (`now=True`) 3 dòng có `resource` đúng bản ghi, `component` đúng, `ai_suggested = 1`, `ai_confidence` 0–100; `get_link_suggestion_status` = `done`, `suggested = 3`; một NC AI Log `ref_doctype = "NC Norm Set"`; dòng Nhân lực đã liên kết không đổi | `test_FR_AI_007_khoi_tao_de_xuat_lien_ket` | FR-AI-007, UC-009 bước 3 |
| 13 | Bộ có dòng đề xuất: `confirm_line` dòng đó → lỗi "còn đề xuất AI"; `confirm_set` → lỗi liệt kê `line_id: … Còn đề xuất AI chưa xử lý`; sau `accept_link_suggestions(all=1)` + xác nhận đủ dòng → `confirm_set` qua, trạng thái "Đã xác nhận chuyên môn" | `test_UC009_8a_de_xuat_chua_xu_ly_chan_xac_nhan` | FR-AI-007, FR-AI-008, UC-009 8a |
| 14 | `reject_link_suggestion`: dòng về `resource` trống, cấu phần như lúc khởi tạo, `ai_suggested = 0`, không lỗi "Nguồn lực" bắt buộc; `save_line` đổi `resource` của dòng đề xuất → `ai_suggested = 0`; `save_line` chỉ đổi `hospital_qty` → vẫn đề xuất; `frappe.client.set_value`/form đặt `ai_suggested = 1` hoặc sửa `ai_confidence` → bị khôi phục | `test_FR_AI_007_chap_nhan_bo_sua_de_xuat` | FR-AI-007, FR-AI-008 |
| 15 | AI tắt: `create_norm_set` trả `link_job = None`, không log; `start_link_suggestion` → lỗi AI tắt. Provider lỗi: status `failed`, bộ không đổi | `test_FR_AI_007_ai_tat_hoac_loi_khong_de_xuat` | FR-AI-015, FR-AI-010 |
| 16 | Quyền: NC Auditor, NC Finance, Clinician khoa khác gọi `start_link_suggestion`, `accept_link_suggestions`, `reject_link_suggestion` → `PermissionError`; trạng thái job của người khác → `PermissionError`; NC Auditor đọc `get_norm_set` thấy `ai_confidence` | `test_FR_AI_007_quyen_de_xuat_lien_ket` | data-model mục 4 |
| 17 | Mẫu lệnh: sau cài đặt chỉ `-v1` (test cũ giữ xanh); lần gọi đầu tạo `CONSISTENCY_CHECK-v2`, `SUGGEST_NORM_LINK-v2`; v1 Admin đã sửa → không tạo v2 | `test_mau_lenh_feat_025_v2` | ASM-025-11 |
| 18 | Giao diện: chuỗi `__()` có bản dịch; nút gọi đúng API; ẩn nút AI khi AI tắt, ẩn nút ghi khi không quyền | `normcore/tests/unit/test_feat_025_ui.py` | SCR-DSK-009, 014 |

Test cũ phải xanh, không sửa: `nc_prompt_template/test_nc_prompt_template.py`, `api/test_norm.py`, `api/test_norm_version.py`, `api/test_procedure_ai.py`, `api/test_procedure.py`, `nc_ai_log/test_nc_ai_log.py`. Độ phủ ≥ 90% cho `procedure/consistency.py`, `norm/ai_link.py`.

## 5. Giả định và rủi ro

Giả định ghi ở `docs/decisions/assumptions/FEAT-025.md` (ASM-025-01..12); sửa thiết kế ở `docs/decisions/amendments/AMD-025-01.md`.

Rủi ro:

- Gọi AI đồng bộ ở `check_consistency`: `timeout_seconds` cấu hình lớn hơn thời hạn yêu cầu web (gunicorn mặc định 120 giây) sẽ cắt kết nối trước gateway. Giảm: ghi ở As-Built; chuyển sang hàng đợi nếu đo thấy chậm (ASM-025-06 đảo ngược được).
- Danh mục lớn: ứng viên lọc bằng Jaccard có thể bỏ sót bản ghi khớp nghĩa nhưng khác chữ; người dùng vẫn chọn tay. Gửi tối đa 10 ứng viên × số dòng chờ: kiểm token trong hạn mức.
- Tác vụ nền ghi bộ trong lúc người dùng sửa lưới: `reload` trước khi áp, chỉ áp dòng vẫn chờ (ASM-025-10); vẫn có thể `TimestampMismatchError` ở phía người dùng — lưới nạp lại khi nhận realtime.
- Chất lượng mẫu lệnh chưa chấm trên dữ liệu thật (như FEAT-024).
