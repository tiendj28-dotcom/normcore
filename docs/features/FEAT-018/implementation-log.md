# FEAT-018 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_costing_snapshot_lock.py normcore/tests/unit/test_costing_snapshot.py normcore/tests/unit/test_reconcile.py` | 34 passed (tệp FEAT-036, FEAT-017 không sửa) | 0580533 |
| T02 | `pytest normcore/tests/unit/test_costing_compare.py` | 12 passed | 3c87003 |
| T03 | `golden_engine.py` (+ `--no-depr`) thoát 0; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 985 passed; độ phủ 99,08%; TC-COST-09 (recompute), TC-COST-18 (−63.636,36) khớp golden | 3a5d484+ |
| T04 | `with_bench.sh 'migrate; run-tests --module ...test_nc_costing_run_lock/_allocation/test_nc_costing_run/test_nc_costing_cls'`; check_conventions | lock 6 OK, allocation 6 OK, run 15 OK, cls 7 OK | 519278a |
