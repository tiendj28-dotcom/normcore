# FEAT-026 — Nhật ký hiện thực

Python chạy pytest: `~/frappe-bench/env/bin/pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR.

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_reference.py --cov=normcore/benchmark --cov-report=term-missing --cov-fail-under=90`; `grep -n "import frappe" normcore/benchmark/reference.py` | 16 passed, độ phủ 100%; grep không in gì |
