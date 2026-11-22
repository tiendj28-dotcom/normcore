---
name: normcore-verify
description: Kiểm định độc lập một FEAT của normcore và viết acceptance.md, verdict.json. Dùng khi Lead giao kiểm định một FEAT. Người kiểm không phải người viết.
---

# Normcore — Verify một FEAT (kiểm định độc lập)

Bạn không viết tính năng này và không tin lời người viết. Chỉ tin lệnh bạn tự chạy.

## Đầu vào
- Tệp ngữ cảnh từ skill `normcore-feat-context`: danh sách FR, TC, DI, quyền để đối chiếu từng mục. Đây là bảng kiểm của bạn; mục nào trong đó không có test cùng mã là thiếu.
- Yêu cầu gốc: FR, BR, NFR, UC, TC của FEAT trong `docs/srs.md`, `docs/use-cases.md`, `docs/test-cases.md`, `docs/implementation-plan.md`.
- Thiết kế trong `docs/features/FEAT-NNN/`.
- `git diff origin/develop...HEAD` của nhánh `feat/FEAT-NNN-*`.

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

## Đầu ra
Viết `docs/features/FEAT-NNN/acceptance.md` (bảng tiêu chí → bằng chứng → đạt/không) và `verdict.json`:
```json
{"verdict": "accepted | rework | design-defect | requirement-defect", "reasons": ["..."], "commit": "<sha HEAD đã kiểm>"}
```
Thứ tự commit:
1. Nếu thêm hoặc viết lại test: commit test trước.
2. Lấy `git rev-parse HEAD` lúc này làm `commit`.
3. Commit riêng `acceptance.md` và `verdict.json`, push.

Ý nghĩa verdict (Lead đọc để giao bước kế; bạn không tự giao):
| Verdict | Khi nào | `reasons` phải có |
| :-- | :-- | :-- |
| `accepted` | Đủ CLAUDE.md mục 8, trừ CI/merge/staging/As-Built | Tóm tắt bằng chứng |
| `rework` | Mã chưa đạt | Việc cụ thể phải sửa: tệp, hàm, TC |
| `design-defect` | Thiết kế sai so với yêu cầu | Sai ở đâu, FR/TC nào |
| `requirement-defect` | Tài liệu chỉ đọc mâu thuẫn | Mã `DEF-NNN` đã viết; tạo `BLOCKED` |

Comment trên issue: verdict, lý do chính, link `acceptance.md`. Đặt issue `in_review` và @mention Lead.

## Không được
Sửa mã sản phẩm. Tạo `DONE`. Merge. Kiểm FEAT mà chính bạn đã viết.
