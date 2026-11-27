# FEAT-028 — Nhật ký hiện thực

Python chạy pytest: `~/frappe-bench/env/bin/pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR.

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_stats.py --cov=normcore/benchmark --cov-report=term-missing`; `grep -n "import frappe" normcore/benchmark/stats.py` | 11 passed, `stats.py` phủ 98%; grep không in gì |
| T02 | `pytest normcore/tests/unit/test_benchmark_rules.py --cov=normcore/benchmark --cov-report=term-missing`; `grep -n "import frappe" normcore/benchmark/rules.py` | 17 passed, `rules.py` phủ 100%; grep không in gì. Tác động DV-TEST-A (độ lệch +20,85, ngưỡng 10): BR-ADJ-001 EQ1 0,4→0,5 = −15.411,93; BR-ADJ-002 L04 20→15 phút = −5.218,93; BR-ADJ-005 5%→4% = −2.877,45; thứ tự 001, 002, 005 |
| T03 | `with_bench 'migrate && run-tests --module normcore.nc_benchmark.doctype.nc_adjustment_suggestion.test_nc_adjustment_suggestion'`; `check_conventions.py` | 8 tests OK; conventions exit 0. Tạo mới luôn ép status "Mới"; sửa/quyết định chỉ khi `flags.adj_system` / `flags.adj_decision` (API đặt) |
