# FEAT-011 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (pytest không có ở python hệ thống).

- T01: thiết kế, tasks, ASM-063..068; `build_rtm.py docs` — không thêm vấn đề mới.
- T02: `pytest normcore/tests/unit/test_parameters.py` — 8 passed.
- T03–T04: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_parameter_set.test_nc_costing_parameter_set'` — 13 tests OK. Lưu ý: `is_locked` trùng property `Document.is_locked` của Frappe (khóa tệp), nên đọc/ghi qua `get()`/`set()`.
- T05–T06: `… run-tests --module …nc_price_category.test_nc_price_category` — 12 OK; `--module normcore.tests.test_permissions` OK (19 DocType); `python3 scripts/check_conventions.py` thoát 0.
- T07: `pytest normcore/tests/unit/test_parameter_ui_conventions.py` xanh; `bench build --app normcore` thoát 0.
- T08 kiểm toàn bộ: golden_engine (cả `--no-depr`), golden_cls thoát 0; `build_rtm.py docs` `VAN DE: 0`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` 102 passed, 99,21%; `bench run-tests --app normcore` 218 tests OK; `check_conventions.py` thoát 0; `ruff check` và `ruff format --check` sạch.
- Sửa theo Reviewer (bình luận 01a2051f…): (1) lấy `can_create` trước `disable_form()` + test thứ tự; (2) `is_locked` `no_copy`=1 và `validate` đặt 0 cho bản ghi mới (server `frappe.copy_doc` mặc định bỏ qua no_copy); (3) bỏ `fill_defaults`, thêm test trường bắt buộc trống bị từ chối / tùy chọn giữ trống; (4) `Duplicate` có ngữ cảnh `NC Costing Parameter Set` trong `vi.csv` và JS; (5) `description` "Giả định — chờ xác nhận" ở tích lũy, nghĩa vụ, trần hao hụt, ba loại chi phí TBD-14; (6) ASM-069 cho đổi test_permissions 18 → 19 (chờ Lead).
