# FEAT-016 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_accounting.py normcore/tests/unit/test_allocation_rules.py normcore/tests/golden/test_accounting_golden.py --cov=normcore.costing.accounting --cov=normcore.costing.allocation_rules --cov-fail-under=90`; `grep -n frappe` hai module | 36 passed, độ phủ 100%; grep không in gì | (T01) |
