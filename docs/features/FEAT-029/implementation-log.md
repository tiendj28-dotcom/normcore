# FEAT-029 — Nhật ký hiện thực

Ghi chú môi trường: pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python hệ thống không có pytest); `--cov` dùng tên module `normcore.benchmark.scenario`.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_scenario.py --cov=normcore.benchmark.scenario --cov-report=term-missing` | 9 passed, độ phủ 98%; `grep -n "import frappe" normcore/benchmark/scenario.py` không in gì; `golden_engine.py` giá tính toán 302,132.73; `test_TC_ADJ_05_apply_thiet_bi_ve_golden` ra 302.132,73 | (T01) |
| T02 | `scripts/with_bench.sh 'bench --site normcore.test migrate && run-tests --module …test_nc_costing_scenario / …test_nc_costing_run / …test_nc_costing_run_lock'` | scenario 1 test OK; test_nc_costing_run 15 OK; test_nc_costing_run_lock 6 OK; `check_conventions.py` exit 0 | (T02) |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && run-tests --module …test_nc_procedure_change_request && …test_nc_adjustment_suggestion'` | 6 OK; 8 OK; `pytest normcore/tests/unit normcore/tests/golden` 1252 passed (gồm test_scope_registry với SCOPED thêm NC Procedure Change Request, ASM-029-15); `check_conventions.py` exit 0. Controller NC Adjustment Suggestion đã coi "Đã chuyển yêu cầu sửa quy trình" là đã quyết (FEAT-028), không phải sửa | (T03) |
