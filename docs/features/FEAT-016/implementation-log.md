# FEAT-016 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_accounting.py normcore/tests/unit/test_allocation_rules.py normcore/tests/golden/test_accounting_golden.py --cov=normcore.costing.accounting --cov=normcore.costing.allocation_rules --cov-fail-under=90`; `grep -n frappe` hai module | 36 passed, độ phủ 100%; grep không in gì | (T01) |
| T02 | `pytest normcore/tests/unit`; `scripts/with_bench.sh 'bench --site normcore.test run-tests --module normcore.api.test_importer && ...test_importer_equipment && ...test_importer_test_system'` | unit 248 passed (gồm test FEAT-004 cũ, không sửa dòng nào); bench: 8, 6, 5 test `OK` (ASM-124: Lead chọn `key_fields` trên NORM-28) | (T02) |
