# FEAT-021: Nhật ký hiện thực (NORM-64)

Nhánh `feat/FEAT-021-thay-the-van-ban`. Mỗi task một commit `FEAT-021 Tnn: …`. Mọi lệnh bench chạy qua `scripts/with_bench.sh`.

| Task | Việc đã làm | Lệnh và kết quả |
| :-- | :-- | :-- |
| T01 | DocType NC Legal Supersession (bảng con, 4 trường); NC Legal Document thêm `supersession_section`, `supersessions`, `superseded_by_html` | `with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore --module normcore.nc_library.doctype.nc_legal_document.test_nc_legal_document'`: Ran 19 OK; `check_conventions.py` thoát 0 |
