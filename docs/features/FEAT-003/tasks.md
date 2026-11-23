# FEAT-003 — Tasks

Mỗi task một commit `FEAT-003 Tnn: …`, test trước. `bench` qua `scripts/with_bench.sh`. Viết tắt: `E=normcore.nc_core.doctype.nc_audit_event.test_nc_audit_event`.

- [x] T01 Thiết kế, ASM-065..069 — done-when: `python3 docs/tools/build_rtm.py docs` in `VAN DE: 0`
- [x] T02 DocType NC Audit Event, `check_conventions`, test đếm 19, `core/audit.py` (`log_event`, `log_export`, `guard_immutable`), chốt bất biến cho NC AI Log — done-when: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module $E --test test_TC_AUD_02_ban_ghi_bat_bien'` in `OK`; `python3 scripts/check_conventions.py` rc=0
- [x] T03 Hook `doc_events["*"]` ghi chuyển trạng thái, khóa; `ignore_links_on_delete` — done-when: `… --test test_TC_AUD_01_lich_su_va_su_kien`, `… --test test_FR_AUD_001_xoa_ban_ghi_nguon_khong_bi_chan` in `OK`
- [x] T04 `api/audit.py::get_events` — done-when: `… --test test_TC_AUD_03_loc_theo_quy_trinh`, `… --test test_FR_AUD_003_` in `OK`
- [x] T05 `log_export` — done-when: `… --test test_FR_AUD_004_ghi_xuat_tep` in `OK`
- [x] T06 SCR-DSK-030: list JS, bộ lọc NC AI Log, Workspace — done-when: `pytest normcore/tests/unit/test_audit_ui_conventions.py` xanh; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore'` rc=0
- [x] T09 Sửa theo Reviewer: AMD-006 (sự kiện Xóa), `on_change` cho NC Costing Run, `to_time` trọn ngày, bỏ test dịch rỗng — done-when: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_core.doctype.nc_audit_event.test_nc_audit_event'` in `OK` (15 tests)
- [x] T07 `docs/as-built/FEAT-003.md`, `implementation-log.md` — done-when: mỗi task có dòng lệnh và kết quả
- [x] T08 Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions.py, golden đều xanh
