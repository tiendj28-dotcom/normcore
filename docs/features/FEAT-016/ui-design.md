# FEAT-016 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-020, SCR-DSK-021 (luồng tính giá: `t5` "Nhập số liệu kế toán" → "Chốt"); `design.md`; `technical-design.md` mục 2–5. Form và danh sách chuẩn của Desk, không trang Vue (ASM-129). Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.csv` (giữ thứ tự chữ cái, không trùng khóa); nhãn DocType, tùy chọn Select và thông báo máy chủ tiếng Việt. Chỉ dùng biến CSS của Desk, `indicator-pill`, `frm.dashboard`; không mã màu cứng. Mọi quyền do máy chủ quyết; ẩn/hiện nút chỉ là tiện ích. Số tiền định dạng theo NFR-LOC-001 (`format_currency`, dấu chấm hàng nghìn).

**Workspace "Normcore"**: thêm nhóm lối tắt "Kế toán và phân bổ" (sau nhóm thiết bị/cận lâm sàng): "Nhập số liệu kế toán" (List NC Accounting Import), "Bảng ánh xạ tài khoản" (NC Account Mapping), "Sản lượng dịch vụ" (NC Service Volume), "Tiêu chí trung tâm chi phí" (NC Cost Center Driver), "Quy tắc phân bổ" (NC Allocation Rule). Lối tắt chỉ hiện với vai trò đọc được DocType (Desk tự lọc).

## SCR-DSK-020 Nhập số liệu kế toán (F)

Hiện thực: List + Form chuẩn NC Accounting Import; tệp `nc_accounting_import.js`, `nc_accounting_import_list.js`.

**Danh sách**: cột Mã (`KT-2026-01`), Năm tài chính, Chế độ kế toán, Số dòng, Tổng tiền, Trạng thái (`get_indicator`: Nháp `orange`, Đã chốt `green`; Nháp có `error_count` > 0 → `red` "Có dòng lỗi"). Bộ lọc chuẩn: năm, trạng thái. Sắp mới nhất trước (nhiều lần nhập cùng năm cùng hiện — FR-ACCT-011). Nút "Tải tệp mẫu" (khi có quyền đọc): `normcore.api.accounting.download_template` qua `open_url_post`/`window.open` với `frappe.request.url`.

**Form — bản ghi mới**: chỉ hiện `fiscal_year`, `accounting_regime` (mặc định Hành chính sự nghiệp), `source_file` và dòng hướng dẫn "Tải tệp Excel theo mẫu (Mã tài khoản, Tên tài khoản, Mã trung tâm chi phí, Số tiền) rồi bấm Lưu." kèm liên kết "Tải tệp mẫu". Lưu → máy chủ đọc tệp (`before_insert`); lỗi mức tệp (không phải .xlsx, thiếu cột) hiện hộp thoại lỗi chuẩn, bản ghi không được tạo.

**Form — bản ghi đã có** (bố cục):
1. Đầu form: cột trái `fiscal_year`, `accounting_regime`, `source_file`; cột phải `status`, `line_count`, `total_amount`, `error_count`. `fiscal_year`, `accounting_regime` chỉ đọc sau khi tạo.
2. **Khối tóm tắt** (HTML `summary_html`, không lưu; gọi `normcore.api.accounting.get_import_summary(name)` lúc mở form và sau mỗi hành động): ba thẻ ngang — "Số dòng / Tổng tiền", "Dòng lỗi khi đọc tệp" (số, pill `red` nếu > 0, `green` "Không có"), "Dòng chưa gán loại chi phí" (số, pill `orange` nếu > 0); xuống cột dưới 768 px.
3. **Lỗi theo dòng** (trong khối tóm tắt, chỉ khi `errors` có): bảng "Dòng Excel | Cột | Lỗi" (dùng `text` của lỗi, tối đa 200 dòng, còn lại "và n lỗi khác"). Dưới bảng: "Sửa tệp, đính kèm lại ở ô Tệp nguồn rồi bấm Đọc lại tệp, hoặc tạo lần nhập mới."
4. **Dòng chưa gán** (chỉ khi `unassigned` có): bảng "Dòng | Mã TK | Trung tâm | Số tiền" và nút "Lọc bảng dòng" (đặt bộ lọc lưới hoặc cuộn tới dòng đầu tiên chưa gán, tô dòng bằng lớp `indicator-pill orange` ở cột Loại chi phí).
5. **Bảng Dòng** (`lines`): cột Mã TK, Tên TK, Trung tâm, Số tiền, Loại chi phí, Loại trừ, Người sửa. Lưới không thêm/xóa dòng (`cannot_add_rows`, `cannot_delete_rows`); các cột nguồn chỉ đọc. Mỗi dòng có nút "Sửa loại chi phí" (trong form dòng, `frm.fields_dict.lines.grid` thêm nút) khi "Nháp" và có quyền ghi → hộp thoại `frappe.ui.Dialog`: "Loại chi phí" (Select 6 mã, kèm mô tả tiếng Việt từng mã), "Loại trừ" (Check), "Lý do" (Small Text, bắt buộc); Lưu → `normcore.api.accounting.update_line(name, row, cost_category, is_excluded, change_reason)`; thiếu lý do → hộp thoại báo "Nhập lý do…" và giữ hộp thoại mở (TC-ACCT-04). Sửa trực tiếp ô Loại chi phí trong lưới vẫn được nhưng lưu mà không có lý do bị máy chủ từ chối với cùng thông báo.
6. **Tổng theo trung tâm và loại chi phí**: "Nháp" → bảng xem trước từ `totals` của `get_import_summary` (tiêu đề "Xem trước — ghi khi chốt"); "Đã chốt" → bảng con `totals` chỉ đọc. Bảng dạng ma trận: hàng = trung tâm, cột = LABOR, DRUG_SUPPLY, DEPRECIATION, UTILITY, MANAGEMENT, hàng tổng cuối (cùng bố cục bảng mục 2.1 test-cases).

**Nút** (thanh trên, chỉ khi "Nháp" và `frm.perm[0].write`):
| Nút | Vị trí | API | Ghi chú |
| :-- | :-- | :-- | :-- |
| "Chốt" | nút chính (`primary`) | `finalize(name)` | Hộp thoại xác nhận: "Sau khi chốt, các dòng bị khóa và không mở lại được. Chốt lần nhập này?". Bị từ chối → hộp thoại liệt kê lý do của máy chủ (dòng lỗi, dòng chưa gán — TC-ACCT-02, 03). Nút vẫn bấm được khi `can_finalize` = false nhưng có tooltip lý do (máy chủ quyết) |
| "Gán lại theo bảng ánh xạ" | nhóm "Thao tác" | `reapply_mapping(name)` | Thông báo "Đã gán lại n dòng; các dòng sửa tay giữ nguyên" |
| "Đọc lại tệp" | nhóm "Thao tác" | `reload_file(name)` | Xác nhận: "Đọc lại tệp sẽ thay toàn bộ dòng và bỏ các sửa tay. Tiếp tục?" |
| "Tải tệp mẫu" | nhóm "Thao tác" | `download_template()` | Mọi vai trò đọc được |

Phím tắt: Ctrl+S lưu (chuẩn Desk); không thêm phím riêng.

| Trạng thái | Hiển thị |
| :-- | :-- |
| Nháp, không lỗi, đã gán đủ | Pill `orange` "Nháp"; thẻ lỗi, chưa gán `green` "Không có"; "Chốt" sẵn sàng |
| Nháp có lỗi dòng | Headline `red` (`frm.dashboard.set_headline_alert`): "Tệp có n dòng lỗi: sửa tệp rồi Đọc lại tệp. Chưa chốt được." |
| Nháp có dòng chưa gán | Headline `orange`: "Còn n dòng chưa có loại chi phí." |
| Đã chốt | Pill `green` "Đã chốt"; form chỉ đọc (máy chủ chặn mọi lưu), ẩn mọi nút trừ "Tải tệp mẫu"; headline `green` "Đã chốt: số liệu dùng được cho lần tính giá." |
| Đang tải tóm tắt / lỗi tải | "Đang tải tóm tắt…"; lỗi: "Không tải được tóm tắt lần nhập." + nút "Thử lại" |
| Chỉ đọc (NC Director, NC Admin, NC Auditor) | Form chỉ đọc chuẩn Desk; khối tóm tắt, lỗi, tổng vẫn hiện; không nút hành động |
| Không có quyền (Clinician, Consultant, Resource Manager…) | Desk báo "Không có quyền"; lối tắt Workspace không hiện |

## SCR-DSK-021 Sản lượng và phân bổ (L + F)

Hiện thực: bốn List + Form chuẩn (ASM-129), nối bằng nhóm Workspace "Kế toán và phân bổ" và nút liên kết qua lại ở đầu mỗi danh sách ("Sản lượng dịch vụ", "Tiêu chí trung tâm chi phí", "Quy tắc phân bổ", "Bảng ánh xạ tài khoản" — `frappe.set_route("List", ...)`). Liên kết sang SCR-DSK-037 để FEAT-035.

**Nút "Nhập từ Excel"** trên danh sách NC Service Volume, NC Cost Center Driver, NC Account Mapping (khi `frappe.model.can_create`): mở trang `import-excel` với bộ `nc_service_volume` / `nc_cost_center_driver` / `nc_account_mapping` chọn sẵn (`frappe.set_route("import-excel", {import_set: ...})`; nếu trang chưa đọc tham số thì chỉ mở trang — Dev kiểm và ghi vào log, như FEAT-031). Kết quả nhập (số tạo/cập nhật, lỗi theo dòng — TC-ACCT-05) do trang FEAT-004 hiển thị.

### Sản lượng dịch vụ (NC Service Volume)
- **Danh sách**: cột Năm, Dịch vụ, Khoa, **Kịch bản** ([1.1]), Sản lượng. Bộ lọc chuẩn: năm, dịch vụ, khoa, kịch bản; nhóm theo năm (sidebar "Nhóm theo" chuẩn).
- **Form**: một cột trái `fiscal_year`, `technical_service`, `department`; cột phải `scenario` (mặc định "Thực tế 12 tháng"), `volume`. Lỗi trùng bốn trường hiện thông báo máy chủ.

### Tiêu chí trung tâm chi phí (NC Cost Center Driver)
- **Danh sách**: cột Năm, Trung tâm chi phí, Số nhân lực, Diện tích (m²), Doanh thu. Bộ lọc: năm, trung tâm.
- **Form**: trái `fiscal_year`, `cost_center`; phải `headcount`, `area_m2`, `revenue`. Mô tả dưới khối: "Dùng cho phân bổ cấp 1 (Hỗ trợ sang Lâm sàng) theo HEADCOUNT, AREA, REVENUE."

### Quy tắc phân bổ (NC Allocation Rule)
- **Danh sách**: cột Tên quy tắc, Cấp, Loại chi phí, Tiêu chí, Trung tâm (trống hiện "Mọi trung tâm"). Bộ lọc: cấp, loại chi phí.
- **Form**: `rule_name`; trái `level`, `cost_category`; phải `driver`, `cost_center`. Khi `level` = "Cấp 2", JS lọc tùy chọn `driver` bỏ HEADCOUNT, AREA, REVENUE (`frm.set_df_property("driver", "options", ...)`) và đặt `get_query` của `cost_center` chỉ trung tâm "Lâm sàng"; "Cấp 1" → mọi tiêu chí, trung tâm "Hỗ trợ". Đổi cấp mà tiêu chí đang chọn không hợp lệ → xóa tiêu chí. Máy chủ vẫn kiểm (TC-ACCT-07). Mô tả trường `driver` liệt kê nghĩa tiếng Việt bảy mã (BR-COST-009).

### Bảng ánh xạ tài khoản (NC Account Mapping)
- **Danh sách**: cột Chế độ kế toán, Tiền tố tài khoản, Loại chi phí, Ghi chú; sắp theo tiền tố. Bộ lọc: chế độ, loại. Dòng có ghi chú chứa "Giả định — chờ xác nhận" hiện pill `gray` "Giả định" (`get_indicator` không dùng vì không có trạng thái; dùng `formatters.note`).
- **Form**: trái `accounting_regime`, `account_prefix`; phải `cost_category`, `note`. Mô tả: "Khớp theo tiền tố dài nhất. Sửa bảng không đổi lần nhập đã có; dùng Gán lại theo bảng ánh xạ trên lần nhập Nháp."

| Trạng thái (cả bốn) | Hiển thị |
| :-- | :-- |
| Rỗng | Trạng thái rỗng chuẩn Desk; NC Finance thấy nút "Thêm" và "Nhập từ Excel" |
| Lỗi lưu | Thông báo máy chủ tiếng Việt (trùng khóa, số âm, tiêu chí chỉ dùng cấp 1, sai loại trung tâm) |
| Chỉ đọc (Director, Admin, Auditor) | List/Form chỉ đọc; không nút Thêm, Nhập từ Excel |
| Không có quyền | Desk báo "Không có quyền" |

## Kiểm chung

- 1366 × 768: form lần nhập 10–50 dòng hiển thị không cuộn ngang (7 cột lưới vừa khung; ma trận tổng 6 cột); khối tóm tắt ba thẻ trên một hàng ≥ 992 px.
- Bàn phím: mọi nút là nút Desk chuẩn (Tab tới được); hộp thoại sửa loại dùng Enter để lưu, Esc để đóng.
- Tương phản (NFR-USE-004): chỉ dùng màu `indicator-pill` và biến CSS của Desk; trạng thái luôn có chữ, không chỉ màu.
- Test quy ước giao diện `tests/unit/test_accounting_ui_conventions.py` (như FEAT-031): mọi chuỗi `__()` trong các tệp JS mới có bản dịch trong `vi.csv`; không mã màu hex trong JS/CSS mới; nút gọi đúng tên API ở `technical-design.md` mục 3.
