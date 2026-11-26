# FEAT-025 — Nhật ký hiện thực

Python dùng để chạy pytest: `~/frappe-bench/env/bin/python -m pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR (quy tắc tránh conflict 3, 5).

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `with_bench 'migrate && run-tests --module normcore.api.test_norm'`; check_conventions.py; build_rtm.py | 32 tests OK; conventions exit 0; VAN DE: 0. Thêm `ai_confidence` (AMD-025-01), áp data-model 3.5 |
| T02 | `pytest test_procedure_consistency.py --cov=normcore.procedure.consistency` | 4 passed, độ phủ 100%; không import frappe |
| T03 | `pytest test_norm_ai_link.py --cov=normcore.norm.ai_link` | 2 passed, độ phủ 100%; không import frappe |
| T04 | with_bench migrate + run-tests test_procedure_consistency + test_nc_prompt_template | 1 test OK; 6 tests OK; test_nc_prompt_template.py không đổi |
| T05 | with_bench run-tests test_procedure_consistency, test_procedure, test_procedure_ai | 6 OK; 22 OK; 18 OK. Lệch thiết kế: `purpose` = mã mẫu lệnh (ASM-025-13) |
| T06 | with_bench migrate + run-tests test_norm_ai_link, test_norm, test_norm_version, test_norm_cls | 1, 32, 10, 19 tests OK. Controller: AI_LINK_FIELDS, guard_ai_fields, cờ ai_link; ai_link_cleared dành cho save_line (T07) |
| T07 | with_bench migrate + run-tests test_norm_ai_link, test_norm, test_norm_version, test_norm_cls, test_procedure_consistency | 7, 32, 10, 19, 6 tests OK. API đề xuất liên kết; `apply_suggestions` dùng `row.update` cho dòng Document |
| T08 | pytest test_feat_025_ui test_vi_csv_order test_procedure_editor_behavior test_feat_024_ui; check_conventions.py; with_bench migrate && bench build --app normcore | 25 passed; conventions exit 0; build exit 0. ProcedureEditor.vue, NormGrid.vue, norm_create.js, vi.d/FEAT-025.csv. Chưa làm: lưu trước ô đang sửa khi bấm kiểm (ASM-025-14) |
| T09 | python3 docs/tools/build_rtm.py docs | VAN DE: 0; thêm docs/as-built/FEAT-025.md, docs/rtm-testref/FEAT-025.md (rtm.md, verification-report.md không đưa vào PR) |
