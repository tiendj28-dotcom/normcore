# NORM-38 — sửa giao diện FEAT-035

| Lỗi | Nguyên nhân | Sửa | Test |
| :-- | :-- | :-- | :-- |
| 1. Form hiện 0 thay ô trống | `Document.as_dict` của Frappe ép Float NULL thành 0 khi gửi xuống form; form lưu lại thì ghi 0 thật (ASM-035-04) | `nc_test_system_volume.py`: `load_from_db` nhớ cột test phụ NULL, `as_dict` trả `None` cho cột đó nếu giá trị vẫn trống. Nhập 0 thì lưu 0 | `test_FR_QC_006_form_nhan_null_khong_phai_0` (đỏ trước sửa: `0.0 is not None`), `test_FR_QC_006_luu_form_giu_null`, `test_FR_QC_006_nhap_0_thi_luu_0` |
| 2. Trang import-excel ẩn bộ nhập | Ô chọn có thể không hiện | `import_excel.js`: thêm dòng chữ `Danh mục: <tên bộ nhập>` luôn hiện, cập nhật khi đổi bộ. Không đổi chọn sẵn của NORM-31 | `test_NORM38_luon_hien_ten_bo_nhap_dang_chon` |
| 3. Chữ chồng ở khối Tình trạng | Pill có chiều cao cố định, chữ dài tràn | `nc_test_system.js`: tiêu đề `display:block`, pill `height:auto; white-space:normal` | Cần QA kiểm bằng ảnh ở 1366×768 (không có khung test CSS) |

## Kiểm toàn bộ
- Lint CI đỏ do `AUX = [...]` (RUF012) và format; sửa thành tuple, `ruff check normcore scripts` và `ruff format --check normcore scripts` sạch.
- `run-tests --app normcore` trên site dùng chung `normcore.test` có 44 lỗi (`WorkflowPermissionError` Nháp → Đã ban hành, trùng `QT-DV-TEST-A-KHOA-TEST-v1`). Lỗi môi trường, cũng xảy ra trên `develop` nguyên bản. Theo Quyết định Lead (bình luận trên NORM-38, mục 2), bằng chứng chạy site thay bằng job "Test trên site Frappe v15" của CI. Không sửa Workflow trên site.
