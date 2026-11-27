# FEAT-027 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-025 "Giá tham chiếu" (L + F: "nhập tệp; rà soát dòng "Đề xuất""); `design.md` mục 3 (nhãn "Đề xuất", `indicator-pill`); `technical-design.md` (TD) 3.4, 3.5; FEAT-026 `ui-design.md` (danh sách, form, hành động xác nhận hàng loạt giữ nguyên). Desk chuẩn (Form + Dialog), không trang Vue. Chuỗi JS viết tiếng Anh trong `__()`, bản dịch ở `normcore/translations/vi.d/FEAT-027.csv`; thông báo máy chủ tiếng Việt. Chạy được ở 1366 × 768; Tab, Enter, Esc; chỉ lớp và biến CSS của Desk.

Mọi mã giao diện ở **một tệp mới** `normcore/public/js/benchmark_pdf_ai.js` (nạp qua `hook_registry/FEAT-027.json`). Không sửa `nc_benchmark_price_list.js`, `nc_benchmark_price.js`, `nc_benchmark_facility.js`, `vi.d/FEAT-026.csv` (ASM-027-10). Gắn bằng `frappe.ui.form.on("<DocType>", { refresh(frm) {...} })`, handler cộng dồn với handler của FEAT-026.

## SCR-DSK-025 (phần nhập tệp PDF) — form NC Benchmark Facility

### Nút
- "Extract price list from PDF (AI)" ("Trích bảng giá PDF (AI)"), nhóm nút "Price list" ("Bảng giá"). Hiện khi đủ ba điều kiện: `normcore.ai.enabled()` (FR-AI-015), `!frm.is_new()`, `frappe.model.can_create("NC Benchmark Price")` (NC Finance, NC Consultant). NC Auditor, NC Department Head, NC Director, NC Admin: không thấy nút. AI tắt: không có nút nào, không có chữ "AI" nào trên form; nút "Lập phiếu khảo sát giá" của FEAT-026 giữ nguyên.

### Hộp thoại `frappe.ui.Dialog` — "Extract price list from PDF" ("Trích bảng giá từ tệp PDF")

| Thứ tự | Trường | Kiểu | Bắt buộc | Ghi chú |
| :-: | :-- | :-- | :-: | :-- |
| 1 | `pdf_file` "PDF file" ("Tệp PDF") | Attach (`options: { restrictions: { allowed_file_types: [".pdf"] } }`, tải lên riêng tư, gắn `doctype = NC Benchmark Facility`, `docname = frm.doc.name`) | Có | |
| 2 | `price_category` "Price category" ("Loại giá") | Link NC Price Category | Có | ASM-027-03 |
| 3 | `source_doc_no` "Source document no." ("Số văn bản nguồn") | Data | | |
| 4 | `default_effective_date` "Default effective date" ("Ngày hiệu lực mặc định") | Date | | Mô tả: "Used for rows without a date in the file" ("Dùng cho dòng không ghi ngày trong tệp") |
| 5 | HTML ghi chú | | | "AI reads the file; every row is created as Proposed and must be checked against the original page before it is used for comparison." ("AI đọc tệp; mọi dòng tạo ở trạng thái "Đề xuất", cần đối chiếu với trang gốc trước khi dùng để so sánh.") |

- Nút chính "Extract" ("Trích"), Enter kích hoạt; Esc đóng. Thiếu trường bắt buộc → kiểm chuẩn của Dialog.
- Gọi `normcore.api.benchmark_ai.start_price_list_extraction({facility: frm.doc.name, price_category, file_url: pdf_file, source_doc_no, default_effective_date})`. Lỗi máy chủ (AI tắt, không phải PDF, không có quyền) → `frappe.msgprint` của Frappe, hộp thoại giữ nguyên để sửa.

### Đang chạy
- Có `job_id` → đóng hộp thoại, `frm.dashboard.set_headline_alert` lớp `alert-info`: "Extracting price list… You can keep working; the result will appear here." ("Đang trích bảng giá… Có thể làm việc khác; kết quả sẽ hiện ở đây.").
- Theo dõi: `frappe.realtime.on("normcore_price_list_ai", ...)` theo `job_id`, kèm hỏi lại `get_price_list_extraction_status(job_id)` mỗi 3 giây (dừng khi `done`/`failed`/`unknown` hoặc rời form), như `cls_norm_suggest.js`.

### Kết quả
- `done`: headline `alert-success` "{0} reference prices created as Proposed." ("Đã tạo {0} giá tham chiếu ở trạng thái "Đề xuất".") + nút trong dải "Review rows" ("Rà soát các dòng") → `frappe.set_route("List", "NC Benchmark Price", { ai_log: log })`. Có `duplicates`, `skipped` → `frappe.msgprint` bảng hai cột "Service name" ("Tên dịch vụ") · "Reason" ("Lý do"), tiêu đề "Some rows were not created" ("Một số dòng không được tạo"); `not_in_file` > 0 ghi thêm "{0} rows were not found in the file and were dropped." ("{0} dòng không thấy trong tệp, đã bỏ."). `created = 0` mà không lỗi: `alert-warning` "No price rows found in the file." ("Không tìm thấy dòng giá nào trong tệp.").
- `failed`: headline `alert-danger` với `message` của máy chủ (đã có gợi ý "Có thể nhập tay hoặc nhập từ Excel.") + hai nút "Enter manually" ("Nhập tay") → `frappe.new_doc("NC Benchmark Price", {facility})`, "Import from Excel" ("Nhập từ Excel") → `frappe.set_route("import-excel", {import_set: "nc_benchmark_price"})` (UC-013 2c).
- Mọi giá trị từ máy chủ hiển thị qua `frappe.utils.escape_html`.

## SCR-DSK-025 (rà soát) — form NC Benchmark Price, dòng do AI tạo

Thêm bằng `frappe.ui.form.on("NC Benchmark Price", { refresh })` trong cùng tệp; không dùng `set_headline_alert` (FEAT-026 dùng cho "Đề xuất khớp…").

- Khi `frm.doc.ai_log` có giá trị: `frm.dashboard.add_comment(...)`, lớp `blue`: "Extracted by AI from the source file. Check against the original page before confirming." ("Do AI trích từ tệp nguồn. Đối chiếu với trang gốc trước khi xác nhận."). Hiện cả khi AI đã tắt (dữ liệu lịch sử, không phải nút gọi AI).
- Có `source_url` → nút "Open original page" ("Mở trang gốc"), nhóm "Source" ("Nguồn"), `window.open(source_url)`; không có mà có `source_file` → mở `source_file`.
- Xác nhận, loại bỏ, mở lại: dùng nguyên nút của FEAT-026 (`confirm_prices` …). Dòng "Đề xuất" hiện nhãn tím/cam như FEAT-026.

## Danh sách NC Benchmark Price

Không đổi (ASM-027-01). Người dùng tới các dòng vừa trích bằng nút "Review rows" (lọc `ai_log`), hoặc lọc nhanh "Cần rà soát" có sẵn; xác nhận hàng loạt bằng menu "Actions" của FEAT-026.

## Trạng thái và quyền

| Trường hợp | Hiển thị |
| :-- | :-- |
| AI tắt | Không có nút, không hộp thoại; luồng tay/Excel của FEAT-026 (FR-AI-015) |
| Không có quyền tạo giá (Auditor, Dept Head, Director, Admin) | Không có nút; gọi API trực tiếp → `PermissionError` |
| Đơn vị chưa lưu | Không có nút |
| Đang chạy, rời form rồi quay lại | Không giữ tiến độ trên form; dòng đã tạo xem ở danh sách (đủ cho R3) |

## Kiểm giao diện

- Test tĩnh `normcore/tests/unit/test_feat_027_ui.py` (kiểu `test_feat_038_ui.py`): mọi chuỗi `__()` của `benchmark_pdf_ai.js` có trong `vi.d/FEAT-027.csv`; nút nằm trong nhánh `normcore.ai.enabled()` và `can_create("NC Benchmark Price")`; gọi đúng `start_price_list_extraction`, `get_price_list_extraction_status`; `hook_registry/FEAT-027.json` khai báo tệp JS; ba tệp JS của FEAT-026 không bị sửa (test cũ `test_khong_co_chu_ai` vẫn xanh).
- Trên staging (QA): form đơn vị ở 1366 × 768, hộp thoại dùng bàn phím, chạy với `normcore_ai_provider = "mock"` (provider giả lập trả JSON không có `rows` → dải `alert-danger` "Kết quả AI thiếu danh sách rows…" kèm hai nút "Nhập tay", "Nhập từ Excel": kiểm luồng UC-013 2c), tắt AI thì nút biến mất.
