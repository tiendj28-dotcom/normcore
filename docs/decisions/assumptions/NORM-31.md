# Giả định của NORM-31 (chống conflict khi merge)

Theo ASM-NORM32-02: mỗi issue một tệp trong `docs/decisions/assumptions/`. Mã gắn tiền tố feature (Lead duyệt trên NORM-31). Trước đổi mã: ASM-131 → ASM-004-01, ASM-132 → ASM-016-01.

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-004-01 | — | FEAT-004 (NORM-31), SCR-DSK-031 | Trang `import-excel` đọc khóa bộ nhập từ `frappe.route_options.import_set` (Frappe v15 nạp cả đối số object của `set_route` lẫn query `?import_set=` vào đây) ở `on_page_show`; dùng xong đặt `frappe.route_options = null`. Khóa phải nằm trong kết quả `list_import_sets` (đã lọc quyền tạo); khóa sai hoặc không có quyền thì bỏ qua im lặng, chọn bộ đầu như cũ. | `nc_core/page/import_excel/import_excel.js::apply_route_options`, `preselect` | Áp dụng theo CLAUDE.md mục 6; phạm vi theo Quyết định Lead trên NORM-31 (phương án 1) |
| ASM-016-01 | — | FEAT-016 (NORM-31), SCR-DSK-020, TC-ACCT-04 | Nút "Sửa loại chi phí của một dòng" đòi đúng một dòng được tích trong bảng Dòng; 0 dòng hoặc từ 2 dòng → thông báo, không mở hộp thoại (bỏ cách tự lấy dòng 1). Tiêu đề hộp thoại ghi số thứ tự dòng (`idx`) và mã tài khoản. | `nc_costing/doctype/nc_accounting_import/nc_accounting_import.js` | Áp dụng theo CLAUDE.md mục 6 (phương án đơn giản nhất, đảo ngược được) |
