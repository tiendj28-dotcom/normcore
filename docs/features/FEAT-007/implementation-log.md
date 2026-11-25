# FEAT-007 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_procedure_validation.py`; `grep -n "import frappe" normcore/procedure/validation.py` | 8 passed; grep không in gì | (xem git log) |
| T02 | `pytest normcore/tests/unit/test_procedure_approval.py`; grep import frappe | 10 passed; không import frappe | (git log) |
| T03 | `scripts/with_bench.sh 'bench pip install python-docx'`; `pytest normcore/tests/unit/test_procedure_printing.py` | python-docx 1.2.0 cài, exit 0; 5 passed | (git log) |
| T04 | `build_rtm.py docs`; `with_bench.sh 'migrate && run-tests --module normcore.tests.test_feat_007_workflow'` | VAN DE: 0; 6 tests OK | (git log) |
| T05 | `git diff origin/develop -- '*test*.py' \| grep -E '^-.*assert'` (rỗng); `with_bench.sh 'migrate && run-tests --module <8 module>'` | không dòng assert nào bị đổi/xóa; 8 module OK (15, 5, 9, 8, 20, 8, 14, 21 test) | (git log) |

Dòng dựng dữ liệu đã đổi ở T05 (ASM-007-16): `tests/utils.py` (thêm `to_state`, `publish_procedure`; `make_chain_data` dùng helper thay `flags.allow_publish`), `test_feat_001._publish`, `test_nc_audit_event._publish`, `test_nc_costing_run._published_norm_set`, `test_nc_norm_set._published` và `test_nguon_luc_nhan_luc_chua_gan_chuc_danh_bi_tu_choi`, `test_feat_039` (TC_AUD_03), `test_form_actions._published_procedure`, `api/test_procedure` (2 chỗ). Ba test ban hành của `test_nc_clinical_procedure` đưa quy trình về "Chờ ban hành" bằng `to_state` rồi gọi `publish()` thật.
| T06 | `grep -rn allow_publish normcore` (rỗng); `with_bench.sh 'migrate && run-tests --module ...test_nc_clinical_procedure'` | OK 17 test, gồm `test_TC_WF_03_*` (5 trạng thái, form + `api.procedure.update_step`). Ghi chú: `publish()` gọi `apply_action` nên chạy cùng `api/procedure_workflow.py` của T07 (commit liền sau) | (git log) |
| T07 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_procedure_workflow'` | OK 9 test: TC_PROC_05, TC_PROC_06, TC_WF_01 (+ca âm), TC_WF_02 (3 cấp), quyền Auditor, Finance | (git log) |
