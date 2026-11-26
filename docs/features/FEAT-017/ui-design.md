# FEAT-017: Thiết kế giao diện

## Căn cứ
- `ux-foundations.md`: SCR-DSK-024 Bảng đối soát (loại R), Luồng 2 (SCR-DSK-022 → SCR-DSK-024, "Xác nhận, Khóa"). SCR-DSK-022 phần "khóa".
- `design.md`: mục 3 (màu trạng thái, Bản ghi chỉ đọc), mục 4, mục 5 (số `1.234.567`, tiền thêm ` đ`, phần trăm `−28,08%`); nguyên tắc "Dùng form, list, report chuẩn khi đủ dùng".
- API: `technical-design.md` mục 5.

## Chiến lược hiện thực
- SCR-DSK-024 là **Script Report chuẩn của Desk** (`nc_costing/report/nc_reconciliation/`, tên "Bảng đối soát"), không làm trang Vue.
- Giải trình ghi qua hộp thoại của report, gọi `save_explanation`.
- SCR-DSK-022 chỉ thêm nút và dải thông báo vào form FEAT-015.
- Phần **[1.1]** của SCR-DSK-024 (liên kết SCR-DSK-038, điều kiện khóa vật chất) **không** làm ở đây; thuộc FEAT-037.

## Quy ước chung
- Màu chỉ báo giữ như FEAT-015. Vượt ngưỡng dùng `red`; đã giải trình dùng `green`; theo dõi (không vượt) dùng `gray`; cảnh báo dùng `yellow`. Nhãn màu luôn có chữ.
- Chuỗi qua `__()` (JS), `_()` (Python); bản dịch ở `vi.csv`.
- Mã loại chi phí hiện kèm nhãn: Nhân công (LABOR), Thuốc và vật tư (DRUG_SUPPLY), Khấu hao (DEPRECIATION), Tiện ích (UTILITY).

## SCR-DSK-024 Bảng đối soát (Script Report "Bảng đối soát")

**Quyền vào.** Report `roles`: NC Finance, NC Director, NC Admin, NC Auditor. `ref_doctype` = NC Reconciliation Line. Dữ liệu lấy từ `get_reconciliation(run)`; hàm này kiểm quyền đọc NC Costing Run.

**Bộ lọc** (hàng đầu):
- `costing_run`: Link NC Costing Run, bắt buộc. Mặc định lấy từ `frappe.route_options` khi mở từ SCR-DSK-022.
- `cost_center`: Link NC Cost Center, không bắt buộc.
- `only_over`: Check "Chỉ dòng vượt ngưỡng".

**Dải đầu** (vẽ ở `onload`/`after_datatable_render` bằng `report.page.add_inner_message` hoặc khối HTML trên bảng):
1. Dòng tóm tắt, ví dụ "Lần tính TG-2026-001 · Đã tính · Ngưỡng đối soát 10%". Indicator trạng thái theo màu FEAT-015.
2. Khi `blocked` > 0: dải `red` có `role="alert"`, "Còn {n} dòng vượt ngưỡng chưa có giải trình. Lần tính chưa khóa được."
3. Khi `blocked` = 0 và có dòng vượt ngưỡng: dải `green`, "Mọi dòng vượt ngưỡng đã có giải trình."
4. `warnings` không rỗng: dải `yellow`, tiêu đề "Cảnh báo phân bổ", mỗi cảnh báo một dòng (tối đa 5, thêm "Xem tất cả" để mở rộng).
5. `partial_scope`: dải `--text-muted`, "Phạm vi một phần: phần còn lại của trung tâm chỉ chia cho dịch vụ trong phạm vi lần tính." (ASM-017-03)
6. `include_depreciation` = 0: dải `--text-muted`, "Loại giá không kết cấu khấu hao: không phân bổ và không đối soát khấu hao." (BR-COST-016)
7. Ghi chú cố định nhỏ dưới bảng: "Nhân công, khấu hao, tiện ích: số đã tính thấp hơn số kế toán là bình thường (phần gián tiếp được phân bổ cấp 2). Loại quản lý không đối soát." (BR-COST-015)

**Cột** (số căn phải, font đơn cách; rộng tổng ≤ 1300 px):

| Cột | Nguồn | Định dạng |
| :-- | :-- | :-- |
| Trung tâm chi phí | `cost_center` + `cost_center_name` | "K01 · Khoa K01" |
| Loại chi phí | `category_label` | |
| Số đã tính | `costed_amount` | tiền |
| Số kế toán (gồm cấp 1) | `accounting_amount` | tiền |
| Chênh lệch | `variance` | tiền, có dấu |
| Chênh lệch % | `variance_pct` | `−28,08%`; trống hiện "—" và tooltip "Số kế toán bằng 0" |
| Phần còn lại | `remainder` | tiền |
| Tình trạng | `over_tolerance`, `needs_explanation` | nhãn: "Vượt ngưỡng · cần giải trình" `red`; "Vượt ngưỡng · đã giải trình" `green`; "Theo dõi" `gray` |
| Giải trình | `explanation` | cắt 60 ký tự, đủ nội dung ở tooltip |
| (hành động) | | nút nhỏ "Giải trình" / "Sửa giải trình" khi `can_explain` và dòng vượt ngưỡng; dòng không vượt ngưỡng vẫn có "Ghi chú" (không bắt buộc) |

Sắp theo trung tâm rồi loại (thứ tự API trả). Không có dòng tổng.

**Hành động:**
- Nút "Giải trình" mở hộp thoại `frappe.ui.Dialog`:
  - tiêu đề "Giải trình: K01 · Thuốc và vật tư";
  - phần chỉ đọc: số đã tính, số kế toán, chênh lệch %;
  - trường `explanation` Small Text, bắt buộc khi dòng vượt ngưỡng; chỉ khoảng trắng thì báo "Nhập nội dung giải trình";
  - nút chính "Lưu" gọi `save_explanation(line, explanation)`. Thành công: `show_alert` "Đã lưu giải trình" (`green`), tải lại report. Lỗi máy chủ: `msgprint` nguyên văn;
  - Esc đóng hộp thoại.
- Nút trang "Khóa lần tính" (`btn-primary`, ở `report.page.set_primary_action`) chỉ hiện khi `can_lock`.
  - Bấm thì hiện hộp xác nhận "Khóa lần tính {run}? Sau khi khóa không tính lại và không sửa giải trình được." rồi gọi `lock_run(run)`.
  - Thành công: `show_alert` "Đã khóa" (`green`), tải lại.
  - Có `blocked` > 0 thì nút hiện nhưng bị vô hiệu, kèm tooltip "Còn {n} dòng cần giải trình".
- Nút "Mở lần tính" (`btn-default`) mở form NC Costing Run.
- Bấm vào tên trung tâm mở danh sách NC Service Cost lọc theo lần tính và các khoa của trung tâm.

**Trạng thái:**
- **Chưa chọn lần tính:** "Chọn một lần tính giá để xem bảng đối soát."
- **Đang tải:** khung xám chuẩn của report.
- **Lần tính chưa "Đã tính"/"Đã khóa"** (Nháp, Đang tính, Tính lỗi): bảng rỗng, "Lần tính chưa có kết quả đối soát. Chạy tính giá trước." Khi "Đang tính" thêm "Đang tính giá… n%".
- **Đã tính, không có dòng** (không trung tâm nào có số): "Không có dòng đối soát cho lần tính này."
- **Đã khóa:** dải theo design.md "Bản ghi đã Đã khóa, không sửa được."; không có nút Giải trình, Khóa.
- **NC Auditor, NC Director, NC Admin** (`can_explain` sai): xem đủ, không có nút sửa hay khóa.
- **Vai trò khác** (NC Clinician…): Desk từ chối mở report (trang lỗi quyền chuẩn); API trả PermissionError.
- **Lỗi máy chủ:** `frappe.msgprint` nguyên văn, mỗi lỗi một dòng.

**NC Reconciliation Line form và list** (đường vào phụ, ví dụ từ tìm kiếm):
- List: cột Lần tính, Trung tâm, Loại, Chênh lệch %, Vượt ngưỡng; bộ lọc chuẩn Lần tính, Trung tâm, Vượt ngưỡng. Không có nút "Thêm" vì `from_costing` chặn tạo tay: ẩn bằng `can_create` = false ở `listview_settings`, máy chủ vẫn chặn.
- Form: mọi trường chỉ đọc trừ `explanation` (chỉ đọc khi lần tính khác "Đã tính"). Thêm nút "Mở bảng đối soát".

## SCR-DSK-022 Lần tính giá (bổ sung vào form FEAT-015)

- **Nút "Bảng đối soát"** (`btn-default`, nhóm cạnh "Xem kết quả tính giá"; status "Đã tính" hoặc "Đã khóa") mở report "Bảng đối soát" với `costing_run` = tên lần tính. Khi `recon_blocked` > 0, nhãn nút có huy hiệu số dòng cần giải trình (chữ, không chỉ màu).
- **Nút "Khóa"** (`btn-primary`, khi status "Đã tính" và `frm.perm[0].write`):
  - còn dòng chặn (`recon_blocked` > 0) thì `msgprint` "Còn {n} dòng đối soát vượt ngưỡng chưa có giải trình" kèm liên kết "Mở bảng đối soát";
  - không còn thì hộp xác nhận như trên, rồi gọi `lock_run`.
  - Khi trạng thái "Đã tính" thì "Chạy tính giá" chuyển thành `btn-default`, để nút chính là "Khóa".
- **Dải "Cảnh báo phân bổ"** (`yellow`, `role="alert"`) dưới section Trạng thái khi `allocation_warnings` có nội dung, mỗi cảnh báo một dòng. Trường `allocation_warnings` ẩn khỏi bố cục form, chỉ hiện qua dải này.
- **Bảng kết quả:** dòng có `has_volume_warning` có nhãn `yellow` "Sản lượng 0" ở cột Kết quả, cạnh nhãn trạng thái. Lọc nhanh "Chỉ dịch vụ lỗi hoặc cảnh báo" gồm cả các dòng này. Dải tạm của FEAT-015 ("No shared allocation yet…") chỉ hiện khi **không dịch vụ nào** có dòng phân bổ.
- **Hộp xác nhận chạy lại** (status "Đã tính") thêm câu: "Dòng đối soát và giải trình hiện có sẽ bị thay." (ASM-017-08)
- **Đã khóa:** ẩn "Chạy tính giá", "Khóa"; giữ "Xem kết quả tính giá", "Bảng đối soát".

## SCR-DSK-023 Bảng giải trình (không đổi bố cục)
- Bảng phân bổ (đã có ở FEAT-015) nay có dòng thật. Cột "Số tiền phân bổ (pool)" có nhãn "Phần còn lại của trung tâm".
- Ghi chú `VOLUME_WARNING` hiện trong dải ghi chú khi có.

## Kiểm
- **1366 × 768:** report 4–10 dòng không cuộn ngang; hộp thoại giải trình vừa màn hình.
- **Bàn phím:** Tab qua bộ lọc, nút dòng, nút trang; Enter mở hộp thoại; Ctrl+S trong hộp thoại thì Lưu; Esc đóng.
- **Tương phản ≥ 4,5:1** (NFR-USE-004): chỉ dùng biến màu của Desk, không mã màu cứng.
- **Test tĩnh mới `tests/unit/test_reconciliation_ui.py`:**
  - JS của report và form chỉ gọi `normcore.api.costing.*`;
  - mọi chuỗi qua `__()` và có trong `vi.csv`;
  - có `role="alert"` ở dải chặn khóa và dải cảnh báo;
  - không mã màu hex;
  - report JSON có `roles` đúng 4 vai trò trên.
