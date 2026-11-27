# FEAT-038 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-003 ("Loại Tài liệu của hãng có bảng mặt hàng, thiết bị liên quan"), SCR-DSK-014 ("Dòng đề xuất AI"), SCR-DSK-033 ("đề xuất AI chưa xử lý"); `design.md` mục 3 ("Dòng đề xuất của AI": nền nhấn nhẹ, nhãn "Đề xuất" `purple`, hai nút nhỏ "Chấp nhận" và "Bỏ"; **[1.1]** dùng cùng kiểu cho đề xuất định mức và kế hoạch chất lượng lấy từ tài liệu của hãng; nhãn quan hệ trích dẫn "Theo hướng dẫn" `green`, "Chưa có căn cứ" `red`); `technical-design.md` (TD) mục 3.3–3.7; AMD-025-02, ASM-038-13 (không sửa `NormGrid.vue`, `api/norm.py`).

Quy ước chung: chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.d/FEAT-038.csv` (nêu trong ngoặc dưới đây); thông báo máy chủ tiếng Việt qua `_()`. Chạy được ở 1366 × 768 (hộp thoại `size: "extra-large"`, bảng cuộn dọc trong hộp thoại, không cuộn ngang ở 1366 px); thao tác được bằng bàn phím (Tab tới nút, Enter bấm, Esc đóng hộp thoại); chỉ dùng `indicator-pill`, `alert-*`, `frappe.ui.Dialog`, `frm.dashboard.set_headline` và biến CSS của Desk (NFR-USE-004: không tự đặt màu chữ). FR-AI-015: AI tắt (`normcore.ai.enabled()` = false) thì không có nút "AI đề xuất định mức"; đề xuất cũ vẫn xem, chấp nhận, bỏ được (FR-AI-008).

## SCR-DSK-003 Văn bản và mục — form NC Legal Document (mở rộng, Form Desk chuẩn)

- Trường `doc_type` thêm lựa chọn "Tài liệu của hãng".
- Khi `doc_type` = "Tài liệu của hãng": hiện section "Related items and equipment" ("Mặt hàng, thiết bị liên quan") ngay sau "Thay thế", chứa bảng `related_resources` (cột: Loại danh mục, Mặt hàng/thiết bị). Ô `linked_doctype` lọc chỉ NC Item, NC Equipment (`frm.set_query`). Mô tả trường: "Bắt buộc với tài liệu của hãng. AI chỉ dùng tài liệu này cho hệ thống xét nghiệm có các mặt hàng, thiết bị ở đây."
- Nhãn trường `doc_number` giữ "Số hiệu"; mô tả khi loại là tài liệu của hãng: "Mã tài liệu của hãng kèm phiên bản" (`frm.set_df_property`, ASM-038-01).
- Lỗi lưu (bảng trống, loại danh mục sai, dòng trùng): thông báo máy chủ (TD 2.1), form giữ dữ liệu.
- Người chỉ đọc (Clinician, Auditor…): form chỉ đọc như FEAT-020, bảng hiện.
- API: không có API mới; lưu bằng form chuẩn.

## Thành phần dùng chung — `normcore/public/js/cls_norm_suggest.js`

`normcore.cls_norm_ai.attach(frm, test_system)`; gọi từ `refresh` của hai form dưới, chỉ khi `test_system` có giá trị và bản ghi đã lưu. Mọi lời gọi đều tới `normcore.api.cls_norm_ai.*`.

1. **Đếm và dải**: gọi `list_cls_norm_suggestions(test_system)` (một lần mỗi `refresh`). `pending > 0` → `frm.dashboard.set_headline(__("{0} AI suggestions not yet processed", [n]))` ("{0} đề xuất AI chưa xử lý") màu `purple`/indicator, kèm liên kết "Review" ("Xem").
2. **Nút "AI norm suggestion" ("AI đề xuất định mức")**, nhóm nút "AI": hiện khi `ai_enabled` và `can_edit` (quyền ghi NC Test System trong phạm vi khoa). Bấm → `start_cls_norm_suggestion(test_system)`:
   - `job_id` rỗng kèm `message` → `frappe.msgprint(message)`.
   - Có `job_id`: nút đổi "Running…" ("Đang chạy…"), vô hiệu; theo dõi realtime `normcore_cls_norm_ai` và hỏi `get_cls_norm_suggestion_status` mỗi 3 giây.
   - `done` → `frappe.show_alert({message: __("{0} suggestions created ({1} without basis, {2} not in catalog)", …), indicator: "green"})` ("Đã tạo {0} đề xuất ({1} chưa có căn cứ, {2} ngoài danh mục)"), mở hộp thoại xem.
   - `failed` → `frappe.msgprint({indicator: "red", title: __("AI suggestion failed"), message: error})` ("Đề xuất bằng AI không thực hiện được"); thêm câu "Your data is unchanged." ("Dữ liệu của bạn được giữ nguyên.") (UC-025 3c). Nút trở lại bình thường.
3. **Nút "Review AI suggestions" ("Xem đề xuất AI")**: hiện khi `pending > 0`, cho mọi người đọc được (gồm NC Auditor, Finance). Mở hộp thoại.
4. **Hộp thoại "AI norm suggestions" ("Đề xuất định mức của AI")** — `frappe.ui.Dialog`, một trường HTML vẽ bảng, nhóm theo `suggestion_type` theo thứ tự: Lượng hóa chất mỗi test, Tần suất chuẩn máy, Tần suất nội kiểm, Hạn dùng sau mở. Bộ lọc nhỏ trên bảng: "Pending" ("Chờ xử lý", mặc định) / "All" ("Tất cả") → gọi lại `list_cls_norm_suggestions(test_system, status)`.

   | Cột | Nội dung |
   | :-- | :-- |
   | Mặt hàng, thiết bị | Nhãn danh mục (`resource` – tên) hoặc `resource_text` kèm nhãn `orange` "Not in catalog" ("Ngoài danh mục") |
   | Giá trị đề xuất | `value` định dạng số theo NFR-LOC-001 + `uom`; căn phải |
   | Căn cứ | "Theo hướng dẫn" `green` + "<số hiệu> – mục <section_no>" (liên kết mở form NC Legal Section) và đoạn trích nguyên văn trong `<blockquote>` rút gọn 200 ký tự, có "Show more" ("Xem thêm"); hoặc nhãn `red` "Chưa có căn cứ" |
   | Trạng thái | Nhãn `purple` "Đề xuất" khi chờ; `green` "Đã chấp nhận"; `darkgrey` "Đã bỏ" |
   | Thao tác | Khi chờ: nút nhỏ "Accept" ("Chấp nhận", `btn-primary btn-xs`) khi `can_accept`; "Reject" ("Bỏ", `btn-default btn-xs`) khi `can_edit`; khi ngoài danh mục: nút "Link" ("Liên kết") thay "Chấp nhận" |

   - Dòng chờ dùng nền nhấn nhẹ (`var(--highlight-color)` hoặc lớp tiện ích tương đương của Desk), như "Dòng đề xuất của AI".
   - "Liên kết": hộp thoại nhỏ hai trường `resource_doctype` (Select NC Item / NC Equipment) và `resource` (Dynamic Link) → `link_cls_norm_suggestion`; xong nạp lại bảng, dòng hiện nút "Chấp nhận" (FR-AI-018).
   - "Chấp nhận" → `frappe.confirm(__("Apply {0} = {1} {2} to {3}?", …))` ("Áp {0} = {1} {2} vào {3}?", {3} = "bộ định mức Nháp"/"kế hoạch chất lượng"/"danh mục mặt hàng") → `accept_cls_norm_suggestion(name)`. Thành công: `show_alert` xanh, nạp lại bảng, `frm.reload_doc()`. Lỗi (không có bộ Nháp, không có dòng kế hoạch, thiếu quyền): `msgprint` thông báo máy chủ, dòng giữ "Đề xuất".
   - "Bỏ" → `reject_cls_norm_suggestion(name)`, không hỏi xác nhận; nạp lại bảng.
   - Không có nút "Chấp nhận tất cả" (mỗi đề xuất ghi vào bản ghi đích khác nhau, cần người xem từng số; ASM-038-08).
   - Rỗng: "No pending AI suggestions." ("Không có đề xuất AI nào chờ xử lý."). Đang tải: `frappe.dom.freeze` không dùng; trường HTML hiện "Loading…" ("Đang tải…"). Lỗi tải: thông báo máy chủ trong trường HTML.
   - Không quyền (`list_*` trả `PermissionError`): không hiện dải, nút; không báo lỗi trên form.
   - NC Auditor, Finance (chỉ đọc đề xuất): thấy bảng, không có nút ghi. Resource Mgr/Finance thấy nút "Chấp nhận" chỉ ở dòng "Hạn dùng sau mở" (`can_accept` do máy chủ tính, ASM-038-07).

## SCR-DSK-033 Kế hoạch chất lượng — form NC QC Plan (mở rộng, Form Desk chuẩn)

- `nc_qc_plan.js` `refresh`: khối `// FEAT-038` gọi `normcore.cls_norm_ai.attach(frm, frm.doc.test_system)`. Bố cục và trường của form giữ như FEAT-034/035; số test ước tính (`estimate_html`) không đổi khi có đề xuất chờ (đề xuất không vào phép tính, FR-AI-008).
- Trạng thái "đề xuất AI chưa xử lý" = dải headline ở mục 1 của thành phần dùng chung.
- Sau khi chấp nhận tần suất nội kiểm/chuẩn máy, `reload_doc` làm số trong bảng `iqc_lines`/`calibration_lines` và số test ước tính cập nhật.

## SCR-DSK-014 Lưới định mức — form NC Norm Set (mở rộng; lưới Vue không đổi)

- Theo AMD-025-02 và ASM-038-13: `NormGrid.vue`, `normcore/public/js/norm_grid/`, `normcore/api/norm.py` **không sửa**. Phần đề xuất của FEAT-038 nằm trên form NC Norm Set (nơi có nút mở lưới), khối riêng `// FEAT-038` trong `nc_norm_set.js`, ngoài khối `FEAT-014, AMD-014-01` và `FEAT-025, AMD-025-02`.
- Chỉ khi `frm.doc.test_system` có giá trị: gọi `normcore.cls_norm_ai.attach(frm, frm.doc.test_system)`. Dải headline của FEAT-025 (đề xuất liên kết) và của FEAT-038 cùng có thì nối hai câu trong một headline (FEAT-038 thêm câu sau, cách bằng " · ").
- Nút "AI đề xuất định mức" chỉ hiện khi bộ "Nháp" (ngoài điều kiện chung). Bộ đã xác nhận/khóa: vẫn có "Xem đề xuất AI"; "Chấp nhận" lượng hóa chất báo lỗi máy chủ "Chưa có bộ định mức Nháp…".
- Sau khi chấp nhận lượng hóa chất: `reload_doc`; dòng được áp hiện trên lưới như dòng thường, chưa xác nhận (người soạn xác nhận lại trên lưới như FEAT-012).

## Kiểm tra (test unit đọc mã, `normcore/tests/unit/test_feat_038_ui.py`)

- `cls_norm_suggest.js` chỉ gọi `normcore.api.cls_norm_ai.(start_cls_norm_suggestion|get_cls_norm_suggestion_status|list_cls_norm_suggestions|accept_cls_norm_suggestion|reject_cls_norm_suggestion|link_cls_norm_suggestion)`.
- Nút AI có điều kiện `normcore.ai.enabled()`; nút ghi có điều kiện `can_edit`/`can_accept`.
- Mọi chuỗi trong `__()` của ba tệp JS có dòng trong `vi.d/FEAT-038.csv`.
- `hooks.py` `doctype_js` có NC QC Plan, NC Norm Set trỏ `public/js/cls_norm_suggest.js` và giữ NC Technical Service.
- Không có thay đổi ở `normcore/public/js/norm_grid/`, `normcore/api/norm.py` (so `origin/develop`).
