# FEAT-035 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_cls_volume.py normcore/tests/unit/test_test_systems.py --cov=normcore/costing` | 49 passed; cls_volume.py 100%; không import frappe | (xem git log) |
| T02 | `pytest normcore/tests/unit` ; bench run-tests api.test_importer, _accounting, _test_system | 346 passed; 3 module bench OK (8, 4, 5 test) | (xem git log) |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module ...test_nc_test_system_volume'`; `check_conventions.py` | OK (9 test: DI-14, mặc định kịch bản, fetch, số âm, MandatoryError, NULL, Auditor, Clinician, Department Head); thoát 0 | (xem git log) |
| T04 | run-tests `test_nc_equipment_usage`, `test_nc_stock_issue_actual`, `normcore.tests.test_permissions`; `check_conventions.py` | OK (5, 3, 3 test); thoát 0 | (xem git log) |
| T05 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_importer_cls_volume'` | OK (8 test: TC-CLS-34, 35 ×2, 36, phút khai thác, quyền Auditor/Director) | (xem git log) |
| T06 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --module normcore.api.test_importer'` (Quyết định Lead trên NORM-36, ASM-035-09) | OK (8 test; assertEqual đủ danh sách NC Finance, thêm 3 khóa) | (xem git log) |
| T07 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --module normcore.api.test_test_system'` | OK (8 test, có test mục volume empty→estimated/ok) | (xem git log) |
| T08 | `pytest normcore/tests/unit/test_cls_volume_ui_conventions.py normcore/tests/unit/test_vi_csv_order.py`; `check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore'` | 353 unit passed; conventions thoát 0; build thoát 0 | (xem git log) |
| T09 | `python3 docs/tools/build_rtm.py docs` | VAN DE: 0; As-Built, Test ref, ASM cập nhật | (xem git log) |
| T10 | golden_engine.py, golden_cls.py (thoát 0); `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`; check_conventions.py; build_rtm.py | 365 passed, coverage 99,03% (cls_volume 100%); bench Ran 736 tests OK; conventions thoát 0; VAN DE: 0 | (xem git log) |
