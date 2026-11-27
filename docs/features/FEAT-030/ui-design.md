# FEAT-030 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-027 ("Dòng giá đề xuất; căn cứ điều chỉnh; xác nhận của khoa; phê duyệt"; trạng thái "dòng dưới giá thành", "chờ khoa", "chờ trình"), SCR-DSK-028 (FEAT-019); `design.md` mục 3 (màu nhãn: Nháp `gray`; Chờ khoa xác nhận, Chờ phê duyệt `orange`; Đã duyệt nội bộ chờ trình `blue`; Đã duyệt `green`; "Đã được cấp thẩm quyền duyệt" `green`; Vượt ngưỡng/dưới giá thành `red`); `technical-design.md` (TD) mục 2, 3.2–3.4.

Chuỗi JS viết tiếng Anh trong `__()`, bản dịch `normcore/translations/vi.d/FEAT-030.csv`; nhãn DocType và thông báo máy chủ tiếng Việt. Tiền, ngày theo NFR-LOC-001 (`format_currency`, `frappe.datetime.str_to_user`). Chạy được ở 1366 × 768; thao tác được bằng bàn phím; chỉ dùng lớp và biến CSS của Desk, không tự đặt màu chữ (NFR-USE-004).

## SCR-DSK-027 Phương án giá — Form/List chuẩn của Desk (NC Price Proposal)

Loại: Form và List chuẩn, mở rộng bằng `nc_price_proposal.js`, `nc_price_proposal_list.js`. Chuyển trạng thái qua `normcore.api.price_proposal.apply_action` (không qua nút workflow của Desk: JS ẩn menu "Actions" của workflow như form quy trình FEAT-007).

### Lối vào
- Form NC Costing Run `status = "Đã khóa"`, người có quyền create NC Price Proposal: nút "Create price proposal" ("Tạo phương án giá") nhóm "Create" → hộp thoại (Tên phương án, mặc định "Phương án giá {title}"; Ngày áp dụng) → `create_proposal` → mở form mới. Lần tính chưa khóa: không có nút.
- Workspace NC Benchmark: shortcut "Phương án giá" (List). Thông báo và "Việc chờ xử lý" (FR-NOTI-003) mở thẳng form.

### List
Cột: Tên phương án · Lần tính · Loại giá · Ngày áp dụng · Trạng thái (indicator theo bảng màu trên). Bộ lọc chuẩn: Trạng thái, Loại giá, Lần tính. Trưởng khoa chỉ thấy phương án có khoa mình (máy chủ lọc).

### Form — bố cục

**Đầu form**: tiêu đề · nhãn trạng thái · nút hành động (bên phải, theo `get_proposal.actions`).

**Thanh tóm tắt** (HTML, trên section đầu, từ `get_proposal.summary`): "{n} services · {a} adjusted · {b} below full cost · {u} awaiting director acknowledgement" ("{n} dịch vụ · {a} dòng điều chỉnh · {b} dòng dưới giá thành · {u} dòng chờ giám đốc xác nhận"). Có dòng dưới giá thành: `alert-warning` "Some proposed prices are below full cost; the director must acknowledge each of these lines when approving" ("Có giá đề xuất thấp hơn giá thành toàn bộ; Giám đốc phải xác nhận riêng từng dòng khi phê duyệt").

**Section "Thông tin"** (2 cột): Tên phương án, Lần tính giá (link) · Loại giá, Cấp phê duyệt (chỉ đọc), Ngày áp dụng (bắt buộc hiển thị `*` khi cấp "Bệnh viện").

**Section "Dòng giá đề xuất"**: lưới `items`, cột: Dịch vụ · Khoa · Giá thành toàn bộ · Giá tính toán · Giá làm tròn · Trung vị tham chiếu (trống → "—", tooltip "Not enough comparison data" / "Chưa đủ dữ liệu so sánh") · Số đơn vị · Giá đề xuất · Căn cứ điều chỉnh · Dưới giá thành · GĐ xác nhận · Giá cấp thẩm quyền (chỉ hiện khi trạng thái "Đã duyệt nội bộ, chờ trình" trở đi).
- Sửa được: chỉ "Giá đề xuất", "Căn cứ điều chỉnh" ở "Nháp" với NC Finance. Không thêm/xóa dòng (`cannot_add_rows`, `cannot_delete_rows`).
- Dòng `below_cost`: ô Giá đề xuất có nhãn `red` "Below cost" ("Dưới giá thành") — dùng `formatter` của lưới (lớp `indicator-pill red`), không đổi màu chữ tự đặt.
- Dòng giá đề xuất khác giá làm tròn mà căn cứ trống: ô Căn cứ có nhãn `orange` "Basis required" ("Cần căn cứ") (FR-PRICE-002). Sửa giá đề xuất → tính lại `below_cost` phía khách để hiển thị ngay; máy chủ đặt lại khi lưu.
- Nút nhỏ trên lưới "Reset to rounded price" ("Đặt lại theo giá làm tròn") cho dòng đang chọn (chỉ Nháp).

**Section "Xác nhận của khoa"** (hiện từ "Chờ khoa xác nhận"): bảng HTML từ `get_proposal.confirmations`: Khoa · Trạng thái (`orange` "Chờ xác nhận" / `green` "Đã xác nhận") · Người xác nhận · Thời điểm · Ghi chú. Trưởng khoa: dòng khoa mình được tô nền `--control-bg`.

**Section "Văn bản phê duyệt của cấp thẩm quyền"** (hiện khi cấp "Cơ quan có thẩm quyền" và trạng thái "Đã duyệt nội bộ, chờ trình" trở đi): Số văn bản, Ngày văn bản (chỉ đọc). Trạng thái "Đã duyệt nội bộ, chờ trình": `alert-info` "Approved internally, awaiting submission to the competent authority" ("Đã duyệt nội bộ, chờ trình cấp có thẩm quyền").

**Lịch sử**: timeline chuẩn của Desk (comment "Workflow" cho từng hành động, lý do từ chối).

### Hành động (nút chính, theo `actions` máy chủ trả)

| Nút | Người, trạng thái | Tương tác | API |
| :-- | :-- | :-- | :-- |
| "Submit for review" ("Gửi duyệt") | NC Finance, Nháp | Form bẩn → lưu trước. Lỗi máy chủ (danh sách dòng thiếu căn cứ, thiếu ngày áp dụng) hiện `msgprint` tiêu đề "Chưa gửi duyệt được"; các dòng lỗi được đánh dấu | `apply_action(action="Gửi duyệt")` |
| "Confirm" ("Xác nhận") | Trưởng khoa có khoa trong `my_departments` | Hộp thoại: danh sách khoa của mình còn chờ (Check, mặc định chọn hết) + "Ghi chú" (tùy chọn) | `apply_action(action="Xác nhận", department=…)` (gọi một lần mỗi khoa đã chọn) |
| "Approve" ("Phê duyệt") | NC Director, Chờ phê duyệt | Hộp thoại: bảng các dòng `below_cost` (Dịch vụ · Giá đề xuất · Giá thành toàn bộ · Check "Tôi xác nhận dòng này"), nút "Approve" chỉ bật khi đã tích đủ; không có dòng dưới giá thành thì hộp thoại xác nhận ngắn. Máy chủ vẫn kiểm (TC-PRICE-03) | `apply_action(action="Phê duyệt", acknowledged=[…])` |
| "Reject" ("Từ chối") | Trưởng khoa (Chờ khoa xác nhận), NC Director (Chờ phê duyệt) | `frappe.prompt` Small Text bắt buộc "Reason" ("Lý do"); trống không gửi được | `apply_action(action="Từ chối", reason=…)` |
| "Record authority decision" ("Ghi kết quả phê duyệt") | NC Finance, Đã duyệt nội bộ, chờ trình | Hộp thoại: Số văn bản (bắt buộc), Ngày văn bản (bắt buộc), Ngày áp dụng (mặc định ngày áp dụng của phương án), bảng Dịch vụ · Giá đã trình (chỉ đọc) · Giá được duyệt (Currency, mặc định = giá đã trình, bắt buộc) | `record_authority_result` |
| "Export price comparison" ("Xuất bảng so sánh giá") | mọi người đọc được phương án | tải `.xlsx` | `export_price_comparison(proposal)` |
| "Open price comparison" ("Mở Bàn so sánh giá") | người đọc được lần tính | `frappe.set_route("price-compare", {run})` | — |

Sau mỗi hành động: `frm.reload_doc()`, `show_alert` "Moved to {0}" ("Đã chuyển sang {0}").

### Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Đang tải | chuẩn Desk; thanh tóm tắt và bảng xác nhận hiện khung xương, `aria-busy="true"` |
| Rỗng (lần tính không có dịch vụ thành công) | không tạo được: `msgprint` thông báo máy chủ |
| Lỗi máy chủ khi hành động | `msgprint` thông báo máy chủ; form giữ nguyên |
| Không có quyền | Desk báo không có quyền (List lọc, `PermissionError` khi mở form khoa khác) |
| Chỉ đọc (NC Auditor, NC Consultant, NC Admin) | mọi trường chỉ đọc, không có nút hành động, vẫn có "Xuất bảng so sánh giá" |
| Nháp | NC Finance sửa giá đề xuất, căn cứ, ngày áp dụng; vai khác chỉ đọc |
| Chờ khoa xác nhận | form chỉ đọc; thanh nhãn `orange`; trưởng khoa thấy Xác nhận/Từ chối |
| Chờ phê duyệt | chỉ đọc; Giám đốc thấy Phê duyệt/Từ chối; cột GĐ xác nhận hiện |
| Đã duyệt | khóa; `alert-success` "Approved prices recorded on services from {0}" ("Đã ghi giá duyệt vào dịch vụ, áp dụng từ {0}") |
| Đã duyệt nội bộ, chờ trình | khóa; `alert-info` như trên; Finance thấy "Ghi kết quả phê duyệt" |
| Đã được cấp thẩm quyền duyệt | khóa; cột Giá cấp thẩm quyền cạnh Giá đề xuất; section văn bản hiện |

## NC Technical Service — section "Giá đã duyệt" (mở rộng form FEAT-001)

Section mới cuối form, gập mặc định: lưới chỉ đọc `approved_prices` (Loại giá · Giá · Ngày áp dụng · Phương án (link) · Số văn bản), sắp ngày áp dụng giảm dần; không thêm/xóa dòng. Rỗng: "No approved price yet" ("Chưa có giá đã duyệt").

## SCR-DSK-028 Hộp thoại "Xuất hồ sơ" (mở rộng FEAT-019)

Khối Phụ lục thêm dòng "Bảng so sánh giá" + nút "Download", cùng luật bật/tắt (chỉ lần tính "Đã khóa"). Không đổi phần còn lại; không đưa vào hồ sơ nén (ASM-030-14).

## Kiểm

- 1366 × 768: lưới dòng cuộn ngang trong khung; cột Dịch vụ cố định; hộp thoại Phê duyệt và Ghi kết quả cuộn trong thân hộp thoại.
- Bàn phím: Tab tới các nút hành động; trong hộp thoại Tab qua các Check/ô giá, Enter gửi, Esc đóng. Nhãn trạng thái có chữ, không chỉ màu.
- `normcore/tests/unit/test_feat_030_ui.py`: mọi chuỗi trong `nc_price_proposal.js`, `nc_price_proposal_list.js` và phần thêm ở `nc_costing_run.js`, `nc_technical_service.js`, `export_dialog.js` nằm trong `__()`; khóa có trong `vi.d/FEAT-030.csv`; JS gọi đúng `normcore.api.price_proposal.*`; không màu hex tự đặt.
