# Giả định đã áp dụng (CLAUDE.md §6)

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-001 | TBD-02 | BR-COST-013 (NORM-4) | Cài đúng như `docs/golden/golden_engine.py`; chế độ tích lũy và các tỷ lệ là tham số, công thức nằm trong một hàm. Đã được duyệt trên issue NORM-4. | `normcore/costing/engine.py::apply_accumulation` | Đã xác nhận (Tài chính kế toán xác nhận công thức trên issue NORM-4, 2026-11-21; không có điểm khác golden) |
| ASM-002 | — (Giả định G1 của NORM-6) | BR-COST-001 (NORM-6) | Chi phí năm nhập thẳng (`annual_cost_override`): `None` = dùng công thức; có giá trị thì thay toàn bộ công thức (kể cả thu nhập khác), đơn giá giờ công vẫn = chi phí năm / (ngày × giờ), làm tròn 4 số lẻ HALF_UP. Golden không có ca này. | `normcore/costing/engine.py::job_rate` | Chờ Tài chính kế toán xác nhận |
