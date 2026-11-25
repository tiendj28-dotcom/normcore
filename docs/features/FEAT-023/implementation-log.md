# FEAT-023 — Nhật ký hiện thực

Điều chỉnh theo "Quyết định Lead" (NORM-55): ASM-023-04 chặn khi lũy kế > hạn mức (không phải ≥); đã sửa ASM và technical-design.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_ai_guard.py`; `grep -n "import frappe" normcore/ai/guard.py` | 10 passed (76 subtests); grep không in gì | (xem git log) |
| T02 | `pytest normcore/tests/unit/test_ai_prompts.py`; `grep -n "import frappe" normcore/ai/prompts.py` | 7 passed; grep không in gì | (xem git log) |
| T03 | `pytest normcore/tests/unit/test_ai_providers.py normcore/tests/unit/test_ai_providers_openai.py`; `git diff origin/develop -- normcore/tests/unit/test_ai_providers.py` | 15 passed; diff rỗng | (xem git log) |
