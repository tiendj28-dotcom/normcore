# FEAT-009 — Nhật ký hiện thực (NORM-18)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_pricing.py normcore/tests/golden/test_material_golden.py` | đỏ (không import được) → xanh sau khi viết `pricing.py`; 2 test tự sai dữ liệu mẫu (ngày chứng từ) đã sửa trong lượt viết; `pricing.py` cov 99% |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate && run-tests --module …test_nc_item && …test_nc_item_price && normcore.tests.test_permissions'` | rc=0; 10 OK; 13 OK; 3 OK. Lần đầu đỏ: validate chạy trước kiểm bắt buộc, Select tự chọn tùy chọn đầu → thêm tùy chọn rỗng đầu và kiểm `is not None` |
| T03 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_item'` | 13 tests OK (TC-RES-01, 02, 08, TC-CLS-45..47, TC-ADM-02) |
| T04 | `pytest normcore/tests/unit/test_item_ui_conventions.py`; `with_bench.sh 'migrate && bench build --app normcore'` | 4 passed; build thoát 0. **Chưa kiểm trên trình duyệt** (preview thiếu site như FEAT-005) |
| T05 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0` |
| T06 | golden_engine (+ `--no-depr`), golden_cls; `pytest unit golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py`; `ruff check`, `ruff format --check` | golden rc=0; 120 passed, cov 98,83%; lần đầu `Ran 247`, 2 FAIL ở `test_importer.py` (Finance, RM thấy thêm bộ `nc_item`) → sửa kỳ vọng theo ASM-074 → `Ran 247 tests`, OK; conventions rc=0; ruff sạch |
