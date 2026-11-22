---
name: normcore-design
description: Thiết kế kỹ thuật cho một FEAT của normcore (technical-design.md và tasks.md). Dùng khi issue FEAT ở trạng thái Todo và Lead giao cho BA.
---

# Normcore — Design một FEAT

## Khi nào dùng
Issue `FEAT-NNN ...` ở Todo, Lead mention bạn. Bị trả về do lỗi thiết kế cũng dùng skill này.

## Kiểm trước khi bắt đầu
1. Đọc `CLAUDE.md`. Sinh ngữ cảnh FEAT bằng skill `normcore-feat-context` (`python3 scripts/feat_context.py FEAT-NNN -o "$TMPDIR/FEAT-NNN-context.md"`) và đọc tệp đó trước.
2. Phụ thuộc (tệp ngữ cảnh đã ghi DONE hay chưa của từng FEAT): tìm dòng FEAT trong `.autopilot/build-order.txt` (cột 3). Mỗi FEAT phụ thuộc phải có `docs/features/FEAT-xxx/DONE` trên `origin/develop` (`git cat-file -e origin/develop:docs/features/FEAT-xxx/DONE`). Thiếu: bình luận "chờ FEAT-xxx", chuyển Blocked, mention Lead, dừng. Không làm thay FEAT kia.
3. Đã có `docs/features/FEAT-NNN/technical-design.md` và `tasks.md` trên nhánh FEAT: chỉ sửa theo "Quyết định Lead" hoặc lý do `design-defect` trong `verdict.json`, không viết lại từ đầu.

## Đầu vào
- Dòng FEAT ở `docs/implementation-plan.md` mục 3 (FR, UC, màn hình, khối, DocType) và tiêu chí nghiệm thu.
- FR, BR, NFR trong `docs/srs.md`; UC trong `docs/use-cases.md`; DocType trong `docs/data-model.md`; ADR trong `docs/architecture.md`; TC trong `docs/test-cases.md`.
- `docs/as-built/*.md` của các FEAT đã DONE: hợp đồng API, DocType, hàm đã có. Không tạo trùng.
- Phần lớn đầu vào trên đã có trong tệp ngữ cảnh. Chỉ mở tài liệu gốc khi cần nguyên văn, bằng `grep -n "<mã>"`, không đọc cả tệp lớn.

## Các bước
1. Tạo nhánh `feat/FEAT-NNN-<slug>` từ `origin/develop` mới nhất (nếu chưa có).
2. Viết `docs/features/FEAT-NNN/technical-design.md`:
   - Phạm vi: FR được làm; FR "một phần" thì nói phần nào.
   - DocType mới/đổi: trường, kiểu, bắt buộc, quyền, luồng trạng thái, DI áp dụng. Chỉ dùng DocType có trong `data-model.md`; cần DocType mới thì viết AMD trước (CLAUDE.md mục 7).
   - API whitelisted: tên hàm, tham số, kết quả, mã lỗi, kiểm quyền.
   - Logic thuần: module, hàm, ánh xạ tới BR và tới hàm golden.
   - Bảng tiêu chí nghiệm thu: mỗi dòng = một điều kiện kiểm được + mã TC + mã FR.
   - Giả định (ASM) và rủi ro.
3. Viết `docs/features/FEAT-NNN/tasks.md`, mỗi task là một commit:
   `- [ ] T01 <việc> — done-when: <lệnh kiểm cụ thể và kết quả mong đợi>`
   Task cuối luôn là `- [ ] Txx Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions.py, golden đều xanh`.
4. Thiếu thông tin hoặc tài liệu chưa rõ: tra `CLAUDE.md` mục 2 (thứ bậc nguồn) và mục 6 (mặc định). Có câu trả lời thì làm theo, ghi `ASM-NNN`/`CF-NNN`, làm tiếp. Không có: bình luận câu hỏi cụ thể (mã FR/BR/TC, trích hai bên, phương án đề xuất), chuyển issue sang Blocked, mention Lead, dừng. Lead quyết.
5. Chạy `python3 docs/tools/build_rtm.py docs`: phải 0 vấn đề.
6. Commit `FEAT-NNN design: ...`, push.

## Đầu ra
- Comment trên issue: phạm vi, số task, ASM mới, đường dẫn hai tệp.
- Làm tiếp skill `normcore-ui` trong cùng lượt (BA làm cả hai).

## Không được
Viết mã sản phẩm ở giai đoạn này.
