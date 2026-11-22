# FEAT-006 — Thiết kế giao diện

Căn cứ: `ux-foundations.md` (SCR-DSK-007, SCR-DSK-009, bảng thành phần), `design.md` mục 2–5, 7, ADR-010. Chiến lược code-native, không dùng công cụ thiết kế ngoài.

## SCR-DSK-007 Danh sách quy trình
- **Loại**: List chuẩn của Desk cho NC Clinical Procedure (không viết mã giao diện mới ngoài `listview_settings`).
- **Cột**: tên, dịch vụ, khoa, phiên bản, trạng thái (đã `in_list_view`); lọc chuẩn: Trạng thái, Khoa, Cần rà soát (`in_standard_filter`).
- **Chỉ báo** trạng thái: Nháp = xám, Đã ban hành = xanh. Nút "Mở trình soạn" trên form (đã có).
- **Trạng thái**: rỗng (Desk có sẵn), không có quyền (Desk 403), chỉ đọc (NC Auditor không thấy nút Mới).

## SCR-DSK-009 Trình soạn quy trình (Desk Page `procedure-editor`, Vue 3)
**Bố cục** (1366 × 768, hai cột: nội dung 2fr | bảng trích dẫn 1fr; dưới 900px xếp một cột):
1. Thanh trên: ô chọn quy trình; nút "Tạo quy trình" (dịch vụ, khoa); nút "Sao chép từ…".
2. Tiêu đề: tên, nhãn trạng thái, dải thông báo khi không sửa được ("Quy trình đã ban hành, chỉ đọc" / "Bạn chỉ có quyền xem").
3. Cột trái: 8 phần cố định theo thứ tự FR-PROC-001. Bảy phần là ô văn bản + nút "Lưu phần"; phần "Các bước tiến hành" là danh sách thẻ bước.
4. **Thẻ bước**: mã bước (chữ đậm), giai đoạn, tên, mô tả; nút "Lên", "Xuống", "Sửa", "Xóa"; chọn thẻ = chọn bước đang xét. Dưới thẻ: bảng nguồn lực của bước (loại, tên, số lượng, đơn vị, số người) với "Thêm nguồn lực", "Sửa", "Xóa"; ô tên có gợi ý chức danh (datalist) và cho để trống liên kết. Nhân lực: ô đơn vị chỉ đọc "phút", nhãn số lượng "Số phút / người", ô "Số người".
5. Cột phải: **bảng trích dẫn** của phần hoặc bước đang chọn; mỗi dòng có nhãn quan hệ **chữ + màu** (Theo hướng dẫn = xanh, Khác biệt = cam, Chưa có căn cứ = đỏ), đoạn trích, lý do khác biệt; "Thêm trích dẫn", "Sửa", "Xóa". Mỗi dòng hiện văn bản và mục (Data tạm, ASM-046; FEAT-020 đổi sang Link).

**Trạng thái**: đang tải (chữ "Đang tải…"); rỗng (chưa chọn quy trình; chưa có bước; chưa có nguồn lực/trích dẫn); lỗi (dải đỏ có chữ, `role="alert"`); không quyền (nút ghi ẩn, dải thông báo); chỉ đọc (NC Auditor, Đã ban hành: toàn bộ điều khiển ghi ẩn, văn bản dùng `readonly`).

**API cho từng hành động**: chọn → `list_procedures`, `get_procedure`; tạo → `create_procedure` (lỗi → `find_existing` để hiện liên kết tới bản có sẵn); lưu phần → `save_sections`; bước → `add_step`/`update_step`/`delete_step`/`reorder_steps`; nguồn lực → `add_resource`/`update_resource`/`delete_resource`, gợi ý → `suggest_catalog`; trích dẫn → `add_citation`/`update_citation`/`delete_citation`; sao chép → `copy_procedure`. Trình duyệt không ghi thẳng DocType.

**Bàn phím và tiếp cận (NFR-USE-004)**: Tab đi qua mọi điều khiển theo thứ tự trực quan; Enter gửi biểu mẫu đang mở; Esc đóng biểu mẫu thêm/sửa; sắp lại bước bằng nút Lên/Xuống (không cần kéo chuột), sau khi sắp tiêu điểm ở lại nút vừa bấm; viền focus `outline: 2px solid var(--primary)` nhìn thấy; chỉ dùng biến CSS của Desk (`--text-color`, `--text-muted`, `--border-color`, `--card-bg`, `--primary`, `--red-600`, `--green-800`, `--orange-700`; nhãn quan hệ dùng ba màu này, đo trên nền trắng: 5,36 / 5,42 / 5,44) đạt tương phản ≥ 4,5:1 ở giao diện sáng; nhãn quan hệ luôn kèm chữ, không chỉ màu; nút icon có `aria-label`.

**Chuỗi**: mọi chuỗi qua `__()`, nguồn tiếng Anh, bản dịch ở `normcore/translations/vi.csv` (quy ước FEAT-000); `test_ui_conventions` kiểm mọi chuỗi có bản dịch và không có mã màu cứng.
**Kiểm 1366 × 768**: hai cột không tràn ngang; kiểm bằng ảnh chụp sau khi deploy staging (do người duyệt/QA, theo "Xong khi").
