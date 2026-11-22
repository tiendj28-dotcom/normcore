# FEAT-010 — Tasks

Mỗi task một commit `FEAT-010 Tnn: …`, test viết trước mã. `bench` qua `scripts/with_bench.sh`.

- [x] T01 Hàm thuần `costing/resources.py` + test đơn vị và golden (TC-RES-03, TC-RES-04, TC-RES-10 phần số, so `golden_cls` EQ_A/EQ_B/EQ_C) — done-when: `pytest normcore/tests/unit/test_resources.py normcore/tests/golden/test_resources_golden.py` xanh; `grep -n frappe normcore/costing/resources.py` không in gì
- [x] T02 DocType NC Equipment Type, NC Room (quyền, `check_conventions.py`, `hooks.py`, bảng đếm DocType trong test) — done-when: `python3 scripts/check_conventions.py` thoát 0; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_room.test_nc_room'` in `OK` (có `test_TC_RES_10_*`)
- [x] T03 NC Costing Parameter Set thêm `expired_depreciation_mode` — done-when: `… migrate && … run-tests --module normcore.nc_costing.doctype.nc_costing_parameter_set.test_nc_costing_parameter_set` in `OK`; test cũ của bộ tham số vẫn xanh
- [x] T04 NC Equipment, bảng con NC Equipment Component, NC Equipment Allocation, `validate` — done-when: `… migrate && … run-tests --module normcore.nc_costing.doctype.nc_equipment.test_nc_equipment` in `OK` (có `test_TC_CLS_48_*`, `test_TC_CLS_49_*`, `test_TC_RES_03_*`, `test_TC_RES_04_*`, quyền, Auditor, xóa bị tham chiếu)
- [x] T05 `api/equipment.py` (`get_indicative_rate`, `get_room_rate`) — done-when: `… run-tests --module normcore.api.test_equipment` in `OK`
- [ ] T06 SCR-DSK-018: JS form, danh sách, `vi.csv`, Workspace — done-when: `pytest normcore/tests/unit/test_equipment_ui_conventions.py` xanh; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore'` thoát 0
- [ ] T07 As-Built, ASM, CF, nhật ký — done-when: `python3 docs/tools/build_rtm.py docs` in `VAN DE: 0`
- [ ] T08 Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions.py, golden đều xanh
