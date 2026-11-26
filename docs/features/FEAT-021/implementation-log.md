# FEAT-021: Nhật ký hiện thực (NORM-64)

Nhánh `feat/FEAT-021-thay-the-van-ban`. Mỗi task một commit `FEAT-021 Tnn: …`. Mọi lệnh bench chạy qua `scripts/with_bench.sh`.

| Task | Việc đã làm | Lệnh và kết quả |
| :-- | :-- | :-- |
| T01 | DocType NC Legal Supersession (bảng con, 4 trường); NC Legal Document thêm `supersession_section`, `supersessions`, `superseded_by_html` | `with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore --module normcore.nc_library.doctype.nc_legal_document.test_nc_legal_document'`: Ran 19 OK; `check_conventions.py` thoát 0 |
| T02 | `library/supersession.py` + `tests/unit/test_library_supersession.py` | `PYTHONPATH=. pytest normcore/tests/unit/test_library_supersession.py --cov=normcore.library.supersession --cov-fail-under=90`: 10 passed, độ phủ 100% (dùng `~/frappe-bench/env/bin/python -m pytest`; `PYTHONPATH=.` vì `apps/normcore` đang trỏ checkout khác) |
| T03 | `procedure/review.py` + `tests/unit/test_procedure_review.py` | `PYTHONPATH=. pytest normcore/tests/unit/test_procedure_review.py --cov=normcore.procedure.review --cov-fail-under=90`: 7 passed, độ phủ 99% |
| T04 | `validate` (check_supersessions) + `on_update` → `api.library.apply_supersessions`; API `declare_supersession`, `get_supersessions`; `api/test_library_supersession.py` (5 test: TC-LIB-05, TC-LIB-06, kiểm khi lưu, hai văn bản cùng thay B, quyền) | `with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore --module normcore.api.test_library_supersession'`: Ran 5 OK |
