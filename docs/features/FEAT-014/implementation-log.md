# FEAT-014 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_time_study.py --cov=normcore.norm.time_study --cov-report=term-missing`; `grep -n "import frappe" normcore/norm/time_study.py` | 14 passed; phủ 100%; grep không in gì | (git log) |
| T02+T03 | `python3 scripts/check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_time_study.test_nc_time_study && bench --site normcore.test run-tests --module normcore.tests.test_permissions'` | check_conventions thoát 0 (thêm dòng ma trận "Phiếu bấm giờ" `W W - R - - R W R R` và hai ánh xạ DocType vào `scripts/check_conventions.py`, đúng data-model mục 4, như các FEAT trước); 10 test OK; test_permissions 3 OK | (git log) |
