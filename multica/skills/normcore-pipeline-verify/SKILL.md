---
name: normcore-pipeline-verify
description: Kiểm định kỳ, chỉ đọc, toàn bộ trạng thái truy vết của normcore (DONE có đủ bằng chứng, RTM, tài liệu chỉ đọc không đổi). Dùng cho autopilot hằng đêm.
---

# Normcore — Pipeline verify (chỉ đọc)

Không sửa mã hay tài liệu nào, trừ tệp báo cáo `docs/pipeline-health.md`.

## Kiểm, trên `origin/develop` mới nhất
1. Bộ tài liệu: `python3 docs/golden/golden_engine.py`, `--no-depr`, `golden_cls.py`, `build_rtm.py docs`: đều không lỗi, RTM 0 vấn đề.
2. Mọi mã FR, UC, SCR, FEAT, ADR, DEF, ASM, AMD được dẫn trong `docs/features/`, `docs/as-built/`, `docs/decisions/` đều tồn tại.
3. FEAT có `DONE` thì có `docs/as-built/FEAT-NNN.md`, `acceptance.md`, `verdict.json` = `accepted`.
4. Không FEAT `DONE` nào phụ thuộc FEAT chưa `DONE` (theo `.autopilot/build-order.txt`).
5. Tài liệu chỉ đọc không đổi so với **mốc đã duyệt**:
   ```
   BASE=$(git rev-parse -q --verify 'refs/tags/docs-baseline^{commit}' || echo afcbd59)
   git log --format='%h %an %ad %s' --date=short "$BASE"..origin/develop -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/golden docs/implementation-plan.md
   ```
   Rỗng là đạt. `afcbd59` là commit nạp bộ tài liệu bản 1.1; không dùng commit đầu tiên của kho, vì lúc đó chưa có `docs/`. Khi người cập nhật tài liệu hợp lệ (bản mới), người đó dời tag `docs-baseline` tới commit đó; bạn không tự dời tag.
   Có commit: liệt kê sha, tác giả, thông điệp. Tác giả là agent → nghiêm trọng. Tác giả là người → ghi "cần người xác nhận và dời tag docs-baseline".
   Tài liệu sửa qua AMD (`data-model.md`, `architecture.md`, `ux-foundations.md`, `design.md`) không thuộc mục này; chỉ kiểm mỗi lần sửa có AMD tương ứng trong `docs/decisions/amendments/`.
6. Test nhanh: `pytest normcore/tests/unit normcore/tests/golden -q`.

## Đầu ra
- Ghi `docs/pipeline-health.md` (thời điểm, kết quả từng mục, vấn đề). Commit lên nhánh `chore/pipeline-health-<ngày>`, mở PR vào `develop` nếu có thay đổi.
- Comment trên issue của autopilot: một dòng kết luận, rồi bảng từng mục đạt/không.
- Không có vấn đề: chuyển issue sang `done`.
- Có vấn đề nghiêm trọng (tài liệu chỉ đọc bị đổi, FEAT DONE thiếu bằng chứng, golden lỗi): để issue ở `in_review`, nêu rõ ở dòng đầu comment.
