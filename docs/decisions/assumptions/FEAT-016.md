# Giả định của FEAT-016 (chống conflict khi merge)

Theo ASM-NORM32-02: mỗi FEAT một tệp trong `docs/decisions/assumptions/`. Mã dưới đây phát sinh ở NORM-31 (Lead duyệt); trước đổi mã là ASM-132.

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-016-01 | — | FEAT-016 (NORM-31), SCR-DSK-020, TC-ACCT-04 | Nút "Sửa loại chi phí của một dòng" đòi đúng một dòng được tích trong bảng Dòng; 0 dòng hoặc từ 2 dòng → thông báo, không mở hộp thoại (bỏ cách tự lấy dòng 1). Tiêu đề hộp thoại ghi số thứ tự dòng (`idx`) và mã tài khoản. | `nc_costing/doctype/nc_accounting_import/nc_accounting_import.js` | Áp dụng theo CLAUDE.md mục 6 (phương án đơn giản nhất, đảo ngược được) |
