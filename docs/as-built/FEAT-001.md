# As-Built: FEAT-001 Vai trò, khoa, trung tâm chi phí, phạm vi theo khoa
- Phiên bản app 0.0.1, ngày nghiệm thu: chờ QA, người nghiệm thu: chờ QA và người duyệt PR

## 1. Luồng nghiệp vụ đã xây
NC Admin khai báo khoa và trung tâm chi phí, gán người dùng vào khoa; Clinician / Dept Head chỉ sửa quy trình và bộ định mức của khoa được gán, đọc được quy trình "Đã ban hành" của mọi khoa. Khác SRS: Q3 (ASM-028) thu hẹp quyền đọc bản nháp và bộ định mức của khoa khác.

## 2. DocType tạo mới hoặc thay đổi
NC Cost Center (mới); NC Department thêm `cost_center`; quyền xóa NC Admin trên NC Department, NC Cost Center, NC Job Title, NC Technical Service.

## 3. API, tác vụ nền, hook, fixtures
`normcore.api.access.assign_department / unassign_department / list_department_users`; hook `has_permission`, `permission_query_conditions` (NC Clinical Procedure, NC Norm Set); `doc_events.on_trash` cho bốn danh mục; patch `add_cost_center_to_departments`.

## 4. Quyền và luồng trạng thái
Ma trận mục 4 + G1 cho NC Cost Center; quét tự động NC-07, NC-08.

## 5. Cấu hình cần thiết khi triển khai
Sau migrate, NC Admin kiểm tra trung tâm chi phí do patch tạo (mã khoa) và sửa cho khớp tệp kế toán thật trước FEAT-016 (ASM-030); gán khoa cho người dùng hiện có, nếu không họ không sửa được gì (G5).

## 6. Test case đã chạy và kết quả
TC-ACC-01..05, TC-ADM-04, TC-ADM-05, FR-ACC-006: xanh trên `norm12.test` (toàn app 110 test OK). Chờ log migrate staging.

## 7. Giới hạn đã biết và nợ kỹ thuật
ASM-026..ASM-034. Số liệu kế toán của NC Consultant "cấp riêng" để FEAT-016; ô "A (khoa)" để FEAT-007, FEAT-012; người có vai trò khác cấp quyền đọc thì thấy mọi khoa.
