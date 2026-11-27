# As-Built: FEAT-029 Kịch bản điều chỉnh và yêu cầu sửa quy trình
- Phiên bản app 0.0.1, hiện thực bởi Dev (Multica NORM-83). Nghiệm thu độc lập: QA (chưa thực hiện lúc viết).

## 1. Luồng nghiệp vụ đã xây
UC-014 bước 4, 5, 6 (phần lặp), 4b; UC-007 1c. Ở Bàn so sánh giá (SCR-DSK-026), người có quyền quyết định (NC Finance, NC Director, Trưởng khoa của khoa dịch vụ) bấm Chấp nhận một gợi ý:
- BR-ADJ-001, 002, 004, 005: ghi một dòng NC Scenario Change vào kịch bản đang mở (tự tạo nếu chưa có) rồi tính lại toàn bộ kịch bản từ ảnh chụp của lần tính gốc bằng `snapshot.recompute`; không công thức mới. Lần tính gốc (kể cả "Đã khóa") không đổi.
- BR-ADJ-002, 004 (dòng định mức): thêm bộ định mức "Nháp" phiên bản kế tiếp mang giá trị mới, dòng đổi bỏ xác nhận, chờ xác nhận lại; có bộ "Nháp" thì dùng bộ đó; bộ "Đã xác nhận chuyên môn" thì chặn và hoàn tác.
- BR-ADJ-003 (đổi mặt hàng): không áp vào kịch bản hay bộ định mức; tạo NC Procedure Change Request, thông báo trưởng khoa. Trưởng khoa Tiếp nhận thì hệ thống tạo bản nháp quy trình kế tiếp (`create_revision`) kèm Comment đề xuất. Người dùng cũng đề xuất sửa quy trình tự do (kèm lý do).
- BR-ADJ-006, 007: chỉ ghi quyết định, kèm cảnh báo.

## 2. DocType tạo mới hoặc thay đổi
NC Scenario Change (bảng con, mới); NC Procedure Change Request (mới, `YCSQT-.YYYY.-.#####`); NC Costing Run thêm `based_on_run`, `scenario_changes` (không cần patch). Kịch bản chỉ ghi qua API (`flags.scenario_write`), không chạy, khóa, nhân bản. Giả định ASM-029-01..18 ở `docs/decisions/assumptions/FEAT-029.md`.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/scenario.py` (`get_open_scenario`, `create_scenario`, `accept_suggestion`, `request_procedure_change`, `change_request_actions`, `act_on_change_request`); `normcore/api/scenario_norm.py` (`version_for_adjustment`, ASM-029-18); `normcore/benchmark/scenario.py` (thuần); `api/price_compare.py` mở rộng (`decide_suggestion` Chấp nhận đi qua kịch bản, `is_scenario`, `can_request_change`). Giao diện: `PriceCompare.vue`, form/list NC Costing Run, NC Procedure Change Request, dải nhắc trên NC Clinical Procedure; bản dịch `translations/vi.d/FEAT-029.csv`. Scope rule `core/scope_rules/nc_procedure_change_request.json`. Không tác vụ nền.

## 4. Quyền và luồng trạng thái
NC Procedure Change Request theo dòng "Gợi ý, kịch bản, phương án giá" (`perm_matrix/nc_procedure_change_request.json`): Clinician không đọc, Auditor chỉ đọc, Trưởng khoa theo khoa (qua `procedure`), Finance tạo. Luồng: Mới → Đã tiếp nhận → Đã thực hiện; Mới/Đã tiếp nhận → Từ chối (cần lý do). Thao tác của Trưởng khoa là quyền qua API.

## 5. Cấu hình cần thiết khi triển khai
`NC Department.head_user` phải đặt để trưởng khoa nhận thông báo (thiếu thì có cảnh báo, không chặn). Cần quy trình "Đã ban hành" hoặc bộ định mức "Đã khóa" của dịch vụ.

## 6. Test case đã chạy và kết quả (mã TC)
TC-ADJ-05 (giá DV-TEST-A trong kịch bản 302.132,73 khớp golden; lần gốc không đổi), TC-ADJ-06, TC-ADJ-07 đạt. Lệnh và kết quả ở `docs/features/FEAT-029/implementation-log.md`. `accept_suggestion` trên bộ vàng chạy 0,16 đến 0,17 s.

## 7. Giới hạn đã biết và nợ kỹ thuật
- Đổi hệ số sử dụng thiết bị trong kịch bản ảnh hưởng mọi dịch vụ dùng thiết bị đó, kể cả khoa khác (đúng bản chất BR-ADJ-001).
- Lần gốc "Đã tính" dựng ảnh chụp từ dữ liệu sống: dữ liệu đổi sau lần tính thì giá kịch bản phản ánh cả thay đổi đó (có cảnh báo trên kịch bản).
- Chỉ dịch vụ thường (dòng cận lâm sàng không đổi theo thiết bị, ASM-029-05); `test_system` của bộ định mức nháp chỉ xử lý bộ không có hệ thống xét nghiệm.
- Không có ô nhập số tự do vào kịch bản ngoài gợi ý (ASM-029-14). Khóa kịch bản và phương án giá thuộc FEAT-030.
- Giao diện chưa kiểm bằng trình duyệt (chỉ test giao diện tĩnh và `bench build`).
