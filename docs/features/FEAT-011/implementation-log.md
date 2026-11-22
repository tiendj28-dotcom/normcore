# FEAT-011 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest` (pytest không có ở python hệ thống).

- T01: thiết kế, tasks, ASM-063..068; `build_rtm.py docs` — không thêm vấn đề mới.
- T02: `pytest normcore/tests/unit/test_parameters.py` — 8 passed.
- T03–T04: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_parameter_set.test_nc_costing_parameter_set'` — 13 tests OK. Lưu ý: `is_locked` trùng property `Document.is_locked` của Frappe (khóa tệp), nên đọc/ghi qua `get()`/`set()`.
- T05–T06: `… run-tests --module …nc_price_category.test_nc_price_category` — 12 OK; `--module normcore.tests.test_permissions` OK (19 DocType); `python3 scripts/check_conventions.py` thoát 0.
- T07: `pytest normcore/tests/unit/test_parameter_ui_conventions.py` xanh; `bench build --app normcore` thoát 0.
- T08 kiểm toàn bộ: golden_engine (cả `--no-depr`), golden_cls thoát 0; `build_rtm.py docs` `VAN DE: 0`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` 102 passed, 99,21%; `bench run-tests --app normcore` 218 tests OK; `check_conventions.py` thoát 0; `ruff check` và `ruff format --check` sạch.
