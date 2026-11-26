# FEAT-037 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python3 hệ thống không có pytest).

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | pytest test_reconcile_physical.py test_reconcile.py | 18 passed; grep import frappe: không có (chỉ chuỗi trong docstring) | ae93402 |
