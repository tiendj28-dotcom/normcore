# Nghiệm thu FEAT-012 (NORM-39) — QA (Multica), commit b06a8ed9617cd770e5273293907f12ddd8ab1155

| Hạng mục | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Test trên site sạch `normcore-verify.test` (cài app, `run-tests --app normcore`, xóa site, một lần gọi with_bench) | Ran 1115 tests, OK, rc=0 | Đạt |
| pytest unit + golden, độ phủ `costing` + `benchmark` | 566 passed; TOTAL 99% (≥ 90%) | Đạt |
| `golden_engine.py`, `golden_cls.py` | chạy thoát 0 | Đạt |
| `check_conventions.py`, `build_rtm.py docs` | không báo lỗi mới (Must chưa có TC: 0) | Đạt |
| CI PR #51 ở `b06a8ed` | 2 job SUCCESS | Đạt |
| Tài liệu chỉ đọc (srs, test-cases, use-cases, golden, plan, CLAUDE.md, .claude, .autopilot, .github) | không có trong diff | Đạt |
| Diff test: không xóa/skip/nới | 4 tệp test FEAT khác chỉ thêm `confirm_norm_set` trước `lock()` (do FR-NORM-011, Quyết định Lead Q1); `test_FR_AUD_001_khoa_bo_dinh_muc` đổi vế từ-trạng-thái theo ASM-012-17 (Quyết định Lead), assertion giữ nguyên ý | Đạt |
| TC-NORM-01..07, 09..12 | mỗi TC có test `test_TC_NORM_NN_*` (api/test_norm.py, unit, golden), đều qua trong 1115 test | Đạt |
| TC-NORM-03 khớp golden (L03=20, L09=10, L01=10); FR-NORM-016 11 dòng khớp `direct_lines` | tests/golden/test_norm_golden.py | Đạt |
| Quyền: vai trò không quyền (Council) và NC Auditor | `test_quyen_norm_set_council_khong_co_quyen`, `test_quyen_norm_set_auditor_chi_doc`, Finance/Clinician | Đạt |
| Hai lỗ đi vòng FR-NORM-010/011 của Code review lần 1 | test mới `test_TC_NORM_02_insert_truc_tiep...`, `test_khoa_tu_nhap_bi_tu_choi_va_bo_khoa_khong_sua_qua_client` đạt | Đạt |
| Giao diện bằng trình duyệt (SCR-DSK-013/014, 1366×768) | **Chưa kiểm** bằng Playwright; chỉ có test tĩnh `test_norm_grid_ui.py` và `bench build` | Giới hạn, ghi ở As-Built |

Kết luận: accepted.
