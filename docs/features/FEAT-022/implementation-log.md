# FEAT-022 — implementation-log

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_library_mapping.py --cov=normcore.library.mapping --cov-report=term-missing` | 17 passed; độ phủ `mapping.py` xem dòng lệnh; `grep -n "import frappe" normcore/library/mapping.py` không in gì. Hiệu năng 5.000 dịch vụ × 300 mục < 5 giây (test dùng từ vựng 300 từ; số học Dice bằng số nguyên half-up thay Decimal để nhanh, cùng kết quả). |
| T02 | `scripts/with_bench.sh 'bench --site normcore.test migrate && run-tests --module ...test_nc_section_service_map && run-tests --module ...test_nc_legal_document'`; `python3 scripts/check_conventions.py` | 4 test OK (đóng dấu, đổi dịch vụ, trùng dịch vụ, quyền Auditor/Clinician/DC/không vai trò); 19 test NC Legal Document OK; check_conventions thoát 0 |
