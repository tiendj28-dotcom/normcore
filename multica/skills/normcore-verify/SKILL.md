---
name: normcore-verify
description: Kiểm định độc lập một FEAT của normcore và viết acceptance.md, verdict.json. Dùng khi issue FEAT ở trạng thái QA. Người kiểm không phải người viết.
---

# Normcore — Verify một FEAT (kiểm định độc lập)

Bạn không viết tính năng này và không tin lời người viết. Chỉ tin lệnh bạn tự chạy.

## Đầu vào
- Tệp ngữ cảnh từ skill `normcore-feat-context`: danh sách FR, TC, DI, quyền để đối chiếu từng mục. Đây là bảng kiểm của bạn; mục nào trong đó không có test cùng mã là thiếu.
- Yêu cầu gốc: FR, BR, NFR, UC, TC của FEAT trong `docs/srs.md`, `docs/use-cases.md`, `docs/test-cases.md`, `docs/implementation-plan.md`.
- Thiết kế trong `docs/features/FEAT-NNN/`.
- `git diff origin/develop...HEAD` của nhánh `feat/FEAT-NNN-*` (nhánh của PR). Bạn làm việc trên chính nhánh này.

## Kiểm
1. **Độ phủ tiêu chí:** mỗi FR và TC của FEAT có test cùng mã; assertion kiểm đúng điều yêu cầu nói, không kiểm thứ dễ hơn. Test yếu: bạn được viết lại hoặc thêm **test**, không sửa mã sản phẩm.
2. **Chạy lại từ đầu trên site sạch:** tạo `normcore-verify.test`, cài app, chạy toàn bộ test và xóa site trong **một** lần gọi có khóa (bench dev dùng chung với Dev):
   ```
   scripts/with_bench.sh 'bench new-site normcore-verify.test --admin-password "$(openssl rand -hex 12)" --db-root-password "$DB_ROOT_PASSWORD" --install-app normcore && bench --site normcore-verify.test set-config allow_tests true && bench --site normcore-verify.test run-tests --app normcore; rc=$?; bench drop-site normcore-verify.test --force --db-root-password "$DB_ROOT_PASSWORD"; exit $rc'
   ```
   Kiểm trực tiếp ở mục 3 cần site còn sống thì gộp vào cùng lần gọi đó (`bench --site ... execute`), hoặc làm trên staging. Ngoài bench: pytest unit + golden + độ phủ, `check_conventions.py`, `build_rtm.py docs`.
3. **Kiểm như người dùng:** gọi API cho luồng chính của UC; thử với vai trò không có quyền và với NC Auditor; số liệu tính giá so với golden.
4. **Soát diff test:** có test nào bị xóa, skip, nới, đổi giá trị mong đợi (kể cả của FEAT khác) → `rework`.
5. **Phạm vi:** sửa ngoài phạm vi không cần thiết → `rework`.
6. **Tài liệu chỉ đọc** bị sửa → `rework`.
7. **CI của PR:** `gh pr checks` phải xanh.

## Giữ verdict sau khi gộp develop
Khi PR đã có verdict `accepted` rồi `develop` được gộp vào nhánh, verdict **vẫn hiệu lực** nếu diff riêng của PR (`git diff origin/develop...HEAD`) trước và sau khi gộp chỉ khác ở tệp sinh hoặc tệp ghép tự động. Khi đó không kiểm định lại: chỉ cần **CI xanh trên HEAD mới** (`gh pr checks`).

Tệp sinh (loại khỏi phép so):
- `docs/rtm.md`, `docs/verification-report.md`
- `normcore/translations/vi.csv`
- `normcore/nc_core/workspace/normcore/normcore.json`, `normcore/nc_core/workspace/normcore/shortcuts.txt`

Tệp hồ sơ QA cũng loại khỏi phép so vì QA ghi sau lần kiểm: `docs/features/*/acceptance.md`, `verdict.json`, `DONE`, `docs/as-built/*`.

Ghi chú: NORM-60 Phần 1 có thể đổi danh sách tệp sinh (tách `vi.csv`, workspace, test ref theo FEAT). Khi đó cập nhật danh sách này theo technical-design của NORM-60.

Lệnh kiểm (`<base_cu>`/`<head_cu>`: merge-base với develop cũ và commit trong `verdict.json`; `<base_moi>`/`<head_moi>`: `origin/develop` và HEAD hiện tại):
```
GEN=(docs/rtm.md docs/verification-report.md normcore/translations/vi.csv normcore/nc_core/workspace/normcore/normcore.json normcore/nc_core/workspace/normcore/shortcuts.txt)
EX=(); for f in "${GEN[@]}"; do EX+=(":(exclude)$f"); done
EX+=(':(exclude)docs/features/*/acceptance.md' ':(exclude)docs/features/*/verdict.json' ':(exclude)docs/features/*/DONE' ':(exclude)docs/as-built/*')
d() { git diff "$1...$2" -- . "${EX[@]}"; }
cu=$(d <base_cu> <head_cu> | git patch-id --stable | cut -d' ' -f1)
moi=$(d <base_moi> <head_moi> | git patch-id --stable | cut -d' ' -f1)
echo "cu=$cu moi=$moi"; [ "$cu" = "$moi" ] && echo GIU-VERDICT || echo KIEM-LAI
```
`<base_cu>` lấy bằng `git merge-base <commit trong verdict> <develop cũ>`; không còn ref develop cũ thì dùng cha thứ nhất của commit gộp. Xem thêm: `git range-diff <base_cu>..<head_cu> <base_moi>..<head_moi>`, hoặc so `--stat` hai diff rồi tự lọc tệp sinh.

Ví dụ đã chạy trên PR #57 (FEAT-015): `<base_cu>`=`f71b9f4`, `<head_cu>`=`a1b16fb` (commit đã kiểm), `<base_moi>`=`3b917c4` (develop sau gộp #54), `<head_moi>`=`3ed1e15` (sau sắp lại `vi.csv`) cho `cu=moi=9676a787…` → `GIU-VERDICT`. Đối chứng với `<head_moi>`=`cfcb1c8` (QA thêm test) cho hai giá trị khác nhau → `KIEM-LAI`.

Kết quả:
- `GIU-VERDICT`: ghi **một dòng** vào `acceptance.md`: `Giữ verdict: commit cũ <sha>, commit mới <sha>, lệnh so diff (patch-id, loại tệp sinh), kết quả GIU-VERDICT, CI xanh <link>`. Cập nhật `commit` trong `verdict.json` sang HEAD mới nếu `normcore-integrate` cần khớp.
- `KIEM-LAI`: diff riêng khác ở tệp không phải tệp sinh. Kiểm định lại đầy đủ như các mục trên.

## Đầu ra
Viết `docs/features/FEAT-NNN/acceptance.md` (bảng tiêu chí → bằng chứng → đạt/không) và `verdict.json`:
```json
{"verdict": "accepted | rework | design-defect | requirement-defect", "reasons": ["..."], "commit": "<sha HEAD đã kiểm>"}
```
Thứ tự commit:
1. Nếu thêm hoặc viết lại test: commit test trước.
2. Lấy `git rev-parse HEAD` lúc này làm `commit`.
3. Commit riêng `acceptance.md` và `verdict.json`, push.

Verdict và trạng thái chuyển tiếp:
| Verdict | Khi nào | `reasons` phải có | Chuyển sang |
| :-- | :-- | :-- | :-- |
| `accepted` | Đủ CLAUDE.md mục 8, trừ CI/merge/staging/As-Built | Tóm tắt bằng chứng | Chạy tiếp `normcore-integrate`, rồi **In Review** |
| `rework` | Mã chưa đạt | Việc cụ thể phải sửa: tệp, hàm, TC | **Đang làm** |
| `design-defect` | Thiết kế sai so với yêu cầu | Sai ở đâu, FR/TC nào | **Blocked** (Lead quyết) |
| `requirement-defect` | Tài liệu chỉ đọc mâu thuẫn | Mã `DEF-NNN` đã viết | **Blocked** (Lead chuyển lên người) |

Bình luận trên issue: verdict, lý do chính, link `acceptance.md`, mention Lead.

## Không được
Sửa mã sản phẩm. Merge. Tạo `DONE` khi verdict chưa `accepted`. Kiểm FEAT mà chính bạn đã viết.
