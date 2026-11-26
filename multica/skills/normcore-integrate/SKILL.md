---
name: normcore-integrate
description: Hoàn thiện hồ sơ một FEAT normcore trên chính nhánh PR sau khi verify accepted (As-Built, Test ref RTM, DONE), rồi chuyển In Review để người merge. QA dùng ngay sau normcore-verify. Không merge.
---

# Normcore — Hoàn thiện hồ sơ trước khi người merge

QA dùng ngay sau `normcore-verify` khi verdict là `accepted`, trên **cùng nhánh PR** (`feat/FEAT-NNN-*`). Có thể chạy lại nhiều lần: bước nào đã xong thì bỏ qua.

**Không sửa mã sản phẩm hay test. Không merge** (hook chặn `gh pr merge`; người merge).

## Kiểm trước khi bắt đầu
1. `docs/features/FEAT-NNN/verdict.json` có `"verdict": "accepted"`. Không phải: dừng, quay lại kết quả của `normcore-verify`.
2. Mã không đổi sau lần kiểm: `git diff --name-only <commit trong verdict> HEAD` chỉ chứa `docs/features/FEAT-NNN/acceptance.md`, `verdict.json`. Có tệp khác: chạy lại `normcore-verify`. Nếu sau lần kiểm `develop` được gộp vào nhánh, áp dụng mục "Giữ verdict sau khi gộp develop" của `normcore-verify`: diff riêng chỉ khác ở tệp sinh thì verdict còn hiệu lực, chỉ cần CI xanh trên HEAD mới.

## Các bước
0. Dùng tệp ngữ cảnh từ skill `normcore-feat-context`. Lấy danh sách FR trong đó để ghi Test ref.
1. Viết `docs/as-built/FEAT-NNN.md` theo mẫu ở `docs/implementation-plan.md` mục 6. Người nghiệm thu: "QA (Multica)". Mục giới hạn ghi rõ những gì chưa kiểm được, ví dụ giao diện chưa kiểm bằng trình duyệt.
2. Ghi cột Test ref cho các FR của FEAT trong `docs/rtm.md` (tên test thật). Chạy `python3 docs/tools/build_rtm.py docs`: không thêm vấn đề mới. Nếu script sinh lại `rtm.md` và xóa cột Test ref, ghi vào `docs/rtm-testref.md` (FR → test) thay vì sửa tay.
3. Tạo `docs/features/FEAT-NNN/DONE`, nội dung:
   ```
   verify accepted: <commit trong verdict.json>
   thời điểm: <ISO 8601>
   merge và deploy staging: do người merge PR; deploy-staging chạy sau CI của develop
   ```
4. Commit `FEAT-NNN: As-Built, Test ref, DONE`, rồi push lên nhánh PR.
5. Đợi CI của PR xanh. Không ngồi chờ: đặt wakeup rồi kết thúc lượt.
   ```
   multica issue wakeup create <MÃ-ISSUE> --until-pr checks --expires-in 6h --on-timeout wake \
     --instruction "Tiếp normcore-integrate từ bước 5: đọc kết quả CI của PR."
   ```
   CI đỏ vì mã thì không tự sửa: chuyển issue về **Đang làm**, bình luận lỗi, mention Lead.
6. CI xanh:
   - bình luận: verdict, link `acceptance.md`, As-Built, "PR sẵn sàng merge";
   - chuyển issue sang **In Review**;
   - mention Lead.

## Lưu ý Multica
Workspace đặt **Settings → Code → After PRs merge, move the issue to = Done**. Người merge thì issue tự đóng.
