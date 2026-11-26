# FEAT-037: Thiết kế giao diện

## Căn cứ
- `ux-foundations.md`: SCR-DSK-024 **[1.1]** (liên kết SCR-DSK-038; điều kiện khóa gồm vật chất), SCR-DSK-038 (R; hai bảng), SCR-DSK-039 (R; chạy theo phạm vi; "Không thiếu gì"), SCR-DSK-040 (P nhẹ; ba ô giả định; gốc và thử cạnh nhau; "Giả định không hợp lệ"; nhãn "Kết quả thử, không lưu"); luồng `w6 --> w8` (Bảng đối soát → Đối soát vật chất).
- `design.md`: mục 3 (màu trạng thái, Bản ghi chỉ đọc), mục 5 (số `1.234.567`, số lẻ `18.185,56`, tiền ` đ`, phần trăm `−3,27%`), "Kết quả thử [1.1]" (dải cố định, cột thử nền nhấn nhẹ).
- `architecture.md` ADR-010 [1.1]: trang `sensitivity` chỉ đọc qua API whitelisted, không ghi dữ liệu.
- API: `technical-design.md` mục 3.

## Chiến lược hiện thực
| Màn hình | Loại hiện thực | Vị trí |
| :-- | :-- | :-- |
| SCR-DSK-038 Đối soát vật chất và sản lượng | Script Report chuẩn "NC Physical Reconciliation" (nhãn "Đối soát vật chất và sản lượng"); hai bảng vẽ bằng bộ lọc "Bảng" (Vật chất / Sản lượng) của một report | `nc_costing/report/nc_physical_reconciliation/` |
| SCR-DSK-039 Báo cáo thiếu dữ liệu | Script Report chuẩn "NC Missing Data" (nhãn "Báo cáo thiếu dữ liệu") | `nc_costing/report/nc_missing_data/` |
| SCR-DSK-040 Phân tích độ nhạy | Desk Page `sensitivity` + Vue nhẹ (cùng cách `norm_grid`) | `nc_costing/page/sensitivity/`, `public/js/sensitivity/` |
| SCR-DSK-024 [1.1] | Bổ sung report "NC Reconciliation" (FEAT-017) | `nc_costing/report/nc_reconciliation/` |
| SCR-DSK-022, SCR-DSK-023 | Bổ sung nút, dải vào form NC Costing Run, NC Service Cost | `nc_costing_run.js`, `nc_service_cost.js` |

## Quy ước chung
- Màu chỉ báo như FEAT-017: "Vượt ngưỡng · cần giải trình", "Chưa đối soát · cần giải trình" `red`; "đã giải trình" `green`; "Trong ngưỡng" `gray`; cảnh báo sản lượng `yellow`. Nhãn màu luôn có chữ.
- Chuỗi qua `__()` (JS), `_()` (Python); bản dịch ở `normcore/translations/vi.d/37-feat-037.csv`.
- Lượng: 2 số lẻ, căn phải, font đơn cách, kèm đơn vị định mức của mặt hàng (`norm_uom`, ví dụ "18.185,56 test"). Phần trăm 2 số lẻ có dấu. Trống hiện "—" kèm tooltip lý do (`note` của dòng).
- Mọi dải chặn khóa có `role="alert"`.

## SCR-DSK-038 Đối soát vật chất và sản lượng (Script Report)

**Quyền vào.** `roles`: NC Finance, NC Director, NC Admin, NC Auditor; `ref_doctype` NC Reconciliation Line. Dữ liệu từ `get_physical_reconciliation(run)`.

**Bộ lọc:**
- `costing_run` Link NC Costing Run, bắt buộc; mặc định từ `frappe.route_options`.
- `table` Select "Vật chất" / "Sản lượng", mặc định "Vật chất".
- `department` Link NC Department.
- `only_attention` Check "Chỉ dòng cần chú ý" (vượt ngưỡng, chưa đối soát, cảnh báo).

**Dải đầu** (trên bảng, theo thứ tự):
1. Tóm tắt: "Lần tính TG-2026-001 · Đã tính · Ngưỡng vật chất 5% · Ngưỡng sản lượng 2%".
2. `available` = 0: dải `--text-muted` "Đối soát vật chất và sản lượng chỉ lập cho kịch bản Thực tế 12 tháng. Lần tính này dùng kịch bản {scenario}." Bảng rỗng.
3. `blocked` > 0: dải `red`, `role="alert"`: "Còn {n} dòng vượt ngưỡng hoặc chưa đối soát chưa có giải trình. Lần tính chưa khóa được."
4. Có khoa "Chưa đối soát" (`unreconciled` > 0): dải `red` (hoặc `green` khi đã giải trình hết) "Chưa đối soát vật chất: {khoa, …} — chưa có số liệu xuất kho năm {y}. NC Finance xác nhận kèm lý do để khóa."
5. Bảng Sản lượng có cảnh báo: dải `yellow` "{n} dịch vụ lệch sản lượng quá ngưỡng. Chỉ cảnh báo, không chặn khóa."
6. Ghi chú nhỏ dưới bảng Vật chất: "Lượng tính được = định mức × k × số kết quả (và các dòng theo ống, mẻ, ngày, kỳ, nội kiểm). Xuất kho đổi về đơn vị định mức."

**Cột — bảng Vật chất** (tổng rộng ≤ 1300 px):

| Cột | Nguồn | Định dạng |
| :-- | :-- | :-- |
| Khoa | `department` · `department_name` | "XN · Khoa Xét nghiệm" |
| Mặt hàng | `item` · `item_name` | dòng khoa chưa đối soát: "— (cả khoa)" |
| Lượng tính được | `calculated_qty` | lượng + `norm_uom` |
| Xuất kho thực tế | `actual_qty` | lượng + `norm_uom`; trống "—" |
| Chênh lệch | `diff_qty` | lượng có dấu |
| Chênh lệch % | `variance_pct` | `3,27%`; trống "—" |
| Tình trạng | `recon_status`, `over_tolerance`, `needs_explanation` | "Trong ngưỡng" `gray`; "Vượt ngưỡng · cần giải trình" `red`; "Vượt ngưỡng · đã giải trình" `green`; "Chưa đối soát · cần giải trình" `red`; "Chưa đối soát · đã xác nhận" `green` |
| Giải trình | `explanation` | cắt 60 ký tự, đủ ở tooltip |
| (hành động) | | "Giải trình" / "Sửa giải trình" khi `can_explain` |

**Cột — bảng Sản lượng:** Dịch vụ (`technical_service` · `service_name`), Khoa, Số kết quả trả (`calculated_qty`, số nguyên `16.000`), Sản lượng HIS (`actual_qty`; trống "—" tooltip "Thiếu sản lượng HIS"), Chênh lệch, Chênh lệch %, Tình trạng ("Trong ngưỡng" `gray` / "Cảnh báo lệch sản lượng" `yellow`), Ghi chú (`explanation`), nút "Ghi chú" (không bắt buộc) khi `can_explain`.

**Hành động:**
- Hộp thoại "Giải trình: XN · HC_GLU" (hoặc "Xác nhận chưa đối soát: XN"): phần chỉ đọc lượng tính, xuất kho, %; trường `explanation` Small Text, bắt buộc với dòng chặn (nhãn "Lý do" ở dòng Chưa đối soát); chỉ khoảng trắng → "Nhập nội dung giải trình"; "Lưu" gọi `save_explanation`; thành công `show_alert` "Đã lưu giải trình" `green`, tải lại; lỗi máy chủ `msgprint` nguyên văn; Esc đóng; Ctrl+S lưu.
- Nút trang "Khóa lần tính" (`btn-primary`) khi `can_lock`; khi `blocked` > 0 hiện nhưng vô hiệu, tooltip "Còn {n} dòng cần giải trình". Xác nhận rồi gọi `lock_run`, như SCR-DSK-024.
- Nút "Bảng đối soát tài chính" (`btn-default`) mở SCR-DSK-024 cùng lần tính; "Mở lần tính" mở form.

**Trạng thái:** chưa chọn lần tính ("Chọn một lần tính giá để xem đối soát vật chất và sản lượng."); đang tải (khung chuẩn); lần tính chưa có kết quả ("Lần tính chưa có kết quả đối soát. Chạy tính giá trước."); không có dòng ("Lần tính không có dịch vụ cận lâm sàng để đối soát."); Đã khóa (dải "Bản ghi đã Đã khóa, không sửa được.", không nút sửa, khóa); NC Director, NC Admin, NC Auditor xem đủ, không nút sửa, khóa; vai trò khác: trang lỗi quyền chuẩn, API PermissionError; lỗi máy chủ `msgprint` nguyên văn.

## SCR-DSK-024 Bảng đối soát — phần [1.1] (sửa report FEAT-017)
- Bảng chỉ dòng Tài chính (API lọc).
- Dải mới dưới tóm tắt (`--text-muted` hoặc `red` khi có dòng vật chất chặn, `role="alert"` khi chặn): "Đối soát vật chất: {material_blocked} dòng vượt ngưỡng, {unreconciled} khoa chưa đối soát cần giải trình · Sản lượng: {volume_warnings} cảnh báo" + nút liên kết "Mở đối soát vật chất và sản lượng" (route sang SCR-DSK-038 cùng `costing_run`). `available` = 0 thì chỉ ghi "Không lập đối soát vật chất (kịch bản {scenario})."
- Dải chặn khóa đổi thành "Còn {n} dòng đối soát (tài chính và vật chất) chưa có giải trình. Lần tính chưa khóa được."; `can_lock` theo `blocked` mới.

## SCR-DSK-022 Lần tính giá (bổ sung form)
- Nút "Đối soát vật chất và sản lượng" (`btn-default`, cạnh "Bảng đối soát", khi Đã tính hoặc Đã khóa) mở SCR-DSK-038.
- Nút "Báo cáo thiếu dữ liệu" (`btn-default`, mọi trạng thái, cả Nháp) mở SCR-DSK-039 với bộ lọc lấy từ lần tính (năm, ngày tính, bộ tham số, loại giá, kịch bản, phạm vi).
- Dải `red`, `role="alert"` khi `physical_unreconciled` > 0: "Chưa đối soát vật chất: {n} khoa chưa có số liệu xuất kho. Cần NC Finance xác nhận kèm lý do trước khi khóa." kèm liên kết mở SCR-DSK-038.
- Nút "Khóa": thông báo chặn dùng `recon_blocked` mới, liên kết tới bảng tương ứng (tài chính hoặc vật chất).

## SCR-DSK-039 Báo cáo thiếu dữ liệu (Script Report)

**Quyền vào.** `roles`: NC Finance, NC Director, NC Admin, NC Auditor, NC Department Head; `ref_doctype` NC Costing Run. NC Department Head: bộ lọc `departments` mặc định và bị ép về khoa được phân (máy chủ lọc lại).

**Bộ lọc:** `fiscal_year` (Int, bắt buộc, mặc định năm hiện tại), `costing_date` (Date, bắt buộc, mặc định hôm nay), `parameter_set` (Link, bắt buộc, mặc định bộ có `effective_from` gần nhất ≤ ngày tính), `price_category` (Link, bắt buộc), `volume_scenario` (Select, mặc định "Thực tế 12 tháng"), `departments` (MultiSelectList NC Department), `services` (MultiSelectList NC Technical Service), `kind` (Select năm loại, trống = tất cả). Khi mở từ SCR-DSK-022 lấy từ `route_options`.

**Cột:** Dịch vụ (mã · tên, liên kết NC Technical Service), Khoa, Loại thiếu (nhãn `yellow` có chữ), Chi tiết (`detail`, ví dụ "L02 · Hóa chất GLU", "Hệ thống GLU-B", "Thiết bị EQ_A · Hồ sơ kiểm định"), Mở (liên kết sửa: NC Item Price, NC Service Volume, NC Test System Volume, NC Time Study, NC QC Plan, NC Equipment Compliance theo loại; chỉ hiện khi người dùng có quyền tạo DocType đó). Nhóm theo dịch vụ (cột Dịch vụ gộp như `group_by` chuẩn của report); sắp dịch vụ, khoa, loại.

**Dải đầu:**
- Tóm tắt: "{n} dịch vụ thiếu dữ liệu trong {m} dịch vụ của phạm vi · Thiếu đơn giá {a} · Thiếu sản lượng {b} · Thiếu bấm giờ {c} · Thiếu kế hoạch chất lượng {d} · Thiếu hồ sơ tuân thủ {e}".
- Có cặp chưa có bộ định mức "Đã khóa": dải `--text-muted` "{k} dịch vụ chưa có bộ định mức Đã khóa, không kiểm được dữ liệu." kèm danh sách mở rộng.

**Trạng thái:** thiếu bộ lọc bắt buộc → thông báo chuẩn của report; đang chạy (khung chuẩn); **không thiếu gì**: dải `green` "Không thiếu gì. Mọi dịch vụ trong phạm vi đủ dữ liệu để tính giá." và bảng rỗng; không có dịch vụ trong phạm vi: "Phạm vi không có dịch vụ nào."; vai trò khác: lỗi quyền chuẩn; lỗi máy chủ `msgprint` nguyên văn. Báo cáo chỉ đọc, không có nút ghi.

## SCR-DSK-040 Phân tích độ nhạy (Page `sensitivity`)

**Lối vào:** nút "Phân tích độ nhạy" (`btn-default`) trên form NC Service Cost (SCR-DSK-023) khi lần tính Đã tính hoặc Đã khóa → `/app/sensitivity?service_cost=<name>`. Thiếu tham số: ô chọn "Kết quả tính giá" (Link NC Service Cost) ở đầu trang. Page `roles`: NC Finance, NC Director, NC Admin, NC Auditor, NC Department Head; API kiểm từng dịch vụ.

**Bố cục** (một cột, rộng ≤ 1300 px, vừa 1366 × 768 không cuộn ngang):
1. **Dải cố định** ở đầu trang (`position: sticky`, nền `--alert-bg-info` hoặc tương đương của Desk), chữ đậm: "Kết quả thử, không lưu" + câu nhỏ "Thay đổi ở đây không ghi vào lần tính giá." (design.md).
2. **Tiêu đề:** "GLU · Glucose — Khoa XN · Lần tính TG-2026-001 (Đã khóa)", liên kết về bảng giải trình.
3. **Khối giả định** (ba nhóm, mỗi nhóm có nhãn):
   - **Sản lượng:** dịch vụ cận lâm sàng — bảng nhỏ mỗi hệ thống một dòng: Hệ thống, Qbn gốc (chỉ đọc), ô "Qbn giả định" (Float). Dịch vụ thường — một ô "Sản lượng giả định".
   - **Đơn giá:** danh sách mặt hàng của dịch vụ: Mặt hàng, Đơn vị mua, Giá gốc một đơn vị mua (chỉ đọc), ô "Giá giả định" (Currency). Ô tìm nhanh khi > 10 mặt hàng.
   - **Hình thức có máy:** mỗi thiết bị: Thiết bị, Hình thức gốc, ô Select (Mua / Thuê / Đặt theo hóa chất / Liên doanh, liên kết), ô "Chi phí năm theo hợp đồng" (hiện khi Thuê hoặc Liên doanh, liên kết; bắt buộc).
   - Ô trống = giữ giá trị gốc. Nút "Tính thử" (`btn-primary`, Ctrl+Enter), "Đặt lại" (`btn-default`, xóa mọi giả định).
4. **Bảng so sánh** (hai cột số cạnh nhau, cột "Thử" nền nhấn nhẹ `--highlight-color`/`--bg-light-gray` theo design.md): dòng Chi phí trực tiếp theo cấu phần (Nhân công, Thuốc, Vật tư, Thiết bị, Hạ tầng, Tiện ích), Phân bổ, **Giá thành toàn bộ**, Giá tính toán, Giá làm tròn; cột Gốc, Thử, Chênh lệch (tiền có dấu), Chênh lệch %.
5. **Theo hệ thống** (dịch vụ cận lâm sàng): Hệ thống, k gốc, k thử (6 số lẻ), chi phí trực tiếp một kết quả gốc / thử.
6. **Cảnh báo** (`yellow`) từ `warnings` (ví dụ "Dữ liệu đầu vào đã đổi sau lần tính; so sánh có thể lệch").

**API:** mở trang → `get_sensitivity_base(service_cost)` (điền gốc, danh sách hệ thống, mặt hàng, thiết bị); "Tính thử" → `run_sensitivity(service_cost, overrides)` chỉ gửi ô có giá trị. Không gọi API nào khác; không có nút lưu.

**Trạng thái:**
- Đang tải: khung xám; "Tính thử" hiện spinner, khóa nút đến khi có kết quả.
- Chưa tính thử: cột Thử "—", chữ nhỏ "Nhập giả định rồi bấm Tính thử."
- **Giả định không hợp lệ:** kiểm phía máy khách (số ≤ 0 ở sản lượng, giá âm, thiếu chi phí hợp đồng) → viền lỗi ô và chữ dưới ô, không gọi API; lỗi máy chủ (`ValidationError`) → dải `red`, `role="alert"`, nội dung nguyên văn (ví dụ "Sản lượng giả định phải lớn hơn 0"); kết quả cũ bị xóa khỏi cột Thử.
- Kết quả thử "Lỗi" (dịch vụ không tính được với giả định): cột Thử "—", dải `red` với `calc_message`.
- Lần tính chưa có kết quả: "Lần tính chưa có kết quả" và không có khối giả định.
- Không có quyền (ngoài khoa, vai trò khác): thông báo lỗi quyền chuẩn, không hiện số.
- NC Auditor, NC Director, NC Admin: dùng đủ (trang không ghi gì nên không có chế độ chỉ đọc riêng).

## Kiểm
- **1366 × 768:** SCR-DSK-038 tới 10 cột không cuộn ngang; SCR-DSK-040 khối giả định và bảng so sánh nhìn thấy trong hai màn hình cuộn dọc; hộp thoại giải trình vừa màn hình.
- **Bàn phím:** Tab qua bộ lọc, ô giả định, nút; Enter trong ô giả định không gửi form; Ctrl+Enter = Tính thử; Ctrl+S trong hộp thoại = Lưu; Esc đóng.
- **Tương phản ≥ 4,5:1** (NFR-USE-004): chỉ biến màu của Desk, không mã màu hex; nhãn trạng thái luôn có chữ.
- **Chuỗi tiếng Việt** qua `__()`/`_()`, có trong `vi.d/37-feat-037.csv`; số theo NFR-LOC-001 (`format_number`/`format_currency` của Desk với locale vi).
- Test tĩnh: `tests/unit/test_physical_reconciliation_ui.py` (hai report và phần sửa `nc_reconciliation.js`, `nc_costing_run.js`) và `tests/unit/test_sensitivity_ui.py` (trang): chỉ gọi `normcore.api.costing.*` được phép, chuỗi có bản dịch, `role="alert"` ở dải chặn và dải lỗi, dải "Kết quả thử, không lưu" có trong trang, không mã hex, `roles` của report/page đúng `technical-design.md` mục 2.2.
