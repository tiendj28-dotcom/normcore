# As-Built: FEAT-028 So sánh giá và gợi ý điều chỉnh
- Phiên bản app 0.0.1; Dev: NORM-81; nghiệm thu: QA (Multica), `docs/features/FEAT-028/acceptance.md`

## 1. Luồng nghiệp vụ đã xây
- **FR-ADJ-001.** Giá tham chiếu so sánh = dòng "Đã xác nhận" (FEAT-026), cùng loại giá với lần tính, `effective_date` trong `[ngày tính giá − benchmark_window_months tháng, ngày tính giá]`; mỗi đơn vị một dòng mới nhất (hòa ngày: `name` nhỏ nhất). Giá bị loại hiện kèm lý do (Ngoài cửa sổ 24 tháng, Cũ hơn giá khác của đơn vị, Sau ngày tính giá) (ASM-028-01).
- **FR-ADJ-002, 003.** Thấp nhất, trung vị, cao nhất, độ lệch % = (giá tính toán − trung vị) ÷ trung vị × 100, 2 số lẻ `ROUND_HALF_UP` (BR-ADJ-008, ASM-028-03). Dưới `min_benchmark_facilities` đơn vị: nhãn "Chưa đủ dữ liệu so sánh", không thống kê, không sinh gợi ý. TC-ADJ-02: 302.132,73 với 3 giá → 280.000, +7,90%; 4 giá → 290.000, +4,18%.
- **FR-ADJ-004.** Lọc tỉnh/thành phố, hạng, loại hình; tính lại thống kê trên tập đã lọc. Công tắc "Dùng giá hiệu chỉnh" (BR-ADJ-009, mặc định tắt, ASM-028-02).
- **FR-ADJ-005.** Vượt ngưỡng (|độ lệch| > `comparison_tolerance`, ASM-028-04) → `rules.generate`: giá cao hơn trung vị chạy BR-ADJ-001..004 và 005 (giảm 1 điểm %); thấp hơn chạy 006, 007 và 005 (tăng 1 điểm %) (ASM-028-05). Gợi ý bằng quy tắc, không AI. Tác động ước tính gọi lại `engine.direct_line`, `engine.price_service`, `resources.machine_hourly_rate`, phân bổ cấp 2 giữ nguyên (ASM-028-06); BR-ADJ-006, 007 không có số ước tính (ASM-028-07). Dữ kiện đọc từ dữ liệu sống, dòng định mức và đơn giá từ ảnh chụp đầu vào của lần tính (ASM-028-08). Sinh lại: cập nhật bản "Mới" cùng (quy tắc, đối tượng), giữ bản đã quyết, xóa bản "Mới" không còn kích hoạt (ASM-028-09). DV-TEST-A (độ lệch +20,85%, EQ1 hệ số 0,4, trung vị bấm giờ L04 = 15 phút): BR-ADJ-001 −15.411,93; BR-ADJ-002 −5.218,93; BR-ADJ-005 −2.877,45 (thứ tự 001, 002, 005).
- **FR-ADJ-008.** `decide_suggestion`: Chấp nhận / Từ chối từ trạng thái "Mới"; Từ chối bắt buộc lý do; lưu người và thời điểm. Gợi ý cần sửa quy trình (BR-ADJ-003) chỉ Từ chối được (UC-014 4b thuộc FEAT-029, ASM-028-11).
- **FR-ADJ-010.** Cơ cấu giá: giá trị và tỷ trọng của 6 cấu phần trực tiếp (thêm Ngoại kiểm khi có) và 5 cấu phần phân bổ; Σ giá trị = giá thành toàn bộ (287.745,46 với DV-TEST-A) (ASM-028-10).
- **Màn hình SCR-DSK-026** (`price-compare`): bảng dịch vụ có thanh so sánh giá, khung chi tiết (giá tham chiếu, cơ cấu giá, gợi ý), mở từ nút "So sánh giá" của NC Costing Run.

## 2. DocType tạo mới hoặc thay đổi
Một DocType mới: **NC Adjustment Suggestion** (module NC Benchmark), đặt tên `ADJ-.YYYY.-.#####`, mọi trường chỉ đọc trên form. Không đổi DocType cũ; không cần patch. Controller: sinh/sửa chỉ khi máy chủ đặt `flags.adj_system`, quyết định khi `flags.adj_decision`; bản đã quyết không sửa; tạo mới luôn ở "Mới". Phạm vi khoa qua `core/scope_rules/nc_adjustment_suggestion.json` (`via` service_cost).

## 3. API, hook
- `api/price_compare.py`: `get_comparison`, `get_service_detail`, `generate_suggestions`, `decide_suggestion` (whitelist, kiểm quyền); `_facts` dựng dữ kiện quy tắc.
- `api/benchmark.py`: thêm `comparable_prices_bulk` (không whitelisted); `get_comparable_prices` giữ nguyên.
- `benchmark/stats.py`, `benchmark/rules.py` (thuần). Độ phủ `rules.py` 100%.
- Giao diện: Page `price-compare`, `public/js/price_compare/`, nút ở `nc_costing_run.js`, form/list NC Adjustment Suggestion; bản dịch `translations/vi.d/FEAT-028.csv`; lối tắt `shortcuts.d/FEAT-028.txt`.

## 4. Quyền
Dòng "Gợi ý, kịch bản, phương án giá" (data-model mục 4): NC Finance đọc/tạo/sửa; NC Department Head, NC Director đọc (Trưởng khoa theo khoa); NC Consultant, NC Admin, NC Auditor đọc. Quyết định Chấp nhận/Từ chối ("A"): NC Finance, NC Director, Trưởng khoa trong khoa của dịch vụ; NC Auditor, NC Admin, NC Consultant bị từ chối. Sinh gợi ý: NC Finance. Trang `price-compare` không mở cho NC Consultant (không đọc được kết quả tính giá). Trưởng khoa không đọc NC Costing Run nên quyền xem dựa trên NC Service Cost.

## 5. Cấu hình cần thiết khi triển khai
Không. Ngưỡng lệch ở NC Costing Parameter Set (`comparison_tolerance`, `wastage_cap`); cửa sổ và số đơn vị tối thiểu ở NC Settings.

## 6. Test case đã chạy và kết quả
TC-ADJ-01, 02, 03, 04, 08: xanh (xem `docs/rtm-testref/FEAT-028.md` và `implementation-log.md`). Không gọi AI.

## 7. Giới hạn đã biết
- ASM-028-01..11 (`docs/decisions/assumptions/FEAT-028.md`); `docs/golden/` không có hàm BR-ADJ-*, số mong đợi từ test-cases.md.
- Tác động ước tính chưa tính lại phân bổ cấp 2; số chính xác ở kịch bản FEAT-029.
- Dịch vụ cận lâm sàng: quy tắc chỉ xét dòng định mức thường, chưa có quy tắc theo hệ thống xét nghiệm.
- Dữ kiện thiết bị, mặt hàng tương đương, bấm giờ đọc từ dữ liệu sống nên lần tính "Đã khóa" cũ có thể cho giá trị hiện tại khác lúc tính.
- Giao diện chưa kiểm bằng trình duyệt (chỉ test tĩnh và build).
