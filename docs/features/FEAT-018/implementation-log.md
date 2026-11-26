# FEAT-018 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_costing_snapshot_lock.py normcore/tests/unit/test_costing_snapshot.py normcore/tests/unit/test_reconcile.py` | 34 passed (tệp FEAT-036, FEAT-017 không sửa) | 0580533 |
| T02 | `pytest normcore/tests/unit/test_costing_compare.py` | 12 passed | 3c87003 |
| T03 | `golden_engine.py` (+ `--no-depr`) thoát 0; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 985 passed; độ phủ 99,08%; TC-COST-09 (recompute), TC-COST-18 (−63.636,36) khớp golden | 3a5d484+ |
| T04 | `with_bench.sh 'migrate; run-tests --module ...test_nc_costing_run_lock/_allocation/test_nc_costing_run/test_nc_costing_cls'`; check_conventions | lock 6 OK, allocation 6 OK, run 15 OK, cls 7 OK | 519278a |
| T05 | `with_bench.sh 'migrate; run-tests --module normcore.api.test_costing_lock / test_costing / test_costing_reconciliation'`; đo khóa 500 dịch vụ (dữ liệu `test_costing_perf`, đo một lần, tệp đo tạm đã xóa) | lock 4 OK, costing 11 OK, reconciliation 4 OK; khóa 500 dịch vụ: 15,4 s (< 120 s, ASM-018-11); `lock_run` giữ nguyên `{"status"}` vì test FEAT-017 so khớp chính xác (hash qua `get_run_results`, ASM-018-13) | 9f78205 |
