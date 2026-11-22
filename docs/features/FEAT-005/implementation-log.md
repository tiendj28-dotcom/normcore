# FEAT-005 — Nhật ký hiện thực (NORM-17)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `python3 docs/tools/build_rtm.py docs`; `git diff --name-only origin/develop...HEAD -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/implementation-plan.md docs/golden` | `VAN DE: 0`; không in gì. Áp AMD-003 (`data-model.md`), AMD-004 (`ux-foundations.md`); ASM-047, 051, 054 dẫn thêm bình luận Lead `01a2028d-…` |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate; run-tests --module …test_nc_specialty; run-tests --module normcore.tests.test_permissions'` | rc=0; 6 tests OK; 3 tests OK (test_co_18_doctype…). Test chặn xóa vì tham chiếu viết ở T03 |
| T03 | `with_bench.sh 'migrate; run-tests --module …test_nc_technical_service; …test_nc_specialty; --test test_TC_SVC_04_nhieu_khoa'` | 4 tests OK; 9 tests OK; `Ran 1 test` OK (viết test và mã cùng lượt, không quan sát bước đỏ riêng) |
| T04 | `with_bench.sh 'run-tests --module …test_nc_technical_service; --test test_TC_SVC_01_nhap_danh_muc; --module normcore.api.test_importer'`; `git diff --stat origin/develop...HEAD -- <tệp khung importer>` | 10 tests OK; `Ran 1 test` OK; 8 tests OK; diff khung rỗng; pytest unit xanh |
| T05 | `pytest normcore/tests/unit/test_chain.py -v`; `grep -n frappe normcore/procedure/chain.py` | 15 passed (đỏ ban đầu 1 test do test tự viết sai kỳ vọng mục không quyền rows=[] theo thiết kế 5.3, đã sửa test mới của chính FEAT); grep không in gì |
| T06 | `with_bench.sh 'run-tests --module normcore.api.test_service; …--test test_TC_SVC_03_tinh_trang_chuoi; --module normcore.tests.test_feat_001'` | 7 tests OK; `Ran 1 test` OK; 20 tests OK (sửa 1 test mới sai kỳ vọng rows của mục không quyền, theo thiết kế 5.3) |
| T07 | `pytest normcore/tests/unit/test_service_ui_conventions.py`; `with_bench.sh '… --test test_SCR_DSK_005_loc_danh_sach'` | 4 passed; `Ran 1 test` OK. Lọc `frappe.get_list` qua bảng con đúng, không lặp dòng. Bộ lọc `page.add_field` chưa chạy trên trình duyệt |
| T08 | `with_bench.sh 'migrate && bench build --app normcore'`; `multica env start preview` | rc=0; Workspace có 3 lối tắt. Preview lỗi: "chưa có site normcore.test trong /home/claudebot/preview-bench" → **chưa kiểm trên trình duyệt** (1366 × 768, 768 px, NC Finance, NC Document Controller, NC Auditor) |
| T09 | — | Nợ kỹ thuật ở `docs/as-built/FEAT-005.md` mục 7 |
| T10 | golden_engine (+ `--no-depr`), golden_cls, `build_rtm.py docs`; `pytest unit golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py`; `ruff check`, `ruff format --check` | golden rc=0, `VAN DE: 0`; 88 passed, cov 98,9%; `Ran 180 tests`, OK; conventions rc=0; ruff sạch |
