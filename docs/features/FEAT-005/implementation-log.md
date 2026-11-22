# FEAT-005 — Nhật ký hiện thực (NORM-17)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `python3 docs/tools/build_rtm.py docs`; `git diff --name-only origin/develop...HEAD -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/implementation-plan.md docs/golden` | `VAN DE: 0`; không in gì. Áp AMD-003 (`data-model.md`), AMD-004 (`ux-foundations.md`); ASM-047, 051, 054 dẫn thêm bình luận Lead `01a2028d-…` |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate; run-tests --module …test_nc_specialty; run-tests --module normcore.tests.test_permissions'` | rc=0; 6 tests OK; 3 tests OK (test_co_18_doctype…). Test chặn xóa vì tham chiếu viết ở T03 |
| T03 | `with_bench.sh 'migrate; run-tests --module …test_nc_technical_service; …test_nc_specialty; --test test_TC_SVC_04_nhieu_khoa'` | 4 tests OK; 9 tests OK; `Ran 1 test` OK (viết test và mã cùng lượt, không quan sát bước đỏ riêng) |
| T04 | `with_bench.sh 'run-tests --module …test_nc_technical_service; --test test_TC_SVC_01_nhap_danh_muc; --module normcore.api.test_importer'`; `git diff --stat origin/develop...HEAD -- <tệp khung importer>` | 10 tests OK; `Ran 1 test` OK; 8 tests OK; diff khung rỗng; pytest unit xanh |
| T05 | `pytest normcore/tests/unit/test_chain.py -v`; `grep -n frappe normcore/procedure/chain.py` | 15 passed (đỏ ban đầu 1 test do test tự viết sai kỳ vọng mục không quyền rows=[] theo thiết kế 5.3, đã sửa test mới của chính FEAT); grep không in gì |
