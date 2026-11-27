# FEAT-030 — Implementation log

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_price_proposal_logic.py --cov=normcore.benchmark.proposal --cov-fail-under=90` (thấy đỏ khi chưa có module) | 15 passed, proposal.py phủ 97%; `grep "import frappe" proposal.py` rỗng | xem git log |
| T02 | `pytest normcore/tests/unit/test_scope_child.py normcore/tests/unit/test_scope_registry.py` | 12 passed (test scope cũ trên site chạy ở T03/T09) | xem git log |
