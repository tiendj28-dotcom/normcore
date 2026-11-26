# FEAT-024 — Nhật ký hiện thực

Python dùng để chạy pytest: `~/frappe-bench/env/bin/python -m pytest` (python3 hệ thống không có pytest).

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_ai_citation.py --cov=normcore.ai.citation` | 5 passed, độ phủ 97%; `grep "import frappe"` không in gì |
| T02 | `pytest normcore/tests/unit/test_procedure_ai_draft.py --cov=normcore.procedure.ai_draft` | 7 passed, độ phủ 99%; không import frappe |
