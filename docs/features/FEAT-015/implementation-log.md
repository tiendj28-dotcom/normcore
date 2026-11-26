# FEAT-015 — Implementation log

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest` test_costing_engine/rates/runner/labor/accumulation; `grep -rn "import frappe" normcore/costing/` (chỉ còn dòng docstring); `build_rtm.py docs` | 43 passed; VAN DE: 0; áp AMD-015-01, AMD-015-02 | 2a40be2 |
| T02 | `git diff origin/develop -- "*test*.py" \| grep -E "^-.*assert"` | rỗng; 9 chỗ: test_nc_audit_event.py, test_nc_costing_parameter_set.py, test_nc_costing_run.py, test_nc_test_system.py, test_feat_039.py (2), test_feat_001.py, test_form_actions.py, utils.py::make_chain_data; ASM-015-21 | b28f9b6 |
