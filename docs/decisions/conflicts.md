# Mâu thuẫn tài liệu (CLAUDE.md §5)

| Mã | Nội dung mâu thuẫn | Tài liệu liên quan | Trạng thái |
| :-- | :-- | :-- | :-- |
| CF-001 | `docs/implementation-plan.md` mục 2 "Xong khi" của FEAT-000 mô tả luồng "khởi tạo bộ định mức, chạy lần tính giá" không có bước khóa, trong khi DI-06 (`data-model.md` mục 6) và FR-COST-002 (`srs.md`) bắt lần tính giá chỉ đọc bộ định mức "Đã khóa". | `implementation-plan.md` mục 2; `data-model.md` DI-06, 5.2; `srs.md` FR-COST-002 | Theo DI-06 (bậc cao hơn): skeleton thêm nút tạm "Khóa" (ASM-010). Người duyệt đồng ý Q2 ngày 2026-11-21. Cần người có quyền sửa `implementation-plan.md` bổ sung bước khóa vào mục 2. |
