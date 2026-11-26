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
| T10 (một phần) | golden_engine.py, golden_cls.py; pytest unit+golden --cov costing,benchmark; with_bench migrate + run-tests --app normcore; check_conventions.py; git merge origin/develop | golden 0/0; conventions exit 0; đã merge origin/develop (Already up to date); bench 1797 tests, 3 đỏ, đều là test cũ cần Lead quyết (không sửa): `test_norm_grid_ui.py::TestNormGridUI::test_chi_goi_api_norm`, `::TestNormGridFeat013::test_FR_NORM_015_chi_goi_api_norm` (danh sách API_FUNCS của lưới thiếu 4 hàm FEAT-025), `test_time_study_ui.py::TestNormSetFormButton::test_luoi_va_api_norm_khong_doi` (git diff origin/develop của norm_grid/ và api/norm.py phải rỗng). Các test còn lại xanh. T10 chưa đánh dấu |
| Sửa theo AMD-025-02 (BA) | hoàn tác api/norm.py, norm_grid/, norm_create.js về origin/develop; thêm api/norm_link.py, after_insert + guard_ai_fields trong controller, nc_norm_set.js, sửa test_norm_ai_link.py và test_feat_025_ui.py | pytest unit 1008 passed; bench test_norm_ai_link 8 OK, test_norm 32, test_norm_version 10, test_norm_cls 19, test_procedure_consistency 6 OK |
| T10 | golden_engine.py, golden_cls.py; pytest unit+golden --cov costing,benchmark --cov-fail-under=90; with_bench migrate + run-tests --app normcore; check_conventions.py; build_rtm.py; git merge origin/develop | golden 0/0; pytest 1057 passed, độ phủ 99.08%; bench 1798 tests OK; conventions exit 0; VAN DE: 0; Already up to date |
