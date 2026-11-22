# FEAT-005 — Nhật ký hiện thực (NORM-17)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `python3 docs/tools/build_rtm.py docs`; `git diff --name-only origin/develop...HEAD -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/implementation-plan.md docs/golden` | `VAN DE: 0`; không in gì. Áp AMD-003 (`data-model.md`), AMD-004 (`ux-foundations.md`); ASM-047, 051, 054 dẫn thêm bình luận Lead `01a2028d-…` |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate; run-tests --module …test_nc_specialty; run-tests --module normcore.tests.test_permissions'` | rc=0; 6 tests OK; 3 tests OK (test_co_18_doctype…). Test chặn xóa vì tham chiếu viết ở T03 |
