# FEAT-017: Nhật ký hiện thực (NORM-43)

Nhánh `feat/FEAT-017-allocation-reconcile`. Mỗi task một commit `FEAT-017 Tnn: …`. Mọi lệnh bench chạy qua `scripts/with_bench.sh`.

| Task | Việc đã làm | Lệnh và kết quả |
| :-- | :-- | :-- |
| T01 | `costing/allocation.py`, `costing/reconcile.py`; test đơn vị | `pytest normcore/tests/unit/test_allocation.py normcore/tests/unit/test_reconcile.py`: 29 passed. `grep -rn "^import frappe\|^from frappe" normcore/costing/` không in gì |
| T02 | `tests/golden/test_allocation_golden.py` (6 test, đầu vào lấy từ `golden_engine`) | `pytest normcore/tests/golden` xanh; `golden_engine.py`, `--no-depr`, `golden_cls.py` thoát 0; độ phủ `normcore/costing` 99,11% (allocation.py, reconcile.py 100%) |
| T03 | DocType NC Reconciliation Line; `allocation_warnings` (AMD-017-01, áp vào `data-model.md`); ma trận quyền qua `perm_matrix/nc_reconciliation_line.json` (ASM-017-12) | `check_conventions.py` thoát 0; `build_rtm.py docs`: `VAN DE: 0`; `with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.tests.test_permissions'`: Ran 3, OK |
| T04 | `loader.allocation_context`, `allocate_pools(results, actx)`, `_run`, `execute_costing`, `lock_costing`, `writer.write_reconciliation`, fixture `make_golden_allocation` | `…run-tests --module …test_nc_costing_run_allocation` Ran 6 OK; `…test_nc_costing_run` (test cũ, không sửa) Ran 13 OK |
| T05 | `get_reconciliation`, `save_explanation`, `lock_run`; mở rộng `get_run_results`, `get_explanation` | `…test_costing_reconciliation` Ran 4 OK; `…api.test_costing` Ran 8 OK |
| T06 | `tests/test_costing_perf.py` | Ran 1 OK. **Số đo thật (500 dịch vụ, 50.000 dòng): pha tính 8,1 s, pha ghi 37,7 s, tổng 45,8 s** (giới hạn 300 s). Không cần tối ưu `writer` |
| T07 | `nc_costing_run.js`; `vi.d/FEAT-017.csv`; `tests/unit/test_reconciliation_ui.py` | `pytest test_form_buttons_i18n test_ui_conventions test_vi_csv_order test_costing_ui test_reconciliation_ui`: 38 passed |
| T08 | Script Report `nc_reconciliation`, form, list | `…migrate; bench build --app normcore; …run-tests --module …nc_reconciliation.test_nc_reconciliation` Ran 1 OK |
| T09 | `docs/as-built/FEAT-017.md`, `docs/rtm-testref/FEAT-017.md`, ASM-017-12..14 | `build_rtm.py docs`: `VAN DE: 0` |
| T10 | Kiểm toàn bộ sau `git merge origin/develop` | Xem dưới |

## T10: kiểm toàn bộ
- `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py`: thoát 0 (cả `--no-depr`).
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`: 859 passed, 173 subtests; độ phủ 99,11%.
- `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`: Ran 1530 tests in 407s, OK.
- `python3 scripts/check_conventions.py`: thoát 0. `python3 docs/tools/build_rtm.py docs`: `VAN DE: 0`.
- `git diff origin/develop --stat -- '*test*.py'`: chỉ tệp mới (9 tệp, 942 dòng thêm); `git diff origin/develop -- '*test*.py' | grep -E '^-'` chỉ có dòng tiêu đề `---`.

## Ghi chú
- Tiến độ giữ thang 0–100% vì test cũ đòi `[50, 100]` (ASM-017-13).
- Ma trận quyền theo NORM-60 thay vì sửa `check_conventions.py` (ASM-017-12).
- Test site cần `bench migrate` ngay trong cùng lần gọi: bench dùng chung có thể mang lược đồ DocType của FEAT khác (gặp `NC Test System Cost` khi quên migrate).
