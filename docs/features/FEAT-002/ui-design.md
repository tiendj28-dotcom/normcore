# FEAT-002 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-001, SCR-DSK-031, SCR-DSK-005 (AMD-004), thành phần "Thẻ tình trạng chuỗi"; `design.md` mục 2–5, 7. API ở `technical-design.md` mục 3.5. Mọi chuỗi qua `__()` (JS) / `_()` (Python), bản tiếng Việt trong `translations/vi.csv`. Chỉ dùng biến CSS của Desk.

## Thành phần dùng chung — Thẻ tình trạng chuỗi (`normcore/public/js/nc_chain_dots.js`)

- Hàm `normcore.chain_dots.render(dots)` trả HTML: bốn chấm nối bằng một đường mảnh (`--border-color`), thứ tự quy trình → định mức → giá thành → giá duyệt. Mỗi chấm: vòng tròn 10 px màu theo `indicator` (pill màu của Desk: `green`, `blue`, `yellow`, `gray`, `red`), có `title` và `aria-label` "<mục>: <trạng thái>" (màu không là kênh duy nhất, design.md 4).
- Mục "Không có quyền xem": chấm rỗng viền xám, nhãn "Không có quyền xem" (ASM-047). Mục giá duyệt R1: chấm xám, `title` "Chưa có giá đã duyệt — Giả định — chờ xác nhận".
- Dùng ở SCR-DSK-005 (cột). SCR-DSK-001 chỉ hiện số đếm, không dùng chấm. SCR-DSK-006 (form dịch vụ) giữ khối chi tiết của FEAT-005, không đổi.
- Nạp qua `app_include_js` trong `hooks.py` (bundle có sẵn của app nếu đã có).

## SCR-DSK-001 Trang chủ Normcore

**Loại:** Workspace `Normcore` (W) có sẵn + Custom HTML Block `NC Trang chủ` đặt đầu trang, chiều ngang 12 cột (ASM-002-10). Dưới block giữ nguyên lối tắt hiện có (Frappe tự ẩn lối tắt người dùng không có quyền đọc → "lối tắt theo vai trò").

**Bố cục block (1366 × 768: hai cột 8 | 4; ≤ 768 px: một cột, "Việc chờ" trước):**

1. Hàng đầu: tiêu đề "Trang chủ Normcore" (h4) và bên phải ô chọn **Khoa** (Link NC Department, nhãn "Lọc theo khoa", có lựa chọn trống "Tất cả khoa trong phạm vi"). Danh sách khoa lấy từ `get_home().departments` (đã giới hạn theo phạm vi). Đổi khoa → gọi lại `get_home(department)`.
2. Cột trái — thẻ **"Việc chờ xử lý (n)"** (`--card-bg`, viền `--border-color`):
   - Bảng gọn, mỗi việc một dòng: cột "Việc" (`task`), "Bản ghi" (`title`, dưới là `name` chữ `--text-muted`), "Trạng thái" (indicator pill theo design.md 3, ví dụ "Chờ trưởng khoa duyệt" `orange`), "Chờ từ" (`since` dạng dd/mm/yyyy; nếu `overdue` thêm pill `red` "Quá hạn").
   - Cả dòng là liên kết tới `route` (thẻ `<a>`, Tab tới được, Enter mở). Sắp xếp: chờ lâu nhất trước (theo API).
   - Lọc khoa áp cả cho việc chờ (lọc phía máy khách theo `department`; việc không có khoa luôn hiện).
   - Quá 10 việc: hiện 10, nút "Xem tất cả (n)" mở rộng tại chỗ.
3. Cột phải — thẻ **"Dịch vụ theo tình trạng chuỗi"**: năm dòng theo `stages` (thứ tự Chưa có quy trình, Có quy trình, Có định mức đã khóa, Đã tính giá, Đã duyệt giá), mỗi dòng: nhãn, số căn phải (định dạng `1.234`).
   - Số là liên kết tới danh sách dịch vụ có bộ lọc tình trạng chuỗi (`/app/nc-technical-service?nc_chain_stage=<stage>[&nc_department=<khoa>]`, SCR-DSK-005 đọc tham số này).
   - `no_permission`: thay số bằng chữ `--text-muted` "Không có quyền xem", không liên kết.
   - `assumption` ("Đã duyệt giá"): số 0 kèm pill `yellow` "Giả định — chờ xác nhận".
   - Dòng chú thích dưới thẻ: "Mỗi dịch vụ tính ở mức cao nhất đã đạt."

**Trạng thái:**

| Trạng thái | Hiển thị |
| :-- | :-- |
| Đang tải | Hai thẻ hiện khung xám nhạt (skeleton của Desk) và chữ "Đang tải…" |
| Trống (không có việc) | Thẻ việc: "Bạn không có việc nào đang chờ xử lý. Các việc cần bạn duyệt sẽ hiện ở đây." + nút "Mở danh sách quy trình" (`/app/nc-clinical-procedure`) nếu đọc được DocType đó |
| Không có dịch vụ | Thẻ tình trạng: "Chưa có dịch vụ kỹ thuật nào." + nút "Mở danh sách dịch vụ" |
| Không đọc được dịch vụ (`stages = []`) | Ẩn thẻ tình trạng chuỗi; cột trái chiếm 12 cột |
| Lỗi API | Dải thông báo `red` trong block: "Không tải được trang chủ. Thử lại." + nút "Thử lại"; lỗi quyền khi lọc khoa: "Khoa này ngoài phạm vi của bạn", đặt lại ô khoa về trống |
| NC Auditor (chỉ đọc) | Việc chờ luôn trống (không có hành động duyệt); thẻ tình trạng theo quyền đọc; không có nút tạo |
| Người bị hẹp theo khoa | Ô khoa chỉ có khoa trong phạm vi; số chỉ tính trong phạm vi; mục không đọc được "Không có quyền xem" |

**API:** `normcore.api.home.get_home` khi mở trang và khi đổi khoa. Không gọi API khác. Làm mới khi Workspace hiện lại (sự kiện `page-change`) và khi nhận realtime `notification` (Frappe phát khi có Notification Log mới) — để việc mới hiện mà không tải lại trang.

**Thông báo (FR-NOTI-001, 002):** chuông thông báo chuẩn của Desk; tiêu đề như FEAT-007 (ví dụ "QT-…: chờ trưởng khoa duyệt"), bấm vào mở bản ghi. Email do Frappe gửi theo mẫu `new_notification`, có nút mở bản ghi. Không có giao diện riêng.

**Kiểm:** 1366 × 768 không cuộn ngang, hai thẻ thấy được trên màn đầu với ≤ 6 việc; 768 px một cột. Bàn phím: Tab qua ô khoa → các dòng việc → các số tình trạng → "Xem tất cả"; viền focus thấy được. Tương phản 4,5:1 (chỉ biến Desk). Số định dạng `1.234`, ngày `dd/mm/yyyy`.

## SCR-DSK-005 Danh sách dịch vụ — cột và bộ lọc tình trạng chuỗi (AMD-004)

**Loại:** List chuẩn của Desk, mở rộng `nc_technical_service_list.js` (giữ bộ lọc khoa, hai nút nhập của FEAT-005).

- **Bộ lọc "Tình trạng chuỗi"**: `listview.page.add_field` Select, các lựa chọn trống + năm nhãn `STAGE_LABELS` (chỉ hiện mức người dùng đọc được — lấy từ `get_home().stages` một lần khi `onload`). Chọn → `services_in_stage(stage, department)` (department lấy từ bộ lọc "Khoa thực hiện" nếu có) → đặt bộ lọc `name in [...]`; danh sách rỗng → bộ lọc `name = "__none__"` để hiện trạng thái trống chuẩn. Bỏ chọn → xóa bộ lọc `name`. Quá 2.000 mã: không lọc, `frappe.show_alert` "Quá nhiều dịch vụ, hãy lọc theo khoa trước" (`orange`).
- Đọc tham số `nc_chain_stage`, `nc_department` trên URL khi `onload` (liên kết từ trang chủ) để đặt sẵn hai bộ lọc.
- **Cột "Tình trạng chuỗi"**: sau mỗi lần `refresh`, gọi `get_service_stages(<mã đang hiện>)` (một lần cho cả trang, ≤ 500 mã theo trang) rồi chèn thẻ bốn chấm vào ô cuối mỗi dòng (phần tử `.nc-chain-dots`, không làm vỡ cột chuẩn; trên màn ≤ 1366 px hiện ở cuối dòng, trước chỉ báo "Đang hoạt động"). Đang tải: không hiện chấm; lỗi: bỏ qua cột, không chặn danh sách.
- Không quyền đọc một mục: chấm "Không có quyền xem" như thành phần chung.
- Kiểm: 1366 × 768 cột mã, tên, chuyên khoa vẫn đủ; chấm có `aria-label`.

## SCR-DSK-031 Tham số vận hành — form NC Settings (Single, form chuẩn)

**Loại:** Form chuẩn của Desk ("Cài đặt Normcore"), lối tắt "Tham số vận hành" ở Workspace đã có.

**Bố cục (thứ tự section):**

1. **Tham số vận hành** (mới, hai cột): trái — Số ca bấm giờ tối thiểu, Hạn tham chiếu đơn giá (tháng); phải — Cửa sổ giá tham chiếu (tháng), Số đơn vị tham chiếu tối thiểu, Chế độ kế toán.
2. Phê duyệt quy trình (có sẵn, giữ nguyên vị trí): Số ngày nhắc duyệt, Thư ký hội đồng.
3. Hồ sơ tuân thủ (có sẵn): Số ngày nhắc hạn hồ sơ tuân thủ.

- Mỗi trường mới có mô tả ngắn dưới ô (description, technical-design 2.1). Dòng mô tả section "Tham số vận hành": "Giá trị mới áp dụng cho thao tác kế tiếp, không cần khởi động lại."
- `nc_settings.js`: khi lưu thành công, `frappe.show_alert` `green` "Đã lưu. Giá trị mới áp dụng cho thao tác kế tiếp."
- Lỗi kiểm (≤ 0): thông báo tiếng Việt của controller, mỗi lỗi một dòng.
- NC Auditor: form chỉ đọc (quyền R), không nút Lưu. Vai trò khác: không thấy lối tắt (Workspace ẩn), mở URL → trang "Không có quyền" chuẩn.
- Thời hạn gọi AI không ở form này (ASM-002-09): thêm dòng mô tả cuối section "Tham số vận hành": "Thời hạn gọi AI đặt ở Cấu hình AI." kèm liên kết `/app/nc-ai-settings` (chỉ hiện nếu đọc được NC AI Settings).
- Khoa, trung tâm chi phí, phạm vi khoa, trang nhập Excel của SCR-DSK-031: đã có ở FEAT-001, FEAT-004; không đổi.

## Tiếp cận, bàn phím, chuỗi (NFR-USE-004, NFR-USE-001)

- Không dùng màu làm kênh duy nhất: pill có chữ, chấm có `aria-label`.
- Mọi phần tử tương tác trong block là `<a>`/`<button>`/ô Desk, Tab tới được; focus thấy rõ.
- Chuỗi mới (nhãn mức, việc, thông báo trống, lỗi, mô tả trường) có trong `vi.csv`; test quy ước giao diện hiện có phải xanh.
