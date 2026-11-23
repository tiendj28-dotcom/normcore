# FEAT-003 — Nhật ký hiện thực (NORM-21)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0`; ASM-065..069 |
| T02 | `with_bench.sh 'migrate; run-tests --module normcore.nc_core.doctype.nc_audit_event.test_nc_audit_event'`; `check_conventions.py` | 8 tests OK; rc=0. Test và mã viết cùng lượt, không quan sát riêng bước đỏ |
| T03 | cùng lệnh (test_TC_AUD_01_*, test_FR_AUD_001_*) | OK. Bổ sung so với thiết kế: NC Norm Set dùng trường `status` (map `STATE_FIELDS`), khóa ghi loại "Khóa" |
| T04 | cùng lệnh (test_TC_AUD_03_*, test_FR_AUD_003_*) | OK |
| T05 | cùng lệnh (test_FR_AUD_004_*) | OK |
| T06 | `python3 -m pytest normcore/tests/unit/test_audit_ui_conventions.py`; `with_bench.sh 'migrate; bench build --app normcore'` | 3 passed; build rc=0. Chưa xem trên trình duyệt |
| T08 | golden_engine + golden_cls; `build_rtm.py`; pytest unit+golden cov; `with_bench.sh '… run-tests --app normcore'`; `check_conventions.py`; ruff | golden OK; `VAN DE: 0`; 94 passed, độ phủ 98,90%; 193 tests OK; rc=0; ruff sạch |

## Sửa theo Reviewer và Lead (bình luận `01a20517-0d3a-77c8-b7fb-bbdbc7838e39`)

| Việc | Lệnh | Kết quả |
| :-- | :-- | :-- |
| 1 NC Costing Run: hook `on_change` (bắt `db_set`), mốc `flags.audit_state`, bỏ `in_delete` | `with_bench.sh '… run-tests --module …test_nc_audit_event'` | 15 tests OK, gồm thành công, lỗi rồi tính lại, lưu nhiều lần không ghi trùng |
| 2 AMD-006: sự kiện "Xóa", `before_value` | cùng lệnh | OK: Version bị Frappe xóa vẫn còn đúng một sự kiện "Xóa"; xóa bị chặn không có sự kiện; không Password |
| 3 `to_time` chỉ có ngày lấy trọn ngày | cùng lệnh | OK |
| 4 Test dịch rỗng: bỏ; sửa ui-design, T06 | `python3 -m pytest normcore/tests/unit/test_audit_ui_conventions.py` | 2 passed |
| 5 ASM-068 ghi "chờ người duyệt" | — | giữ 18 → 19, chưa được duyệt |
