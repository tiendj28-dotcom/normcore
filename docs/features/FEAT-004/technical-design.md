# FEAT-004 — Thiết kế kỹ thuật: Khung nhập Excel và tệp mẫu

Issue NORM-13. Nhánh `ai/NORM-13-feat-004` từ `develop` @ `f82065b`. Nguồn: `srs.md` FR-ADM-002, FR-RES-012; `use-cases.md` UC-008; `test-cases.md` TC-ADM-02; ADR-012; `data-model.md` 3.5, mục 4.

## 1. Phạm vi
Khung dùng chung (`core/importer.py`), sổ đăng ký (`core/import_sets.py`), API (`api/importer.py`), một bộ nhập mẫu NC Job Title, trang Desk "Nhập dữ liệu từ Excel". Không thêm DocType (G9).

## 2. Thành phần
- `core/importer.py` (thuần, không import `frappe`; dùng `openpyxl`): `Column`, `ImportSet`, `register`, `get_import_set`, `build_template`, `parse`, `process`. `process(set, content, mode, lookup, write, link_exists, can_update)` quyết định tạo/cập nhật/không đổi theo cột khóa; việc đọc/ghi CSDL do hàm truyền vào.
- `api/importer.py`: `list_import_sets`, `download_template`, `import_file` (whitelisted) + `build_template_file`, `run_import` (lõi, dùng cho test). Ghi từng dòng qua `get_doc().insert()/save()` trong savepoint riêng (G7); lỗi Frappe của dòng thành lỗi dòng.
- Quyền: `has_permission(đích, "create")` cho nhập (cả chế độ thử) và liệt kê; `"read"` cho tải mẫu (G6); `"write"` theo từng dòng cập nhật. NC Auditor/Resource Manager chỉ đọc → `PermissionError`.

## 3. Hợp đồng
Kết quả: `{mode, created, updated, unchanged, error_count, errors:[{row,column,message,text}], warnings}`. Lỗi `text` theo G3. Chế độ: `"thu"` / `"ghi"`. Ngưỡng G8: 5 MB, 5.000 dòng.

## 4. Tiêu chí nghiệm thu
TC-ADM-02 (trên NC Job Title, ASM-026); FR-ADM-002 (≥ 8 test); FR-RES-012 (tạo hoặc cập nhật theo mã, báo lỗi dòng); quyền.
