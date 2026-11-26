# FEAT-022 — Ánh xạ hướng dẫn với dịch vụ — Thiết kế kỹ thuật

Issue NORM-54. Nguồn: `srs.md` FR-SVC-005, FR-SVC-006, FR-SVC-007 (và FR-AI-001, FR-AI-011 để biết nguồn gửi AI sẽ được FEAT-024 dùng thế nào); `use-cases.md` UC-003 bước 3–5, 4a, 5a; `data-model.md` mục 3.2 (NC Legal Section `service_mappings`, NC Section Service Map) và mục 4 dòng "Văn bản, mục, ánh xạ"; `ux-foundations.md` SCR-DSK-004; TC-SVC-02. Phụ thuộc FEAT-020 (DONE), FEAT-005 (DONE). Giả định: `docs/decisions/assumptions/FEAT-022.md` (ASM-022-01..).

Dùng lại, **không tạo lại**: NC Legal Document, NC Legal Section, `api/library.py`, `library/search.py` (FEAT-020); NC Technical Service (FEAT-005); `ai/gateway.py`, `ai/guard.py`, provider giả lập (FEAT-023).

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-SVC-005 (Should) | Sau khi lập chỉ mục xong một văn bản có `is_procedure_guideline` = 1, tự đề xuất ánh xạ từng mục quy trình với dịch vụ kỹ thuật: khớp mã → độ tin cậy 100%; khớp tên → độ tin cậy ≤ 95% (mục 3). Ghi dòng NC Section Service Map trạng thái "Đề xuất". Có nút "Đề xuất lại" cho văn bản đã lập chỉ mục trước FEAT này. |
| FR-SVC-006 (Must) | Xác nhận (từng dòng, nhiều dòng đã chọn, hoặc mọi dòng 100%), sửa dịch vụ của một dòng, thêm ánh xạ tay (UC-003 5a), bỏ một ánh xạ (4a). Dòng được xác nhận/sửa → "Đã xác nhận", `confirmed_by` = người thao tác, `confirmed_on` = thời điểm máy chủ. Quy tắc này cài ở `validate` của NC Legal Section nên cũng đúng khi sửa bảng con trực tiếp trên form. |
| FR-SVC-007 (Must) | Hàm máy chủ `get_draft_sources(technical_service)` — **cửa duy nhất** dựng danh sách mục nguồn gửi AI khi soạn dự thảo cho một dịch vụ: chỉ mục có ánh xạ "Đã xác nhận" với dịch vụ đó (và còn hiệu lực, ASM-022-07), qua `guard.build_source`. FEAT-024 gọi hàm này, không tự truy vấn. TC-SVC-02 kiểm bằng gateway + provider giả lập ghi lại nguồn. |

Không làm: màn hình/nút "Soạn dự thảo", NC Clinical Procedure AI, trích dẫn (FEAT-024); rà soát ánh xạ khi văn bản bị thay thế (FEAT-021/025); đề xuất bằng AI qua mẫu lệnh `MAP_SECTION_SERVICE` (ASM-022-03).

## 2. DocType

### 2.1 Mới — NC Section Service Map (bảng con, module NC Library)
Tệp `normcore/nc_library/doctype/nc_section_service_map/`. `istable` = 1, `editable_grid` = 1, `permissions` = [] (bảng con theo quyền DocType cha — data-model mục 4 ghi chú [1.1]). Không `track_changes` riêng: thay đổi bảng con hiện trong Version của NC Legal Section (cha có `track_changes` = 1).

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| technical_service | Dịch vụ kỹ thuật | Link NC Technical Service | Có | `in_list_view`; tên dịch vụ hiển thị qua liên kết, API trả `service_name` bằng JOIN — không thêm cột ngoài data-model (ASM-022-09) |
| mapping_status | Trạng thái | Select `Đề xuất` / `Đã xác nhận` | Có | mặc định `Đề xuất`, `in_list_view` |
| confidence | Độ tin cậy (%) | Percent | | `read_only`, `in_list_view`; trống với ánh xạ thêm tay |
| confirmed_by | Người xác nhận | Link User | | `read_only` |
| confirmed_on | Thời điểm xác nhận | Datetime | | `read_only` |

### 2.2 Mở rộng — NC Legal Section
Thêm sau `validity_status` (trước Section Break "Đối chiếu"): Section Break `mapping_section` (nhãn "Ánh xạ dịch vụ") + `service_mappings` (Table NC Section Service Map, nhãn "Ánh xạ dịch vụ"). Không đổi trường cũ. Quyền giữ nguyên (`R R R R R W R R W R`).

### 2.3 Mở rộng — NC Legal Document (chỉ bố cục)
Thêm Section Break `mapping_doc_section` (nhãn "Ánh xạ hướng dẫn", `depends_on: eval:doc.is_procedure_guideline`) + HTML `mapping_html` sau `sections_html`. Trường HTML không có cột CSDL, cùng tiền lệ ASM-020-02 — không AMD.

### 2.4 Kiểm tra khi lưu NC Legal Section (`validate` → `library/mapping.stamp_rows`)
Với mỗi dòng `service_mappings`, so với bản đã lưu (`doc.get_doc_before_save()`, theo `name` dòng):
1. Hai dòng cùng `technical_service` trong một mục → `frappe.ValidationError` "Dịch vụ {0} đã được ánh xạ với mục này" (ASM-022-05).
2. Dòng "Đã xác nhận" mà (là dòng mới) hoặc (trước đó "Đề xuất") hoặc (đổi `technical_service`) → `confirmed_by` = `frappe.session.user`, `confirmed_on` = `now_datetime()`. Dòng "Đã xác nhận" không đổi gì → giữ nguyên người/thời điểm cũ.
3. Dòng "Đề xuất" → xóa `confirmed_by`, `confirmed_on`.
4. Dòng "Đã xác nhận" có `confidence` = 100 vẫn giữ `confidence` (thông tin gốc của đề xuất).

Không có DI mới trong `data-model.md` cho bảng này; quy tắc 1 ghi ASM-022-05.

### 2.5 Migration
Bảng mới và trường mới tạo bởi `bench migrate`; không cần patch dữ liệu (NC Legal Section chưa có cột nào bị đổi). Văn bản hướng dẫn đã lập chỉ mục trước FEAT này: người dùng bấm "Đề xuất lại" (ASM-022-08); không tự chạy hàng loạt khi migrate.

## 3. Logic thuần — `normcore/library/mapping.py` (không import `frappe`)

Hằng số đầu tệp (cấu hình bằng mã, có test): `CODE_CONFIDENCE = 100`, `NAME_EXACT_CONFIDENCE = 95`, `MIN_CONFIDENCE = 50`, `MAX_SUGGESTIONS = 3`, `CONFIRMED = "Đã xác nhận"`, `SUGGESTED = "Đề xuất"`.

| Hàm | Vào → Ra | Quy tắc |
| :-- | :-- | :-- |
| `normalize_title(s)` | str → str | Bỏ số thứ tự đầu dòng (`^\s*[0-9IVXLCivxlc]+[.)]\s*`), `search.normalize_text` (NFC + casefold), thay dấu câu bằng khoảng trắng, gộp khoảng trắng |
| `title_tokens(s)` | str → frozenset[str] | Tách `normalize_title(s)` theo khoảng trắng |
| `code_in_heading(heading, code)` | → bool | Mã dịch vụ xuất hiện nguyên vẹn trong tiêu đề, không phân biệt hoa thường, ranh giới là đầu/cuối chuỗi hoặc ký tự không phải chữ/số/dấu chấm (regex `(?<![\w.])<re.escape(code)>(?![\w.])`, `re.I`). Mã rỗng → False |
| `name_confidence(heading, service_name)` | → int (0..95) | `normalize_title` hai bên bằng nhau → 95. Khác: Dice trên token `2·|A∩B| / (|A|+|B|)`, `round(95 × dice)` (làm tròn half-up bằng `Decimal`), rỗng → 0 |
| `suggest_for_section(heading, services, index=None)` | `services`: list `(service_code, service_name)` → list `(service_code, confidence)` | Khớp mã → 100 (bỏ qua khớp tên của dịch vụ đó). Khớp tên ≥ `MIN_CONFIDENCE`. Sắp giảm theo độ tin cậy rồi tăng theo mã; lấy tối đa `MAX_SUGGESTIONS`. `index` (từ `build_token_index`) để chỉ tính Dice cho dịch vụ có chung ít nhất một token |
| `build_token_index(services)` | → dict token → set mã | Chỉ mục ngược cho hiệu năng (≥ 5.000 dịch vụ × 300 mục) |
| `merge_suggestions(existing_rows, suggestions)` | `existing_rows`: list dict có `technical_service`, `mapping_status` → list dict dòng mới | Giữ mọi dòng "Đã xác nhận" nguyên vẹn; bỏ mọi dòng "Đề xuất" cũ; thêm đề xuất mới có mã chưa có trong dòng đã xác nhận, `mapping_status` = "Đề xuất", `confidence` = độ tin cậy (ASM-022-04) |
| `stamp_rows(rows, before_rows, user, now)` | → None (sửa `rows`) hoặc `MappingError` | Quy tắc mục 2.4 |
| `is_draft_source(row)` | → bool | `row.mapping_status == CONFIRMED` (FR-SVC-007) |
| `is_mappable_section(section_no)` | → bool | False với mục "0" (Phần mở đầu, ASM-020-04); True với mục khác |

Ánh xạ tới BR/golden: không có phép tính tiền; không dùng `docs/golden/`.

## 4. API và tác vụ — `normcore/api/library.py` (mở rộng)

Mọi hàm whitelisted kiểm quyền tường minh. Đọc = `frappe.has_permission("NC Legal Document", "read", doc)`; ghi = `frappe.has_permission("NC Legal Section", "write", doc=section)` (NC Document Controller, NC Admin). Thiếu quyền → `frappe.PermissionError` với thông báo tiếng Việt. Ghi bằng `section.save()` (không `ignore_permissions`) để `validate` 2.4 chạy và Version ghi đúng người.

| Hàm | Tham số | Kết quả | Lỗi |
| :-- | :-- | :-- | :-- |
| `refresh_suggestions(legal_document)` (không whitelisted) | tên văn bản | `{"sections": n, "suggested": m}` | Bỏ qua (trả 0) nếu văn bản không phải hướng dẫn QTKT. Lấy dịch vụ `is_active` = 1; với mỗi mục `is_mappable_section`, `merge_suggestions` rồi lưu mục (chỉ khi bảng con đổi). Chạy dưới quyền hệ thống khi gọi từ tác vụ nền |
| `index_document` (đã có) | | | Sau khi "Đã lập", gọi `refresh_suggestions(name)` trong cùng savepoint; lỗi đề xuất **không** làm văn bản thành "Lỗi": ghi `frappe.log_error` và để trống đề xuất (ASM-022-10) |
| `suggest_mappings(legal_document)` | | như `refresh_suggestions` | quyền ghi; văn bản không phải hướng dẫn QTKT → "Văn bản không phải hướng dẫn quy trình kỹ thuật"; `index_status` ≠ "Đã lập" → "Văn bản chưa lập chỉ mục xong" |
| `get_mappings(legal_document, unconfirmed_only=0, start=0, page_length=100)` | | `{"total", "pending_exact", "rows": [{"section", "section_no", "heading", "validity_status", "mappings": [{"row", "technical_service", "service_name", "mapping_status", "confidence", "confirmed_by", "confirmed_on"}]}]}` | quyền đọc. Mục sắp theo `search.natural_key`; bỏ mục "0". `unconfirmed_only` = 1: mục có ít nhất một dòng "Đề xuất" hoặc chưa có dòng nào (ASM-022-06). `pending_exact` = số dòng "Đề xuất" có `confidence` = 100 trong cả văn bản. `page_length` ≤ 500 |
| `confirm_mappings(legal_document, rows)` | `rows`: JSON list tên dòng con | `{"confirmed": n}` | quyền ghi; dòng không thuộc mục của văn bản → "Ánh xạ không thuộc văn bản này"; dòng đã xác nhận bỏ qua (không đóng dấu lại) |
| `confirm_exact(legal_document)` | | `{"confirmed": n}` | quyền ghi; xác nhận mọi dòng "Đề xuất" có `confidence` = 100 |
| `save_mapping(section, technical_service, row=None)` | | `{"row", "mapping_status": "Đã xác nhận"}` | quyền ghi. Có `row`: đổi dịch vụ của dòng đó (sửa) và xác nhận. Không có `row`: thêm dòng mới "Đã xác nhận", `confidence` trống (UC-003 5a). Dịch vụ không tồn tại → `frappe.DoesNotExistError`; trùng dịch vụ trong mục → lỗi 2.4.1 |
| `remove_mapping(row)` | tên dòng con | `{"removed": 1}` | quyền ghi trên mục cha; xóa dòng (bỏ đề xuất sai hoặc gỡ ánh xạ, UC-003 4a) |
| `get_draft_sources(technical_service, valid_only=True)` (không whitelisted, cho FEAT-024) | mã dịch vụ | list dict `guard.build_source("NC Legal Section", {name, section_no, heading, plain_text})`, sắp theo số hiệu văn bản rồi `natural_key(section_no)` | Truy vấn: JOIN `tabNC Section Service Map` m ON m.parent = s.name AND m.parenttype = 'NC Legal Section' AND m.parentfield = 'service_mappings' WHERE m.technical_service = %s AND m.mapping_status = 'Đã xác nhận' (+ `s.validity_status = 'Còn hiệu lực'` khi `valid_only`). Không trùng mục |

`_search_service` của FEAT-020 (`api/library.py`) đã truy vấn `tabNC Section Service Map` với `mapping_status = 'Đã xác nhận'` khi bảng tồn tại; tên bảng, `parenttype`, `technical_service` (= `service_code`, vì NC Technical Service đặt tên theo `service_code`) và giá trị "Đã xác nhận" của thiết kế này khớp với truy vấn đó — **không sửa** `_search_service`; chỉ thêm test (tiêu chí #9).

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test (đề xuất tên) |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Mục M có dòng "Đề xuất" với dịch vụ X; `get_draft_sources(X)` rồi `gateway.complete("Soạn dự thảo", "DRAFT_PROCEDURE", …, sources)` với provider giả lập ghi lại `sources`: M **không** có trong nguồn provider nhận và không có trong `source_sections` của NC AI Log. Sau `confirm_mappings` dòng đó: M có ở cả hai | TC-SVC-02 | FR-SVC-006, FR-SVC-007 | `api/test_library_mapping.py::test_TC_SVC_02_chi_muc_da_xac_nhan_vao_nguon_ai` |
| 2 | Lập chỉ mục văn bản hướng dẫn QTKT có mục "1. <MÃ X> …" và mục "2. <TÊN Y>": mục 1 có đề xuất X 100%, mục 2 có Y 95%, cả hai "Đề xuất"; văn bản không phải hướng dẫn QTKT: không có dòng nào; mục "0" không có dòng | — | FR-SVC-005 | `test_FR_SVC_005_de_xuat_sau_lap_chi_muc` |
| 3 | Hàm thuần: khớp mã = 100 và bỏ khớp tên cùng mã; tên trùng sau chuẩn hóa = 95; Dice < 50 bị bỏ; tối đa 3 đề xuất, sắp đúng; mã "01.01" không khớp "01.011"; `merge_suggestions` giữ dòng đã xác nhận, thay dòng đề xuất; `stamp_rows` đủ 4 nhánh mục 2.4 | — | FR-SVC-005, FR-SVC-006 | `tests/unit/test_library_mapping.py` (độ phủ `library/mapping.py` ≥ 90%) |
| 4 | `confirm_mappings`, `confirm_exact`, `save_mapping` (sửa và thêm): dòng thành "Đã xác nhận", `confirmed_by` = người gọi, `confirmed_on` có giá trị; dòng đã xác nhận không bị đóng dấu lại; có Version trên mục | — | FR-SVC-006 | `test_FR_SVC_006_xac_nhan_luu_nguoi_va_thoi_diem` |
| 5 | Sửa trực tiếp bảng con trên NC Legal Section (đặt "Đã xác nhận" bằng `doc.save()`): `confirmed_by/on` được đóng dấu; đặt lại "Đề xuất" thì xóa; hai dòng cùng dịch vụ → lỗi | — | FR-SVC-006 | `nc_legal_section/test_nc_section_service_map.py::test_FR_SVC_006_validate_dong_dau` |
| 6 | Quyền: NC Clinician và NC Auditor gọi `confirm_mappings`, `save_mapping`, `remove_mapping`, `suggest_mappings` → `PermissionError`; NC Auditor gọi `get_mappings` được; người dùng không vai trò NC gọi `get_mappings` → `PermissionError`; NC Document Controller làm được mọi thao tác | — | FR-SVC-006, FR-ACC-007 | `test_FR_SVC_006_quyen_anh_xa` |
| 7 | `get_mappings(unconfirmed_only=1)` chỉ trả mục có dòng "Đề xuất" hoặc chưa có dòng; `pending_exact` đúng | — | FR-SVC-005 (SCR-DSK-004) | `test_SCR_DSK_004_loc_chua_xac_nhan` |
| 8 | `get_draft_sources(valid_only=True)` bỏ mục "Hết hiệu lực" dù đã xác nhận; mỗi phần tử chỉ có khóa trong `guard.ALLOWED_SOURCES["NC Legal Section"]` | — | FR-SVC-007, FR-AI-011 | `test_FR_SVC_007_nguon_chi_truong_cho_phep` |
| 9 | `search_sections(mode="service")` trả mục có ánh xạ "Đã xác nhận" với `match` = "Ánh xạ dịch vụ"; ánh xạ "Đề xuất" không làm mục xuất hiện qua nhánh này; `test_TC_LIB_08_*` cũ vẫn đạt | TC-LIB-08 (hồi quy) | FR-LIB-010 | `test_FR_LIB_010_tim_theo_anh_xa_da_xac_nhan` |
| 10 | Lập lại chỉ mục: dòng "Đã xác nhận" của mục còn giữ nguyên; dòng "Đề xuất" được tính lại | — | FR-SVC-005, FR-SVC-006 | `test_FR_SVC_005_lap_lai_giu_da_xac_nhan` |
| 11 | `check_conventions.py` thoát 0 với DocType mới; nhãn tiếng Việt; chuỗi JS có trong `vi.csv` | — | NFR-MNT-003 | `tests/unit/test_library_ui_conventions.py` (mở rộng) |

Test tích hợp đặt cạnh mã: `normcore/api/test_library_mapping.py`, `normcore/nc_library/doctype/nc_section_service_map/test_nc_section_service_map.py` (hoặc cạnh NC Legal Section). Không gọi nhà cung cấp AI thật: `frappe.flags.in_test` buộc provider giả lập; TC-SVC-02 truyền `provider=` là một lớp ghi lại tham số `sources` (cùng giao diện `MockProvider.complete`).

## 6. Giả định và rủi ro

Giả định ASM-022-01..10 ở `docs/decisions/assumptions/FEAT-022.md`.

Rủi ro:
- Tiêu đề mục trong hướng dẫn QTKT của Bộ hiếm khi có mã dịch vụ; phần lớn đề xuất sẽ là khớp tên (≤ 95%), nên "Xác nhận các dòng 100%" có thể ít dòng. Chất lượng khớp tên chưa thử trên văn bản thật (TBD-09) — ghi As-Built.
- Danh mục lớn (≥ 5.000 dịch vụ, văn bản ≥ 300 mục): chỉ mục ngược token để không so mọi cặp; test hiệu năng đơn vị với 5.000 dịch vụ giả × 300 mục < 5 giây.
- Lập lại chỉ mục đổi tiêu đề mục nhưng giữ `section_no`: ánh xạ đã xác nhận giữ nguyên dù nội dung đổi; rà soát thuộc FEAT-021/025.
- `get_draft_sources` là hợp đồng cho FEAT-024; đổi chữ ký phải cập nhật As-Built.
