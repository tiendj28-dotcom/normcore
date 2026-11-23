# FEAT-039 — Nhật ký hiện thực (NORM-29)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_readonly.py --cov=normcore.core.readonly --cov-fail-under=90`; `grep -n "import frappe" normcore/core/readonly.py` | Quan sát đỏ trước khi có mã (ImportError); sau đó 12 passed, phủ 100%; grep không in gì. Test so `WRITE_PTYPES` với `AUDITOR_FORBIDDEN` nên T01 đã đưa luôn ba cờ `import`, `share`, `set_user_permissions` vào `AUDITOR_FORBIDDEN` (phần này của T02); `check_conventions.py` thoát 0 |
