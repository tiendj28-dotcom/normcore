# FEAT-027 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python hệ thống không có pytest).

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_benchmark_pdf_extract.py normcore/tests/unit/test_benchmark_reference.py --cov=normcore/benchmark --cov-fail-under=90`; `grep -n "import frappe" normcore/benchmark/pdf_extract.py` | 7 test xanh cho pdf_extract; độ phủ `pdf_extract.py` 97%, gộp `benchmark/` ≥ 90%; grep không in gì | (xem git log) |
