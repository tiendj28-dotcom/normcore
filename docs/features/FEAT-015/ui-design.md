# FEAT-015 — Thiết kế giao diện

Căn cứ: `ux-foundations.md` SCR-DSK-022 (F), SCR-DSK-023 (P nhẹ, chế độ xem của NC Service Cost), Luồng 2, thành phần "Thanh cơ cấu giá"; `design.md` mục 3 (màu trạng thái, Bản ghi chỉ đọc), 4, 5 (số `1.234.567`, tiền thêm ` đ`, ngày `dd/mm/yyyy`); API ở `technical-design.md` mục 3. Chiến lược code-native: Form/List chuẩn của Desk + HTML vẽ trong vùng dashboard của form (`frm.dashboard.add_section`), không trang Vue riêng, không thêm trường HTML (không cần AMD). Phần **[1.1]** của hai màn hình (kịch bản sản lượng, cách phân bổ kiểm định, tab theo hệ thống xét nghiệm, khối "k được tính thế nào", cột cấp phát sinh, k, mẫu số) **không** làm ở đây — FEAT-036.

Màu chỉ báo: Nháp `gray`; Đang tính `orange`; Đã tính `blue`; Tính lỗi, Lỗi `red`; Đã khóa, Thành công `green`; Cảnh báo `yellow`. Mọi nhãn màu có chữ. Chuỗi qua `__()` (JS), `_()` (Python), dịch ở `vi.csv`. Giữ `__("Run costing")` (Chạy tính giá) và `__("View costing results")` (Xem kết quả tính giá) vì `test_form_buttons_i18n.py` buộc.

## SCR-DSK-022 Lần tính giá (Form + List NC Costing Run)

**List** (`nc_costing_run_list.js`): cột Tên, Năm tài chính, Ngày tính giá, Loại giá, Trạng thái (indicator), Tiến độ; bộ lọc chuẩn Trạng thái, Năm, Loại giá. Rỗng: "Chưa có lần tính giá. Tạo lần tính giá đầu tiên." + nút "Thêm" (chỉ khi `can_create`).

**Form — bố cục** (1366 × 768, hai cột):
1. Section "Đầu vào": cột trái `title`, `fiscal_year`, `costing_date`; cột phải `parameter_set`, `accounting_import` (`set_query` lọc `status = "Đã chốt"`, mô tả "Chỉ chọn được lần nhập đã chốt"), `price_category`.
2. Section "Phạm vi": `scope_departments`, `scope_services` (Table MultiSelect); mô tả "Để trống cả hai = toàn viện".
3. Section "Trạng thái": `status` (chỉ đọc), `progress` (chỉ đọc, ẩn khi không "Đang tính").
4. **Vùng kết quả** (dashboard, chỉ khi "Đã tính" hoặc "Tính lỗi" có kết quả): dòng đếm "n dịch vụ: a Thành công · b Cảnh báo · c Lỗi" (indicator); bảng (`get_run_results`) cột Mã dịch vụ, Tên, Khoa, Kết quả (indicator), Thông báo (cắt 80 ký tự, đủ ở tooltip), Giá thành, Giá tính toán, Giá làm tròn (căn phải, số đơn cách). Bấm/Enter trên dòng → mở form NC Service Cost (SCR-DSK-023). Lọc nhanh "Chỉ dịch vụ lỗi hoặc cảnh báo". Có dịch vụ không có dòng phân bổ → dải `yellow` trên bảng: "Chưa gồm chi phí phân bổ chung (phân bổ cấp 1, cấp 2 làm ở FEAT-017)" (ASM-015-02).

**Hành động**:
- "Chạy tính giá" (`btn-primary`; status ∈ Nháp, Tính lỗi, Đã tính; `frm.perm[0].write`; form đã lưu — chưa lưu thì `msgprint` "Lưu trước khi chạy"): gọi `check_scope(run)`.
  - `ineligible` rỗng → hộp xác nhận "Tính giá cho n dịch vụ?" (+ "Lần tính sẽ chạy nền và hiện tiến độ." khi `background`) → `start_costing(run, 0)`.
  - `ineligible` khác rỗng → hộp thoại "Có m dịch vụ chưa có bộ định mức Đã khóa" liệt kê từng dòng "Mã — Tên dịch vụ · Khoa" (cuộn khi > 10), câu "Chỉ tính n dịch vụ đủ điều kiện." Nút "Chỉ tính dịch vụ đủ điều kiện" (`btn-primary`) → `start_costing(run, 1)`; "Hủy". `eligible` rỗng → chỉ nút "Đóng", nội dung "Không có dịch vụ nào đủ điều kiện để tính."
  - Ở "Đã tính" nhãn hộp xác nhận nêu hệ quả: "Kết quả cũ của lần tính này sẽ được thay."
- "Xem kết quả tính giá" (status "Đã tính"): mở List NC Service Cost lọc `costing_run`.
- Không có nút "Khóa", "Nhân bản" ở FEAT-015 (FEAT-018).

**Trạng thái**:
- Đang tính: dải `orange` "Đang tính giá… n%" + thanh tiến độ (`frm.dashboard.show_progress`), cập nhật qua `frappe.realtime.on("normcore_costing_progress")`, dự phòng gọi `get_progress` mỗi 5 giây; xong → `frm.reload_doc()` và `show_alert` "Đã tính xong" (`green`) hoặc "Tính lỗi" (`red`). Mọi trường đầu vào chỉ đọc.
- Tính lỗi: dải `red` "Lần tính lỗi. Xem Error Log hoặc chạy lại."; đầu vào sửa được.
- Đã tính: đầu vào chỉ đọc (máy chủ cũng chặn), dải "Muốn đổi đầu vào, hãy nhân bản lần tính." (chữ `--text-muted`).
- Đã khóa: dải chỉ đọc theo design.md "Bản ghi đã Đã khóa, không sửa được." (khóa là FEAT-018; form chỉ hiển thị).
- Lỗi máy chủ (từ chối tạo TC-COST-19, từ chối chạy): `frappe.msgprint` chữ máy chủ, mỗi lỗi một dòng.
- Không quyền đọc: trang lỗi quyền chuẩn. NC Auditor, NC Director: form chỉ đọc, không nút "Chạy tính giá"; vùng kết quả vẫn hiện.

## SCR-DSK-023 Bảng giải trình dịch vụ (Form NC Service Cost, chế độ xem)

**Vào màn hình**: từ bảng kết quả SCR-DSK-022 hoặc List NC Service Cost (`nc_service_cost_list.js`: cột Lần tính, Dịch vụ, Khoa, Kết quả (indicator Thành công `green` / Cảnh báo `yellow` / Lỗi `red`), Giá thành, Giá làm tròn; bộ lọc Lần tính, Khoa, Kết quả). Form toàn bộ chỉ đọc; bảng con `lines` ẩn (nội dung hiện ở vùng giải trình). `refresh` gọi `get_explanation(name)` và vẽ vào dashboard.

**Bố cục** (một cột, rộng ≤ 1366 px, bảng cuộn dọc trong trang):
1. **Đầu**: tên dịch vụ, khoa, liên kết lần tính giá, loại giá, nhãn Kết quả; `calc_message` khi có (dải `red` ở Lỗi, `yellow` ở Cảnh báo).
2. **Dải ghi chú** (`notes`): "Khấu hao bị loại: loại giá không kết cấu khấu hao — khấu hao thiết bị và hạ tầng lấy bằng 0; bảo trì, kiểm định vẫn tính." (FR-COST-007); "Chưa gồm chi phí phân bổ chung…" (ASM-015-02).
3. **Khối giá** (hàng 5 ô số căn phải): Chi phí trực tiếp · Phân bổ · Giá thành toàn bộ · Tích lũy · Nghĩa vụ tài chính · Giá tính toán · **Giá làm tròn** (đậm). Tiền định dạng `1.234.567,89 đ`; giá làm tròn không lẻ.
4. **Thanh cơ cấu giá** (thành phần ux): thanh xếp chồng theo cấu phần (Nhân lực, Thuốc, Vật tư, Thiết bị, Hạ tầng, Tiện ích, rồi các loại phân bổ), mỗi đoạn có nhãn chữ + số tiền + tỷ trọng ở chú giải bên dưới (không dựa riêng vào màu); màu dùng biến CSS của Desk (`--blue-500`, `--green-500`…), không mã màu cứng.
5. **Bảng chi phí trực tiếp**, nhóm theo cấu phần rồi bước (hàng nhóm nền nhấn nhẹ, tổng ở cuối hàng; Enter/bấm để thu gọn): cột Mã bước ("Chung" khi trống), Dòng định mức, Nguồn lực, Lượng áp dụng, Đơn giá (4 số lẻ khi có phần lẻ), Thành tiền, Nguồn đơn giá, Cảnh báo (nhãn `yellow` chữ "Đơn giá quá hạn tham chiếu" / "Đơn giá chưa xác minh"; nhãn `gray` "Khấu hao bị loại"; dòng loại trừ chữ `--text-muted` "Loại trừ: …").
6. **Bảng phân bổ** (chỉ khi có dòng): cột Loại chi phí, Quy tắc phân bổ (liên kết), Tiêu chí của dịch vụ, Tổng tiêu chí, Số tiền phân bổ (pool), Số tiền một ca. Không có dòng → không hiện bảng (đã có dải ghi chú).

**Trạng thái**: đang tải — khung xám "Đang tải bảng giải trình…"; Lỗi — chỉ đầu + dải lỗi liệt kê dòng thiếu đơn giá (mỗi dòng một dòng), không có khối giá; không quyền — trang lỗi quyền chuẩn (Clinician); NC Auditor, NC Director — xem đủ, không nút nào. NC Department Head chỉ mở được dịch vụ thuộc khoa mình nếu Lead chọn Q2 = PA1.

## Kiểm
- 1366 × 768: form lần tính và bảng giải trình không cuộn ngang ở trang; bảng giải trình 11 dòng DV-TEST-A vừa một màn hình khi thu gọn nhóm.
- Bàn phím: Tab qua nút, dòng bảng kết quả, hàng nhóm; Enter mở/thu gọn; Esc đóng hộp thoại.
- Tương phản ≥ 4,5:1 (NFR-USE-004): chỉ dùng biến màu Desk.
- Test tĩnh `tests/unit/test_costing_ui.py`: tệp JS chỉ gọi `normcore.api.costing.*` và `run_doc_method`; không mã màu cứng; mọi chuỗi qua `__()` có trong `vi.csv`; có `role="alert"` cho dải lỗi.
