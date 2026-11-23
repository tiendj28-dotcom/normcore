# FEAT-031 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_test_systems.py normcore/tests/unit/test_service_rules.py --cov=normcore/costing --cov-report=term`; `grep -n frappe normcore/costing/test_systems.py normcore/procedure/service_rules.py` | 21 passed; `costing/test_systems.py` phủ 100%; grep không in gì | T01_SHA |
| T02 | `with_bench.sh 'migrate && run-tests --module normcore.nc_procedure.doctype.nc_technical_service.test_nc_technical_service'` | Ran 19 OK (có `test_TC_CLS_20_*`, `test_TC_CLS_21_*`, `test_FR_SVC_010_*`, `test_FR_SVC_011_*`; test cũ xanh). `cls_group`, `result_unit` có dòng trống đầu để không mặc định "Hóa sinh" | T02_SHA |
| T03 | `python3 scripts/check_conventions.py`; `with_bench.sh 'migrate && run-tests --module …nc_test_system.test_nc_test_system'`; `… --module normcore.tests.test_permissions` | thoát 0; Ran 10 OK (`test_TC_CLS_20_*`, `test_TC_CLS_22_*`, `test_FR_CLS_005_*`, Auditor, vai trò không quyền); test_permissions Ran 3 OK. Đổi `test_co_27_…` → `test_co_30_…` (27 → 30, docstring) theo Quyết định Lead (ASM-113) | T03_SHA |
| T04 | `with_bench.sh 'run-tests --module …nc_test_system.test_nc_test_system && run-tests --module …nc_costing_run.test_nc_costing_run'` | Ran 12 OK (có `test_TC_CLS_23_*`, `test_FR_SVC_011_*`); Ran 5 OK (test cũ) | T04_SHA |
| T05 | `with_bench.sh 'run-tests --module normcore.api.test_test_system'` | Ran 7 OK (khối tình trạng bốn mục, cảnh báo tổng tỷ trọng, Clinician khoa khác `PermissionError`, Auditor đọc, vai trò không quyền) | T05_SHA |
| T06 | `with_bench.sh 'run-tests --module normcore.api.test_importer_test_system && run-tests --module normcore.api.test_importer'` | Ran 5 OK (có `test_TC_CLS_23_*`, vai trò chỉ đọc, Auditor); test_importer cũ Ran 8 OK không cần sửa | T06_SHA |
