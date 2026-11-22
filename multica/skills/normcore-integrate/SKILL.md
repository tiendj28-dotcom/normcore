---
name: normcore-integrate
description: Đưa một FEAT đã được verify accepted của normcore lên develop và staging (As-Built, RTM, merge PR, smoke test, DONE). Lead dùng khi QA đã cho verdict accepted.
---

# Normcore — Integrate một FEAT

Có thể chạy lại nhiều lần: bước nào đã xong thì bỏ qua. **Không sửa mã sản phẩm hay test.** Chỉ ghi As-Built, RTM, DONE, và sửa hạ tầng CI/deploy nếu lỗi môi trường.

## Kiểm trước khi bắt đầu (trước đây runner làm)
1. `docs/features/FEAT-NNN/verdict.json` có `"verdict": "accepted"`. Không phải: comment lý do, không merge, dừng.
2. Mã không đổi sau lần kiểm: `git diff --name-only <commit trong verdict> HEAD` chỉ được chứa `docs/features/FEAT-NNN/acceptance.md` và `verdict.json`. Có tệp khác: giao lại QA kiểm phần mã mới, không merge.

## Các bước
0. Sinh tệp ngữ cảnh bằng skill `normcore-feat-context`; dùng danh sách FR trong đó để ghi Test ref.
1. Viết `docs/as-built/FEAT-NNN.md` theo mẫu ở `docs/implementation-plan.md` mục 6. Người nghiệm thu: "QA (Multica)".
2. Ghi cột Test ref cho các FR của FEAT trong `docs/rtm.md` (tên test thật); chạy `python3 docs/tools/build_rtm.py docs`: 0 vấn đề. Nếu script sinh lại `rtm.md` và xóa cột Test ref, ghi vào `docs/rtm-testref.md` (FR → test).
3. Commit, push. **Không ngồi chờ CI**: đặt wakeup rồi kết thúc run.
   ```
   multica issue wakeup create <MÃ-ISSUE> --until-pr checks --expires-in 6h --on-timeout wake \
     --instruction "Tiếp normcore-integrate từ bước 3: đọc kết quả CI của PR."
   ```
   Khi được đánh thức:
   - CI đỏ vì môi trường: sửa hạ tầng CI, push, đặt lại wakeup.
   - CI đỏ vì mã: comment lý do, giao lại Dev, không merge, dừng. Không tự sửa `verdict.json`: đó là việc của QA.
4. CI xanh: `gh pr merge --squash --delete-branch`.
5. Deploy staging chạy sau CI của `develop` (`.github/workflows/deploy-staging.yml`), mất vài phút. Đặt wakeup kiểm định kỳ rồi kết thúc run:
   ```
   multica issue wakeup create <MÃ-ISSUE> --kind every --every 10m --expires-in 2h --on-timeout wake \
     --instruction "Tiếp normcore-integrate từ bước 5: gh run list --workflow deploy-staging.yml --branch develop --limit 1. Chưa xong thì multica issue wakeup checkin để kết thúc lượt im lặng."
   ```
   Khi deploy xanh: chạy smoke test trên staging (`scripts/smoke_staging.sh` nếu có, hoặc gọi API luồng chính của FEAT qua REST bằng tài khoản smoke), rồi tắt wakeup (`multica issue wakeup disable`). Deploy hoặc smoke đỏ: comment lỗi kèm log, giao Dev sửa trên nhánh mới, dừng.
6. Tạo `docs/features/FEAT-NNN/DONE` (nội dung: sha merge, thời điểm) qua **PR**, không commit thẳng `develop`:
   ```
   git switch -c chore/FEAT-NNN-done origin/develop
   # ghi tệp DONE
   git add docs/features/FEAT-NNN/DONE && git commit -m "FEAT-NNN: DONE (merge <sha>, staging smoke đạt)"
   git push -u origin chore/FEAT-NNN-done
   gh pr create --base develop --title "<MÃ-ISSUE> FEAT-NNN: DONE" --body "..."
   ```
   Đặt wakeup `--until-pr checks` như bước 3; CI xanh thì `gh pr merge --squash --delete-branch`.
7. Comment: sha merge, kết quả staging và smoke, link As-Built. Chuyển issue sang `done` sau khi PR DONE đã merge.

## Lưu ý Multica
Workspace phải đặt **Settings → Code → After PRs merge, move the issue to = Don't change**. Nếu không, Multica tự chuyển issue sang Done ngay khi PR mã merge, trước khi staging và smoke test xong.
