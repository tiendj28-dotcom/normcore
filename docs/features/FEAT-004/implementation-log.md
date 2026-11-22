# FEAT-004 — Nhật ký hiện thực (NORM-13)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_importer.py` | đỏ (không import được `normcore.core.importer`) → xanh: 17 passed (1 test sai dữ liệu test của chính mình đã sửa, không nới assertion) |
| T02 | `bench --site normcore.test run-tests --module normcore.api.test_importer` | OK, 6 tests (viết test và mã cùng lượt, không quan sát bước đỏ riêng) |
| T03 | `pytest -k import_ui`; `bench migrate` | xanh; Page `import-excel` và Workspace `Normcore` đã đồng bộ |
| T04 | `python3 docs/tools/build_rtm.py docs` | VAN DE: 0 |
| T05 | `pytest unit+golden`; `bench run-tests --app normcore`; `check_conventions.py`; `ruff` | 54 passed, cov costing 99%; bench 91 tests OK; conventions rc=0; ruff sạch |

Ghi chú môi trường: bench dùng chung có symlink `apps/normcore` trỏ workdir NORM-12; chạy bằng `PYTHONPATH=<workdir NORM-13>` để dùng mã nhánh này, không đổi symlink.

## Sửa theo Reviewer (PR #13 @ b3ec6b9)
| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T06 | `build_rtm.py docs` | VAN DE: 0; AMD-002 và `ux-foundations.md` đủ hai cột (Thành phần chính, Trạng thái) |
| T07 | `bench --site normcore.test run-tests --module normcore.api.test_importer` | trước sửa: 2 FAIL (message_log còn 1 thông báo; mã khác hoa/thường bị đếm "cập nhật"); sau sửa: Ran 8 tests, OK. Thêm `test_FR_ADM_002_loi_validate_cua_frappe_...`; đổi tên test cũ thành `..._loi_kieu_cua_dong` (không nới assertion) |
| T08 | tùy chọn Reviewer | `message_log` cắt về độ dài cũ; khóa loại khỏi `changed`; `str(key).casefold()`; ngữ cảnh "Import Excel" cho khóa dịch chung; As-Built mục 7 |
