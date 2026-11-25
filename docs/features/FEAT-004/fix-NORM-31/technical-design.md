# NORM-31 — Thiết kế bản sửa: `import-excel` đọc `import_set`, kèm hai góp ý Reviewer NORM-28

Nhánh: `fix/NORM-31-import-set` (từ `origin/develop` `cf3f5f3`, sau khi PR #35 gộp). Quyết định Lead trên NORM-31: phương án 1, làm cả ba việc trên một nhánh, một PR.
Hồ sơ đặt dưới `docs/features/FEAT-004/fix-NORM-31/` theo tiền lệ `docs/features/FEAT-006/fix-NORM-27/`. Không tạo lại `DONE`, As-Built hay Test ref của FEAT-004/FEAT-016; QA ghi `acceptance.md`, `verdict.json` của bản sửa vào cùng thư mục này.

## 1. Phạm vi

| # | Việc | FEAT gốc | Tệp sửa | Màn hình |
| :-: | :-- | :-- | :-- | :-- |
| S1 | Trang `import-excel` chọn sẵn bộ nhập theo tham số `import_set` | FEAT-004 | `normcore/nc_core/page/import_excel/import_excel.js` | SCR-DSK-031 |
| S2 | Thông báo lỗi tiêu chí âm dùng nhãn tiếng Việt thay tên trường | FEAT-016 (FR-ACCT-010, ASM-126) | `normcore/costing/allocation_rules.py` | SCR-DSK-021 |
| S3 | Hộp thoại "Sửa loại chi phí" ghi rõ số dòng, mã tài khoản; không tự lấy dòng 1 | FEAT-016 (TC-ACCT-04) | `normcore/nc_costing/doctype/nc_accounting_import/nc_accounting_import.js`, `normcore/translations/vi.csv` | SCR-DSK-020 |

Ngoài phạm vi: không đổi API máy chủ, DocType, quyền, bộ nhập, công thức. Không đổi các nút "Nhập từ Excel" ở danh sách (đã truyền đúng `import_set` từ FEAT-016; `nc_equipment_compliance_list.js` không truyền khóa, giữ nguyên). Không DocType mới, không AMD.

## 2. S1 — `import-excel` đọc `import_set`

### Hiện trạng
- Các danh sách gọi `frappe.set_route("import-excel", { import_set: "<key>" })` (`nc_service_volume_list.js:6`, `nc_account_mapping_list.js:14`, `nc_cost_center_driver_list.js:6`, `nc_test_system_list.js:11`).
- Frappe v15 (`frappe/public/js/frappe/router.js`): đối số object của `set_route` được gán vào `frappe.route_options`, không vào chuỗi URL; mở thẳng `/app/import-excel?import_set=<key>` thì `set_route_options_from_url()` cũng nạp query vào `frappe.route_options`. Vậy một nguồn đọc duy nhất là `frappe.route_options.import_set` (ASM-004-01).
- `import_excel.js` chỉ có `on_page_load` (chạy một lần cho mỗi phiên trang); `load_sets()` luôn chọn `sets[0]`. Lần mở thứ hai từ danh sách khác không chạy lại `on_page_load`.

### Thiết kế
1. Thêm `frappe.pages["import-excel"].on_page_show = (wrapper) => wrapper.import_excel && wrapper.import_excel.apply_route_options();`. Frappe gọi `on_page_show` cả ở lần đầu (sau `on_page_load`) và mọi lần quay lại trang.
2. `ImportExcel.apply_route_options()`:
   - `const key = (frappe.route_options || {}).import_set;` Không có → return (giữ lựa chọn hiện tại).
   - Tiêu thụ tham số: `frappe.route_options = null` (giống List view của Frappe), để lần quay lại trang bằng nút Back không chọn lại.
   - Gọi `this.preselect(key)`.
3. `ImportExcel.preselect(key)`:
   - Danh sách bộ nhập chưa tải xong (`this.sets === null`) → lưu `this.pending_key = key`, return.
   - Đã tải: nếu `key` thuộc `this.sets.map(s => s.key)` và khác giá trị hiện tại → `this.set_field.set_value(key)` (sự kiện `change` gọi `reset()` như khi người dùng tự chọn). Không thuộc → không làm gì, không thông báo.
4. `load_sets()` callback: lưu `this.sets = r.message || []`; chọn `pending_key` nếu có trong `sets`, ngược lại `sets[0]` như cũ; xóa `pending_key`. Danh sách rỗng → giữ thông báo "You do not have permission to import data." như cũ, bỏ qua `pending_key`.
5. "Người dùng có quyền với bộ nhập" = bộ nhập có trong kết quả `normcore.api.importer.list_import_sets` (đã lọc `frappe.has_permission(doctype, "create")`). Không gọi API mới. Máy chủ vẫn kiểm quyền ở `download_template`/`import_file` như cũ; việc chọn sẵn chỉ là tiện ích giao diện.
6. `constructor`: khởi tạo `this.sets = null; this.pending_key = null;` trước `make()`.

### Tiêu chí nghiệm thu S1

Không có TC trong `docs/test-cases.md` cho hành vi này; mã kịch bản riêng `N31-xx` dùng làm tên test (tiền lệ NORM-27 dùng mã kịch bản E/K).

| Mã | Điều kiện kiểm được | Nguồn |
| :-- | :-- | :-- |
| N31-01 | `route_options = {import_set: "nc_service_volume"}`, danh sách có khóa đó → sau tải, giá trị trường là `nc_service_volume` | Issue NORM-31 việc 1 |
| N31-02 | Khóa không có trong danh sách (sai hoặc không có quyền) → giá trị là `sets[0].key`, không gọi `msgprint`/`throw`, không lỗi console | Issue việc 2 |
| N31-03 | Không có `route_options` → giá trị là `sets[0].key` (hành vi FEAT-004 cũ) | Issue việc 2 |
| N31-04 | Trang đã tải với bộ A; mở lại trang với `import_set` = B (có quyền) → giá trị đổi sang B, tệp đã tải lên bị xóa (`file_url` null, nút Kiểm tra tắt) | Hành vi lần mở thứ hai |
| N31-05 | Sau khi áp dụng, `frappe.route_options` là null; gọi `on_page_show` lần nữa không đổi lựa chọn người dùng đã đổi tay | ASM-004-01 |
| N31-06 | Danh sách rỗng + có `import_set` → không chọn gì, hiện "You do not have permission to import data." như cũ | Issue việc 2 |

## 3. S2 — nhãn tiếng Việt trong `driver_errors`

### Hiện trạng
`allocation_rules.py:34`: `f"{k} không được âm"` với `k` là fieldname (`headcount`, `area_m2`, `revenue`) → người dùng thấy "headcount không được âm". Vi phạm NFR-MNT-003 (thông báo tiếng Việt).

### Thiết kế
- Thêm hằng `DRIVER_LABELS = {"headcount": "Số nhân lực", "area_m2": "Diện tích (m²)", "revenue": "Doanh thu"}` — trùng nguyên văn `label` trong `nc_cost_center_driver.json`.
- `driver_errors`: `f"{DRIVER_LABELS.get(k, k)} không được âm"`; giữ thứ tự theo `values`, giữ chữ ký hàm và kiểu trả về. Module vẫn thuần Python. Controller `nc_cost_center_driver.py` không đổi.
- Không đụng `DRIVER_FIELDS`, `driver_shares`, `get_driver_values` (không ảnh hưởng số liệu, golden).

### Tiêu chí nghiệm thu S2

| Mã | Điều kiện | Nguồn |
| :-- | :-- | :-- |
| N31-07 | `driver_errors({"headcount": -1, "area_m2": -2, "revenue": -5})` == `["Số nhân lực không được âm", "Diện tích (m²) không được âm", "Doanh thu không được âm"]` (`assertEqual` đủ danh sách) | Góp ý Reviewer NORM-28 |
| N31-08 | Lưu NC Cost Center Driver có `headcount = -1` trên site → `ValidationError` có chuỗi "Số nhân lực không được âm", không có "headcount" | FR-ACCT-010 |
| — | `test_allocation_rules.py::test_driver_errors` hiện có giữ nguyên, vẫn đạt | Luật cứng 1 |

## 4. S3 — hộp thoại "Sửa loại chi phí của dòng"

### Hiện trạng
`nc_accounting_import.js:150`: `sel = get_selected_children()[0] || rows[0]` → chưa tích dòng nào thì mở hộp thoại cho dòng 1 mà người dùng không biết; tiêu đề chung "Edit cost category" không cho biết đang sửa dòng nào.

### Thiết kế
- Nút "Edit cost category of a line" (nhóm Actions, chỉ khi Nháp và có quyền ghi — như cũ):
  - `const sel = frm.fields_dict.lines.grid.get_selected_children() || [];`
  - `sel.length === 0` → `frappe.msgprint(__("Select one line in the Lines table first."))`, không mở hộp thoại.
  - `sel.length > 1` → `frappe.msgprint(__("Select only one line to edit."))`, không mở hộp thoại (ASM-016-01).
  - Đúng một dòng → `edit_line_dialog(frm, sel[0])`.
  - Bỏ hẳn nhánh `|| rows[0]`.
- `edit_line_dialog`: tiêu đề `__("Edit cost category: line {0}, account {1}", [row.idx, row.account_code])`. `row.idx` là số thứ tự dòng trong lưới (1-based) mà người dùng thấy ở cột "#"; `account_code` đi qua `frappe.utils.escape_html` trước khi đưa vào tiêu đề (dữ liệu từ tệp Excel). Phần còn lại của hộp thoại, API `update_line`, kiểm lý do bắt buộc (TC-ACCT-04) giữ nguyên.
- `vi.csv` thêm ba khóa, giữ thứ tự chữ cái, không trùng khóa:
  - `Edit cost category: line {0}, account {1}` → `Sửa loại chi phí: dòng {0}, tài khoản {1}`
  - `Select one line in the Lines table first.` → `Chọn một dòng trong bảng Dòng trước.`
  - `Select only one line to edit.` → `Chỉ chọn một dòng để sửa.`
  - Khóa cũ `Edit cost category` không còn được dùng trong JS: giữ dòng trong `vi.csv` (không xóa bản dịch, tránh đụng tệp khác dùng chung).

### Tiêu chí nghiệm thu S3

| Mã | Điều kiện | Nguồn |
| :-- | :-- | :-- |
| N31-09 | Không tích dòng nào, bấm nút → không tạo `frappe.ui.Dialog`, `msgprint` được gọi với "Select one line in the Lines table first." | Góp ý Reviewer NORM-28 |
| N31-10 | Tích dòng `idx = 3`, `account_code = "6421"` → một Dialog với tiêu đề chứa "3" và "6421" (đúng chuỗi `Edit cost category: line 3, account 6421` khi `__` là định dạng đồng nhất) và `default` của `cost_category` bằng của dòng đó | Góp ý Reviewer NORM-28 |
| N31-11 | Tích hai dòng → không tạo Dialog, `msgprint` "Select only one line to edit." | ASM-016-01 |
| N31-12 | `test_accounting_ui_conventions.py` (chuỗi `__()` có bản dịch, không mã màu cứng, đúng API) và `test_vi_csv_order.py` vẫn đạt, không sửa | Luật cứng 1 |

## 5. Cách kiểm thử

- **S1, S3 — test hành vi JS chạy thật trong Node**, theo tiền lệ NORM-27 (`tests/unit/test_procedure_editor_behavior.py` + `tests/unit/js/procedure_editor_harness.js`): không đọc chuỗi mã nguồn.
  - `normcore/tests/unit/js/import_excel_harness.js`: nạp `import_excel.js` vào `vm` với `frappe` giả (`pages`, `ui.make_app_page` trả `page` giả có `add_field`/`set_secondary_action`/`add_inner_button`/`main`, `call` trả `list_import_sets` bất đồng bộ, `route_options`, `provide`, `msgprint`, `throw`); `$`/jQuery tối giản cho `page.main.find(...)`, `.prop`, `.text`, `.html`, `.empty`. Mỗi kịch bản in một dòng JSON: `value`, `file_url`, `btn_check_disabled`, `message`, `route_options`, `msgprint_calls`, `consoleErrors`.
  - `normcore/tests/unit/js/accounting_import_harness.js`: nạp `nc_accounting_import.js`, bắt handler qua `frappe.ui.form.on`, gọi `refresh(frm)` với `frm` giả (`doc.status = "Nháp"`, `perm[0].write = 1`, lưới có `get_selected_children`), bắt các `add_custom_button`, bấm nút "Edit cost category of a line"; `frappe.ui.Dialog` giả ghi lại `title`, `fields`.
  - Test Python: `normcore/tests/unit/test_import_excel_behavior.py` (N31-01…06), `normcore/tests/unit/test_accounting_import_behavior.py` (N31-09…11). Không có Node thì test báo lỗi (AssertionError), không skip.
- **S2** — `normcore/tests/unit/test_allocation_rules.py` thêm `test_N31_07_driver_errors_dung_nhan_tieng_viet`; `normcore/nc_costing/doctype/nc_cost_center_driver/test_nc_cost_center_driver.py` thêm `test_N31_08_so_am_bao_nhan_tieng_viet` (FrappeTestCase).
- Tên test: `test_N31_NN_<mô_tả>`.
- Test bắt được lỗi thật: Dev ghi vào `implementation-log.md` kết quả chạy test mới với mã `origin/develop` trước khi sửa (phải đỏ) và sau khi sửa (xanh).

## 6. Giả định, rủi ro

- **ASM-004-01**: nguồn tham số là `frappe.route_options.import_set` (gồm cả query URL); tiêu thụ xong đặt `frappe.route_options = null`; khóa sai/không có quyền bỏ qua im lặng.
- **ASM-016-01**: nút sửa dòng đòi đúng một dòng được tích; 0 hoặc ≥ 2 dòng → thông báo, không mở hộp thoại.
- Rủi ro: `on_page_show` có thể chạy trước khi `list_import_sets` trả về → đã xử lý bằng `pending_key`. Đổi `set_value` gọi `reset()` xóa tệp đã tải lên — chấp nhận, giống người dùng tự đổi bộ nhập.
- Rủi ro xung đột: `vi.csv` dùng `merge=union`; Dev chạy `test_vi_csv_order.py` sau mỗi lần gộp develop.
