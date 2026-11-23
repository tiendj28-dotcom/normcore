# FEAT-011 — Thiết kế giao diện

## SCR-DSK-019 Bộ tham số (form NC Costing Parameter Set)
Dùng form chuẩn Frappe, nhãn tiếng Việt theo `data-model.md`. Bố cục: mục "Tham số nhân công" (lương cơ sở, tỷ lệ đóng góp, ngày, giờ) → "Tích lũy và nghĩa vụ" → "Làm tròn, ngưỡng" → "Điện nước" → mục "Khấu hao thiết bị hết thời gian sử dụng và đối soát [1.1]" → mục "Loại chi phí tạm (TBD-14)" → bảng "Chi phí theo chức danh".
Trạng thái "Đã được dùng": banner đỏ nhạt "Bộ tham số đã được lần tính giá khóa sử dụng: chỉ đọc. Dùng Nhân bản để tạo bản sửa được." + toàn bộ trường chỉ đọc; nút chính "Nhân bản" (cần quyền tạo). Nút cũng có ở bộ chưa khóa (menu).
## NC Price Category
Form chuẩn; danh sách hiện mã, tên, cấp phê duyệt. Nhãn: Mã loại giá, Tên loại giá, Cấp phê duyệt, Có kết cấu khấu hao, Có tích lũy. Chuỗi mới vào `translations/vi.csv`.
