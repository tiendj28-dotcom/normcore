---
name: normcore-ui
description: Thiết kế giao diện (ui-design.md) cho một FEAT của normcore. Dùng sau normcore-design, thường trong cùng issue thiết kế do Lead giao.
---

# Normcore — UI design một FEAT

## Khi nào dùng
Sau khi đã có `technical-design.md` của `FEAT-NNN`.

## Đầu vào
- Tệp ngữ cảnh từ skill `normcore-feat-context` (có sẵn dòng màn hình SCR-DSK và đặc tả DocType).
- Màn hình SCR-DSK-* của FEAT trong `docs/implementation-plan.md`.
- Mô tả màn hình ở `docs/ux-foundations.md`; quy ước ở `docs/design.md`.
- Hợp đồng API ở `docs/features/FEAT-NNN/technical-design.md`.

## Các bước
1. Làm trên nhánh `feat/FEAT-NNN-*`.
2. FEAT không có màn hình nào: ghi "Không có màn hình" vào `docs/features/FEAT-NNN/ui-design.md`, commit, push, rồi làm như mục Đầu ra.
3. Viết `ui-design.md`, mỗi màn hình gồm:
   - Loại hiện thực: Form/List DocType chuẩn của Desk, Report, hay Desk Page Vue.
   - Bố cục (section, cột, trường theo thứ tự), hành động, nút, phím tắt.
   - Trạng thái: rỗng, đang tải, lỗi, không có quyền, chỉ đọc (NC Auditor), các trạng thái workflow.
   - API gọi cho từng hành động.
   - Kiểm 1366 × 768, bàn phím, tương phản (NFR-USE-004), chuỗi tiếng Việt qua `_()`.
4. Cần task hiện thực giao diện chưa có trong `tasks.md`: chèn trước task "Kiểm toàn bộ".
5. Commit `FEAT-NNN ui: ...`, push.

## Đầu ra
- Comment liệt kê màn hình và task đã thêm.
- Đặt issue `in_review` và @mention Lead. Không tự chuyển sang bước kế, không tự giao việc cho agent khác. Nếu cùng issue còn bước hiện thực thì làm tiếp normcore-implement thay vì dừng.

## Không được
Viết mã sản phẩm.
