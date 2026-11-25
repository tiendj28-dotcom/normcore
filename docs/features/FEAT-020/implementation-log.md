# FEAT-020 — Implementation log

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_library_{sections,validity,search}.py --cov=normcore/library` | 25 passed; sections 99%, validity 97%, search 100%; grep frappe/pypdf/docx rỗng | f07b2fd |
| T02 | `scripts/with_bench.sh 'bench --site normcore.test run-tests --module normcore.nc_library.doctype.nc_legal_document.test_extract'` | Ran 10 tests OK | 99595de |
| T03 | check_conventions.py; `with_bench 'migrate && run-tests --module ...test_nc_legal_document && ...test_permissions && SHOW INDEX FULLTEXT'` | conv=0; Ran 19 OK; permissions Ran 3 OK; có nc_section_ft (heading, plain_text) | 15705ae |
| T04 | `with_bench 'migrate && run-tests --module normcore.api.test_library'` | Ran 20 OK (TC-LIB-01, TC-LIB-03, OCR giả, DOCX, lập lại, Auditor, Version, get_source_view) | 0e5b721 |
