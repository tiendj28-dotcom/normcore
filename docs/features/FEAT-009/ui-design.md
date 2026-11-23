# FEAT-009 — Thiết kế giao diện: SCR-DSK-017 Mặt hàng và đơn giá

Loại: Form và List chuẩn của Desk (code-native), thêm JS; không Desk Page Vue.

## NC Item (form)
Bố cục: mã, tên, loại | đơn vị tính, số lần dùng, đang dùng, thanh toán riêng, nhóm tương đương; phần "Đơn vị định mức" (đơn vị định mức, số đơn vị trong một đơn vị mua, số test danh nghĩa, hạn dùng sau mở, hóa chất chính); phần "Đơn giá có chứng từ" (HTML `price_history_html`, chỉ khi đã lưu).
Thẻ: dòng "Đơn giá đang dùng hôm nay" (nguồn, cảnh báo cam: quá hạn tham chiếu, chưa xác minh), "Đơn giá một đơn vị định mức"; bảng lịch sử đơn giá (nguồn, đơn giá 4 số lẻ, số chứng từ, hiệu lực từ/đến, nhãn Đã/Chưa xác minh). Nút "Thêm đơn giá" khi có quyền tạo. API: `get_effective_price`, `frappe.db.get_list`.
Trạng thái: chưa có giá → "Chưa có đơn giá"; không quyền đọc → Desk tự từ chối; NC Auditor chỉ đọc, không thấy nút thêm.

## NC Item Price (form, danh sách)
Form: mặt hàng, đơn giá, nguồn, số và ngày chứng từ | hiệu lực từ/đến; phần "Xác minh": tệp chứng từ, trạng thái, người, thời điểm (chỉ đọc). Dòng đầu form: nhãn xanh "Đã xác minh" hoặc cam "Chưa xác minh"; nút "Xác minh" (chỉ khi chưa xác minh, có quyền ghi, form không sửa dở) gọi `verify_price`; thiếu tệp → thông báo lỗi của máy chủ.
Danh sách: chỉ báo xanh/cam theo trạng thái xác minh, bộ lọc theo mặt hàng, nguồn, trạng thái.

## Kiểm
Chuỗi qua `__()` có bản dịch ở `vi.csv` (test `test_item_ui_conventions.py`); không mã màu cứng, dùng chỉ báo của Desk (tương phản NFR-USE-004 theo theme); dữ liệu chèn vào HTML qua `escape_html`; bảng cuộn ngang ở 1366 × 768 theo Desk. Chưa kiểm trên trình duyệt (preview lỗi site như FEAT-005, xem implementation-log).
