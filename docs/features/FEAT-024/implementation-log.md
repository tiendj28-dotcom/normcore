# FEAT-024 — Nhật ký hiện thực

Python dùng để chạy pytest: `~/frappe-bench/env/bin/python -m pytest` (python3 hệ thống không có pytest).

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_ai_citation.py --cov=normcore.ai.citation` | 5 passed, độ phủ 97%; `grep "import frappe"` không in gì |
| T02 | `pytest normcore/tests/unit/test_procedure_ai_draft.py --cov=normcore.procedure.ai_draft` | 7 passed, độ phủ 99%; không import frappe |
| T03 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench ... run-tests --module normcore.api.test_procedure_ai && ... test_nc_ai_log && ... test_nc_ai_settings && ... test_nc_prompt_template'` | 2, 4, 9, 6 tests, OK cả bốn. Lệch thiết kế: không patch/after_install cho v2, gọi lười (ASM-024-15) vì test_nc_prompt_template cũ |
| T04 | with_bench migrate + run-tests test_procedure_ai + test_procedure | 3 tests OK; 21 tests OK (đỏ trước khi viết mã, xanh sau) |
| T05 | with_bench run-tests --module normcore.api.test_procedure_ai | 12 tests OK (đủ TC-AI-01..04, 1a, 1b x2, 4a, nguồn chọn thêm). Lưu ý: tham số `job_id` của frappe.enqueue không tới hàm, dùng `draft_job` |
| T06 | with_bench run-tests test_procedure_ai + test_procedure + test_procedure_workflow | 16 OK + 21 OK + 9 OK (TC-AI-10, quyền Auditor/Finance/khoa khác/job người khác) |
| T07 | check_conventions.py; with_bench 'migrate && bench build --app normcore'; pytest test_vi_csv_order test_procedure_editor_behavior test_feat_024_ui test_feat_007_ui | conventions exit 0; build exit 0; 26 passed. Nút Soạn quy trình, ai_draft_dialog.js (doctype_js), ProcedureEditor.vue, vi.d/FEAT-024.csv |
| T08 | python3 docs/tools/build_rtm.py docs | VAN DE: 0; thêm docs/as-built/FEAT-024.md, docs/rtm-testref/FEAT-024.md |
| T09 | golden_engine.py, golden_cls.py; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `with_bench 'migrate && run-tests --app normcore'`; check_conventions.py; build_rtm.py | golden 0/0; pytest 904 passed, độ phủ 99.11%; bench 1614 tests OK; conventions exit 0; VAN DE: 0. Đã `git merge origin/develop` (Already up to date). Sửa thêm: ProcedureEditor.vue không dùng msgprint (test_E15) |
| Sửa lần 1 (Reviewer) | with_bench run-tests --module normcore.api.test_procedure_ai | 18 tests OK (thêm 2 ca mẫu v2: v1 đã sửa không đè, admin có v2 không tạo v3); sửa ASM-024-02/10/11/15 và tasks.md T03 |
