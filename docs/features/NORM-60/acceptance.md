# NORM-60 — Nghiệm thu (QA độc lập: Tester iu)

Chore, không có TC. Kiểm trên HEAD `23472a35ded309531cbd4cc198072b6e7d307aaf` (đã chứa `origin/develop` mới nhất).

| Tiêu chí | Lệnh | Kết quả | Đạt |
|---|---|---|---|
| AC-1 hai nhánh song song không conflict (+ đối chứng bố cục cũ) | `pytest scripts/tests/test_norm60_parallel_merge.py` (nằm trong `pytest scripts/tests`) | 28 passed trong `scripts/tests` | Đạt |
| AC-2 pr_sync dùng script của nhánh, không mất block (+ chuyển tiếp PR cũ) | `pytest scripts/tests/test_norm60_pr_sync.py` | passed | Đạt |
| AC-3, AC-4 | — | Chuyển NORM-61 | — |
| AC-5 không xóa/skip/nới test | `git diff origin/develop -- '*test*.py' \| grep -E '^-.*(assert\|def test)'` | không in gì; NC-08/09/10/11 còn chạy | Đạt |
| Site sạch | `with_bench.sh` new-site normcore-verify.test, install-app, `generated.selfcheck`, `run-tests --app normcore`, drop-site | 1473 tests OK; selfcheck: 554/554 bản dịch, 27/27 lối tắt Workspace, ok=true | Đạt |
| pytest unit + golden + phủ | `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` | 815 passed, phủ 98,94% | Đạt |
| golden, RTM, quy ước, ruff | `golden_engine.py`, `golden_cls.py`, `build_rtm.py docs`, `check_conventions.py`, `ruff check/format` | golden OK; VAN DE: 0; check_conventions thoát 0; ruff sạch | Đạt |
| Tệp sinh không bị theo dõi | `build_generated.py` rồi `git status --porcelain` | rỗng | Đạt |
| Tài liệu chỉ đọc | `git diff origin/develop --stat -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/golden docs/implementation-plan.md CLAUDE.md .claude .autopilot .github` | rỗng | Đạt |
| CI PR #63 (head f45a129) | `gh pr checks 63` | cả hai job pass | Đạt |

## Lưu ý
- `scripts/tests/test_check_conventions.py`: 4 test đỏ (`test_luat5_permissions_rong`, `test_luat6_auditor_ghi`, `test_luat6_vai_tro_khac_duoc_ghi`, `test_fields_va_permissions_null_khong_van`). Trên `origin/develop` tôi chạy lại: 15/27 đỏ, gồm cả 4 test này. Lỗi có sẵn, NORM-60 giảm 15 xuống 4; Lead duyệt ASM-NORM60-10 (bình luận 10:02). Test bọc `test_norm60_scripts_tests.py` chỉ chạy `test_norm60_*.py`.
- Kiểm như người dùng với vai trò/Auditor: không áp dụng (không có UI, API, DocType mới). Quyền do ma trận `perm_matrix` được test NC-08 và `test_permission_matrix.py` (trong 815 passed, 1473 OK) giữ nguyên.
- Staging chưa kiểm Workspace 26 lối tắt sau migrate theo yêu cầu Lead: staging chạy bản develop, chưa có mã NORM-60 trước khi merge. Thay bằng `selfcheck` trên site sạch (27 lối tắt khớp 27 dòng mảnh). Nên kiểm lại trên staging sau deploy.
- QA sửa `scripts/conventions/perm_matrix/README.md` (dòng `delete`) theo ghi chú Lead; chỉ tài liệu.
