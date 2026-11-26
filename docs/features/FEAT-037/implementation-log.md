# FEAT-037 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python3 hệ thống không có pytest).

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | pytest test_reconcile_physical.py test_reconcile.py | 18 passed; grep import frappe: không có (chỉ chuỗi trong docstring) | ae93402 |
| T02 | pytest test_reconcile_cls_golden.py; python3 docs/golden/golden_cls.py | 3 passed; golden thoát 0 | 821254e |
| T03 | pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90 | 1037 passed; coverage 98.89% | 02ba221 |
| T04 | with_bench migrate + run-tests --module ...test_nc_reconciliation_line; check_conventions.py | Ran 4 tests OK; conventions thoát 0 (bản dịch vi.d/37 thêm ở T09, ASM-037-xx: nhãn UI) | 26c0bcb |
