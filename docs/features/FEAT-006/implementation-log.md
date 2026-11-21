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
