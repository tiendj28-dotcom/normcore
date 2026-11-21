# As-Built: FEAT-006 Soạn quy trình có cấu trúc (thủ công)
- Phiên bản app 0.0.1; chưa nghiệm thu (PR NORM-11 đang chờ Reviewer/QA); người nghiệm thu: chưa có

## 1. Luồng nghiệp vụ đã xây
Người soạn tạo quy trình cho (dịch vụ, khoa) → bản nháp v1 có 8 phần → nhập 7 phần văn bản, thêm/sửa/xóa/sắp lại bước, khai báo nguồn lực theo bước, gắn trích dẫn tay → lưu có lịch sử; hoặc sao chép từ quy trình khác. Khác SRS: chưa gắn mục văn bản vào trích dẫn (Q1, ASM-017); tạo vào (dịch vụ, khoa) đã có bản ban hành bị từ chối (Q3, ASM-020).

## 2. DocType tạo mới hoặc thay đổi
NC Clinical Procedure thêm 13 trường (`previous_version`, `needs_review`, `doctor_request`, 7 phần văn bản, `citations`, `copied_from`, `ai_log`); NC Procedure Citation (bảng con mới). DI-02 ở controller. Không cần patch dữ liệu (chỉ thêm trường). AMD-001: `next_resource_seq`.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/procedure.py`: `list_procedures`, `find_existing`, `create_procedure`, `get_procedure`, `save_sections`, `add_step`, `update_step`, `delete_step`, `reorder_steps`, `add_resource`, `update_resource`, `delete_resource`, `suggest_catalog`, `add_citation`, `update_citation`, `delete_citation`, `copy_procedure`. Logic thuần ở `normcore/procedure/` (`codes`, `steps`, `copying`). Trang Vue `procedure-editor` (SCR-DSK-009) và chỉ báo danh sách (SCR-DSK-007). Không hook, không tác vụ nền, không fixtures mới.

## 4. Quyền và luồng trạng thái
Ma trận không đổi: Clinician, Dept Head đọc/sửa/tạo; 8 vai trò còn lại chỉ đọc; không ai xóa. Mọi hàm ghi từ chối `PermissionError` cho vai trò chỉ đọc và NC Auditor, và từ chối khi quy trình không ở "Nháp". Phạm vi theo khoa là FEAT-001.

## 5. Cấu hình cần thiết khi triển khai
Chạy `bench migrate` và `bench build --app normcore`. Không có cấu hình mới.

## 6. Test case đã chạy và kết quả
TC-PROC-01, 02, 03 (đơn vị + tích hợp), 04, 08, 09; FR-PROC-005, FR-PROC-013; quyền; Q3; DI-02; DI-07. Kết quả lệnh ở `docs/features/FEAT-006/implementation-log.md` và bình luận NORM-11.

## 7. Giới hạn đã biết và nợ kỹ thuật
- Trích dẫn chưa có `legal_section`; DI-08 và quy tắc BB chờ FEAT-020.
- Gợi ý danh mục chỉ cho NC Job Title (ASM-019).
- Giao diện chưa chụp màn hình 1366 × 768 (cần staging).
- Phạm vi khoa chưa áp (FEAT-001); gửi duyệt và kiểm FR-PROC-008/012 ở FEAT-007.
- Hàm `add_step`, `remove_step`, `move` trong `procedure/steps.py` mới chỉ được test dùng (API dùng `reorder`, controller dùng `next_code`); giữ làm logic thuần cho FEAT-008 và FEAT-024.
