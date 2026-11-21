# FEAT-004 — Thiết kế giao diện: SCR-DSK-031 (nhập Excel)

Desk Page `import-excel` "Nhập dữ liệu từ Excel", vào từ workspace Normcore (shortcut). Luồng: chọn danh mục → "Tải tệp mẫu" → "Tải tệp lên" (chỉ `.xlsx`, tệp riêng tư) → "Kiểm tra" (chế độ thử) → xem số tạo/cập nhật/không đổi/lỗi và bảng lỗi (Dòng, Cột, Thông báo) → "Xác nhận ghi" → xem kết quả.

Trạng thái: chưa chọn tệp (Kiểm tra, Xác nhận tắt); đã tải lên (Kiểm tra bật); đã kiểm tra chính tệp đó (Xác nhận ghi bật; đổi danh mục hoặc tệp thì tắt lại). Không có quyền: thông báo, không có danh mục.
Quy ước: chuỗi qua `__()` + `vi.csv`; không mã màu; chỉ dùng thành phần Desk (page, field, bảng Bootstrap), chạy được 1366 × 768; chỉ gọi API ở `normcore.api.importer`.
