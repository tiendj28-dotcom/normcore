# FEAT-010 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_resources.py normcore/tests/golden/test_resources_golden.py`; `grep frappe normcore/costing/resources.py` | 14 passed, 24 subtests; grep không in gì | c71cadb |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate && run-tests --module …nc_room.test_nc_room'` và `…nc_equipment_type`; `…tests.test_permissions` | thoát 0; Ran 7 OK; Ran 4 OK; Ran 3 OK (đếm DocType 18 → 20) | 15d7560 |
| T03 | `with_bench.sh 'migrate && run-tests --module …nc_costing_parameter_set.test_nc_costing_parameter_set && …nc_costing_run.test_nc_costing_run'` | Ran 3 OK; Ran 5 OK | b2ce2c2 |
| T04 | `with_bench.sh 'migrate && run-tests --module …nc_equipment.test_nc_equipment && …tests.test_permissions'`; `check_conventions.py` | Ran 14 OK; Ran 3 OK (đếm DocType 20 → 23); thoát 0 | 128f002 |
