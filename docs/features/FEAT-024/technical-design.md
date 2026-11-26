# FEAT-024 — Soạn dự thảo quy trình bằng AI — Thiết kế kỹ thuật

Issue NORM-63. Nguồn: `srs.md` FR-AI-001..005, FR-AI-008 (kèm FR-AI-009, 010, 011, 015, FR-PROC-001, 002, FR-SVC-007 mà luồng phải tôn trọng); `use-cases.md` UC-004 (luồng chính, 1a, 1b, 2a, 4a, 5a); `data-model.md` 3.3 (NC Clinical Procedure, NC Procedure Step, NC Procedure Resource, NC Procedure Citation), 3.4 (NC Prompt Template, NC AI Log), mục 4 (dòng "Quy trình"), mục 5.1 (điều kiện "không còn `ai_suggested`"), DI-01, DI-08; `architecture.md` ADR-005, ADR-007, ADR-009; `ux-foundations.md` SCR-DSK-006 (AMD-004), SCR-DSK-008, SCR-DSK-009; `design.md` mục 3 ("Nhãn quan hệ trích dẫn", "Dòng đề xuất của AI"); TC-AI-01, 02, 03, 04, 10.

Phụ thuộc (đều có `DONE` trên `origin/develop`): FEAT-006 (trình soạn, API `api/procedure.py`), FEAT-022 (`api.library.get_draft_sources`, As-Built mục 4), FEAT-023 (`ai/gateway.py`, `ai/guard.py`, mẫu lệnh `DRAFT_PROCEDURE-v1`, ASM-023-03, ASM-023-06, ASM-023-15). FEAT-007 đã cài điều kiện gửi duyệt "không còn `ai_suggested`" (`procedure/validation.py::submit_errors` nhánh 5).

Giả định: `docs/decisions/assumptions/FEAT-024.md` (ASM-024-01..14). **Không có AMD:** mọi trường cần dùng đã có trong `data-model.md` và đã có trong DocType trên develop (`doctor_request`, `ai_log`, `citations`, `steps.ai_suggested`, `resources.ai_suggested` do FEAT-006 tạo). Issue ghi "mở rộng (trường `doctor_request`, `ai_log`, bảng `citations`)": ba trường này **đã có**, FEAT-024 không thêm trường, không tạo lại DocType.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-AI-001 | API `prepare_ai_draft` cho SCR-DSK-008 bước 1 (nguồn sẽ dùng); `start_ai_draft` gửi cho gateway: yêu cầu của người soạn (`doctor_request`), mục hướng dẫn lấy **chỉ** qua `api.library.get_draft_sources(service, valid_only=True)` (FR-SVC-007), mục chọn thêm (chỉ mục "Còn hiệu lực", ASM-024-03), quy trình hiện hành nếu có (ASM-024-04). Mọi nguồn dựng bằng `guard.build_source` (FR-AI-011) |
| FR-AI-002 | Kết quả AI (lược đồ mục 3.3) → bản nháp phiên bản kế tiếp có 7 phần văn bản, bước, nguồn lực theo bước, trích dẫn; mỗi phần (8 phần, "Các bước tiến hành" tính theo từng bước) và mỗi bước có ≥ 1 trích dẫn hợp lệ hoặc một dòng "Chưa có căn cứ" do hệ thống thêm |
| FR-AI-003 | Trích dẫn AI đánh `relation = "Khác biệt"` → giữ nhãn "Khác biệt", `deviation_reason` lấy từ `doctor_request` (đoạn AI chỉ ra nếu khớp nguyên văn trong yêu cầu, không thì cả yêu cầu, ASM-024-06). Người soạn sửa lý do bằng `update_citation` có sẵn |
| FR-AI-004 | Dịch vụ không có mục nguồn nào → `prepare_ai_draft` trả `no_sources = true` (SCR-DSK-008 cảnh báo); `start_ai_draft` không có `confirm_no_source = 1` → từ chối (`NoSourceError`); có xác nhận → gọi AI với danh sách nguồn rỗng; mọi trích dẫn AI trả về đều bị loại (không có mục nguồn) → mọi phần, mọi bước mang "Chưa có căn cứ" |
| FR-AI-005 | `ai/citation.py` (thuần): so khớp `quote` với `plain_text` của **chính mục nguồn đã gửi** sau chuẩn hóa khoảng trắng và dấu câu (ASM-024-07). Không khớp, thiếu `quote`, hoặc mục không nằm trong nguồn đã gửi → loại; phần/bước còn 0 trích dẫn → thêm "Chưa có căn cứ". Số bị loại ghi vào `NC AI Log.rejected_citations` (qua móc `postprocess` của gateway, mục 3.4). DI-08 thêm ở controller cho trích dẫn trỏ tới một NC Legal Section có thật (ASM-024-08) |
| FR-AI-008 | Bước và dòng nguồn lực do AI tạo có `ai_suggested = 1`; trình soạn hiện nhãn "Đề xuất" (`purple`) với "Chấp nhận" / "Bỏ". API mới `accept_suggestions`. Gửi duyệt khi còn `ai_suggested` bị từ chối và nêu bước/dòng (đã có ở FEAT-007; FEAT-024 thêm TC-AI-10). Bộ định mức: `norm/init_from_procedure.py` đã đặt `ai_suggested = 0` cho dòng sinh từ quy trình đã ban hành (quy trình đã ban hành không thể còn đề xuất); tính giá không đọc quy trình (không cần thêm) |
| FR-AI-009 (dùng lại) | Một lời gọi = một NC AI Log (gateway). `ref_doctype = "NC Technical Service"`, `ref_name = service` vì bản nháp chưa tồn tại lúc gọi (ASM-024-09); bản nháp tạo xong có `ai_log` trỏ tới log |
| FR-AI-010 (dùng lại) | Lỗi / quá hạn / chặn hạn mức: **không** tạo bản nháp; trả trạng thái lỗi kèm thông điệp của gateway; SCR-DSK-008 giữ dữ liệu đã nhập, cho "Thử lại" hoặc "Soạn thủ công" (UC-004 4a) |
| FR-AI-015 (dùng lại) | Nút "Soạn quy trình" trên SCR-DSK-006 luôn hiện cho người có quyền tạo; AI tắt → nút tạo bản nháp trống bằng `create_procedure` có sẵn (UC-004 1a); `start_ai_draft` gọi `gateway.ensure_enabled()` (ASM-023-03) |
| FR-PROC-001, 002 (dùng lại) | Bản nháp AI tạo bằng cùng đường `_refuse_if_exists` của `create_procedure` (1b: đã có bản nháp/đang duyệt → từ chối, dẫn tới bản đang có; đã ban hành → từ chối, Q3). Kiểm hai lần: lúc bắt đầu và lúc ghi kết quả |

**Không làm:** AI soạn phiên bản sửa đổi từ quy trình đã ban hành (đường `create_revision`, ASM-024-05); kiểm tra nhất quán (FR-AI-006/007, CONSISTENCY_CHECK — FEAT khác); đổi `NC Procedure Citation.legal_section` từ Data sang Link (ASM-024-02); bộ 10 dịch vụ mẫu chấm chất lượng mẫu lệnh (rủi ro của kế hoạch, không phải tiêu chí FEAT này); đánh dấu đề xuất ở mức phần văn bản (data-model không có trường, ASM-024-10).

**Dùng lại, không làm lại:** `gateway.complete`, `ensure_enabled`, `is_enabled`, `get_settings`; `guard.build_source`; `api.library.get_draft_sources`, `search_sections`, `get_source_view`; `api.procedure._refuse_if_exists`, `_editable`, `_require`, `_save`, `_dump`, `ExistingProcedureError`, `update_citation`, `delete_step`, `delete_resource`; controller `assign_step_ids` / `assign_resource_ids` (cấp `S###`, `R###` qua bộ đếm, DI-01); `procedure/validation.py::submit_errors`; `api/procedure_workflow.apply_action`.

**Ràng buộc từ test cũ (không sửa, CLAUDE.md mục 3 luật 1):** `nc_ai_log/test_nc_ai_log.py`, `tests/unit/test_ai_providers.py`, `nc_ai_settings/test_nc_ai_settings.py` (gồm TC-AI-08 gọi `DRAFT_PROCEDURE` với `MockProvider` và lược đồ mặc định), `api/test_procedure.py` (TC-PROC-09 dùng `legal_section = "Điều 5"` dạng chữ tự do) phải xanh nguyên trạng. Hệ quả: (a) thêm tham số vào `gateway.complete` phải có mặc định giữ hành vi cũ; (b) mẫu lệnh v2 không được làm hỏng TC-AI-08: test đó gọi `MOCK_RESPONSE` (`{"mock": true, ...}`) qua mẫu đang dùng; lược đồ v2 (mục 3.3) bắt buộc `sections`, `steps` sẽ làm lời gọi đó thành "Lỗi". Vì vậy lược đồ ghi trong `output_schema` của v2 giữ `{"type": "object"}` và **toàn bộ** kiểm cấu trúc dự thảo nằm ở `procedure/ai_draft.py::parse_draft` (ASM-024-11). Dev chạy lại `test_nc_ai_settings` sau T02 để chứng minh; (c) DI-08 ở controller chỉ áp khi `legal_section` là tên một NC Legal Section có thật, nên "Điều 5" của TC-PROC-09 không bị kiểm.

## 2. DocType

Không DocType mới, không trường mới, không đổi kiểu trường → không patch cấu trúc. Chỉ một patch dữ liệu (mẫu lệnh, mục 3.5).

### 2.1 NC Clinical Procedure (đã có, FEAT-006) — cách FEAT-024 ghi

| Trường | Giá trị khi AI soạn |
| :-- | :-- |
| technical_service, department | Từ tham số `start_ai_draft` |
| version_no, previous_version | Như `create_procedure` (`_refuse_if_exists` → `version + 1`, `latest`) |
| doctor_request | Nguyên văn yêu cầu người soạn nhập (cũng gửi AI) |
| overview, indications, contraindications, cautions, preparation_notes, monitoring, references | `sections.<key>.text` của kết quả AI (chuỗi thuần, escape HTML rồi bọc `<p>`; ASM-024-12) |
| steps | Mỗi bước AI: `phase` (một trong 4 giá trị, sai → "Thực hiện" và ghi cảnh báo), `step_title`, `description`, `reference_minutes` (số ≥ 0 hoặc trống), `ai_suggested = 1`; `step_id` để trống cho controller cấp `S001…` |
| resources | Mỗi nguồn lực của bước: `step_id` = mã vừa cấp cho bước cha, `resource_type` (một trong 8, sai → "Khác"), `resource_text`, `quantity` (> 0, sai → bỏ dòng và ghi cảnh báo), `uom` (Nhân lực luôn "phút" theo `validate_resources`), `headcount`, `ai_suggested = 1`; không gắn `linked_doctype/linked_name` (người soạn chọn sau bằng `suggest_catalog`) |
| citations | Mục 3.2 |
| ai_log | Tên NC AI Log của lời gọi |
| workflow_state | "Nháp" (mặc định controller) |

Cách ghi: tạo `doc` mới với 7 phần + `steps` (chưa có `resources`), `insert()` để controller cấp `step_id`; sau đó nối `resources` và `citations` theo chỉ số bước → `step_id`, `save()`. Cả hai trong cùng giao dịch của tác vụ nền; lỗi ở bất kỳ bước nào → `frappe.db.rollback()`, không để bản nháp dở (FR-AI-010).

### 2.2 NC Procedure Citation (đã có) — dòng do AI tạo

| Trường | Giá trị |
| :-- | :-- |
| target_section | Nhãn phần (một trong các nhãn Select đã có: "Đại cương" … "Tài liệu tham khảo"), hoặc trống nếu là bước |
| target_step_id | `step_id` của bước, hoặc trống nếu là phần |
| relation | "Theo hướng dẫn" / "Khác biệt" (từ AI, giá trị khác → "Theo hướng dẫn"); "Chưa có căn cứ" do hệ thống thêm |
| legal_section | **Tên** NC Legal Section (`LS-…`) của mục nguồn (ASM-024-02) |
| legal_document | `doc_number` của văn bản chứa mục (để hiện cho người đọc) |
| quote | Đoạn trích AI trả về, nguyên văn (không lưu bản chuẩn hóa) |
| deviation_reason | Khi "Khác biệt": theo ASM-024-06 |

Dòng "Chưa có căn cứ" do hệ thống thêm: chỉ `target_*` và `relation`, các trường khác trống.

### 2.3 DI-08 ở controller (mở rộng `validate_citations`)

Với mỗi dòng có `quote` và `legal_section` là tên một NC Legal Section tồn tại: `citation.quote_in_text(quote, plain_text)` phải đúng, không thì `frappe.throw("Trích dẫn dòng {0}: đoạn trích không có nguyên văn trong mục {1}")`. Dòng có `legal_section` dạng chữ tự do (trích dẫn tay kiểu FEAT-006) không kiểm (ASM-024-08). Một truy vấn `frappe.get_all("NC Legal Section", filters={"name": ["in", names]}, fields=["name","plain_text"])` cho cả bảng.

### 2.4 Quyền

Không đổi ma trận. Mọi API mới:
- đọc (`prepare_ai_draft`, `get_ai_draft_status`): `has_permission("NC Clinical Procedure", "create")` (vai trò được tạo quy trình: NC Clinician, NC Department Head, theo khoa — phạm vi khoa đã áp ở FEAT-001 qua User Permission) và quyền đọc NC Technical Service;
- ghi (`start_ai_draft`): như `create_procedure` (`_require("create")`) + `department` phải thuộc phạm vi khoa của người gọi (`frappe.has_permission("NC Department", "read", department)` — cùng cơ chế User Permission);
- `accept_suggestions`, `reject_suggestion`: `_editable(procedure)` (quyền write + trạng thái "Nháp").
- NC Auditor, NC Finance, người không vai trò NC: mọi hàm trên → `frappe.PermissionError`. Gateway và NC AI Log giữ nguyên quyền (log ghi `ignore_permissions` ở máy chủ).

## 3. Thành phần

### 3.1 `normcore/ai/citation.py` — thuần, không import `frappe`

| Hàm | Hợp đồng |
| :-- | :-- |
| `normalize(text: str) -> str` | `unicodedata.normalize("NFC")`; thay mọi ký tự thuộc nhóm Unicode `P*` (dấu câu) bằng khoảng trắng; gộp mọi chuỗi khoảng trắng (kể cả `\n`, `\t`, `\xa0`) thành một dấu cách; `strip()`. **Giữ** chữ hoa/thường và dấu tiếng Việt (ASM-024-07) |
| `quote_in_text(quote, text) -> bool` | `normalize(quote)` khác rỗng và là chuỗi con của `normalize(text)` (so khớp theo ranh giới từ: bao bằng dấu cách cả hai bên để "a b" không khớp "xa by") |
| `check_citations(items, sources) -> CheckResult` | `items`: danh sách `{"target": <khóa>, "section": str, "quote": str, "relation": str, "request_excerpt": str?}`; `sources`: danh sách dict có `name`, `plain_text` (đúng các mục đã gửi). Trả `CheckResult(kept: list, rejected: list[(item, reason)])`. Lý do loại: `"missing_quote"`, `"unknown_section"` (mục không thuộc nguồn đã gửi), `"not_verbatim"` |
| `label_unsupported(targets, kept) -> list` | Với mỗi khóa đích (phần hoặc chỉ số bước) không còn trích dẫn nào trong `kept` → một dòng `{"target": k, "relation": "Chưa có căn cứ"}` |

Hằng số: `REL_FOLLOW = "Theo hướng dẫn"`, `REL_DEVIATION = "Khác biệt"`, `REL_NONE = "Chưa có căn cứ"`.

### 3.2 `normcore/procedure/ai_draft.py` — thuần, không import `frappe`

| Hàm | Hợp đồng |
| :-- | :-- |
| `SECTION_KEYS` | Bộ 7 khóa phần văn bản → nhãn `target_section` (trùng `api.procedure.SECTIONS`, trừ "steps"). Khóa đích của phần "Các bước tiến hành" không dùng: bước nào cũng có trích dẫn riêng |
| `parse_draft(data) -> Draft` | Kiểm và chuẩn hóa kết quả AI theo lược đồ mục 3.3. Thiếu `sections`/`steps`, `steps` rỗng, bước thiếu `step_title` hoặc `description` → `DraftError` (tiếng Việt, liệt kê lỗi). Giá trị lệch được sửa theo bảng 2.1 và ghi vào `Draft.warnings` |
| `resolve_deviation_reason(excerpt, doctor_request) -> str` | ASM-024-06: `excerpt` khớp `citation.quote_in_text(excerpt, doctor_request)` → `excerpt.strip()`; không → `doctor_request.strip()` (cắt 1000 ký tự) |
| `build_rows(draft, sources, doctor_request) -> BuildResult` | Gộp mọi trích dẫn của phần và bước → `citation.check_citations` → `label_unsupported` cho 7 phần + mọi bước; dựng `sections` (dict 7 trường), `steps` (list dict có `ai_suggested = 1`), `resources` theo chỉ số bước, `citations` theo khóa đích (`("section", key)` hoặc `("step", i)`); trả thêm `rejected` (số và lý do), `warnings` |
| `request_variables(doctor_request, service, current) -> dict` | Biến gửi mẫu lệnh: `doctor_request`, `service` (`service_code`, `service_name`), `current_procedure` (hoặc `None`), `phases`, `resource_types`, `section_keys` để mô hình trả đúng giá trị |

Không công thức tiền, không golden liên quan.

### 3.3 Lược đồ kết quả AI (hợp đồng mẫu lệnh `DRAFT_PROCEDURE-v2`)

```json
{
  "sections": {
    "overview":          {"text": "…", "citations": [CIT, …]},
    "indications":       {"text": "…", "citations": []},
    "contraindications": {…}, "cautions": {…}, "preparation_notes": {…},
    "monitoring": {…}, "references": {…}
  },
  "steps": [
    {"phase": "Chuẩn bị|Thực hiện|Theo dõi|Kết thúc", "step_title": "…", "description": "…",
     "reference_minutes": 5,
     "resources": [{"resource_type": "Nhân lực|Thuốc|…|Khác", "resource_text": "…", "quantity": 1, "uom": "…", "headcount": 1}],
     "citations": [CIT, …]}
  ]
}
CIT = {"section": "<name của NC Legal Section trong nguồn>", "quote": "<nguyên văn>",
       "relation": "Theo hướng dẫn|Khác biệt", "request_excerpt": "<đoạn trong yêu cầu, khi Khác biệt>"}
```

Thiếu khóa phần → phần đó trống + "Chưa có căn cứ". `output_schema` của v2 = `{"type": "object"}` (ASM-024-11); kiểm chi tiết ở `parse_draft`.

### 3.4 Gateway — mở rộng nhỏ `ai/gateway.py::complete`

Thêm tham số `postprocess=None` (callable `data -> (data, rejected_count)`), gọi sau kiểm lược đồ, trước `_write_log`. Ngoại lệ trong `postprocess` (gồm `DraftError`) → `res.ok = False`, `status = "Lỗi"`, `error` = thông điệp. `_write_log` nhận thêm `rejected_citations` (mặc định 0) ghi vào NC AI Log. Lý do: NC AI Log bất biến sau khi tạo (`guard_immutable`), nên số trích dẫn bị loại phải có **trước** khi ghi log. Mặc định `None` giữ nguyên hành vi cũ (test FEAT-023 không đổi).

### 3.5 Mẫu lệnh — `ai/prompts_install.py`

Hàm mới `ensure_draft_procedure_v2()`: chỉ khi bản `DRAFT_PROCEDURE` đang dùng là `DRAFT_PROCEDURE-v1` **và** nội dung v1 còn đúng mặc định (`DEFAULT_SYSTEM`, `DEFAULT_USER`) → tạo `DRAFT_PROCEDURE-v2` (`is_active = 1`, v1 tự thôi dùng theo controller FEAT-023). Admin đã sửa (đang dùng v ≥ 2 hoặc v1 khác mặc định) → không đụng. Gọi từ `after_install` (sau `ensure_default_templates`) và patch `normcore.patches.add_draft_procedure_prompt_v2` (thêm dòng cuối `patches.txt`). Nội dung v2:
- `system_prompt`: vai trò soạn QTKT theo hướng dẫn của Bộ Y tế; chỉ dùng mục nguồn được cung cấp; mỗi phần và bước kèm trích dẫn nguyên văn (`section` = `name` của mục); nơi nội dung khác hướng dẫn do yêu cầu của người soạn thì `relation = "Khác biệt"` và `request_excerpt` chép nguyên văn đoạn yêu cầu; không có nguồn thì để `citations` rỗng; chỉ trả JSON đúng lược đồ 3.3.
- `user_prompt` (Jinja, biến của `request_variables`): yêu cầu người soạn, dịch vụ, quy trình hiện hành nếu có, danh sách giá trị hợp lệ, `{{ sources | tojson }}`.
- `output_schema`: `{"type": "object"}`.

### 3.6 API — `normcore/api/procedure.py` (mở rộng)

Mọi hàm `@frappe.whitelist()`, kiểm quyền như 2.4, thông báo tiếng Việt.

| Hàm | Tham số | Kết quả | Lỗi |
| :-- | :-- | :-- | :-- |
| `prepare_ai_draft` | `technical_service`, `department` | `{ai_enabled, existing (tên bản nháp/đang duyệt/đã ban hành hoặc null), existing_state, sources: [{name, legal_document, doc_number, section_no, heading}], no_sources: bool, current_procedure: {name, version_no} \| null}` — không trả `plain_text` (xem bằng `get_source_view` có sẵn) | `PermissionError` |
| `search_extra_sources` | `query`, `technical_service`, `start=0`, `page_length=20` | Gọi `api.library.search_sections(query, validity_status="Còn hiệu lực")`, bỏ mục đã có trong nguồn ánh xạ; trả `[{name, doc_number, section_no, heading}]` | `PermissionError` |
| `start_ai_draft` | `technical_service`, `department`, `doctor_request` (BB, ≤ 5000 ký tự), `extra_sections` (JSON list tên mục, ≤ 20), `confirm_no_source=0` | `{job_id}`. Thứ tự: quyền → `gateway.ensure_enabled()` → `doctor_request` không rỗng → `_refuse_if_exists` (1b) → dựng nguồn (`get_draft_sources` + mục thêm hợp lệ, không trùng) → rỗng và chưa xác nhận → `NoSourceError` → `frappe.enqueue("normcore.api.procedure.run_ai_draft", queue="long", timeout=timeout_seconds + 60, job_id=…, now=frappe.flags.in_test, …)`; trạng thái job ghi cache (`normcore:ai_draft:<job_id>`, TTL 3600 s): `{"status": "queued", "user": session.user}` | `PermissionError`; "Tính năng AI đang tắt"; "Nhập yêu cầu soạn thảo"; `ExistingProcedureError` (kèm `existing_procedure`); `NoSourceError` ("Dịch vụ chưa có mục hướng dẫn nào đã xác nhận và còn hiệu lực…"); mục thêm không tồn tại / hết hiệu lực → `ValidationError` nêu mục |
| `run_ai_draft` (không whitelisted, tác vụ nền) | `job_id`, `technical_service`, `department`, `doctor_request`, `source_names`, `user` | Đặt `frappe.set_user(user)`; cache `running` + `publish_realtime("normcore_ai_draft", {job_id, status}, user=user)`; dựng lại nguồn bằng `guard.build_source` từ `source_names` (chỉ mục vẫn còn đủ điều kiện lúc chạy); `gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", variables, sources, ref_doctype="NC Technical Service", ref_name=service, postprocess=…)` với `postprocess` chạy `parse_draft` + `build_rows` và trả số bị loại; thành công → `_refuse_if_exists` lần 2 → ghi bản nháp (2.1) → cache `done` `{procedure, log, rejected, warnings}`; thất bại → rollback, cache `failed` `{error, log, status}`; luôn `publish_realtime` | Không ném ra ngoài job; mọi lỗi vào cache |
| `get_ai_draft_status` | `job_id` | Nội dung cache; chỉ người tạo job (hoặc Administrator) đọc được, không có/hết hạn → `{"status": "unknown"}` | `PermissionError` khi khác người |
| `reject_suggestion` | `procedure`, `step_id` | `{"deleted": step_id, "resources": n, "citations": m}` | `PermissionError`, "Quy trình không ở trạng thái Nháp", bước không phải đề xuất → `ValidationError` |
| `accept_suggestions` | `procedure`, `step_ids=None`, `resource_row_ids=None`, `all=0` | Đặt `ai_suggested = 0` cho các bước/dòng nêu (hoặc mọi dòng khi `all=1`); chấp nhận một bước **không** tự chấp nhận nguồn lực của nó (ASM-024-13); trả `{"accepted_steps": [...], "accepted_resources": [...], "remaining": n}` | `PermissionError`, "Quy trình không ở trạng thái Nháp", mã không tồn tại → `ValidationError` |

`create_procedure` (đã có) thêm tham số tùy chọn `doctor_request=None` (ghi vào bản nháp; nút "Soạn thủ công" sau lỗi AI dùng để không mất yêu cầu, FR-AI-010); không truyền → hành vi cũ.

`get_procedure` (đã có) thêm `relations` (dict `"step:<step_id>"` / `"section:<nhãn phần>"` → danh sách quan hệ khác nhau của đích đó, tính trên toàn bộ bảng trích dẫn, để trình soạn vẽ nhãn "Khác biệt"/"Chưa có căn cứ" trên thẻ), thêm `ai_suggested` vào `STEP_FIELDS`/`RESOURCE_FIELDS` khi dump cho trình soạn, thêm `ai_log`, `doctor_request`, và với trích dẫn có `legal_section` là tên NC Legal Section: `section_label` = `"<doc_number> — <section_no> <heading>"`. Thêm trường vào kết quả, không đổi trường cũ (test FEAT-006 so khớp theo khóa: Dev kiểm lại `test_procedure.py` xanh; nếu test cũ so khớp đủ dict thì không thêm vào `STEP_FIELDS` mà thêm khóa riêng `ai_suggested` trong `get_procedure`).

"Bỏ" một dòng nguồn lực đề xuất = `delete_resource` có sẵn. "Bỏ" một bước đề xuất: `delete_step` có sẵn từ chối khi bước còn nguồn lực hoặc trích dẫn (ASM-018), nên thêm `reject_suggestion(procedure, step_id)`: chỉ nhận bước có `ai_suggested = 1`; xóa bước cùng mọi nguồn lực và trích dẫn gắn bước trong một lần lưu; mã bước không tái dùng (bộ đếm giữ nguyên, DI-01); bước đã chấp nhận → `ValidationError` "Bước {0} không còn là đề xuất; dùng Xóa bước". `delete_step` không đổi.

Ngoại lệ mới: `class NoSourceError(frappe.ValidationError)` trong `api/procedure.py`.

### 3.7 Giao diện

Chi tiết ở `ui-design.md`: SCR-DSK-006 nút "Soạn quy trình" (`nc_technical_service.js`), SCR-DSK-008 hộp thoại 3 bước (`normcore/public/js/ai_draft_dialog.js`, nạp qua `doctype_js` của NC Technical Service), SCR-DSK-009 mở rộng `ProcedureEditor.vue` (nhãn "Đề xuất", "Chấp nhận", "Bỏ", "Chấp nhận tất cả", dải "Còn n đề xuất AI chưa xử lý", nhãn quan hệ trên thẻ bước/phần).

## 4. Tiêu chí nghiệm thu

Test tích hợp trong `normcore/api/test_procedure_ai.py` (lớp `FrappeTestCase`), test đơn vị trong `normcore/tests/unit/test_ai_citation.py`, `normcore/tests/unit/test_procedure_ai_draft.py`. Mọi test dùng provider giả lập tiêm qua `unittest.mock.patch("normcore.ai.gateway.get_provider", return_value=FakeProvider(json))` ghi lại `sources` nhận được; không gọi mạng (CLAUDE.md mục 3 luật 6). Dữ liệu: dịch vụ X, khoa K, văn bản hướng dẫn QTKT có mục M1, M2 ánh xạ "Đã xác nhận" với X và "Còn hiệu lực", mục M3 ánh xạ "Đề xuất", mục M4 "Đã xác nhận" nhưng "Hết hiệu lực"; AI bật.

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Provider giả lập trả dự thảo 7 phần + 5 bước (mỗi bước ≥ 1 nguồn lực, mỗi phần và bước có trích dẫn đúng nguyên văn M1/M2). `start_ai_draft` → job `done`; bản nháp v1, "Nháp", 5 bước `S001..S005` `ai_suggested = 1`, đủ nguồn lực gắn đúng `step_id`, 7 phần có văn bản; mỗi phần và mỗi bước có ≥ 1 trích dẫn "Theo hướng dẫn" với `legal_section` ∈ {M1, M2}, không dòng "Chưa có căn cứ"; `sources` provider nhận = đúng {M1, M2} (không M3, M4), `source_sections` của log cùng tập; `ai_log` trỏ log "Thành công", `rejected_citations = 0`; `doctor_request` lưu nguyên văn | TC-AI-01 | FR-AI-001, FR-AI-002 | `test_TC_AI_01_du_thao_5_buoc_co_trich_dan` |
| 2 | Hàm thuần: `check_citations` với 1 trích dẫn có `quote` không có trong `plain_text` của mục → 1 bị loại (`not_verbatim`), còn lại giữ; `label_unsupported` thêm "Chưa có căn cứ" cho đúng bước đó; `build_rows` trả `rejected = 1`. Thêm: khác khoảng trắng/dấu câu vẫn khớp; khác chữ (một từ) không khớp; `quote` rỗng → `missing_quote`; mục ngoài nguồn → `unknown_section`; ranh giới từ | TC-AI-02 | FR-AI-005 | `tests/unit/test_ai_citation.py::test_TC_AI_02_loai_trich_dan_khong_nguyen_van` (+ các test `test_FR_AI_005_*`) |
| 3 | Tích hợp của #2: provider trả 1 trích dẫn sai ở bước S002 (bước đó chỉ có trích dẫn này) → bản nháp: S002 có đúng 1 dòng "Chưa có căn cứ", không dòng nào chứa đoạn trích sai; NC AI Log `rejected_citations = 1` | TC-AI-02 | FR-AI-005 | `test_TC_AI_02_nhat_ky_ghi_trich_dan_bi_loai` |
| 4 | `doctor_request` = "Khoa dùng máy siêu âm cầm tay thay máy siêu âm tại giường"; provider trả bước S003 có trích dẫn đúng nguyên văn M1 với `relation = "Khác biệt"`, `request_excerpt` = "dùng máy siêu âm cầm tay" → trích dẫn của S003 "Khác biệt", `deviation_reason` = "dùng máy siêu âm cầm tay". Nhánh phụ: `request_excerpt` không có trong yêu cầu → `deviation_reason` = cả yêu cầu. Người soạn `update_citation(deviation_reason=…)` sửa được | TC-AI-03 | FR-AI-003 | `test_TC_AI_03_khac_biet_lay_ly_do_tu_yeu_cau` |
| 5 | Dịch vụ Y không có mục nào đủ điều kiện: `prepare_ai_draft` → `no_sources = true`; `start_ai_draft(confirm_no_source=0)` → `NoSourceError`, không có bản nháp, không có NC AI Log mới; `confirm_no_source=1` → provider nhận `sources = []`; mọi trích dẫn AI trả về bị loại; bản nháp có "Chưa có căn cứ" ở cả 7 phần và mọi bước, không dòng nào khác | TC-AI-04 | FR-AI-004 | `test_TC_AI_04_khong_co_nguon_canh_bao_roi_chua_co_can_cu` |
| 6 | Bản nháp AI 5 bước (nội dung đủ điều kiện gửi duyệt khác); `accept_suggestions` cho S001, S002, S004, S005 và mọi dòng nguồn lực → `remaining = 1`; `apply_action(name, "Gửi duyệt")` → bị từ chối, thông báo chứa "Bước S003 còn là đề xuất AI chưa xử lý", vẫn "Nháp"; sau khi chấp nhận S003 → gửi duyệt thành công. Nhánh phụ: `reject_suggestion` cho một bước đề xuất xóa bước + nguồn lực + trích dẫn của bước, mã không tái dùng; gọi cho bước đã chấp nhận → lỗi | TC-AI-10 | FR-AI-008 | `test_TC_AI_10_con_de_xuat_tu_choi_gui_duyet` |
| 7 | AI tắt: `prepare_ai_draft` → `ai_enabled = false`; `start_ai_draft` → lỗi "Tính năng AI đang tắt", không log; `create_procedure` vẫn tạo bản nháp trống 8 phần (UC-004 1a) | — | FR-AI-015, FR-AI-001 | `test_UC004_1a_ai_tat_soan_tay` |
| 8 | Đã có bản "Nháp" của (X, K): `prepare_ai_draft` trả `existing`; `start_ai_draft` → `ExistingProcedureError` kèm `existing_procedure`; bản nháp được tạo bởi người khác giữa lúc job chạy → job `failed` với thông báo dẫn tới bản đó, không tạo bản thứ hai (UC-004 1b, DI-02) | — | FR-PROC-002, FR-AI-001 | `test_UC004_1b_da_co_ban_nhap` |
| 9 | Provider ném `ProviderTimeout` / trả JSON sai lược đồ 3.3 (thiếu `steps`) → job `failed` với thông điệp gateway, không có bản nháp, NC AI Log "Quá hạn" / "Lỗi"; gọi lại `start_ai_draft` với cùng tham số được; `create_procedure(..., doctor_request=…)` tạo bản nháp trống giữ yêu cầu (UC-004 4a) | — | FR-AI-010, FR-AI-002 | `test_UC004_4a_ai_loi_khong_tao_ban_nhap` |
| 10 | Mục chọn thêm: M5 (ánh xạ dịch vụ khác, "Còn hiệu lực") có trong `sources` provider nhận; M4 ("Hết hiệu lực") trong `extra_sections` → `ValidationError` nêu M4; nguồn gửi đi qua `guard.build_source` (không có khóa ngoài `name, section_no, heading, plain_text`); quy trình hiện hành (bản "Đã ban hành" của X ở khoa khác) được gửi dưới khóa `current_procedure` qua `build_source("NC Clinical Procedure", …)` | — | FR-AI-001, FR-AI-011 | `test_FR_AI_001_nguon_chon_them_va_quy_trinh_hien_hanh` |
| 11 | DI-08 ở controller: trích dẫn `legal_section = M1` với `quote` không có trong M1 → lưu bị từ chối; `quote` khớp sau chuẩn hóa → lưu được; `legal_section = "Điều 5"` (chữ tự do) không bị kiểm | — | FR-AI-005 (DI-08) | `test_DI_08_doan_trich_nguyen_van` |
| 12 | Thuần: `parse_draft` — lược đồ đúng → `Draft`; thiếu `steps`/bước thiếu `description` → `DraftError` liệt kê; `phase`, `resource_type` lạ được sửa và có `warnings`; `quantity ≤ 0` → bỏ dòng; `resolve_deviation_reason` hai nhánh; `request_variables` không chứa khóa ngoài danh sách | — | FR-AI-002, FR-AI-003 | `tests/unit/test_procedure_ai_draft.py` (độ phủ `ai/citation.py`, `procedure/ai_draft.py` ≥ 90%) |
| 13 | Quyền: NC Auditor và NC Finance gọi `prepare_ai_draft`, `start_ai_draft`, `accept_suggestions`, `reject_suggestion` → `PermissionError`; NC Clinician khoa khác gọi `start_ai_draft` cho khoa K → `PermissionError`; `get_ai_draft_status` của job người khác → `PermissionError` | — | FR-ACC-003, FR-ACC-007 | `test_quyen_ai_draft` |
| 14 | Gateway: `complete(..., postprocess=f)` với `f` trả `(data, 2)` → log `rejected_citations = 2`; `f` ném lỗi → `ok = False`, log "Lỗi"; không truyền `postprocess` → hành vi cũ (`test_nc_ai_log`, `test_nc_ai_settings` xanh nguyên trạng) | — | FR-AI-005, FR-AI-009 | `test_FR_AI_005_gateway_postprocess` (trong `test_procedure_ai.py`) |
| 15 | Mẫu lệnh: sau migrate có `DRAFT_PROCEDURE-v2` đang dùng khi v1 còn mặc định; chạy lại `ensure_draft_procedure_v2` không tạo v3; v1 đã bị Admin thay bằng v2 tự soạn → không tạo thêm | — | FR-AI-014 | `test_mau_lenh_draft_procedure_v2` |

## 5. Giả định và rủi ro

ASM-024-01..14: `docs/decisions/assumptions/FEAT-024.md`.

| Rủi ro | Giảm thiểu |
| :-- | :-- |
| Mô hình thật trả JSON lệch lược đồ, trích dẫn không nguyên văn nhiều | `parse_draft` chịu lỗi nhẹ (sửa + cảnh báo); trích dẫn sai bị loại an toàn → "Chưa có căn cứ"; chấm chất lượng mẫu lệnh trên 10 dịch vụ mẫu trước R2 (implementation-plan, không thuộc FEAT) |
| Lời gọi dài hơn thời hạn worker web | Chạy ở hàng đợi `long` (ADR-009, ASM-023-15), `timeout` job = `timeout_seconds + 60` |
| Trùng bản nháp do hai người cùng soạn | `_refuse_if_exists` lúc bắt đầu và lúc ghi; DI-02 ở controller là lớp cuối |
| `legal_section` vẫn là Data | Lưu tên `LS-…` (tương thích khi đổi sang Link), DI-08 áp khi tên là mục có thật (ASM-024-02, 08) |
| Văn bản phần do AI soạn không có cờ "Đề xuất" | Ghi ASM-024-10; trích dẫn và nhãn quan hệ vẫn hiện nguồn gốc; dải cảnh báo trên trình soạn nhắc "Nội dung phần do AI soạn, kiểm trước khi gửi duyệt". Lead xem xét nếu cần AMD thêm cờ cấp phần |
| Cache Redis mất trạng thái job (khởi động lại) | `get_ai_draft_status` trả `unknown`; giao diện báo "Không còn theo dõi được, mở danh sách quy trình để kiểm" và cho thử lại; bản nháp nếu đã tạo vẫn được 1b chặn trùng |
