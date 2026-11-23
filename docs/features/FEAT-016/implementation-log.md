# FEAT-016 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_accounting.py normcore/tests/unit/test_allocation_rules.py normcore/tests/golden/test_accounting_golden.py --cov=normcore.costing.accounting --cov=normcore.costing.allocation_rules --cov-fail-under=90`; `grep -n frappe` hai module | 36 passed, độ phủ 100%; grep không in gì | (T01) |
| T02 | `pytest normcore/tests/unit`; `scripts/with_bench.sh 'bench --site normcore.test run-tests --module normcore.api.test_importer && ...test_importer_equipment && ...test_importer_test_system'` | unit 248 passed (gồm test FEAT-004 cũ, không sửa dòng nào); bench: 8, 6, 5 test `OK` (ASM-124: Lead chọn `key_fields` trên NORM-28) | (T02) |
| T03 | `python3 scripts/check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && ...run-tests --module ...test_nc_accounting_import && ...test_nc_account_mapping'` | check_conventions rc=0; 10 test + 3 test `OK` (TC_ACCT_01, 02, 04 trực tiếp, FR_ACCT_011, Auditor, vai trò không quyền). AMD-010 đã áp vào `docs/data-model.md` | (T03) |
| T04 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_accounting_import.test_nc_accounting_import'` | 17 test `OK` (TC_ACCT_02/03/04/06 qua API, sự kiện "Khóa", totals = `golden_engine.ACCOUNTING`, Auditor `finalize` → PermissionError) | (T04) |
