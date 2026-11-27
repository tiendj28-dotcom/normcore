# FEAT-026 — Nhật ký hiện thực

Python chạy pytest: `~/frappe-bench/env/bin/pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR.

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_reference.py --cov=normcore/benchmark --cov-report=term-missing --cov-fail-under=90`; `grep -n "import frappe" normcore/benchmark/reference.py` | 16 passed, độ phủ 100%; grep không in gì |
| T02 | `with_bench 'migrate && run-tests --doctype "NC Benchmark Facility"'`; `check_conventions.py` | 7 tests OK; conventions exit 0. Thêm `scripts/conventions/perm_matrix/nc_benchmark_facility.json` (NORM-60). Tên đơn vị thiếu báo ValidationError (trường đặt tên), 3 trường còn lại MandatoryError |
| T03 | `with_bench 'migrate && run-tests --doctype "NC CPI Index"'`; `check_conventions.py` | 5 tests OK; conventions exit 0. Thêm perm_matrix/nc_cpi_index.json |
| T04 | `with_bench 'migrate && run-tests --doctype "NC Benchmark Price"'` (và Facility) | 9 tests OK; 7 tests OK. Thêm `tests/benchmark_utils.py`, `perm_matrix/nc_benchmark_price.json`; `find_saved_duplicate` dùng chung với bộ nhập |
| T05 | `with_bench 'migrate && run-tests --module normcore.api.test_benchmark && run-tests --module normcore.api.test_importer'` | test_benchmark OK; **test_importer: 1 FAIL** `test_finance_thay_bo_nhap_va_import_file_qua_file_rieng_tu` — danh sách bộ nhập của NC Finance nay có thêm `nc_benchmark_price` (đúng ma trận: Finance W). Không sửa test cũ; chờ quyết định (xem bình luận). Sửa tối thiểu khung nhập: ASM-026-13 |
| T06 | `run-tests --module normcore.api.test_benchmark` | 9 tests OK (5 nhập + 4 API: so sánh, giá hiệu chỉnh, xác nhận, quyền) |
