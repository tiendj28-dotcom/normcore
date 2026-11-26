# FEAT-021 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-012 ("L có bộ lọc sẵn": quy trình mang cờ "Cần rà soát" và trích dẫn bị ảnh hưởng; hành động "Sửa đổi", "Không cần sửa"), SCR-DSK-003 ("khai báo thay thế"), SCR-DSK-007 (lọc cờ "Cần rà soát"); `design.md` mục 3–5, 7; technical-design mục 2, 4. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `vi.csv` (cùng cách FEAT-020, FEAT-022); nhãn DocType và thông báo máy chủ tiếng Việt. Ngày `dd/mm/yyyy` (NFR-LOC-001) qua `frappe.datetime.str_to_user`. Mọi chuỗi dữ liệu chèn vào HTML phải qua `frappe.utils.escape_html`.

Màu chỉ báo (`indicator-pill`, `design.md` mục 3):

| Giá trị | Lớp |
| :-- | :-- |
| Cần rà soát | `yellow` |
| Còn hiệu lực | `green` |
| Hết hiệu lực | `darkgrey` |
| Chưa hiệu lực | `yellow` |
| Đã ban hành | `green` |
| Quan hệ trích dẫn: Theo hướng dẫn / Khác biệt / Chưa có căn cứ | `green` / `orange` / `red` |

## SCR-DSK-003 Văn bản và mục — phần "Thay thế" (Form NC Legal Document, mở rộng)
Loại: Form chuẩn của Desk. Tệp: mở rộng `normcore/nc_library/doctype/nc_legal_document/nc_legal_document.js` (hàm vẽ tách riêng `normcore/public/js/library_supersession.js` nếu dài hơn ~150 dòng, nạp qua `doctype_js`).

**Bố cục:** section "Thay thế" (`supersession_section`) nằm sau "Các mục", trước "Ánh xạ hướng dẫn":
1. Bảng con `supersessions` (lưới chuẩn, chỉ đọc trên lưới — `editable_grid` = 0; mở dòng ra form dòng để sửa). Cột: Văn bản bị thay thế (liên kết), Phạm vi, Các mục bị thay thế, Từ ngày.
2. HTML `superseded_by_html` "Bị thay thế bởi": chỉ hiện khi `get_supersessions(...).superseded_by` có dòng. Mỗi dòng một hàng: liên kết số hiệu — tên văn bản A, "Toàn bộ" hoặc "Các mục: 2, 5", "từ dd/mm/yyyy". Không có dòng → ẩn cả khối (không hiện trạng thái trống).
3. Trường `expiry_date` đã có: khi văn bản bị thay thế toàn bộ, mô tả dưới trường (set bằng `frm.set_df_property(..., "description", ...)`) "Set by supersession: {0}" ("Đặt theo khai báo thay thế: {0}", {0} = số hiệu A).

**Hành động:**

| Nút / thao tác | Hiện khi | Gọi | Sau khi xong |
| :-- | :-- | :-- | :-- |
| "Declare supersession" ("Khai báo thay thế"), nút chính ở thanh form, nhóm riêng không | bản ghi đã lưu và `frm.perm[0].write` (NC Document Controller, NC Admin) | mở hộp thoại (dưới) | — |
| Hộp thoại "Khai báo thay thế": trường Văn bản bị thay thế (Link NC Legal Document, BB, lọc `name != frm.doc.name`), Phạm vi (Select Toàn bộ / Một phần, mặc định Toàn bộ), Các mục bị thay thế (MultiCheck, chỉ hiện khi Một phần; nạp bằng `get_sections(B)` sau khi chọn B, nhãn "{section_no} — {heading}", sắp theo `section_no`; B chưa lập chỉ mục → dòng chữ "Văn bản chưa lập chỉ mục, không chọn được mục" và khóa "Một phần"), Từ ngày (Date, BB). Dòng chú thích dưới Từ ngày, tự cập nhật: "{B} sẽ hết hiệu lực từ {dd/mm/yyyy} (ngày hết hiệu lực {D − 1})" | | `normcore.api.library.declare_supersession` (`sections` = mảng mã đã chọn) | `frappe.show_alert` xanh "Đã khai báo thay thế"; `frm.reload_doc()`; lỗi kiểm tra máy chủ hiện trong `frappe.msgprint` (mỗi lỗi một dòng), hộp thoại giữ nguyên dữ liệu |
| Nút xác nhận của hộp thoại: "Declare" ("Khai báo"). Trước khi gọi, hộp xác nhận nêu hệ quả: "Sau khi khai báo, {B} (hoặc các mục đã chọn) sẽ hết hiệu lực từ {ngày}; các quy trình đã ban hành có trích dẫn sẽ được gắn cờ Cần rà soát." | | | |

**Trạng thái:**
- Chưa lưu: không có nút.
- Chỉ đọc (NC Auditor, vai trò đọc khác): không có nút; bảng và khối "Bị thay thế bởi" vẫn hiện.
- Đang gọi: nút "Khai báo" khóa và có chỉ báo đang tải (`dialog.disable_primary_action` / `frappe.call` `freeze`).
- Lỗi mạng hoặc quyền: `frappe.call` hiện thông báo máy chủ; hộp thoại không đóng.

## SCR-DSK-012 Hàng đợi rà soát (Desk Page `review-queue`)
Loại: Desk Page (module NC Procedure, tệp `normcore/nc_procedure/page/review_queue/review_queue.{json,js,py}`), JS thuần dựng bằng `frappe.ui.make_app_page`, không Vue (ASM-021-10). Tiêu đề trang "Review queue" ("Hàng đợi rà soát"). Roles của Page: NC Clinician, NC Department Head, NC Council Member, NC Finance, NC Resource Manager, NC Document Controller, NC Director, NC Consultant, NC Admin, NC Auditor (mọi vai có quyền đọc quy trình; dữ liệu vẫn do `get_review_queue` lọc theo quyền và khoa). Lối tắt Workspace: `nc-rvq-s|Hàng đợi rà soát|review-queue|Page|`.

**Bố cục (từ trên xuống):**
1. Thanh lọc của trang (`page.add_field`): Khoa (Link NC Department; NC Department Head thấy sẵn khoa của mình qua phạm vi, vẫn để trống được). Đổi bộ lọc → tải lại trang 1. Bộ lọc sẵn cố định (không sửa được, hiện bằng chữ nhỏ dưới tiêu đề): "Đã ban hành · Cần rà soát".
2. Dòng tóm tắt: "{0} procedures need review" ("{0} quy trình cần rà soát").
3. Danh sách thẻ, mỗi quy trình một thẻ (`frappe-card`, khoảng cách bằng biến CSS của Desk):
   - Hàng đầu: liên kết tên quy trình (mở form), tên dịch vụ (`service_name`), khoa, "v{version_no}", chỉ báo `green` "Đã ban hành" và `yellow` "Cần rà soát"; bên phải: số quyết định, ngày hiệu lực.
   - Nếu `pending_revision`: dòng chú thích "Revision in progress: {0}" ("Đang có bản sửa đổi: {0}", liên kết mở trình soạn của bản đó).
   - Bảng trích dẫn bị ảnh hưởng (mỗi trích dẫn một hàng):

| Cột | Nội dung |
| :-- | :-- |
| Vị trí trong quy trình | `target_section` hoặc "Bước {target_step_id}" |
| Văn bản, mục | số hiệu (liên kết NC Legal Document) + "mục {section_no} — {heading}" (liên kết NC Legal Section) hoặc "(cả văn bản)" |
| Hiệu lực | chỉ báo `darkgrey` "Hết hiệu lực" + "từ {expiry_date + 1}" |
| Lý do | `reason` ("Văn bản hết hiệu lực" / "Mục hết hiệu lực") |
| Đoạn trích | `quote` rút gọn 160 ký tự, đầy đủ ở `title` |
| Văn bản thay thế | mỗi `replacements` một dòng: liên kết số hiệu A — tên, "toàn bộ" hoặc "các mục: …", "từ dd/mm/yyyy"; không có → "—" |

   - Không có trích dẫn nào (ASM-021-11): một dòng chữ "Affected citations could not be identified" ("Không xác định được trích dẫn bị ảnh hưởng").
   - Hàng nút cuối thẻ (chỉ khi `can_act`): "Revise" ("Sửa đổi", nút chính) và "No change needed" ("Không cần sửa", nút phụ). `can_act` = false (vai đọc, NC Auditor, trưởng khoa khoa khác): không có nút, không có chữ thay thế.
4. Dưới danh sách: nút "More" ("Xem thêm") khi `start + rows < total` (trang 50).

**Tương tác và API:**

| Hành động | Gọi | Sau khi xong |
| :-- | :-- | :-- |
| Mở trang, đổi bộ lọc, "Xem thêm" | `normcore.api.review.get_review_queue(department, start, page_length=50)` | vẽ lại / nối thêm thẻ |
| "Sửa đổi" | `normcore.api.procedure.create_revision(procedure)` | `existing` = 1 → alert "Đã có bản sửa đổi đang soạn" ; luôn `frappe.set_route("procedure-editor", name)` (tham số route giống nút "Revise" trên form FEAT-008) |
| "Không cần sửa" | mở `frappe.ui.Dialog`: "Reason" ("Lý do", Small Text, BB); chú thích "Cờ Cần rà soát sẽ được gỡ; lý do ghi vào lịch sử quy trình." Nút "Confirm" ("Xác nhận") → `normcore.api.review.dismiss_review(procedure, reason)` | alert xanh "Đã gỡ cờ cần rà soát"; bỏ thẻ khỏi danh sách, giảm số tóm tắt; lỗi máy chủ hiện trong hộp thoại, không đóng |

**Trạng thái:**
- Đang tải: khung xương 3 thẻ xám (`frappe.ui` skeleton hoặc chữ "Đang tải…"), nút khóa.
- Rỗng: "Không có quy trình nào cần rà soát. Quy trình được gắn cờ khi văn bản hoặc mục được trích dẫn hết hiệu lực." kèm nút "Open procedure list" ("Mở danh sách quy trình", route `/app/nc-clinical-procedure`).
- Lỗi tải: dải `alert-danger` có thông báo máy chủ và nút "Retry" ("Thử lại").
- Không có quyền (`PermissionError` khi gọi API, ví dụ người không có vai NC): dải "Bạn không có quyền xem quy trình" thay cho danh sách.
- Chỉ đọc (NC Auditor, vai đọc khác): như trên, không có nút hành động.
- Trạng thái workflow: hàng đợi chỉ chứa "Đã ban hành"; quy trình đã thành "Đã thay thế" rời hàng đợi ở lần tải sau.

**Bàn phím, kích thước, tương phản:** thẻ và nút theo thứ tự Tab tự nhiên (tên quy trình → liên kết trích dẫn → Sửa đổi → Không cần sửa); Enter kích hoạt nút; Esc đóng hộp thoại (mặc định Desk). Ở 1366 × 768 bảng trích dẫn vừa khung (cột Đoạn trích co giãn, xuống dòng); ở 768 px bảng cuộn ngang trong thẻ. Chỉ dùng biến CSS và lớp của Desk (tương phản ≥ 4,5:1, NFR-USE-004); nhãn màu luôn có chữ.

## SCR-DSK-007 / form NC Clinical Procedure (mở rộng nhỏ)
- List (`nc_clinical_procedure_list.js`): giữ chỉ báo trạng thái hiện có; khi `needs_review` = 1 và "Đã ban hành" thì chỉ báo là `yellow` "Cần rà soát" (bộ lọc `needs_review,=,1`). Bộ lọc cờ "Cần rà soát" của SCR-DSK-007 có sẵn qua trường Check `needs_review` ở thanh lọc chuẩn.
- Form (`nc_clinical_procedure.js`): khi `needs_review` = 1, dải thông báo `yellow` đầu form (`frm.dashboard.set_headline_alert`): "This procedure cites a legal document or section that is no longer in force. Review it in the review queue." ("Quy trình trích dẫn văn bản hoặc mục đã hết hiệu lực. Rà soát ở hàng đợi rà soát.") kèm nút "Open review queue" ("Mở hàng đợi rà soát") → `frappe.set_route("review-queue")`. Thông báo cho trưởng khoa (Notification Log) mở form này nên đây là đường vào chính từ thông báo.

## Kiểm (ghi vào implementation-log ở T07, T08)
- 1366 × 768 và 768 px: hộp thoại khai báo, trang hàng đợi với ≥ 3 trích dẫn mỗi thẻ không vỡ bố cục.
- Bàn phím: mở hộp thoại, chọn mục, khai báo; Tab tới "Không cần sửa", nhập lý do, Enter.
- Vai: NC Document Controller (có nút khai báo), NC Auditor (không nút, xem được bảng và hàng đợi), NC Department Head (chỉ khoa mình, có hai nút), NC Clinician (xem, không nút).
- Mọi chuỗi mới có trong `vi.csv`; `check_conventions.py` thoát 0.
