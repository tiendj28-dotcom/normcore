# FEAT-005 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-005, SCR-DSK-006, "Thẻ tình trạng chuỗi"; `design.md` mục 3–7; technical-design mục 2–5. Dùng danh sách và form chuẩn của Desk; không trang tùy biến. Chuỗi JS viết tiếng Anh trong `__()`, bản dịch ở `normcore/translations/vi.csv`; nhãn DocType và chuỗi máy chủ viết tiếng Việt. Chỉ biến CSS của Desk và lớp `indicator-pill`.

## SCR-DSK-005 Danh sách dịch vụ — List chuẩn

Tệp: `nc_procedure/doctype/nc_technical_service/nc_technical_service_list.js`.

| Phần | Nội dung |
| :-- | :-- |
| Cột | Tên dịch vụ (title), Mã dịch vụ (ID), Chuyên khoa, Đang dùng |
| Bộ lọc chuẩn | ID (mã), Tên dịch vụ, Chuyên khoa, Đang dùng, **Khoa thực hiện** |
| Chỉ báo | Đang dùng `green`, Ngừng dùng `darkgrey` (`get_indicator` theo `is_active`) |
| Nút | "Tải tệp mẫu" (mọi người đọc được danh sách); "Nhập từ Excel" (`frappe.model.can_create`) |

- Bộ lọc khoa: trong `onload(listview)` gọi `listview.page.add_field({fieldname: "department", doctype: "NC Service Department", fieldtype: "Link", options: "NC Department", condition: "=", label: …, onchange: …})`. `FilterArea.get_standard_filters` của Frappe 15.127 đọc mọi trường trong `page.fields_dict` và dùng `df.doctype`, nên gửi đúng `["NC Service Department", "department", "=", <khoa>]`; `onchange` gọi `listview.filter_area.debounced_refresh_list_view()`. Đã đọc mã nguồn Frappe, chưa chạy trên trình duyệt: Dev xác nhận ở T07.
- "Tải tệp mẫu": mở `/api/method/normcore.api.importer.download_template?import_set=nc_technical_service`. "Nhập từ Excel": `frappe.set_route("import-excel")`; không sửa trang `import-excel`.
- Không có cột và bộ lọc tình trạng chuỗi (AMD-004).

| Trạng thái | Hiển thị |
| :-- | :-- |
| Rỗng | Trạng thái trống chuẩn của Desk; hai nút trên vẫn có, nên người có quyền nhập được ngay |
| Đang tải, lỗi | Chuẩn của Desk |
| Không có quyền | Trang "không đủ quyền" chuẩn của Desk |
| Chỉ đọc (NC Auditor và bảy vai trò đọc) | Không có nút tạo và nút "Nhập từ Excel"; còn "Tải tệp mẫu" |

## SCR-DSK-006 Dịch vụ kỹ thuật — Form chuẩn

Tệp: `nc_procedure/doctype/nc_technical_service/nc_technical_service.js`.

| Thứ tự | Section | Trường |
| :-- | :-- | :-- |
| 1 | (không nhãn), hai cột | Trái: `service_code`, `service_name`. Phải: `specialty`, `is_active` |
| 2 | `chain_section` "Tình trạng chuỗi" | `chain_status_html` (HTML) |
| 3 | `departments_section` "Khoa thực hiện" | `departments` |

**Thẻ tình trạng chuỗi.** Bốn thẻ con trên một hàng, nối bằng đường kẻ (biến `--border-color`), thứ tự Quy trình → Định mức → Giá thành → Giá đã duyệt. Dưới 768 px xếp dọc. Mỗi thẻ: chấm và nhãn trạng thái (`indicator-pill` + chữ), rồi một hàng cho mỗi khoa.

| `state` của mục | Hiển thị |
| :-- | :-- |
| `ok` | Mỗi khoa một hàng: tên khoa, liên kết tên bản ghi, trạng thái có màu, ngày `dd/mm/yyyy` |
| `empty` | Xám, "Chưa có" hoặc `message` của mục |
| `no_permission` | Xám, "Không có quyền xem"; không liên kết, không dòng khoa nào khi `rows` rỗng |

- Hàng khoa `no_permission`: tên khoa và "Không có quyền xem". Hàng `empty`: tên khoa và "Chưa có".
- Thẻ Giá thành: nhãn vàng "Giả định — chờ xác nhận"; hàng có ngày tính, trạng thái lần tính, liên kết NC Service Cost; nhãn đỏ "Lỗi" hoặc vàng "Cảnh báo" theo kết quả. Không có số tiền.
- Thẻ Giá đã duyệt: phần tử `id="nc-chain-price"`, `tabindex="-1"`; chữ "Chưa có giá đã duyệt" là liên kết `#nc-chain-price`: bấm thì cuộn tới và đặt focus vào thẻ, không đổi route.
- Quy trình chưa tới ngày hiệu lực: thêm nhãn vàng "Chưa hiệu lực".
- Mọi dữ liệu chèn vào HTML đi qua `frappe.utils.escape_html`. Liên kết là thẻ `<a href>` thật, dùng `route` từ API.

| Trạng thái form | Hiển thị |
| :-- | :-- |
| Bản ghi mới chưa lưu | Ẩn section Tình trạng chuỗi; không gọi API |
| Đang tải | "Đang tải tình trạng chuỗi…" |
| Lỗi gọi API | "Không tải được tình trạng chuỗi." và nút "Thử lại"; không chặn form |
| Chuyển bản ghi khi API chưa về | Bỏ kết quả có `service` khác `frm.doc.name` |
| Chỉ đọc (Auditor, Clinician…) | Form chuẩn chỉ đọc; thẻ vẫn hiện theo quyền |
| Lỗi nhập liệu | Trùng khoa: thông báo máy chủ; thiếu mã, tên: thông báo chuẩn |

| Hành động | API |
| :-- | :-- |
| Mở form, sau khi lưu, "Thử lại" | `normcore.api.service.get_chain_status(service)` |
| Gán khoa, sửa | Lưu form chuẩn |

Không có nút "Soạn quy trình", "Khởi tạo bộ định mức", khối "Cận lâm sàng".

## Danh mục chuyên khoa (NC Specialty)

Danh sách và form chuẩn, hai trường. `quick_entry` = 1 để tạo nhanh từ ô Chuyên khoa của dịch vụ (người có quyền tạo). Không có mã SCR riêng.

## Workspace

Thêm hai lối tắt "Dịch vụ kỹ thuật" và "Chuyên khoa" vào Workspace "Normcore" (`nc_core/workspace/normcore/normcore.json`), không xóa lối tắt cũ.

## Kiểm

- 1366 × 768: bốn thẻ nằm trên một hàng, không cuộn ngang; 768 px: xếp dọc.
- Bàn phím: Tab qua từng liên kết và "Thử lại"; viền focus thấy được; Enter mở. Trạng thái có chữ, không chỉ màu; tương phản do biến CSS của Desk (NFR-USE-004).
- Chuỗi: U trong technical-design mục 6, dòng 19.
- Xem thật bằng `multica env start preview`; không chụp được thì ghi rõ "chưa kiểm trên trình duyệt" trong `implementation-log.md`.
