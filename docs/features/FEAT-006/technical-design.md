# FEAT-006 — Thiết kế kỹ thuật: Soạn quy trình có cấu trúc (thủ công)

Issue NORM-11. Nhánh `ai/NORM-11-feat-006` từ `develop` @ `f82065b`. Tài liệu nguồn: `implementation-plan.md` mục 3 và 5; `srs.md` FR-PROC-001..007, 009, 013; `use-cases.md` UC-005; `data-model.md` 3.3, 4, 6; ADR-002, ADR-010, ADR-014.

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-PROC-001 | Đủ | Tạo bản nháp v1, 8 phần cố định (7 trường văn bản + các bước) |
| FR-PROC-002 | Đủ | DI-02 ở controller; API dẫn tới bản đang có |
| FR-PROC-003, 006 | Đủ | Thêm/sửa/xóa/sắp lại bước; mã `S###` từ `next_step_seq` |
| FR-PROC-004 | Đủ | Nguồn lực có cấu trúc gắn `step_id`, mã dòng `R###` |
| FR-PROC-005 | Một phần | Gợi ý chỉ cho Nhân lực (NC Job Title); loại khác để trống liên kết (G2, ASM-019) |
| FR-PROC-007 | Một phần | Chưa có `legal_section` (Q1, ASM-017); lưu đích, đoạn trích, quan hệ, lý do |
| FR-PROC-009 | Đủ | `track_changes` (Version); API sửa dòng tại chỗ |
| FR-PROC-013 | Đủ | Sao chép, đích qua cùng kiểm tra tạo |
| FR-PROC-008, 012 | Không | FEAT-007 |

## 2. DocType

**NC Clinical Procedure** thêm: `previous_version` (Link tự thân), `needs_review` (Check), `doctor_request` (Text), `overview`, `indications`, `contraindications`, `cautions`, `preparation_notes`, `monitoring`, `references` (Text Editor), `citations` (Table NC Procedure Citation), `copied_from` (Link tự thân), `ai_log` (Link NC AI Log). `next_resource_seq` giữ (G5 → AMD-001). Danh sách chuẩn lọc theo `workflow_state`, `department`, `needs_review` (`in_standard_filter`).

**NC Procedure Citation** (bảng con, mới): `target_section` (Select, 8 phần — G1), `target_step_id` (Data), `relation` (Select BB, mặc định "Chưa có căn cứ"), `quote` (Small Text), `deviation_reason` (Small Text). Không có `legal_section` (Q1). Quyền theo cha.

**Quyền**: giữ nguyên ma trận đã cài ở FEAT-000 (Clinician, Dept Head: đọc/sửa/tạo; 8 vai trò còn lại chỉ đọc; không ai có xóa — ASM-015). Không đổi `permissions`.

**Ràng buộc (controller `validate`/`before_insert`, mỗi cái có test)**
- DI-01: đã có (mã duy nhất, bất biến, từ bộ đếm). Mã bước/dòng cấp bằng `procedure/codes.py::next_code` (hàm thuần, chuyển ra khỏi controller).
- DI-02: không có bản thứ hai cùng (dịch vụ, khoa) ở trạng thái khác {Đã ban hành, Đã thay thế, Đã thu hồi}. Chạy ở `before_insert` (trước khi đặt tên, tránh lỗi trùng khóa) và `validate`.
- Trích dẫn: đúng một trong `target_section`/`target_step_id`; `target_step_id` phải có trong `steps`.
- Nguồn lực: `step_id` phải có trong `steps` (đã có); Nhân lực đơn vị "phút" (ASM-011).
- DI-07: đã có (`before_save` khóa bản ban hành).

**Patch**: thêm trường/DocType mới được `bench migrate` đồng bộ từ JSON; không đổi/mất dữ liệu cũ nên không cần patch dữ liệu (`CLAUDE.md` mục 4 chỉ đòi patch cho thay đổi cấu trúc cần chuyển dữ liệu). Bản ghi FEAT-000 trên staging có các trường mới trống, hợp lệ.

## 3. Logic thuần — `normcore/procedure/`

- `codes.py::next_code(prefix, counter, existing)` → `(số, mã)`; không tái dùng (FR-PROC-003, ADR-002).
- `steps.py`: `reorder(ids, order)` (kiểm `order` là hoán vị của `ids`), `move(ids, step_id, delta)`, `add_step(steps, counter, data)`, `remove_step(steps, step_id)`.
- `copying.py::copy_structure(steps, resources, citations)` → bản mới với mã bước cấp lại từ `S001` theo thứ tự hiển thị, mã dòng từ `R001`, ánh xạ `step_id` của nguồn lực và trích dẫn (G4).
- Không có BR giá nào ở FEAT này; không liên quan golden.

## 4. API `normcore/api/procedure.py` (mọi hàm `@frappe.whitelist()`)

Quy ước: đọc → `frappe.has_permission(..., "read")`; ghi → `"write"`/`"create"`; thiếu quyền ném `frappe.PermissionError`. Mọi hàm ghi vào quy trình có sẵn dùng `_editable(name)`: kiểm quyền ghi, rồi từ chối nếu `workflow_state != "Nháp"` (DI-07, `ValidationError`). Thông báo tiếng Việt.

| Hàm | Tham số | Kết quả / lỗi |
| :-- | :-- | :-- |
| `list_procedures` | `state, department, needs_review` (tùy chọn) | danh sách (đã có, thêm lọc và `needs_review`) |
| `create_procedure` | `technical_service, department` | `{name, version_no}`. Lỗi: có bản "Đã ban hành" → "Dịch vụ đã có quy trình ban hành; tạo phiên bản mới thuộc chức năng sửa đổi" (Q3); có bản đang soạn/duyệt → từ chối. Cả hai ném `ExistingProcedureError` (con của `ValidationError`) mang `.existing` và đặt `frappe.response["existing_procedure"]` |
| `find_existing` | `technical_service, department` | `{draft, published}` (tên hoặc null) — cho giao diện dẫn tới bản có sẵn |
| `get_procedure` | `name` | 8 phần (`sections` theo thứ tự FR-PROC-001), `steps` (theo thứ tự), `resources`, `citations`, `can_edit`, `needs_review`, `copied_from`, `previous_version` |
| `save_sections` | `procedure, sections` (dict, 7 trường văn bản) | các phần đã lưu; khóa lạ bị từ chối |
| `add_step` | `procedure, phase, step_title, description` | đã có; giữ hợp đồng |
| `update_step` | `procedure, step_id, phase, step_title, description` | sửa tại chỗ; `step_id` không đổi được |
| `delete_step` | `procedure, step_id` | từ chối nếu còn nguồn lực/trích dẫn gắn bước (ASM-018); mã không tái dùng |
| `reorder_steps` | `procedure, order` (list `step_id`) | hoán vị đầy đủ; mã giữ nguyên (FR-PROC-006) |
| `add_resource` | `procedure, step_id, resource_type, resource_text, quantity, uom, linked_doctype, linked_name, headcount` | `resource_row_id` |
| `update_resource` / `delete_resource` | `procedure, resource_row_id, ...` | sửa tại chỗ; mã dòng bất biến |
| `suggest_catalog` | `resource_type, text` | `[{doctype, name, label}]`; chỉ Nhân lực (NC Job Title), loại khác `[]` (G2) |
| `add_citation` / `update_citation` / `delete_citation` | `procedure, ...`; dòng xác định bằng `name` của dòng con | `relation` mặc định "Chưa có căn cứ"; đúng một đích |
| `copy_procedure` | `source, technical_service, department` | `{name}`; đích qua cùng kiểm tra `create_procedure`; ghi `copied_from` |

Gợi ý danh mục dùng `frappe.get_all` sau khi kiểm quyền đọc quy trình, vì NC Clinician không có quyền đọc NC Job Title (ma trận mục 4) nhưng phải chọn được chức danh.

**Lịch sử (FR-PROC-009, ADR-014)**: mọi ghi đi qua `doc.save()` nên `track_changes` ghi Version với `changed` (trường), `row_changed` (bước, dòng nguồn lực, trích dẫn: trước/sau), `added`, `removed`; kèm người (`owner`) và thời điểm (`creation`). Các hàm `update_*` sửa dòng tại chỗ, không xóa-chèn lại.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | Tạo bản nháp v1, `workflow_state` = Nháp, `get_procedure` có đủ 8 phần | TC-PROC-01 | FR-PROC-001 |
| 2 | Tạo lần hai (còn Nháp) ném lỗi, trả tên bản có | TC-PROC-02 | FR-PROC-002 |
| 3 | 3 bước S001..S003, đổi chỗ 1 và 3 giữ mã, xóa S002, bước mới S004 (thuần) | TC-PROC-03 | FR-PROC-003, 006 |
| 4 | Nhân lực: `step_id`, `R001`, `headcount`, NC Job Title; mã không đổi khi sửa | TC-PROC-04 | FR-PROC-004 |
| 5 | Gợi ý theo tên; để trống liên kết | — | FR-PROC-005 |
| 6 | Sửa mô tả bước và số lượng nguồn lực → Version có trước, sau, người, thời điểm | TC-PROC-08 | FR-PROC-009 |
| 7 | Trích dẫn S001 "Theo hướng dẫn", phần Chỉ định "Khác biệt" + lý do; mặc định "Chưa có căn cứ"; lọc theo bước/phần | TC-PROC-09 | FR-PROC-007 |
| 8 | Sao chép: mã mới, ánh xạ nguồn lực/trích dẫn, `copied_from` | — | FR-PROC-013 |
| 9 | Q3: tạo/sao chép vào (dịch vụ, khoa) đã có bản ban hành bị từ chối | — | FR-PROC-001/002/013 |
| 10 | NC Finance (chỉ đọc) và NC Auditor bị `PermissionError` ở mọi hàm ghi | — | FR-ACC-007 |
| 11 | Quy trình không Nháp bị từ chối ở mọi hàm ghi (DI-07) | — | — |

Test: `test_FR_PROC_005_*` (gợi ý), `test_FR_PROC_013_*` (sao chép) đặt tên theo FR vì không có TC.

## 6. Giả định (ASM) và rủi ro

ASM-017 (Q1 không `legal_section`; TC-PROC-09 chờ FEAT-020), ASM-018 (G1 phần + xóa bước còn nguồn lực bị từ chối), ASM-019 (G2 gợi ý chỉ NC Job Title), ASM-020 (Q3 từ chối khi đã ban hành), ASM-021 (G3 vai trò "không quyền" = NC Finance), ASM-022 (G4 sao chép), ASM-023 (G6 lịch sử = Version), ASM-024 (G7 tên nhánh). Q2 cập nhật cột trạng thái ASM-011. G5 → AMD-001.

Rủi ro: (1) Version chỉ ghi khi dữ liệu đổi; sắp lại bước thuần túy được ghi ở `row_changed` theo `idx` — kiểm bằng test. (2) `frappe.response` trên đường lỗi — giao diện không phụ thuộc vào nó, dùng `find_existing`. (3) Bài toán đổi 14 → 15 DocType ở `test_permissions` (Q4).
