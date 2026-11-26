# FEAT-020 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-002, SCR-DSK-003; `design.md`; technical-design mục 2–4. Chỉ dùng List, Form chuẩn của Desk và `frappe.ui.Dialog`, không trang Vue. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `vi.csv`; nhãn DocType, thông báo máy chủ tiếng Việt. Màu chỉ báo dùng lớp `indicator-pill` của Desk, không mã màu cứng. Ngày dd/mm/yyyy (định dạng hệ thống, NFR-LOC-001).

Màu chỉ báo dùng chung:

| Giá trị | Lớp |
| :-- | :-- |
| Còn hiệu lực / Chưa hiệu lực / Hết hiệu lực | `green` / `blue` / `gray` |
| Chưa lập / Đang lập / Đã lập / Lỗi | `gray` / `orange` / `green` / `red` |

## SCR-DSK-002 Danh sách văn bản (List NC Legal Document)
Tệp: `nc_legal_document_list.js`.

- Cột: Số hiệu, Tên văn bản, Loại, Hiệu lực, Lập chỉ mục. `get_indicator` theo Hiệu lực (bảng trên); Lập chỉ mục hiển thị bằng formatter chỉ báo trong cột.
- Bộ lọc chuẩn (`in_standard_filter`): Số hiệu, Loại, Hiệu lực, Lập chỉ mục. Ô tìm của danh sách tìm theo Số hiệu, Tên (`search_fields`).
- Nút "Search in content" ("Tìm trong nội dung", phím tắt `Ctrl+Shift+F` đăng ký bằng `frappe.ui.keys.add_shortcut` khi ở trang này) mở hộp thoại tìm toàn văn:
  - Trường: Query (Data, BB, gợi ý "Từ khóa, cụm từ, số hiệu hoặc mã dịch vụ"), Type (Select loại văn bản, trống = tất cả), Validity (Select, trống = tất cả). Enter trong ô Query = Tìm.
  - Gọi `normcore.api.library.search_sections(query, mode="auto", doc_type, validity_status, start, page_length=20)`.
  - Kết quả (HTML trong hộp thoại, bảng): Số hiệu | Số mục | Tiêu đề | Trang (`page_from–page_to`, trống thì "—") | Hiệu lực (chỉ báo) | Khớp theo (`match`) | Đoạn trích (cụm từ tô bằng `<mark>`, nội dung đã escape). Dòng tiêu đề kết quả: "{0} results — searched by {1}" ({1} = nội dung / số hiệu / mã dịch vụ theo `mode`). Bấm một dòng → `frappe.set_route("Form", "NC Legal Section", section)`. Nút "More" tải trang kế khi `start + rows < total`.
  - Hộp thoại rộng `extra-large`; trên 1366 × 768 bảng cuộn dọc trong hộp thoại, cột Đoạn trích tự xuống dòng.
- Nút "New" chuẩn chỉ hiện với người có quyền tạo (Doc Controller, Admin).

## SCR-DSK-003 Văn bản và mục (Form NC Legal Document)
Tệp: `nc_legal_document.js`.

**Bố cục:**
1. Thông tin văn bản (2 cột): `doc_number`, `title`, `doc_type`, `issuer` | `issue_date`, `effective_date`, `expiry_date`, `validity_status` (chỉ đọc), `is_procedure_guideline`.
2. Tệp và lập chỉ mục: `file` | `index_status` (chỉ đọc), `index_error` (chỉ đọc, `depends_on: eval:doc.index_status=='Lỗi'`).
3. Các mục: `sections_html` (toàn chiều rộng).

Mô tả trường: `is_procedure_guideline` — "Bật nếu văn bản là hướng dẫn quy trình kỹ thuật: mỗi quy trình thành một mục"; `file` — "PDF hoặc DOCX, tối đa 100 MB".

**Tương tác:**
- Tiêu đề form có chỉ báo Hiệu lực; dưới tiêu đề (`frm.dashboard.set_headline`) theo Lập chỉ mục:
  - Chưa lập / Đang lập: "Indexing in progress. Sections will appear when it finishes." (màu `orange`), form tự làm mới mỗi 10 giây (`setTimeout` + `frm.reload_doc()`) tối đa 30 lần khi đang mở form, dừng khi rời form.
  - Lỗi: "Indexing failed: {0}" (`red`, {0} = `index_error`) kèm gợi ý "Replace the file or click Re-index."
  - Đã lập: "{0} sections" (`green`).
- Nút "Re-index" ("Lập lại chỉ mục") trong nhóm Actions, chỉ hiện khi `frm.perm[0].write` và `index_status` ≠ "Đang lập", không ở bản mới; xác nhận "Re-index this document? Manual edits to section text will be overwritten (kept in version history)." → `normcore.api.library.reindex(legal_document)` → làm mới form.
- `sections_html`: `normcore.api.library.get_sections(legal_document, start, page_length=100)` vẽ bảng: Số mục | Tiêu đề | Trang | Hiệu lực (chỉ báo) | nút "View" (mở form mục). Trên 100 mục có nút "More". Rỗng: "No sections yet" (Chưa lập/Đang lập/Lỗi) hoặc "No sections found in the file". Connections (`links`) nhóm "Mục" vẫn có để mở danh sách mục lọc theo văn bản.
- Khai báo thay thế (FEAT-021) và bảng mặt hàng, thiết bị liên quan (FEAT-038) chưa có ở FEAT này.

## Form mục — xem cạnh trang gốc (Form NC Legal Section; một phần SCR-DSK-003, FR-LIB-011, FR-LIB-012)
Tệp: `nc_legal_section.js`.

**Bố cục:**
1. Đầu (2 cột): `legal_document` (chỉ đọc), `section_no` (chỉ đọc), `heading` | `page_from`, `page_to` (chỉ đọc), `expiry_date`, `validity_status` (chỉ đọc).
2. Đối chiếu (2 cột bằng nhau): trái `plain_text` (Long Text, cao ~ 60vh), phải `source_view_html`.

**Khung trang gốc (`source_view_html`):** khi `refresh` gọi `normcore.api.library.get_source_view(section)`:
- PDF: `<iframe>` (cao bằng ô `plain_text`, `title` = "Original page") với `src = file_url + "#page=" + page_from`; trên khung có dòng "Pages {0}–{1} of {2}" (số hiệu) và nút "Open file" mở tệp ở thẻ mới. Tệp private: trình duyệt tải bằng phiên đăng nhập, Frappe kiểm quyền đọc văn bản.
- DOCX hoặc không có trang: "Original pages are not available for DOCX files." + nút "Download file" (ASM-020-06).
- Lỗi tải (mất quyền tệp, tệp bị xóa): thông báo "Cannot load the original file" trong khung, form vẫn dùng được.

**Sửa (FR-LIB-012):** `heading`, `plain_text`, `expiry_date` sửa được khi có quyền ghi (Doc Controller, Admin); lưu bằng Ctrl+S. Dòng thời gian (timeline) chuẩn của Desk hiển thị Version: giá trị trước/sau, người sửa, thời điểm. Khi `plain_text` vừa đổi, hiện ghi chú dưới trường: "The previous text is kept in the version history below."

## Workspace
Workspace "Normcore" thêm thẻ "Thư viện văn bản": liên kết "Văn bản pháp lý" (List NC Legal Document), "Mục văn bản" (List NC Legal Section).

## Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Rỗng | Danh sách: trạng thái trống chuẩn, nút tạo mới nếu có quyền. Tìm kiếm không kết quả: "No matching sections" |
| Đang tải | Chuẩn của Desk; hộp thoại tìm khóa nút Tìm và hiện "Searching…" trong khi gọi |
| Lỗi | Lỗi máy chủ (trùng số hiệu, tệp sai loại, quá 100 MB, truy vấn < 2 ký tự) hiện bằng `frappe.msgprint` tiếng Việt; trùng số hiệu có liên kết tới bản ghi trùng |
| Không có quyền | Trang không đủ quyền của Desk (người dùng không có vai trò NC nào); nút "Tìm trong nội dung" không hiện nếu không đọc được NC Legal Section |
| Chỉ đọc (NC Auditor, Clinician, Dept Head, Council, Finance, Resource Manager, Director, Consultant) | Form chỉ đọc, không nút lưu, không "Re-index", không nút tạo; vẫn tìm, xem mục, xem trang gốc |
| Lập chỉ mục: Chưa lập / Đang lập / Đã lập / Lỗi | Chỉ báo theo bảng màu ở đầu tệp; headline và nút như mục SCR-DSK-003 |
| Hiệu lực: Chưa / Còn / Hết | Chỉ báo ở danh sách, form văn bản, form mục, bảng mục, kết quả tìm |

Bàn phím: chuẩn Desk (Ctrl+S lưu, Ctrl+B tạo mới, Tab theo thứ tự trường); hộp thoại tìm: Enter tìm, Esc đóng, Tab qua các dòng kết quả (mỗi dòng là `<a>` focus được). 1366 × 768: form hai cột; khung đối chiếu hai cột mỗi bên ~ 50%. Tương phản (NFR-USE-004): chỉ lớp và biến CSS của Desk; `<mark>` dùng màu mặc định trình duyệt trên nền Desk.

API: `normcore.api.library.search_sections`, `get_sections`, `get_source_view`, `reindex`; lưu bằng API chuẩn của Form.
