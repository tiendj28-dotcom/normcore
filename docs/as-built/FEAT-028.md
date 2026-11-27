# As-Built: FEAT-028 Bàn so sánh giá
- Phiên bản app 0.0.1, ngày nghiệm thu 2026-11-27, người nghiệm thu: QA (Multica)

## 1. Luồng nghiệp vụ đã xây
UC-014 bước 1–3, 2a, 2b, 4a. Từ lần tính giá, trang `price-compare` (SCR-DSK-026) liệt kê dịch vụ với giá thấp nhất, trung vị, cao nhất của đơn vị tham chiếu và độ lệch %. Giá tham chiếu lấy từ dòng "Đã xác nhận" (FEAT-026), mỗi đơn vị một giá mới nhất trong cửa sổ `price_valid_months` (mặc định 24, ASM-028). Dưới ngưỡng số đơn vị: nhãn "Chưa đủ dữ liệu so sánh", không sinh gợi ý. Vượt ngưỡng lệch: sinh gợi ý theo quy tắc BR-ADJ-001..007 (không dùng AI), xếp theo tác động giảm dần; người dùng chấp nhận hoặc từ chối (từ chối cần lý do). Gợi ý cần sửa quy trình chỉ chấp nhận được ở FEAT-029 (bị chặn ở đây). Chi tiết cơ cấu giá hiển thị giá trị và tỷ trọng từng cấu phần, tổng bằng giá thành.

## 2. DocType tạo mới hoặc thay đổi
NC Adjustment Suggestion (mới): quy tắc, mục tiêu, giá trị hiện tại/đề xuất, hướng, tác động ước tính, trạng thái, người và thời điểm quyết định, lý do từ chối. Chỉ sửa qua API (`test_sua_ngoai_api_bi_chan`). Giả định ASM-028-01..12 ở `technical-design.md`.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/price_compare.py`: `get_comparison`, `get_service_detail`, `generate_suggestions`, `decide_suggestion`; mở rộng `api/benchmark.py`. Python thuần: `benchmark/stats.py`, `benchmark/rules.py`. Trang `nc_benchmark/page/price_compare`, `PriceCompare.vue`, nút từ NC Costing Run, shortcut workspace, bản dịch `translations/vi.d/FEAT-028.csv`.

## 4. Quyền và luồng trạng thái
Theo `perm_matrix/nc_adjustment_suggestion.json`: Clinician không đọc, Auditor chỉ đọc, Trưởng khoa theo khoa, Finance tạo. Trạng thái gợi ý: mới → Chấp nhận / Từ chối.

## 5. Cấu hình cần thiết khi triển khai
Ngưỡng độ lệch và số đơn vị tối thiểu đọc từ NC Costing Parameter Set; `price_valid_months` mặc định 24. Cần bộ giá tham chiếu "Đã xác nhận" (FEAT-026).

## 6. Test case đã chạy và kết quả (mã TC)
TC-ADJ-01, 02, 03, 04, 08 đạt (pytest 1228 passed; site sạch 2088 test OK; rules.py phủ 100%). Chi tiết ở `docs/features/FEAT-028/acceptance.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- Giao diện SCR-DSK-026 chưa kiểm bằng trình duyệt (staging chưa có nhánh); chỉ có test giao diện tĩnh `test_feat_028_ui.py` và test API theo vai trò.
- Golden không có hàm BR-ADJ-* ngoài 001, 007, 008; số mong đợi lấy từ `test-cases.md`.
- FR-ADJ-006, 007, 009 (kịch bản điều chỉnh, yêu cầu sửa quy trình) thuộc FEAT-029.
