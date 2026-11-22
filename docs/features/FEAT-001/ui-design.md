# FEAT-001 UI design: SCR-DSK-031 (phần khoa, trung tâm chi phí)

Kiểu L + F theo `docs/ux-foundations.md`; `docs/design.md` không có chi tiết riêng, dùng danh sách và form chuẩn của Desk (biến CSS của Desk, không mã màu cứng), chạy được ở 1366 × 768.

- **Danh sách NC Department**: cột Tên khoa, Loại, Trung tâm chi phí. **Danh sách NC Cost Center**: Tên, Loại.
- **Form NC Department** (chỉ NC Admin thấy nút): nút "Gán người dùng" mở hộp thoại chọn User; dải đầu form liệt kê "Người dùng được gán vào khoa" kèm liên kết "Bỏ gán". Trống thì hiện "Chưa gán người dùng nào."
- Trạng thái: thiếu trường bắt buộc → thông báo của Frappe, nhãn tiếng Việt; xóa danh mục đang tham chiếu → thông báo nêu bản ghi tham chiếu.
- Chuỗi giao diện qua `__()`, có trong `normcore/translations/vi.csv`; test `tests/unit/test_department_form_i18n.py`.
- Ngoài phạm vi: NC Settings, tham số vận hành (FEAT-002); tệp mẫu Excel (FEAT-004).
