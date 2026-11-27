# FEAT-038 — Nhật ký hiện thực

Bench qua `scripts/with_bench.sh`. pytest chạy bằng `~/frappe-bench/env/bin/python -m pytest`.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T02 (làm trước T01 vì fixture của T01 cần tài liệu của hãng) | `pytest normcore/tests/unit/test_library_manufacturer.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module …test_nc_legal_document_manufacturer && … --module …test_nc_legal_document'`; `check_conventions.py` | pytest 3 passed; bench OK (3 test) và OK (19 test); conventions thoát 0 | xem `git log` (`FEAT-038 T02`) |
