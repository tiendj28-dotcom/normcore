# As-Built: FEAT-000 Walking skeleton
- Phiên bản app 0.0.1, ngày nghiệm thu 2026-11-21, người nghiệm thu: QA (Multica) và người duyệt PR

## 1. Luồng nghiệp vụ đã xây
Dịch vụ kỹ thuật → quy trình một bước, một nguồn lực nhân lực (NC Clinical Procedure) → "Đã ban hành" → bộ định mức (`make_norm_set`, mỗi nguồn lực Nhân lực thành một dòng LABOR) → "Đã khóa" → lần tính giá (NC Costing Run, `run_costing`) → NC Service Cost có một dòng LABOR truy về mã bước (`step_id`) và mã dòng định mức (`norm_line_id`).
Khác SRS/kế hoạch: luồng có thêm bước khóa bộ định mức vì DI-06 và FR-COST-002 (CF-001, ASM-010); lần tính chạy cho mọi bộ "Đã khóa" trên site (ASM-004).

## 2. DocType tạo mới hoặc thay đổi
NC Department, NC Job Title, NC Job Title Rate (bảng con), NC Costing Parameter Set, NC Technical Service, NC Clinical Procedure (+ bảng con NC Procedure Step, NC Procedure Resource), NC Norm Set (+ NC Norm Line), NC Costing Run, NC Service Cost (+ NC Service Cost Line), NC AI Log. Rút gọn so với `data-model.md`: ASM-003, ASM-004, ASM-005.

## 3. API, tác vụ nền, hook, fixtures
Phương thức gọi được qua REST: `publish` (NC Clinical Procedure), `lock` (NC Norm Set), `run_costing` (NC Costing Run) qua `run_doc_method`; `normcore.nc_costing.doctype.nc_norm_set.nc_norm_set.make_norm_set`. Vai trò tạo trong `before_install`/`after_install` và patch `ensure_base_data` (ASM-016). Cấu hình AI đọc từ `site_config.json` (ASM-006).

## 4. Quyền và luồng trạng thái
Quy trình: Nháp → Đã ban hành (ASM-012). Bộ định mức: Nháp → Đã khóa, chỉ NC Finance (ASM-010). Lần tính: Nháp → Đang tính → Đã tính / Tính lỗi. Quyền theo `data-model.md` mục 4; không vai trò nào có quyền xóa (ASM-015).

## 5. Cấu hình cần thiết khi triển khai
Smoke cần ba biến môi trường `SMOKE_URL`, `SMOKE_API_KEY`, `SMOKE_API_SECRET` (chỉ ghi tên). Người dùng API của smoke cần bốn vai trò: NC Document Controller, NC Clinician, NC Director, NC Finance.

## 6. Test case đã chạy và kết quả
- Smoke staging `python3 scripts/smoke_feat000.py` (3 lượt liên tiếp, đều thoát 0). Dòng cuối mỗi lượt: `SMOKE FEAT-000: ĐẠT`; dòng LABOR: `step_id=S001 norm_line_id=L001 applied_qty=10.0 unit_rate=59644.8864 amount=9940.81`, `direct_labor=9940.81`, `calc_status=Thành công`. Thiếu `SMOKE_URL` thì thoát 2 kèm thông báo.
- Đã chạy ở NORM-7: TC-PROC-03, TC-PROC-04, TC-NORM-02, dòng L01, L03, L04, L09 (bằng chứng ở bình luận NORM-7).

## 7. Giới hạn đã biết và nợ kỹ thuật
- Giả định ASM-003 đến ASM-016 và xung đột CF-001 (xem `docs/decisions/`).
- Hai thao tác tạm "Ban hành" (ASM-012) và "Khóa" (ASM-010).
- Dữ liệu smoke không xóa được trên staging (ASM-015, DI-07): mỗi lượt để lại một dịch vụ, bộ tham số, quy trình, bộ định mức, lần tính; cần dọn tay trước UAT.
- Skeleton chưa có nút nào trên form: `publish`, `make_norm_set`, `lock`, `run_costing` chỉ gọi được qua REST. Nút "Ban hành" do FEAT-007 thay bằng Workflow, "Khóa" thuộc FEAT-012, "Chạy tính giá" thuộc FEAT-015.
