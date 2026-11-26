# FEAT-018: Thiết kế giao diện

## Căn cứ
- `ux-foundations.md`: SCR-DSK-022 Lần tính giá (loại F; trạng thái "đã khóa"); vai trò NC Finance "so sánh"; Luồng 2 (Xác nhận, Khóa).
- `design.md`: mục 3 (màu trạng thái, bản ghi chỉ đọc), mục 5 (số `1.234.567`, tiền thêm ` đ`, số âm `−63.636,36`, phần trăm `−22,12%`); nguyên tắc "Dùng form, list, report chuẩn khi đủ dùng".
- API: `technical-design.md` mục 5. Giả định: ASM-018-07..10.

## Chiến lược hiện thực
- SCR-DSK-022: thêm nút, dải thông báo, section "Ảnh chụp đầu vào" vào form của FEAT-015/017 (`nc_costing_run.js`). Không làm trang Vue.
- So sánh hai lần tính: **Script Report chuẩn** "So sánh hai lần tính giá" (`nc_costing/report/nc_costing_run_comparison/`, ASM-018-09), mở từ SCR-DSK-022. Không phải SCR-DSK-026 (bàn so sánh giá tham chiếu).
- Chuỗi nguồn tiếng Anh qua `__()` / `_()` như form hiện có; bản dịch tiếng Việt ở `normcore/translations/vi.d/FEAT-018.csv`.

## Quy ước chung
- Màu chỉ báo giữ như FEAT-015/017: "Đã khóa" `green`; khác biệt / lỗi `red`; cảnh báo `yellow`; không đổi `gray`. Nhãn màu luôn có chữ.
- Số âm dùng dấu trừ "−" và định dạng tiền của Desk (`format_currency` / `frappe.format` theo trường Currency); chênh lệch dương có dấu "+".
- Mã băm hiện 12 ký tự đầu, kiểu `monospace`, có `title` là đủ 64 ký tự; nút sao chép chuẩn của Desk.

## SCR-DSK-022 Lần tính giá (bổ sung)

### Bố cục
- Section mới **"Ảnh chụp đầu vào"** (cuối form, sau "Cảnh báo phân bổ"), chỉ hiện khi có `snapshot_file`: hai cột — trái `snapshot_file` (liên kết tải tệp `.json.gz`, private), phải `snapshot_hash` (chỉ đọc). Mô tả dưới section: "Toàn bộ đầu vào đã dùng khi khóa. Dùng 'Kiểm tra tái lập' để tính lại từ ảnh chụp."
- Dải đầu trang khi "Đã khóa" (thay câu FEAT-015): `green` "Đã khóa · ảnh chụp {12 ký tự}. Không tính lại, không sửa được; dùng Nhân bản để tạo lần tính mới."
- Dải khi "Đã tính" giữ: "Muốn đổi đầu vào, hãy nhân bản lần tính giá." — nay có nút "Nhân bản" thật.

### Nút (theo trạng thái và quyền)

| Nút | Hiện khi | Kiểu | Hành động / API |
| :-- | :-- | :-- | :-- |
| Chạy tính giá (có) | Nháp, Tính lỗi, Đã tính; quyền write | như FEAT-017 | ẩn ở "Đã khóa" |
| Khóa (có) | Đã tính; quyền write | `btn-primary` | như FEAT-017, rồi `lock_run`. Hộp xác nhận thêm câu: "Hệ thống sẽ tính lại từ dữ liệu hiện tại để kiểm, rồi lưu ảnh chụp đầu vào." Trong lúc chờ: `freeze` "Đang lưu ảnh chụp đầu vào…". Thành công: alert xanh "Đã khóa, mã băm {12 ký tự}", `reload_doc`. Bị từ chối vì đầu vào đã đổi: `msgprint` đỏ tiêu đề "Không khóa được", nội dung câu lỗi máy chủ (giữ nguyên văn) và nút "Chạy tính giá lại" (gọi luồng `ask_to_run` có sẵn) |
| Nhân bản | mọi trạng thái trừ "Đang tính"; `can_duplicate` (quyền create) | `btn-primary` khi "Đã khóa", còn lại `btn-default` trong nhóm "Hành động" | `frappe.confirm("Tạo lần tính giá mới ở trạng thái Nháp với cùng đầu vào và phạm vi? Kết quả, đối soát và ảnh chụp không được chép.")` → `duplicate_run` → alert "Đã tạo {name}" → `frappe.set_route("Form", "NC Costing Run", name)` |
| Kiểm tra tái lập | "Đã khóa" và có `snapshot_file` (mọi vai trò đọc được, gồm NC Auditor) | `btn-default` | `verify_snapshot`, `freeze` "Đang tính lại từ ảnh chụp…". `ok`: `msgprint` tiêu đề "Tái lập trùng khớp", indicator `green`: "Tính lại từ ảnh chụp (lược đồ {version}) trùng kết quả đã khóa ở mọi trường: {services} dịch vụ, {lines} dòng giải trình, {recon_lines} dòng đối soát." Không `ok`: indicator `red`, tiêu đề "Tái lập không khớp", `role="alert"`, danh sách ≤ 50 câu `diffs` (cuộn trong hộp, `max-height` 50vh) và dòng "Tổng {diff_count} khác biệt" |
| So sánh với lần tính khác | "Đã tính" hoặc "Đã khóa" | `btn-default` | Hộp thoại một trường Link "Lần tính để so sánh" (NC Costing Run, `get_query` lọc `status in ("Đã tính","Đã khóa")`, `name != frm.doc.name`, sắp `modified desc`), nút chính "So sánh" → `frappe.set_route("query-report", "NC Costing Run Comparison", {base_run: frm.doc.name, other_run: chọn})`. Lần đang mở là **lần gốc** |

- Ở "Đã khóa" mọi trường form chỉ đọc (Desk tự khóa khi `validate` từ chối; JS đặt `frm.disable_form()` để không cho gõ rồi mới báo lỗi). Bảng phạm vi không thêm/bớt được.
- NC Auditor, NC Director: thấy "Kiểm tra tái lập", "So sánh với lần tính khác", tải tệp ảnh chụp; không thấy "Khóa", "Nhân bản", "Chạy tính giá".

### Trạng thái
- **Đang tải:** dải kết quả có sẵn ("Đang tải kết quả…").
- **Lỗi máy chủ / không có quyền:** câu lỗi của máy chủ qua `msgprint` chuẩn; nút không hiện khi không có quyền (`can_duplicate`, `frm.perm[0].write`).
- **Đã khóa không có ảnh chụp** (bản ghi cũ trước FEAT-018): section ảnh chụp ẩn, nút "Kiểm tra tái lập" ẩn; dải đầu trang dùng câu "Đã khóa (không có ảnh chụp đầu vào)" `green`.

## Report "So sánh hai lần tính giá" (NC Costing Run Comparison)

### Bộ lọc (thứ tự)
1. `base_run` "Lần gốc" — Link NC Costing Run, bắt buộc.
2. `other_run` "Lần so sánh" — Link NC Costing Run, bắt buộc.
3. `only_changed` "Chỉ dịch vụ có chênh lệch" — Check, mặc định 1.
4. `technical_service` "Dịch vụ" — Link NC Technical Service, tùy chọn.

Thiếu một trong hai lần tính: report hiện thông điệp rỗng "Chọn hai lần tính giá để so sánh."

### Đầu report
- `message` (HTML, trên bảng): "Lần gốc {base} ({status}) · Lần so sánh {other} ({status}). Chênh lệch = lần so sánh − lần gốc." Nếu `input_changes` có dòng: khối `alert-info` "Đầu vào khác nhau" liệt kê `nhãn: gốc → so sánh` (ví dụ "Loại giá: Giá dịch vụ → Giá không kết cấu khấu hao").
- `report_summary` (thẻ chuẩn): "Số dịch vụ", "Có chênh lệch", "Chỉ ở lần gốc", "Chỉ ở lần so sánh", "Tổng chênh lệch giá thành" (indicator `red` khi ≠ 0, `green` khi 0; chữ luôn kèm số).

### Bảng (cây, `tree: true`, `parent_field`, `initial_depth: 0`)

| Cột | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| `label` | Dịch vụ / cấu phần | Data, rộng 280 | Dòng dịch vụ (`indent` 0): "{mã} — {tên} · {khoa}". Dòng cấu phần (`indent` 1): "Trực tiếp · Thiết bị", "Phân bổ · Khấu hao", "Giá · Giá làm tròn"… theo thứ tự `compare.COMPONENTS` |
| `base_value` | Lần gốc | Currency | dòng dịch vụ = giá thành toàn bộ |
| `other_value` | Lần so sánh | Currency | |
| `diff` | Chênh lệch | Currency | dấu "+"/"−"; trống khi không tính được |
| `diff_pct` | Chênh lệch % | Percent | trống khi gốc = 0 |
| `note` | Ghi chú | Data | "Chỉ ở lần gốc", "Chỉ ở lần so sánh", "Lỗi ở lần gốc/so sánh: {câu}", "Trạng thái: A → B" |

- Dòng dịch vụ mặc định đóng; mở để thấy cấu phần. Với `only_changed` = 1, dòng cấu phần có `diff` = 0 vẫn hiện khi mở (đủ 15–16 dòng, để tổng khớp), dòng dịch vụ không đổi bị ẩn.
- `formatter` JS: `diff` âm/dương in đậm, nhãn chữ `indicator-pill` `red` "Khác" ở cột Ghi chú khi dòng dịch vụ có chênh lệch; không mã màu hex.
- Nút "Mở bảng giải trình" trên dòng dịch vụ (cột `label` là liên kết tới NC Service Cost của lần so sánh nếu có, không thì của lần gốc).
- Xuất Excel/CSV, in: chuẩn của Desk.

### Trạng thái
- **Không có quyền** với một trong hai lần tính: lỗi máy chủ chuẩn "Không đủ quyền" (PermissionError).
- **Lần tính chưa có kết quả** / **chọn trùng**: thông điệp lỗi của API (technical-design mục 5) hiện ở `msgprint`.
- **Không có chênh lệch nào:** bảng rỗng, thông điệp "Hai lần tính giá cho cùng kết quả ở mọi dịch vụ."
- Quyền report: NC Finance, NC Director, NC Admin, NC Auditor (chỉ đọc; report không có thao tác ghi).

## Kiểm
- **1366 × 768:** form không cuộn ngang; report 6 cột vừa màn hình khi đóng các dòng; hộp thoại kiểm tra tái lập cuộn trong hộp.
- **Bàn phím:** Tab qua nút và bộ lọc; Enter chọn trong Link; Ctrl+Enter / nút chính trong hộp thoại "So sánh"; Esc đóng hộp thoại; mũi tên mở/đóng dòng cây của report (chuẩn DataTable).
- **Tương phản ≥ 4,5:1** (NFR-USE-004): chỉ dùng biến màu và `indicator` của Desk.
- **Test tĩnh mới `tests/unit/test_costing_lock_ui.py`:**
  - JS của form và report chỉ gọi `normcore.api.costing.*` (`verify_snapshot`, `duplicate_run`, `compare_runs`, `lock_run`);
  - mọi chuỗi qua `__()` / `_()` và có trong `vi.d/FEAT-018.csv` hoặc tệp dịch đã có;
  - có `role="alert"` ở hộp "Tái lập không khớp";
  - không mã màu hex;
  - report JSON có `roles` đúng 4 vai trò; `ref_doctype` NC Costing Run;
  - `nc_costing_run.json` có `snapshot_file`, `snapshot_hash` `read_only` và `no_copy`.
