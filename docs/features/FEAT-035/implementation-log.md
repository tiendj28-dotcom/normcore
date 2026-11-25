# FEAT-035 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_cls_volume.py normcore/tests/unit/test_test_systems.py --cov=normcore/costing` | 49 passed; cls_volume.py 100%; không import frappe | (xem git log) |
| T02 | `pytest normcore/tests/unit` ; bench run-tests api.test_importer, _accounting, _test_system | 346 passed; 3 module bench OK (8, 4, 5 test) | (xem git log) |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module ...test_nc_test_system_volume'`; `check_conventions.py` | OK (9 test: DI-14, mặc định kịch bản, fetch, số âm, MandatoryError, NULL, Auditor, Clinician, Department Head); thoát 0 | (xem git log) |
| T04 | run-tests `test_nc_equipment_usage`, `test_nc_stock_issue_actual`, `normcore.tests.test_permissions`; `check_conventions.py` | OK (5, 3, 3 test); thoát 0 | (xem git log) |
