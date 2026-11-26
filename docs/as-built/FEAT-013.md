# As-Built FEAT-013 — Phiên bản bộ định mức theo quy trình mới

Issue NORM-51. FR: FR-NORM-015. UC-009 (luồng 1a, 9a), SCR-DSK-014. TC-NORM-08 (sau TC-WF-06).
Người hiện thực: Dev (Multica). Người nghiệm thu: QA (Multica), 2026-11-26 (verdict accepted, commit 275b3dc).

## Đã làm
- **Logic thuần** `normcore/norm/init_from_procedure.py`: `carry_lines`, `steps_without_lines`, `removed_flag`, `format_note`; `normcore/norm/validation.py`: DI-04 bỏ qua dòng `step_removed`, `confirm_blockers` thêm lý do "Thuộc bước đã bỏ".
- **NC Norm Line.step_removed** (Check, chỉ đọc, mặc định 0; AMD-013-01, đã áp `docs/data-model.md` 3.5 và DI-04). Controller `NCNormSet.validate_lines` chuẩn hóa cờ ở mọi đường ghi: chỉ `new_version` đặt được; gán bước hợp lệ hoặc Chung thì cờ gỡ.
- **API** `normcore/api/norm.py`: `new_version` hai nhánh (có quy trình "Đã ban hành" mới hơn: bộ Nháp mới mang dòng, đánh dấu dòng bước đã bỏ, trả `steps_without_lines`, ghi Comment; không có: giữ hành vi FEAT-012); `get_norm_set` thêm `step_removed`, nhóm "Bước đã bỏ", `steps_without_lines`, `doc.newer_procedure`, `actions.new_version`; `delete_line` xóa được dòng có cờ; `confirm_line` chặn dòng có cờ.
- **Giao diện** `NormGrid.vue`: nút "Tạo phiên bản theo quy trình mới", dải "Thay đổi theo quy trình mới" (`role="status"`, chip bước chưa có dòng), nhóm và nhãn "Bước đã bỏ", ô "Gắn với" và nút xóa cho dòng có cờ; form NC Norm Set thêm dòng dẫn; chuỗi mới ở `vi.csv`.

## Khác thiết kế
- Hộp kết quả sau khi tạo dùng `frappe.msgprint` rồi mở lưới của bộ mới.
- Giao diện chưa kiểm bằng trình duyệt thật (mã chưa có trên staging; QA kiểm qua test `test_norm_grid_ui.py` và API `get_norm_set`). Cần xem lại trên staging sau khi merge.

## ASM, AMD
ASM-013-01..08 (`docs/decisions/assumptions/FEAT-013.md`, trạng thái "Áp dụng theo CLAUDE.md mục 6"); AMD-013-01.
