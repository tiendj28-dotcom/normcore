# FEAT-033 — Nhật ký hiện thực

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_compliance.py --cov=normcore.costing.compliance --cov-report=term-missing --cov-fail-under=90`; `grep -n frappe normcore/costing/compliance.py` | 20 passed, độ phủ 97,5%; grep không in gì |
| T02 | `python3 scripts/check_conventions.py`; `with_bench.sh 'migrate && run-tests --module …nc_equipment_compliance.test_nc_equipment_compliance'` | thoát 0; Ran 10 OK (có `test_TC_CLS_27_*`) |
| T03 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_compliance'` | Ran 9 OK (có `test_TC_CLS_28_nhac_han_thong_bao_va_doi_so_ngay`) |
| T04 | `with_bench.sh 'migrate && run-tests --module …nc_compliance_expiry.test_nc_compliance_expiry'` | Ran 5 OK (có `test_TC_CLS_28_bao_cao_*`) |
| T05 | `with_bench.sh 'run-tests --module normcore.api.test_importer_compliance'` | Ran 4 OK |
| T06 | `with_bench.sh 'run-tests --module normcore.tests.test_permissions && … normcore.api.test_importer'` | Ran 3 OK; Ran 8 OK. Đổi theo Quyết định Lead (ASM-105): 27 → 29 DocType; thêm `nc_equipment_compliance` cho Resource Manager; vẫn `assertEqual` đủ danh sách |
| T07 | `pytest normcore/tests/unit/test_compliance_ui_conventions.py normcore/tests/unit/test_vi_csv_order.py`; `with_bench.sh 'migrate && bench build --app normcore'` | 11 passed; build thoát 0. Chưa xem trên trình duyệt |
| T08 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0`; thêm `docs/as-built/FEAT-033.md` |
| T09 | `golden_engine.py`, `golden_cls.py`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore.costing --cov=normcore.benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py`; `ruff check`, `ruff format --check` | golden chạy xong; 206 passed, 59 subtests, độ phủ 98,25%; Ran 452 tests OK; thoát 0; ruff sạch |
| T10 | `git merge origin/develop` (gộp PR 33 FEAT-031, PR 34 NORM-27; giải xung đột assumptions, import_sets, utils, check_conventions, workspace, test_permissions); `with_bench.sh 'migrate && run-tests --app normcore'`; `pytest … --cov-fail-under=90`; `check_conventions.py`; `build_rtm.py` | Ran 533 tests OK; 235 passed, độ phủ 98,53%; thoát 0; VAN DE: 0. Đếm DocType 30 → 32 (ASM-105, số thực sau gộp); ASM-001..117 không trùng |
