# As-Built FEAT-011 — Bộ tham số, chức danh, loại giá

Issue NORM-20. FR: FR-RES-009, 010, 011, 012 (chức danh, không đổi), 015. UC-008, SCR-DSK-019.

## Đã làm
- **NC Costing Parameter Set** mở rộng đủ trường `data-model.md` 3.5 (gồm sáu trường [1.1]), mặc định ZERO / 5 / 2 (TC-CLS-50). Kiểm khoảng giá trị ở `normcore/costing/parameters.py` (thuần Python, phủ 100%). Bản ghi cũ: patch `backfill_parameter_set_defaults`.
- **Khóa (TC-RES-06):** bộ có `is_locked` hoặc có NC Costing Run "Đã khóa" trỏ tới thì từ chối sửa/xóa, nêu mã lần tính; `duplicate()` (cần quyền tạo) nhân bản thành bộ mới chưa khóa.
- **NC Price Category** mới (TC-RES-11): cấp phê duyệt bắt buộc; Admin xóa được, chặn khi đang được tham chiếu. Hai loại giá mẫu `GIA-BV`, `GIA-NN` (patch `add_sample_price_categories`, `install.after_install`), ghi "Giả định — chờ xác nhận".
- Form SCR-DSK-019: banner chỉ đọc khi bộ đã dùng, nút "Nhân bản"; `vi.csv`.
- TC-RES-05: không đổi công thức; test unit/golden có sẵn + test mức DocType.

## Nợ kỹ thuật, ghi chú
- Chưa mã nào bật `is_locked`; FEAT-015 bật khi khóa lần tính (ASM-068).
- Chưa DocType R1 nào liên kết tới NC Price Category; chặn xóa mới kiểm được bằng móc đã gắn (FEAT-012/030 thêm liên kết).
- Form SCR-DSK-019 chưa được kiểm bằng mắt: xem implementation-log về preview.

## ASM
ASM-063..070 (`docs/decisions/assumptions.md`). CF-004, AMD-007 (bốn trường bắt buộc theo srs, sửa `data-model.md` 3.5). ASM-069 chờ người duyệt (tiendj28, NORM-21); ASM-066, ASM-068 đã duyệt.
