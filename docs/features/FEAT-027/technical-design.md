# FEAT-027 — Trích bảng giá PDF bằng AI — Thiết kế kỹ thuật

Issue NORM-82. Bản phát hành R3. Phụ thuộc FEAT-023 (gateway AI, mẫu lệnh, NC AI Log), FEAT-026 (NC Benchmark Facility, NC Benchmark Price, `benchmark/reference.py`), cả hai có `DONE` trên `develop`.

Nguồn: `srs.md` FR-BM-003, FR-BM-004, FR-BM-005, FR-BM-007, FR-AI-008..011, FR-AI-015; `use-cases.md` UC-013 luồng 2a, 2b, 2c; `data-model.md` NC Benchmark Price, mục 4 dòng "Giá tham chiếu, chỉ số giá"; `ux-foundations.md` SCR-DSK-025; `test-cases.md` TC-BM-05; As-Built FEAT-020 (`library/extract.py`), FEAT-023 (`ai/gateway.py`, `ai/guard.py`, `ai/prompts_install.py`), FEAT-026 (hợp đồng `before_insert` + `ai_log`), FEAT-038 (mẫu tác vụ nền AI `api/cls_norm_ai.py`). Giả định: `docs/decisions/assumptions/FEAT-027.md` (ASM-027-01..12).

FEAT này không có phép tính tiền. Giá trích từ tệp được lưu nguyên số AI đọc (sau khi kiểm là số dương); không dùng `docs/golden/`.

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-BM-003 | Đủ | Nạp tệp PDF của một đơn vị tham chiếu → tách chữ theo trang (`library/extract.py`) → gateway (`EXTRACT_PRICE_LIST`) → mỗi dòng hợp lệ thành một NC Benchmark Price có `ai_log`, trạng thái "Đề xuất" |
| FR-BM-004 | Dùng lại | Dòng AI chỉ có tên gốc; `before_insert` của FEAT-026 đề xuất dịch vụ khớp bằng quy tắc (`reference.suggest_service`). Không gọi AI để so khớp tên (ASM-027-09) |
| FR-BM-005 | Dùng lại | Dòng "Đề xuất" không vào `get_comparable_prices` (TC-BM-05 "chưa tham gia so sánh") |
| FR-BM-007 | Dùng lại | Dòng trùng bị `validate` của FEAT-026 từ chối; FEAT này đếm và báo, các dòng khác vẫn tạo (UC-013 2b) |
| FR-AI-008 | Đủ | Dòng AI luôn "Đề xuất" cho đến khi người có quyền xác nhận bằng `confirm_prices` (FEAT-026) |
| FR-AI-009 | Dùng lại | Một lời gọi = một NC AI Log do gateway ghi; `ref_doctype = NC Benchmark Facility` |
| FR-AI-010 | Đủ | AI lỗi, quá hạn, bị chặn hạn mức → không tạo dòng nào, báo lỗi, gợi ý nhập tay hoặc Excel (UC-013 2c) |
| FR-AI-011 | Đủ | Chỉ gửi chữ tách từ tệp người dùng nạp (bảng giá công khai, ghi chú FR-BM-003). Không gửi bản ghi DocType nào; NC Benchmark Price, NC CPI Index, NC Price Category giữ trong `FORBIDDEN_DOCTYPES` |
| FR-AI-015 | Đủ | Nút AI chỉ hiện khi `normcore.ai.enabled()`; máy chủ gọi `gateway.ensure_enabled()`. AI tắt: form, Excel của FEAT-026 vẫn chạy (phần giá tham chiếu của TC-AI-07, ASM-023-16) |

Ngoài phạm vi: gợi ý tên dịch vụ bằng AI (mẫu `MATCH_SERVICE_NAME`, ASM-027-09); màn hình so sánh (FEAT-028); tệp Excel/DOCX qua AI (Excel đã có bộ nhập FEAT-026). Không sửa test của FEAT-023, FEAT-026.

## 2. DocType

**Không có DocType mới, không đổi trường** (không cần AMD, không cần patch).

NC Benchmark Price (FEAT-026) dùng nguyên các trường có sẵn cho dòng AI:

| Trường | Giá trị dòng AI tạo |
| :-- | :-- |
| `facility` | đơn vị người dùng chọn |
| `service_name_raw` | tên dịch vụ AI đọc (cắt 140 ký tự) |
| `technical_service` | để trống; `before_insert` đề xuất bằng quy tắc |
| `price` | giá AI đọc, sau `parse_price` (3.1) |
| `price_category` | loại giá người dùng chọn trong hộp thoại (một tệp = một loại giá, ASM-027-03) |
| `effective_date` | ngày AI đọc của dòng; không có thì ngày hiệu lực mặc định người dùng nhập (ASM-027-04) |
| `source_doc_no` | số văn bản người dùng nhập (tùy chọn) |
| `source_file` | `file_url` của tệp PDF đã nạp |
| `source_url` | `file_url + "#page=N"` (trang chứa dòng) để mở đúng trang gốc khi rà soát (UC-013 2a, ASM-027-06); dài quá 140 ký tự thì bỏ trống |
| `ai_log` | tên NC AI Log của lời gọi |
| `status` | không đặt; `before_insert` → "Đề xuất" vì có `ai_log` (ASM-026-02) |

Quyền giữ nguyên ma trận FEAT-026 (data-model mục 4, dòng "Giá tham chiếu, chỉ số giá"): NC Finance, NC Consultant W; NC Department Head, NC Director, NC Admin, NC Auditor R; vai khác không. API mới kiểm `create` trên NC Benchmark Price.

## 3. Thành phần

### 3.1 `normcore/benchmark/pdf_extract.py` — thuần, không import `frappe`

| Hàm / hằng | Kết quả | FR |
| :-- | :-- | :-- |
| `MAX_PAGES = 30` | Số trang tối đa một tệp (ASM-027-05) | FR-AI-013 (giới hạn token) |
| `REQUIRE_NAME_IN_SOURCE = True` | Bật kiểm tên có trong chữ của tệp (ASM-027-07) | FR-AI-005 (tinh thần) |
| `SKIP_NO_NAME`, `SKIP_BAD_PRICE`, `SKIP_NO_DATE`, `SKIP_NOT_IN_FILE` | Lý do bỏ dòng, tiếng Việt: "Thiếu tên dịch vụ", "Giá không hợp lệ", "Thiếu ngày hiệu lực", "Không thấy trong tệp" | |
| `page_sources(pages) -> list[dict]` | `[{"page": n, "text": t}]` cho trang có chữ, theo thứ tự; `Page.number` lấy từ `library.extract.Page` | FR-AI-011 |
| `check_page_count(pages)` | `len(pages) > MAX_PAGES` → `ValueError("Tệp có {n} trang, vượt {MAX_PAGES} trang. Tách tệp rồi nạp lại.")` | |
| `parse_price(value) -> Decimal \| None` | `int`/`float`/`Decimal` (không phải `bool`) → `Decimal(str(v))`. Chuỗi: bỏ khoảng trắng, "đ", "₫", "VNĐ", "VND" (không phân biệt hoa thường); khớp `^\d{1,3}([.,]\d{3})+$` → bỏ dấu phân cách nghìn; khớp `^\d+([.,]\d{1,2})?$` → "," thành "."; khác → `None`. Kết quả `<= 0` → `None` | FR-BM-003 |
| `parse_date(value) -> date \| None` | Nhận `YYYY-MM-DD`, `DD/MM/YYYY`, `D/M/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`; sai hoặc không phải ngày thật → `None` | FR-BM-003 |
| `locate(name, pages, hint=None) -> int \| None` | `n = reference.normalize_name(name)`; có `hint` hợp lệ và `n` nằm trong `normalize_name(text)` của trang `hint` → `hint`; không thì trang đầu tiên chứa `n`; không có → `None` | UC-013 2a |
| `parse_rows(data, pages, default_date=None) -> (rows, skipped)` | `data` phải là dict có `rows` là list, không thì `ValueError("Kết quả AI thiếu danh sách rows")` (gateway ghi log "Lỗi"). Mỗi phần tử dict `{"service_name", "price", "effective_date", "page"}`: tên trống → bỏ `SKIP_NO_NAME`; `parse_price` None → `SKIP_BAD_PRICE`; `parse_date(effective_date) or default_date` None → `SKIP_NO_DATE`; `REQUIRE_NAME_IN_SOURCE` và `locate` None → `SKIP_NOT_IN_FILE`. Dòng hợp lệ: `{"service_name_raw": tên.strip()[:140], "price": Decimal, "effective_date": date, "page": int \| None}`. `skipped`: `[{"service_name", "reason"}]`, giữ thứ tự AI trả. Phần tử không phải dict → `SKIP_NO_NAME` | FR-BM-003, FR-AI-008 |
| `source_url(file_url, page, max_len=140) -> str \| None` | `f"{file_url}#page={page}"` khi có `page` và độ dài ≤ `max_len`; không thì `None` | ASM-027-06 |
| `summary(created, duplicates, skipped) -> dict` | `{"created": n, "duplicates": [..], "skipped": [..], "not_in_file": số SKIP_NOT_IN_FILE}` | |

Độ phủ `normcore/benchmark/` ≥ 90% (lệnh chuẩn đã có `--cov=normcore/benchmark`).

### 3.2 Mẫu lệnh `EXTRACT_PRICE_LIST-v2` — `normcore/ai/prompts_install.py` (nối thêm)

`EXTRACT_PRICE_LIST-v1` (mặc định chung) đã cài bởi FEAT-023. Thêm hằng `PRICE_LIST_V2_SYSTEM`, `PRICE_LIST_V2_USER` và `ensure_extract_price_list_v2()` = `_ensure_v2("EXTRACT_PRICE_LIST", ...)`; gọi lười ở đầu tác vụ nền, không qua patch (cùng cách ASM-025-11, ASM-038-14: test FEAT-023 đòi bản dùng là v1 sau cài đặt; bản Admin đã sửa không bị ghi đè).

- System (tiếng Việt): trích bảng giá dịch vụ y tế; chỉ dựa trên chữ của các trang được gửi; không bịa; mỗi dòng một dịch vụ có giá; `service_name` chép nguyên văn tên trong tệp; `price` là số (đồng, không dấu phân cách); `effective_date` dạng `YYYY-MM-DD` nếu tệp ghi ngày áp dụng, không có thì để trống; `page` là số trang chứa dòng; bỏ dòng tiêu đề, tổng cộng, ghi chú. Chỉ trả về JSON `{"rows": [{"service_name", "price", "effective_date", "page"}]}`.
- User: `"Đơn vị: {{ variables.facility_name }}\nTệp: {{ variables.file_name }}\nCác trang: {{ sources | tojson }}"`.
- `output_schema`: giữ `DEFAULT_SCHEMA` (`{"type": "object"}`) như các bản v2 khác; `parse_rows` kiểm cấu trúc.

`variables` chỉ gồm `facility_name` (tên đơn vị công khai, người dùng tự nhập) và `file_name`. Không có giá, loại giá, dịch vụ hay bản ghi nào khác (FR-AI-011).

### 3.3 `normcore/ai/guard.py` (nối thêm một hàm)

`price_list_pages(pages) -> list[dict]`: nguồn gửi AI cho FR-BM-003 = chữ tách từ tệp bảng giá do người dùng nạp, `[{"page": int, "text": str}]` (gọi `pdf_extract.page_sources` không được vì guard thuần không phụ thuộc benchmark; viết lại ngắn trong guard). Chỉ nhận đối tượng có `number`, `text` (kiểu `Page`); phần tử là dict có `doctype` hoặc bất kỳ mapping nào → `GuardError("Chỉ gửi chữ của tệp bảng giá cho AI")`. Không đổi `ALLOWED_SOURCES`, `FORBIDDEN_DOCTYPES`. Ghi chú trong docstring: căn cứ ghi chú FR-BM-003. Test thêm vào tệp test mới, không sửa test guard cũ.

### 3.4 API — `normcore/api/benchmark_ai.py` (mới; không sửa `api/benchmark.py`)

Mẫu theo `api/cls_norm_ai.py` (FEAT-038): bắt đầu → tác vụ nền `queue="long"`, `timeout = timeout_seconds + 120` → trạng thái trong cache (`normcore:price_list_ai:{job_id}`, TTL 3600 s) + `publish_realtime("normcore_price_list_ai", {job_id, status}, user=...)`. Trong test `now=True` (ASM-027-02).

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `start_price_list_extraction(facility, price_category, file_url, source_doc_no=None, default_effective_date=None)` whitelisted | đơn vị; loại giá; `file_url` của File đã tải lên | `{"job_id"}` | `has_permission("NC Benchmark Price", "create", throw=True)`; `has_permission("NC Benchmark Facility", "read", doc, throw=True)`; `gateway.ensure_enabled()` (FR-AI-015). `price_category` phải tồn tại. File: `frappe.get_doc("File", {"file_url": file_url})`, không có → lỗi "Không tìm thấy tệp"; `has_permission("File", "read", doc, throw=True)`; `library.extract.file_kind(file_name)` khác `"pdf"` → lỗi "Chỉ nhận tệp PDF". `default_effective_date` (nếu có) phải là ngày hợp lệ |
| `run_price_list_extraction(price_job, facility, price_category, file_url, source_doc_no, default_effective_date, user)` không whitelisted | | ghi trạng thái | Chạy dưới `user` (`frappe.set_user`), không ném lỗi ra ngoài (bắt mọi `Exception` → `failed`) |
| `get_price_list_extraction_status(job_id)` whitelisted | | `{"status": "queued"\|"running"\|"done"\|"failed"\|"unknown", "created", "duplicates", "skipped", "not_in_file", "log", "message"}` | Chỉ người khởi chạy (hoặc Administrator) đọc được, khác → `PermissionError` |

`run_price_list_extraction` theo thứ tự:

1. `job_set(running)`. Đọc File, `extract_pages(content, file_name, ocr=available_ocr())`; `ExtractionError` → `failed` với thông điệp của nó (không gọi AI, không ghi NC AI Log). `pdf_extract.check_page_count(pages)` → lỗi thì `failed`.
2. `prompts_install.ensure_extract_price_list_v2()`.
3. `sources = guard.price_list_pages(pages)`; `variables = {"facility_name": facility_name, "file_name": file_name}`.
4. `res = gateway.complete("EXTRACT_PRICE_LIST", "EXTRACT_PRICE_LIST", variables, sources, ref_doctype="NC Benchmark Facility", ref_name=facility, postprocess=post)`; `post(data)` gọi `pdf_extract.parse_rows(data, pages, default_date)`, giữ kết quả trong biến đóng, trả `(data, not_in_file)` để số dòng bị loại vì không thấy trong tệp vào `rejected_citations` của log.
5. `res.ok` sai → `failed` với `res.error` + "Có thể nhập tay hoặc nhập từ Excel." (FR-AI-010, UC-013 2c); không tạo dòng nào.
6. Mỗi dòng hợp lệ: `frappe.get_doc({"doctype": "NC Benchmark Price", facility, service_name_raw, price, price_category, effective_date, source_doc_no, source_file=file_url, source_url=pdf_extract.source_url(...), ai_log=res.log_name}).insert()` (quyền của `user`, không `ignore_permissions`) trong `savepoint` riêng. `frappe.ValidationError` có chữ "Trùng" → thêm vào `duplicates` (`{"service_name", "message"}`), rollback savepoint, tiếp dòng sau (FR-BM-007); lỗi khác → `skipped` với thông điệp lỗi.
7. `frappe.db.commit()`; `job_set(done, **summary, log=res.log_name)`.

Lỗi người dùng thấy (tiếng Việt): "Tính năng AI đang tắt" (gateway), "Chỉ nhận tệp PDF", "Không tìm thấy tệp", thông điệp `ExtractionError` của FEAT-020 (PDF mã hóa, không có lớp văn bản…), "Tệp có N trang, vượt 30 trang…", lỗi gateway + gợi ý nhập tay.

### 3.5 Giao diện (chi tiết ở `ui-design.md`)

- `normcore/public/js/benchmark_pdf_ai.js`, nạp bằng `normcore/hook_registry/FEAT-027.json` (`{"app_include_js": ["/assets/normcore/js/benchmark_pdf_ai.js"]}`), không sửa `hooks.py`.
- Không sửa ba tệp JS và `vi.d/FEAT-026.csv` của FEAT-026: test `test_feat_026_ui.py::test_khong_co_chu_ai` cấm chữ "AI" ở đó (ASM-027-10). Mọi chuỗi mới ở `normcore/translations/vi.d/FEAT-027.csv`.
- Không lối tắt Workspace mới.

### 3.6 Khác

Không DocType, không patch, không fixtures, không scheduler. Tệp PDF mẫu cho test: `normcore/nc_benchmark/doctype/nc_benchmark_price/test_files/bang_gia_4_dong.pdf` (có lớp văn bản, 2 trang, 4 dịch vụ có giá, 1 dòng tiêu đề, 1 dòng "Tổng cộng"); Dev sinh một lần bằng công cụ sẵn có và ghi lệnh sinh vào `implementation-log.md`.

## 4. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | AI bật; nhà cung cấp giả lập trả 4 dòng hợp lệ có tên nằm trong `bang_gia_4_dong.pdf`; NC Finance gọi `start_price_list_extraction` → trạng thái `done`, `created = 4`; đúng 4 NC Benchmark Price mới của đơn vị, mỗi dòng `status = "Đề xuất"`, `ai_log` = tên một NC AI Log có `purpose = "EXTRACT_PRICE_LIST"`, `status = "Thành công"`, `ref_doctype = "NC Benchmark Facility"`, `ref_name` = đơn vị; `verified_by` trống; `source_file` = tệp. Một dòng khớp được dịch vụ `S` qua `suggest_service` → `get_comparable_prices(S)["rows"]` không chứa dòng nào trong 4 dòng ("chưa tham gia so sánh") | TC-BM-05 | FR-BM-003, FR-BM-005, FR-AI-008 | `test_TC_BM_05_trich_bang_gia_pdf_de_xuat` (`api/test_benchmark_ai.py`) |
| 2 | Nguồn gửi đi (bắt được ở nhà cung cấp giả lập) chỉ gồm `[{"page", "text"}]` của tệp và `variables` chỉ có `facility_name`, `file_name`; `guard.price_list_pages` từ chối dict/bản ghi | — | FR-AI-011, NFR-SEC-005 | `test_FR_AI_011_chi_gui_chu_cua_tep` (site) + `test_FR_AI_011_guard_trang_bang_gia` (unit) |
| 3 | AI trả 6 phần tử: 3 hợp lệ, 1 thiếu giá, 1 tên không có trong tệp, 1 trùng dòng đã có → `created = 3`, `skipped` có "Giá không hợp lệ" và "Không thấy trong tệp", `duplicates` 1 dòng; `rejected_citations` của log = 1 | — | FR-BM-003, FR-BM-007 | `test_FR_BM_003_bo_dong_khong_hop_le_va_trung` |
| 4 | Dòng không có ngày, có `default_effective_date` → dùng ngày mặc định; không có cả hai → bỏ "Thiếu ngày hiệu lực" | — | FR-BM-003 | unit `test_FR_BM_003_parse_rows` |
| 5 | `parse_price`: `25000`, `"25.000"`, `"25,000 đ"`, `"1.250.000 VNĐ"` → đúng số; `"abc"`, `0`, `-5`, `True` → `None`. `parse_date`: `"2026-01-15"`, `"15/01/2026"`, `"1/2/2026"` đúng; `"31/02/2026"` → `None`. `locate`: theo gợi ý trang, không gợi ý thì trang đầu chứa tên, không có → `None`. `source_url` cắt khi dài | — | FR-BM-003 | unit `test_FR_BM_003_doc_gia_ngay_trang` (`tests/unit/test_benchmark_pdf_extract.py`) |
| 6 | Nhà cung cấp giả lập ném `ProviderTimeout` / `ProviderError`, hoặc trả JSON thiếu `rows` → `failed`, thông điệp có "nhập tay"; 0 dòng NC Benchmark Price mới; đúng 1 NC AI Log trạng thái "Quá hạn"/"Lỗi" | — | FR-AI-010, UC-013 2c | `test_FR_AI_010_ai_loi_khong_tao_dong` |
| 7 | AI tắt: `start_price_list_extraction` → `frappe.ValidationError` "Tính năng AI đang tắt", không NC AI Log mới; tạo NC Benchmark Price bằng tay và nhập Excel `nc_benchmark_price` vẫn được (phần giá tham chiếu của TC-AI-07, ASM-023-16). Tĩnh: nút trong `benchmark_pdf_ai.js` nằm trong nhánh `normcore.ai.enabled()` | — | FR-AI-015 | `test_FR_AI_015_tat_ai_gia_tham_chieu_thu_cong` + `test_feat_027_ui.py` |
| 8 | Tệp không phải PDF → "Chỉ nhận tệp PDF"; PDF không có lớp văn bản, không OCR → `failed` với thông điệp FEAT-020, không NC AI Log; > 30 trang → `failed` "vượt 30 trang" | — | FR-BM-003 | `test_FR_BM_003_tep_khong_hop_le` |
| 9 | Quyền: NC Clinician và NC Auditor gọi `start_price_list_extraction` → `frappe.PermissionError`, không NC AI Log mới; NC Consultant chạy được; người khác gọi `get_price_list_extraction_status(job_id)` của NC Finance → `PermissionError` | — | data-model mục 4, FR-ACC-007 | `test_quyen_feat_027` |
| 10 | Mẫu lệnh: lần chạy đầu tạo `EXTRACT_PRICE_LIST-v2` khi v1 còn mặc định; Admin đã có v2 tự sửa → không ghi đè; NC AI Log ghi `prompt_template` = bản đang dùng | — | FR-AI-009, FR-AI-014 | `test_FR_AI_014_mau_lenh_trich_bang_gia` |

`check_conventions.py` xanh; `build_rtm.py` không thêm vấn đề mới; test cũ (`test_feat_026_ui.py`, `api/test_benchmark.py`, test FEAT-023) không sửa và vẫn xanh.

## 5. Giả định và rủi ro

- ASM-027-01..12 ở `docs/decisions/assumptions/FEAT-027.md`.
- Rủi ro: bảng giá PDF dạng bảng, `pypdf` tách chữ có thể đứt tên qua dòng → kiểm "Không thấy trong tệp" so sau chuẩn hóa (gộp khoảng trắng) nên phần lớn vẫn khớp; nếu loại nhầm nhiều, đặt `REQUIRE_NAME_IN_SOURCE = False` (dòng vẫn "Đề xuất", người dùng rà với trang gốc).
- Rủi ro: AI đọc sai giá → mọi dòng là "Đề xuất", có `source_url` mở đúng trang để đối chiếu; không vào so sánh trước khi xác nhận (FR-BM-005, FR-AI-008).
- Rủi ro: tệp lớn tốn token → giới hạn 30 trang và hạn mức tháng của gateway (FR-AI-013).
- Attach `source_file` trỏ cùng một `file_url` ở nhiều dòng: Frappe tạo bản ghi File gắn từng dòng nhưng không chép nội dung; chấp nhận.
