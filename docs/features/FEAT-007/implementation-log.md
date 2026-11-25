# FEAT-007 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_procedure_validation.py`; `grep -n "import frappe" normcore/procedure/validation.py` | 8 passed; grep không in gì | (xem git log) |
| T02 | `pytest normcore/tests/unit/test_procedure_approval.py`; grep import frappe | 10 passed; không import frappe | (git log) |
