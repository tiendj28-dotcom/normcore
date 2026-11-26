# FEAT-014 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_time_study.py --cov=normcore.norm.time_study --cov-report=term-missing`; `grep -n "import frappe" normcore/norm/time_study.py` | 14 passed; phủ 100%; grep không in gì | (git log) |
| T02+T03 | `python3 scripts/check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_time_study.test_nc_time_study && bench --site normcore.test run-tests --module normcore.tests.test_permissions'` | check_conventions thoát 0 (thêm dòng ma trận "Phiếu bấm giờ" `W W - R - - R W R R` và hai ánh xạ DocType vào `scripts/check_conventions.py`, đúng data-model mục 4, như các FEAT trước); 10 test OK; test_permissions 3 OK | (git log) |
| T04 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_time_study'` | 3 test OK | (git log) |
| T06 | `pytest normcore/tests/unit/test_time_study_ui.py test_ui_conventions.py test_vi_csv_order.py test_form_buttons_i18n.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore'` | 27 passed; build thoát 0 | (git log) |

## Trạng thái dở dang (2026-11-26)

- **T05 chưa làm:** `git cat-file -e origin/develop:normcore/core/settings.py` → không có (FEAT-002/NORM-52 chưa merge). Theo Quyết định Lead không tự viết `core/settings.py`, không viết cứng số 5.
- **T07 chưa làm:** Script Report gọi `api.time_study.get_result` (T05) nên chưa kiểm được bằng bench.
- **T08 chưa làm, cần Lead quyết:** `NormGrid.vue` phải gọi `apply_to_norm_set` (API `normcore.api.time_study`), nhưng test cũ `test_norm_grid_ui.py::test_chi_goi_api_norm` chỉ cho `this.call(...)` thuộc `API_FUNCS` của `normcore.api.norm` và đúng một `method: API + method`. Thêm lệnh gọi sang API khác (hoặc hàm bọc `norm.apply_time_study`) làm test cũ đỏ; CLAUDE.md mục 3.1 không cho nới test ngoài trường hợp thêm DocType/bộ nhập/vai trò. Chưa sửa test.
- **T09, T10:** chờ các task trên.
| ASM-014-11 | `pytest normcore/tests/unit normcore/tests/golden` | thêm NC Time Study vào SCOPED theo Quyết định Lead; unit + golden xanh | (git log) |
