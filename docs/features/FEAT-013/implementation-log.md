# FEAT-013 — Implementation log

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_norm_carry.py normcore/tests/unit/test_norm_validation.py normcore/tests/unit/test_norm_init.py`; `grep -rn "import frappe" normcore/norm/`; `python3 docs/tools/build_rtm.py docs` | 52 passed; grep không in gì; `VAN DE: 0`. Đã áp AMD-013-01 vào `docs/data-model.md` 3.5 và DI-04 | (xem commit T01) |
| T02 | `check_conventions.py`; `with_bench.sh "migrate && run-tests --module ...test_nc_norm_set"` | exit 0; Ran 17 tests OK | (xem commit T02) |
| T03 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_norm_version / api.test_norm / api.test_procedure_norm_flag'` | OK: 9 / 32 / 3 tests | (xem commit T03+T04) |
| T04 | test_quyen_new_version_* (cùng `test_norm_version`); `run-tests --module normcore.tests.test_permissions` | OK: 9 / 3 tests | (xem commit T03+T04) |
