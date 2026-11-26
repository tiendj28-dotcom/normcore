# FEAT-013 — Thiết kế giao diện

Màn hình: SCR-DSK-014 Lưới định mức (Desk Page `norm-grid`, Vue 3, đã có từ FEAT-012 — **mở rộng**), và một thay đổi nhỏ ở form NC Norm Set (SCR-DSK-013, Desk chuẩn). Không màn hình mới. Hợp đồng API: `technical-design.md` mục 3. Chuỗi trong mã viết tiếng Anh qua `__()` như FEAT-012, bản dịch tiếng Việt ở `vi.csv` (cột phải dưới đây là nhãn tiếng Việt hiển thị).

Màu chỉ báo giữ FEAT-012 (design.md mục 3); thêm: "Bước đã bỏ" `red`; "Bước chưa có dòng" `orange`. Mọi nhãn màu luôn kèm chữ.

## SCR-DSK-014 Lưới định mức — phần thêm

**1. Đầu trang — nút "Tạo phiên bản theo quy trình mới"**
- Hiện khi `actions` có `new_version` **và** `doc.newer_procedure` có giá trị: nhãn "Tạo phiên bản theo quy trình mới" (`btn-primary`; ở bộ "Nháp" là `btn-default` đặt sau "Xác nhận chuyên môn" để không tranh nút chính). Không có `newer_procedure` thì giữ nút "Tạo phiên bản mới" của FEAT-012 (chỉ ở "Đã khóa").
- Cạnh nhãn "Cần cập nhật" (đã có) thêm liên kết "Quy trình mới: <newer_procedure>" mở form quy trình.
- Bấm: `frappe.confirm` "Tạo bộ nháp phiên bản n+1 theo quy trình <newer_procedure>? Dòng của bước còn tồn tại được mang sang; dòng của bước đã bỏ được đánh dấu để xử lý." → `new_version(norm_set)`.
  - `existing` = 1: `frappe.msgprint` chữ máy chủ ("Đã có bộ định mức đang soạn theo quy trình …") + nút "Mở bộ đó" → `norm-grid/<name>`.
  - Thành công: hộp thoại kết quả "Đã tạo <name>" ba dòng: "Mang sang: n dòng (S001, S003, S004)", "Bước đã bỏ: n dòng (S002) — cần xử lý", "Bước chưa có dòng: S005"; nút "Mở lưới" (mặc định, focus) → `norm-grid/<name>`.
  - Lỗi (403 hoặc ValidationError): `frappe.msgprint` chữ máy chủ; lưới giữ nguyên.

**2. Dải "Thay đổi theo quy trình mới"** (chỉ ở bộ "Nháp" có `previous_version` và có dòng `step_removed` hoặc `steps_without_lines` khác rỗng; `role="status"`, nền `--bg-yellow`/biến cảnh báo của Desk, đặt dưới dải thông báo FEAT-012):
- Tiêu đề "Bộ này tạo theo quy trình <procedure>, từ <previous_version>."
- "Bước đã bỏ: n dòng" + nhãn `red` "Bước đã bỏ" + nút "Xem các dòng này" (cuộn tới nhóm "Bước đã bỏ", mở nhóm, focus hàng nhóm). Hướng dẫn `--text-muted`: "Gán bước khác, chuyển Chung cho cả dịch vụ hoặc xóa trước khi xác nhận chuyên môn."
- "Bước chưa có dòng:" danh sách chip `orange` "S005 · <tên bước>"; mỗi chip là nút mở "Thêm dòng" với "Gắn với" điền sẵn bước đó (có `save_line`); không có quyền sửa thì chip chỉ là chữ.
- Hết dòng có cờ và hết bước thiếu → dải ẩn (vẽ lại sau mỗi `save_line`/`delete_line`).

**3. Lưới — nhóm "Bước đã bỏ"** (từ `groups` có `removed` = true; đặt sau các bước của quy trình, trước "Chung cho cả dịch vụ"):
- Hàng nhóm: "Bước đã bỏ" + nhãn `red`, số dòng, tổng tạm tính; mặc định mở.
- Mỗi hàng dòng: cột Mã dòng thêm nhãn `red` "Bước đã bỏ: S002" (tooltip "Bước S002 không còn trong quy trình <procedure>"); ô Xác nhận không có nút "Xác nhận", thay bằng chữ `--text-muted` "Cần gán bước".
- Bảng chi tiết dòng (FEAT-012 mục 5) với dòng có cờ: hiện ô "Gắn với" (chọn `S### · tên` của quy trình mới hoặc "Chung cho cả dịch vụ", bắt buộc) kể cả khi dòng lấy từ quy trình; đổi → `save_line(norm_set, values={step_id, service_level}, line_id)`; thành công thì dòng chuyển sang nhóm mới, `frappe.show_alert` "Đã chuyển Lxxx sang S003". Nút "Xóa dòng" hiện cho dòng có cờ (có `delete_line`): xác nhận "Xóa dòng Lxxx của bước đã bỏ?" → `delete_line`.
- Bộ lọc "Chỉ dòng cần xử lý" (FEAT-012) gồm cả dòng có cờ.

**4. Hộp từ chối "Xác nhận chuyên môn"** (FEAT-012): lý do "Thuộc bước đã bỏ" hiện như các lý do khác; bấm hàng → cuộn tới dòng.

**5. Khối chi phí tạm tính**: hàng của bước đã bỏ ghi "S002 (đã bỏ)" chữ `--text-muted`.

**Trạng thái**
- Đang tải / lỗi tải / không có quyền: như FEAT-012.
- Chỉ đọc (NC Auditor, Finance, Director, Resource Manager, Consultant, Admin): thấy nhãn "Bước đã bỏ", nhóm, dải thay đổi (chip chỉ là chữ); không có nút "Tạo phiên bản theo quy trình mới", "Thêm dòng", "Xóa dòng", ô "Gắn với".
- Bộ "Đã xác nhận chuyên môn"/"Đã khóa"/"Đã thay thế": không có dải thay đổi (bộ đóng không có dòng có cờ; `steps_without_lines` = []). "Đã thay thế": không có nút tạo phiên bản.
- Bộ "Nháp" dựa quy trình cũ (`needs_update`): nút "Tạo phiên bản theo quy trình mới" (người có quyền tạo + ghi cùng khoa).

**Bàn phím, truy cập**: nút và chip vào thứ tự Tab theo thứ tự hiển thị; chip có `aria-label` "Thêm dòng cho bước S005"; nhãn "Bước đã bỏ" có chữ (không chỉ màu); hộp kết quả focus nút "Mở lưới"; Esc đóng hộp.

**API**: `new_version`, `get_norm_set`, `save_line`, `delete_line` (`normcore.api.norm.*`); trình duyệt không ghi thẳng DocType (ADR-010).

**Kiểm**: 1366 × 768 — đầu trang có tối đa 4 nút không xuống dòng (nút dài dùng `text-truncate` + `title`); dải thay đổi xuống dòng chip trong khung; tương phản NFR-USE-004 chỉ dùng biến màu Desk.

## SCR-DSK-013 Form NC Norm Set — phần thêm

- Dải "Cần cập nhật" (FEAT-008) thêm nút "Mở lưới định mức" (đã có ở form, dùng lại) với chữ dẫn "Tạo phiên bản theo quy trình mới trên lưới định mức." Không thêm nút ghi trên form.
- Bảng `lines` (chỉ đọc): cột `step_removed` không vào lưới form (`in_list_view` = 0); mở dòng thấy ô chỉ đọc "Thuộc bước đã bỏ".

## Chuỗi mới (vi.csv)

| Khóa (tiếng Anh) | Tiếng Việt |
| :-- | :-- |
| Create version from new procedure | Tạo phiên bản theo quy trình mới |
| New procedure: {0} | Quy trình mới: {0} |
| Removed step | Bước đã bỏ |
| Removed step: {0} | Bước đã bỏ: {0} |
| Steps without lines | Bước chưa có dòng |
| Changes from new procedure | Thay đổi theo quy trình mới |
| Needs a step | Cần gán bước |
| Carried over: {0} lines ({1}) | Mang sang: {0} dòng ({1}) |
| Open grid | Mở lưới |
| Add line for step {0} | Thêm dòng cho bước {0} |

Dev giữ đúng khóa nếu đã có tương đương trong `vi.csv`; chuỗi máy chủ (`_()` trong `api/norm.py`) viết thẳng tiếng Việt như FEAT-012.
