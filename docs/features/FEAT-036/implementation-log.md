# FEAT-036 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_costing_cls.py normcore/tests/unit/test_costing_engine.py normcore/tests/unit/test_costing_runner.py`; `python3 docs/tools/build_rtm.py docs` | 45 passed; VAN DE: 0; độ phủ `cls.py` 99% | 32541de |
| T02 | `pytest normcore/tests/golden/test_cls_golden.py`; `python3 docs/golden/golden_cls.py`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 16 golden passed (TC-CLS-01..14); golden thoát 0; độ phủ 99% | dd3cd85 |
| T03 | `pytest normcore/tests/unit/test_costing_snapshot.py`; lệnh độ phủ T02 | 6 passed; độ phủ ≥ 90% | 3252052 |
| T04 | `python3 scripts/check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run'` | check_conventions thoát 0; Ran 15 tests, OK (gồm `test_TC_CLS_08_mac_dinh_lan_tinh`, `test_khoa_dau_vao_kich_ban_khi_da_tinh`) | 13ee967 |
| T05 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --module …test_nc_costing_cls'` + `…test_nc_costing_run` + `…nc_test_system.test_nc_test_system` | Ran 6 OK (TC-CLS-10, 15 bốn ca, 37, 38, 51 trên site, V1/kịch bản); Ran 15 OK; Ran 13 OK. ASM-036-26, 27 | fc43e2c |
| T06 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_costing'` | Ran 11 OK | 570268c |
| T07 | `pytest normcore/tests/unit/test_form_buttons_i18n.py … test_costing_cls_ui.py` | 37 passed | fbf7fa1 |
| T08 | pytest T07; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore && … run-tests --module normcore.api.test_costing'` | pytest xanh; build thoát 0; api.test_costing Ran 11 OK | cb3c544 |
| T09 | `python3 docs/tools/build_rtm.py docs` | VAN DE: 0; có `docs/as-built/FEAT-036.md`, `docs/rtm-testref/FEAT-036.md` | (T09) |
