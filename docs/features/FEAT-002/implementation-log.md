# FEAT-002 — Implementation log

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python hệ thống không có pytest).

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit` | 504 passed; `grep import frappe chain.py` rỗng | 95b5dd2 |
| T02 | `with_bench.sh 'migrate && run-tests --module ...test_nc_settings'`; `check_conventions.py` | 8 tests OK; conventions exit 0. Ghi chú: patch đặt ở `normcore/patches/` (theo quy ước sẵn có, không `v0_0/`); Frappe trả 0 cho Int trống nên `settings.is_unset` coi 0 là trống với tham số ≥ 1 | 262c6db |
