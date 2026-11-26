# FEAT-034 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-014 (phần **[1.1]**), SCR-DSK-041; `design.md` mục 3 (Lưới định mức, Bản ghi chỉ đọc, chỉ báo trạng thái); hợp đồng API ở `technical-design.md` mục 3. Nền là giao diện FEAT-012 (`docs/features/FEAT-012/ui-design.md`): chỉ mô tả phần **thêm hoặc đổi**; phần còn lại giữ nguyên.

Quy ước chung: chuỗi qua `__()` (JS/Vue) và `_()` (Python), có trong `normcore/translations/vi.csv`; chỉ dùng biến màu của Desk, nhãn luôn kèm chữ (NFR-USE-004); số theo NFR-LOC-001; kiểm ở 1366 × 768.

## SCR-DSK-041 Mẫu định mức (Form + List chuẩn của Desk, DocType NC Norm Template)

**Danh sách** (`nc_norm_template_list.js`): cột Mã mẫu, Nhóm chuyên ngành, Đang dùng; chỉ báo `green` "Đang dùng" / `gray` "Không dùng"; bộ lọc chuẩn Nhóm chuyên ngành, Đang dùng. Nút "Mới" chỉ hiện với NC Finance, NC Admin (theo DocPerm).

**Form** (`nc_norm_template.js`), một cột, hai section:
1. "Thông tin mẫu": Mã mẫu (`template_code`, chỉ sửa khi tạo), Nhóm chuyên ngành (`cls_group`), Đang dùng (`is_active`). Mô tả dưới "Đang dùng": "Mỗi nhóm chuyên ngành chỉ có một mẫu đang dùng. Mẫu áp khi khởi tạo bộ định mức cho dịch vụ cận lâm sàng thuộc nhóm."
2. "Khoản mục": bảng con NC Norm Template Item — cột Tên khoản mục, Cấu phần (Select, nhãn tiếng Việt như lưới: Nhân lực, Thuốc và hóa chất, Vật tư, Thiết bị, Hạ tầng, Tiện ích), Cấp phát sinh mặc định (Theo kết quả, Theo ống mẫu, Theo mẻ, Theo ngày-máy, Theo kỳ), Bắt buộc (ô đánh dấu). Bảng sắp xếp được (kéo thả của Desk); thứ tự là thứ tự ghép với dòng quy trình (ASM-034-04).

Nhãn Select hiển thị tiếng Việt: giá trị lưu là mã (`RESULT`…), form dùng `frappe.meta` + `formatter` của trường để hiện nhãn (hoặc Select có nhãn dịch trong `vi.csv` cho từng mã). Cùng cách cho NC Norm Line trên form NC Norm Set (bảng chỉ đọc).

**Trạng thái**: Mẫu mới cài sẵn (`MDM-HOA-SINH`, `MDM-MIEN-DICH`) hiện dải `blue` trên form: "Mẫu cài sẵn — chưa dùng. Rà khoản mục rồi bật Đang dùng." khi `is_active` = 0 và mã thuộc hai mẫu cài sẵn. Lỗi lưu (hai mẫu đang dùng cùng nhóm, trùng tên khoản mục, mẫu đang dùng chưa có khoản mục) hiện bằng `frappe.throw` của máy chủ, chữ tiếng Việt. Chỉ đọc: NC Clinician, NC Department Head, NC Resource Manager, NC Director, NC Consultant, NC Auditor — form không có nút Lưu, bảng con không thêm/xóa được (DocPerm). Không có quyền (NC Council Member, NC Document Controller): Desk báo không có quyền.

**Điều hướng**: lối tắt "Mẫu định mức" trong Workspace NC Costing, nhóm cùng "Bộ định mức".

**Kiểm**: 1366 × 768, Tab đi đủ trường và bảng con, nút Lưu Ctrl+S của Desk.

## SCR-DSK-013 và form quy trình — khởi tạo có chọn hệ thống

Nút "Khởi tạo bộ định mức" (danh sách NC Norm Set và form NC Clinical Procedure) gọi `create_options(procedure)` trước:
- `required` = false → gọi `create_norm_set(procedure)` như FEAT-012.
- `required` = true → `frappe.ui.Dialog` "Chọn hệ thống xét nghiệm": một Select bắt buộc liệt kê `test_systems` dạng "GLU-A · EQ_A"; hệ thống có `open_set` hiện thêm "(đã có bộ đang soạn)". Có `template` → dòng chữ `--text-muted` "Sẽ thêm khoản mục bắt buộc của mẫu <tên mẫu>." Nút "Khởi tạo" → `create_norm_set(procedure, test_system)`. Kết quả có `message` (đã có bộ đang soạn) → `frappe.show_alert` rồi mở bộ đó. Xong → `frappe.set_route("norm-grid", name)`.
- Lỗi máy chủ hiện trong hộp thoại (`role="alert"`).

Danh sách NC Norm Set: thêm cột và bộ lọc chuẩn "Hệ thống xét nghiệm".

## SCR-DSK-014 Lưới định mức — phần **[1.1]**

Các phần cận lâm sàng chỉ hiện khi `meta.is_paraclinical`. Dịch vụ không cận lâm sàng: lưới như FEAT-012 (ASM-034-08), chỉ thêm nút "Xuất Excel".

**1. Đầu trang** — thêm sau tên khoa:
- Nhãn hệ thống `blue` "Hệ thống GLU-A · EQ_A" (liên kết mở form NC Test System) khi có `test_system`; dịch vụ cận lâm sàng mà bộ không có hệ thống → nhãn `orange` "Chưa gắn hệ thống xét nghiệm".
- "Sao chép từ <tên bộ>" (liên kết `norm-grid/<copied_from>`) khi có; "Mẫu: <norm_template>" (liên kết form mẫu) khi có.
- Nút thêm theo `actions`: "Sao chép sang hệ thống khác" (`btn-default`, có `copy_norm_set`), "Xuất Excel" (`btn-default`, có `export_norm_set`, mọi trạng thái, kể cả NC Auditor). Thứ tự: nút chính theo trạng thái, "Trả lại", "Thêm dòng", "Sao chép sang hệ thống khác", "Xuất Excel". Thiếu chỗ ở 1366 px: hai nút cuối gom vào menu "…" (`dropdown` của Desk).

**2. Ô số xét nghiệm mỗi ống** — hàng ngay trên lưới, trái: nhãn "Số xét nghiệm bình quân trên một ống mẫu", ô số (Float, ≥ 0). Sửa được khi có `save_head`; rời ô/Enter → `save_head(norm_set, {"tests_per_tube": v})`. Có dòng Theo ống mẫu mà ô trống/0 → viền `orange` + chữ nhỏ "Bắt buộc trước khi xác nhận chuyên môn (có dòng Theo ống mẫu)". Chỉ đọc: hiện số, không viền.

**3. Dải thông báo** — thêm, sau các dải của FEAT-012:
- `warnings` (TC-CLS-26) → dải `yellow` cho mỗi cảnh báo, ví dụ "Hệ thống GLU-A chưa có kế hoạch nội kiểm. Vẫn khóa được; vật liệu nội kiểm sẽ không được tính." + liên kết "Mở kế hoạch chất lượng" (form NC QC Plan của hệ thống, hoặc tạo mới). Hiện ở mọi trạng thái.
- `set_blockers` (chỉ Nháp) → dải `yellow` "Chưa xác nhận chuyên môn được:" + danh sách gạch đầu dòng từng lý do (chữ máy chủ). Khoản mục thiếu có nút "Lọc dòng giữ chỗ".

**4. Thanh lọc** — thêm Select "Cấp phát sinh" (Tất cả + 5 nhãn). "Chỉ dòng cần xử lý" tính thêm dòng giữ chỗ và dòng `qc_conflict`.

**5. Cột lưới** — chèn sau "Cấu phần":

| Cột | Trường | Sửa được (Nháp + quyền) | Ghi chú |
| :-- | :-- | :-- | :-- |
| Cấp phát sinh | `cost_level` | Có (Select 5, nhãn `options.cost_level`) | Đổi khỏi "Theo kết quả" mà `apply_k` đang bật → máy khách tắt `apply_k` trong cùng lần `save_line` (tránh lỗi DI-17); đổi sang Theo ngày-máy/Theo kỳ mà chưa có "Gắn với" → mở bảng chi tiết dòng, focus ô "Gắn với" |
| Nhân k | `apply_k` | Ô đánh dấu, **chỉ bật được** khi cấp = Theo kết quả, cấu phần Thuốc và hóa chất/Vật tư, bộ có hệ thống; ngoài ra ô vô hiệu + tooltip "Chỉ dòng Theo kết quả loại thuốc, hóa chất, vật tư" | Bật → ô Hao hụt % về 0 và vô hiệu, tooltip "Hao hụt đã nằm trong hệ số k" (BR-CLS-001) |

Cột "Định mức BV": nhãn đơn vị theo cấp hiện dưới tiêu đề cột ở tooltip: "cho một kết quả / một ống / một mẻ / một ngày / một năm" (data-model 3.5); trên ô, hậu tố nhỏ "/ống", "/mẻ", "/ngày", "/năm" khi cấp khác Theo kết quả.

Cột "Thành tiền tạm tính": dòng cấp khác Theo kết quả hoặc nhân k → chữ `--text-muted` "Tính ở lần tính giá" (ASM-034-22).

**Dòng giữ chỗ** (`placeholder`): nền nhấn `--bg-yellow` (biến Desk) + nhãn `orange` "Khoản mục bắt buộc — chưa có lượng: <template_item>" ở cột Nguồn lực; các ô trống có viền gạch. Dòng có `template_item` khác: nhãn nhỏ `gray` "Mẫu: <tên>" dưới nguồn lực.

**Dòng `qc_conflict`** (bộ cũ có dòng trùng mặt hàng kế hoạch chất lượng): biểu tượng cảnh báo `red` + tooltip "Mặt hàng đã có trong kế hoạch chất lượng của hệ thống; đánh dấu Loại trừ hoặc đổi nguồn lực".

**6. Bảng chi tiết dòng** — thêm: "Gắn với" (Select: Hệ thống xét nghiệm, Thiết bị; chỉ hiện khi Theo ngày-máy/Theo kỳ; mục "Hệ thống xét nghiệm" vô hiệu khi bộ không có hệ thống), "Thiết bị được gắn" (Link NC Equipment qua `search_resources` với cấu phần EQUIPMENT, chỉ khi "Thiết bị"), "Khoản mục của mẫu" (Select các `template_items` + trống; chỉ khi bộ có mẫu). Lý do loại trừ có sẵn "Không áp dụng" (đánh dấu khoản mục không áp dụng, UC-021 2a).

**7. Khối khoản mục của mẫu** (dưới khối chi phí tạm tính, chỉ khi có `norm_template`): bảng nhỏ Khoản mục · Cấu phần · Cấp mặc định · Bắt buộc · Tình trạng ("Đã có" `green` / "Thiếu" `orange` từ `template_items[].satisfied`). Bấm một khoản mục "Thiếu" → lọc tới dòng giữ chỗ của khoản mục đó.

**8. Thêm dòng** (hộp thoại FEAT-012) — thêm: Cấp phát sinh (mặc định Theo kết quả; ẩn ở dịch vụ không cận lâm sàng), Nhân k (theo cùng điều kiện cột), Gắn với / Thiết bị được gắn (khi Theo ngày-máy/Theo kỳ). Lỗi FR-NORM-024 (TC-CLS-31) hiện trong hộp thoại: "QC_L đã có trong kế hoạch nội kiểm/chuẩn máy của hệ thống GLU-A, không làm dòng định mức." — hộp thoại giữ mở, ô Nguồn lực viền đỏ.

**9. Hành động bộ** — thêm/đổi:
- "Xác nhận chuyên môn" bị từ chối (TC-CLS-32): hộp thoại "Chưa xác nhận chuyên môn được" liệt kê **trước** các lý do của bộ (số xét nghiệm mỗi ống, khoản mục thiếu, chưa gắn hệ thống, dòng trùng kế hoạch), rồi các dòng như FEAT-012. Lý do "số xét nghiệm mỗi ống" bấm được → đóng hộp thoại, focus ô ở mục 2.
- "Sao chép sang hệ thống khác": `frappe.ui.Dialog` — Select bắt buộc "Hệ thống đích" (`meta.other_test_systems`, dạng "GLU-B · EQ_B"); chữ `--text-muted` "Tạo bộ nháp mới cho hệ thống đích, mang các dòng có mã bước còn trong quy trình; xác nhận các dòng phải làm lại." → `copy_norm_set(source, test_system)`. Kết quả có `skipped` → hộp thoại thứ hai "Các dòng không sao chép" liệt kê "Lxxx — <lý do>", nút "Mở bộ mới"; không có `skipped` → `frappe.show_alert` "Đã tạo <tên>" rồi `frappe.set_route("norm-grid", name)`. Có `message` (đã có bộ đang soạn) → alert và mở bộ đó.
- "Xuất Excel": `window.open` tới `/api/method/normcore.api.norm.export_norm_set?name=<tên>` (tải tệp; trình duyệt xử lý). Lỗi → `frappe.msgprint` chữ máy chủ.
- "Khóa": không đổi; có `warnings` thì hộp xác nhận thêm dòng "Lưu ý: <cảnh báo>" (không chặn).

**Bàn phím**: ô Cấp phát sinh, Nhân k nằm trong thứ tự Tab của hàng; Space bật/tắt Nhân k; ô số xét nghiệm mỗi ống đứng trước lưới trong thứ tự Tab. Ô vô hiệu vẫn nhận focus để đọc tooltip (`aria-disabled="true"`, không `disabled`).

**Trạng thái** (bổ sung FEAT-012):
- Đang tải / rỗng / lỗi tải / không có quyền: như FEAT-012.
- Chỉ đọc (NC Auditor, vai trò chỉ đọc, bộ đã đóng): ô số xét nghiệm mỗi ống, Cấp phát sinh, Nhân k không viền; dải `warnings` vẫn hiện; nút "Xuất Excel" vẫn có. NC Auditor không có nút nào khác.
- Đã khóa / Đã thay thế: như FEAT-012; "Sao chép sang hệ thống khác" vẫn có (tạo bộ mới, không sửa bộ này) cho người có `copy_norm_set`.

**API theo hành động**: mở → `get_norm_set`; sửa dòng → `save_line`; số xét nghiệm mỗi ống → `save_head`; xác nhận → `confirm_line`, `confirm_set`; sao chép → `copy_norm_set`; xuất → `export_norm_set`; khởi tạo → `create_options`, `create_norm_set`. Trình duyệt không ghi thẳng DocType (ADR-010).

**Kiểm**: 1366 × 768 — đầu trang không xuống quá hai dòng (nút thừa vào menu "…"), lưới thêm 2 cột vẫn cuộn ngang trong khung, cột Mã dòng và Nguồn lực cố định trái; tương phản dải vàng/đỏ dùng biến Desk; mọi chuỗi mới trong `vi.csv`; test tĩnh `test_norm_grid_ui.py` (FEAT-012) vẫn xanh và thêm kiểm: chỉ gọi `normcore.api.norm.*`, có `role="alert"` cho lỗi hộp thoại, không mã màu cứng.
