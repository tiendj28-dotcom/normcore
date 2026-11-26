# FEAT-036 — Thiết kế giao diện

Căn cứ: `ux-foundations.md` SCR-DSK-022, SCR-DSK-023 (phần **[1.1]**); `design.md` mục 3 (màu trạng thái, Bản ghi chỉ đọc), 4, 5 (số `1.234.567`, tiền thêm ` đ`, ngày `dd/mm/yyyy`; k hiện 6 chữ số `1,108247`); API ở `technical-design.md` mục 3. Giữ chiến lược của FEAT-015 (`docs/features/FEAT-015/ui-design.md`): Form/List chuẩn của Desk + HTML vẽ trong dashboard của form, không trang Vue, không trường HTML mới. Phần không nêu ở đây giữ nguyên như FEAT-015.

Màu: như FEAT-015. Thêm nhãn `blue` "Cận lâm sàng", nhãn `orange` "Ước tính từ kế hoạch", nhãn `yellow` "Sản lượng thấp", "Thiếu hồ sơ tuân thủ". Mọi nhãn màu có chữ. Chuỗi qua `__()` / `_()`, dịch ở `vi.csv`.

Nhãn cấp phát sinh (hiện thay mã `cost_level`): RESULT "Theo kết quả", TUBE "Theo ống mẫu", BATCH "Theo mẻ", DAY "Theo ngày-máy", PERIOD "Theo kỳ".

## SCR-DSK-022 Lần tính giá (Form NC Costing Run) — phần thêm

**Loại**: Form DocType chuẩn + vùng dashboard (như FEAT-015).

**Bố cục**
1. Section "Đầu vào", cột phải sau `price_category`: `volume_scenario` (Select, mô tả "Mỗi lần tính dùng một kịch bản; so sánh kịch bản bằng nhân bản lần tính"), `compliance_allocation_mode` (Select, mô tả "Cách chia chi phí kiểm định, hiệu chuẩn của thiết bị"). Khi tạo mới hiện sẵn giá trị mặc định "Thực tế 12 tháng", "Theo giá trị tài sản". Chỉ đọc ngoài Nháp, Tính lỗi (như các đầu vào khác).
2. Section "Trạng thái": thêm `run_warnings` (chỉ đọc, ẩn khi trống).
3. **Dải cảnh báo lần tính** (đầu vùng kết quả, khi `run_warnings` khác trống): dải `yellow`, `role="status"`, tiêu đề "Lần tính có n cảnh báo, vẫn tính", mỗi cảnh báo một dòng (ví dụ "Thiết bị EQ_A (Máy hóa sinh) không có hồ sơ tuân thủ còn hạn tại 31/12/2026"). Quá 5 dòng → "Xem thêm" mở rộng tại chỗ.
4. **Bảng kết quả** (`get_run_results`): thêm nhãn `blue` "Cận lâm sàng" sau tên dịch vụ khi `is_paraclinical`; cột "Thông báo" hiện cả lỗi dừng dịch vụ (ví dụ "Hệ thống GLU-B thiếu sản lượng năm 2026, kịch bản Thực tế 12 tháng") và "Sản lượng thấp: …". Bộ lọc nhanh "Chỉ dịch vụ lỗi hoặc cảnh báo" giữ nguyên.
5. **Khối "Kết quả theo hệ thống xét nghiệm"** (dưới bảng kết quả, chỉ khi có dịch vụ cận lâm sàng; tiêu đề thu gọn được, mặc định mở): bảng một dòng mỗi hệ thống, nhóm theo dịch vụ · khoa. Cột: Hệ thống, Bộ định mức (liên kết), Số kết quả trả, Tỷ trọng (`75,00%`), k (6 chữ số; nhãn `orange` "Ước tính từ kế hoạch" khi `k_estimated`), Chi phí trực tiếp một kết quả, Cảnh báo (nhãn `yellow` "Sản lượng thấp"). Hàng nhóm dịch vụ: "Bình quân gia quyền + ngoại kiểm = chi phí trực tiếp dịch vụ". Bấm/Enter trên dòng → mở NC Service Cost của dịch vụ, cuộn tới hệ thống.

**Hành động**: không thêm nút. "Chạy tính giá" như FEAT-015; hộp thoại dịch vụ chưa đủ điều kiện liệt kê cả dịch vụ cận lâm sàng chưa có hệ thống nào có bộ "Đã khóa".

**Trạng thái**: rỗng (chưa tính) — không hiện khối 5; đang tính — như FEAT-015, khối 3–5 ẩn; Tính lỗi — như FEAT-015; dịch vụ cận lâm sàng "Lỗi" — dòng bảng 4 `red`, không có dòng ở khối 5 (không có kết quả hệ thống); Đã khóa — chỉ đọc. NC Auditor, NC Director: xem đủ, không nút. Không quyền: trang lỗi quyền chuẩn.

**API**: `check_scope`, `start_costing`, `get_progress`, `get_run_results` (đã mở rộng).

## SCR-DSK-023 Bảng giải trình dịch vụ (Form NC Service Cost) — dịch vụ cận lâm sàng

**Loại**: Form chỉ đọc + vùng dashboard (như FEAT-015). `test_system_costs` ẩn như `lines` (nội dung hiện ở vùng giải trình). Dịch vụ thường hiển thị như FEAT-015, không đổi.

**Bố cục** (khi `get_explanation.paraclinical` khác None; một cột, ≤ 1366 px):
1. **Đầu**: như FEAT-015 + nhãn `blue` "Cận lâm sàng"; dòng phụ "Kịch bản: Thực tế 12 tháng · Kiểm định: Theo giá trị tài sản".
2. **Dải ghi chú**: như FEAT-015 + "Khấu hao thiết bị hết thời gian sử dụng: lấy bằng 0 (ZERO)" hoặc "… tiếp tục tính (CONTINUE)" khi có (TC-CLS-11); "Số test phụ của hệ thống GLU-B ước tính từ kế hoạch chất lượng" (nhãn `orange`) khi có hệ thống `k_estimated`.
3. **Khối giá**: như FEAT-015.
4. **Bảng tổng hợp hệ thống** (tiêu đề "Chi phí trực tiếp theo hệ thống xét nghiệm"): cột Hệ thống, Thiết bị, Số kết quả trả, Tỷ trọng, Nguồn tỷ trọng ("Từ số kết quả trả" / "Khai tay"), k, Chi phí một kết quả, Cảnh báo. Ba dòng cuối căn phải: "Bình quân gia quyền" (`weighted_direct`), "Ngoại kiểm một kết quả" (`eqa_cost`), "**Chi phí trực tiếp của dịch vụ**" (`direct_total`, đậm).
5. **Khối "k được tính thế nào"** (mỗi hệ thống một thẻ, thu gọn được, mặc định mở hệ thống đầu): công thức chữ "k = (Qbn + Qnk + Qchuẩn + Qlại + Qngk) ÷ ((1 − h) × Qbn)"; bảng hai cột: Qbn (số kết quả trả), Qnk (nội kiểm), Qchuẩn (chuẩn máy), Qlại (chạy lại), Qngk (ngoại kiểm), Tổng test, h (%), k (6 chữ số). Hệ thống `k_estimated` → nhãn `orange` "Ước tính từ kế hoạch" cạnh tiêu đề thẻ. Ví dụ hiển thị: "12.000 + 600 + 48 + 240 + 12 = 12.900; 12.900 ÷ ((1 − 3%) × 12.000) = 1,108247".
6. **Bảng chi phí trực tiếp**, nhóm theo **hệ thống** → cấu phần → bước (hàng nhóm hệ thống nền nhấn, ghi "GLU-A · một kết quả của hệ thống · tổng 41.531,03"; nhóm cuối "Cấp dịch vụ" chứa dòng ngoại kiểm). Cột: Dòng (`norm_line_id`; dòng tự sinh hiện tên: "Linh kiện theo số kết quả", "Điện của thiết bị", "Vật liệu nội kiểm", "Chất chuẩn", "Ngoại kiểm"), Nguồn của dòng (`line_origin`), Cấp phát sinh, Nguồn lực, Lượng áp dụng, Đơn giá, k (chỉ dòng nhân k), Mẫu số (`divisor_label` + `divisor_value`, ví dụ "Cỡ mẻ: 40", "Qtb: 300.000"), Nguồn mẫu số (`Thực tế` chữ thường; `Ước tính từ kế hoạch` nhãn `orange`), Thành tiền, Nguồn đơn giá, Cảnh báo. Dưới bảng, chữ `--text-muted`: "Thành tiền mỗi dòng là chi phí cho một kết quả của hệ thống. Chi phí trực tiếp của dịch vụ là bình quân gia quyền theo tỷ trọng, cộng ngoại kiểm."
   - Bảng rộng: ở 1366 px gộp "Nguồn lực" và "Nguồn đơn giá" thành một cột hai dòng; "Cảnh báo" chỉ hiện nhãn, chi tiết ở tooltip — không cuộn ngang trang (bảng tự cuộn ngang trong khung nếu cần).
7. **Bảng phân bổ**: như FEAT-015.

**Trạng thái**: đang tải — khung xám "Đang tải bảng giải trình…"; Lỗi — đầu + dải `red` `role="alert"` liệt kê từng lỗi (`calc_message` tách theo "; "), không có khối 3–6; Cảnh báo — dải `yellow` "Sản lượng thấp: …" ở đầu, có đủ khối; NC Auditor, NC Director — xem đủ, không nút; NC Department Head — chỉ dịch vụ thuộc khoa mình (scope rule FEAT-015); không quyền — trang lỗi quyền chuẩn.

**API**: `get_explanation(service_cost)` (mở rộng, `technical-design.md` mục 3).

## Kiểm
- 1366 × 768: form lần tính và bảng giải trình GLU (2 hệ thống, 11 dòng mỗi hệ thống + 1 dòng ngoại kiểm) không cuộn ngang ở trang; thu gọn nhóm hệ thống còn ≤ 1 màn hình.
- Bàn phím: Tab qua dòng khối 5 (SCR-DSK-022), thẻ k, hàng nhóm; Enter mở/thu gọn hoặc mở dịch vụ; Esc đóng hộp thoại.
- Tương phản ≥ 4,5:1 (NFR-USE-004): chỉ biến màu Desk (`--orange-500`, `--yellow-500`, `--blue-500`…), không mã màu cứng; nhãn màu luôn có chữ.
- Số: tiền `41.531,03 đ`; k `1,108247`; tỷ trọng `75,00%`; số test `12.900`.
- Test tĩnh `tests/unit/test_costing_cls_ui.py` (T07, T08): mọi chuỗi mới qua `__()` có trong `vi.csv`; không mã màu cứng; JS chỉ gọi `normcore.api.costing.*` và `run_doc_method`; có `role="alert"` cho dải lỗi và `role="status"` cho dải cảnh báo; có đủ năm nhãn cấp phát sinh.
