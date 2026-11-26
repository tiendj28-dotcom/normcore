# FEAT-008 — Sửa đổi, so sánh phiên bản, thu hồi — Thiết kế kỹ thuật

Issue NORM-50. Nguồn: `srs.md` FR-WF-009, FR-WF-010, FR-WF-011, FR-WF-012; `use-cases.md` UC-007; `data-model.md` 3.3 (NC Clinical Procedure và bảng con), 3.5 (NC Norm Set: `needs_update`, `step_change_note`), mục 4 (dòng "Quy trình", "Bộ định mức"), 5.1 (dòng "Thu hồi"), 5.2, DI-01, DI-02, DI-07; `architecture.md` ADR-002, ADR-010, ADR-011, ADR-014; `ux-foundations.md` SCR-DSK-011; `design.md` mục 3, 5; TC-WF-05, TC-WF-06, TC-WF-07. Phụ thuộc FEAT-007 (DONE; As-Built `docs/as-built/FEAT-007.md`).

Giả định: `docs/decisions/assumptions/FEAT-008.md` (ASM-008-01..14). Q1 (mục 9) đã có Quyết định Lead: PA1 (ASM-008-14). Không có AMD.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-WF-009 (Must) | "Sửa đổi" trên quy trình "Đã ban hành" mới nhất của (dịch vụ, khoa) → bản nháp `version_no` kế tiếp, sao chép toàn bộ nội dung (8 phần, `doctor_request`, bước, nguồn lực, trích dẫn), **giữ nguyên** `step_id`, `resource_row_id`, `next_step_seq`, `next_resource_seq`; `previous_version` = bản nguồn. Đã có bản đang soạn/duyệt của (dịch vụ, khoa) → trả bản đó, không tạo mới (UC-007 1d). Bản nháp đi qua đúng luồng FEAT-007 (UC-007 bước 3) |
| FR-WF-010 (Should) | So sánh hai phiên bản cùng (dịch vụ, khoa): khác biệt theo phần (8 phần cố định), theo bước (`step_id`), theo dòng nguồn lực (`resource_row_id`); mỗi mục mang trạng thái thêm / bỏ / đổi / giữ nguyên; màn hình SCR-DSK-011 |
| FR-WF-011 (Must) | Khi một phiên bản được "Ban hành": mọi NC Norm Set đang dựa trên một phiên bản cũ hơn của cùng (dịch vụ, khoa), trạng thái khác "Đã thay thế", được đặt `needs_update = 1` và `step_change_note` liệt kê mã bước thêm, bỏ, đổi. Theo PA1 (ASM-008-14) |
| FR-WF-012 (Should) | NC Director "Thu hồi" quy trình "Đã ban hành": bắt buộc lý do; trạng thái "Đã thu hồi"; lý do ghi vào sổ sự kiện và Comment "Workflow"; thông báo người soạn. Không có TC riêng; vẫn có test (mục 7) |

Không làm:
- UC-007 1c (yêu cầu sửa đổi đến từ phân hệ D, UC-014): thuộc FEAT của UC-014; FEAT-008 không thêm trường đề xuất/lý do (ASM-008-04).
- Hàng đợi rà soát SCR-DSK-012 ("Sửa đổi", "Không cần sửa"): FEAT của FR-LIB-009. API `create_revision` ở đây là điểm gọi chung để FEAT đó dùng lại.
- Sinh, sửa, khóa bộ định mức; gỡ cờ "Cần cập nhật" (FEAT-012, ASM-008-09).
- Phục hồi bản "Đã thay thế" khi bản hiện hành bị thu hồi (ASM-008-11).
- So sánh trích dẫn (FR-WF-010 chỉ nêu phần, bước, nguồn lực; ASM-008-06).

Dùng lại, không làm lại: luồng duyệt `api/procedure_workflow.apply_action`, `_notify`, `supersede_due`, `procedure/approval.py` (FEAT-007); API trình soạn `api/procedure.py` (`_find_existing`, hằng `SECTIONS`, `STEP_FIELDS`, `RESOURCE_FIELDS`, `CITATION_FIELDS`, `TEXT_FIELDS`) và trang `procedure-editor` (FEAT-006/007); `core/audit.py` (`log_event`, `flags.audit_detail`); `core/permissions.py` (phạm vi khoa, FEAT-001); khung NC Norm Set (FEAT-000, `nc_costing/doctype/nc_norm_set`).

## 2. DocType

### 2.1 NC Clinical Procedure — không thêm trường
Mọi trường cần đã có (`version_no`, `previous_version`, `workflow_state`, `next_step_seq`, `next_resource_seq`). Controller **không đổi**: bản nháp sửa đổi đi qua `before_insert`/`validate` sẵn có (DI-02 một bản đang soạn; `assign_step_ids` giữ mã đã có và đếm tiếp từ `next_step_seq` đã sao chép → bước mới của phiên bản 2 không tái dùng mã đã bỏ ở phiên bản 1, DI-01).

Trạng thái "Đã thu hồi" đã có trong fixture Workflow State và Workflow (danh sách state) từ FEAT-007. **Không thêm transition "Thu hồi" vào fixture Workflow** (ASM-008-02): test cũ `test_feat_007_workflow::test_workflow_fixture_khop_transitions` (fixture = `approval.TRANSITIONS`) và `tests/unit/test_procedure_approval::test_transitions_la_du_lieu` (`len == 7`) khóa luồng duyệt 7 transition; luật cứng 1 không cho sửa. Thu hồi đi đường hệ thống giống "Đã thay thế" của FEAT-007 (`db_set` + sổ sự kiện), kiểm vai trò trong `apply_action`.

### 2.2 NC Norm Set — thêm hai trường (PA1, ASM-008-14)
DocType đã có từ FEAT-000 (khung, chưa có hai trường dưới). `data-model.md` 3.5 đã định nghĩa cả hai; FEAT-008 **mở rộng, không tạo DocType**.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| needs_update | Cần cập nhật | Check | | `read_only = 1`, `in_list_view`, `in_standard_filter` (SCR-DSK-013 lọc theo cờ); đặt bởi FR-WF-011 |
| step_change_note | Bước thêm, bỏ, đổi | Small Text | | `read_only = 1`; định dạng mục 4.2 |

Đặt sau `procedure`. Chỉ thêm trường, mặc định 0/trống → không cần patch (tiền lệ FEAT-007 mục 2.2). Ghi bằng `frappe.db.set_value(..., update_modified=False)` vì bộ "Đã khóa" chặn `save()` (controller FEAT-000) — cờ là dữ liệu hệ thống như `needs_review` của quy trình (ASM-008-08). Quyền không đổi (ma trận mục 4, dòng "Bộ định mức"; NC Auditor chỉ đọc đã có).

## 3. API whitelisted

Mọi hàm kiểm quyền tường minh. Lỗi quyền: `frappe.PermissionError`; lỗi nghiệp vụ: `frappe.ValidationError` (thông báo tiếng Việt qua `_()`).

### 3.1 `normcore.api.procedure.create_revision(procedure)` — FR-WF-009
| Bước | Kiểm / làm | Lỗi |
| :-- | :-- | :-- |
| 1 | `has_permission(DT, "create")` và `has_permission(DT, "write", doc=procedure)` (phạm vi khoa: NC Clinician, NC Department Head của khoa chủ trì; ASM-008-01) | PermissionError "Bạn không có quyền sửa đổi quy trình này" |
| 2 | Có bản đang soạn/duyệt của (dịch vụ, khoa) (`_find_existing` → `draft`) | Không lỗi: trả `{"name": draft, "version_no": …, "existing": 1}` (UC-007 1d) |
| 3 | `workflow_state == "Đã ban hành"` | ValidationError "Chỉ sửa đổi được quy trình đã ban hành" |
| 4 | Bản nguồn là bản "Đã ban hành" có `version_no` lớn nhất của (dịch vụ, khoa) (ASM-008-03) | ValidationError "Đã có phiên bản ban hành mới hơn: {0}. Sửa đổi từ phiên bản đó." |
| 5 | `versioning.build_revision(src, max_version)` → `insert()` (qua validate controller, DI-02) | — |
| 6 | `doc.add_comment("Info", "Tạo phiên bản sửa đổi từ {nguồn}")` | — |

Trả `{"name", "version_no", "existing": 0}`. `max_version` = `version_no` lớn nhất của mọi bản (mọi trạng thái) của (dịch vụ, khoa).

### 3.2 `normcore.api.procedure.list_versions(procedure)` — cho bộ chọn SCR-DSK-011
Kiểm `has_permission(DT, "read", doc=procedure)`. Trả các bản cùng (dịch vụ, khoa) mà người gọi đọc được (`frappe.get_list`): `name, version_no, workflow_state, effective_date, decision_no`, sắp `version_no` giảm dần.

### 3.3 `normcore.api.procedure.compare_versions(base, target)` — FR-WF-010
| Kiểm | Lỗi |
| :-- | :-- |
| `has_permission(DT, "read", doc=…)` cho cả hai | PermissionError "Bạn không có quyền xem quy trình này" |
| `base != target`; cùng `technical_service` và `department` | ValidationError "Chỉ so sánh hai phiên bản của cùng một quy trình (dịch vụ, khoa)" |

Trả `{"base": hdr, "target": hdr, **diff.diff_procedures(base_dict, target_dict, SECTIONS)}`; `hdr` = `name, version_no, workflow_state, effective_date`. Thứ tự không bắt buộc cũ → mới; giao diện mặc định đặt bản `version_no` nhỏ làm `base`.

### 3.4 `normcore.api.procedure_workflow.apply_action(procedure, "Thu hồi", reason)` — FR-WF-012
Mở rộng hàm có sẵn, không thêm endpoint:
- `approval.next_state` tìm trong `approval.ACTIONS = TRANSITIONS + (WITHDRAW,)`, `WITHDRAW = ("Đã ban hành", "Thu hồi", "Đã thu hồi", "NC Director")`. `TRANSITIONS` giữ 7 dòng (ASM-008-02).
- `_actor_error`: thêm nhánh `state == "Đã ban hành"`: không có vai trò NC Director → "Chỉ NC Director được thu hồi quy trình". (Hiện tại nhánh này chưa có → hàm trả None; phải thêm trước khi `_available_actions` dùng `ACTIONS`.)
- `_available_actions` duyệt `approval.ACTIONS` → `get_review` trả `"Thu hồi"` cho Director ở "Đã ban hành".
- Lý do trống sau strip → ValidationError "Cần nhập lý do thu hồi".
- Ghi: `frappe.db.set_value(DT, name, "workflow_state", "Đã thu hồi")`; `audit.log_event("Chuyển trạng thái", DT, name, "Đã ban hành", "Đã thu hồi", detail=reason)` (người = người gọi); `doc.add_comment("Workflow", "Thu hồi: Đã ban hành → Đã thu hồi — {lý do}")`; `_notify([doc.owner], "{name}: đã thu hồi — {lý do}", doc)`.
- `get_review` trả thêm `last_withdraw` (`{by, at, reason}` từ sự kiện "Chuyển trạng thái" tới "Đã thu hồi" mới nhất; None nếu không có) cho dải lý do ở giao diện.
- NC Auditor, NC Finance, NC Department Head, NC Council Member: PermissionError (qua `_actor_error`). Trạng thái khác "Đã ban hành" (kể cả "Đã thay thế"): ValidationError "Hành động Thu hồi không áp dụng ở trạng thái {0}" (đã có sẵn trong `apply_action`).

### 3.5 Mở rộng "Ban hành" — FR-WF-011 (PA1, ASM-008-14)
Trong `_after_action` nhánh "Ban hành", sau `supersede_due`: gọi `_flag_norm_sets(doc)`:
1. Lấy NC Norm Set có `technical_service`, `department` của `doc`, `status != "Đã thay thế"`, `procedure` ≠ `doc.name` và `procedure.version_no < doc.version_no` (ASM-008-07).
2. Với mỗi `procedure` cũ khác nhau: `diff.step_changes(old, new)` → `diff.format_step_note(...)`.
3. `frappe.db.set_value("NC Norm Set", ns, {"needs_update": 1, "step_change_note": note}, update_modified=False)`; Comment "Info" trên bộ định mức: "Cần cập nhật do ban hành {doc.name}: {note}" (NC Audit Event không có loại sự kiện phù hợp; không thêm loại mới, ASM-008-08).
Chạy với `ignore_permissions` (hệ thống): người ban hành (Director) chỉ có R trên bộ định mức. Không có bộ định mức nào → không làm gì.

## 4. Logic thuần

### 4.1 `normcore/procedure/versioning.py` (mới, không import frappe)
- `build_revision(src: dict, max_version: int) -> dict`: dict cho `frappe.get_doc` gồm `doctype`, `technical_service`, `department`, `version_no = max_version + 1`, `previous_version = src["name"]`, các trường `TEXT_FIELDS` và `doctor_request`, `needs_review` (ASM-008-05), `steps` (giữ `step_id`, `phase`, `step_title`, `description`, `reference_minutes`, `ai_suggested = 0`), `resources` (giữ `resource_row_id` và mọi trường `RESOURCE_FIELDS`, `ai_suggested = 0`), `citations` (giữ `target_section`, `target_step_id`, `relation`, `legal_document`, `legal_section`, `quote`, `deviation_reason`), `next_step_seq`, `next_resource_seq` của nguồn. Không sao chép: `workflow_state` (để controller đặt "Nháp"), `decision_no`, `effective_date`, `copied_from`, `ai_log`. Danh sách trường nhận qua tham số hoặc hằng trong module (không import `api`).
- `can_revise(state) -> bool`: `state == "Đã ban hành"`.

Không có BR tính giá, không có golden.

### 4.2 `normcore/procedure/diff.py` (mới, không import frappe)
Đầu vào: dict quy trình `{"<field>": str, "steps": [dict], "resources": [dict]}` (trường như DocType).
- `STEP_COMPARE = ("phase", "step_title", "description", "reference_minutes")`; `RESOURCE_COMPARE = ("step_id", "resource_type", "resource_text", "linked_doctype", "linked_name", "quantity", "uom", "headcount")`. Chuẩn hóa: None/"" bằng nhau; số so bằng `float`; chuỗi `strip()`.
- `diff_sections(old, new, sections) -> list[dict]`: mỗi phần trong 8 phần (bỏ "steps"): `{"key", "label", "status": "added"|"removed"|"changed"|"same", "old", "new"}` (trống → có = added; có → trống = removed).
- `diff_steps(old_steps, new_steps) -> list[dict]`: ghép theo `step_id`. `{"step_id", "status", "fields": [tên trường đổi], "old", "new", "old_idx", "new_idx"}`. Thứ tự: theo thứ tự bản mới, bước bị bỏ chèn sau bước đứng trước nó ở bản cũ. Chỉ đổi vị trí → `status = "same"`, `moved = True` (ASM-008-06).
- `diff_resources(old_res, new_res) -> list[dict]`: ghép theo `resource_row_id`; `{"resource_row_id", "step_id", "status", "fields", "old", "new"}`; `step_id` của bản mới (bỏ thì của bản cũ).
- `diff_procedures(old, new, sections) -> dict`: `{"sections", "steps", "resources", "summary": {"sections": {added, removed, changed}, "steps": {...}, "resources": {...}}}` (đếm).
- `step_changes(old, new) -> {"added": [...], "removed": [...], "changed": [...]}` (FR-WF-011): `added`/`removed` theo `step_id`; `changed` = bước có ở cả hai và (một trường `STEP_COMPARE` đổi **hoặc** có dòng nguồn lực thêm/bỏ/đổi gắn `step_id` đó ở bản cũ hoặc bản mới). Mỗi danh sách sắp theo mã. TC-WF-06: bỏ S002, thêm S005, đổi nguồn lực S003 → `{"added": ["S005"], "removed": ["S002"], "changed": ["S003"]}`. Dòng nguồn lực chuyển từ S003 sang S004 → cả S003, S004 "đổi". Dòng nguồn lực của bước bị bỏ không làm bước đó thành "đổi".
- `format_step_note(changes) -> str`: `"thêm S005; bỏ S002; đổi S003"` (thứ tự thêm, bỏ, đổi; nhiều mã nối ", "; nhóm rỗng bỏ qua; cả ba rỗng → `"Không có bước thêm, bỏ, đổi"`) (ASM-008-10).

### 4.3 `normcore/procedure/approval.py` (mở rộng)
Thêm `WITHDRAW`, `ACTIONS`; `next_state` tìm trong `ACTIONS`. `TRANSITIONS`, `PENDING_STATES`, `CLOSED_STATES` không đổi.

## 5. Giao diện (chi tiết ở `ui-design.md`)
- Form Desk NC Clinical Procedure: nút "Sửa đổi" (Đã ban hành, người có quyền ghi), "So sánh phiên bản" (có ≥ 2 phiên bản đọc được), "Thu hồi" (Đã ban hành, NC Director; hộp thoại lý do).
- `procedure-editor`: cùng ba nút ở thanh trên khi chỉ đọc; chế độ so sánh SCR-DSK-011 trong cùng trang (route `procedure-editor/<name>/compare/<other>`; ADR-010 chỉ ba trang Vue, ASM-008-12).
- NC Norm Set: form có dải `yellow` "Cần cập nhật: <ghi chú>" khi `needs_update`; danh sách có cột và bộ lọc "Cần cập nhật".

## 6. Quyền
| Thao tác | Được | Không được (có test) |
| :-- | :-- | :-- |
| Sửa đổi | NC Clinician, NC Department Head cùng khoa chủ trì | NC Auditor, NC Finance, NC Director (chỉ R), Clinician khoa khác |
| Danh sách / so sánh phiên bản | Mọi vai trò có R trên quy trình (gồm NC Auditor), trong phạm vi khoa | NC Clinician khoa khác (PermissionError) |
| Thu hồi | NC Director | NC Department Head, NC Council Member, NC Auditor, NC Finance |
| Cờ bộ định mức | Hệ thống khi ban hành | — (trường `read_only`; NC Auditor không sửa được) |

Không có DocType mới → không thêm dòng `DOCTYPE_ROW` trong `check_conventions.py`.

## 7. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Quy trình v1 "Đã ban hành" có 4 bước S001..S004 và nguồn lực R001..: `create_revision(v1)` → bản mới `version_no = 2`, "Nháp", `previous_version = v1`, đúng 4 bước cùng `step_id` và thứ tự, cùng `resource_row_id`, 7 phần văn bản bằng nhau, `next_step_seq`/`next_resource_seq` bằng nguồn; thêm bước mới ở v2 được `S005` (không tái dùng) | TC-WF-05 | FR-WF-009 | `test_TC_WF_05_sua_doi_giu_ma_buoc` (tích hợp) + unit `build_revision` |
| 2 | Gọi lại `create_revision(v1)` khi v2 đang Nháp → trả v2, `existing = 1`, không thêm bản ghi | — | FR-WF-009 (UC-007 1d) | `test_sua_doi_da_co_ban_nhap_tra_ban_dang_co` |
| 3 | `create_revision` trên "Nháp", "Đã thay thế", "Đã thu hồi" hoặc bản ban hành cũ hơn → ValidationError; NC Auditor, NC Finance, Clinician khoa khác → PermissionError | — | FR-WF-009, FR-ACC-007 | `test_sua_doi_tu_choi_trang_thai_va_quyen` |
| 4 | v2 bỏ S002, thêm S005, đổi nguồn lực của S003; bộ định mức dựa trên v1 (Nháp và Đã khóa); ban hành v2 qua `apply_action` → cả hai có `needs_update = 1`, `step_change_note = "thêm S005; bỏ S002; đổi S003"`; bộ "Đã thay thế" và bộ dựa trên v2 không bị gắn | TC-WF-06 | FR-WF-011 | `test_TC_WF_06_ban_hanh_gan_co_bo_dinh_muc` (tích hợp) + unit `step_changes`, `format_step_note` |
| 5 | `compare_versions(v1, v2)` (dữ liệu dòng 4, thêm đổi phần "Chỉ định"): `sections` có "indications" = changed, còn lại same; `steps` S002 removed, S005 added, S003 same (trường bước không đổi), S001/S004 same; `resources` dòng của S003 changed với `fields` đúng; `summary` đếm đúng. Giao diện hiển thị thêm (xanh), bỏ (đỏ), đổi (vàng) theo phần, bước, dòng nguồn lực | TC-WF-07 | FR-WF-010 | `test_TC_WF_07_so_sanh_phien_ban` (tích hợp API) + unit `diff_*`; phần hiển thị loại M: QA kiểm bằng mắt (Playwright) |
| 6 | `compare_versions` hai quy trình khác (dịch vụ, khoa) → ValidationError; Clinician khoa khác → PermissionError; NC Auditor đọc được | — | FR-WF-010, FR-ACC-007 | `test_so_sanh_kiem_quyen_va_cung_quy_trinh` |
| 7 | NC Director `apply_action(v, "Thu hồi", "lý do")` trên "Đã ban hành" → "Đã thu hồi"; NC Audit Event (`from_state` Đã ban hành, `to_state` Đã thu hồi, `detail` = lý do); Comment "Workflow"; Notification Log cho người soạn; nội dung vẫn bị khóa | — | FR-WF-012 | `test_FR_WF_012_thu_hoi_co_ly_do` |
| 8 | Thu hồi thiếu lý do → ValidationError, trạng thái giữ; NC Department Head, NC Council Member, NC Auditor → PermissionError; trên "Đã thay thế"/"Nháp" → ValidationError; `get_review` chỉ trả "Thu hồi" cho Director | — | FR-WF-012, FR-ACC-007 | `test_FR_WF_012_thu_hoi_tu_choi` |
| 9 | Test cũ FEAT-007 (fixture = `TRANSITIONS`, `len == 7`) vẫn xanh không sửa | — | — | bộ test hiện có |

## 8. Giả định và rủi ro
- ASM-008-01..13: `docs/decisions/assumptions/FEAT-008.md`.
- Rủi ro: FEAT-012 sau này viết lại NC Norm Set. Hai trường của PA1 đúng tên, kiểu ở data-model 3.5 nên FEAT-012 giữ được; FEAT-012 phải giữ `_flag_norm_sets` khi đổi controller.
- Rủi ro: Thu hồi không qua Frappe Workflow → nút workflow chuẩn của Desk không có "Thu hồi"; thay bằng nút tùy biến (ui-design). Nếu Lead cho cập nhật số đếm test cũ (luật cứng 1, ngoại lệ không phủ transition), có thể chuyển sang transition trong fixture sau.

## 9. Câu hỏi cho Lead

**Q1 — cờ "Cần cập nhật" trên NC Norm Set (FR-WF-011, TC-WF-06) khi FEAT-012 chưa DONE.**
Hiện trạng: NC Norm Set **đã có trên develop** từ FEAT-000 (khung walking skeleton: `technical_service`, `department`, `procedure`, `version_no`, `status`, `lines`, `next_line_seq`, `locked_by`, `locked_on`; có `make_norm_set`). Chưa có `needs_update`, `step_change_note` (data-model 3.5 đã định nghĩa, ghi "Đặt bởi FR-WF-011").
- **PA1 (đề xuất):** FEAT-008 thêm hai trường `needs_update`, `step_change_note` vào NC Norm Set đã có (mở rộng, không tạo DocType; không cần patch), gắn cờ khi ban hành (mục 3.5). TC-WF-06 test đủ ngay ở FEAT-008 bằng bộ định mức tạo qua `make_norm_set` của FEAT-000. FEAT-012 giữ hai trường này.
- **PA2:** FEAT-008 chỉ làm logic thuần `diff.step_changes`/`format_step_note` và hàm `_flag_norm_sets` có test đơn vị; không đổi NC Norm Set; TC-WF-06 (tích hợp) chuyển sang FEAT-012. FEAT-008 khi đó không đủ DoD cho FR-WF-011 (Must) và TC-WF-06 → cần Lead ghi nhận ngoại lệ.

**Quyết định Lead:** PA1 (bình luận `01a215c3-0642-7c84-890a-45607e456bdb` trên NORM-50). PA2 bị loại vì để FR Must thiếu DoD. FEAT-008 không gỡ cờ, không làm UC-007 1c. Ghi ở ASM-008-14; T06 theo PA1.
