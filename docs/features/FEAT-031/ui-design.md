# FEAT-031 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-006 (khối "Cận lâm sàng" [1.1]), SCR-DSK-032; luồng 4 (`w1` SCR-DSK-006 → `w2` SCR-DSK-032); `design.md`; `technical-design.md` mục 2–5. Form và danh sách chuẩn của Desk, không trang Vue. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.csv` (giữ thứ tự chữ cái, không trùng khóa); nhãn DocType, tùy chọn Select và thông báo máy chủ tiếng Việt. Chỉ dùng biến CSS của Desk và lớp `indicator-pill`, `frm.dashboard`; không mã màu cứng. Mọi quyền do máy chủ quyết; ẩn hiện nút chỉ là tiện ích.

## SCR-DSK-006 Dịch vụ kỹ thuật — khối "Cận lâm sàng"

Hiện thực: Form chuẩn NC Technical Service đã có (FEAT-005), sửa `nc_technical_service.js`; giữ nguyên thẻ "Tình trạng chuỗi".

**Bố cục** (sau mục "Khoa thực hiện"):
1. Section "Cận lâm sàng" (`cls_section`, thu gọn được, mở sẵn khi `is_paraclinical` = 1). Cột trái: `is_paraclinical`, `cls_group`, `result_unit`. Cột phải: `is_send_out`, `send_out_price`. `cls_group`, `result_unit`, `is_panel`, `is_send_out` chỉ hiện khi `is_paraclinical`; dấu bắt buộc hiện ngay khi bật cờ (`mandatory_depends_on`).
2. Bảng "Mã trên hệ thống ngoài" (`external_codes`): cột Hệ thống nguồn, Mã ngoài, Tên trên hệ thống ngoài. Luôn hiện (FR-SVC-009 không giới hạn cận lâm sàng).
3. Dịch vụ bộ: `is_panel`; khi bật hiện `panel_costing_mode` (mô tả dưới trường: "Giả định — chờ xác nhận (TBD-17)") và bảng "Thông số thành phần" (Mã thông số, Tên thông số, Dịch vụ tương ứng).
4. "Hệ thống xét nghiệm" (`cls_systems_html`, chỉ khi `is_paraclinical` và bản ghi đã lưu): gọi `normcore.api.test_system.get_service_systems(service)`. Nhóm theo khoa; mỗi khoa một tiêu đề "Khoa <tên> — tổng tỷ trọng <x>%" và bảng: Mã (liên kết tới SCR-DSK-032), Thiết bị chính, Tỷ trọng (%), Trạng thái (pill `green` Đang dùng / `gray` Ngừng dùng). Tổng ≠ 100% (chỉ tính hệ thống đang dùng): pill `orange` "Tổng tỷ trọng khác 100%". Nút "Thêm hệ thống xét nghiệm" khi `can_create`: mở form NC Test System mới với `technical_service` điền sẵn (`frappe.new_doc`).
5. Tab "Kết nối" chuẩn (`links`): nhóm "Cận lâm sàng" đếm NC Test System.

| Trạng thái | Hiển thị |
| :-- | :-- |
| Bản ghi mới | Khối hệ thống ẩn; hiện "Lưu để thêm hệ thống xét nghiệm" |
| Không cận lâm sàng | Chỉ hiện cờ và bảng mã ngoài |
| Cận lâm sàng, chưa có hệ thống | "Chưa có hệ thống xét nghiệm" + nút thêm (nếu có quyền) |
| Đang tải / lỗi | "Đang tải hệ thống xét nghiệm…"; lỗi: "Không tải được hệ thống xét nghiệm." + nút "Thử lại" (cùng mẫu thẻ tình trạng chuỗi) |
| Người xem bị hẹp theo khoa | Chỉ thấy hệ thống khoa mình; tổng tỷ trọng vẫn là tổng thật của khoa đó |
| Chỉ đọc (Auditor, Clinician, Dept Head, Finance, …) | Form chỉ đọc chuẩn Desk; danh sách hệ thống vẫn hiện; nút thêm chỉ khi `can_create` (Clinician, Dept Head) |
| Lỗi lưu | Thông báo máy chủ tiếng Việt: thiếu nhóm/đơn vị (TC-CLS-20), mã ngoài đã gắn dịch vụ khác (TC-CLS-21), bộ rỗng, gửi ngoài thiếu giá, bỏ cờ khi còn hệ thống |

## SCR-DSK-032 Hệ thống xét nghiệm (L + F)

Hiện thực: List + Form chuẩn NC Test System; tệp `nc_test_system.js`, `nc_test_system_list.js`. Lối tắt trong Workspace "Normcore" (nhóm cận lâm sàng, cạnh "Thiết bị").

**Danh sách**: cột Mã (ID), Dịch vụ, Khoa, Thiết bị chính, Tỷ trọng (%), Trạng thái (`get_indicator`: Đang dùng `green`, Ngừng dùng `gray`). Bộ lọc chuẩn: dịch vụ, khoa, thiết bị chính, trạng thái. Clinician, Dept Head chỉ thấy khoa được gán (`permission_query_conditions`). Nút "Nhập từ Excel" trên danh sách (khi có quyền tạo) mở trang `import-excel` với bộ `nc_test_system` chọn sẵn (`frappe.set_route("import-excel", {import_set: "nc_test_system"})`; nếu trang chưa đọc tham số thì chỉ mở trang — Dev kiểm và ghi vào log).

**Form** (bố cục):
1. Nhận diện: cột trái `test_system_code`, `technical_service`, `department`; cột phải `main_equipment`, `status`.
2. Sản lượng và ước tính: `volume_share_pct`, `est_rerun_rate`, `est_wastage_rate`; cột phải `machine_minutes_per_case`. Khi chọn/đổi `main_equipment` (và lúc mở form), JS đọc `allocation_basis` của thiết bị (`frappe.db.get_value`); "Phút chiếm máy" thì đặt `reqd` cho phút chiếm máy và mô tả "Thiết bị chia theo phút chiếm máy"; khác thì bỏ `reqd`. Máy chủ vẫn kiểm.
3. Tình trạng (`status_html`, chỉ khi đã lưu): gọi `normcore.api.test_system.get_status(test_system)`. Bốn thẻ ngang (cùng mẫu CSS thẻ tình trạng chuỗi của SCR-DSK-006, xuống cột dưới 768 px): "Bộ định mức hiện hành", "Kế hoạch chất lượng", "Sản lượng kịch bản mặc định", "Hệ số k và giá thành lần tính gần nhất"; ở FEAT này mỗi thẻ hiện pill `gray` "Chưa có" (ASM-115).

**Cảnh báo đầu form** (`frm.dashboard.set_headline_alert`, từ `warnings` của `get_status`):
- `inactive`: màu `gray` — "Hệ thống đã ngừng dùng: không vào các lần tính giá mới".
- `share_total`: màu `orange` — "Tổng tỷ trọng của dịch vụ … tại khoa … là x%, khác 100%" (ASM-112).
- "Thiếu kế hoạch nội kiểm" của ux-foundations thuộc FEAT-032; FEAT-031 không hiện.

**Hành động**: nút "Ngừng dùng" (khi `Đang dùng`) / "Dùng lại" (khi `Ngừng dùng`), chỉ khi `frm.perm[0].write` và form không có thay đổi chưa lưu (có thì báo "Lưu thay đổi trước"). "Ngừng dùng" hỏi xác nhận "Ngừng dùng hệ thống <mã>? Hệ thống sẽ không vào các lần tính giá mới; các lần tính đã có giữ nguyên." rồi `frm.set_value("status", …)` và `frm.save()`. Không có nút xóa (không vai trò nào có quyền).

| Trạng thái | Hiển thị |
| :-- | :-- |
| Danh sách rỗng | Trạng thái trống chuẩn Desk; người bị hẹp theo khoa chưa gán khoa thấy rỗng |
| Bản ghi mới | Khối tình trạng ẩn; "Lưu để xem tình trạng" |
| Đang tải / lỗi khối tình trạng | "Đang tải tình trạng…"; lỗi: "Không tải được tình trạng." + "Thử lại" |
| Không có quyền (Doc Controller, Council; Clinician khoa khác mở theo URL) | Trang không đủ quyền chuẩn Desk |
| Chỉ đọc (Auditor, Finance, Resource Manager, Director, Consultant, Admin) | Form chỉ đọc, không nút lưu, không nút Ngừng dùng / Dùng lại; khối tình trạng và cảnh báo vẫn hiện |
| Ngừng dùng | Pill trạng thái `gray`, cảnh báo `inactive`; vẫn sửa được (DI-07) |
| Lỗi lưu | Thông báo máy chủ: dịch vụ chưa đánh dấu cận lâm sàng, tỷ trọng ngoài (0, 100], tỷ lệ ngoài miền, thiếu phút chiếm máy, không có quyền với khoa (TC-CLS-22) |

## Nhập Excel hệ thống xét nghiệm

Dùng trang `import-excel` của FEAT-004 không đổi; bộ "Hệ thống xét nghiệm" hiện với người có quyền tạo (Clinician, Dept Head). Báo cáo lỗi theo dòng/cột của khung (ví dụ dòng thiết bị lạ: `"EQ_X" không tồn tại trong NC Equipment`, TC-CLS-23).

## Kiểm chung
- 1366 × 768: bảng mã ngoài, thông số, danh sách hệ thống cuộn trong form; bốn thẻ tình trạng một hàng ở 1366 px, xếp dọc dưới 768 px.
- Bàn phím: chuẩn Desk (Ctrl+S lưu, Tab theo thứ tự trường); nút Ngừng dùng / Dùng lại, Thêm hệ thống, Thử lại là `button` lấy được focus; liên kết hệ thống là thẻ `a`.
- Tương phản (NFR-USE-004): chỉ lớp Desk (`indicator-pill`, `text-muted`), không màu tự đặt.
- Chuỗi: mọi chuỗi JS qua `__()`, có dòng trong `vi.csv`; test quy ước tĩnh `tests/unit/test_test_system_ui_conventions.py` (theo mẫu `test_equipment_ui_conventions.py`): không mã màu hex, mọi chuỗi `__()` có bản dịch, gọi đúng tên API.

API dùng: `normcore.api.test_system.get_service_systems`, `normcore.api.test_system.get_status`; trang `import-excel` (FEAT-004).
