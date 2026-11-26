# FEAT-012 — Thiết kế giao diện

Căn cứ: `ux-foundations.md` SCR-DSK-013, SCR-DSK-014, Luồng 2, bảng thành phần ("Lưới định mức: lưới sửa trực tiếp, nhóm theo bước, hàng tổng theo bước và cấu phần"), UXQ-05; `design.md` mục 3 (màu trạng thái, Lưới định mức, Dòng đề xuất của AI, Bản ghi chỉ đọc, trạng thái thành phần), mục 4–5; ADR-010; API ở `technical-design.md` mục 3. Chiến lược code-native, không dùng công cụ thiết kế ngoài. Kế thừa quy ước của `docs/features/FEAT-006/ui-design.md` (Vue 3 trong Desk Page, `SetVueGlobals`, biến CSS của Desk, `__()`, gọi API bọc Promise, lỗi ở dải `role="alert"`). Cột **[1.1]** (cấp phát sinh, nhân k, số xét nghiệm mỗi ống, khoản mục mẫu, cảnh báo kế hoạch nội kiểm) **không** làm ở đây — FEAT-034 thêm vào cùng lưới.

Màu chỉ báo (design.md mục 3): Nháp `gray`; Đã xác nhận chuyên môn `blue`; Đã khóa `green`; Đã thay thế `darkgrey`; Cần cập nhật `yellow`; Đề xuất `purple`.

## SCR-DSK-013 Danh sách bộ định mức (List view chuẩn của Desk)

- Loại: List DocType NC Norm Set, `nc_norm_set_list.js`.
- Cột (vừa 1366 px): Tên (`DM-…`), Dịch vụ (`technical_service`), Khoa, Phiên bản, Trạng thái (indicator), Cần cập nhật (nhãn `yellow` khi bật), Sửa lần cuối.
- Bộ lọc chuẩn: Trạng thái, Khoa, Cần cập nhật, Dịch vụ. Mặc định sắp `modified` giảm dần.
- `get_indicator`: theo màu ở trên; bộ có `needs_update` hiện thêm "Cần cập nhật" `yellow` cạnh trạng thái.
- Bấm một dòng → mở **trang `norm-grid/<name>`** (`onload` đặt `listview.settings.primary_action`/`frappe.set_route("norm-grid", name)`), không mở form; form vẫn vào được từ menu "…".
- Nút "Thêm" chuẩn ẩn (`hide_name_field`, không tạo trực tiếp): thay bằng nút "Khởi tạo bộ định mức" (chỉ khi `frappe.model.can_create("NC Norm Set")`) mở hộp thoại một trường "Quy trình đã ban hành" (Link NC Clinical Procedure, lọc `workflow_state = Đã ban hành`) → `create_norm_set` → mở `norm-grid`.
- Trạng thái: rỗng — "Chưa có bộ định mức. Khởi tạo từ một quy trình đã ban hành."; không quyền đọc — trang lỗi quyền chuẩn của Desk; NC Auditor — chỉ đọc, không nút "Khởi tạo".

## Form NC Norm Set (thay đổi nhỏ)
- Bỏ nút tạm "Khóa" (FEAT-000). Thêm nút chính "Mở lưới định mức" → `norm-grid/<name>`.
- Bảng `lines` chỉ đọc (`frm.set_df_property("lines", "read_only", 1)`); dải đầu form ở "Đã khóa"/"Đã thay thế": "Bản ghi đã <trạng thái>, không sửa được. Tạo phiên bản mới trên lưới định mức."
- Form NC Clinical Procedure "Đã ban hành": nút "Khởi tạo bộ định mức" gọi `create_norm_set`, thành công → `norm-grid/<name>`; lỗi (TC-NORM-02, Q2) → `frappe.msgprint` chữ máy chủ.

## SCR-DSK-014 Lưới định mức (Desk Page `norm-grid`, Vue 3)

**Vào trang**: route `norm-grid/<name>`; `on_page_show` gọi `get_norm_set(name)`. Không có `name` → dải "Chọn một bộ định mức ở danh sách" + liên kết SCR-DSK-013.

**Bố cục** (1366 × 768, một cột, lưới cuộn ngang trong khung nếu thiếu chỗ, cột Mã dòng và Nguồn lực cố định trái):
1. **Đầu trang** (cố định khi cuộn): tên dịch vụ, khoa, "Phiên bản n", liên kết quy trình (mở form quy trình), liên kết "Phiên bản trước" nếu có; nhãn trạng thái; nhãn "Cần cập nhật" + `step_change_note` khi bật. Bên phải các nút theo `actions` (không có thì không hiện), thứ tự: nút chính theo trạng thái ("Xác nhận chuyên môn" ở Nháp; "Khóa" ở Đã xác nhận chuyên môn; "Tạo phiên bản mới" ở Đã khóa — `btn-primary`), rồi "Trả lại" (`btn-default`), "Thêm dòng".
2. **Dải thông báo**: Đã xác nhận chuyên môn — "Bộ đã xác nhận chuyên môn, chờ Tài chính khóa. Không sửa được."; Đã khóa/Đã thay thế — "Bản ghi đã <trạng thái>, không sửa được. Tạo phiên bản mới." (nút trong dải nếu có `new_version`); có `blockers` ở Nháp — dải `yellow` "Còn n dòng chưa đủ điều kiện xác nhận chuyên môn" + nút "Lọc các dòng này". Trần hao hụt mặc định (ASM-012-10) — dòng nhỏ `--text-muted` "Trần hao hụt 10% (Giả định — chờ xác nhận: chưa có bộ tham số hiệu lực)".
3. **Thanh lọc**: ô tìm (mã dòng, tên nguồn lực), chọn Cấu phần, nút bật "Chỉ dòng cần xử lý" (chưa liên kết / chưa xác nhận / đề xuất / trùng), "Hiện dòng loại trừ" (mặc định bật). Nút "Thu gọn tất cả bước".
4. **Lưới** (thành phần "Lưới định mức" của design.md): nhóm theo bước theo thứ tự quy trình, nhóm cuối "Chung cho cả dịch vụ". **Hàng nhóm**: nền nhấn nhẹ (`--subtle-fg`/`--bg-light-gray`), "S002 · <tên bước> · <giai đoạn>", số dòng, tổng chi phí tạm tính của bước căn phải ở cuối hàng; bấm/Enter để thu gọn. Cột của hàng dòng:

   | Cột | Trường | Sửa được (Nháp + quyền) | Ghi chú |
   | :-- | :-- | :-- | :-- |
   | Mã dòng | `line_id` | Không | Kèm biểu tượng nhỏ "từ quy trình" khi có `procedure_resource_row` (tooltip "Dòng nguồn lực gốc R00x") |
   | Cấu phần | `component` | Có (Select 6, nhãn tiếng Việt: Nhân lực, Thuốc và hóa chất, Vật tư, Thiết bị, Hạ tầng, Tiện ích) | Đổi cấu phần thì xóa nguồn lực, `resource_doctype` theo DI-05 |
   | Nguồn lực | `resource` | Có (ô Link của Desk `frappe.ui.form.make_control`, DocType theo cấu phần) | Trống → nhãn `orange` "Chưa liên kết"; `ai_suggested` → nền nhấn, nhãn `purple` "Đề xuất" (không có nút Chấp nhận/Bỏ ở FEAT-012, FEAT-025 thêm) |
   | Số người | `headcount` | Có, chỉ LABOR | Ô vô hiệu ở cấu phần khác |
   | Định mức BV | `hospital_qty` | Có | Đơn vị phút ở LABOR/EQUIPMENT/INFRA hiện ngay sau số |
   | Đ.mức ban hành | `authority_qty` | Có | Có giá trị thì hiện biểu tượng văn bản; bấm mở ô `authority_ref` |
   | Lượng áp dụng | `applied_qty` | Không | Tô đậm khi khác Định mức BV (BR-COST-007) |
   | Đơn vị | `uom` | Có | |
   | Hao hụt % | `wastage_rate` | Có, chỉ DRUG/SUPPLY | Vượt trần → nhãn `yellow` "Vượt trần"; ô lý do bắt buộc ở bảng chi tiết |
   | Căn cứ | `basis` | Có (Select 5) | Kèm `basis_ref` ở bảng chi tiết |
   | Loại trừ | `is_excluded` | Có (ô đánh dấu) | Bật → chữ dòng `--text-muted`, nhãn "Loại trừ: <lý do>"; thành tiền 0 |
   | Thành tiền tạm tính | `cost.amount` | Không | Căn phải, phông số đơn cách; thiếu → chữ `--text-muted` "Chưa có đơn giá" |
   | Xác nhận | `confirmed_by` | Nút "Xác nhận" (khi có `confirm_line`) | Đã xác nhận: dấu tick + tên viết tắt, tooltip người và thời điểm dd/mm/yyyy HH:mm |

   Cột số căn phải, phông số đơn cách của Desk; ô sửa được có viền khi rê chuột/focus, ô chỉ đọc không viền. Số định dạng theo NFR-LOC-001 (`format_number`, dấu chấm phân nghìn, phẩy thập phân theo ngôn ngữ hệ thống); tiền `format_currency` không số lẻ hiển thị khi tổng, 2 số lẻ ở dòng như golden.
   Dòng trùng (FR-NORM-014): biểu tượng cảnh báo `orange` + tooltip "Trùng nguồn lực với Lxxx trong cùng bước".
5. **Bảng chi tiết dòng** (mở dưới dòng khi bấm "…" hoặc Enter trên Mã dòng; một dòng mở một lúc): `authority_ref`, `wastage_reason` (Small Text, bắt buộc khi vượt trần), `basis_ref`, `exclude_reason` (Select 5, bắt buộc khi loại trừ), `step_id` / "Chung cho cả dịch vụ" (chỉ dòng thêm tay), nút "Xóa dòng" (chỉ dòng thêm tay, có `delete_line`), thông tin xác nhận.
6. **Khối chi phí tạm tính** (dưới lưới, FR-NORM-016): bảng chéo bước (hàng) × 6 cấu phần (cột) + cột Tổng + hàng Tổng; ô 0 hiện "–". Tiêu đề "Chi phí trực tiếp tạm tính (bộ tham số <tên>, ngày <hôm nay>)". `incomplete` → nhãn `yellow` "Chưa đủ: có dòng chưa có đơn giá hoặc chưa liên kết". Ghi chú `--text-muted` "Chỉ để tham khảo; giá thành chính thức tính ở Lần tính giá."

**Sửa ô** (Nháp + `save_line`): sửa tại chỗ; rời ô (blur) hoặc Enter → `save_line(norm_set, line_id, values)` cho cả dòng; trong lúc lưu ô hiện trạng thái đang tải, các ô khác của dòng khóa tạm. Esc hủy thay đổi ô. Lỗi máy chủ (FR-NORM-003/004/005/008/013) → viền đỏ ô liên quan (theo tên trường trong thông báo) + dải `role="alert"` ngay dưới dòng có chữ máy chủ; giá trị trên lưới trở về giá trị đã lưu. `saved: false` + `duplicates` → `frappe.confirm` "Nguồn lực này đã có ở dòng Lxxx của cùng bước. Vẫn lưu?" → Đồng ý gọi lại với `allow_duplicate=1`.

**Thêm dòng**: hộp thoại `frappe.ui.Dialog`: Cấu phần (bắt buộc), Nguồn lực (Link theo cấu phần, bắt buộc), "Gắn với" (chọn: một mã bước `S### · tên` hoặc "Chung cho cả dịch vụ", bắt buộc — TC-NORM-09), Số người (LABOR), Định mức BV, Đơn vị, Căn cứ (mặc định "Ước tính"). Nút "Thêm" → `save_line(norm_set, values)` không `line_id`. Lỗi hiện trong hộp thoại.

**Hành động bộ** (hộp thoại Desk):
- "Xác nhận chuyên môn" (Dept Head): xác nhận "Sau khi xác nhận, bộ không sửa được cho đến khi Tài chính trả lại." → `confirm_set`. Bị từ chối (TC-NORM-05): hộp thoại "Chưa xác nhận chuyên môn được" liệt kê mỗi dòng một hàng "Lxxx — <lý do>, <lý do>"; bấm một hàng → đóng hộp thoại, cuộn tới và focus dòng đó.
- "Trả lại" (Finance): trường "Lý do trả lại" (Small Text, bắt buộc cả máy khách và máy chủ) → `return_set`.
- "Khóa" (Finance): xác nhận "Sau khi khóa, bộ định mức không sửa được và được dùng để tính giá." → `lock_set`.
- "Tạo phiên bản mới": xác nhận "Tạo bộ nháp phiên bản n+1 từ bộ này?" → `new_version` → chuyển `norm-grid/<tên mới>`.
- "Xác nhận" một dòng: không hộp thoại; gọi `confirm_line`; alert "Đã xác nhận Lxxx".
- Sau mỗi hành động thành công: vẽ lại từ kết quả, `frappe.show_alert` "Đã chuyển sang <trạng thái>", focus về nhãn trạng thái.

**Bàn phím**: Tab/Shift+Tab đi qua ô sửa được theo hàng; mũi tên lên/xuống đi cùng cột khi ô không ở chế độ sửa; Enter vào/thoát sửa; Esc hủy; Ctrl+Shift+A "Thêm dòng"; mọi nút có focus nhìn thấy (`--focus` của Desk). Hàng nhóm là nút (`aria-expanded`). Bảng dùng `role="grid"`, ô `role="gridcell"`, nhãn cột `scope="col"`.

**Trạng thái**:
- Đang tải: khung xương 5 hàng + "Đang tải…"; nút vô hiệu.
- Rỗng: bộ không có dòng — "Bộ định mức chưa có dòng nào." + nút "Thêm dòng" nếu được sửa.
- Lỗi tải: dải đỏ `role="alert"` chữ máy chủ + nút "Thử lại".
- Không có quyền: `get_norm_set` PermissionError (403) → dải "Bạn không có quyền xem bộ định mức này" (đọc `responseJSON` như FEAT-006 E15), không vẽ lưới.
- Chỉ đọc (NC Auditor, Finance/Director/Resource Manager/Consultant/Admin ở Nháp, mọi người ở trạng thái đóng): mọi ô không viền, không nút sửa/thêm/xóa/xác nhận; Finance vẫn có "Khóa"/"Trả lại" ở Đã xác nhận chuyên môn; NC Auditor không có nút nào.
- Theo trạng thái: Nháp (người sửa: ô sửa, Thêm dòng, Xác nhận dòng; Dept Head thêm "Xác nhận chuyên môn"); Đã xác nhận chuyên môn (chỉ đọc; Finance: Khóa, Trả lại); Đã khóa (chỉ đọc; người có quyền tạo: Tạo phiên bản mới); Đã thay thế (chỉ đọc).

**API**: mở → `get_norm_set`; sửa → `save_line`, `delete_line`; xác nhận → `confirm_line`, `confirm_set`; Tài chính → `lock_set`, `return_set`; phiên bản → `new_version`; danh sách/form → `create_norm_set`. Trình duyệt không ghi thẳng DocType (ADR-010).

**Kiểm**: 1366 × 768 không vỡ đầu trang và thanh lọc, lưới cuộn ngang trong khung, cột trái cố định; > 100 dòng (UXQ-05) dùng thu gọn bước; tương phản theo NFR-USE-004 (chỉ dùng biến màu Desk, nhãn trạng thái luôn kèm chữ, không dựa màu đơn thuần); mọi chuỗi qua `__()` và có trong `vi.csv`.
