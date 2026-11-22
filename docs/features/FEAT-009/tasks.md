# FEAT-009 — Tasks

Lệnh chạy ở gốc kho; `bench` qua `scripts/with_bench.sh`. Pytest dùng `~/frappe-bench/env/bin/python -m pytest`.

- [x] T01 Hàm thuần `normcore/costing/pricing.py` và test (unit + golden) — done-when: `pytest normcore/tests/unit/test_pricing.py normcore/tests/golden/test_material_golden.py` xanh; `grep -n frappe normcore/costing/pricing.py` không in gì
- [x] T02 NC Item, NC Item Price (DocType, quyền, `check_conventions.py`), đổi test đếm DocType 18 → 20 — done-when: `check_conventions.py` thoát 0; `with_bench.sh 'migrate && run-tests --module …test_nc_item && …test_nc_item_price && normcore.tests.test_permissions'` in `OK`
- [x] T03 Bộ nhập `nc_item`, API `normcore/api/item.py` — done-when: `with_bench.sh 'migrate && run-tests --module normcore.api.test_item'` in `OK` (có TC-RES-08, TC-ADM-02)
- [x] T04 SCR-DSK-017: JS form/list, `vi.csv` — done-when: `pytest normcore/tests/unit/test_item_ui_conventions.py` xanh; `with_bench.sh 'migrate && bench build --app normcore'` thoát 0
- [x] T05 Tài liệu: ASM-063..073, As-Built, nhật ký — done-when: `build_rtm.py docs` in `VAN DE: 0`
- [x] T06 Sửa theo Reviewer và Lead (PR #26 @ 95c3a00): AMD-005, `price_code`, bộ nhập đơn giá, khóa đã xác minh, `no_copy`, `getdate`, bỏ mặc định số đơn vị, `material_line` quy đổi đơn vị, API `norm_unit_price`, vi.csv có ngữ cảnh, cuộn ngang, sửa tài liệu — done-when: `with_bench.sh 'migrate && run-tests --module …test_nc_item_price && …test_nc_item && normcore.api.test_item'` in `OK`; `pytest normcore/tests/unit normcore/tests/golden` xanh
- [ ] T07 ASM-074: sau khi tiendj28 duyệt, sửa đúng ba kỳ vọng ở `api/test_importer.py` và docstring `test_permissions.py:1` — done-when: `run-tests --app normcore` in `OK`
- [ ] T08 Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions.py, golden đều xanh
