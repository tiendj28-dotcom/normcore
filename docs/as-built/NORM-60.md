# As-Built: NORM-60 Chống conflict giữa các PR FEAT (Phần 1, 2)
- Phiên bản app 0.0.1; Dev: NORM-60; Người nghiệm thu: QA (Multica)

## 1. Nội dung đã xây
Chore, không đổi nghiệp vụ, DocType, công thức. Dữ liệu mọi FEAT từng sửa chung được tách thành mảnh theo tên FEAT, ghép lúc cần:
- Bản dịch: `normcore/translations/vi.d/*.csv` ghép thành `vi.csv` (không còn theo dõi bằng git).
- Lối tắt Workspace: `normcore/nc_core/workspace/normcore/shortcuts.d/*.txt` ghép thành `normcore.json` (không theo dõi).
- Test ref RTM: `docs/rtm-testref/*.md`.
- Ma trận quyền: `scripts/conventions/perm_matrix/*.json`.
- Hook: `normcore/hook_registry/*.json` qua `normcore/core/hook_registry.py`.

## 2. Mã
`normcore/generated.py` (ghép, sinh tệp, `before_migrate`, `selfcheck`), `scripts/build_generated.py`, `scripts/pr_sync.sh` (chạy bản chép của chính nhánh), `scripts/pr_sync_fix.py` (chuyển PR bố cục cũ sang mảnh `00-base.*`), `scripts/check_conventions.py` (NC-08..NC-11 kiểm trên kết quả ghép).

## 3. Vận hành
- Thêm bản dịch/lối tắt/Test ref/quyền/hook: tạo mảnh riêng của FEAT, không sửa `00-base.*`.
- Sinh lại: `python3 scripts/build_generated.py`; tự chạy ở `before_install`, `before_migrate`, `conftest.py`.
- Workspace "Normcore" là bản chuẩn của app, chỉ sửa qua mảnh `shortcuts.d/`; sửa tay trên giao diện không được bảo toàn sau migrate (ASM-NORM60-05, Lead duyệt).

## 4. Test và kết quả
AC-1, AC-2: `scripts/tests/test_norm60_parallel_merge.py`, `test_norm60_pr_sync.py`; `normcore/tests/unit/test_generated.py`, `test_hook_registry.py`, `test_perm_matrix_files.py`. Site sạch: 1473 tests OK; pytest unit+golden 815 passed, phủ 98,94%; check_conventions thoát 0.

## 5. Giới hạn và nợ
- AC-3, AC-4 thuộc NORM-61. Người vận hành sửa tay CLAUDE.md, `.autopilot/prompts/50-integrate.md`, `scripts/autopilot.sh` (xem DEF-NORM60-01).
- 4 test cũ trong `scripts/tests/test_check_conventions.py` đỏ có sẵn trên develop (ASM-NORM60-10); nên có issue riêng sửa.
- Chưa kiểm Workspace trên staging sau deploy; kiểm lại sau khi merge.
