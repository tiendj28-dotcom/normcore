# FEAT-032 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_qc_plans.py …/test_test_systems.py normcore/tests/golden/test_qc_plans_golden.py --cov=normcore.costing.qc_plans --cov-fail-under=90`; `grep -n frappe normcore/costing/qc_plans.py` | 48 passed; `qc_plans.py` phủ 97%; grep không in gì | 093a8bb |
| T02 | `with_bench.sh 'run-tests --module normcore.tests.test_feat_001 && run-tests --module …nc_test_system.test_nc_test_system'` | Ran 20 OK; Ran 13 OK (test cũ không sửa) | 9338379 |
| T03 | `check_conventions.py`; `with_bench.sh 'migrate && run-tests --module …nc_qc_plan.test_nc_qc_plan'`; `… --module normcore.tests.test_permissions` | thoát 0; Ran 14 OK (`test_TC_CLS_24_*`, `test_TC_CLS_25_*`, Auditor, vai trò không quyền, phạm vi khoa); test_permissions Ran 3 OK | 460b24f |
| T04 | `with_bench.sh 'migrate && run-tests --module …nc_eqa_program.test_nc_eqa_program'` | Ran 12 OK (`test_TC_CLS_24_*`, `test_TC_CLS_25_*` 50% + 40% bị từ chối, Auditor, vai trò không quyền) | 227a0d6 |
| T05 | `with_bench.sh 'run-tests --module normcore.api.test_qc_plan && run-tests --module normcore.api.test_test_system'` | Ran 9 OK (`test_TC_CLS_26_*`); Ran 7 OK (test FEAT-031 không sửa) | 9f1e345 |
| T06 | `with_bench.sh 'run-tests --module normcore.api.test_importer_qc_plan && run-tests --module normcore.api.test_importer'` | Ran 3 OK; Ran 8 OK | 3c17242 |
| T07 | `pytest …test_qc_plan_ui_conventions.py …test_test_system_ui_conventions.py …test_vi_csv_order.py`; `check_conventions.py`; `build_workspace.py --check`; `with_bench.sh 'migrate && bench build --app normcore'` | 20 passed; thoát 0; thoát 0; build thoát 0. Chưa xem giao diện trên trình duyệt | fc96b49 |
| T08 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0`; thêm `docs/as-built/FEAT-032.md`; ASM-032-01..10 chuyển "Đã áp dụng" | 6d56631 |
| T09 | `golden_engine.py && golden_cls.py`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore.costing --cov=normcore.benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py` | golden thoát 0; 357 passed, phủ 98,46%; bench Ran 740 OK; check thoát 0 | (commit T09) |
