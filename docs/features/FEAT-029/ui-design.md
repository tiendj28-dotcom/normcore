# FEAT-029 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-026 (trạng thái "gợi ý cần sửa quy trình; kịch bản đang mở"), luồng 3; `design.md` (`indicator-pill`, `alert-*`); `technical-design.md` (TD) mục 3.3; `ui-design.md` của FEAT-028 (bố cục trang `price-compare` đã có, chỉ mở rộng). Chuỗi JS viết tiếng Anh trong `__()`, bản dịch ở `normcore/translations/vi.d/FEAT-029.csv`; thông báo máy chủ tiếng Việt. Số, tiền, ngày theo NFR-LOC-001. Chạy được ở 1366 × 768; thao tác được bằng bàn phím; chỉ dùng biến CSS của Desk (tương phản NFR-USE-004).

## SCR-DSK-026 Bàn so sánh giá — mở rộng `PriceCompare.vue`

Loại: Desk Page Vue `price-compare` (FEAT-028). Không đổi vai trò của Page. Khi tải trang gọi thêm `scenario.get_open_scenario(run)` song song với `get_comparison`.

### Dải "Kịch bản đang mở" (dưới đầu trang, trên thanh lọc)
- Có kịch bản: `alert-info` `role="status"`: "Open scenario {0} · {1} changes · calculated {2}" ("Kịch bản đang mở {0} · {1} thay đổi · tính lúc {2}") + nút "Show scenario" ("Xem kịch bản", bật/tắt khung kịch bản) + nút "New scenario" ("Kịch bản mới", chỉ khi `can_create`; hỏi xác nhận "Start a new empty scenario? The current one is kept." / "Bắt đầu kịch bản mới rỗng? Kịch bản hiện tại vẫn giữ.") → `create_scenario`, tải lại.
- `warnings` của kịch bản: từng dòng `alert-warning` nhỏ ngay dưới dải.
- Không có kịch bản: không hiện dải; NC Finance thấy liên kết nhỏ "Create scenario" ("Tạo kịch bản").
- Đang xem chính một kịch bản (`?run=<kịch bản>`): dải `alert-warning` "This is an adjustment scenario of {0}; suggestions are handled on the original run" ("Đây là kịch bản điều chỉnh của {0}; xử lý gợi ý ở lần tính gốc") + liên kết mở lần gốc. Khung gợi ý chỉ đọc.

### Bảng dịch vụ
Khi có kịch bản đang mở: thêm cột "Scenario price" ("Giá kịch bản") sau "Giá tính toán", hiện `scenario_price` của dòng khớp `(technical_service, department)`; khác giá gốc thì kèm chênh `−12.345,67` (chữ `text-muted`, không tô màu riêng). Dịch vụ người gọi không đọc được ở kịch bản: "—". Cột "Gợi ý" đếm thêm "Đã chuyển yêu cầu sửa quy trình".

### Khung kịch bản (bật bằng "Xem kịch bản"; trên 1366 px nằm ở cột chi tiết, thay khung chi tiết dịch vụ cho đến khi tắt)
1. Bảng thay đổi (`changes`): Loại · Dịch vụ (hoặc "Cả lần tính") · Đối tượng · Trường (nhãn: "Hệ số sử dụng", "Số phút", "Hao hụt %", "Tỷ lệ tích lũy %") · Cũ → Mới · Gợi ý nguồn (liên kết form NC Adjustment Suggestion). Rỗng: "No changes yet" ("Chưa có thay đổi").
2. Bảng giá (`rows`): Dịch vụ · Khoa · Giá gốc · Giá kịch bản · Chênh · Chênh %; chỉ dòng có chênh khác 0 (công tắc "Show all services" / "Hiện mọi dịch vụ").
3. NC Finance, Director, Admin, Auditor: liên kết "Compare runs" ("So sánh hai lần tính") → màn so sánh lần tính FEAT-018 (`compare_runs` base = gốc, other = kịch bản). Trưởng khoa không có liên kết (không đọc NC Costing Run).

### Thẻ gợi ý (khối 3 của khung chi tiết, FEAT-028) — thay đổi
- Gợi ý **không cần sửa quy trình**, trạng thái "Mới", `can_decide`: nút "Accept" ("Chấp nhận") gọi `scenario.accept_suggestion(name)` (không còn gọi `decide_suggestion`). Trong khi chạy: nút khóa, `aria-busy`, chữ "Recalculating scenario…" ("Đang tính lại kịch bản…"). Xong:
  - `outcome = scenario`: `frappe.show_alert` xanh "Added to scenario {0}; new price {1}" ("Đã ghi vào kịch bản {0}; giá mới {1}"); nếu có `norm_set`: `frappe.msgprint` "Draft norm set {0} created with the new value, waiting for re-confirmation" ("Đã tạo bộ định mức nháp {0} với giá trị mới, chờ xác nhận lại") + nút mở `norm-grid/{0}` (bộ đã có: "Applied to draft norm set {0}" / "Đã áp vào bộ định mức nháp {0}").
  - `outcome = decision_only`: `show_alert` vàng với cảnh báo máy chủ.
  - Tải lại dải kịch bản, cột "Giá kịch bản", thẻ gợi ý.
- Gợi ý **cần sửa quy trình** ("Mới", `can_decide`): thay chữ "Xử lý bằng yêu cầu sửa quy trình" của FEAT-028 bằng nút "Send procedure change request" ("Chuyển yêu cầu sửa quy trình") → hộp thoại: đoạn chỉ đọc "The change will not be applied to the scenario or norm set; a request is sent to department {0}" ("Thay đổi không áp vào kịch bản hay bộ định mức; yêu cầu được gửi khoa {0}"), câu gợi ý, ô Small Text không bắt buộc "Note" ("Ghi chú") → `accept_suggestion(name, note)`. Xong: `show_alert` "Request {0} sent to {1}" ("Đã gửi yêu cầu {0} cho {1}"); cảnh báo thiếu trưởng khoa hiện `alert-warning`.
- Nhãn trạng thái thêm: `purple` "Sent as procedure change request" ("Đã chuyển yêu cầu sửa quy trình") + liên kết tới NC Procedure Change Request và trạng thái của yêu cầu.
- Gợi ý "Chấp nhận" đã vào kịch bản: thêm dòng nhỏ "In scenario {0}" ("Trong kịch bản {0}").
- Nút "Reject" ("Từ chối") giữ như FEAT-028.

### Nút "Đề xuất sửa quy trình" (khung chi tiết, dưới khối gợi ý; khi `can_request_change` và không phải kịch bản)
"Propose procedure change" ("Đề xuất sửa quy trình") → `frappe.prompt` hai trường bắt buộc: Text "Proposed change (add, remove or change steps/resources)" ("Thay đổi đề xuất (thêm, bỏ, đổi bước hoặc nguồn lực)"), Small Text "Reason" ("Lý do") → `request_procedure_change`. Lý do trống: không gửi được.

### Trạng thái
| Trạng thái | Hiển thị |
| :-- | :-- |
| Đang tải kịch bản | khung xương trong dải, `aria-busy="true"` |
| Lỗi khi chấp nhận (bộ chờ khóa, thiếu dữ liệu thiết bị, …) | `frappe.msgprint` đỏ với thông báo máy chủ; thẻ giữ "Mới" (máy chủ đã rollback) |
| Chỉ đọc (NC Auditor, NC Admin, NC Consultant không vào trang) | thấy dải và khung kịch bản; không có nút Chấp nhận, Chuyển yêu cầu, Đề xuất, Kịch bản mới |
| Trưởng khoa | dải, khung kịch bản chỉ dịch vụ khoa mình; có Chấp nhận, Chuyển yêu cầu, Đề xuất cho dịch vụ khoa mình; không có Kịch bản mới |
| NC Director | như Trưởng khoa nhưng mọi khoa; không có Kịch bản mới |

### Bàn phím và truy cập
Dải: Tab tới "Xem kịch bản", "Kịch bản mới"; khung kịch bản `role="region"` `aria-label` "Scenario"; bảng có `<th scope="col">`; hộp thoại đóng bằng Esc, Enter gửi khi đủ trường.

## NC Costing Run — Form/List chuẩn (kịch bản)

- Form (`nc_costing_run.js`): khi `based_on_run`: dải `set_intro` vàng "Adjustment scenario of {0}. Changes are made on the price comparison page." ("Kịch bản điều chỉnh của {0}. Thay đổi làm ở Bàn so sánh giá.") có liên kết lần gốc; ẩn nút Tính giá, Khóa, Nhân bản; nút "Open in price comparison" ("Mở ở Bàn so sánh giá") → `price-compare?run=<based_on_run>`. Section "Kịch bản điều chỉnh" hiện `based_on_run` và bảng `scenario_changes` chỉ đọc.
- Lần gốc có kịch bản: nút "Scenarios ({0})" ("Kịch bản ({0})") trong nhóm "View" → list NC Costing Run lọc `based_on_run`.
- List (`nc_costing_run_list.js`): thêm bộ lọc chuẩn `based_on_run`; dòng kịch bản có nhãn phụ `purple` "Scenario" ("Kịch bản") cạnh trạng thái.

## NC Procedure Change Request — Form/List chuẩn

- List (`nc_procedure_change_request_list.js`): cột Quy trình, Người yêu cầu, Trạng thái, ngày tạo; indicator Mới `blue`, Đã tiếp nhận `orange`, Từ chối `gray`, Đã thực hiện `green`; bộ lọc chuẩn Quy trình, Trạng thái. Không có nút "Thêm" cho vai khác NC Finance; Finance cũng tạo qua Bàn so sánh (form chỉ đọc).
- Form: mọi trường chỉ đọc; section "Yêu cầu" (procedure, requested_by, source_suggestion, status), section "Nội dung" (proposed_change, hiển thị nhiều dòng). Nút theo `scenario.change_request_actions(name)`:
  - "Accept and open revision" ("Tiếp nhận và mở bản sửa đổi") → `act_on_change_request(name, "Tiếp nhận")` → mở `procedure-editor/<revision>`.
  - "Reject" ("Từ chối") → `frappe.prompt` "Reason" ("Lý do") bắt buộc.
  - "Mark as done" ("Đánh dấu đã thực hiện").
  - Liên kết "Open procedure" ("Mở quy trình") và "Open suggestion" ("Mở gợi ý") khi có.
- NC Auditor, Finance, Director, Consultant, Admin: không có nút hành động (danh sách hành động rỗng).

## NC Clinical Procedure — form Desk (dải nhắc, UC-007 1c)

`nc_clinical_procedure.js`: khi có NC Procedure Change Request trạng thái Mới hoặc Đã tiếp nhận cho cùng (dịch vụ, khoa) mà người dùng đọc được (`frappe.db.get_list`), `dashboard.set_headline_alert` vàng "There are {0} change requests from price comparison" ("Có {0} yêu cầu sửa đổi từ Bàn so sánh giá") với liên kết list đã lọc. Bản nháp tạo từ yêu cầu hiện nội dung đề xuất trong timeline (Comment "Info", TD 2.3).

## Kiểm
- 1366 × 768: khung kịch bản cuộn riêng; cột "Giá kịch bản" không làm bảng tràn (bảng đã cuộn ngang, cột Mã/Tên cố định).
- `test_feat_029_ui.py`: mọi chuỗi mới trong `__()`, khóa có trong `vi.d/FEAT-029.csv`; `PriceCompare.vue` gọi `normcore.api.scenario.accept_suggestion`, `get_open_scenario`, `create_scenario`, `request_procedure_change`; không còn chuỗi "(coming)"; `nc_procedure_change_request.js` gọi `act_on_change_request`; không màu hex tự đặt trong `.vue`.
