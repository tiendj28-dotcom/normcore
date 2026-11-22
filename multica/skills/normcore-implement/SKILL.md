---
name: normcore-implement
description: Hiện thực một FEAT của normcore theo tasks.md, viết test trước, mỗi task một commit. Dùng khi Lead giao bước hiện thực của một FEAT, kể cả khi QA trả về (rework).
---

# Normcore — Implement một FEAT

## Khi nào dùng
Lead giao hiện thực `FEAT-NNN`: lần đầu, hoặc giao lại sau verdict `rework` của QA.

## Kiểm trước khi bắt đầu
1. Đọc `CLAUDE.md`. Sinh tệp ngữ cảnh bằng skill `normcore-feat-context` (có sẵn TC, BR, dòng golden, DI cần test). Rồi đọc `docs/features/FEAT-NNN/technical-design.md`, `ui-design.md`, `tasks.md`, `implementation-log.md` (nếu có).
2. Bị trả về: đọc `docs/features/FEAT-NNN/verdict.json` và `acceptance.md`. Mỗi lý do trong `reasons` là một việc phải sửa; thêm thành task mới trước task "Kiểm toàn bộ" và bỏ đánh dấu task đó.
3. Checkout nhánh `feat/FEAT-NNN-*`, rebase lên `origin/develop` mới nhất.
4. Bench dev dùng chung với QA và có thể đang chạy mã của FEAT khác. **Mọi lệnh `bench` chạy qua khóa**, từ gốc checkout:
   ```
   scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'
   ```
   Script trỏ `apps/normcore` về checkout này, giữ khóa suốt lệnh, nhả khi xong. Chuỗi lệnh cần cùng một trạng thái site (migrate rồi test) phải nằm trong **một** lần gọi. Không `cd $BENCH_DIR` chạy bench trực tiếp, không tự `ln` liên kết. pytest unit/golden không cần bench, chạy thẳng.

## Các bước — lặp cho từng task chưa `[x]`, theo thứ tự
1. Viết test trước. Tên test mang mã TC nếu task gắn TC: `test_TC_PROC_01_tao_ban_nhap`. Chạy để thấy đỏ.
2. Viết mã cho đạt. Đổi DocType thì migrate và chạy test trong cùng một lần `scripts/with_bench.sh '...'`.
3. Chạy đúng lệnh trong `done-when`. Đạt: đánh dấu `[x]`, thêm một dòng vào `implementation-log.md` (task, lệnh, kết quả, sha), commit `FEAT-NNN Txx: ...`.
4. Đỏ: sửa, tối đa 3 lần cho một task. Lần 3 vẫn đỏ: đưa nhánh về commit xanh gần nhất, ghi lý do vào `implementation-log.md`, tạo `docs/features/FEAT-NNN/BLOCKED`, comment nguyên nhân, chuyển issue sang `blocked`, @mention Lead, dừng.
5. Thực tế khác thiết kế: viết AMD (CLAUDE.md mục 7), sửa thiết kế, làm tiếp. Không âm thầm làm khác thiết kế.

## Kết thúc
- Mọi task `[x]`, kể cả "Kiểm toàn bộ". Push nhánh.
- Mở PR (nếu chưa có): `gh pr create --base develop --title "<MÃ-ISSUE> FEAT-NNN: <tên>"`. Mã issue ở đầu tiêu đề để Multica gắn PR.
- FEAT có màn hình: bật preview để tự kiểm giao diện như người dùng: `multica env start preview` (in ra URL), mở các màn hình SCR-DSK của FEAT, thử với NC Auditor. Ghi URL vào comment để người duyệt mở từ sidebar.
- **Không ngồi chờ CI.** Ngay sau lần push cuối, đặt wakeup rồi kết thúc run:
  ```
  multica issue wakeup create <MÃ-ISSUE> --until-pr checks --expires-in 6h --on-timeout wake \
    --instruction "CI của PR đã chạy xong. Xanh: comment kết quả, đặt issue in_review, @mention Lead. Đỏ: gh run view <run-id> --log-failed, sửa, push, đặt lại wakeup này."
  ```
  Wakeup chỉ tính các check kết thúc sau khi tạo rule, nên phải tạo sau khi push.
- Comment: số task, lệnh kiểm cuối và kết quả, link PR, "đang chờ CI (wakeup)". Giữ issue `in_progress`; lượt được đánh thức mới đặt `in_review` và @mention Lead.

## Không được
- Tự viết `verdict.json`, tự tạo `DONE`, tự merge, tự giao issue cho QA.
- Sửa, skip, nới test (kể cả test của FEAT khác); sửa tài liệu chỉ đọc.
