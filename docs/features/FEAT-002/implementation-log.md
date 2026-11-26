# FEAT-002 — Implementation log

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (python hệ thống không có pytest).

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit` | 504 passed; `grep import frappe chain.py` rỗng | 95b5dd2 |
| T02 | `with_bench.sh 'migrate && run-tests --module ...test_nc_settings'`; `check_conventions.py` | 8 tests OK; conventions exit 0. Ghi chú: patch đặt ở `normcore/patches/` (theo quy ước sẵn có, không `v0_0/`); Frappe trả 0 cho Int trống nên `settings.is_unset` coi 0 là trống với tham số ≥ 1 | 262c6db |
| T03, T04 | `with_bench.sh 'migrate && run-tests --module normcore.core.test_notify && ...api.test_procedure_workflow && ...api.test_procedure_workflow_jobs'` | 9 OK; 9 OK; 5 OK; test FEAT-007 không đổi dòng nào (`git diff origin/develop -- normcore/api/test_procedure_workflow*.py` rỗng). Sai khác: ASM-002-14 (email cho loại Alert) | 3700025 |
| T05 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_home'` | 8 tests OK. Đo: get_home = 9 truy vấn dữ liệu (15 gồm siêu dữ liệu Frappe) → ASM-002-16 (thiết kế ≤ 6). Chưa đo 300 dịch vụ | cbfcc6e |
| T06, T09 | `with_bench.sh 'migrate && run-tests --module ...test_nc_settings'` | 11 tests OK (gồm test_TC_ADM_03_doi_so_ca_toi_thieu_ap_ngay; TC-ADM-03 phần trung vị thuộc FEAT-014, ASM-002-13). Sửa kèm: validate điền mặc định khi trường chưa đặt (tránh lưu 0 rồi tự chặn lần lưu sau) | e82a379 |
| T07, T08 | `node --check` 3 tệp JS + script block; `with_bench.sh 'migrate && bench build --app normcore && run-tests --module normcore.tests.test_feat_002'`; `pytest tests/unit/test_home_ui_conventions.py test_ui_conventions.py`; `check_conventions.py` | 2 test bench OK (block ở vị trí 2 sau tiêu đề, 26 lối tắt cũ còn đủ); 14 unit OK; conventions exit 0. **Chưa kiểm bằng mắt 1366 × 768**: `multica env start preview` thất bại ("chưa có site normcore.test trong ~/preview-bench", cần dựng một lần theo multica/README.md). Sai khác: Custom HTML Block là fixture `fixtures/custom_html_block.json` (không có thư mục module); `scripts/build_workspace.py` được mở rộng loại `CustomBlock` và tăng `modified` của Workspace (bắt buộc để migrate nạp lại Workspace) | 4bcf833 |
| T10 | `python3 docs/tools/build_rtm.py docs` | VAN DE: 0 | db5675e |
| T11 | golden_engine.py + golden_cls.py; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py`; `build_rtm.py docs`; đã `git merge origin/develop` trước khi chạy | golden exit 0; pytest 520 passed, cov 98.64%; bench Ran 1055 tests OK; conventions exit 0; VAN DE: 0 | (commit kế tiếp) |
