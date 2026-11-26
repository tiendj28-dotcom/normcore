# As-Built FEAT-034 — Định mức theo hệ thống xét nghiệm

Issue NORM-40, PR #58. FR: FR-NORM-017..025, FR-OUT-011. UC-021, SCR-DSK-014, SCR-DSK-041. TC: TC-CLS-29..33. App 0.0.1, nghiệm thu 2026-11-26.
Người nghiệm thu: QA (Multica).
Giới hạn: giao diện (norm-grid, hộp thoại sao chép, form mẫu định mức) chưa kiểm bằng trình duyệt vì nhánh chưa lên staging; phần này chỉ có test unit đọc mã giao diện (`test_norm_cls_ui.py`, `test_norm_template_ui.py`). Tính chi phí theo cấp phát sinh và k thuộc FEAT-036; FEAT này chỉ lưu dữ liệu và kiểm ràng buộc nhập.

## Đã làm
- Mở rộng NC Norm Set (gắn hệ thống xét nghiệm, số xét nghiệm mỗi ống, xác nhận chuyên môn kiểm khoản mục bắt buộc) và NC Norm Line (cấp phát sinh `cost_level`, cờ k; k chỉ ở dòng Theo kết quả loại thuốc, vật tư; bật k thì hao hụt về 0; từ chối dòng dùng vật liệu QC thuộc kế hoạch chất lượng). Patch `set_norm_line_cost_level` cho dữ liệu đã có.
- DocType mới NC Norm Template, NC Norm Template Item; mẫu cài sẵn Hóa sinh và Miễn dịch (chưa bật), áp mẫu khi khởi tạo bộ (khoản mục bắt buộc chưa có trong quy trình thêm dạng dòng chung chưa có lượng).
- Sao chép bộ sang hệ thống khác (`norm/copy.py`, `copy_norm_set`); dòng có nguồn lực gốc không còn ở quy trình đích bị bỏ qua kèm lý do (ASM-034-26).
- Xuất bộ định mức (`exports/norm_set.py`) có cấp phát sinh, kế hoạch chất lượng, k.
- Logic thuần ở `normcore/norm/` (`validation.py`, `templates.py`, `copy.py`); API ở `api/norm.py`; giao diện NormGrid.vue và `norm_create.js`; Workspace; `vi.csv`.

## Ghi chú
- ASM-034-xx trong `docs/features/FEAT-034/technical-design.md`; ASM-034-24, 25, 26 Lead đã duyệt.
- Cảnh báo thiếu kế hoạch nội kiểm (TC-CLS-26) kiểm lại trên bộ định mức, vẫn cho khóa.
- `scripts/check_conventions.py` thêm hàng ma trận quyền "Mẫu định mức" cho DocType mới.

## Test đã chạy
Site sạch: 1338 test OK. pytest 708 passed, độ phủ `normcore/costing` + `benchmark` 99%. TC-CLS-29..33 đạt (xem `acceptance.md`).
