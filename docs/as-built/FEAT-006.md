# As-Built: FEAT-006 Soạn quy trình có cấu trúc (thủ công)
- Phiên bản app 0.0.1; Dev: NORM-11, NORM-15, NORM-22, NORM-23, NORM-27; nghiệm thu: QA (Multica), NORM-16, 2026-11-23

## 1. Luồng nghiệp vụ đã xây
Người soạn tạo quy trình cho (dịch vụ, khoa) → bản nháp v1 có 8 phần → nhập 7 phần văn bản, thêm/sửa/xóa/sắp lại bước, khai báo nguồn lực theo bước, gắn trích dẫn tay → lưu có lịch sử; hoặc sao chép từ quy trình khác. Trích dẫn lưu văn bản và mục dưới dạng Data tạm (ASM-017, ASM-046; FEAT-020 đổi sang Link); tạo vào (dịch vụ, khoa) đã có bản ban hành bị từ chối (Q3, ASM-020).

## 2. DocType tạo mới hoặc thay đổi
NC Clinical Procedure thêm 13 trường (`previous_version`, `needs_review`, `doctor_request`, 7 phần văn bản, `citations`, `copied_from`, `ai_log`); NC Procedure Citation (bảng con mới; có `legal_document`, `legal_section` Data tạm, ASM-046). DI-02 ở controller. Không cần patch dữ liệu (chỉ thêm trường). AMD-001: `next_resource_seq`.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/procedure.py`: `list_procedures`, `find_existing`, `create_procedure`, `get_procedure`, `save_sections`, `add_step`, `update_step`, `delete_step`, `reorder_steps`, `add_resource`, `update_resource`, `delete_resource`, `suggest_catalog`, `add_citation`, `update_citation`, `delete_citation`, `copy_procedure`. Logic thuần ở `normcore/procedure/` (`codes`, `steps`, `copying`). Trang Vue `procedure-editor` (SCR-DSK-009) và chỉ báo danh sách (SCR-DSK-007). Không hook, không tác vụ nền, không fixtures mới.

## 4. Quyền và luồng trạng thái
Ma trận không đổi: Clinician, Dept Head đọc/sửa/tạo; 8 vai trò còn lại chỉ đọc; không ai xóa. Mọi hàm ghi từ chối `PermissionError` cho vai trò chỉ đọc và NC Auditor, và từ chối khi quy trình không ở "Nháp". Phạm vi theo khoa đã áp ở FEAT-001 (người dùng phải được gán khoa). Trên giao diện, NC Auditor không thấy nút "Tạo quy trình", "Sao chép" và mọi nút ghi (kiểm bằng Playwright trên staging).

## 5. Cấu hình cần thiết khi triển khai
Chạy `bench migrate` và `bench build --app normcore`. Không có cấu hình mới.

## 6. Test case đã chạy và kết quả
TC-PROC-01, 02, 03 (đơn vị + tích hợp), 04, 08, 09; FR-PROC-005, FR-PROC-013; quyền; Q3; DI-02; DI-07. Kết quả lệnh ở `docs/features/FEAT-006/implementation-log.md` và bình luận NORM-11.

## 7. Giới hạn đã biết và nợ kỹ thuật
- Trích dẫn có `legal_document` và `legal_section` (Data tạm, ASM-046). Chờ FEAT-020: đổi sang Link NC Legal Document / NC Legal Section, DI-08 và quy tắc BB "trừ khi Chưa có căn cứ".
- Gợi ý danh mục chỉ cho NC Job Title (ASM-019).
- Giao diện đã kiểm bằng Playwright trên staging ở 1366 × 768, ngôn ngữ `vi` (L, E, G, U, K, C đều đạt; NORM-16). Khi xóa dòng nguồn lực bằng bàn phím trong cùng phiên, console có một yêu cầu `delete_resource` lặp (417), kết quả hiển thị đúng; nên điều tra ở FEAT sau.
- Gửi duyệt và kiểm FR-PROC-008/012 ở FEAT-007.
- Hàm `add_step`, `remove_step`, `move` trong `procedure/steps.py` mới chỉ được test dùng (API dùng `reorder`, controller dùng `next_code`); giữ làm logic thuần cho FEAT-008 và FEAT-024.
