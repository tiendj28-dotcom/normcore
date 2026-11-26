# FEAT-034 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_norm_cls.py test_norm_templates.py test_norm_copy.py test_norm_validation.py`; `grep -rn "import frappe" normcore/norm/` | 86 passed; grep không in gì | 48a0bb0 |
| T02 | `check_conventions.py` rc 0; `with_bench.sh 'migrate && run-tests --module normcore.tests.test_permissions'`; `build_rtm.py` | OK (3 tests); VAN DE: 0 | 7be1c05 |
