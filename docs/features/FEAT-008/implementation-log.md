# FEAT-008 — Implementation log

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_procedure_versioning.py` | 6 passed | dbb8605 |
| T02 | `pytest normcore/tests/unit/test_procedure_diff.py` | 11 passed | 4449678 |
| T03 | `pytest normcore/tests/unit/test_procedure_approval.py` | xanh; test cũ không sửa, 3 test mới | d309bf6 |
| T04 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --app normcore --module normcore.api.test_procedure_revision'` | Ran 9 tests OK | bc786c7 |
| T05 | `scripts/with_bench.sh '... --module normcore.api.test_procedure_withdraw'` + `normcore.tests.test_feat_007_workflow` + `normcore.api.test_procedure_workflow` | 3 OK; 6 OK; 9 OK | cdfa7fc |
| T06 | `scripts/with_bench.sh 'bench --site normcore.test migrate && ... --module normcore.api.test_procedure_norm_flag'`; `python3 scripts/check_conventions.py` | 3 OK; quy ước xanh | 07ca37a |
| T07 | `scripts/with_bench.sh '... --module normcore.api.test_procedure_compare'` | 2 OK | 3661180 |
| T08 | `pytest normcore/tests/unit/test_feat_008_ui.py`; `scripts/with_bench.sh 'bench build --app normcore'` | 5 passed; build không lỗi | ec68e4e |
| T09 | `pytest normcore/tests/unit/test_feat_008_ui.py test_feat_007_ui.py test_procedure_editor_behavior.py`; `scripts/with_bench.sh 'bench build --app normcore'` | 29 passed; build không lỗi, bundle chứa ProcedureCompare. **Chưa** mở trang ở 1366 × 768 bằng trình duyệt (không có trình duyệt trong run này): bố cục dựa trên CSS (bảng cuộn ngang trong khung `nc-cmp__scroll`); để QA kiểm bằng Playwright theo ui-design mục 6 | 8e1c8cb |
| T10 | `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore && bench --site normcore.test run-tests --app normcore'`; `python3 scripts/check_conventions.py`; `python3 docs/tools/build_rtm.py docs` | golden OK; pytest 546 passed, coverage 98,64%; bench Ran 1074 tests OK; quy ước rc=0; build_rtm không thêm vấn đề mới (cảnh báo TC-CLS có sẵn) | 9dc435b |
