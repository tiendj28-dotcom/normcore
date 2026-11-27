# FEAT-027 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python hệ thống không có pytest).

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_pdf_extract.py normcore/tests/unit/test_benchmark_reference.py --cov=normcore/benchmark --cov-fail-under=90`; `grep -n "import frappe" normcore/benchmark/pdf_extract.py` | 7 test xanh cho pdf_extract; độ phủ `pdf_extract.py` 97%, gộp `benchmark/` ≥ 90%; grep không in gì | (xem git log) |
| T02 | `pytest normcore/tests/unit/test_guard_price_list.py`; `pytest normcore/tests/unit -k guard` | 1 passed; 11 passed (test guard cũ không đổi) | (git log) |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && ... run-tests --module normcore.api.test_benchmark_ai && ... --module normcore.api.test_ai'` | `Ran 2 tests OK`; `Ran 6 tests OK` | (git log) |
| T04 | Sinh `bang_gia_4_dong.pdf`: `scripts/with_bench.sh 'bench --site normcore.test execute normcore.nc_benchmark.doctype.nc_benchmark_price.test_files.make_samples.run'` (wkhtmltopdf qua `frappe.utils.pdf.get_pdf`, 2 trang, 4 dịch vụ + tiêu đề + "Tổng cộng"). Test: `scripts/with_bench.sh 'bench ... migrate && ... run-tests --module normcore.api.test_benchmark_ai && ... --module normcore.api.test_benchmark'` | `Ran 7 tests OK`; `Ran 13 tests OK` | (git log) |
| T05 | `scripts/with_bench.sh 'bench ... migrate && ... run-tests --module normcore.api.test_benchmark_ai'`; `python3 scripts/check_conventions.py` | `Ran 9 tests OK`; check_conventions thoát 0 | (git log) |
| T06 | `pytest normcore/tests/unit/test_feat_027_ui.py normcore/tests/unit/test_feat_026_ui.py normcore/tests/unit/test_vi_csv_order.py`; `check_conventions.py`; `scripts/with_bench.sh 'bench ... migrate && bench build --app normcore'` | `22 passed`; thoát 0; build thoát 0 | (git log) |
| T07 | `python3 docs/tools/build_rtm.py docs` | "Must chua co TC: 0 \| moi: []"; hai tệp sinh lại không commit | (git log) |
