# FEAT-008 — Sửa đổi, so sánh phiên bản, thu hồi — Thiết kế giao diện

Căn cứ: `ux-foundations.md` SCR-DSK-011 ("P nhẹ"; khác biệt theo phần, bước, nguồn lực; thêm xanh, bỏ đỏ, đổi vàng), SCR-DSK-009/010 (trang `procedure-editor`), SCR-DSK-013 (lọc cờ "Cần cập nhật"); `design.md` mục 3 (indicator, dải chỉ đọc), 4 (bàn phím, tương phản, màu không là kênh duy nhất), 5 (câu chữ, hộp xác nhận nêu hệ quả); ADR-010; API ở `technical-design.md` mục 3. Chiến lược code-native. Kế thừa quy ước `docs/features/FEAT-006/ui-design.md` và `FEAT-007/ui-design.md` (biến CSS của Desk, `__()`, bố cục hai cột). Mọi chuỗi mới vào `normcore/translations/vi.csv` (giữ sắp xếp, không trùng khóa).

## 1. Form Desk NC Clinical Procedure (mở rộng `nc_clinical_procedure.js`)

Loại: Form DocType chuẩn. Thêm nút (cạnh "Open editor"):

| Nút | Hiện khi | Hành động | API |
| :-- | :-- | :-- | :-- |
| "Sửa đổi" | `workflow_state` = Đã ban hành và `frm.perm[0].write` | Hộp xác nhận: "Tạo bản nháp phiên bản kế tiếp từ phiên bản {n}. Mã bước giữ nguyên; bản nháp đi qua luồng duyệt như bản đầu." [Tạo bản nháp] [Hủy]. Thành công → mở `procedure-editor/<bản mới>`; `existing = 1` → `frappe.show_alert(__("Đã có bản đang soạn: {0}"))` rồi mở bản đó | `normcore.api.procedure.create_revision` |
| "So sánh phiên bản" | `version_no` > 1 hoặc có `previous_version` | Mở `procedure-editor/<previous_version hoặc name>/compare/<name>` | — |
| "Thu hồi" | Đã ban hành và người dùng có vai trò NC Director | Hộp thoại: trường "Lý do thu hồi" (Small Text, bắt buộc), câu hệ quả "Sau khi thu hồi, quy trình chuyển 'Đã thu hồi' và không dùng làm căn cứ được nữa." [Thu hồi] (nút đỏ) [Hủy]. Lý do trống → báo lỗi tại trường, không gọi API | `normcore.api.procedure_workflow.apply_action(procedure, "Thu hồi", reason)` |

Dải chỉ đọc (đã có từ FEAT-007, đổi câu chữ cho đúng `design.md` 3): "Bản ghi đã ban hành, không sửa được. Chọn 'Sửa đổi' để tạo phiên bản mới." — chỉ nối thêm câu hành động khi nút "Sửa đổi" hiện. Ở "Đã thu hồi": dải đỏ "Quy trình đã thu hồi: {lý do}" (lý do lấy từ `get_review.last_withdraw` — xem mục 5).

Lỗi API → `frappe.msgprint` của Desk (đỏ, tiêu đề từ lỗi). PermissionError → "Bạn không có quyền …" như thông điệp máy chủ. NC Auditor: không thấy "Sửa đổi", "Thu hồi"; thấy "So sánh phiên bản".

## 2. Trình soạn `procedure-editor` — thanh trên khi chỉ đọc

Khi quy trình không ở Nháp (SCR-DSK-009 chế độ chỉ đọc / SCR-DSK-010): thêm vào nhóm nút bên phải thanh trên, cùng điều kiện mục 1: "Sửa đổi", "So sánh phiên bản", "Thu hồi" (Thu hồi lấy từ `get_review.actions` chứa "Thu hồi"). Hộp thoại dùng `frappe.ui.Dialog`, cùng câu chữ mục 1. Sau thu hồi: tải lại dữ liệu, nhãn trạng thái đổi "Đã thu hồi" (`red`).

## 3. SCR-DSK-011 So sánh phiên bản — chế độ của `procedure-editor`

Loại: chế độ trong Desk Page Vue `procedure-editor` (ASM-008-12). Route `procedure-editor/<base>/compare/<target>`; thiếu `target` → mở bộ chọn với `target` = bản mới nhất khác `base`.

### 3.1 Bố cục (1366 × 768, một cột nội dung rộng, không cột trích dẫn)
1. **Thanh trên:** tiêu đề "So sánh phiên bản — {mã dịch vụ} · {khoa}". Hai ô chọn "Phiên bản gốc" và "Phiên bản so sánh" (Select, nhãn mỗi lựa chọn: `v{n} · {trạng thái} · {ngày hiệu lực dd/mm/yyyy hoặc "—"}`), nút "Đổi chiều" (⇄, có `aria-label` "Đổi chiều so sánh"), nút "Đóng so sánh" (về `procedure-editor/<target>`). Đổi lựa chọn → cập nhật route và gọi lại API.
2. **Dải tóm tắt:** ba nhóm "Phần", "Bước", "Dòng nguồn lực", mỗi nhóm ba nhãn có số: "Thêm {n}" (`green`), "Bỏ {n}" (`red`), "Đổi {n}" (`yellow`). Ô đánh dấu "Chỉ hiện chỗ khác" (mặc định bật).
3. **Khối "Phần"** (7 phần văn bản theo thứ tự FR-PROC-001): mỗi phần một thẻ, tiêu đề + nhãn trạng thái. Đổi: hai cột "v{gốc}" | "v{so sánh}" (HTML đã làm sạch, `frappe.utils.xss_sanitise` / hiển thị như trình soạn). Thêm: chỉ cột phải; bỏ: chỉ cột trái. Giữ nguyên: thu gọn một dòng "Không đổi" (ẩn khi "Chỉ hiện chỗ khác").
4. **Khối "Các bước"**: bảng một dòng mỗi bước, cột: Mã bước | Giai đoạn | Tên bước | Trạng thái | Trường đổi. Dòng thêm: viền trái và nhãn "Thêm" `green`; bỏ: nhãn "Bỏ" `red`, chữ gạch ngang; đổi: nhãn "Đổi" `yellow`, ô "Trường đổi" liệt kê nhãn tiếng Việt (Giai đoạn, Tên bước, Mô tả, Thời gian tham chiếu) và "Nguồn lực" nếu đổi do dòng nguồn lực; `moved` → nhãn "Đổi vị trí" `gray`. Enter/bấm trên dòng → mở rộng ngay dưới: giá trị cũ → mới từng trường đổi, và các dòng nguồn lực của bước (mục 5).
5. **Khối "Dòng nguồn lực"**: nhóm theo mã bước (theo bản so sánh; bỏ thì theo bản gốc), cột: Mã dòng | Loại | Tên | Số lượng | Đơn vị | Số người | Trạng thái. Ô đổi hiển thị "cũ → mới" (số căn phải, định dạng `1.234,5` theo NFR-LOC-001), ô không đổi chữ thường.

Màu chỉ qua indicator pill của Desk và `var(--green-…)`/`var(--red-…)`/`var(--yellow-…)` nền nhẹ cho viền trái; luôn kèm chữ "Thêm/Bỏ/Đổi" (design.md 4). Không mã màu cứng.

### 3.2 Trạng thái
| Trạng thái | Hiển thị |
| :-- | :-- |
| Đang tải | Khung xương của dải tóm tắt và ba khối; ô chọn vô hiệu |
| Chỉ có một phiên bản | "Quy trình này mới có một phiên bản. So sánh dùng khi đã có phiên bản sửa đổi." + nút "Sửa đổi" (nếu có quyền) |
| Hai bản giống nhau | Dải tóm tắt toàn 0 và câu "Hai phiên bản không khác nhau về phần, bước, nguồn lực." |
| Lỗi (khác dịch vụ/khoa, mạng) | Hộp báo đỏ với thông điệp máy chủ + nút "Thử lại" |
| Không có quyền | "Bạn không có quyền xem một trong hai phiên bản." (PermissionError); bộ chọn chỉ liệt kê bản đọc được (`list_versions`) |
| NC Auditor | Như người đọc; chế độ so sánh vốn chỉ đọc, không có nút ghi nào |

### 3.3 API
- Vào trang / đổi bộ chọn: `normcore.api.procedure.list_versions(procedure=base)` (một lần), `normcore.api.procedure.compare_versions(base, target)`.

### 3.4 Bàn phím, tiếp cận
- Thứ tự Tab: ô gốc → ô so sánh → Đổi chiều → Đóng → "Chỉ hiện chỗ khác" → dòng tóm tắt (Enter cuộn tới khối) → thẻ phần → dòng bước (Enter mở/đóng chi tiết) → bảng nguồn lực. Esc: đóng chi tiết đang mở, rồi đóng hộp thoại.
- Phím tắt: `Alt+←`/`Alt+→` chọn phiên bản so sánh trước/sau (không trùng phím Desk).
- Tương phản ≥ 4,5:1 (NFR-USE-004): chữ trên nền nhấn nhẹ dùng `--text-color`; kiểm ở chủ đề sáng và tối.
- Bảng có `<th scope>`; nhãn trạng thái có chữ, không chỉ màu.
- 1366 × 768: hai cột của khối "Phần" mỗi cột ≥ 520 px; bảng bước và nguồn lực cuộn ngang trong khung nếu thiếu chỗ, không cuộn cả trang theo chiều ngang.

## 4. NC Norm Set — form và danh sách (PA1, ASM-008-14)

Loại: Form/List DocType chuẩn (SCR-DSK-013 là danh sách, FEAT-012 làm đầy đủ; FEAT-008 chỉ phần cờ).
- Form (`nc_norm_set.js`): khi `needs_update` = 1, `frm.dashboard.set_headline_alert` dải `yellow`: "Cần cập nhật: quy trình có phiên bản mới — {step_change_note}." kèm liên kết "So sánh phiên bản" → `procedure-editor/<procedure>/compare/<bản ban hành mới nhất>`. Hai trường hiển thị chỉ đọc.
- Danh sách: `needs_update` là cột và bộ lọc chuẩn (`in_list_view`, `in_standard_filter`); chỉ báo danh sách (`listview_settings.get_indicator`) giữ theo `status`, thêm nhãn phụ "Cần cập nhật" (`yellow`) qua `formatters`/`add_fields`.
- NC Auditor: thấy dải và cột, không sửa được.

## 5. Dữ liệu phụ cho giao diện
`get_review` (FEAT-007) thêm `last_withdraw` (`{by, at, reason}` của sự kiện "Chuyển trạng thái" tới "Đã thu hồi" mới nhất; None nếu không có) để dải đỏ mục 1 và trình soạn hiển thị lý do. Không thêm endpoint.

## 6. Kiểm
- Unit (không cần site, như `tests/unit/test_feat_007_ui.py`): chuỗi mới có trong `vi.csv`; JS form có nút "Sửa đổi", "So sánh phiên bản", "Thu hồi" gọi đúng API; Vue có route `compare`.
- QA (loại M, TC-WF-07): Playwright mở so sánh v1/v2 của dữ liệu TC-WF-06, chụp 1366 × 768: S005 "Thêm" xanh, S002 "Bỏ" đỏ, S003 "Đổi" vàng do nguồn lực, dòng nguồn lực của S003 "cũ → mới".
