# Ma trận quyền theo DocType (NORM-60)

Mỗi DocType mới thêm **một tệp** `<ten_doctype_snake>.json` ở đây thay vì sửa ba bảng `MATRIX`,
`DOCTYPE_ROW`, `DELETE_ALLOWED` trong `scripts/check_conventions.py` (nguyên nhân 9–13 PR cùng conflict).

```json
{"doctype": "NC Norm Template", "row": "Mẫu định mức", "codes": "R R - W R - R R W R", "delete": []}
```

- Tên tệp = tên DocType viết thường, khoảng trắng thành `_` (`nc_norm_template.json`).
- `row`: dòng của `docs/data-model.md` mục 4 (hoặc ghi chú ASM). Nếu dòng đã có trong `MATRIX`, `codes` phải khớp.
- `codes`: 10 ký hiệu `R`, `W` hoặc `-` theo thứ tự `ROLES` trong `check_conventions.py`.
- `delete`: vai trò được thêm quyền xóa: `NC Admin` hoặc vai trò đã có trong `DELETE_ALLOWED` của `check_conventions.py`; `[]` nếu không có.
- Không khai lại DocType đã có trong bảng literal. `check_conventions.py` báo NC-08 nếu tệp sai.
