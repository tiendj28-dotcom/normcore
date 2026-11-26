# FEAT-015 — Implementation log

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest` test_costing_engine/rates/runner/labor/accumulation; `grep -rn "import frappe" normcore/costing/` (chỉ còn dòng docstring); `build_rtm.py docs` | 43 passed; VAN DE: 0; áp AMD-015-01, AMD-015-02 | 2a40be2 |
| T02 | `git diff origin/develop -- "*test*.py" \| grep -E "^-.*assert"` | rỗng; 9 chỗ: test_nc_audit_event.py, test_nc_costing_parameter_set.py, test_nc_costing_run.py, test_nc_test_system.py, test_feat_039.py (2), test_feat_001.py, test_form_actions.py, utils.py::make_chain_data; ASM-015-21 | b28f9b6 |
| T03 | golden_engine.py (+ --no-depr) thoát 0; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 594 passed, độ phủ costing 98,9% | 87ea5f3 |
| T04 | `check_conventions.py` thoát 0; `with_bench.sh migrate && run-tests --module ...test_nc_costing_run` OK (7 test, có TC_COST_19, khoa_dau_vao_khi_da_tinh); `...test_nc_equipment` OK (21) | xanh | e072b97 |
