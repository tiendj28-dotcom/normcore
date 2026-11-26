# FEAT-012 — Nhật ký hiện thực

Quyết định Lead (bình luận trên NORM-39, 2026-11-26): Q1 = PA1, Q2 = PA1, duyệt AMD-012-01/CF-012-01.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_norm_init.py test_norm_validation.py test_norm_workflow.py`; `grep -rn "import frappe" normcore/norm/`; `python3 docs/tools/build_rtm.py docs` | 34 passed; grep không in gì; VAN DE: 0 | (git log) |
| T02 | `pytest normcore/tests/unit/test_norm_provisional.py normcore/tests/golden/test_norm_golden.py --cov=normcore.costing.provisional`; `python3 docs/golden/golden_engine.py` | 11 passed; phủ provisional.py 100%; golden thoát 0 | (git log) |
| T03 | Q1=PA1, Q2=PA1 (Quyết định Lead, NORM-39). Thêm `tests/utils.py::confirm_norm_set`; chèn 1 dòng `confirm_norm_set(ns)` trước `lock()` ở 12 chỗ: `nc_audit_event/test_nc_audit_event.py` (1), `nc_costing_run/test_nc_costing_run.py` (4), `nc_test_system/test_nc_test_system.py` (3), `nc_norm_set/test_nc_norm_set.py` (3), `api/test_ai.py` (1); mỗi tệp thêm tên vào dòng import. `git diff origin/develop -- '*test*.py' \| grep -E '^-.*assert'` | không in gì; chỉ dòng import bị thay | (git log) |
| T04 | `python3 scripts/check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_norm_set.test_nc_norm_set'`; chạy toàn bộ `run-tests --app normcore` | conventions rc=0; module 17 OK (có test_TC_NORM_10/07/04 mức `doc.save()`, `frappe.client.set_value` trên bộ khóa bị từ chối); toàn bộ 1076 test: 1 đỏ có chủ ý (xem dưới), `test_service` đã sửa mã (không sửa test) và xanh | (git log) |

**Test đỏ có chủ ý, chờ người duyệt:** `nc_audit_event/test_nc_audit_event.py::test_FR_AUD_001_khoa_bo_dinh_muc` khẳng định `(from_state, to_state) == ("Nháp", "Đã khóa")`. Sau Q1 khóa chỉ từ "Đã xác nhận chuyên môn" nên bản ghi kiểm toán là `("Đã xác nhận chuyên môn", "Đã khóa")`. Dòng này nằm ngoài 12 chỗ Lead duyệt (điều kiện (b): không đổi `assert`) → không sửa, hỏi Lead (ASM-012-17).
