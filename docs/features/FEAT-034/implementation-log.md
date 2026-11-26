# FEAT-034 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_norm_cls.py test_norm_templates.py test_norm_copy.py test_norm_validation.py`; `grep -rn "import frappe" normcore/norm/` | 86 passed; grep không in gì | 48a0bb0 |
| T02 | `check_conventions.py` rc 0; `with_bench.sh 'migrate && run-tests --module normcore.tests.test_permissions'`; `build_rtm.py` | OK (3 tests); VAN DE: 0 | 7be1c05 |
| T03 | `with_bench.sh 'migrate && run-tests --module` nc_norm_template, nc_norm_set, nc_test_system, nc_costing_run`; thêm api.test_norm, test_service, test_ai, nc_equipment, nc_audit_event, test_feat_039, test_form_actions, test_feat_001 | OK cả 12 module (10+17+13+5 test; các module thêm đều OK); test cũ không sửa | 574731f |
| T04 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_norm_cls && ... normcore.api.test_norm'` | OK (5 + 32 test). Phần 'bộ thiếu hệ thống không xác nhận được' của TC-CLS-29 làm ở T06 (cần set_blockers trong confirm_set) | 19d6366 |
| T05 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_norm_cls && normcore.api.test_norm'`; `pytest normcore/tests/golden/test_norm_golden.py` | OK (10 + 32); golden 4 passed. Lệch thiết kế: `export_norm_set` không đưa vào `actions` (test cũ test_quyen_norm_set_auditor_chi_doc đòi `actions` của Auditor rỗng, không sửa test): ASM-034-24, giao diện luôn hiện nút Xuất | 3376f65 |
