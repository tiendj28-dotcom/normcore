# NORM-31 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest`.

- T01: `pytest normcore/tests/unit/test_import_excel_behavior.py` với `import_excel.js` của develop → 4 đỏ (N31-01 x2, N31-04, N31-05), 3 xanh (N31-02, N31-03, N31-06).
- T02: sau khi sửa `import_excel.js`, `pytest test_import_excel_behavior.py test_import_ui_conventions.py` → 9 xanh, consoleErrors rỗng.
- T03: test_N31_07 đỏ trước khi sửa (1 đỏ/11 xanh), sau khi thêm `DRIVER_LABELS` → `pytest test_allocation_rules.py` 12 xanh, `test_driver_errors` cũ không đổi.
- T04: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore --module ...test_nc_cost_center_driver'` → Ran 4 tests, OK (gồm test_N31_08).
- T05: `pytest test_accounting_import_behavior.py` với `nc_accounting_import.js` của develop → 4 đỏ (N31-09, N31-10 x2, N31-11).
- T06: sau khi sửa `nc_accounting_import.js` và thêm 3 khóa `vi.csv` → `pytest test_accounting_import_behavior.py test_accounting_ui_conventions.py test_vi_csv_order.py` 15 xanh.
- T07: golden_engine, golden_cls thoát 0; build_rtm `VAN DE: 0`; pytest unit+golden 297 xanh, độ phủ costing/benchmark 99%; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'` → Ran 634 tests, OK; check_conventions thoát 0.
