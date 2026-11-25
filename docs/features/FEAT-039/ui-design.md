# FEAT-039 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-030 ("Chỉ đọc. **[1.1]** NC Auditor truy cập được"); `design.md`; `technical-design.md`. FEAT này **không thêm màn hình, không đổi bố cục**: SCR-DSK-030 đã xây ở FEAT-003 (List chuẩn NC Audit Event, NC AI Log) và NC Auditor đã đọc được. Phần việc giao diện là kiểm, không vẽ mới. Mọi quyền do máy chủ quyết; ẩn hiện nút chỉ là tiện ích.

## SCR-DSK-030 Nhật ký — List chuẩn, chỉ đọc (đã có)

Hiện thực: List + Form chuẩn Desk của NC Audit Event và NC AI Log (`nc_core/doctype/nc_audit_event/nc_audit_event_list.js`). Lối vào: Workspace "Normcore", lối tắt "Nhật ký", "Nhật ký AI" (Workspace không giới hạn vai trò; NC Auditor có `desk_access`).

| Trạng thái | Với người chỉ có NC Auditor |
| :-- | :-- |
| Danh sách | Thấy mọi sự kiện, mọi khoa; bộ lọc chuẩn Bản ghi, Người, Thời điểm, Loại sự kiện; sắp theo thời điểm tăng dần (FR-AUD-003) |
| Form | Chỉ đọc chuẩn Desk; không nút "Lưu", "Xóa", "Nhân bản"; menu không có "Xóa" |
| Rỗng, đang tải, lỗi | Chuẩn Desk |
| Không có quyền | Vai trò ngoài NC Director, NC Admin, NC Auditor: trang "không đủ quyền" chuẩn Desk (không đổi) |
| Xem dạng báo cáo, xuất, in | Không có (chỉ cờ `read`, ASM-132); menu Desk tự ẩn |

## Các màn hình khác khi mở bằng NC Auditor (UC-026 bước 1)

Không đổi mã. Desk tự hiển thị form chỉ đọc khi vai trò chỉ có `read`. Các nút tùy biến đã kiểm quyền trước khi hiện:

| Màn hình / form | Nút tùy biến | Điều kiện hiện hiện có | Kết quả với Auditor |
| :-- | :-- | :-- | :-- |
| NC Norm Set | "Lock" | `has_role("NC Finance")` | Ẩn |
| NC Clinical Procedure | "Publish"; "Create norm set"; "Open editor" | `has_role("NC Director")`; `can_create("NC Norm Set")`; luôn | Ẩn; ẩn; hiện — trình soạn mở chỉ đọc (`get_procedure.can_edit` = false) |
| NC Costing Run | "Run costing"; "View costing results" | `frm.perm[0].write`; luôn | Ẩn; hiện (đọc) |
| NC Costing Parameter Set | "Duplicate" | `frm.perm[0].create` | Ẩn |
| NC Item | "Add price" | `can_create("NC Item Price")` | Ẩn |
| NC Item Price | "Verify" | `can_write("NC Item Price")` | Ẩn |
| NC Department | "Assign user" | `has_role("NC Admin")` | Ẩn |
| NC Test System | "Deactivate" / "Reactivate" | `frm.perm[0].write` | Ẩn |
| Trang `import-excel` | Chọn bộ nhập | Danh sách bộ theo quyền | Không có bộ nào; hiện trạng thái rỗng chuẩn của trang |

Người có NC Auditor cùng vai trò khác thấy nút của vai trò kia (ASM-133).

## Kiểm (T06, ghi vào implementation-log)

1. Đăng nhập người chỉ có NC Auditor trên `normcore.test` (hoặc staging): mở Workspace "Normcore", lối tắt "Nhật ký", lọc theo một quy trình → danh sách theo thời gian tăng dần.
2. Mở lần lượt mỗi form ở bảng trên: không có nút ghi, form chỉ đọc; trình soạn quy trình không cho sửa.
3. 1366 × 768: danh sách và form chuẩn Desk không tràn ngang.
4. Bàn phím, tương phản (NFR-USE-004): màn hình chuẩn Desk, không trang tùy biến mới; không thêm màu cứng.
5. Chuỗi: FEAT này không thêm chuỗi giao diện; nếu T04 sửa thông báo lỗi máy chủ thì viết tiếng Việt qua `_()`.

Không cần task giao diện mới ngoài T06 trong `tasks.md`.
