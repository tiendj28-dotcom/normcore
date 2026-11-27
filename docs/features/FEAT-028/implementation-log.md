# FEAT-028 — Nhật ký hiện thực

Python chạy pytest: `~/frappe-bench/env/bin/pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR.

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_stats.py --cov=normcore/benchmark --cov-report=term-missing`; `grep -n "import frappe" normcore/benchmark/stats.py` | 11 passed, `stats.py` phủ 98%; grep không in gì |
