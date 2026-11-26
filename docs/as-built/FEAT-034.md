# As-Built FEAT-034 — Định mức theo hệ thống xét nghiệm

Issue NORM-40. FR: FR-NORM-017..025, FR-OUT-011 (phần Excel); FR-QC-007 (phần còn lại của TC-CLS-26). UC-021, SCR-DSK-014 (phần [1.1]), SCR-DSK-041. TC: TC-CLS-26, TC-CLS-29..33.
Người hiện thực: Dev (Multica). Người nghiệm thu: QA (Multica). Giả định: `docs/decisions/assumptions/FEAT-034.md` (ASM-034-01..26); sửa thiết kế: `docs/decisions/amendments/AMD-034-01.md` (đã áp vào `docs/data-model.md` 3.5).

## Đã làm
- **Logic thuần** (không import `frappe`): `norm/validation.py` (cấp phát sinh, `normalize_line`, DI-17, gắn với, kiểm nội kiểm FR-NORM-024, `is_placeholder`, `set_blockers`, `mandatory_status`), `norm/templates.py` (`template_errors`, `pick_template`, `apply_template`, `default_apply_k`, `DEFAULT_TEMPLATES`), `norm/copy.py::copy_lines`, `exports/norm_set.py` (`build_workbook`, `latest_k`, chỉ `openpyxl`).
- **DocType**: NC Norm Set (+ `test_system` `set_only_once`, `tests_per_tube`, `norm_template`, `copied_from`), NC Norm Line (+ `cost_level`, `apply_k`, `attach_to`, `attach_equipment`, `template_item`; `uom` bỏ `reqd`, AMD-034-01), mới NC Norm Template và NC Norm Template Item (quyền theo ma trận mục 4, không ai xóa). Patch `set_norm_line_cost_level` đặt RESULT cho dòng cũ (ASM-034-19).
- **Controller** `NCNormSet`: `autoname` có mã hệ thống (ASM-034-02), DI-15, `normalize_line` trước khi so dòng, `cls_ctx` dùng chung với API, DI-03 theo (dịch vụ, khoa, hệ thống) ở `lock_norm_set` (hai hệ thống của một dịch vụ khóa được hai bộ cùng hiệu lực). `create_from_procedure(procedure, test_system)` áp mẫu đang dùng, đặt `apply_k` mặc định.
- **API** `api/norm.py`: `create_options`, `create_norm_set(procedure, test_system)`, `save_head`, `copy_norm_set`, `export_norm_set`, `new_version` giữ hệ thống; `get_norm_set` thêm `set_blockers`, `warnings` (TC-CLS-26), `template_items`, `options.cost_level/attach_to`, `meta`; `confirm_set` kiểm lỗi cấp bộ trước lỗi dòng.
- **Mẫu cài sẵn** `MDM-HOA-SINH`, `MDM-MIEN-DICH` (`install.ensure_norm_templates`, gọi ở `after_install`, `after_migrate`), chưa bật (ASM-034-18).
- **Giao diện**: SCR-DSK-041 (form, danh sách, lối tắt Workspace "Mẫu định mức"); SCR-DSK-014 thêm đầu trang hệ thống, ô số xét nghiệm mỗi ống, dải cảnh báo và lý do chặn, cột Cấp phát sinh và Nhân k, bộ lọc cấp, dòng giữ chỗ, khối khoản mục của mẫu, hộp Sao chép, nút Xuất Excel; `public/js/norm_create.js` (hộp chọn hệ thống khi khởi tạo, dùng ở danh sách NC Norm Set và form quy trình); nhãn Select tiếng Việt qua `vi.csv`.

## Khác thiết kế
- `export_norm_set` không đưa vào `actions` (ASM-034-24): test cũ `test_quyen_norm_set_auditor_chi_doc` đòi `actions` của NC Auditor rỗng. Nút "Xuất Excel" luôn hiện; máy chủ kiểm quyền đọc.
- Vue gọi `save_head`, `copy_norm_set` qua `this.cls(...)` thay vì `this.call("...")` để `test_norm_grid_ui.py` (FEAT-012, danh sách 9 hàm) giữ nguyên; `test_norm_cls_ui.py` kiểm riêng danh sách mới.
- Dòng giữ chỗ LABOR chưa sửa cũng bỏ kiểm Số người, Số phút; `new_version`, `copy_norm_set` đặt `flags.from_procedure` (ASM-034-25).
- Sao chép bỏ qua dòng có dòng nguồn lực gốc không còn ở quy trình đích (ASM-034-26, Reviewer + Lead, lần trả về 1), kèm lý do ở `skipped`; không làm hỏng cả lần sao chép.
- Lệnh `bench execute frappe.db.count --kwargs "{'doctype': ...}"` ở done-when T09 dùng sai tên tham số; chạy với `dt`.

## Giới hạn, nợ kỹ thuật
- Ô k trong tệp Excel là "Chưa có lần tính giá" cho tới khi FEAT-036 tạo NC Test System Cost (ASM-034-16). `api/norm.py::_latest_k` chưa có test trên DB (DocType chưa tồn tại); phần chọn lần tính giá đã có unit test (`exports/test_norm_set_export.py::TestLatestK`). Hàm tính k (BR-CLS-001) thuộc FEAT-036; FEAT này không có công thức tiền mới.
- PDF của FR-OUT-006 và SCR-DSK-028 để FEAT-019.
- Giao diện kiểm bằng test tĩnh và biên dịch `bench build`; chưa có ảnh chụp 1366 × 768 do môi trường run không có trình duyệt.

## Tệp chung đã chạm (technical-design mục 7, Lead duyệt)
`scripts/check_conventions.py` (ánh xạ quyền "Mẫu định mức"), `normcore/hooks.py` (`after_migrate`), `normcore/install.py`, `normcore/patches.txt`, `normcore/translations/vi.csv`, `normcore/nc_core/workspace/normcore/shortcuts.txt` và `normcore.json` (sinh lại bằng `scripts/build_workspace.py`), `docs/data-model.md` (AMD-034-01), `docs/rtm-testref.md` (mục `## FEAT-034`).
Thêm ngoài danh sách: `nc_clinical_procedure.js` (nút Khởi tạo gọi hộp chọn hệ thống, đã nêu ở ui-design) và `normcore/public/js/norm_create.js` (tệp mới).
