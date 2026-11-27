# FEAT-038 — Nhật ký hiện thực

Bench qua `scripts/with_bench.sh`. pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest`.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T02 (làm trước T01 vì fixture của T01 cần tài liệu của hãng) | `pytest normcore/tests/unit/test_library_manufacturer.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module …test_nc_legal_document_manufacturer && … --module …test_nc_legal_document'`; `check_conventions.py` | pytest 3 passed; bench OK (3 test) và OK (19 test); conventions thoát 0 | xem `git log` (`FEAT-038 T02`) |
| T01 (tệp DocType nằm trong commit T02) | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_ai_norm_suggestion.test_nc_ai_norm_suggestion'`; `check_conventions.py` | bench OK (4 test); conventions thoát 0. `build_rtm.py` chạy ở T08 | `FEAT-038 T02` |
| T03 | `pytest normcore/tests/unit/test_ai_cls_norm.py --cov=normcore/norm/ai_cls_norm.py --cov-fail-under=90`; `grep -n "import frappe" normcore/norm/ai_cls_norm.py`; `pytest normcore/tests/unit -q` | 8 passed, độ phủ `ai_cls_norm.py` 100%; grep rỗng; unit 1100 passed (cập nhật `SCOPED` của `test_scope_registry.py`, ASM-038-15) | `FEAT-038 T03` |
| T04 | `scripts/with_bench.sh 'bench --site normcore.test migrate && … run-tests --module normcore.api.test_cls_norm_ai && … --module normcore.nc_ai.doctype.nc_prompt_template.test_nc_prompt_template'` | OK (2 test) và OK (6 test) | `FEAT-038 T04` |
| T05 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_cls_norm_ai'`; `grep -rn "NC AI Norm Suggestion" normcore/costing normcore/nc_costing/doctype/nc_costing_run` | OK (13 test); grep rỗng | `FEAT-038 T05` |
| T06 | `scripts/with_bench.sh 'bench --site normcore.test migrate && … run-tests --module` `normcore.api.test_cls_norm_ai`, `normcore.api.test_norm`, `normcore.api.test_norm_cls`, `normcore.nc_costing.doctype.nc_qc_plan.test_nc_qc_plan` | OK (20), OK (32), OK (19), OK (14) | `FEAT-038 T06` |
