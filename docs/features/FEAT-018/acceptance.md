# Nghiệm thu FEAT-018 (QA độc lập)

Commit đã kiểm: `92c1c9d6e0bd92791320875cdc63d57475ee2010` (đã chứa develop `e5edabf`).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch, toàn bộ test | `normcore-verify.test` tạo mới, cài app, `run-tests --app normcore`: Ran 1722 tests, OK; site đã xóa | Đạt |
| pytest unit + golden, độ phủ | 993 passed; tổng 99% (snapshot.py 100%) | Đạt |
| Golden | `golden_engine.py`, `golden_cls.py` thoát 0 | Đạt |
| `check_conventions.py` / `build_rtm.py docs` | thoát 0 / VAN DE: 0 | Đạt |
| TC-COST-09 (khóa, đổi đơn giá, tái lập trùng) | test cùng mã ở `test_nc_costing_run_lock.py`, `test_snapshot_compare_golden.py`; chạy trong bench | Đạt |
| TC-COST-11 (từ chối tính lại, nhân bản về Nháp) | test cùng mã, qua `run_costing` và API | Đạt |
| TC-COST-18 (DV-TEST-A −63.636,36 theo cấu phần) | số lấy từ golden `g.run()`, không chép cứng | Đạt |
| Vai trò không quyền / NC Auditor | `test_costing_lock.py`: Clinician bị từ chối; Auditor chỉ đọc | Đạt |
| Diff test | không xóa/skip/nới dòng test nào | Đạt |
| Tài liệu chỉ đọc | không bị sửa | Đạt |
| CI PR #69 | cả hai job pass | Đạt |
| Giao diện trình duyệt (Playwright) | Chưa kiểm: staging chưa có mã (PR chưa merge) và không có tài khoản test; giao diện kiểm tĩnh + qua API/test | Ghi chú |
