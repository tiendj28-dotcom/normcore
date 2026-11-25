# FEAT-023 — Gateway AI: cấu hình, bộ chuyển đổi, nhật ký, hạn mức, chặn nguồn — Thiết kế kỹ thuật

Issue NORM-55. Nguồn: `srs.md` FR-AI-009..015, NFR-SEC-004; `use-cases.md` UC-017 (bước 4, 4a, 4b, 4c, 4d); `data-model.md` 3.2 (NC AI Settings, NC Prompt Template, NC AI Log), mục 4 (dòng "Cấu hình AI, mẫu lệnh", "Nhật ký AI, sổ sự kiện"); `architecture.md` ADR-005, ADR-007, mục 5 (bố cục `ai/`), 6.1; `ux-foundations.md` SCR-DSK-029; TC-AI-05, 06, 07, 08, 09, 11, TC-NFR-04. Phụ thuộc FEAT-000 (DONE; As-Built `docs/as-built/FEAT-000.md`).

Giả định: `docs/decisions/assumptions/FEAT-023.md` (ASM-023-01..16). Không có AMD: mọi trường dùng ở đây đã có trong `data-model.md`.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-AI-009 | Mỗi lời gọi `gateway.complete` ghi đúng một NC AI Log, thêm trường `prompt_template` (đã có trong data-model, FEAT-000 chưa làm). Đủ: mục đích, người gọi, bản ghi, mẫu lệnh + phiên bản (qua tên `{code}-v{n}`), mục nguồn, mã băm, kết quả, token vào/ra, thời gian, trạng thái |
| FR-AI-010 | Thời hạn `timeout_seconds` (mặc định 180) truyền xuống bộ chuyển đổi; quá hạn → `AIResult(ok=False, status="Quá hạn")`, thông báo tiếng Việt, log "Quá hạn"; lỗi khác → "Lỗi". Gateway không ghi gì ngoài NC AI Log (không bản nháp dở). Phần "cho phép soạn thủ công" ở nơi gọi là FEAT-024 |
| FR-AI-011 | `ai/guard.py`: bộ dựng nội dung gửi AI theo danh sách cho phép (DocType + trường). Mọi DocType kế toán, tính giá, đơn giá, giá tham chiếu, phương án giá bị từ chối (`GuardError`). Thêm nguồn "Tài liệu của hãng" (ADR-007 [1.1]) là FEAT-038; nguồn "tệp bảng giá công khai" thêm ở FEAT làm EXTRACT_PRICE_LIST (ASM-023-08) |
| FR-AI-012 | DocType Single NC AI Settings; gateway đọc cấu hình ở **mỗi** lời gọi (không cache trong tiến trình ngoài cache tài liệu của Frappe, bị xóa khi lưu). Hai bộ chuyển đổi: Anthropic Messages (đã có, mở rộng) và tương thích OpenAI Chat Completions (mới) |
| FR-AI-013 | Trước khi gọi: token lũy kế tháng (tổng `tokens_in + tokens_out` của NC AI Log tạo trong tháng dương lịch hiện tại) > `monthly_token_budget` (> 0; lũy kế = hạn mức thì không chặn, Quyết định Lead trên NORM-55) → chặn, log "Bị chặn hạn mức", Notification Log cho mọi NC Admin đang bật (một lần mỗi tháng mỗi người) |
| FR-AI-014 | NC Prompt Template có phiên bản: nội dung bất biến sau khi tạo; "sửa" = API `new_prompt_version` tạo bản `version + 1`, đặt đang dùng, bản cũ giữ nguyên và thôi dùng. Mỗi `template_code` tối đa một bản đang dùng |
| FR-AI-015 | `enabled` trong NC AI Settings. Tắt → `frappe.boot.normcore_ai_enabled = false`, API `get_ai_status` trả `enabled: false`, hàm JS `normcore.ai.enabled()` trả `false`; `gateway.ensure_enabled()` ném lỗi cho các API gọi AI của FEAT sau. Luồng thủ công không phụ thuộc AI (test hồi quy) |
| NFR-SEC-004 | `api_key` kiểu Password (Frappe mã hóa, lưu ở `__Auth`); không trả dạng rõ qua API/REST/Version; mọi thông báo lỗi của bộ chuyển đổi che khóa; NC AI Log, Error Log không chứa khóa |

Không làm: nút AI trên các màn hình nghiệp vụ (FEAT-024 soạn quy trình, FEAT-038…), kiểm trích dẫn `ai/citation.py` (FEAT-024), mẫu lệnh chi tiết theo nghiệp vụ (FEAT dùng mẫu sẽ tạo phiên bản mới), hàng đợi `long` + realtime cho lời gọi AI dài (FEAT-024, ADR-009), email cho Admin (FR-NOTI-002, FEAT-002).

Dùng lại, không làm lại: `ai/gateway.py::complete`, `AIResult`, `_write_log`, `providers/base.py`, `providers/anthropic.py`, `providers/mock.py`, DocType NC AI Log (FEAT-000). Mẫu Notification Log của `api/compliance.py` (ASM-100). `core/audit.py::guard_immutable` cho NC AI Log.

**Ràng buộc từ test cũ (không được sửa, CLAUDE.md mục 3 luật 1):** `nc_ai_log/test_nc_ai_log.py` và `tests/unit/test_ai_providers.py` phải xanh nguyên trạng:
- `complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {"a": 1}, ["MS-1","MS-2"])` với cấu hình mặc định (AI chưa bật) → `ok=True`, `data == MOCK_RESPONSE`, log đủ trường → gateway **không** chặn khi `enabled = 0` (ASM-023-03) và phải có mẫu DRAFT_PROCEDURE đang dùng sau khi cài (ASM-023-06).
- `complete(..., "T", ..., provider=AnthropicProvider(post=bad_post))` → log "Lỗi", không lộ khóa.
- `get_provider()` trong test, không tiêm transport → `MockProvider` kể cả khi `site_config` ghi `anthropic`.
- Chữ ký `MockProvider().complete(p, code, vars, sources)`, `AnthropicProvider(api_key, model, post=...)`, `.complete(p, code, vars, sources)` giữ nguyên.

## 2. DocType

Module NC AI. Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes = 1`.

### 2.1 Mới — NC AI Settings (Single)

| Trường | Nhãn | Kiểu | BB | Mặc định | Kiểm (`validate`) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| enabled | Bật AI | Check | | 0 | 0→1: chạy kiểm tra kết nối (mục 3.3); thất bại → từ chối lưu, thông báo lỗi trả về (UC-017 4c) |
| protocol | Giao thức | Select: `OpenAI-compatible` / `Anthropic Messages` | Có | Anthropic Messages | |
| base_url | Địa chỉ | Data | Khi OpenAI-compatible | | Bắt đầu `http://` hoặc `https://`; bỏ `/` cuối. Trống với Anthropic → `https://api.anthropic.com` |
| model | Mô hình | Data | Khi `enabled` | | |
| api_key | Khóa | Password | | | NFR-SEC-004. Trống → dự phòng `NORMCORE_AI_API_KEY` / `site_config.normcore_ai_api_key` (ASM-023-02) |
| timeout_seconds | Thời hạn (giây) | Int | Có | 180 | 1..600 |
| max_output_tokens | Số token trả về tối đa | Int | | 4096 (ASM-023-09) | > 0 |
| monthly_token_budget | Hạn mức token tháng | Int | | 0 | ≥ 0; 0 = không giới hạn (mô tả trường ghi rõ) |
| usage_html | Đã dùng tháng này | HTML | | | Chỉ hiển thị, nạp bằng JS từ `get_ai_usage` |

Quyền (mục 4, "Cấu hình AI, mẫu lệnh"): NC Admin read, write; NC Auditor read; vai trò khác không. `scripts/check_conventions.py` thêm `"NC AI Settings": "Cấu hình AI, mẫu lệnh"` vào `DOCTYPE_ROW` (tiền lệ FEAT-007).

### 2.2 Mới — NC Prompt Template

Naming: `{template_code}-v{version}` (autoname `format:{template_code}-v{version}`). Không vai trò nào có `delete` (NC AI Log trỏ tới).

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| template_code | Mã mẫu | Select: DRAFT_PROCEDURE / CONSISTENCY_CHECK / SUGGEST_NORM_LINK / MAP_SECTION_SERVICE / EXTRACT_PRICE_LIST / MATCH_SERVICE_NAME / SUGGEST_CLS_NORM | Có | `in_list_view`, `in_standard_filter`; bất biến |
| version | Phiên bản | Int | Có | Tự cấp `max(version của code) + 1` khi tạo nếu trống hoặc 0; bất biến; trùng → lỗi |
| is_active | Đang dùng | Check | | Khi = 1 sau lưu: các bản khác cùng `template_code` về 0 (`db_set`, ASM-023-05) |
| system_prompt | Lệnh hệ thống | Long Text | Có | Bất biến sau khi tạo |
| user_prompt | Lệnh người dùng (Jinja) | Long Text | Có | Bất biến; phải dựng được bằng Jinja sandbox (kiểm cú pháp khi lưu) |
| output_schema | Lược đồ JSON đầu ra | Code (JSON) | Có | Bất biến; phải là JSON object hợp lệ |

`validate`: bản đã có (không `is_new`) đổi một trong `template_code`, `version`, `system_prompt`, `user_prompt`, `output_schema` → `frappe.ValidationError` "Mẫu lệnh đã tạo không sửa được. Dùng "Tạo phiên bản mới"." Chỉ `is_active` đổi được. Quyền: NC Admin read, write, create; NC Auditor read.

Dữ liệu cài sẵn (UC-017 bước 1): mỗi mã trong 7 mã có `{code}-v1` đang dùng, nội dung chung (lệnh hệ thống yêu cầu chỉ trả JSON theo lược đồ, không bịa trích dẫn; lệnh người dùng `{{ variables | tojson }}` + danh sách nguồn; lược đồ `{"type": "object"}`). Tạo bằng `normcore.ai.prompts_install.ensure_default_templates()` gọi từ `after_install` và patch `normcore.patches.add_default_prompt_templates` (chỉ tạo khi mã đó chưa có bản nào; không ghi đè). Không dùng fixtures (fixtures ghi đè bản Admin sửa) — ASM-023-06.

### 2.3 Đổi — NC AI Log (FEAT-000)

Thêm `prompt_template` (Mẫu lệnh, Link NC Prompt Template, `read_only`) sau `ref_name`. Thêm trường cho phép NULL nên không cần patch dữ liệu (log cũ để trống). Không đổi quyền (Director, Admin, Auditor đọc; không ai tạo/sửa/xóa). `status` đã có đủ 4 giá trị.

## 3. Thành phần

### 3.1 `normcore/ai/providers/` (thuần, không import `frappe`)

- `base.py`: thêm `class ProviderTimeout(ProviderError)`; `ProviderResponse` giữ nguyên.
- Giao diện mở rộng tương thích ngược: `complete(purpose, template_code, variables, sources, *, system=None, user=None)`. Có `system`/`user` (đã dựng từ mẫu) thì dùng; không có thì giữ cách cũ của FEAT-000.
- `anthropic.py`: thêm tham số `base_url` (đã có), `max_tokens`, `timeout`; `_http_post` dùng `requests.post(..., timeout=timeout)`; `requests.exceptions.Timeout` / `socket.timeout` → `ProviderTimeout("Dịch vụ AI không phản hồi trong {timeout} giây")`; lỗi khác → `ProviderError` đã che khóa (giữ). URL `{base_url}/v1/messages`.
- `openai_compat.py` (mới): `OpenAICompatProvider(api_key, model, base_url, max_tokens=4096, timeout=180, post=None)`. Thiếu `base_url`/`model` → `ProviderError`; khóa có thể trống (máy chủ tự host không cần khóa, ASM-023-10). POST `{base_url}/chat/completions`, header `Authorization: Bearer <key>` (bỏ khi khóa trống), thân `{"model", "max_tokens", "messages": [{"role":"system"},{"role":"user"}]}`. Kết quả `choices[0].message.content`, token `usage.prompt_tokens`, `usage.completion_tokens`. Cùng ánh xạ lỗi, cùng che khóa.
- `mock.py`: giữ nguyên hành vi mặc định.
- `http.py` (mới): `default_post(url, headers, payload, timeout)` dùng chung, ném `ProviderTimeout` khi quá hạn.

### 3.2 `normcore/ai/guard.py` (thuần) — FR-AI-011, NFR-SEC-005, ADR-007

```python
class GuardError(Exception): ...
ALLOWED_SOURCES: dict[str, frozenset[str]]       # DocType -> trường được gửi
ALLOWED_CHILDREN: dict[str, dict[str, frozenset]] # DocType cha -> {trường bảng con: trường được gửi}
FORBIDDEN_DOCTYPES: frozenset[str]               # danh sách tường minh để kiểm thử và đọc mã
def is_allowed(doctype: str) -> bool
def build_source(doctype: str, record: Mapping, fields: Iterable[str] | None = None) -> dict
def budget_exceeded(used: int, budget: int) -> bool   # budget > 0 and used > budget (ASM-023-04, Lead)
```

| DocType được phép | Trường |
| :-- | :-- |
| NC Legal Section | `name`, `section_no`, `heading`, `plain_text` |
| NC Technical Service | `service_code`, `service_name` |
| NC Clinical Procedure | `name`, `technical_service`, `doctor_request`, `overview`, `indications`, `contraindications`, `cautions`, `preparation_notes`, `monitoring`, `references`; bảng con `steps` (`step_id`, `phase`, `step_title`, `description`, `reference_minutes`), `resources` (`resource_row_id`, `step_id`, `resource_type`, `resource_text`, `quantity`, `uom`, `headcount`) |
| NC Item | `item_code`, `item_name`, `uom` |
| NC Equipment | `equipment_code`, `equipment_name` |

`FORBIDDEN_DOCTYPES` (từ data-model mục 4 các dòng tiền/kế toán/tính giá/giá): NC Item Price, NC Costing Parameter Set, NC Job Title Rate, NC Price Category, NC Account Mapping, NC Accounting Import, NC Accounting Import Line, NC Accounting Import Total, NC Cost Center, NC Cost Center Driver, NC Allocation Rule, NC Service Volume, NC Test System Volume, NC Equipment Usage, NC Stock Issue Actual, NC Costing Run, NC Scenario Change, NC Service Cost, NC Service Cost Line, NC Test System Cost, NC Reconciliation Line, NC Benchmark Price, NC CPI Index, NC Adjustment Suggestion, NC Price Proposal, NC Price Proposal Item, NC Norm Set, NC Norm Line, NC Room, NC Equipment Component, NC Equipment Allocation, NC AI Settings.

Hành vi `build_source`:
1. `doctype` không trong `ALLOWED_SOURCES` (kể cả mọi DocType trong `FORBIDDEN_DOCTYPES` và mọi DocType lạ) → `GuardError("Không được gửi dữ liệu của <doctype> cho AI")`.
2. `fields` có trường ngoài danh sách (ví dụ `NC Equipment.original_cost`, `NC Item.price_history_html`) → `GuardError` nêu trường.
3. Trả dict chỉ gồm trường được phép (trường cho phép nhưng record không có thì bỏ), bảng con lọc theo `ALLOWED_CHILDREN`. Không bao giờ sao chép khóa lạ của `record`.

Khẳng định bất biến (test): `ALLOWED_SOURCES.keys() ∩ FORBIDDEN_DOCTYPES = ∅`. Thêm nguồn = sửa mã có test (ADR-007), không phải cấu hình.

### 3.3 `normcore/ai/prompts.py` (thuần)

- `render(user_prompt: str, variables: dict, sources: list) -> str`: Jinja2 `SandboxedEnvironment(undefined=StrictUndefined)`, filter `tojson` (ensure_ascii=False). Lỗi dựng → `PromptError`.
- `check_syntax(user_prompt) -> None` (dùng ở `validate` của NC Prompt Template).
- `parse_schema(text) -> dict` (JSON object, không thì `PromptError`).
- `check_output(data, schema) -> list[str]`: kiểm tối thiểu `type` (object/array/string/number/integer/boolean), `required`, `properties` lồng, `items` (ASM-023-07). Danh sách lỗi rỗng = đạt.

### 3.4 `normcore/ai/gateway.py` (mở rộng, không viết lại)

```python
OK, ERROR, TIMEOUT, BLOCKED = "Thành công", "Lỗi", "Quá hạn", "Bị chặn hạn mức"
def get_settings() -> frappe._dict   # đọc NC AI Settings mỗi lần gọi; api_key qua get_password (không cache ngoài doc cache)
def is_enabled() -> bool
def ensure_enabled() -> None          # ném frappe.ValidationError "Tính năng AI đang tắt" — FEAT sau gọi ở API của nút AI
def get_provider(settings=None)       # xem dưới
def monthly_usage(now=None) -> int    # SUM(tokens_in+tokens_out) NC AI Log, creation trong tháng hiện tại
def ping(settings=None) -> AIResult   # kiểm tra kết nối; không ghi NC AI Log, không tính hạn mức
def complete(purpose, template_code, variables, sources, ref_doctype=None, ref_name=None, provider=None) -> AIResult
```

`get_provider(settings)`:
1. `frappe.flags.in_test`: có `frappe.flags.normcore_ai_transport` (hàm `post` giả do test tiêm) → dựng bộ chuyển đổi **thật** theo `settings.protocol` với `post` đó (không gọi mạng; để kiểm TC-AI-11, TC-AI-05). Không có → `MockProvider()` (giữ test cũ; CLAUDE.md mục 3 luật 6).
2. `site_config.normcore_ai_provider == "mock"` → `MockProvider()` (dev/staging smoke, ASM-023-11).
3. Theo `protocol`: `Anthropic Messages` → `AnthropicProvider`, `OpenAI-compatible` → `OpenAICompatProvider`, với `base_url`, `model`, khóa, `max_output_tokens`, `timeout_seconds` của cấu hình hiện tại.

`complete` — thứ tự (mỗi nhánh ghi đúng một NC AI Log, trừ khi không ghi được log thì ném lỗi):
1. `settings = get_settings()`; băm yêu cầu như FEAT-000.
2. Hạn mức: `guard.budget_exceeded(monthly_usage(), settings.monthly_token_budget)` → `status = BLOCKED`, `error = "Đã vượt hạn mức token tháng (đã dùng X / Y). Liên hệ quản trị."`, ghi log (token 0), `_notify_budget(used, budget)`; trả về. Không gọi provider.
3. Mẫu lệnh: bản `is_active = 1` của `template_code`; không có → `ERROR` "Chưa có mẫu lệnh đang dùng cho <code>", log (prompt_template trống). Có → `prompt.render(...)`; lỗi dựng → `ERROR`.
4. Gọi `provider.complete(purpose, template_code, variables, sources, system=..., user=...)` (provider tiêm vào thì cũng truyền system/user). `ProviderTimeout` → `TIMEOUT`, `error = "Dịch vụ AI không phản hồi trong N giây. Dữ liệu của bạn được giữ nguyên; có thể soạn thủ công."`; `ProviderError` → `ERROR`.
5. Phân tích JSON; `prompts.check_output` có lỗi → `ERROR` "Kết quả AI không đúng lược đồ: …" (giữ `text` trong log).
6. `_write_log(..., prompt_template=name)`. Mọi chuỗi ghi log đi qua `_redact(text, key)` (thay khóa bằng `***`).

Không ghi, không sửa bản ghi nào ngoài NC AI Log và Notification Log (FR-AI-010: không bản nháp dở). Không `frappe.db.commit()` trong gateway.

`_notify_budget(used, budget)`: người nhận = User đang bật có vai trò NC Admin, bỏ Administrator, Guest (cùng cách `api/compliance.py`). Tiêu đề "Đã vượt hạn mức token AI tháng MM/YYYY"; bỏ qua nếu người đó đã có Notification Log cùng tiêu đề (một lần mỗi tháng, ASM-023-04). `document_type = "NC AI Settings"`, `document_name = "NC AI Settings"`, `type = "Alert"`, `email_content` nêu đã dùng / hạn mức.

`ping(settings)`: gọi provider với `system="Trả về JSON {\"ok\": true}"`, `user="ping"`; trả `AIResult` (OK / Quá hạn / Lỗi + thông báo đã che khóa). Không log, không tính token (ASM-023-12).

### 3.5 Controller

- `nc_ai_settings.py`: `validate` (mục 2.1); khi `enabled` 0→1: `res = gateway.ping(self_as_settings)`; `not res.ok` → `frappe.throw(_("Kiểm tra kết nối thất bại: {0}. AI chưa được bật.").format(res.error))`. Lấy khóa: nếu trường `api_key` vừa nhập (khác `*`) thì dùng giá trị mới, không thì `get_password`.
- `nc_prompt_template.py`: `autoname`/`before_insert` cấp `version`; `validate` (bất biến, cú pháp, lược đồ); `on_update` khi `is_active` → tắt bản khác (`frappe.db.set_value`, cùng giao dịch).

### 3.6 API `normcore/api/ai.py` (`@frappe.whitelist()`, kiểm quyền tường minh)

| Hàm | Tham số | Quyền | Kết quả / lỗi |
| :-- | :-- | :-- | :-- |
| `get_ai_status()` | — | mọi người dùng đã đăng nhập | `{"enabled": bool}`; không lộ cấu hình khác |
| `test_connection()` | — | `frappe.has_permission("NC AI Settings", "write")` (NC Admin) | `{"ok", "status", "message", "duration_ms"}` theo cấu hình **đã lưu**; thông báo đã che khóa; không đổi `enabled`. Không quyền → `frappe.PermissionError` |
| `get_ai_usage()` | — | `read` NC AI Settings (Admin, Auditor) | `{"used": int, "budget": int, "month": "MM/YYYY", "blocked": bool}` |
| `new_prompt_version(template_code, system_prompt, user_prompt, output_schema)` | | `create` NC Prompt Template (Admin) | Tạo `{code}-v{max+1}`, `is_active = 1`, bản cũ thôi dùng; trả `{"name", "version"}`. Lỗi cú pháp / lược đồ → `ValidationError` tiếng Việt |

`boot_session` (hook `boot_session = "normcore.api.ai.boot_session"`): `bootinfo.normcore_ai_enabled = gateway.is_enabled()`.
`normcore/public/js/normcore_ai.js` (khai báo `app_include_js`): `normcore.ai.enabled()` đọc `frappe.boot.normcore_ai_enabled`; `normcore.ai.toggle(frm_or_el)` tiện ích ẩn nút. FEAT sau thêm nút AI phải bọc bằng hàm này **và** gọi `gateway.ensure_enabled()` ở máy chủ.

## 4. Quyền

| DocType | NC Admin | NC Auditor | NC Director | Vai trò khác |
| :-- | :-- | :-- | :-- | :-- |
| NC AI Settings | R, W | R | — | — |
| NC Prompt Template | R, W, C | R | — | — |
| NC AI Log | R | R | R | — (không đổi) |

Không vai trò nào có `delete`, `submit`, `import`. Auditor không có W/C (`check_conventions.py` NC Auditor không ghi).

## 5. Logic thuần và ánh xạ

| Module / hàm | FR / NFR | Golden |
| :-- | :-- | :-- |
| `ai/guard.py::build_source`, `is_allowed` | FR-AI-011, NFR-SEC-005, ADR-007 | Không có (không phải phép tính giá) |
| `ai/guard.py::budget_exceeded` | FR-AI-013 | Không có |
| `ai/prompts.py::render`, `check_output` | FR-AI-014, ADR-005 (kiểm lược đồ) | Không có |
| `ai/providers/*` | FR-AI-010, FR-AI-012, NFR-SEC-004 | Không có |

FEAT không có phép tính tiền; không đụng `costing/`, `docs/golden/`.

## 6. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test (đề xuất) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Tiêm transport ném `requests.Timeout`, `timeout_seconds = 5`: `complete(..., ref=quy trình P)` → `ok=False`, `status="Quá hạn"`, `error` tiếng Việt chứa "không phản hồi"; transport nhận `timeout=5`; P không đổi (`modified`, nội dung); số NC Clinical Procedure không đổi; đúng một log mới "Quá hạn". `test_connection` cùng tình huống trả `status="Quá hạn"` | TC-AI-05 | FR-AI-010 | `nc_ai_settings/test_nc_ai_settings.py::test_TC_AI_05_qua_han_giu_du_lieu` |
| 2 | `build_source` với từng DocType trong `FORBIDDEN_DOCTYPES` và mọi DocType `NC *` trong `normcore/*/doctype/*.json` ngoài `ALLOWED_SOURCES` → `GuardError`; 5 DocType được phép đi qua và chỉ trả trường cho phép (khóa lạ, `original_cost` bị bỏ/từ chối); hai tập rời nhau | TC-AI-06 | FR-AI-011 | `tests/unit/test_ai_guard.py::test_TC_AI_06_*` |
| 3 | `enabled = 0`: `boot_session` → `normcore_ai_enabled = False`; `get_ai_status()` → `enabled False`; `ensure_enabled()` ném lỗi; tạo NC Clinical Procedure, `make_norm_set` + khóa, tạo NC Benchmark Price (nếu DocType đã có trên develop; không thì bỏ phần này, ghi log) bằng tay vẫn thành công. Bật lại → `True` | TC-AI-07 | FR-AI-015 | `test_nc_ai_settings.py::test_TC_AI_07_tat_ai` |
| 4 | `complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", vars, ["LS-0000001"], "NC Clinical Procedure", P)` bằng provider giả lập → log có `purpose`, `user`, `ref_doctype`, `ref_name`, `prompt_template = "DRAFT_PROCEDURE-v<n>"` (bản đang dùng), `source_sections`, `tokens_in`, `tokens_out`, `duration_ms`, `status="Thành công"` (ASM-023-13) | TC-AI-08 | FR-AI-009 | `test_nc_ai_settings.py::test_TC_AI_08_log_du_truong` |
| 5 | `monthly_token_budget = 1000`, chèn log tháng này tổng 1.200 token → `complete` không gọi provider (transport không được gọi), `status="Bị chặn hạn mức"`, log mới "Bị chặn hạn mức"; mỗi NC Admin đang bật có đúng một Notification Log tiêu đề tháng; gọi lần nữa không thêm thông báo; log tháng trước không tính | TC-AI-09 | FR-AI-013 | `test_nc_ai_settings.py::test_TC_AI_09_chan_han_muc` |
| 6 | Cấu hình Anthropic + `base_url` A → transport nhận `A/v1/messages`; lưu OpenAI-compatible + `base_url` B (cùng tiến trình, không clear cache tay) → lời gọi kế tiếp tới `B/chat/completions`, header `Authorization: Bearer`, thân OpenAI | TC-AI-11 | FR-AI-012 | `test_nc_ai_settings.py::test_TC_AI_11_doi_dia_chi` |
| 7 | Lưu `api_key = "SK-TEST-123"`: `frappe.get_doc` / `frappe.client.get` / REST `GET /api/resource/NC AI Settings/NC AI Settings` (Admin) không chứa chuỗi; Version của NC AI Settings không chứa; gọi lỗi có khóa trong ngoại lệ → NC AI Log, Error Log, kết quả `test_connection` không chứa; `get_password` vẫn trả đúng ở máy chủ | TC-NFR-04 | NFR-SEC-004 | `test_nc_ai_settings.py::test_TC_NFR_04_khoa_khong_lo` |
| 8 | Sửa nội dung bản đã có → bị từ chối; `new_prompt_version` → `-v2` đang dùng, `-v1` còn, nội dung cũ không đổi, thôi dùng; gateway dùng `-v2` | — | FR-AI-014 | `nc_prompt_template/test_nc_prompt_template.py::test_FR_AI_014_*` |
| 9 | Bật AI khi `ping` thất bại → lưu bị từ chối, `enabled` vẫn 0 (UC-017 4c) | — | FR-AI-012 | `test_nc_ai_settings.py::test_UC017_4c_bat_ai_kiem_ket_noi` |
| 10 | Quyền: Auditor đọc NC AI Settings, NC Prompt Template, không ghi/tạo/xóa; NC Clinician, NC Finance không đọc; NC Clinician gọi `test_connection`, `new_prompt_version` → PermissionError | — | mục 4 | `test_quyen_*` trong hai tệp test |
| 11 | OpenAI-compatible: phân tích `choices`, `usage`; quá hạn → `ProviderTimeout`; lỗi không lộ khóa | — | FR-AI-012, NFR-SEC-004 | `tests/unit/test_ai_providers_openai.py` |
| 12 | Test cũ `test_nc_ai_log`, `test_ai_providers` xanh nguyên trạng | — | FR-AI-009 | — |

Mọi test dùng provider giả lập / transport giả; không test nào gọi mạng (CLAUDE.md mục 3 luật 6).

## 7. Giả định và rủi ro

Giả định chi tiết ở `docs/decisions/assumptions/FEAT-023.md`. Rủi ro:
- **Thời hạn HTTP**: `requests` timeout là thời hạn đọc từng lần, không phải tổng; nhà cung cấp nhỏ giọt dữ liệu có thể vượt 180 giây. Chấp nhận ở FEAT này; FEAT-024 chạy lời gọi trong hàng đợi `long` có thời hạn job.
- **Gateway không tự chặn khi AI tắt** (ASM-023-03, ràng buộc test cũ): an toàn dựa vào `ensure_enabled()` ở API của từng nút AI. Reviewer FEAT-024 trở đi phải kiểm.
- **Lũy kế tháng tính lúc gọi**: hai lời gọi song song có thể cùng qua khi sát hạn mức (vượt tối đa một lời gọi). Chấp nhận.
- **Test hồi quy TC-AI-07 phần giá tham chiếu**: NC Benchmark Price chưa có trên develop (FEAT benchmark R2). Dev kiểm phần có thể; QA ghi rõ phần chưa kiểm được.
