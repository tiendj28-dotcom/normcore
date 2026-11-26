# FEAT-012 — Nhật ký hiện thực

Quyết định Lead (bình luận trên NORM-39, 2026-11-26): Q1 = PA1, Q2 = PA1, duyệt AMD-012-01/CF-012-01.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_norm_init.py test_norm_validation.py test_norm_workflow.py`; `grep -rn "import frappe" normcore/norm/`; `python3 docs/tools/build_rtm.py docs` | 34 passed; grep không in gì; VAN DE: 0 | (git log) |
| T02 | `pytest normcore/tests/unit/test_norm_provisional.py normcore/tests/golden/test_norm_golden.py --cov=normcore.costing.provisional`; `python3 docs/golden/golden_engine.py` | 11 passed; phủ provisional.py 100%; golden thoát 0 | (git log) |
