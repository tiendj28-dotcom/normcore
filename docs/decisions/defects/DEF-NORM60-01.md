# DEF-NORM60-01 — Tệp chỉ đọc còn nhắc tên cũ của tệp chung (CLAUDE.md, .autopilot, autopilot.sh)

- **Phát hiện bởi**: Dev, NORM-60. Lead duyệt cách soạn sẵn trong bình luận trả lời ba điểm của BA. Không chặn NORM-60.
- **Người sửa**: người vận hành. Agent không sửa các tệp này (guard.py và bước "Tài liệu chỉ đọc" của `ci.yml:39`). Khi merge PR NORM-60, Lead báo người một lần cùng việc import lại skill `normcore-integrate`.

Sau NORM-60, bản dịch, lối tắt Workspace và Test ref nằm ở tệp riêng của từng FEAT. Bốn chỗ dưới đây còn mô tả bố cục cũ; thiết kế: `docs/features/NORM-60/technical-design.md` mục 6.

## 1. `CLAUDE.md` mục 4 (dòng 69)

| Hiện tại | Sửa thành |
| :-- | :-- |
| "bản dịch ở `normcore/translations/vi.csv`." | "bản dịch ở `normcore/translations/vi.d/FEAT-NNN.csv` (mỗi FEAT một tệp); `vi.csv` do `normcore/generated.py` sinh lúc install, migrate, pytest, không commit." |

## 2. `CLAUDE.md` mục 11 (dòng 190, gạch đầu dòng `vi.csv`; và gạch đầu dòng `rtm.md`)

Thay gạch đầu dòng `vi.csv` bằng:

> Tệp sinh (`vi.csv`, `normcore.json`, `shortcuts.txt`) không theo dõi; sau `git merge origin/develop` chạy `python3 scripts/pr_sync_fix.py .`. Bản dịch, lối tắt Workspace, Test ref, quyền ma trận, hook dạng danh sách ghi vào tệp riêng của FEAT: `normcore/translations/vi.d/`, `normcore/nc_core/workspace/normcore/shortcuts.d/`, `docs/rtm-testref/`, `scripts/conventions/perm_matrix/`, `normcore/hook_registry/`. `scripts/check_conventions.py` kiểm kết quả ghép (NC-09, NC-10, NC-11, NC-08).

Gạch đầu dòng `docs/rtm.md`, `docs/verification-report.md` giữ nguyên.

## 3. `.autopilot/prompts/50-integrate.md` dòng 6

| Hiện tại | Sửa thành |
| :-- | :-- |
| "ghi Test ref vào `docs/rtm-testref.md` (FR → test)" | "ghi Test ref vào `docs/rtm-testref/{{FEAT}}.md` (FR → test)" |

## 4. `scripts/autopilot.sh` dòng 95

| Hiện tại | Sửa thành |
| :-- | :-- |
| `":(exclude)docs/rtm-testref.md"` | `":(exclude)docs/rtm-testref/"` |

## Không cần đổi

`CLAUDE.md` mục 8, `.claude/hooks/guard.py`, `.github/`.
