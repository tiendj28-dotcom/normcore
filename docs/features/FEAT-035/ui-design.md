# FEAT-035 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-021, SCR-DSK-037 (luồng tính giá: "Sản lượng và xuất kho SCR-DSK-037" → "Lần tính giá SCR-DSK-022"); `design.md`; `technical-design.md` mục 2–5. Hiện thực bằng danh sách + form chuẩn Desk của ba DocType mới và trang `import-excel` đã có (FEAT-004), không trang Vue (ASM-035-08, cùng hướng ASM-129). Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.csv` (giữ thứ tự chữ cái, không trùng khóa); nhãn DocType, tùy chọn Select, thông báo máy chủ tiếng Việt. Chỉ dùng biến CSS của Desk, `indicator-pill`, `frm.dashboard`; không mã màu cứng. Mọi quyền do máy chủ quyết; ẩn/hiện nút chỉ là tiện ích. Số theo NFR-LOC-001 (`format_number`, dấu chấm hàng nghìn).

**Workspace "Normcore"** (`nc_core/workspace/normcore/shortcuts.txt`, rồi `python3 scripts/build_workspace.py`; không sửa tay `normcore.json`): thêm nhóm lối tắt "Sản lượng cận lâm sàng và xuất kho" ngay sau "Sản lượng dịch vụ": "Sản lượng cận lâm sàng" (List NC Test System Volume), "Phút khai thác thiết bị" (List NC Equipment Usage), "Xuất kho thực tế" (List NC Stock Issue Actual), "Nhập sản lượng và xuất kho" (Page `import-excel`). Desk tự ẩn lối tắt với vai trò không đọc được DocType.

## SCR-DSK-037 Sản lượng cận lâm sàng và xuất kho (L + F)

Bước UC-022: (1) chọn năm và kịch bản → bộ lọc chuẩn của danh sách và cột "Năm tài chính", "Kịch bản sản lượng" trong tệp; (2)(3)(4) tải ba tệp → nút "Nhập từ Excel" của từng danh sách mở `import-excel` chọn sẵn bộ nhập; xem dòng đã nhập → danh sách.

### Ba danh sách (tệp `nc_test_system_volume_list.js`, `nc_equipment_usage_list.js`, `nc_stock_issue_actual_list.js`)

| Danh sách | Cột (`in_list_view`) | Bộ lọc chuẩn | Bộ nhập |
| :-- | :-- | :-- | :-- |
| NC Test System Volume | Năm tài chính, Kịch bản sản lượng, Hệ thống xét nghiệm, Dịch vụ, Số kết quả trả | năm, kịch bản, hệ thống, khoa | `nc_test_system_volume` |
| NC Equipment Usage | Năm tài chính, Kịch bản sản lượng, Thiết bị, Khoa, Tổng số phút khai thác | năm, kịch bản, thiết bị, khoa | `nc_equipment_usage` |
| NC Stock Issue Actual | Năm tài chính, Khoa, Mặt hàng, Lượng xuất | năm, khoa, mặt hàng | `nc_stock_issue_actual` |

- Nút "Nhập từ Excel" (`listview.page.add_inner_button`, chỉ khi `frappe.model.can_create(doctype)`): `frappe.set_route("import-excel", { import_set: "<khóa>" })` (ASM-004-01). Trên trang `import-excel` người dùng tải tệp mẫu, "Kiểm tra" (chế độ `thu`), "Xác nhận ghi" (`ghi`); bảng lỗi theo dòng/cột của khung FEAT-004 hiện đủ lỗi FR-ACCT-014 (TC-CLS-35).
- Nút "Tải tệp mẫu" không thêm ở danh sách (đã có trên `import-excel`).
- Mặc định bộ lọc danh sách NC Test System Volume và NC Equipment Usage: `scenario` = "Thực tế 12 tháng" (`filters` trong `listview_settings`; người dùng bỏ được) để khớp "kịch bản mặc định" (REF-09).
- NC Test System Volume: `get_indicator` — mọi cột test phụ có số → `green` "Có số thực tế"; có ít nhất một cột trống → `orange` "Sẽ ước tính từ kế hoạch" (`add_fields`: bốn trường test phụ). Chú thích trạng thái dùng chữ, không chỉ màu (NFR-USE-004).
- Rỗng: thông điệp chuẩn Desk + mô tả DocType "Chưa có sản lượng. Bấm Nhập từ Excel để nạp tệp từ LIS, RIS."

### Form NC Test System Volume (`nc_test_system_volume.js`)

Bố cục theo `technical-design.md` mục 2.1:
1. Cột trái: Năm tài chính, Kịch bản sản lượng (mặc định "Thực tế 12 tháng"), Hệ thống xét nghiệm, Dịch vụ (chỉ đọc), Khoa (chỉ đọc). Cột phải: Số kết quả trả, Tệp nguồn.
2. Section "Số test phụ (để trống: ước tính từ kế hoạch)": cột trái nội kiểm, chuẩn máy, chạy lại, ngoại kiểm; cột phải hao hụt (%), cỡ mẻ bình quân, số ngày chạy máy. Mô tả trường (`description`) của bốn số test: "Để trống nếu LIS không xuất được; lần tính giá sẽ ước tính từ kế hoạch chất lượng. Nhập 0 nghĩa là thật sự bằng 0."
3. `refresh`: khi `cls_volume.blank_aux` khác rỗng (tính ở JS bằng bốn trường trống), `frm.dashboard.set_headline_alert` màu `orange`: "Các cột trống sẽ được ước tính từ kế hoạch chất lượng khi tính giá: <danh sách nhãn>." Đủ số → không headline.
4. Ctrl+S lưu (chuẩn Desk). Lỗi máy chủ (trùng DI-14, số âm, hao hụt > 100) hiện hộp thoại lỗi chuẩn, tiếng Việt.

### Form NC Equipment Usage, NC Stock Issue Actual

Form chuẩn một section hai cột, thứ tự trường như `technical-design.md` 2.2, 2.3. NC Stock Issue Actual: khi chọn mặt hàng, JS đọc `NC Item.uom` và đặt `set_df_property("issued_qty", "description", "Đơn vị: Hộp")` (chỉ hiển thị, không lưu). NC Equipment Usage: mô tả trường thiết bị "Chỉ thiết bị chia chi phí theo Phút chiếm máy."

### Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Rỗng | Danh sách rỗng chuẩn Desk + mô tả; nút "Nhập từ Excel" (nếu có quyền tạo) |
| Đang tải | Skeleton chuẩn của danh sách/form Desk |
| Lỗi nhập | Trên `import-excel`: bảng "Dòng | Cột | Lỗi" của FEAT-004; dòng khác vẫn ghi ở "Xác nhận ghi" |
| Lỗi lưu form | Hộp thoại lỗi chuẩn, nội dung tiếng Việt của máy chủ |
| Không có quyền (Clinician, Consultant, Resource Manager…) | Lối tắt ẩn; mở URL trực tiếp → trang "Không có quyền" chuẩn |
| Chỉ đọc (NC Director, NC Admin, NC Auditor; NC Department Head chỉ khoa mình) | Danh sách/form chỉ đọc; không nút "Nhập từ Excel"; indicator và headline vẫn hiện |
| Workflow | Không có luồng trạng thái |

### Khối tình trạng trên form NC Test System (SCR-DSK-032, FEAT-031)

Mục "Sản lượng kịch bản mặc định" (khóa `volume`) đổi theo `get_status`: `ok` → pill `green` + "Năm 2026: 12.000 kết quả trả"; `estimated` → pill `orange` + "Năm 2026: 4.000 kết quả trả — số test phụ sẽ ước tính từ kế hoạch"; `empty` → giữ "Chưa có" như cũ. Mục là liên kết tới danh sách NC Test System Volume lọc theo hệ thống. Không đổi ba mục còn lại.

## SCR-DSK-021 Sản lượng và phân bổ (L + F) — phần FEAT-035

Cột kịch bản của sản lượng HIS **đã có** (FEAT-016: `scenario` ở danh sách NC Service Volume). FEAT này chỉ thêm liên kết sang SCR-DSK-037: nút "Clinical volume and stock issues" (vi: "Sản lượng cận lâm sàng và xuất kho") ở `nc_service_volume_list.js` (nhóm nút trong, mọi vai trò đọc được NC Test System Volume) → `frappe.set_route("List", "NC Test System Volume")`. Không đổi nút "Nhập từ Excel" đã có.

## Kiểm chung

- 1366 × 768: danh sách ≤ 5 cột, form hai cột; không cuộn ngang.
- Bàn phím: thứ tự Tab theo thứ tự trường; nút có nhãn chữ.
- Tương phản: chỉ `indicator-pill` và biến CSS Desk (NFR-USE-004); trạng thái luôn có chữ.
- Chuỗi: mọi chuỗi JS qua `__()`, có dòng `vi.csv`; test quy ước kiểu `tests/unit/test_cls_volume_ui_conventions.py` (mẫu `test_accounting_ui_conventions.py`): có `__(`, không mã màu cứng, khóa `vi.csv` có đủ.
