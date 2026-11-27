# FEAT-026 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-025 "Giá tham chiếu" (L + F: "Đơn vị, giá, nguồn; nhập tệp; rà soát dòng "Đề xuất""; trạng thái "Chưa gắn mã; chưa xác nhận"); `design.md` mục 3 (nhãn trạng thái `indicator-pill`, dòng đề xuất nhãn "Đề xuất"); `technical-design.md` (TD) 2, 3.4. Dùng Desk chuẩn (List + Form), không trang Vue. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch `normcore/translations/vi.d/FEAT-026.csv`; thông báo máy chủ tiếng Việt. Chạy được ở 1366 × 768; bàn phím (Tab, Enter, Esc); chỉ biến CSS và lớp của Desk, không tự đặt màu chữ. Không có nút hay chữ "AI" nào (FR-AI-015; AI thuộc FEAT-027).

## SCR-DSK-025 Giá tham chiếu — danh sách NC Benchmark Price (`nc_benchmark_price_list.js`)

### Cột và bộ lọc
- Cột: Đơn vị, Tên dịch vụ gốc, Dịch vụ, Giá (định dạng tiền NFR-LOC-001), Ngày hiệu lực, Trạng thái.
- Bộ lọc chuẩn: Đơn vị, Dịch vụ, Loại giá, Ngày hiệu lực, Trạng thái. Mặc định không lọc.
- `get_indicator`:

| Điều kiện | Nhãn | Màu |
| :-- | :-- | :-- |
| `status = Đã xác nhận` | "Confirmed" ("Đã xác nhận") | `green` |
| `status = Đề xuất`, có `technical_service` | "Proposed" ("Đề xuất") | `purple` |
| `status = Đề xuất`, chưa có `technical_service` | "No service code" ("Chưa gắn mã") | `orange` |
| `status = Loại bỏ` | "Rejected" ("Loại bỏ") | `gray` |

- Hai bộ lọc nhanh (nút `btn-default btn-xs` ở thanh danh sách): "Needs review" ("Cần rà soát") = `status = Đề xuất`; "No service code" ("Chưa gắn mã") = `status = Đề xuất` và `technical_service` trống.

### Nút ở thanh danh sách (chỉ hiện khi `frappe.model.can_create("NC Benchmark Price")`: NC Finance, NC Consultant)
- "Download template" ("Tải tệp mẫu") → `normcore.api.importer.download_template?import_set=nc_benchmark_price` (như FEAT-005).
- "Import from Excel" ("Nhập từ Excel") → `frappe.set_route("import-excel")` với bộ nhập "Giá tham chiếu" chọn sẵn (tham số route nếu trang hỗ trợ; không thì người dùng chọn). Trang `import-excel` có sẵn của FEAT-004 hiển thị Kiểm tra / Xác nhận ghi và lỗi theo dòng (dòng trùng: "trùng giá tham chiếu …").
- Hành động hàng loạt (menu "Actions" khi chọn dòng, chỉ người có quyền ghi): "Confirm" ("Xác nhận") → `confirm_prices(names)`; "Reject" ("Loại bỏ") → `reject_prices`; "Reopen" ("Mở lại để rà soát") → `reopen_prices`. Hộp xác nhận trước khi gọi: "Confirm {0} reference prices?" ("Xác nhận {0} giá tham chiếu?"). Kết quả: `frappe.show_alert` số dòng đã đổi; lỗi dòng (chưa gắn mã, dòng đã loại bỏ) liệt kê trong `frappe.msgprint` dạng bảng mã · lý do. Danh sách tự tải lại.

### Trạng thái rỗng
- Chưa có dòng nào: thông điệp Desk mặc định + nút "Import from Excel" (người có quyền tạo).

## Form NC Benchmark Price (`nc_benchmark_price.js`)

Bố cục (hai cột, khối có tiêu đề):

| Khối | Trường |
| :-- | :-- |
| "Dịch vụ" | `facility`, `service_name_raw` · `technical_service`, `status` |
| "Giá" | `price`, `price_category` · `effective_date` |
| "Nguồn" | `source_doc_no`, `source_url` · `source_file` |
| "Giá hiệu chỉnh" | `adjusted_html` |
| "Xác nhận" (thu gọn) | `verified_by`, `verified_on`, `ai_log` |

- `status`: chỉ đọc trên form (`read_only = 1` trong JSON); đổi bằng nút để luôn qua `confirm_prices`/`reject_prices`/`reopen_prices`.
- Dải nhắc (`frm.dashboard.set_headline_alert`, lớp `alert-warning`) khi `status = Đề xuất`:
  - có `technical_service`: "Proposed match: {0}. Check and confirm." ("Đề xuất khớp: {0}. Kiểm tra rồi xác nhận.") — `{0}` = mã · tên dịch vụ.
  - chưa có: "No matching service found. Choose a service, then confirm." ("Chưa tìm được dịch vụ khớp. Chọn dịch vụ rồi xác nhận.").
- Nút (người có quyền ghi, bản đã lưu):
  - `status = Đề xuất`: "Confirm" ("Xác nhận", nút chính) → `confirm_prices([name], technical_service)` (gửi `technical_service` hiện trên form để người dùng đổi cặp khớp trước khi xác nhận; form chưa lưu thì lưu trước); "Reject" ("Loại bỏ").
  - `status = Đã xác nhận` hoặc `Loại bỏ`: "Reopen" ("Mở lại để rà soát") trong nhóm "Actions".
- `adjusted_html`: khi tải form gọi `get_adjusted_price(name)`; hiện "Adjusted to {0}: {1} (index {2} → {3})" ("Giá hiệu chỉnh đến tháng {0}: {1} (chỉ số {2} → {3})"); thiếu chỉ số: "No CPI for month {0}; price not adjusted" ("Chưa có chỉ số giá tháng {0}; chưa hiệu chỉnh"). Bản chưa lưu: không gọi.
- NC Auditor, NC Department Head, NC Director, NC Admin: form chỉ đọc, không có nút.

## Danh sách và form NC Benchmark Facility

- Cột: Tên đơn vị, Tỉnh/thành phố, Loại hình, Hạng. Bộ lọc: Tỉnh, Loại hình.
- Form: một khối, bốn trường bắt buộc (dấu `*` chuẩn Desk). Thiếu trường → thông báo bắt buộc chuẩn của Frappe (TC-BM-06).
- Nút "Price survey" ("Lập phiếu khảo sát giá", người có quyền tạo NC Benchmark Price, bản đã lưu) → `frappe.ui.Dialog`:
  - `price_category` (Link NC Price Category, bắt buộc), `specialty` (Link NC Specialty), `services` (Table MultiSelect / MultiSelectList NC Technical Service). Phải chọn chuyên khoa **hoặc** ít nhất một dịch vụ; thiếu → thông báo "Choose a specialty or services" ("Chọn chuyên khoa hoặc dịch vụ").
  - "Download" ("Tải phiếu") → `window.open` tới `normcore.api.benchmark.download_price_survey` với tham số; Esc đóng hộp.
- Thẻ liên kết (connections): "Giá tham chiếu" (NC Benchmark Price theo `facility`).

## Danh sách và form NC CPI Index

- Cột: Tháng (hiện `MM/YYYY`), Chỉ số giá, Nguồn; sắp theo tháng giảm dần.
- Form: `month` (Date; mô tả "Ngày bất kỳ trong tháng; lưu về ngày 1"), `index_value`, `source` (mô tả "Giả định — chờ xác nhận: nguồn chỉ số giá chưa chốt (TBD-11)").

## Workspace

`shortcuts.d/FEAT-026.txt`: "Đơn vị tham chiếu" (NC Benchmark Facility, List), "Giá tham chiếu" (NC Benchmark Price, List), "Chỉ số giá tiêu dùng" (NC CPI Index, List); chạy `python3 scripts/build_workspace.py`.

## Kiểm giao diện

- Test tĩnh `normcore/tests/unit/test_feat_026_ui.py` (kiểu `test_feat_025_ui.py`): mọi chuỗi trong `__()` của ba tệp JS có trong `vi.d/FEAT-026.csv`; list JS gọi đúng `confirm_prices`, `reject_prices`, `reopen_prices`, `download_template?import_set=nc_benchmark_price`; form JS gọi `get_adjusted_price`; facility JS gọi `download_price_survey`; không có chuỗi "AI".
- Trên staging (QA/người duyệt): SCR-DSK-025 ở 1366 × 768, nhãn trạng thái bốn màu, nhập tệp mẫu, xác nhận hàng loạt.
