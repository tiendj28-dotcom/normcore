# As-Built FEAT-010 — Thiết bị, phòng

Issue NORM-19. FR: FR-RES-005..008, FR-RES-012 (thiết bị, phòng), FR-RES-019..026. UC-008, SCR-DSK-018.
Người nghiệm thu: QA (Multica). Giới hạn: giao diện chưa kiểm bằng trình duyệt (Playwright không kết nối); chưa tạo được site sạch ở QA (thiếu DB_ROOT_PASSWORD), CI của PR chạy trên site mới.

## Đã làm
- DocType mới: NC Equipment, NC Room, NC Equipment Type, NC Equipment Component, NC Equipment Allocation; hình thức có máy Mua / Thuê / Liên doanh, liên kết / Đặt theo hóa chất; trường bắt buộc theo điều kiện; tiêu chí chia, linh kiện lớn, tỷ lệ theo khoa (tổng 100%), điện năng.
- Khấu hao, đơn giá giờ máy, giờ phòng: Python thuần ở `normcore/costing/resources.py`, khớp golden (EQ1 176.136,3636; V2 ZERO 34.090,9091). Lựa chọn ZERO/CONTINUE đọc từ NC Costing Parameter Set (trường của FEAT-011).
- Bộ nhập thiết bị, phòng (FR-RES-012); form SCR-DSK-018; `vi.csv`.

## Ghi chú
- TC-CLS-07/09/11/12/13 thuộc FEAT-036; cấu trúc dữ liệu đã đủ để dùng.
- ASM-078..084 (`docs/decisions/assumptions.md`); CF-003. ASM-084: sửa hai test cũ theo duyệt.
- PR 26 merge trước thì cần gộp `develop` lại và đánh lại số ASM.
