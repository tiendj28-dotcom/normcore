# Cài Multica cho normcore — 5 việc ưu tiên

Thư mục này chứa mọi thứ cần dán hoặc import vào Multica. Không có gì ở đây chạy tự động; mỗi bước dưới đây là một thao tác của người vận hành (owner hoặc admin workspace). Làm theo thứ tự.

| Tệp | Dùng ở bước |
| :-- | :-- |
| `workspace-context.md` | 1 |
| `project-r1.md` | 1 |
| `skills/*/SKILL.md` | 3 |
| `../scripts/feat_context.py`, `../scripts/with_bench.sh`, `../.multica/environments.toml`, `../scripts/preview_env.sh` | Thêm |
| `agents.md` | 3 |
| `autopilots/*` | 4 |

---

## Bước 1 — Ngữ cảnh: Workspace Context, project, repo

1. **Settings → General → Context**: dán phần dưới đường kẻ của `workspace-context.md`. Multica đưa Context vào mọi agent trong workspace.
2. Tạo project **Normcore R1** (sau đó R2, R3). Dán `project-r1.md` vào **Description**. Mô tả project đi vào mọi run của issue trong project.
3. Project → **Resources → Repositories → Add repository**: `https://github.com/mvl26/normcore`, ref `develop`. Mỗi run sẽ tự checkout đúng repo, khỏi dán đường dẫn vào issue.
   ```
   multica project resource add <project-id> --type github_repo --url https://github.com/mvl26/normcore --ref develop
   ```

Kiểm: mở execution log của một run → **Context received**, thấy tên project và repo.

## Bước 2 — GitHub integration

1. **Settings → Code → Connect GitHub**, cấp quyền cho repo `mvl26/normcore` (cần quyền admin trên repo).
2. Trong **Pull requests & issues**:
   - **Auto-link PRs**: bật. PR gắn vào issue khi mã issue (`NORM-12`) nằm trong tên nhánh hoặc tiêu đề. Nhánh `ai/NORM-N-*` hiện tại đã khớp; nhánh `feat/FEAT-NNN-*` thì tiêu đề PR phải bắt đầu bằng mã issue (skill implement đã dặn).
   - **PR card → CI & mergeability**: bật, để thấy CI xanh/đỏ và xung đột ngay trên issue.
   - **Co-authored-by**: bật.
   - **After PRs merge, move the issue to: Done.** Người merge PR là bước cuối; QA đã đưa acceptance, verdict, As-Built, Test ref, DONE vào chính PR đó trước khi chuyển In Review.

## Bước 3 — Skills và đội agent đang có

**Skills.** Mỗi thư mục trong `skills/` là một skill (thư mục có `SKILL.md`). Import:
- UI: **Skills → New skill → Import from local**, chọn từng thư mục; hoặc
- CLI: nén từng thư mục thành `.zip` rồi `multica skill import --file normcore-design.zip`.

Sửa skill sau này: sửa tệp ở đây qua PR, rồi import lại với `--on-conflict overwrite` (chỉ người tạo skill được overwrite).

**Đội.** Dùng đội đang có (Lead, BA, Dev, Reviewer, QA, squad do Lead điều phối); **không** tạo agent mới, **không** tạo workflow theo cột. Lead duyệt mọi câu hỏi và Blocked; người chỉ merge. Theo `agents.md`:
- thay instructions của từng agent bằng khối **Quy tắc chung** + khối của vai;
- gắn skill theo bảng;
- đặt `custom_env` (`BENCH_DIR`, `PREVIEW_BENCH_DIR`, `AUTOPILOT_STAGE` theo vai).
```
multica skill list                                   # lấy id của skill
multica agent skills add <agent-id> --skill-ids <skill-id>
```
`AUTOPILOT_STAGE` quyết định hook `guard.py` cho làm gì: không vai nào (`design`, `implement`, `verify`) được `gh pr merge` hay commit lên `develop`/`main`; chỉ người merge.

Kiểm: giao Lead một FEAT; Lead mention BA ở Todo; execution log → Context received liệt kê skill `normcore-*` là delivered; đầu run có lệnh `scripts/feat_context.py`.

## Bước 4 — Autopilot

1. `autopilots/pipeline-verify-nightly.md`: kiểm truy vết lúc 2 giờ sáng mỗi đêm, giao QA. Mốc tài liệu chỉ đọc là tag `docs-baseline` (không có thì commit `afcbd59`); khi cập nhật tài liệu hợp lệ, người vận hành dời tag: `git tag -f docs-baseline <sha> && git push -f origin refs/tags/docs-baseline`.
2. `autopilots/ci-failure-webhook.md`: GitHub báo workflow thất bại trên `develop`, tạo issue cho Dev. Bộ lọc ở `ci-failure-filter.json`.

Bấm **Run now** một lần cho mỗi autopilot để thử. Multica tự tạm dừng autopilot nếu 7 ngày qua có từ 50 run trở lên mà 90% thất bại; xem lý do ở run history.

## Bước 5 — Daemon chạy dưới user riêng

Theo trang Security model của Multica, run có toàn quyền của user chạy daemon, và Claude Code chạy với `--permission-mode bypassPermissions`. Ranh giới an toàn phải nằm ngoài daemon. Trên máy Ubuntu autopilot (PLAYBOOK mục 3.1):

```bash
sudo adduser --disabled-password --gecos "" multica
sudo -iu multica
# cài frappe-bench, node, Claude Code theo PLAYBOOK 3.1–3.2, đăng nhập `claude` một lần
# cài Multica CLI theo hướng dẫn trên trang Runtimes → Add → Other machine or server
multica login --token                    # dán PAT tạo ở Settings → API Token
multica config set workspaces_root /data/multica_workspaces   # ổ lớn: bench + node_modules nặng
multica daemon start
multica daemon autostart enable
sudo loginctl enable-linger multica      # chạy cả khi không ai đăng nhập
```

Chỉ cấp cho user `multica` đúng những gì agent cần: deploy key riêng cho repo, token `gh` hạn chế repo, không có khóa production.

Hook `.claude/hooks/guard.py` gọi `python3`; trên Ubuntu lệnh này có sẵn. Nếu daemon chạy trên Windows thì `python3` là lối tắt Microsoft Store và hook bị bỏ qua: phải sửa lệnh trong `.claude/settings.json` thành `python`.

Kiểm:
```bash
multica daemon status --output json
multica daemon logs --lines 100
```
Trang **Runtimes** thấy máy online với Claude Code. Đổi runtime của cả 5 agent sang máy này.

---

## Thêm — ngữ cảnh FEAT, preview site, wakeup chờ CI

**Ngữ cảnh FEAT.** `scripts/feat_context.py FEAT-NNN` gom FR, BR, TC, UC, màn hình, DocType, DI, ma trận quyền, dòng golden và phụ thuộc của một FEAT vào một tệp (FEAT-006: khoảng 15 KB, so với khoảng 330 KB tài liệu gốc). Skill `normcore-feat-context` dặn agent chạy nó ở đầu mọi giai đoạn. Import skill này như các skill khác và gắn cho cả 5 agent.

**Bench dev dùng chung có khóa** (`scripts/with_bench.sh`). Dev và QA có thể chạy cùng lúc trên hai FEAT. Mỗi lệnh bench đi qua script này: giữ khóa `$BENCH_DIR/.normcore-bench.lock`, trỏ `apps/normcore` về checkout của run, chạy, nhả khóa. Run khác chờ (tối đa `BENCH_LOCK_WAIT`, mặc định 90 phút). Ai đang giữ khóa: `cat $BENCH_DIR/.normcore-bench.lock.owner`. Muốn song song thật thì cho Dev và QA mỗi người một `BENCH_DIR`.

**Preview site** (`.multica/environments.toml` + `scripts/preview_env.sh`). Agent chạy `multica env start preview` để bật `normcore.test` với mã của checkout, rồi tự mở giao diện kiểm. Bạn mở cùng site đó từ mục **Environments** trong sidebar của issue. Điều kiện:
- Daemon chạy trên Linux hoặc macOS (Multica chưa hỗ trợ Environments trên Windows).
- Preview chạy trên **bench riêng** `$PREVIEW_BENCH_DIR` (mặc định `~/preview-bench`), không phải bench dev, để không giữ liên kết của bench dev hàng giờ. Tạo một lần:
  ```bash
  bench init ~/preview-bench --frappe-branch version-15
  cd ~/preview-bench
  # đổi cổng Redis cho khỏi trùng bench dev: sửa port trong config/redis_cache.conf, config/redis_queue.conf
  # và redis_cache, redis_queue trong sites/common_site_config.json (vd. 13100, 11100)
  ln -s <checkout bất kỳ> apps/normcore && echo normcore >> sites/apps.txt
  bench new-site normcore.test --install-app normcore
  ```
- Mỗi máy chỉ một preview tại một thời điểm (script giữ khóa; preview thứ hai bị từ chối). TTL 2 giờ.

URL chỉ mở được trên máy chạy daemon. Truy cập từ xa thì forward cổng hoặc dùng Tailscale như staging.

**Wakeup chờ CI.** Skill implement và integrate không còn ngồi chờ `gh pr checks --watch`. Agent đặt wakeup `--until-pr checks` (và `--kind every` để chờ deploy staging), kết thúc run, rồi được đánh thức khi CI xong. Xem các wakeup đang chờ ở **Autopilot → Issue wakeups**.

## Sau một tuần
- **Analytics → Errors**: lỗi rơi vào nhóm nào (Timeout, Agent, Runtime…). Nhóm Agent với `iteration_limit` thì thu hẹp phạm vi issue hoặc tăng `--max-turns` qua custom args của agent.
- `multica issue usage <NORM-x>`: chi phí từng FEAT.
- Lỗi lặp lại nhiều lần thì ghi luật vào skill tương ứng ở đây, mở PR, rồi import lại skill.
