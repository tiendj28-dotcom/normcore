# FEAT-024 — Nhật ký hiện thực

Python dùng để chạy pytest: `~/frappe-bench/env/bin/python -m pytest` (python3 hệ thống không có pytest).

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_ai_citation.py --cov=normcore.ai.citation` | 5 passed, độ phủ 97%; `grep "import frappe"` không in gì |
| T02 | `pytest normcore/tests/unit/test_procedure_ai_draft.py --cov=normcore.procedure.ai_draft` | 7 passed, độ phủ 99%; không import frappe |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench ... run-tests --module normcore.api.test_procedure_ai && ... test_nc_ai_log && ... test_nc_ai_settings && ... test_nc_prompt_template'` | 2, 4, 9, 6 tests, OK cả bốn. Lệch thiết kế: không patch/after_install cho v2, gọi lười (ASM-024-15) vì test_nc_prompt_template cũ |
