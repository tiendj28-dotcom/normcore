# FEAT-011 — Tasks

Mỗi task một commit `FEAT-011 Tnn: …`, test trước mã. `scripts/with_bench.sh` cho mọi lệnh bench.

- [ ] T01 Thiết kế + ASM-063..068 — done-when: `python3 docs/tools/build_rtm.py docs` in `VAN DE: 0`
- [ ] T02 `costing/parameters.py` + unit test — done-when: `pytest normcore/tests/unit/test_parameters.py` xanh; `grep -n frappe normcore/costing/parameters.py` không in gì
- [ ] T03 Sáu trường [1.1] và các trường còn thiếu của bộ tham số, mặc định; test TC-CLS-50 — done-when: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_parameter_set.test_nc_costing_parameter_set'` `OK`
- [ ] T04 Khóa, từ chối sửa/xóa, nhân bản (TC-RES-06); TC-RES-05 mức DocType — done-when: cùng lệnh T03 `OK`
- [ ] T05 NC Price Category, quyền, hooks, check_conventions, test 18→19; TC-RES-11 — done-when: `… run-tests --module normcore.nc_costing.doctype.nc_price_category.test_nc_price_category` và `--module normcore.tests.test_permissions` `OK`; `python3 scripts/check_conventions.py` thoát 0
- [ ] T06 Dữ liệu mẫu hai loại giá (patch + after_install) — done-when: test `test_TBD_05_hai_loai_gia_mau` `OK`
- [ ] T07 SCR-DSK-019: form JS, banner, nút Nhân bản, `vi.csv` — done-when: `pytest normcore/tests/unit/test_ui_conventions.py` xanh; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore'` thoát 0
- [ ] T08 As-Built, nhật ký, kiểm toàn bộ — done-when: pytest unit+golden `--cov=normcore/costing --cov-fail-under=90`, `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`, `check_conventions.py`, golden, `build_rtm.py docs`, `ruff check normcore scripts && ruff format --check normcore scripts` đều xanh
