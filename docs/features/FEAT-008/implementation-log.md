# FEAT-008 — Implementation log

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_procedure_versioning.py` | 6 passed | dbb8605 |
| T02 | `pytest normcore/tests/unit/test_procedure_diff.py` | 11 passed | 4449678 |
| T03 | `pytest normcore/tests/unit/test_procedure_approval.py` | xanh; test cũ không sửa, 3 test mới | d309bf6 |
| T04 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --app normcore --module normcore.api.test_procedure_revision'` | Ran 9 tests OK | bc786c7 |
