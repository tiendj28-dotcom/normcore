# FEAT-006 — Nhật ký hiện thực (NORM-11)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T00 | commit tài liệu thiết kế | `technical-design.md`, `ui-design.md`, `tasks.md` |
| T01 | `pytest normcore/tests/unit -k TC_PROC_03 -v` | 2 passed (viết test trước: lỗi thu thập vì chưa có module) |
| T02 | `bench migrate`; `run-tests --module ...test_nc_clinical_procedure`; `--module normcore.tests.test_permissions` | OK (13 test; 3 test) |
| T03–T07 | `bench --site normcore.test run-tests --module normcore.api.test_procedure` | OK, 20 tests (viết test trước, đỏ; sửa: idx khi sắp lại, `ignore_version=False`, kiểu số trong Version) |
| T08 | `pytest normcore/tests/unit`; `bench build --app normcore` | 41 passed; build thành công |
| T09 | `python3 docs/tools/build_rtm.py docs` | VAN DE: 0 |
| T10 | xem bình luận NORM-11 | pytest 41 passed, bench 108 tests OK, check_conventions thoát 0 |

**Ngoại lệ Q4**: `normcore/tests/test_permissions.py::test_co_14_doctype_va_10_vai_tro` đổi thành `test_co_15_doctype_va_10_vai_tro`, 14 → 15 vì thêm DocType NC Procedure Citation. Người duyệt cho phép ngày 2026-11-21.

**Sửa fixture (ASM-025)**: `normcore/tests/utils.py::make_procedure` đặt `flags.ignore_single_active` vì `test_form_actions` (cũ, giữ nguyên) tạo nhiều bản nháp cùng (dịch vụ, khoa) và va DI-02 mới. Không sửa assertion nào.

## Gỡ xung đột với develop (sau PR #14, FEAT-001)
Merge `origin/develop` vào nhánh (không rebase, không force). Ba tệp xung đột:
- `docs/decisions/assumptions.md`: develop dùng ASM-026..045, FEAT-006 dùng ASM-017..025 → **không trùng số**, giữ cả hai, không đánh lại. Bảng số cũ → số mới: không có thay đổi.
- `normcore/translations/vi.csv`: lấy hợp hai bên (86 dòng), không có khóa trùng khác bản dịch, không bỏ dòng nào của develop.
- `normcore/tests/test_permissions.py`: develop đã có 15 DocType (tên test còn ghi 14). Cộng đúng 1 DocType của FEAT-006 (NC Procedure Citation) → 16; đổi tên `test_co_14_...` thành `test_co_16_doctype_va_10_vai_tro`, số 15 → 16. Không đổi assertion nào khác. Đây là mở rộng ngoại lệ Q4 (đổi số DocType) do thêm bảng con mới.
- Sau merge, 13 test của lớp `TestProcedureEditorAPI` (mới của FEAT-006) đỏ vì `PermissionError` khi Clinician tạo quy trình: FEAT-001 chỉ cho Clinician ghi ở khoa được gán. Sửa `setUp` của lớp này (thêm `access.assign_department`); không đổi test cũ hay assertion.

## NORM-15 (sửa design-defect: trích dẫn lưu văn bản và mục)
| Việc | Lệnh | Kết quả |
| :-- | :-- | :-- |
| Thêm `legal_document`, `legal_section`; API, Vue, vi.csv, ASM-046 | `bench --site normcore.test run-tests --app normcore` | Ran 148 tests, OK |
| Sửa theo review: TC-PROC-09 kiểm đủ 4 thuộc tính cho cả trích dẫn bước và phần; kiểm sao chép mang theo hai trường (chỉ thêm kiểm) | `bench --site normcore.test run-tests --module normcore.api.test_procedure` | xem bình luận NORM-15 |
| Định dạng | `ruff format --check normcore scripts` | xem bình luận NORM-15 |
| NORM-22: G1 (nút tạo/sao chép ẩn khi không có quyền tạo), K3 (tiêu điểm sau khi busy false), C4 (placeholder `--text-muted`), AMD-005, ASM-063; test `TestEditorFeat006Fixes` | pytest unit+golden 94 passed, độ phủ 99%; `bench --site normcore.test migrate && run-tests --app normcore` Ran 185 tests OK; `bench build --app normcore` OK; check_conventions, golden, build_rtm thoát 0 | Đạt; K3 và G1 phần hiển thị cần người duyệt bấm trên trình duyệt |
