# Nghiệm thu NORM-24 — sắp xếp vi.csv, kiểm trong check_conventions

Commit đã kiểm: 22b7f6dd6b470bb8c8ee70e3f12d9217493fe88c (PR #31).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| vi.csv sắp xếp, không trùng khóa, không đổi bản dịch | So với origin/develop: 131 dòng cả hai, tập hợp dòng bằng nhau (so sánh đã sắp xếp) | Đạt |
| check_conventions kiểm thứ tự + khóa trùng | `check_conventions.check_vi_csv` (NC-09, NC-10); `python3 scripts/check_conventions.py` thoát 0 | Đạt |
| Test cho cả hai trường hợp | `normcore/tests/unit/test_vi_csv_order.py` 5 test (sắp xếp đúng, chưa sắp xếp, trùng khóa, cùng khóa khác ngữ cảnh, vi.csv thật) | Đạt |
| merge=union không conflict | Repo tạm: hai nhánh thêm dòng D và E vào cuối cùng một tệp có `merge=union` → merge không conflict, giữ cả hai dòng | Đạt |
| Golden, pytest, RTM | golden_engine, golden_cls, build_rtm.py docs thoát 0; pytest unit+golden 180 passed | Đạt |
| Test bench | `bench --site normcore.test migrate` + `run-tests --app normcore`: 418 tests OK | Đạt (xem lưu ý) |
| Diff test / phạm vi / tài liệu chỉ đọc | Diff 3 tệp (vi.csv, check_conventions.py, test mới); không xóa/skip/nới test; không đụng tài liệu chỉ đọc | Đạt |
| CI PR | 2 check SUCCESS ở 22b7f6d | Đạt |

Lưu ý: không tạo được site sạch `normcore-verify.test` vì môi trường QA không có `DB_ROOT_PASSWORD` (MariaDB từ chối root). Đã chạy trên site dùng chung `normcore.test` (sau migrate); CI của PR chạy trên site sạch và xanh. Phạm vi thay đổi không đụng DocType/DB.
Ghi chú: kết quả merge=union không tự giữ thứ tự chữ cái; check_conventions sẽ báo NC-10 và agent phải sắp xếp lại khi gỡ (đúng quy tắc CLAUDE.md mục 11).
