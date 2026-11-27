# FEAT-030 — Implementation log

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_price_proposal_logic.py --cov=normcore.benchmark.proposal --cov-fail-under=90` (thấy đỏ khi chưa có module) | 15 passed, proposal.py phủ 97%; `grep "import frappe" proposal.py` rỗng | xem git log |
| T02 | `pytest normcore/tests/unit/test_scope_child.py normcore/tests/unit/test_scope_registry.py` | 12 passed (test scope cũ trên site chạy ở T03/T09) | xem git log |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_benchmark.doctype.nc_price_proposal.test_nc_price_proposal'`; `python3 scripts/check_conventions.py` | Ran 10 tests OK; check_conventions thoát 0. Lệch TD 2.7: bỏ DocPerm xóa của NC Finance (ASM-030-17, quy ước NC-08) | xem git log |
| T04 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_price_proposal && bench --site normcore.test run-tests --module normcore.api.test_price_compare'` | test_price_proposal: Ran 4 OK; test_price_compare: Ran 15 OK | xem git log |
| T05 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_price_proposal'` | Ran 14 tests OK (TC-PRICE-01..07, quyền hành động, lịch sử chỉ thêm, việc chờ) | xem git log |
| T06 | `pytest normcore/tests/unit/test_exports_price_comparison.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_price_proposal && bench --site normcore.test run-tests --module normcore.api.test_export'` | unit 4 passed; test_price_proposal Ran 15 OK (có TC-OUT-05); test_export Ran 7 OK | xem git log |
