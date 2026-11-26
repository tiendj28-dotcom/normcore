# As-Built FEAT-014 — Khảo sát bấm giờ

Issue NORM-49. FR: FR-TS-001..005, NFR-USE-003, phần bấm giờ của FR-ADM-003. UC-010, SCR-DSK-015, SCR-DSK-016. TC-TS-01..05, TC-NFR-05, TC-ADM-03 (phần bấm giờ).
Người hiện thực: Dev (Multica). Chưa qua QA.

## Đã làm
- **Logic thuần** `normcore/norm/time_study.py` (`lines_from_procedure`, `line_errors`, `median`, `collect`, `summarize`, `plan_apply`, `basis_ref`); không import frappe, phủ 100%.
- **DocType** NC Time Study và NC Time Study Line (module NC Costing), quyền theo dòng "Phiếu bấm giờ", phạm vi khoa qua `core/scope_rules/nc_time_study.json`. Controller tự chọn quy trình đã ban hành, nạp dòng theo bước, kiểm dòng ở mọi đường ghi. Không có trường định danh người bệnh.
- **API** `normcore/api/time_study.py`: `get_entry`, `get_result`, `apply_to_norm_set` (đọc số ca tối thiểu qua `core.settings.get`, không cache).
- **Giao diện**: SCR-DSK-015 (form + bảng ghi theo bước vào `entry_panel`), SCR-DSK-016 (Script Report `NC Time Study Result`, nút "Áp vào bộ định mức" kèm xác nhận thiếu ca), nút điều hướng "Áp kết quả bấm giờ" trên form NC Norm Set.
- `scripts/check_conventions.py`: thêm dòng ma trận "Phiếu bấm giờ" và ánh xạ hai DocType.

## Khác thiết kế
- AMD-014-01: không thêm nút "Áp kết quả bấm giờ" vào lưới định mức (`NormGrid.vue`) và không sửa `api/norm.py`; áp đi qua report. Nút trên form NC Norm Set chỉ điều hướng.
- ASM-014-12: `procedure` kiểm bắt buộc ở controller, không `reqd` ở meta (để Desk lưu được phiếu mới). Bảng con `lines` ẩn dưới 1200 px bằng class riêng `nc-ts-lines`, không dùng selector chung.
- ASM-014-11: thêm `NC Time Study` vào tập `SCOPED` của `test_scope_registry.py` theo Quyết định Lead.

## Nợ kỹ thuật, ghi chú
- **TC-NFR-05 (kiểm tay 768 px, ca 6 bước) và kiểm giao diện 1366 × 768 chưa thực hiện**: site preview (`~/preview-bench`) chưa được tạo nên `multica env start preview` không chạy. Mới có kiểm tĩnh (`unit/test_time_study_ui.py`: vùng chạm ≥ 44 px, `inputmode="decimal"`, `flex-wrap`, không chiều rộng > 768 px).
- Không lưu ngoại tuyến, không xóa phiếu (ASM-014-09).

## ASM
ASM-014-01..12 (`docs/decisions/assumptions/FEAT-014.md`); AMD-014-01. ASM-014-01, ASM-014-11 và ASM-014-12 theo Quyết định Lead.
