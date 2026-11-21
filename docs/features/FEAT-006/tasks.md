# FEAT-006 — Tasks

- [ ] T01 Hàm thuần `normcore/procedure/` (codes, steps, copying) + test đơn vị `test_TC_PROC_03_*` — done-when: `pytest normcore/tests/unit -k TC_PROC_03 -v` ≥ 1 passed (S001..S003, đổi 1↔3 giữ mã, xóa S002, bước mới S004)
- [ ] T02 DocType: trường mới của NC Clinical Procedure + NC Procedure Citation, DI-02, ràng buộc trích dẫn, danh sách chuẩn; đổi `test_co_14_*` → 15 (Q4); AMD-001 — done-when: `bench --site normcore.test migrate` OK; `bench --site normcore.test run-tests --module normcore.nc_procedure.doctype.nc_clinical_procedure.test_nc_clinical_procedure` OK; `bench --site normcore.test run-tests --module normcore.tests.test_permissions` OK
- [ ] T03 API tạo / tìm bản có / đọc / lưu phần / sao chép (`test_TC_PROC_01`, `_02`, `FR_PROC_013`, Q3) — done-when: `bench --site normcore.test run-tests --module normcore.api.test_procedure` OK
- [ ] T04 API bước: sửa, xóa, sắp lại (`test_TC_PROC_03` tích hợp) — done-when: như T03
- [ ] T05 API nguồn lực + gợi ý (`test_TC_PROC_04`, `FR_PROC_005`) — done-when: như T03
- [ ] T06 API trích dẫn (`test_TC_PROC_09`) và lịch sử (`test_TC_PROC_08`) — done-when: như T03
- [ ] T07 Test quyền: NC Finance và NC Auditor bị `PermissionError` ở mọi hàm ghi; bản không Nháp bị từ chối — done-when: như T03
- [ ] T08 Giao diện SCR-DSK-009 (Vue) + SCR-DSK-007 (list settings) + vi.csv — done-when: `pytest normcore/tests/unit -k ui_conventions` xanh; `bench build --app normcore` thành công
- [ ] T09 Tài liệu: ASM-017.., AMD-001, ASM-011 cập nhật, `as-built/FEAT-006.md`, `implementation-log.md`, RTM — done-when: `python3 docs/tools/build_rtm.py docs` 0 vấn đề
- [ ] T10 Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions.py, golden đều xanh
