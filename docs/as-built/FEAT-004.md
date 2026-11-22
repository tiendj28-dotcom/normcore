# As-Built: FEAT-004 Khung nhập Excel và tệp mẫu
- Phiên bản app 0.0.1; ngày nghiệm thu: 2026-11-22; người nghiệm thu: Kiểm định độc lập (NORM-14)

## 1. Luồng nghiệp vụ đã xây
Chọn danh mục → tải tệp mẫu (tiêu đề + một dòng ví dụ) → tải tệp lên → "Kiểm tra" (không ghi; báo số tạo/cập nhật/không đổi và lỗi theo dòng/cột bằng tiếng Việt) → "Xác nhận ghi" (ghi dòng hợp lệ, bỏ dòng lỗi) → xem kết quả. Nhập lại cùng tệp không tạo trùng. Bộ nhập đã đăng ký: NC Job Title. Khác SRS/test: TC-ADM-02 chạy trên NC Job Title (ASM-026).

## 2. DocType tạo mới hoặc thay đổi
Không. Thêm Desk Page `import-excel` và Workspace "Normcore" (module NC Core).

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/importer.py`: `list_import_sets`, `download_template`, `import_file`. Logic thuần `normcore/core/importer.py` (khung) và `core/import_sets.py` (đăng ký). Không hook, tác vụ nền, fixtures. Thêm `openpyxl` vào `dependencies` của `pyproject.toml`.

## 4. Quyền và luồng trạng thái
Tải mẫu: quyền đọc DocType đích. Nhập: quyền tạo (và sửa cho dòng cập nhật). NC Auditor, NC Resource Manager, NC Director, NC Consultant bị `PermissionError` khi nhập; NC Finance, NC Admin nhập được. Không có luồng trạng thái.

## 5. Cấu hình cần thiết khi triển khai
`bench migrate` (đồng bộ Page, Workspace). **CI:** bước "Unit test thuần" cần `pip install pytest pytest-cov openpyxl` trong `.github/workflows/ci.yml` — Dev không được sửa `.github/`, người duyệt cần đổi (Q1); nếu chưa đổi, bước unit đỏ vì `ModuleNotFoundError: openpyxl`.

## 6. Test case đã chạy và kết quả
TC-ADM-02 (`api/test_importer.py`), 17 test `test_FR_ADM_002_*` đơn vị, test quyền, test quy ước giao diện. Kết quả lệnh ở `docs/features/FEAT-004/implementation-log.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
Chưa chụp màn hình 1366 × 768 (cần staging); tệp lớn xử lý đồng bộ (tối đa 5.000 dòng); chỉ `.xlsx`; chưa có nhật ký nhập (FEAT-003 nếu cần); màn hình danh mục chưa có nút mở trang này; trang chỉ liệt kê bộ nhập mà người dùng có quyền tạo nên vai trò chỉ đọc chưa tải được mẫu từ giao diện (API vẫn cho, ASM-032).

## Cách một FEAT sau đăng ký bộ nhập mới
1. Khai báo trong `normcore/core/import_sets.py` (hoặc module riêng được import từ `normcore/api/importer.py`):
```python
NC_ITEM = ImportSet(
    key="nc_item", label="Mặt hàng", doctype="NC Item", key_field="item_code",
    columns=(
        Column("item_code", "Mã mặt hàng", "Data", required=True, example="VD-001"),
        Column("uom", "Đơn vị", "Link", link_doctype="UOM", required=True, example="Hộp"),
        Column("unit_price", "Đơn giá", "Float", example=1500),
    ),
)
register(NC_ITEM)
```
2. Kiểu hỗ trợ: Data, Int, Float, Select (`options=`), Date, Check, Link (`link_doctype=`). `key_field` là cột khóa tìm bản ghi đã có (tạo mới hoặc cập nhật). Dòng ví dụ phải nhập được (G2).
3. Không sửa khung. Quyền lấy từ quyền DocType đích; ràng buộc nghiệp vụ nằm ở `validate` của DocType (lỗi thành lỗi dòng).
4. Test cần viết: `test_FR_<mã>_nhap_*` tích hợp (tải mẫu → nhập → nhập lại không trùng), test quyền (vai trò chỉ đọc và NC Auditor bị từ chối), theo mẫu `normcore/api/test_importer.py`; FEAT-009 thêm `test_TC_ADM_02_mat_hang_*`.
