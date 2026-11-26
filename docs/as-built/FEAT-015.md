# As-Built FEAT-015 — Tính chi phí trực tiếp, giá và bảng giải trình

Issue NORM-41. FR: FR-COST-001, 002, 003, 006, 007, 010, 015 (Should), 016. UC-012 (bước 1–4, 6). SCR-DSK-022, SCR-DSK-023. TC-COST-01, 04, 06, 07, 12, 13, 15, 17, 19.
Người hiện thực: Dev (Multica). QA (Multica) nghiệm thu 2026-11-26, commit đã kiểm cfcb1c8; quyền kiểm trên staging bằng Playwright, màn hình SCR-DSK-022/023 chưa xem được trên staging vì chưa deploy FEAT-015.

## Đã làm
- **Logic thuần** (`normcore/costing/`, không import `frappe`): `engine.py` mở rộng (không đổi hàm cũ): `NormLine`, `LineRate`, `CostLine`, `ServiceInput`, `PricingParams`, `direct_line`, `round_price` (BR-COST-014), `price_service` (BR-COST-012, 013), `cost_service` (có điểm cắm `extension`, ADR-017), `finish_service`, `group_explanation`; `rates.py` (đơn giá LABOR, vật chất, tiện ích, thiết bị, phòng; khấu hao bị loại theo BR-COST-016); `runner.py` (phạm vi, đủ điều kiện, ngưỡng chạy nền 50, vòng tính tất định, điểm cắm `allocate`).
- **DocType** mở rộng: NC Costing Run (`accounting_import`, `price_category`, hai bảng phạm vi, `progress`; `validate` bắt buộc đầu vào, lần nhập "Đã chốt", khóa đầu vào ngoài Nháp/Tính lỗi), NC Service Cost (volume, `direct_*`, `alloc_*`, giá), NC Service Cost Line (`allocation_rule`, `driver_value`, `driver_total`, `pool_amount`, `warning`); hai bảng con mới NC Costing Run Department, NC Costing Run Service (AMD-015-01).
- **Lớp CSDL** cạnh controller (AMD-015-02): `loader.py` (nạp theo lô), `writer.py`. `NCEquipment.indicative(..., include_depr=True)`.
- **Controller**: `run_costing(confirm_ineligible)`, `execute_costing`, chạy nền `queue="long"` kèm tiến độ và realtime `normcore_costing_progress`.
- **API** `normcore/api/costing.py`: `check_scope`, `start_costing`, `get_progress`, `get_run_results`, `get_explanation`.
- **Giao diện**: form và danh sách NC Costing Run (hộp xác nhận dịch vụ chưa khóa, tiến độ, bảng kết quả), form và danh sách NC Service Cost (đầu, ghi chú, khối giá, thanh cơ cấu, bảng trực tiếp nhóm theo cấu phần và bước, bảng phân bổ).
- **Quyền**: NC Service Cost theo dòng "Bảng giải trình của dịch vụ thuộc khoa" (Quyết định Lead Q2, ASM-015-22): trưởng khoa đọc trong khoa mình; `scope_rules/nc_service_cost.json`; `check_conventions.py` thêm một dòng MATRIX.
- **Test cũ**: thêm `**costing_run_inputs()` ở 9 chỗ dựng NC Costing Run (Quyết định Lead Q1, ASM-015-21); không đổi assert nào.

## Khác thiết kế
- `rate_source` của dòng LABOR là tên bộ tham số (không kèm chức danh) vì test cũ FEAT-000 đòi `== params.name` (ASM-015-23); chức danh nằm ở `resource_label`.
- `docs/data-model.md` mục 3 thêm hai dòng khai báo bảng con (cần để `test_permissions` khớp DocType với data-model).
- `tests/unit/test_scope_registry.py::SCOPED` thêm "NC Service Cost" (cập nhật danh sách theo CLAUDE.md mục 3 luật 1, Quyết định Lead Q2).

## Nợ kỹ thuật, ghi chú
- Giá thành ở FEAT này chưa gồm phân bổ cấp 1, cấp 2, đối soát (FEAT-017): `allocate_pools` trả rỗng, giao diện có dải cảnh báo (ASM-015-02). TC-COST-04, 06, 12 kiểm ở mức hàm thuần với phần phân bổ lấy từ golden (ASM-015-01).
- Khóa lần tính, ảnh chụp, nhân bản (FEAT-018) và các trường [1.1] (FEAT-036) chưa làm.
- Đơn giá tạm tính ở lưới định mức (FEAT-012, chọn đơn giá theo hôm nay, tiện ích theo mặt hàng) có thể lệch với lần tính (chọn theo `costing_date`, tiện ích kWh theo bộ tham số): ASM-015-05, 19.
- Giao diện chưa kiểm bằng trình duyệt ở bước Dev.

## ASM
ASM-015-01..23 (`docs/decisions/assumptions/FEAT-015.md`); AMD-015-01, AMD-015-02 (CF-015-01). ASM-015-21, 22 theo Quyết định Lead (bình luận trên NORM-41).
- Giao diện SCR-DSK-022/023 chưa xem được trên staging (staging chưa có FEAT-015); đã kiểm bằng test tĩnh và test API theo vai trò, quyền kiểm trên staging bằng Playwright.
