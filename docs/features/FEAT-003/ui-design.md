# FEAT-003 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-030; `design.md` mục 3–7. Dùng danh sách chuẩn của Desk, không trang tùy biến (ASM-067).

## SCR-DSK-030 Nhật ký — List chuẩn, chỉ đọc

| Phần | Nội dung |
| :-- | :-- |
| NC Audit Event | Cột: Thời điểm, Người thực hiện, Loại sự kiện, Bản ghi (`ref_doctype`, `ref_name`), Trước, Sau. Bộ lọc chuẩn: Bản ghi, Người, Thời điểm, Loại sự kiện. Sắp theo thời điểm tăng dần |
| NC AI Log | Có sẵn từ FEAT-000; thêm bộ lọc chuẩn Người gọi, Bản ghi liên quan, Mục đích |
| Chỉ báo | `Khóa` `orange`, `Xuất tệp` `blue`, còn lại `gray` (không màu cứng) |
| Lối vào | Workspace "Normcore": lối tắt "Nhật ký" (NC Audit Event) và "Nhật ký AI" |
| Chỉ đọc | `in_create`: không nút "Thêm". Form chỉ đọc. NC Auditor mở được, không sửa được |

| Trạng thái | Hiển thị |
| :-- | :-- |
| Rỗng, đang tải, lỗi | Chuẩn Desk |
| Không có quyền (vai trò khác) | Trang "không đủ quyền" chuẩn Desk |

Tệp: `nc_core/doctype/nc_audit_event/nc_audit_event_list.js`. Nhãn chỉ báo là giá trị tiếng Việt của `event_type`, không dùng `__()` nên không đụng `vi.csv`. Cột thêm `before_value` ở form (sự kiện "Xóa").
