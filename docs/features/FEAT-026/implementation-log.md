# FEAT-026 — Nhật ký hiện thực

Python chạy pytest: `~/frappe-bench/env/bin/pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR.

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_reference.py --cov=normcore/benchmark --cov-report=term-missing --cov-fail-under=90`; `grep -n "import frappe" normcore/benchmark/reference.py` | 16 passed, độ phủ 100%; grep không in gì |
| T02 | `with_bench 'migrate && run-tests --doctype "NC Benchmark Facility"'`; `check_conventions.py` | 7 tests OK; conventions exit 0. Thêm `scripts/conventions/perm_matrix/nc_benchmark_facility.json` (NORM-60). Tên đơn vị thiếu báo ValidationError (trường đặt tên), 3 trường còn lại MandatoryError |
| T03 | `with_bench 'migrate && run-tests --doctype "NC CPI Index"'`; `check_conventions.py` | 5 tests OK; conventions exit 0. Thêm perm_matrix/nc_cpi_index.json |
