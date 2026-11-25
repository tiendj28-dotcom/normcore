# FEAT-007 — Thiết kế giao diện

Căn cứ: `ux-foundations.md` SCR-DSK-010 ("Chế độ của SCR-DSK-009"; xem chỉ đọc, ghi ý kiến theo bước, nút duyệt/từ chối/ban hành; bảng tóm tắt khác biệt, danh sách ý kiến chưa xử lý), bảng thành phần (Bảng trích dẫn, Thẻ bước, Nhãn quan hệ); `design.md` mục 3–5, 7; ADR-010; API ở `technical-design.md` mục 3. Chiến lược code-native, không dùng công cụ thiết kế ngoài. Kế thừa toàn bộ quy ước của `docs/features/FEAT-006/ui-design.md` (bố cục hai cột, bàn phím, biến CSS, `__()`).

## SCR-DSK-010 Thẩm định và duyệt (chế độ của Desk Page `procedure-editor`, Vue 3)

**Vào chế độ**: trang `procedure-editor` gọi thêm `get_review(name)` khi mở quy trình. Chế độ thẩm định bật khi `workflow_state` ≠ "Nháp" (mọi người dùng), và luôn hiện phần "Ý kiến thẩm định" ở "Nháp" nếu có ý kiến (người soạn xem sau khi bị trả lại). Ở chế độ này toàn bộ điều khiển soạn ẩn, văn bản `readonly` (như chế độ chỉ đọc của FEAT-006).

**Bố cục** (1366 × 768; nội dung 2fr | cột phải 1fr; dưới 900px một cột):
1. **Thanh duyệt** (dưới tiêu đề, cố định khi cuộn): nhãn trạng thái (indicator, màu theo `design.md` mục 3: Nháp `gray`; ba trạng thái chờ `orange`; Đã ban hành `green`; Đã thay thế `darkgrey`; Đã thu hồi `red`); nút theo `actions` của `get_review`, theo thứ tự: nút chính ("Gửi duyệt" / "Đồng ý" / "Thông qua" / "Ban hành", lớp `btn-primary`), "Từ chối" (`btn-default`), "In PDF", "Tải DOCX". Nút không có trong `actions` thì không hiện. Bên phải: "Ý kiến chưa xử lý: n".
2. **Dải thông báo**: ở trạng thái chờ "Quy trình đang chờ duyệt, không sửa được."; ở trạng thái đóng "Bản ghi đã <trạng thái>, không sửa được. Tạo phiên bản mới ở chức năng Sửa đổi (FEAT-008)."; ở "Nháp" có `last_reject`: dải vàng "Bị từ chối ở cấp <cấp> bởi <người> ngày dd/mm/yyyy: <lý do>".
3. **Bảng tóm tắt khác biệt** (đầu cột trái, UC-006 bước 3): danh sách trích dẫn "Khác biệt" và "Chưa có căn cứ" — nhãn quan hệ (chữ + màu), phần hoặc mã bước (liên kết: bấm/Enter cuộn tới và chọn phần/bước đó), lý do khác biệt. Trống: "Không có chỗ khác biệt hay chưa có căn cứ."
4. **Nội dung chỉ đọc**: 8 phần và thẻ bước như SCR-DSK-009. Mỗi thẻ bước và mỗi phần có huy hiệu "Ý kiến: n" (số ý kiến chưa xử lý / tổng) khi n > 0.
5. **Cột phải, hai thẻ**: "Trích dẫn" (Bảng trích dẫn của phần/bước đang chọn, như FEAT-006) và "Ý kiến thẩm định" (mặc định khi có ý kiến):
   - Danh sách ý kiến của phần/bước đang chọn (chưa chọn: ý kiến chung + tất cả, nhóm theo phần/bước): người ghi, cấp (`review_state`), ngày giờ, nội dung; ý kiến đã xử lý chữ `--text-muted` kèm chữ "Đã xử lý". Ô đánh dấu "Đã xử lý" chỉ hiện với người có quyền ghi (`set_comment_resolved`).
   - Biểu mẫu "Thêm ý kiến" (chỉ ở trạng thái chờ và khi người dùng có vai trò Dept Head / Council / Director): ô "Gắn với" (chọn: Ý kiến chung / một trong 8 phần / một mã bước `S###` — mặc định phần/bước đang chọn), ô "Ý kiến" (textarea, bắt buộc), nút "Lưu ý kiến" → `add_review_comment`.
   - Bộ lọc "Chỉ chưa xử lý".

**Hộp thoại** (dùng `frappe.ui.Dialog` của Desk, không tự tạo kiểu):
- "Gửi duyệt": hộp xác nhận "Sau khi gửi, quy trình không sửa được cho đến khi bị trả lại." → `apply_action(name, "Gửi duyệt")`. Lỗi kiểm tra (FR-PROC-008/012): hộp thoại "Chưa gửi duyệt được" liệt kê từng lỗi một dòng; lỗi có mã bước/dòng có liên kết tới bước đó (design.md mục 5); quy trình giữ "Nháp".
- "Đồng ý" / "Thông qua": xác nhận một câu nêu cấp kế tiếp ("Quy trình sẽ chuyển sang Chờ hội đồng thẩm định.").
- "Từ chối": trường "Lý do từ chối" (Small Text, bắt buộc phía máy khách và máy chủ); nút "Từ chối". Lỗi máy chủ "Cần nhập lý do từ chối" hiện trong hộp thoại.
- "Ban hành": trường "Số quyết định" (Data, bắt buộc), "Ngày hiệu lực" (Date, bắt buộc, mặc định hôm nay); câu "Sau khi ban hành, nội dung phiên bản này không sửa được."; nút "Ban hành".
- Sau mỗi hành động thành công: tải lại `get_procedure` + `get_review`, `frappe.show_alert` "Đã chuyển sang <trạng thái>", tiêu điểm về nhãn trạng thái.

**Tải tệp**: "In PDF" → `window.open` tới `/api/method/normcore.api.procedure_workflow.download_pdf?procedure=<name>`; "Tải DOCX" → `download_docx` cùng cách.

**Trạng thái**:
- Đang tải: "Đang tải…" ở cột phải và thanh duyệt.
- Rỗng: chưa có ý kiến — "Chưa có ý kiến thẩm định." (cộng biểu mẫu nếu được ghi).
- Lỗi: dải đỏ `role="alert"` có chữ lỗi máy chủ.
- Không có quyền: `get_review` PermissionError → dải "Bạn không có quyền xem quy trình này"; không có hành động → thanh duyệt chỉ có In PDF / Tải DOCX.
- Chỉ đọc NC Auditor: không nút duyệt, không biểu mẫu ý kiến, không ô "Đã xử lý"; vẫn có In PDF / Tải DOCX (ASM-007-09).
- Workflow: Nháp (người soạn: "Gửi duyệt"); Chờ trưởng khoa duyệt (trưởng khoa cùng khoa: "Đồng ý", "Từ chối"); Chờ hội đồng thẩm định (thư ký: "Thông qua", "Từ chối"; thành viên khác chỉ ghi ý kiến); Chờ ban hành (giám đốc: "Ban hành", "Từ chối"); Đã ban hành / Đã thay thế / Đã thu hồi (chỉ đọc, In/DOCX).

**API**: mở → `get_procedure`, `get_review`; hành động → `apply_action`; ý kiến → `add_review_comment`, `set_comment_resolved`; tệp → `download_pdf`, `download_docx`. Trình duyệt không ghi thẳng DocType.

## SCR-DSK-009 (thay đổi nhỏ)
- Thêm nút "Gửi duyệt" ở thanh trên khi `get_review.actions` có "Gửi duyệt" (cùng hộp thoại ở trên).
- Ở "Nháp" sau khi bị trả lại: dải lý do từ chối và huy hiệu "Ý kiến: n" trên thẻ bước; thẻ "Ý kiến thẩm định" chỉ đọc ở cột phải (TC-WF-08 "hiển thị tại bước đó cho người soạn").

## Form Desk NC Clinical Procedure
- Frappe Workflow tự hiện nút "Hành động". `nc_clinical_procedure.js` bắt `before_workflow_action`: mở cùng hộp thoại như trên (Từ chối: lý do; Ban hành: số QĐ, ngày; Gửi duyệt: không), gọi `apply_action`, rồi `frm.reload_doc()` và trả promise bị từ chối để Frappe không gọi `apply_workflow` (ASM-007-13). Lỗi kiểm tra hiện bằng `frappe.msgprint` liệt kê.
- Bỏ nút tạm "Ban hành" của FEAT-006 (thay bằng nút workflow). Thêm nút "In PDF", "Tải DOCX" (nhóm "Xuất") và "Mở chế độ thẩm định" (mở `procedure-editor` với quy trình). Dải thông báo chỉ đọc theo `design.md` mục 3 khi ≠ "Nháp".

## SCR-DSK-007 Danh sách quy trình
`nc_clinical_procedure_list.js` `get_indicator` theo bảng màu design.md cho 7 trạng thái (Nháp `gray`; Chờ trưởng khoa duyệt, Chờ hội đồng thẩm định, Chờ ban hành `orange`; Đã ban hành `green`; Đã thay thế `darkgrey`; Đã thu hồi `red`).

## NC Settings (form chuẩn)
Section "Phê duyệt quy trình": "Số ngày nhắc duyệt", "Thư ký hội đồng" (Link User, lọc người có vai trò NC Council Member qua `set_query`).

## NC Review Comment (form, list chuẩn)
List: cột Bản ghi, Phần, Mã bước, Đã xử lý, người tạo; lọc chuẩn Bản ghi, Đã xử lý. Chủ yếu dùng qua SCR-DSK-010.

## Mẫu in (PDF) và DOCX
Theo `technical-design.md` mục 6. Kiểm bằng mắt (TC-PROC-07 loại M): chữ "DỰ THẢO" đọc được nhưng không che nội dung; khối chữ ký không vỡ trang giữa ô; tiếng Việt có dấu hiển thị đúng.

## Tiếp cận, bàn phím, chuỗi (NFR-USE-004)
- Tab đi qua: thanh duyệt → bảng tóm tắt khác biệt → nội dung → cột phải; Enter trên dòng tóm tắt khác biệt cuộn và chọn bước; Esc đóng hộp thoại; sau khi đóng hộp thoại tiêu điểm về nút đã mở nó.
- Viền focus `outline: 2px solid var(--primary)`; chỉ biến CSS Desk (`--text-color`, `--text-muted`, `--border-color`, `--card-bg`, `--primary`, `--red-600`, `--green-800`, `--orange-700`, `--yellow-*` cho dải lý do từ chối kèm chữ đen ≥ 4,5:1); mọi nhãn màu kèm chữ; huy hiệu "Ý kiến: n" có `aria-label` "n ý kiến chưa xử lý".
- Mọi chuỗi qua `__()` (JS) / `_()` (Python), nguồn tiếng Anh, bản dịch `normcore/translations/vi.csv` (giữ thứ tự, không trùng khóa).
- Kiểm 1366 × 768: thanh duyệt một hàng, không tràn ngang; 768 px: một cột. QA kiểm bằng Playwright trên staging theo tiền lệ ASM-006-01.
