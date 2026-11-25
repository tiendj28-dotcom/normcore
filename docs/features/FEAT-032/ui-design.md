# FEAT-032 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-033 (F), SCR-DSK-034 (L + F), nhóm "E. Cận lâm sàng", luồng 4 (`w2` SCR-DSK-032 → `w3` SCR-DSK-033); `design.md`; `technical-design.md` mục 2–5. Form và danh sách chuẩn của Desk, không trang Vue. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.csv` (thứ tự chữ cái, không trùng khóa); nhãn DocType, mô tả trường, thông báo máy chủ tiếng Việt. Chỉ dùng biến CSS của Desk và lớp `indicator-pill`, `frm.dashboard`, `text-muted`; không mã màu cứng. Quyền do máy chủ quyết; ẩn hiện nút chỉ là tiện ích.

## SCR-DSK-032 Hệ thống xét nghiệm — phần thêm của FEAT-032

Sửa `nc_test_system.js` (FEAT-031), không đổi bố cục cũ:
- Thẻ "Kế hoạch chất lượng" của khối tình trạng hiện theo `items[qc_plan]` của `get_status`: `empty` → pill `gray` "Chưa có"; `ok` → pill `green` + message ("Có — 1 dòng nội kiểm, 1 dòng chuẩn máy") và liên kết tới kế hoạch; `warning` → pill `orange` "Thiếu nội kiểm". Thẻ là thẻ `a` khi có kế hoạch.
- Nút "Kế hoạch chất lượng" (nhóm nút "Cận lâm sàng", chỉ khi bản ghi đã lưu): đã có kế hoạch (`frappe.db.get_value("NC QC Plan", {test_system}, "name")`) → mở form; chưa có và `frappe.model.can_create("NC QC Plan")` → `frappe.new_doc("NC QC Plan", {test_system: frm.doc.name})`; chưa có và không có quyền tạo → không hiện nút.
- Cảnh báo thiếu nội kiểm (FR-QC-007) chỉ ở thẻ trên; đầu form không thêm cảnh báo mới (ASM-032-08). Cảnh báo trên bộ định mức làm ở FEAT-034 bằng `normcore.api.qc_plan.missing_iqc_warning`.

## SCR-DSK-033 Kế hoạch chất lượng (F)

Hiện thực: Form chuẩn NC QC Plan; tệp `nc_qc_plan.js`. Danh sách chuẩn Desk vẫn có (cột Hệ thống xét nghiệm, Số ngày chạy mỗi năm; lọc theo hệ thống) nhưng lối vào chính là nút trên SCR-DSK-032 (luồng 4); thêm một lối tắt Workspace "Kế hoạch chất lượng" cạnh "Hệ thống xét nghiệm".

**Bố cục:**
1. Đầu: cột trái `test_system` (chỉ đọc sau khi lưu), cột phải `run_days_per_year`. Dưới `test_system` một dòng `text-muted` "Dịch vụ <mã> — khoa <tên> — nhóm <cls_group>" (đọc bằng `frappe.db.get_value` khi chọn hệ thống).
2. Section "Nội kiểm": bảng `iqc_lines` — cột Vật liệu nội kiểm, Số mức, Số lần chạy mỗi ngày, Lượng dùng mỗi lần, Số thông số dùng chung. Ô vật liệu chỉ gợi ý mặt hàng loại "Vật liệu nội kiểm" (`link_filters`). Mô tả dưới cột số thông số: "Giả định — chờ xác nhận (TBD-15): chia đều theo số thông số".
3. Section "Chuẩn máy": bảng `calibration_lines` — cột Chất chuẩn, Số điểm chuẩn, Số lần lặp, Số lần chuẩn mỗi năm, Chi phí chất chuẩn mỗi lần (tiền theo NFR-LOC-001). Ô chất chuẩn chỉ gợi ý loại "Chất chuẩn".
4. Section "Số test ước tính mỗi năm" (`estimate_html`): hai số "Nội kiểm: 600 test" và "Chuẩn máy: 48 test", định dạng số `format_number`. Cập nhật **ngay** khi đổi `run_days_per_year` hoặc một ô số của hai bảng (sự kiện trường và `*_add`/`*_remove` của bảng con), gọi `normcore.api.qc_plan.estimate_tests` với dữ liệu đang có trên form, chống dội 300 ms. `complete` = False → thêm chú thích `text-muted` "Chưa đủ số liệu ở một số dòng". Dòng cuối `text-muted`: "Dùng khi sản lượng không có số test nội kiểm, chuẩn máy thực tế (FR-QC-006)".

**Cảnh báo đầu form** (`frm.dashboard.set_headline_alert`, màu `orange`): sau khi lưu, nếu `missing_iqc_warning(test_system).warning` → message máy chủ ("Hệ thống GLU-A chưa có kế hoạch nội kiểm"). Không chặn lưu.

| Trạng thái | Hiển thị |
| :-- | :-- |
| Mới, chưa chọn hệ thống | Hai bảng trống; khối ước tính "0 test"; dòng mô tả hệ thống ẩn |
| Hai bảng trống | Bảng con trống chuẩn Desk; nếu nhóm xét nghiệm: cảnh báo thiếu nội kiểm sau khi lưu |
| Đang tải ước tính / lỗi | Giữ số cũ, chú thích "Đang tính…"; lỗi gọi API: "Không tính được số test ước tính." + nút "Thử lại" |
| Không có quyền (Doc Controller, Council; Clinician khoa khác mở theo URL) | Trang không đủ quyền chuẩn Desk |
| Chỉ đọc (Auditor, Finance, Resource Manager, Director, Consultant, Admin) | Form chỉ đọc, không nút lưu, không thêm/xóa dòng; khối ước tính và cảnh báo vẫn hiện |
| Lỗi lưu | Thông báo máy chủ: thiếu trường / ngoài miền theo dòng (TC-CLS-24), mặt hàng sai loại (TC-CLS-25, "mặt hàng HC_GLU thuộc loại Hóa chất, không phải Vật liệu nội kiểm"), vật liệu lặp, hệ thống đã có kế hoạch (DI-11) |
| Đề xuất AI chưa xử lý | Không có ở FEAT này (FEAT-038, R2) |

## SCR-DSK-034 Chương trình ngoại kiểm (L + F)

Hiện thực: List + Form chuẩn NC EQA Program; tệp `nc_eqa_program.js`. Lối tắt Workspace "Chương trình ngoại kiểm" trong nhóm cận lâm sàng.

**Danh sách**: cột Mã (ID), Tên chương trình, Đơn vị triển khai, Khoa tham gia; bộ lọc chuẩn khoa. Clinician, Dept Head chỉ thấy khoa được gán.

**Form:**
1. Cột trái: `eqa_code`, `program_name`, `provider`, `department`. Cột phải: `rounds_per_year`, `samples_per_round`, `annual_fee`, `annual_shipping_fee`.
2. Bảng "Dịch vụ tham gia" (`services`): cột Dịch vụ (chỉ gợi ý dịch vụ `is_paraclinical` = 1 qua `link_filters`), Tỷ lệ riêng (%). Mô tả trên bảng: "Để trống tỷ lệ ở mọi dòng để chia đều; nếu nhập thì nhập ở mọi dòng, tổng bằng 100%".
3. Tóm tắt (`summary_html`), cập nhật ngay khi sửa số đợt, số mẫu hoặc bảng (gọi `normcore.api.qc_plan.eqa_summary`, chống dội 300 ms): "Số mẫu mỗi năm: 12"; "Cách chia: Chia đều cho n dịch vụ (mỗi dịch vụ x%)" hoặc "Tỷ lệ riêng, tổng y%". `mode` = `invalid` → pill `orange` với message ("Tổng tỷ lệ riêng của các dịch vụ là 90%, phải bằng 100%" hoặc "Tỷ lệ riêng phải nhập ở mọi dòng hoặc để trống ở mọi dòng"). Máy chủ vẫn từ chối khi lưu.

| Trạng thái | Hiển thị |
| :-- | :-- |
| Danh sách rỗng | Trạng thái trống chuẩn Desk |
| Mới, bảng dịch vụ trống | Tóm tắt "Chưa có dịch vụ tham gia"; lưu bị từ chối "Thiếu Dịch vụ tham gia" |
| Đang tải / lỗi tóm tắt | "Đang tính…"; lỗi: "Không tính được tóm tắt." + "Thử lại" |
| Không có quyền (Doc Controller, Council; Clinician khoa khác) | Trang không đủ quyền chuẩn Desk |
| Chỉ đọc (Auditor, Finance, Resource Manager, Director, Consultant, Admin) | Form chỉ đọc; tóm tắt vẫn hiện |
| Lỗi lưu | Thông báo máy chủ: thiếu trường (TC-CLS-24), tổng tỷ lệ khác 100% (TC-CLS-25), tỷ lệ chỗ có chỗ trống, dịch vụ lặp, dịch vụ chưa đánh dấu cận lâm sàng |

## Nhập Excel kế hoạch chất lượng

Trang `import-excel` của FEAT-004 không đổi; bộ "Kế hoạch chất lượng" (hai cột: Mã hệ thống xét nghiệm, Số ngày chạy mỗi năm) hiện với người có quyền tạo. Bảng nội kiểm, chuẩn máy khai trên form (ASM-032-07).

## Kiểm chung
- 1366 × 768: hai bảng con năm cột hiện đủ không cuộn ngang ở 1366 px; khối ước tính và tóm tắt xuống dòng dưới 768 px.
- Bàn phím: chuẩn Desk (Ctrl+S, Tab theo thứ tự trường; không thêm phím tắt riêng); nút "Kế hoạch chất lượng", "Thử lại" là `button` lấy được focus; liên kết kế hoạch là thẻ `a`.
- Tương phản (NFR-USE-004): chỉ lớp Desk, không màu tự đặt.
- Chuỗi: mọi chuỗi JS qua `__()`, có dòng trong `vi.csv`. Test quy ước tĩnh `tests/unit/test_qc_plan_ui_conventions.py` (mẫu `test_test_system_ui_conventions.py`): không mã màu hex trong `nc_qc_plan.js`, `nc_eqa_program.js`, phần thêm của `nc_test_system.js`; mọi chuỗi `__()` có bản dịch; gọi đúng tên API `normcore.api.qc_plan.estimate_tests`, `eqa_summary`, `missing_iqc_warning`.

API dùng: `normcore.api.qc_plan.estimate_tests`, `normcore.api.qc_plan.eqa_summary`, `normcore.api.qc_plan.missing_iqc_warning`, `normcore.api.test_system.get_status`; trang `import-excel` (FEAT-004).
