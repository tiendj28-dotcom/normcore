# FEAT-039 — Nhật ký hiện thực (NORM-29)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_readonly.py --cov=normcore.core.readonly --cov-fail-under=90`; `grep -n "import frappe" normcore/core/readonly.py` | Quan sát đỏ trước khi có mã (ImportError); sau đó 12 passed, phủ 100%; grep không in gì. Test so `WRITE_PTYPES` với `AUDITOR_FORBIDDEN` nên T01 đã đưa luôn ba cờ `import`, `share`, `set_user_permissions` vào `AUDITOR_FORBIDDEN` (phần này của T02); `check_conventions.py` thoát 0 |
| T02 | `python3 scripts/check_conventions.py`; `pytest normcore/tests/unit/test_permission_matrix.py` | rc=0; 12 passed (7 TC-ACC-04 cũ không sửa + 5 test_TC_CLS_44_nc06_*). Thêm luật NC-06 "thiếu quyền đọc" (DocType cha không phải bảng con) |
