# FEAT-014 — Khảo sát bấm giờ — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-015 (F, bố cục máy tính bảng), SCR-DSK-016 (R), SCR-DSK-014 (mở rộng); `design.md` mục 3–7 (indicator Desk, hộp thoại Desk, vùng chạm 44 px, câu chữ); NFR-USE-003, NFR-USE-004, NFR-LOC-001. API: `technical-design.md` mục 3. Chuỗi nguồn tiếng Anh bọc `__()`/`_()`, bản tiếng Việt trong `normcore/translations/vi.csv` (như FEAT-012); nhãn dưới đây ghi bản tiếng Việt.

## 1. SCR-DSK-015 — Phiếu bấm giờ (form NC Time Study)

**Loại hiện thực:** Form DocType chuẩn của Desk; phần ghi số phút là bảng tùy biến vẽ bằng JS form (`nc_time_study.js`) vào trường HTML `entry_panel` (ASM-014-08). Không phải Desk Page riêng (design.md mục 6: dùng form chuẩn khi đủ).

### 1.1 Bố cục

1. **Khối đầu** (Section "Thông tin ca", 2 cột ở ≥ 992 px, 1 cột ở 768 px): Dịch vụ, Khoa | Ngày bấm giờ, Người khảo sát. Phiên bản quy trình hiện ngay dưới (chỉ đọc sau khi lưu, có liên kết mở quy trình).
2. **Ghi theo bước** (`entry_panel`): mỗi bước một khối hàng, theo thứ tự quy trình:
   - Dòng tiêu đề: `S002 · Tên bước` (đậm), giai đoạn chữ nhỏ màu `--text-muted`.
   - Mỗi dòng phiếu của bước là một hàng: nhãn nguồn lực (tên chức danh hoặc tên thiết bị; dòng chưa có nguồn lực ghi "Chưa chọn nguồn lực" kèm ô chọn), rồi các ô số:
     - Nhân lực: "Số người" (ô số nhỏ, mặc định 1) và "Phút".
     - Thiết bị: "Phút máy".
   - Hai nút nhỏ cuối khối bước: "+ Nhân lực", "+ Thiết bị" (thêm dòng cùng `step_id`, mở ô chọn Link chuẩn của Desk).
   - Bước có mọi ô phút = 0 hiển thị nhãn `gray` "Không thực hiện" (UC-010 2a; không vào trung vị).
3. **Bảng con `lines`** chuẩn: ẩn trên màn hình < 1200 px, hiện thu gọn ở màn hình lớn cho người dùng quen lưới (cùng dữ liệu).
4. Thanh nút Desk: "Lưu" (Ctrl+S) chuẩn; menu "Xem kết quả bấm giờ" mở SCR-DSK-016 với bộ lọc dịch vụ, khoa, quy trình của phiếu; "Ghi ca mới" tạo phiếu mới cùng dịch vụ, khoa (dòng nạp lại từ quy trình).

### 1.2 Tương tác (NFR-USE-003)

- Ô số: `<input type="number" inputmode="decimal" min="0" step="any">`, cao ≥ 44 px, vùng chạm nút ≥ 44 × 44 px, khoảng cách giữa hai vùng chạm ≥ 8 px.
- Thay đổi ô → `frappe.model.set_value("NC Time Study Line", row.name, field, value)` (form thành "Chưa lưu"); không gọi API ghi riêng. Lưu bằng nút "Lưu" của Desk (một lần cho cả ca).
- Enter / phím "Tiếp" trên bàn phím ảo → focus ô phút kế tiếp (thứ tự: các ô của bước hiện tại, rồi bước sau); ô được focus gọi `scrollIntoView({block: "center"})` để không bị bàn phím che.
- Bàn phím: Tab đi qua mọi ô và nút theo thứ tự hiển thị; viền focus nhìn thấy (biến CSS Desk).
- Không có cột bảng cố định chiều rộng: hàng dùng flex-wrap; ở 768 px nhãn nguồn lực chiếm một dòng, ô số xuống dòng dưới → không cuộn ngang.

### 1.3 Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Phiếu mới, chưa chọn dịch vụ/khoa | `entry_panel`: "Chọn dịch vụ và khoa để nạp các bước của quy trình đã ban hành." |
| Đang nạp (`get_entry`) | `entry_panel` ghi "Đang tải..." (`role="status"`) |
| Phiếu mới đã chọn dịch vụ, khoa | Bảng hiện sau lần lưu đầu (controller nạp dòng); trước đó dải `frappe.msgprint` nhẹ: "Lưu để nạp các bước của quy trình." Lưu lỗi "Dịch vụ chưa có quy trình đã ban hành tại khoa này." → lỗi chuẩn của Desk |
| Lỗi kiểm dòng (`line_errors`) | Hộp lỗi Desk, mỗi lỗi một dòng có mã bước; ô liên quan viền đỏ (`--red-500` qua biến Desk) và `aria-invalid="true"` |
| Lỗi tải `get_entry` | Dòng lỗi `role="alert"` + nút "Thử lại" |
| Không có quyền đọc | Trang 403 chuẩn của Desk |
| Chỉ đọc (NC Auditor, Finance, Director, Admin; Clinician khoa khác không thấy) | `can_write` = false: ô số thành chữ, ẩn "+ Nhân lực", "+ Thiết bị"; dải đầu form "Bạn chỉ xem được phiếu này." |
| Không có workflow | Không có indicator trạng thái ngoài "Chưa lưu" chuẩn |

### 1.4 API

`normcore.api.time_study.get_entry(name)` khi mở form đã lưu và sau mỗi lần lưu (tên bước, nhãn nguồn lực, `can_write`). Ghi dữ liệu qua lưu form chuẩn (controller 2.3).

### 1.5 Cách kiểm TC-NFR-05 (tay, T09)

Thiết bị hoặc DevTools 768 × 1024, chế độ chạm. Phiếu có quy trình 6 bước, mỗi bước 1 nhân lực, ít nhất 2 bước có thêm 1 thiết bị. Ghi một ca: đếm lần chạm của từng bước (chạm vào ô, chạm "Tiếp"/Enter trên bàn phím ảo tính là một lần; gõ chữ số không tính). Đạt khi mọi bước ≤ 3 lần chạm (bước 1 nhân lực + 1 thiết bị: chạm ô phút, "Tiếp", "Tiếp" sang bước sau = 2–3) và `document.documentElement.scrollWidth` ≤ 768 trong suốt quá trình. Ghi bảng đếm + ảnh vào implementation-log.

## 2. SCR-DSK-016 — Kết quả bấm giờ (Script Report `NC Time Study Result`)

**Loại hiện thực:** Script Report chuẩn của Desk, module NC Costing, tên hiển thị "Kết quả bấm giờ". Vai trò: Clinician, Dept Head, Finance, Director, Consultant, Admin, Auditor (đọc theo bảng 2.1).

### 2.1 Bố cục

- Bộ lọc: Dịch vụ (Link, BB), Khoa (Link, BB), Phiên bản quy trình (Link NC Clinical Procedure, lọc theo dịch vụ + khoa; trống = quy trình đã ban hành mới nhất).
- Dải tóm tắt trên bảng (`report.page` message / `get_report_summary`): "Số ca: 6 / tối thiểu 5", "Từ 01/11/2026 đến 20/11/2026". Đủ ca: indicator `green` "Đủ số ca"; chưa đủ: indicator `yellow` "Chưa đủ số ca" + câu "Trung vị chỉ để tham khảo; áp vào bộ định mức cần xác nhận."
- Cột: Mã bước | Tên bước | Loại (Nhân lực / Thiết bị) | Chức danh / thiết bị | Trung vị (phút, căn phải, tối đa 2 chữ số lẻ, dấu phẩy thập phân) | Số ca có số liệu.
- Nút chính "Áp vào bộ định mức" (thanh nút report).

### 2.2 Hành động "Áp vào bộ định mức"

1. Hộp thoại Desk: trường Link "Bộ định mức" lọc `technical_service`, `department`, `procedure` của bộ lọc và `status` = "Nháp". Không có bộ nào → câu "Chưa có bộ định mức Nháp cho quy trình này." + liên kết "Danh sách bộ định mức".
2. "Áp" → `apply_to_norm_set(norm_set)`.
3. Trả `needs_confirm` → `frappe.confirm`: "Mới có {n} ca, ít hơn mức tối thiểu {min}. Vẫn áp trung vị vào bộ định mức? Số phút các dòng tương ứng sẽ bị thay và căn cứ đặt là "Bấm giờ"." → đồng ý gọi lại với `confirm=1`.
4. Thành công → `frappe.show_alert` (xanh): "Đã cập nhật {k} dòng." + nếu `unmatched`: `msgprint` liệt kê "Không có dòng định mức tương ứng: S003 · DD; ..."; nút "Mở lưới định mức" tới `norm-grid`.

### 2.3 Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Chưa chọn dịch vụ/khoa | Thông điệp rỗng chuẩn: "Chọn dịch vụ và khoa để xem trung vị số phút từ các ca bấm giờ." |
| Không có ca | "Chưa có ca bấm giờ nào." + nút "Ghi ca mới" (mở form NC Time Study điền sẵn dịch vụ, khoa); ẩn "Áp vào bộ định mức" |
| Đang tải | Thanh tải chuẩn của report |
| Lỗi (không có quy trình đã ban hành, lỗi API) | Thông báo lỗi Desk |
| Không quyền (Council, Resource Mgr, Doc Controller) | Report không hiện trong menu; mở URL → 403 |
| Chỉ đọc (Auditor, Finance, Director, Admin, Consultant) | Xem đủ; nút "Áp vào bộ định mức" ẩn khi người dùng không có quyền write NC Norm Set (`frappe.model.can_write("NC Norm Set")`); máy chủ vẫn kiểm |

## 3. SCR-DSK-014 — Lưới định mức (mở rộng FEAT-012)

- `NormGrid.vue`, thanh nút: thêm "Áp kết quả bấm giờ" (`btn-default btn-sm`) khi `can('apply_time_study')`. Bấm → `normcore.api.time_study.apply_to_norm_set`; `needs_confirm` → dùng khối xác nhận sẵn có của lưới (`pending`) với câu như 2.2 bước 3; thành công → tải lại lưới, thông báo như 2.2 bước 4. Lỗi → khối `role="alert"` sẵn có.
- Liên kết nhỏ "Xem kết quả bấm giờ" cạnh nút, mở SCR-DSK-016 với bộ lọc của bộ.
- Dòng có `basis` = "Bấm giờ" hiển thị căn cứ như mọi căn cứ khác (đã có cột Căn cứ); không thêm màu.
- Form NC Norm Set (`nc_norm_set.js`): nút "Áp kết quả bấm giờ" cùng điều kiện (bộ "Nháp", người dùng có quyền ghi), cùng luồng xác nhận, sau đó `frm.reload_doc()`.

## 4. Kiểm chung

- 1366 × 768: form và report không cuộn ngang; lưới định mức giữ bố cục FEAT-012.
- Bàn phím: mọi thao tác làm được bằng Tab/Enter/Esc (hộp thoại Desk đóng bằng Esc).
- Tương phản ≥ 4,5:1 (NFR-USE-004): chỉ dùng biến màu Desk, không mã màu cứng; nhãn màu luôn có chữ.
- Số và ngày theo NFR-LOC-001 (`format_number`, `frappe.datetime.str_to_user`).
- Mọi chuỗi qua `__()` (JS) / `_()` (Python), bản dịch trong `vi.csv`.
