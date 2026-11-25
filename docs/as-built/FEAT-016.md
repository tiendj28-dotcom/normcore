# As-Built: FEAT-016 Số liệu kế toán, sản lượng, quy tắc phân bổ

Issue NORM-28. FR-ACCT-001..011, UC-011, SCR-DSK-020, SCR-DSK-021. TC-ACCT-01..09. Người nghiệm thu: QA (Multica). Ngày nghiệm thu: 2026-11-23.

## 1. Luồng nghiệp vụ đã xây
1. NC Finance tạo NC Accounting Import (năm, chế độ kế toán, tệp .xlsx theo mẫu: mã TK, tên TK, mã trung tâm chi phí, số tiền). Lưu → máy chủ đọc tệp, tạo dòng, gán loại chi phí theo NC Account Mapping (tiền tố dài nhất), trạng thái "Nháp".
2. Lỗi mức tệp (không phải .xlsx, thiếu cột, rỗng, quá 5.000 dòng): không tạo bản ghi. Lỗi dòng (thiếu mã TK, số tiền không phải số, trung tâm lạ): tạo "Nháp", lỗi lưu ở `import_errors`, `error_count` > 0 chặn chốt.
3. Sửa loại chi phí hoặc loại trừ một dòng cần lý do; lưu người sửa. "Gán lại theo bảng ánh xạ" giữ dòng sửa tay; "Đọc lại tệp" thay toàn bộ dòng.
4. Chốt: từ chối khi còn dòng lỗi, không có dòng, hoặc dòng không loại trừ chưa có loại (thông báo nêu dòng, tài khoản, trung tâm). Hợp lệ: ghi bảng `totals` theo (trung tâm, loại), status "Đã chốt", sự kiện "Khóa"; sau đó không sửa, không xóa, không mở lại (DI-07).
5. Lần nhập thứ hai cùng năm là bản ghi mới `KT-2026-02`, lần cũ giữ nguyên (FR-ACCT-011).
6. Sản lượng, tiêu chí, ánh xạ nạp bằng khung nhập FEAT-004 (bộ `nc_service_volume`, `nc_cost_center_driver`, `nc_account_mapping`).
Khác SRS/data-model: AMD-010 thêm `line_count`, `error_count`, `import_errors` và bảng con `totals` (đã áp vào `docs/data-model.md`).

## 2. DocType
- NC Accounting Import (+ bảng con NC Accounting Import Line, NC Accounting Import Total), NC Account Mapping, NC Service Volume (duy nhất theo năm, dịch vụ, khoa, kịch bản), NC Cost Center Driver (duy nhất theo năm, trung tâm), NC Allocation Rule. Tổng 5 DocType cha, 2 bảng con.
- Logic thuần: `costing/accounting.py`, `costing/allocation_rules.py` (phủ 100%, không phụ thuộc framework). `get_driver_values` (NC Cost Center Driver) và `driver_shares` cho FEAT-017; tỷ lệ K01 = 20 ÷ 50 = 0,4 khớp golden.

## 3. API, hook, fixtures
- `normcore/api/accounting.py`: `get_import_summary`, `update_line`, `reapply_mapping`, `reload_file`, `finalize`, `download_template`.
- Khung nhập (ASM-124): `ImportSet.key_fields`, `parse(unique=False)`, `ImportFileError`; bộ nhập cũ không đổi hành vi.
- `install.ensure_default_account_mapping` (after_install) và patch `add_default_account_mapping`: 13 dòng chế độ Hành chính sự nghiệp, ghi "Giả định — chờ xác nhận (TBD-03)" (ASM-118); chỉ chèn dòng thiếu.
- `core/audit.py`: `NC Accounting Import.status` là trường trạng thái; "Đã chốt" ghi sự kiện "Khóa".

## 4. Quyền và trạng thái
- Cả 5 DocType: NC Finance đọc/ghi/tạo; NC Director, NC Admin, NC Auditor chỉ đọc; vai trò khác không có quyền; không ai xóa (ASM-128). NC Consultant "cấp riêng" (FR-ACC-004) ngoài phạm vi.
- Trạng thái: Nháp → Đã chốt (chỉ qua API `finalize`).

## 5. Cấu hình khi triển khai
Bảng ánh xạ mặc định là giả định: chuyên gia kế toán thay bằng bộ nhập `nc_account_mapping` hoặc sửa trên form. Chưa có bảng cho chế độ "Doanh nghiệp".

## 6. Test case đã chạy
TC-ACCT-01..09 có test cùng mã (`test_TC_ACCT_NN_*`) ở `test_nc_accounting_import.py`, `test_nc_account_mapping.py`, `test_nc_service_volume.py`, `test_nc_cost_center_driver.py`, `test_nc_allocation_rule.py`, `api/test_importer_accounting.py`, `tests/unit/test_accounting.py`, `tests/golden/test_accounting_golden.py`. Kết quả ở `implementation-log.md`. Test cũ đổi theo Quyết định Lead (ASM-128): `tests/test_permissions.py` 30 → 37, `api/test_importer.py` danh sách Finance.

## 7. Giới hạn đã biết
- Phân bổ cấp 1, cấp 2, đối soát: FEAT-015, FEAT-017. Sản lượng cận lâm sàng: FEAT-035. Chưa nối `NC Costing Run.accounting_import` (ASM-004).
- Giao diện chưa kiểm bằng trình duyệt (chỉ kiểm quy ước, build và API); QA không có tài khoản test theo vai trò. Trang `import-excel` chưa đọc tham số `import_set` nên nút "Nhập từ Excel" chỉ mở trang.
- Gộp với FEAT-033: giữ dòng cả hai bên ở `hooks.py`, `check_conventions.py`, `vi.csv`, `assumptions.md`; đếm lại DocType theo thực tế.
