# NORM-60 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | sha |
|---|---|---|---|
| T01 | `git rev-parse origin/develop`; in ba dict `MATRIX`, `DOCTYPE_ROW`, `DELETE_ALLOWED` | develop = `12a43de2b66bae7f21bd622a9591070ca0c6e977`; git version 2.43.0 (≥ 2.38); JSON ba dict lưu ở `dicts-before.json` (sắp khóa) | (xem commit) |
| T02 | `pytest normcore/tests/unit/test_generated.py normcore/tests/unit/test_pr_sync_fix.py`; `grep "^import frappe" normcore/generated.py`; `ruff check/format --check` | 19 passed; grep rỗng; ruff sạch. **Lưu ý:** `scripts/tests/test_check_conventions.py` đã đỏ 15/27 test trên `origin/develop` trước NORM-60 (fixture không có dòng `DOCTYPE_ROW` cho 'NC Quy Trinh'; `scripts/tests/` không chạy trong CI). Không sửa test (luật 1); bộ lệnh T02 loại tệp này, so sánh: trước và sau đổi đều 15 failed / 12 passed. | (commit) |
