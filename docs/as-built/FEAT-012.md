# As-Built FEAT-012 — Bộ định mức theo bước: khởi tạo, sửa, xác nhận, khóa

Issue NORM-39. FR: FR-NORM-001..014, FR-NORM-016. UC-009, SCR-DSK-013, SCR-DSK-014. TC-NORM-01..07, 09..12.
Người hiện thực: Dev (Multica). Giới hạn: giao diện chưa kiểm bằng trình duyệt (chỉ kiểm tĩnh và `bench build`); `test_FR_AUD_001_khoa_bo_dinh_muc` đỏ có chủ ý chờ Lead (ASM-012-17).

## Đã làm
- **Logic thuần** `normcore/norm/` (khởi tạo từ quy trình, `line_errors`, `duplicates`, `confirm_blockers`, `effective_parameter_set`, `TRANSITIONS`) và `normcore/costing/provisional.py` (chi phí tạm tính; lượng áp dụng qua `engine.applied_qty`, 11 dòng DV-TEST-A khớp `golden_engine.direct_lines`).
- **NC Norm Set / NC Norm Line** mở rộng (không tạo lại): trường mới theo technical-design 2.1, 2.2; `resource` không còn `reqd` (AMD-012-01, CF-012-01; đã áp `docs/data-model.md` 3.5).
- **Controller** `NCNormSet.validate`: khóa nội dung ("Đã khóa", "Đã thay thế", "Đã xác nhận chuyên môn"), chuyển trạng thái chỉ qua `flags.norm_action`, kiểm dòng cho mọi đường ghi (form, `frappe.client`, API), sửa dòng thì xóa xác nhận của dòng đó. `lock()` chỉ từ "Đã xác nhận chuyên môn".
- **API** `normcore/api/norm.py`: `create_norm_set`, `get_norm_set`, `save_line`, `delete_line`, `confirm_line`, `confirm_set`, `return_set`, `lock_set`, `new_version`.
- **Giao diện**: SCR-DSK-013 (`nc_norm_set_list.js`, nút "Khởi tạo bộ định mức"), form NC Norm Set (bảng dòng chỉ đọc, nút "Mở lưới định mức"), nút khởi tạo trên form quy trình gọi `create_norm_set`, SCR-DSK-014 trang Vue `norm-grid` (lưới nhóm theo bước, sửa tại chỗ, thêm dòng, xác nhận, hộp hành động, khối chi phí tạm tính).

## Khác thiết kế
- Form NC Norm Set giữ nút "Khóa" (chỉ NC Finance, chỉ ở "Đã xác nhận chuyên môn") thay vì bỏ hẳn, vì `test_form_buttons_i18n` buộc chuỗi "Lock" còn trong các JS form và không được sửa test.
- Dòng của bộ mới khởi tạo từ quy trình được lưu dù chưa liên kết; dòng thêm tay phải đủ nguồn lực ngay (`changed` khi `insert` = không có `procedure_resource_row`).

## Nợ kỹ thuật, ghi chú
- Các trường [1.1] (FEAT-034), FR-NORM-015 (FEAT-013), đề xuất AI (FEAT-025), cờ `needs_update` (FEAT-008) chưa làm; trường đã có để mở rộng.
- Test đỏ có chủ ý, chờ Lead: `nc_audit_event/test_nc_audit_event.py::test_FR_AUD_001_khoa_bo_dinh_muc` (assert từ-trạng-thái "Nháp"; thực tế "Đã xác nhận chuyên môn" sau Q1).
- Chưa kiểm giao diện bằng mắt.

## ASM
ASM-012-01..17 (`docs/decisions/assumptions/FEAT-012.md`); AMD-012-01, CF-012-01. ASM-012-03, 04 theo Quyết định Lead trên NORM-39; ASM-012-17 chờ Lead.
