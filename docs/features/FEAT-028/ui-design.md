# FEAT-028 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-026 ("Danh sách dịch vụ với thấp nhất, trung vị, cao nhất, độ lệch; chi tiết cơ cấu giá và gợi ý"; trạng thái "Chưa đủ dữ liệu so sánh", "gợi ý cần sửa quy trình"), thành phần "Thanh so sánh giá", "Thanh cơ cấu giá", luồng 3; `design.md` (nhãn trạng thái `indicator-pill`, `alert-*`); `technical-design.md` (TD) mục 3.3, 3.5. Mẫu kỹ thuật: trang `sensitivity` (FEAT-037). Chuỗi JS viết tiếng Anh trong `__()`, bản dịch ở `normcore/translations/vi.d/FEAT-028.csv`; thông báo máy chủ tiếng Việt. Số, tiền, ngày theo NFR-LOC-001 (`format_currency`, `frappe.datetime.str_to_user`). Chạy được ở 1366 × 768; thao tác được bằng bàn phím; chỉ dùng biến CSS của Desk, không tự đặt màu chữ (tương phản NFR-USE-004).

"Kịch bản đang mở" của SCR-DSK-026 thuộc FEAT-029: FEAT-028 không vẽ.

## SCR-DSK-026 Bàn so sánh giá — Desk Page Vue `price-compare`

Loại: Desk Page `price-compare` (tiêu đề "Price comparison" / "Bàn so sánh giá"), Vue 3 `PriceCompare.vue`. Tham số URL `?run=<NC Costing Run>`; thiếu `run`: ô chọn lần tính (Link NC Costing Run, lọc `status in (Đã tính, Đã khóa)`).

### Lối vào
- Form NC Costing Run: nút "Price comparison" ("So sánh giá") trong nhóm "View", chỉ khi `status ∈ {Đã tính, Đã khóa}` → `frappe.set_route("price-compare", {run})`.

### Bố cục (hai cột: danh sách 60%, chi tiết 40%; dưới 1366 px chi tiết xếp dưới danh sách)

**Đầu trang**: tiêu đề lần tính · nhãn trạng thái (`indicator-pill` blue "Đã tính" / gray "Đã khóa") · ngày tính giá · loại giá · bộ tham số · dòng nhỏ "Window {0} months · at least {1} facilities · tolerance {2}%" ("Cửa sổ {0} tháng · tối thiểu {1} đơn vị · ngưỡng lệch {2}%").

**Thanh lọc** (FR-ADJ-004): ba MultiSelect "Province/City" ("Tỉnh/thành phố"), "Level" ("Hạng"), "Ownership" ("Loại hình") lấy từ `filter_options`; công tắc "Use CPI-adjusted prices" ("Dùng giá hiệu chỉnh", mặc định tắt, ASM-028-02); ô tìm dịch vụ (lọc phía khách); bộ lọc nhanh "Only over tolerance" ("Chỉ dịch vụ vượt ngưỡng"). Đổi bộ lọc → gọi lại `get_comparison` (debounce 300 ms), giữ dịch vụ đang chọn.

**Bảng dịch vụ** (`get_comparison.rows`), cột: Mã · Tên dịch vụ · Khoa · Giá tính toán · Số đơn vị · Thấp nhất · Trung vị · Cao nhất · Độ lệch % · Thanh so sánh giá · Gợi ý (số "Mới"). Sắp mặc định theo `abs(deviation_pct)` giảm dần; bấm tiêu đề cột để sắp.
- Độ lệch: `+7,90%` / `−4,18%`; vượt ngưỡng → nhãn `orange` "Over tolerance" ("Vượt ngưỡng").
- `sufficient = false`: các ô thống kê "—", nhãn `gray` "Not enough comparison data" ("Chưa đủ dữ liệu so sánh") ở cột độ lệch, không có thanh (FR-ADJ-003).
- **Thanh so sánh giá**: thang ngang từ min đến max (nền `--gray-200`), vạch trung vị, chấm giá bệnh viện (`--primary`); giá ngoài [min, max] thì chấm ở mép có mũi tên. `aria-label` "Min {0}, median {1}, max {2}, hospital {3}".
- Dòng chọn được bằng chuột hoặc ↑/↓ + Enter; dòng chọn có nền `--control-bg`.

**Khung chi tiết** (`get_service_detail(service_cost, filters…)`), ba khối:
1. *Giá tham chiếu*: bảng Đơn vị · Tỉnh · Hạng · Loại hình · Ngày hiệu lực · Giá · Giá hiệu chỉnh (hoặc "Thiếu chỉ số giá") · Nguồn (số văn bản / liên kết). Liên kết gập "Excluded prices ({0})" ("Giá bị loại ({0})") liệt kê `excluded` kèm lý do (TC-ADJ-01).
2. *Cơ cấu giá thành* (FR-ADJ-010): **Thanh cơ cấu giá** xếp chồng theo cấu phần (màu theo bảng màu biểu đồ của Desk, có chú giải) + bảng Nhóm · Cấu phần · Giá trị · Tỷ trọng; dòng tổng "Full cost" ("Giá thành toàn bộ") = `full_cost`, 100%. Dưới bảng: Tích lũy, Nghĩa vụ, Giá tính toán, Giá làm tròn (chỉ đọc).
3. *Gợi ý điều chỉnh* (FR-ADJ-005, 008):
   - Chưa đủ dữ liệu: `alert-info` "Not enough comparison data: no comparison-based suggestions" ("Chưa đủ dữ liệu so sánh: không có gợi ý dựa trên so sánh").
   - Trong ngưỡng: `alert-success` "Within tolerance, no adjustment needed" ("Trong ngưỡng lệch, không cần điều chỉnh").
   - Vượt ngưỡng, `can_generate`: nút "Generate suggestions" ("Sinh gợi ý") / "Regenerate" ("Sinh lại") → `generate_suggestions`; nút khóa, `aria-busy` khi chạy.
   - Vượt ngưỡng, không `can_generate` và chưa có gợi ý: dòng nhỏ "No suggestions generated yet" ("Chưa sinh gợi ý").
   - Danh sách thẻ, theo thứ tự máy chủ trả (tác động giảm dần). Mỗi thẻ: mã quy tắc · nhãn hướng (`green` "Giảm" / `orange` "Tăng") · câu gợi ý (`text`) · Đối tượng · "Current" ("Hiện tại") → "Suggested" ("Đề xuất") · Tác động "−15.411,93 ₫" hoặc "Chưa ước tính được" · nhãn `red` "Requires procedure change" ("Cần sửa quy trình") khi `requires_procedure_change` · nhãn trạng thái (`blue` Mới, `green` Chấp nhận, `gray` Từ chối kèm lý do, người, thời điểm).
   - Dưới danh sách: chú thích nhỏ "Estimated impact, level-2 allocation not recomputed" ("Ước tính, chưa tính lại phân bổ cấp 2", ASM-028-06).
   - Thẻ "Mới" và `can_decide`: nút "Accept" ("Chấp nhận", ẩn khi cần sửa quy trình, thay bằng chữ "Handled in procedure change request (coming)" / "Xử lý bằng yêu cầu sửa quy trình") và "Reject" ("Từ chối") → hộp thoại `frappe.prompt` một trường Small Text bắt buộc "Reason" ("Lý do"); để trống không gửi được (FR-ADJ-008). Gọi `decide_suggestion`, cập nhật thẻ và số "Mới" ở bảng.

### Trạng thái
| Trạng thái | Hiển thị |
| :-- | :-- |
| Đang tải | khung xương (`skeleton`) ở bảng và chi tiết, `aria-busy="true"` |
| Rỗng (không có dịch vụ thành công) | `alert-info` "This costing run has no service results" ("Lần tính chưa có kết quả dịch vụ") |
| Lần tính chưa tính / lỗi | thông báo máy chủ trong `alert-warning`, ô chọn lần tính khác |
| Không có quyền | Page không có trong vai → Desk báo không có quyền; API PermissionError → `alert-danger` với thông báo máy chủ |
| Chỉ đọc và quyền quyết định | NC Auditor, NC Admin: không có nút Sinh gợi ý / Chấp nhận / Từ chối (`can_generate = can_decide = false`). NC Director, Trưởng khoa (khoa mình): có Chấp nhận/Từ chối, không có Sinh gợi ý |
| Trưởng khoa | bảng chỉ có dịch vụ thuộc khoa mình (máy chủ lọc) |
| Lỗi mạng/máy chủ khi quyết định | `frappe.msgprint`, thẻ giữ nguyên trạng thái |

### Bàn phím và truy cập
Tab qua thanh lọc → bảng → chi tiết; ↑/↓ chọn dịch vụ, Enter mở chi tiết; trong thẻ gợi ý Tab tới Chấp nhận/Từ chối; Esc đóng hộp thoại lý do. Bảng dùng `<table>` có `<th scope="col">`; vùng chi tiết `role="region"` `aria-live="polite"`.

## NC Adjustment Suggestion — Form/List chuẩn của Desk

- List: cột Kết quả dịch vụ, Quy tắc, Hướng, Tác động ước tính, Trạng thái (indicator: Mới blue, Chấp nhận green, Từ chối gray, Đã chuyển yêu cầu sửa quy trình purple; `nc_adjustment_suggestion_list.js`). Bộ lọc chuẩn: Kết quả dịch vụ, Quy tắc, Trạng thái. Không có nút "Thêm" cho vai khác NC Finance (DocPerm); NC Finance cũng nên tạo qua Bàn so sánh (form chỉ đọc).
- Form: mọi trường chỉ đọc (TD 2.1); section "Gợi ý" (service_cost, rule_code, direction, component, target_ref, current_value, suggested_value, estimated_impact, requires_procedure_change), section "Quyết định" (status, decision_reason, decided_by, decided_on). Nút "Open in price comparison" ("Mở ở Bàn so sánh giá") → `price-compare?run=<run của service_cost>`.

## Kiểm
- 1366 × 768: bảng cuộn ngang trong khung, cột Mã và Tên cố định; chi tiết cuộn riêng.
- `test_feat_028_ui.py`: Page JSON có đúng vai trò; mọi chuỗi giao diện trong `__()`; khóa có trong `vi.d/FEAT-028.csv`; không màu hex tự đặt trong `.vue`.
