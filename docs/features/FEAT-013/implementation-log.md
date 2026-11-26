# FEAT-013 — Implementation log

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_norm_carry.py normcore/tests/unit/test_norm_validation.py normcore/tests/unit/test_norm_init.py`; `grep -rn "import frappe" normcore/norm/`; `python3 docs/tools/build_rtm.py docs` | 52 passed; grep không in gì; `VAN DE: 0`. Đã áp AMD-013-01 vào `docs/data-model.md` 3.5 và DI-04 | (xem commit T01) |
| T02 | `check_conventions.py`; `with_bench.sh "migrate && run-tests --module ...test_nc_norm_set"` | exit 0; Ran 17 tests OK | (xem commit T02) |
| T03 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_norm_version / api.test_norm / api.test_procedure_norm_flag'` | OK: 9 / 32 / 3 tests | (xem commit T03+T04) |
| T04 | test_quyen_new_version_* (cùng `test_norm_version`); `run-tests --module normcore.tests.test_permissions` | OK: 9 / 3 tests | (xem commit T03+T04) |
| T05 | `pytest test_norm_grid_ui test_ui_conventions test_vi_csv_order test_form_buttons_i18n`; `with_bench.sh "migrate && bench build --app normcore"` | 36 passed; build exit 0; check_conventions exit 0 | (xem commit T05) |
| T06 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0`; As-Built, Test ref đã ghi | (xem commit T06) |
| T07 | golden_engine, golden_cls; `pytest unit golden --cov-fail-under=90`; `with_bench.sh "migrate && run-tests --app normcore"`; check_conventions; build_rtm; merge origin/develop | golden OK; 651 passed, cov 98,69%; bench Ran 1231 tests OK; conventions exit 0; VAN DE: 0; develop đã up to date | (xem commit T07) |
| Review | Sửa theo Reviewer: `actions.new_version` cho bộ Đã xác nhận chuyên môn (không đòi NC Finance) + test; hàng chi phí "(đã bỏ)"; tiêu đề hộp kết quả; "Bước đã bỏ: n dòng"; nút btn-default ở Nháp. pytest 660 passed (cov 98,69%); bench run-tests --app normcore Ran 1265 OK; ruff sạch; conventions 0; VAN DE: 0 | (xem commit) |
