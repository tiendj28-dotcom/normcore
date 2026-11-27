# FEAT-038 — AI đề xuất định mức từ tài liệu của hãng — Thiết kế kỹ thuật

- Issue: NORM-79. Bản phát hành R2. Nhánh `feat/FEAT-038-ai-de-xuat-dinh-muc-hang`.
- FR: FR-LIB-013, FR-AI-016, FR-AI-017, FR-AI-018 (kèm FR-AI-005, FR-AI-008, FR-AI-011, NFR-SEC-005). UC-025. Màn hình SCR-DSK-003 (phần tài liệu của hãng), SCR-DSK-014, SCR-DSK-033.
- TC: TC-CLS-41, TC-CLS-42, TC-CLS-43.
- Phụ thuộc: FEAT-020 (thư viện, tách mục), FEAT-023 (gateway, guard, mẫu lệnh, nhật ký), FEAT-034 (bộ định mức theo hệ thống xét nghiệm) — đều có `DONE` trên `origin/develop`. Dùng lại `ai/citation.py` (FEAT-024) và cách chạy nền, cài lười mẫu lệnh v2 của FEAT-025.
- Sửa thiết kế: **AMD-038-01** (DocType NC AI Norm Suggestion). Giả định: ASM-038-01..14 (`docs/decisions/assumptions/FEAT-038.md`).
- ADR-007 đã có sửa đổi [1.1] cho tài liệu của hãng (`architecture.md` dòng 426): không cần AMD kiến trúc.

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-LIB-013 | Đủ | Loại "Tài liệu của hãng" ở NC Legal Document; bảng con `related_resources` (NC Document Resource Link) bắt buộc với loại này; tách mục dùng nguyên luồng FEAT-020 (FR-LIB-003) |
| FR-AI-016 | Đủ | Nút "AI đề xuất định mức" trên kế hoạch chất lượng (SCR-DSK-033) và bộ định mức có hệ thống xét nghiệm (SCR-DSK-014, form NC Norm Set). Gửi mục tài liệu của hãng đã gắn với hóa chất, thiết bị của hệ thống + quy trình đã ban hành; tạo bốn loại đề xuất |
| FR-AI-017 | Đủ | Mỗi đề xuất có trích dẫn đã kiểm nguyên văn hoặc "Chưa có căn cứ"; trạng thái "Đề xuất" cho đến khi người có quyền chấp nhận; không DocType tính giá nào đọc đề xuất |
| FR-AI-018 | Đủ | Mã ngoài danh mục → `not_in_catalog = 1`, giữ `resource_text`, không tạo NC Item/NC Equipment; người dùng liên kết thủ công rồi mới chấp nhận được |

Ngoài phạm vi: tính chi phí theo đề xuất (chỉ số liệu đã chấp nhận mới vào phép tính, FEAT-036 đã có); sửa `normcore/api/norm.py`, `normcore/public/js/norm_grid/` (cấm bởi `test_luoi_va_api_norm_khong_doi`, DEF-025-01, AMD-025-02).

## 2. DocType

### 2.1 NC Legal Document (FEAT-020) — mở rộng

- `doc_type` thêm lựa chọn cuối `Tài liệu của hãng`.
- Thêm `related_resources` (Table NC Document Resource Link, nhãn "Mặt hàng, thiết bị liên quan"), `depends_on: eval:doc.doc_type=='Tài liệu của hãng'`, đặt sau `supersessions`.
- Controller `validate` thêm `check_related_resources()` gọi hàm thuần `library/manufacturer.py::resource_link_errors(doc_type, rows)`:
  - loại "Tài liệu của hãng" mà bảng trống → "Tài liệu của hãng phải gắn ít nhất một mặt hàng hoặc thiết bị".
  - `linked_doctype` ngoài {NC Item, NC Equipment} → "Chỉ gắn được mặt hàng hoặc thiết bị".
  - trùng cặp (`linked_doctype`, `linked_name`) → "Dòng {0} trùng với dòng {1}".
  - loại khác mà bảng có dòng: giữ, không báo lỗi (ASM-038-02).
- Không đổi luồng lập chỉ mục, hiệu lực, số hiệu (FR-LIB-002: số hiệu = mã tài liệu của hãng kèm phiên bản, chỉ là nhãn trường; ASM-038-01).
- Không cần patch: thêm lựa chọn và bảng con mới; bản ghi cũ không đổi.

### 2.2 NC Document Resource Link — mới (bảng con, module NC Library)

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| linked_doctype | Loại danh mục | Link DocType | Có | Bộ lọc giao diện: NC Item, NC Equipment |
| linked_name | Mặt hàng, thiết bị | Dynamic Link (`linked_doctype`) | Có | |

`istable = 1`, quyền theo NC Legal Document (dòng "Văn bản, mục, ánh xạ").

### 2.3 NC AI Norm Suggestion — mới (AMD-038-01, module NC Costing)

Trường, ràng buộc như AMD-038-01. Tóm tắt cài đặt:
- Naming `AINS-.#####`; `track_changes = 1`; `title_field = resource_text`; danh sách hiện `test_system`, `suggestion_type`, `resource_text`, `value`, `uom`, `relation`, `status`.
- Mọi trường chỉ đọc trên form trừ không trường nào (người dùng đổi qua API mục 3.3); `in_create = 1` (không tạo tay từ giao diện).
- `department` fetch từ `test_system.department`.
- Controller `validate`: (1) "Theo hướng dẫn" ⇒ `legal_section`, `quote` BB; (2) `quote` có giá trị ⇒ `citation.quote_in_text(quote, plain_text của legal_section)` (cùng DI-08); (3) `resource` có giá trị ⇒ `not_in_catalog = 0`; (4) `status` chỉ đi "Đề xuất" → "Đã chấp nhận" | "Đã bỏ", không quay lại (ASM-038-09).
- Quyền (perm_matrix `nc_ai_norm_suggestion.json`): dòng "Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm", codes `W W - R R - R R R R`, `delete: []`. Phạm vi khoa: `core/scope_rules/nc_ai_norm_suggestion.json` với `department_field: "department"`, `public_read: {}`, không `via`.

### 2.4 NC Prompt Template — mẫu `SUGGEST_CLS_NORM-v2`

Mã `SUGGEST_CLS_NORM` đã có (v1 mặc định của FEAT-023). Thêm `ensure_suggest_cls_norm_v2()` trong `ai/prompts_install.py` qua `_ensure_v2` (cài lười ở lần gọi đầu, như ASM-025-11; không patch, không `after_install`). `output_schema` giữ `{"type": "object"}`; cấu trúc kiểm ở hàm thuần (3.1). Lệnh hệ thống (tóm ý, Dev viết nguyên văn tiếng Việt):
- Chỉ dựa trên các mục nguồn; mỗi đề xuất có `citations: [{"section": <name của mục>, "quote": <nguyên văn>}]`, không có căn cứ thì `citations` rỗng.
- `suggestion_type` ∈ `REAGENT_PER_TEST`, `CALIBRATION_FREQ`, `IQC_FREQ`, `OPEN_STABILITY`; `item_code` chỉ chọn trong `items`/`equipment` đã gửi, không có thì để trống và ghi `item_text`; `value` là số; `uom`.
- Đơn vị của `value`: lượng mỗi test theo `norm_uom` của mặt hàng; chuẩn máy = số lần mỗi năm; nội kiểm = số lần chạy mỗi ngày; hạn dùng sau mở = số ngày (ASM-038-05).
- Đầu ra `{"suggestions": [{"suggestion_type", "item_code", "item_text", "value", "uom", "citations"}]}`.

Lệnh người dùng: `Hệ thống: {{ variables.service | tojson }}`, `Quy trình: {{ variables.procedure | tojson }}`, `Mặt hàng: {{ variables.items | tojson }}`, `Thiết bị: {{ variables.equipment | tojson }}`, `Các mục nguồn: {{ sources | tojson }}`.

### 2.5 Không đổi

NC Norm Set, NC Norm Line, NC QC Plan, NC QC IQC Line, NC QC Calibration Line, NC Item, NC Test System, NC AI Log (đã có `SUGGEST_CLS_NORM` trong `purpose`): không thêm trường. Chấp nhận đề xuất ghi vào chúng qua controller sẵn có.

## 3. Thành phần

### 3.1 `normcore/norm/ai_cls_norm.py` — thuần, không import `frappe`

| Hàm | Việc | FR / ASM |
| :-- | :-- | :-- |
| `TYPE_LABELS` | `{"REAGENT_PER_TEST": "Lượng hóa chất mỗi test", "CALIBRATION_FREQ": "Tần suất chuẩn máy", "IQC_FREQ": "Tần suất nội kiểm", "OPEN_STABILITY": "Hạn dùng sau mở"}` | FR-AI-016 |
| `system_resources(main_equipment, norm_lines, iqc_lines, calibration_lines)` | Tập khóa (`doctype`, `name`) của hệ thống: thiết bị chính; `resource` của dòng định mức có `resource_doctype` NC Item/NC Equipment; `qc_material`; `calibrator` | FR-AI-016, ASM-038-03 |
| `docs_in_scope(docs, resource_keys)` | Lọc tài liệu: `doc_type == "Tài liệu của hãng"`, `validity_status == "Còn hiệu lực"`, `index_status == "Đã lập"`, có ít nhất một dòng `related_resources` trong `resource_keys`. Trả danh sách tên, theo thứ tự tên | ADR-007 [1.1], ASM-038-04 |
| `request_variables(service, procedure, items, equipment)` | Dựng `variables` từ các dict **đã qua `guard.build_source`** | FR-AI-011 |
| `parse_suggestions(data, sources, catalog)` | Kiểm cấu trúc; bỏ đề xuất sai loại hoặc `value` không phải số > 0 (đếm vào `invalid`). Với mỗi đề xuất: `citation.check_citations(citations, sources)`; còn ≥ 1 trích dẫn → `relation = "Theo hướng dẫn"`, lấy trích dẫn đầu (`legal_section`, `quote`); không còn → `"Chưa có căn cứ"`, hai trường trống. `item_code` có trong `catalog` (dict mã → doctype) → `resource_doctype`, `resource`; không có → `not_in_catalog = 1`, `resource_text = item_text or item_code`. Trả `(rows, rejected)` với `rejected` = số trích dẫn bị loại + số đề xuất sai cấu trúc | FR-AI-005, FR-AI-017, FR-AI-018, ASM-038-06 |
| `plan_accept(suggestion, norm_lines, iqc_lines, calibration_lines)` | Trả hành động thuần: `{"target": "norm_line", "line_id"|None, ...}`, `{"target": "iqc", "row"}`, `{"target": "calibration", "row"}`, `{"target": "item"}` hoặc `{"error": <chuỗi>}` theo bảng 3.4 | FR-AI-008, ASM-038-08 |

### 3.2 Guard — `ai/guard.py`

- Thêm hằng `MANUFACTURER_DOC_TYPE = "Tài liệu của hãng"` và hàm `manufacturer_sections(sections, doc_names_in_scope)`: chỉ giữ mục có `legal_document` thuộc `doc_names_in_scope`, rồi `build_source("NC Legal Section", s)` cho từng mục. Mục của tài liệu khác (kể cả tài liệu của hãng không gắn với hệ thống) không bao giờ vào `sources`.
- `ALLOWED_SOURCES` không đổi (NC Legal Section, NC Clinical Procedure, NC Item `item_code/item_name/uom`, NC Equipment `equipment_code/equipment_name`, NC Technical Service đã có). Không thêm NC Test System, NC QC Plan, NC Norm Set (giữ trong `FORBIDDEN_DOCTYPES`).
- NC Item gửi thêm `norm_uom`? **Không** (không thuộc danh sách cho phép; ASM-038-05 dùng `uom`).

### 3.3 API — `normcore/api/cls_norm_ai.py` (mới)

Không sửa `api/norm.py`. Mẫu chạy nền như `api/norm_link.py` (cache `normcore:cls_norm_ai:{job}`, TTL 3600, realtime `normcore_cls_norm_ai`, hàng đợi `long`, `now=frappe.flags.in_test`, `enqueue_after_commit=True`).

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `start_cls_norm_suggestion` | `test_system` | `{"job_id"}` hoặc `{"job_id": None, "message": "Chưa có tài liệu của hãng nào gắn với hóa chất, thiết bị của hệ thống này"}` | `frappe.has_permission("NC Test System", "write", doc, throw=True)` (vai trò soạn + phạm vi khoa) và `frappe.has_permission("NC AI Norm Suggestion", "create", throw=True)`; `gateway.ensure_enabled()`; hệ thống "Ngừng dùng" → `ValidationError` "Hệ thống xét nghiệm đã ngừng dùng". Kiểm có tài liệu trong phạm vi trước khi xếp hàng |
| `run_cls_norm_suggestion` (nền, không whitelist) | `job`, `test_system`, `user` | ghi cache | Xem 3.5 |
| `get_cls_norm_suggestion_status` | `job_id` | trạng thái cache | chỉ người tạo đọc (như FEAT-025) |
| `list_cls_norm_suggestions` | `test_system`, `status="Đề xuất"` | `{"rows": [...], "can_edit", "ai_enabled", "pending"}`; mỗi dòng: `name`, `suggestion_type` (nhãn), `resource_doctype`, `resource`, nhãn danh mục, `resource_text`, `not_in_catalog`, `value`, `uom`, `relation`, `legal_section`, số hiệu + tên tài liệu, `section_no`, `quote`, `status`, `label` = "Đề xuất" khi chờ, `can_accept` (theo 3.4) | `frappe.has_permission("NC Test System", "read", doc, throw=True)` |
| `accept_cls_norm_suggestion` | `name` | `{"status": "Đã chấp nhận", "applied_ref", "norm_set"}` | Trạng thái phải "Đề xuất" (không thì `ValidationError` "Đề xuất đã được xử lý"); `not_in_catalog`/`resource` trống → `ValidationError` "Liên kết mặt hàng hoặc thiết bị trong danh mục trước khi chấp nhận" (FR-AI-018); quyền ghi **bản ghi đích** (3.4) |
| `reject_cls_norm_suggestion` | `name` | `{"status": "Đã bỏ"}` | quyền `write` trên đề xuất (phạm vi khoa) |
| `link_cls_norm_suggestion` | `name`, `resource_doctype`, `resource` | dòng đã cập nhật | quyền `write` trên đề xuất; chỉ khi "Đề xuất"; `resource_doctype` ∈ {NC Item, NC Equipment} và bản ghi tồn tại; đặt `not_in_catalog = 0`, giữ `resource_text` (FR-AI-018 liên kết thủ công) |

Ghi trạng thái đề xuất trong API dùng `doc.save()` của người dùng (không `ignore_permissions`), trừ trường hợp chấp nhận "Hạn dùng sau mở" bởi người chỉ có quyền đọc đề xuất (Finance, Resource Mgr, Admin): khi đó quyền đã kiểm tường minh trên NC Item, ghi trạng thái đề xuất bằng `ignore_permissions=True` và ghi `processed_by` (ASM-038-07).

### 3.4 Chấp nhận — áp vào bản ghi đích (`plan_accept` + API)

| Loại | Bản ghi đích | Áp | Không áp được |
| :-- | :-- | :-- | :-- |
| Lượng hóa chất mỗi test | Bộ định mức "Nháp" có `test_system` này, `version_no` lớn nhất; quyền `write` trên bộ | `resource` là NC Item: dòng có `resource_doctype = NC Item`, `resource` trùng, `cost_level = RESULT`, `is_excluded = 0` → đặt `hospital_qty = value`, `basis = "Ước tính"`, `basis_ref = "<số hiệu> mục <section_no>"` (hoặc "AI — Chưa có căn cứ"), xóa `confirmed_by/on` (đổi lượng phải xác nhận lại). Không có dòng → thêm dòng `service_level = 1`, `component = DRUG`, `resource_doctype = NC Item`, `cost_level = RESULT`, `uom = suggestion.uom or item.uom`, `hospital_qty = value`, cùng `basis`, `basis_ref` (line_id cấp từ `next_line_seq` qua controller) | Không có bộ Nháp → "Chưa có bộ định mức Nháp cho hệ thống {0}. Tạo phiên bản mới rồi chấp nhận lại"; `resource` là NC Equipment → "Lượng mỗi test chỉ áp cho hóa chất"; có > 1 dòng khớp → "Có {0} dòng cùng hóa chất; sửa trực tiếp trên lưới" |
| Tần suất chuẩn máy | NC QC Plan của hệ thống; quyền `write` | dòng `calibration_lines` có `calibrator == resource` → `calibrations_per_year = value` | chưa có kế hoạch / chưa có dòng chất chuẩn đó → "Kế hoạch chất lượng chưa có dòng chuẩn máy cho {0}; thêm dòng rồi chấp nhận lại" |
| Tần suất nội kiểm | NC QC Plan; quyền `write` | dòng `iqc_lines` có `qc_material == resource` → `runs_per_day = value` | tương tự, "… dòng nội kiểm cho {0} …" |
| Hạn dùng sau mở | NC Item `resource`; quyền `write` NC Item | `open_stability_days = round(value)` | `resource` không phải NC Item → "Hạn dùng sau mở chỉ áp cho mặt hàng"; thiếu quyền → `PermissionError` "Hạn dùng sau mở thuộc danh mục mặt hàng; cần Quản lý nguồn lực hoặc Tài chính chấp nhận" |

Ghi đích bằng `doc.save()` của người dùng (controller sẵn có kiểm DI-17, FR-NORM-*, quyền, phạm vi khoa). Lỗi controller → giữ đề xuất "Đề xuất", trả lỗi nguyên văn. Thành công → đề xuất `status = "Đã chấp nhận"`, `norm_set`, `applied_ref`, `processed_by/on`, trong cùng giao dịch.

### 3.5 Tác vụ nền `run_cls_norm_suggestion`

1. `set_user(user)`; cache `running`.
2. Dựng phạm vi: NC Test System → `technical_service`, `main_equipment`; bộ định mức mới nhất (mọi trạng thái trừ "Đã thay thế") của hệ thống → dòng; NC QC Plan → `iqc_lines`, `calibration_lines`. `ai_cls_norm.system_resources(...)`.
3. Tài liệu: `frappe.get_all("NC Legal Document", {"doc_type": "Tài liệu của hãng"}, ...)` kèm `related_resources` → `docs_in_scope`. Rỗng → `done`, `created = 0`, thông báo như 3.3.
4. `sources = guard.manufacturer_sections(sections của các tài liệu đó, docs)`.
5. Quy trình: quy trình "Đã ban hành" mới nhất của `technical_service`, ưu tiên cùng khoa của hệ thống (cùng hàm FEAT-024 dùng ở `api/procedure.py` dòng ~720, ASM-024-04) → `guard.build_source("NC Clinical Procedure", proc.as_dict())`; không có → `procedure = None` (vẫn chạy, ASM-038-10).
6. `items` = `guard.build_source("NC Item", ...)` của các NC Item trong phạm vi; `equipment` = `guard.build_source("NC Equipment", ...)`; `service` = `guard.build_source("NC Technical Service", ...)`.
7. `ensure_suggest_cls_norm_v2()`; `gateway.complete("SUGGEST_CLS_NORM", "SUGGEST_CLS_NORM", variables, sources, ref_doctype="NC Test System", ref_name=test_system, postprocess=post)`; `post` gọi `parse_suggestions(data, sources, catalog)` với `catalog` = mã của **toàn bộ** NC Item và NC Equipment (tra CSDL theo các mã AI trả, không gửi đi).
8. `res.ok` sai (lỗi, quá hạn, hết hạn mức) → cache `failed` với `res.error`; **không** tạo, không đổi đề xuất nào (UC-025 3c).
9. Thành công: các đề xuất cũ "Đề xuất" của cùng hệ thống → "Đã bỏ" (ASM-038-11); tạo mỗi dòng một NC AI Norm Suggestion (`ai_log = res.log_name`, `ignore_permissions=True` vì chỉ tác vụ tạo), cache `done`, `created`, `unsupported` (số "Chưa có căn cứ"), `not_in_catalog`, `rejected` (`rejected_citations` của log).
10. Mọi ngoại lệ → cache `failed`, không ném.

### 3.6 Không vào phép tính (FR-AI-008)

Đề xuất nằm ở DocType riêng; `nc_costing_run/loader.py`, `costing/*` không đọc nó (test kiểm bằng `grep`). Dòng định mức và kế hoạch chất lượng không đổi cho đến khi chấp nhận. Chấp nhận lượng hóa chất xóa xác nhận dòng nên bộ phải xác nhận chuyên môn và khóa lại trước khi vào tính giá (FR-NORM-009/010).

### 3.7 Giao diện (chi tiết ở `ui-design.md`)

- `nc_legal_document.js`: hiện/ẩn bảng `related_resources`, bộ lọc `linked_doctype`.
- `normcore/public/js/cls_norm_suggest.js` (mới): `normcore.cls_norm_ai.attach(frm, test_system)` vẽ dải, nút, hộp thoại dùng chung.
- `hooks.py` `doctype_js`: thêm `"NC QC Plan": "public/js/cls_norm_suggest.js"` và `"NC Norm Set": "public/js/cls_norm_suggest.js"` (giữ dòng NC Technical Service). Form JS gốc của hai DocType gọi `normcore.cls_norm_ai.attach` trong `refresh` (khối `// FEAT-038`). `nc_norm_set.js` sửa thêm khối riêng, không chạm khối FEAT-014, FEAT-025.
- Bản dịch `normcore/translations/vi.d/FEAT-038.csv`.

## 4. Tiêu chí nghiệm thu

Test tích hợp ở `normcore/api/test_cls_norm_ai.py`, `normcore/nc_library/doctype/nc_legal_document/test_nc_legal_document_manufacturer.py`, `normcore/nc_costing/doctype/nc_ai_norm_suggestion/test_nc_ai_norm_suggestion.py`; thuần ở `normcore/tests/unit/test_ai_cls_norm.py`, `test_feat_038_ui.py`. Provider giả lập ghi lại `variables`, `sources` (`unittest.mock.patch("normcore.ai.gateway.get_provider", …)`). Dữ liệu: GLU-A (thiết bị EQ_A), HC_GLU theo `test-cases.md` (dòng 168, 188, 198) dựng bằng fixture có sẵn của FEAT-034/036 nếu có.

| # | Điều kiện kiểm được | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | Nạp tài liệu loại "Tài liệu của hãng" không có dòng `related_resources` → `ValidationError`; gắn HC_GLU → lưu, "Chưa lập", tách mục như văn bản khác | — (`test_FR_LIB_013_tai_lieu_hang_phai_gan`) | FR-LIB-013 |
| 2 | `linked_doctype` ngoài NC Item/NC Equipment hoặc dòng trùng → `ValidationError` | — (`test_FR_LIB_013_loai_va_trung`) | FR-LIB-013 |
| 3 | Có tài liệu A gắn HC_GLU (đã lập, còn hiệu lực), tài liệu B của hãng gắn mặt hàng ngoài GLU-A, một văn bản "Thông tư" có mục: yêu cầu đề xuất cho GLU-A → `sources` của lời gọi chỉ gồm mục của A (so khớp đủ tập `name`), mỗi mục chỉ có khóa `name, section_no, heading, plain_text`; `variables` chỉ có khóa `service, procedure, items, equipment`; `items` chỉ có `item_code, item_name, uom`; `equipment` chỉ có `equipment_code, equipment_name`; quy trình là bản "Đã ban hành"; chuỗi JSON của lời gọi không chứa đơn giá NC Item Price của HC_GLU (6.000.000 / "6000000"), không chứa số kết quả NC Test System Volume (12.000 / "12000"), không chứa khóa `price`, `unit_price`, `volume`, `result_count` | **TC-CLS-41** (`test_TC_CLS_41_noi_dung_gui_chi_gom_muc_da_gan`) | FR-LIB-013, FR-AI-016, NFR-SEC-005 |
| 4 | `guard.manufacturer_sections` loại mục của tài liệu ngoài phạm vi; `docs_in_scope` loại tài liệu hết hiệu lực, chưa lập, không gắn, khác loại | — (`test_FR_AI_016_pham_vi_tai_lieu`, unit) | FR-AI-016, FR-AI-011 |
| 5 | Provider trả 3 đề xuất: 2 trích dẫn nguyên văn trong mục của A, 1 trích dẫn không có trong tài liệu → tạo đúng 3 NC AI Norm Suggestion; đúng 2 có `relation = "Theo hướng dẫn"` với `legal_section`, `quote` đúng; đúng 1 có `relation = "Chưa có căn cứ"`, `legal_section`, `quote` trống; cả 3 `status = "Đề xuất"` và `list_cls_norm_suggestions` trả `label = "Đề xuất"` cho cả 3; NC AI Log `rejected_citations = 1` | **TC-CLS-42** (`test_TC_CLS_42_trich_dan_va_nhan_de_xuat`) | FR-AI-017, FR-AI-005 |
| 6 | Cùng ca 5: dòng của bộ định mức GLU-A (mọi trường `as_dict` trừ `modified`) và kế hoạch chất lượng GLU-A không đổi so với trước khi gọi; `grep -rn "NC AI Norm Suggestion" normcore/costing normcore/nc_costing/doctype/nc_costing_run` không có kết quả | **TC-CLS-42** (`test_TC_CLS_42_khong_vao_phep_tinh`) | FR-AI-008 |
| 7 | Provider đề xuất `item_code = "HC_KHONG_CO"`, `item_text = "Hóa chất X"` → số NC Item, NC Equipment không đổi; đề xuất có `not_in_catalog = 1`, `resource` trống, `resource_text = "Hóa chất X"`; `accept_cls_norm_suggestion` → `ValidationError` "Liên kết mặt hàng…"; `link_cls_norm_suggestion` tới HC_GLU rồi chấp nhận được | **TC-CLS-43** (`test_TC_CLS_43_mat_hang_ngoai_danh_muc`) | FR-AI-018 |
| 8 | Chấp nhận "Lượng hóa chất mỗi test" cho HC_GLU trên bộ Nháp: dòng HC_GLU Theo kết quả có `hospital_qty = value`, `basis = "Ước tính"`, `basis_ref` có số hiệu tài liệu, `confirmed_by` trống; đề xuất "Đã chấp nhận", `applied_ref = line_id`. Bộ không Nháp → lỗi, đề xuất giữ "Đề xuất" | — (`test_FR_AI_016_chap_nhan_luong_hoa_chat`) | FR-AI-016, FR-AI-008 |
| 9 | Chấp nhận tần suất chuẩn máy, nội kiểm → dòng kế hoạch tương ứng đổi đúng giá trị; không có dòng → lỗi như 3.4. Chấp nhận hạn dùng sau mở bởi NC Resource Manager → `open_stability_days`; bởi Clinician → `PermissionError` | — (`test_FR_AI_016_chap_nhan_ke_hoach_va_han_dung`) | FR-AI-016 |
| 10 | Bỏ → "Đã bỏ", không ghi đích; xử lý lần hai → lỗi "Đề xuất đã được xử lý"; lần chạy thành công mới đổi đề xuất chờ cũ sang "Đã bỏ" | — (`test_FR_AI_017_bo_va_chay_lai`) | FR-AI-017 |
| 11 | Provider lỗi / quá hạn / hết hạn mức → trạng thái `failed` có thông báo; đề xuất cũ và dữ liệu định mức, kế hoạch không đổi; có NC AI Log | — (`test_UC025_3c_ai_loi_giu_nguyen`) | UC-025 3c |
| 12 | AI tắt → `start_cls_norm_suggestion` báo lỗi của `ensure_enabled`; vẫn xem, bỏ, chấp nhận được đề xuất cũ | — (`test_FR_AI_008_ai_tat_van_xu_ly`) | FR-AI-008 |
| 13 | Quyền: NC Auditor đọc được đề xuất và `list_*`, mọi API ghi → `PermissionError`; NC Council Member (không quyền) đọc → `PermissionError`; Clinician khoa khác → `PermissionError`; Finance đọc được, không bỏ được; perm JSON của NC AI Norm Suggestion và NC Document Resource Link khớp ma trận | — (`test_quyen_nc_ai_norm_suggestion`) | data-model mục 4, FR-ACC-007 |
| 14 | `quote` không nguyên văn trong `legal_section` khi lưu NC AI Norm Suggestion → `ValidationError`; trạng thái không quay lại "Đề xuất" | — (`test_FR_AI_005_trich_dan_de_xuat_nguyen_van`) | FR-AI-005 |
| 15 | Mẫu `SUGGEST_CLS_NORM-v2` cài lười đúng một lần khi v1 còn mặc định; không cài khi Admin đã đổi | — (`test_mau_lenh_suggest_cls_norm_v2`) | FR-AI-014 |
| 16 | UI (unit đọc mã): `cls_norm_suggest.js` chỉ gọi `normcore.api.cls_norm_ai.*`; ẩn nút AI khi AI tắt, ẩn nút ghi khi `can_edit` sai; chuỗi có trong `vi.d/FEAT-038.csv`; `git diff origin/develop -- normcore/public/js/norm_grid/ normcore/api/norm.py` rỗng; `test_norm_grid_ui.py`, `test_time_study_ui.py` xanh không sửa | — (`test_feat_038_ui.py`) | SCR-DSK-014, SCR-DSK-033 |
| 17 | Toàn bộ: `bench run-tests --app normcore` OK; pytest unit+golden, độ phủ costing ≥ 90%; `check_conventions.py` 0; `build_rtm.py` không thêm vấn đề | — | NFR-MNT-001 |

## 5. Giả định và rủi ro

- Giả định: ASM-038-01..14 (`docs/decisions/assumptions/FEAT-038.md`).
- Rủi ro: tác vụ chạy nền cần worker hàng đợi `long` (như FEAT-024/025). Chất lượng đề xuất trên tài liệu thật chưa chấm; staging dùng provider `mock` chỉ trả `{"mock": true}` nên nhánh thành công chỉ kiểm bằng test tích hợp (`parse_suggestions` coi đầu ra thiếu `suggestions` là 0 đề xuất, không lỗi).
- Rủi ro: chấp nhận đổi số liệu đã xác nhận (xóa `confirmed_by`) có thể khiến bộ đang "Đã xác nhận chuyên môn" — không xảy ra vì chỉ áp vào bộ "Nháp".
- Rủi ro: test cũ liệt kê DocType/Select của NC Legal Document (`test_nc_legal_document.py`) có thể so khớp danh sách `doc_type`; nếu đỏ, Dev cập nhật theo ngoại lệ CLAUDE.md mục 3 luật 1 (thêm đúng lựa chọn của FR-LIB-013, giữ so khớp đủ), xin Quyết định BA trên NORM-79 và ghi ASM.
