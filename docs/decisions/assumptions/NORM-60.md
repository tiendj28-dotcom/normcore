# Giả định của NORM-60 (chống conflict: tách tệp chung theo FEAT, sửa pr-sync)

Tệp theo quy ước ASM-NORM32-02. Thiết kế: `docs/features/NORM-60/technical-design.md`.

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-NORM60-01 | — | NORM-60 phần 1 | CF với ràng buộc 1 của Lead ("build_rtm.py đọc cả thư mục"): `docs/tools/build_rtm.py` chỉ đọc (guard.py, bước "Tài liệu chỉ đọc" của ci.yml) và không đọc Test ref, nên không sửa. Test ref ghi ở `docs/rtm-testref/FEAT-NNN.md`; dữ liệu cũ `git mv` thành `docs/rtm-testref/00-base.md`. Nguồn thắng: CLAUDE.md mục 2 (docs/tools chỉ đọc). | `docs/rtm-testref/` | Thiết kế (BA), chờ Lead xác nhận |
| ASM-NORM60-02 | — | NORM-60 phần 2 | pr-sync sinh và kiểm bằng script của cây đã gộp (thay ASM-NORM37-03 "dùng công cụ của develop"); `pr_sync.sh` tự chép chính nó trước khi checkout nhánh PR. An toàn vì chỉ xử lý PR cùng repo. | `scripts/pr_sync.sh`, `scripts/pr_sync_fix.py` | Thiết kế (BA) |
| ASM-NORM60-03 | — | NORM-60 phần 1 | Thứ tự ghép mảnh: `00-base` rồi theo tên tệp. Lối tắt Workspace hiện theo thứ tự đó; thứ tự dòng `vi.csv` không ảnh hưởng Frappe (tệp ghép vẫn sắp theo `_csv_key`). | `normcore/generated.py` | Thiết kế (BA), theo CLAUDE.md mục 6 |
| ASM-NORM60-04 | — | NORM-60 phần 1 | Dòng literal cũ trong `MATRIX`/`DOCTYPE_ROW`/`DELETE_ALLOWED` (`check_conventions.py`) và trong `hooks.py` giữ nguyên; FEAT mới dùng `scripts/conventions/perm_matrix/*.json`, `normcore/hook_registry/*.json`. Dời literal sang tệp là chore sau khi PR #56, #58, #59 merge. | `scripts/check_conventions.py`, `normcore/hooks.py` | Thiết kế (BA) |
| ASM-NORM60-05 | — | NORM-60 phần 1 | `vi.csv`, `normcore.json` không commit; sinh ở `before_install`, `before_migrate`, `normcore/tests/conftest.py`, `scripts/build_generated.py`. `modified` của Workspace đóng dấu `now()` lúc install/migrate để Frappe luôn nhập lại. | `normcore/generated.py`, `normcore/install.py`, `normcore/hook_registry/NORM-60.json` | Thiết kế (BA) |
| ASM-NORM60-06 | — | NORM-60 AC-1, AC-2 | Test AC-1/AC-2 ở `scripts/tests/` theo Lead; `ci.yml` không chạy thư mục này (không sửa `.github/`), Dev/Reviewer/QA chạy `pytest scripts/tests` và ghi bằng chứng. | `scripts/tests/test_norm60_*.py` | Thiết kế (BA), chờ Lead xác nhận |
