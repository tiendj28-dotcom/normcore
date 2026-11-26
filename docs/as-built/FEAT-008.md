# As-Built: FEAT-008 Sửa đổi, so sánh phiên bản, thu hồi
- Phiên bản app 0.0.1; Dev: NORM-50; Người nghiệm thu: QA (Multica), verify accepted tại 97e58922d804ad244fe353b61be3407ea8b7e256

## 1. Luồng nghiệp vụ đã xây
- **Sửa đổi (FR-WF-009):** từ quy trình "Đã ban hành" mới nhất của (dịch vụ, khoa), `create_revision` tạo bản nháp `version_no` kế tiếp, sao chép 7 phần văn bản, `doctor_request`, bước, nguồn lực, trích dẫn; giữ nguyên `step_id`, `resource_row_id`, `next_step_seq`, `next_resource_seq` nên bước mới không tái dùng mã đã bỏ. Không sao chép `decision_no`, `effective_date`, `copied_from`, `ai_log`; `ai_suggested` = 0. Đã có bản đang soạn/duyệt thì trả bản đó (`existing = 1`). Bản nháp đi qua luồng duyệt FEAT-007.
- **So sánh (FR-WF-010):** `compare_versions` trả khác biệt theo phần (7), bước (`step_id`), dòng nguồn lực (`resource_row_id`) với trạng thái thêm/bỏ/đổi/giữ nguyên và bảng đếm; SCR-DSK-011 là chế độ `compare` của `procedure-editor`.
- **Cờ bộ định mức (FR-WF-011):** khi "Ban hành", `_flag_norm_sets` đặt `needs_update = 1` và `step_change_note` (vd `thêm S005; bỏ S002; đổi S003`) cho NC Norm Set dựa trên phiên bản cũ hơn của cùng (dịch vụ, khoa), trừ bộ "Đã thay thế"; ghi Comment "Info" trên bộ định mức.
- **Thu hồi (FR-WF-012):** `apply_action(procedure, "Thu hồi", reason)`, chỉ NC Director, bắt buộc lý do; trạng thái "Đã thu hồi" bằng `db_set` (không thêm transition vào fixture Workflow, ASM-008-02); ghi NC Audit Event (`detail` = lý do), Comment "Workflow", Notification Log cho người soạn; `get_review.last_withdraw`.

## 2. DocType
- NC Norm Set: thêm `needs_update` (Check, chỉ đọc, `in_list_view`, `in_standard_filter`) và `step_change_note` (Small Text, chỉ đọc) theo data-model 3.5 (ASM-008-14, Quyết định Lead Q1 = PA1). Chỉ thêm trường, không cần patch.
- NC Clinical Procedure: không đổi cấu trúc.

## 3. API, logic thuần, giao diện
- `api/procedure.py`: `create_revision`, `list_versions`, `compare_versions`. `api/procedure_workflow.py`: Thu hồi trong `apply_action`, `_withdraw`, `_flag_norm_sets`, `get_review.last_withdraw`.
- Thuần: `procedure/versioning.py` (`build_revision`, `can_revise`), `procedure/diff.py` (`diff_*`, `step_changes`, `format_step_note`), `procedure/approval.py` (`WITHDRAW`, `ACTIONS`; `TRANSITIONS` vẫn 7 dòng).
- Giao diện: form Desk (nút Sửa đổi, So sánh phiên bản, Thu hồi, dải đỏ lý do thu hồi); `procedure-editor` thêm `ProcedureCompare.vue` (đăng ký ở bundle, route `procedure-editor/<gốc>/compare/<so sánh>`) và ba nút khi chỉ đọc; NC Norm Set có dải vàng "Cần cập nhật", cột và bộ lọc; chuỗi mới ở `vi.csv`.

## 4. Quyền
Sửa đổi: NC Clinician, NC Department Head cùng khoa (quyền tạo và ghi DocType). Thu hồi: chỉ NC Director (`_actor_error`). So sánh/danh sách: quyền đọc theo phạm vi khoa (bản "Đã ban hành" đọc công khai); NC Auditor đọc được, không có nút ghi. Cờ bộ định mức do hệ thống đặt, trường `read_only`.

## 5. Cấu hình khi triển khai
`bench migrate` (thêm hai trường NC Norm Set) và `bench build --app normcore`.

## 6. Test case đã chạy
TC-WF-05, TC-WF-06 (tích hợp), TC-WF-07 (API; hiển thị loại M do QA kiểm), FR-WF-012 (có lý do, bị từ chối, sai trạng thái). Lệnh và kết quả ở `docs/features/FEAT-008/implementation-log.md`.

## 7. Giới hạn đã biết
- Chưa làm: UC-007 1c (đề xuất từ phân hệ D), gỡ cờ "Cần cập nhật" (FEAT-012), phục hồi bản "Đã thay thế" khi bản hiện hành bị thu hồi, so sánh trích dẫn (ASM-008-04, 06, 09, 11).
- Thu hồi không qua Frappe Workflow nên nút workflow chuẩn của Desk không có "Thu hồi"; dùng nút tùy biến.
- Giao diện SCR-DSK-011 chưa kiểm bằng trình duyệt: staging chưa có nhánh, QA không có tài khoản test; cần xem mắt trên staging sau merge. TC-WF-07 phủ bằng test API/unit.
- `ProcedureEditor.vue` không import `ProcedureCompare.vue`: component đăng ký ở `procedure_editor.bundle.js` vì harness Node của test cũ chạy khối script.
