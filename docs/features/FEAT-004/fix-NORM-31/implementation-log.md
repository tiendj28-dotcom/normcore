# NORM-31 — Nhật ký hiện thực

Pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest`.

- T01: `pytest normcore/tests/unit/test_import_excel_behavior.py` với `import_excel.js` của develop → 4 đỏ (N31-01 x2, N31-04, N31-05), 3 xanh (N31-02, N31-03, N31-06).
- T02: sau khi sửa `import_excel.js`, `pytest test_import_excel_behavior.py test_import_ui_conventions.py` → 9 xanh, consoleErrors rỗng.
