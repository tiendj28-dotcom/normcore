# FEAT-019: Thiết kế giao diện

## Căn cứ
- `ux-foundations.md`: SCR-DSK-028 Xuất hồ sơ ("Hộp thoại từ phương án hoặc lần tính giá · Chọn loại tệp và xuất · Đang đóng gói; lỗi xuất"); điểm mở từ SCR-DSK-022 (lần tính giá), SCR-DSK-023 (bảng giải trình), bộ định mức (form NC Norm Set, lưới định mức).
- `design.md`: màu trạng thái (mục 3), định dạng số tiền `1.234.567` (mục 5), nguyên tắc "Dùng form, list, report chuẩn khi đủ dùng".
- API: `technical-design.md` mục 4. Giả định: ASM-019-02, 03, 04, 05, 12, 14.

## Chiến lược hiện thực
- SCR-DSK-028 là **một hộp thoại `frappe.ui.Dialog` dùng chung** trong `normcore/public/js/export_dialog.js`, gọi bằng `normcore.export.open({run})`, `normcore.export.open({service_cost})`, `normcore.export.open({norm_set, run?})`. Nạp toàn cục qua `normcore/hook_registry/FEAT-019.json` (`app_include_js`), không sửa `hooks.py`. **[AMD-019-02]** Khai báo bundle `"normcore_export.bundle.js"` (tệp `normcore/public/js/normcore_export.bundle.js` chỉ `import "./export_dialog.js";`), không khai URL cố định `/assets/normcore/js/export_dialog.js`: Frappe đổi sang `/assets/normcore/dist/js/normcore_export.bundle.<hash>.js`, URL đổi theo nội dung nên trình duyệt không dùng bản cũ trong cache. Không làm trang Vue.
- Nút mở hộp thoại thêm vào form có sẵn: `nc_costing_run.js` (FEAT-015/017/018), `nc_service_cost.js` (SCR-DSK-023), `nc_norm_set.js`.
- Chuỗi nguồn tiếng Anh qua `__()` như các form hiện có; bản dịch tiếng Việt ở `normcore/translations/vi.d/FEAT-019.csv` (nhãn dưới đây là bản tiếng Việt hiển thị). Nhãn loại tệp lấy từ `get_export_options` (máy chủ đã dịch bằng `_()`).
- Tải tệp: `open_url_post("/api/method/normcore.api.export.export_file", {file_type, run, service_cost, norm_set})` — trình duyệt tải trực tiếp, hộp thoại giữ mở để xuất tiếp.

## Điểm mở hộp thoại

| Nơi | Nút | Hiện khi | Gọi |
| :-- | :-- | :-- | :-- |
| Form NC Costing Run (SCR-DSK-022) | "Xuất hồ sơ" (`btn-default`, nhóm chính, cạnh "So sánh với lần tính khác") | `status == "Đã khóa"` (mọi vai trò đọc được, gồm NC Auditor) | `normcore.export.open({run: frm.doc.name})` |
| Form NC Costing Run | — | trạng thái khác | Không hiện nút. Dải "Đã tính" có sẵn không đổi |
| NC Service Cost (SCR-DSK-023) | "Xuất PDF giải trình" (`btn-default`) | lần tính cha "Đã khóa" (`run_status` của `get_explanation`) | `normcore.export.open({service_cost: frm.doc.name})` |
| Form NC Norm Set | "Xuất bộ định mức" (`btn-default`, nhóm "Xuất") | luôn (ai đọc được bộ) | `normcore.export.open({norm_set: frm.doc.name})` |

Lưới định mức (`NormGrid.vue`) **không đổi** (AMD-019-01): không có nút "Xuất PDF" ở lưới; nút "Xuất Excel" có sẵn giữ đường `api.norm.export_norm_set` của FEAT-034 (không có trang thông tin, không ghi nhật ký — giới hạn đã biết, DEF-019-01). Xuất bộ định mức có truy vết bằng hộp thoại từ form NC Norm Set.

## SCR-DSK-028 Xuất hồ sơ (hộp thoại)

### Bố cục (rộng `large`, vừa 1366 × 768, cuộn trong thân khi dài)
1. **Dòng nguồn** (HTML, chỉ đọc): "Lần tính giá **{run}** · Ngày tính {dd/mm/yyyy} · Bộ tham số {mã — tên} · Trạng thái `green` "Đã khóa"". Mở từ dịch vụ: thêm "Dịch vụ {mã — tên} · Khoa {khoa}". Mở từ bộ định mức không qua lần tính: "Bộ định mức **{name}** · Không gắn lần tính giá".
2. **Section "Biểu Thông tư 21"** (chỉ khi có `run`): bốn dòng, mỗi dòng: nhãn loại tệp, mô tả một câu, nút "Tải về" (`btn-default btn-xs`):
   - Phụ lục II — Phương án giá · "Mỗi dịch vụ một trang tính."
   - Phụ lục III — Giá thành theo yếu tố chi phí
   - Phụ lục IV — Giá thành theo phương pháp phân bổ
   - Phụ lục V — Danh mục dịch vụ đề nghị định giá
   
   Dưới section, chữ nhỏ màu `text-muted` kèm pill `yellow` "Giả định — chờ xác nhận": "Cấu trúc cột theo mẫu tạm, chờ đối chiếu mẫu chính thức Thông tư 21/2024/TT-BYT (TBD-01)." (ASM-019-01).
3. **Section "Bảng giải trình (PDF)"**: trường Link/Select "Dịch vụ" (`service_costs` từ `get_export_options`, hiện `mã — tên · khoa`; dịch vụ "Lỗi" có nhãn `red` "Tính lỗi" và không chọn được); nút "Tải PDF". Mở từ NC Service Cost: trường đặt sẵn, chỉ đọc.
4. **Section "Bộ định mức"**: Select "Bộ định mức" (`norm_sets` của lần tính, hoặc bộ đang mở); hai nút "Tải Excel", "Tải PDF".
5. **Section "Toàn bộ hồ sơ"** (chỉ khi có `run`): câu "Đóng gói Phụ lục II–V, mọi bảng giải trình và bộ định mức thành một tệp nén. Chạy nền; hệ thống báo khi xong."; nút "Đóng gói hồ sơ" (`btn-primary` của hộp thoại); nếu đã có tệp (`bundle`): liên kết "Tệp nén gần nhất ({dd/mm/yyyy HH:MM})".
6. Chân hộp thoại: "Mỗi tệp ghi mã lần tính giá, bộ tham số, thời điểm và người xuất; việc xuất được ghi vào nhật ký." (`text-muted`). Nút "Đóng".

Không hiện Phụ lục I và bảng so sánh giá (ASM-019-14). Lựa chọn có `enabled: false` hiện nút mờ (`disabled`) kèm `title` = `reason`.

### Trạng thái
- **Đang tải lựa chọn:** thân hộp thoại "Đang tải…" (spinner chuẩn) tới khi `get_export_options` trả về.
- **Rỗng:** lần tính không có dịch vụ thành công → section giải trình: "Chưa có dịch vụ tính thành công trong lần tính này"; không có bộ định mức → "Lần tính chưa gắn bộ định mức nào".
- **Đang xuất một tệp:** nút vừa bấm `disabled` + chữ "Đang tạo tệp…" tới khi trình duyệt nhận phản hồi (2 giây hoặc sự kiện lỗi), rồi trở lại.
- **Đang đóng gói:** sau `export_bundle` trả `queued: true` → dải `blue` trong section "Toàn bộ hồ sơ": "Đang đóng gói hồ sơ… Bạn có thể đóng hộp thoại; hệ thống sẽ báo khi xong." Nút "Đóng gói hồ sơ" `disabled`. `running: true` (đã có tác vụ) → cùng dải, câu "Hồ sơ của lần tính này đang được đóng gói."
- **Đóng gói xong:** `frappe.realtime.on("nc_export_bundle")` với `status: "done"` → dải `green` "Đã đóng gói hồ sơ." + liên kết "Tải tệp nén" (`file_url`); ngoài hộp thoại: `frappe.show_alert({message, indicator: "green"})` và thông báo trong chuông (Notification Log).
- **Lỗi xuất:** phản hồi lỗi của `export_file` → `msgprint` chuẩn, indicator `red`, tiêu đề "Lỗi xuất", nội dung câu lỗi máy chủ nguyên văn ("Không sinh được tệp …"). Lỗi đóng gói (`status: "error"`) → dải `red` `role="alert"` "Lỗi đóng gói hồ sơ: {message}. Chi tiết ở nhật ký lỗi." Nút đóng gói bật lại.
- **Lần tính chưa khóa** (gọi `open` trực tiếp): mọi nút mờ, dải `yellow` "Chỉ xuất hồ sơ từ lần tính giá đã khóa. Lần tính {run} đang ở trạng thái {status}."
- **Không có quyền:** `get_export_options` trả `PermissionError` → không mở hộp thoại, `msgprint` chuẩn "Bạn không có quyền xuất tệp này". Nút mở không hiện với vai trò không đọc được bản ghi (Desk đã ẩn form).
- **Chỉ đọc (NC Auditor, NC Director):** thấy và dùng mọi nút tải về và đóng gói (xuất là đọc, ASM-019-04); không có thao tác sửa nào trong hộp thoại.

### Bàn phím, truy cập (NFR-USE-004)
- Thứ tự Tab theo bố cục trên; mọi nút là `<button>` có nhãn chữ (không chỉ biểu tượng). `Esc` đóng hộp thoại; `Ctrl+Enter` = nút chính "Đóng gói hồ sơ" (chuẩn `frappe.ui.Dialog`).
- Màu chỉ báo luôn kèm chữ ("Đã khóa", "Tính lỗi", "Giả định — chờ xác nhận"); dùng lớp `indicator-pill` của Desk để giữ tương phản ở chế độ sáng và tối.
- Dải trạng thái đóng gói có `aria-live="polite"`; dải lỗi `role="alert"`.

## Nội dung tệp (bố cục in)
- **Excel Phụ lục II–V:** dòng 1–4 tiêu đề theo mẫu (tên đơn vị trống, "Phụ lục … — Thông tư 21/2024/TT-BYT", tên biểu, dòng lần tính · ngày · loại giá); tiêu đề cột in đậm, cố định khung dưới tiêu đề (`freeze_panes`); tiền `#,##0.00`, giá đề nghị `#,##0`; trang cuối "Thông tin xuất"; chân trang mọi trang tính.
- **PDF bảng giải trình (A4 dọc):** tiêu đề "BẢNG GIẢI TRÌNH GIÁ DỊCH VỤ", bảng đầu (dịch vụ, khoa, lần tính, loại giá, sản lượng); mỗi cấu phần một khối có dòng nhóm in đậm nền nhạt và tổng ở bên phải; trong khối, dòng nhóm bước thụt lề; dòng chi phí cột: Mã dòng · Nguồn lực · Lượng áp dụng · Đơn giá · Thành tiền · Nguồn đơn giá · Cảnh báo; số căn phải, định dạng `287.745,46`; phần "Chi phí phân bổ"; bảng tổng với "Giá thành toàn bộ" in đậm; khối "Thông tin xuất" cuối; chân trang mọi trang: dòng truy vết + "Trang x/y".
- **PDF bộ định mức (A4 ngang):** bảng đầu theo `HEAD_ROWS`; dòng định mức nhóm theo bước (tiêu đề bước in đậm), cột như Excel (bỏ cột cận lâm sàng khi bộ không có hệ thống xét nghiệm), gồm "Căn cứ", "Người xác nhận", "Thời điểm xác nhận"; bảng phụ nội kiểm, chuẩn máy, ngoại kiểm, k khi có hệ thống; khối "Thông tin xuất"; chân trang như trên.

## Kiểm
- 1366 × 768: hộp thoại `large` không tràn ngang; section dài cuộn trong thân hộp thoại.
- `tests/unit/test_export_ui.py` (tĩnh): `export_dialog.js` gọi đúng `normcore.api.export.get_export_options`, `export_file`, `export_bundle`; lắng nghe `nc_export_bundle`; mọi chuỗi `__()` có dòng trong `vi.d/FEAT-019.csv`; `nc_costing_run.js`, `nc_service_cost.js`, `nc_norm_set.js` gọi `normcore.export.open`; `NormGrid.vue` và `api/norm.py` không đổi (guard FEAT-014 `test_luoi_va_api_norm_khong_doi` đạt); `hook_registry/FEAT-019.json` khai báo đúng `["normcore_export.bundle.js"]` và không còn đường `/assets/...` cố định; `normcore_export.bundle.js` import `./export_dialog.js` (AMD-019-02). Không sửa test UI cũ; các test cũ (`test_costing_ui.py`, `test_costing_lock_ui.py`, `test_norm_cls_ui.py`, `test_form_buttons_i18n.py`) phải vẫn xanh — nếu một test cũ so khớp đúng tập nút/API của form, thêm nút theo cách không đổi tập đó (như ASM-018-15: gọi bằng tên phương thức đầy đủ trong `export_dialog.js`, không thêm vào hằng `API` của form).
