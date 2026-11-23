# FEAT-031 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_test_systems.py normcore/tests/unit/test_service_rules.py --cov=normcore/costing --cov-report=term`; `grep -n frappe normcore/costing/test_systems.py normcore/procedure/service_rules.py` | 21 passed; `costing/test_systems.py` phủ 100%; grep không in gì | T01_SHA |
| T02 | `with_bench.sh 'migrate && run-tests --module normcore.nc_procedure.doctype.nc_technical_service.test_nc_technical_service'` | Ran 19 OK (có `test_TC_CLS_20_*`, `test_TC_CLS_21_*`, `test_FR_SVC_010_*`, `test_FR_SVC_011_*`; test cũ xanh). `cls_group`, `result_unit` có dòng trống đầu để không mặc định "Hóa sinh" | T02_SHA |
