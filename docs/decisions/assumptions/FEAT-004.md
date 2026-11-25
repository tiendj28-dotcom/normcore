# Giả định của FEAT-004 (chống conflict khi merge)

Theo ASM-NORM32-02: mỗi FEAT một tệp trong `docs/decisions/assumptions/`. Mã dưới đây phát sinh ở NORM-31 (Lead duyệt); trước đổi mã là ASM-131.

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-004-01 | — | FEAT-004 (NORM-31), SCR-DSK-031 | Trang `import-excel` đọc khóa bộ nhập từ `frappe.route_options.import_set` (Frappe v15 nạp cả đối số object của `set_route` lẫn query `?import_set=` vào đây) ở `on_page_show`; dùng xong đặt `frappe.route_options = null`. Khóa phải nằm trong kết quả `list_import_sets` (đã lọc quyền tạo); khóa sai hoặc không có quyền thì bỏ qua im lặng, chọn bộ đầu như cũ. | `nc_core/page/import_excel/import_excel.js::apply_route_options`, `preselect` | Áp dụng theo CLAUDE.md mục 6; phạm vi theo Quyết định Lead trên NORM-31 (phương án 1) |
