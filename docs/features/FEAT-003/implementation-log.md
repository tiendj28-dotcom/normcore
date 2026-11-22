# FEAT-003 — Nhật ký hiện thực (NORM-21)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0`; ASM-063..066 |
| T02 | `with_bench.sh 'migrate; run-tests --module normcore.nc_core.doctype.nc_audit_event.test_nc_audit_event'`; `check_conventions.py` | 8 tests OK; rc=0. Test và mã viết cùng lượt, không quan sát riêng bước đỏ |
| T03 | cùng lệnh (test_TC_AUD_01_*, test_FR_AUD_001_*) | OK. Bổ sung so với thiết kế: NC Norm Set dùng trường `status` (map `STATE_FIELDS`), khóa ghi loại "Khóa" |
| T04 | cùng lệnh (test_TC_AUD_03_*, test_FR_AUD_003_*) | OK |
| T05 | cùng lệnh (test_FR_AUD_004_*) | OK |
| T06 | `python3 -m pytest normcore/tests/unit/test_audit_ui_conventions.py`; `with_bench.sh 'migrate; bench build --app normcore'` | 3 passed; build rc=0. Chưa xem trên trình duyệt |
| T08 | golden_engine + golden_cls; `build_rtm.py`; pytest unit+golden cov; `with_bench.sh '… run-tests --app normcore'`; `check_conventions.py`; ruff | golden OK; `VAN DE: 0`; 94 passed, độ phủ 98,90%; 193 tests OK; rc=0; ruff sạch |
