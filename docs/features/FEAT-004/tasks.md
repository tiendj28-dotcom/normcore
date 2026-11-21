# FEAT-004 — Tasks

- [x] T01 `core/importer.py` + `core/import_sets.py` + test đơn vị `test_FR_ADM_002_*` — done-when: `pytest normcore/tests/unit -k FR_ADM_002 -v` ≥ 8 passed
- [x] T02 API `api/importer.py` + test tích hợp `test_TC_ADM_02_*`, quyền — done-when: `bench --site normcore.test run-tests --module normcore.api.test_importer` OK
- [x] T03 Trang Desk `import-excel`, workspace Normcore, vi.csv, test quy ước giao diện — done-when: `pytest normcore/tests/unit -k import_ui` xanh; `bench migrate` OK
- [x] T04 Tài liệu: ASM-026.., AMD-002, As-Built, nhật ký — done-when: `python3 docs/tools/build_rtm.py docs` 0 vấn đề
- [x] T05 Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions, ruff đều xanh
