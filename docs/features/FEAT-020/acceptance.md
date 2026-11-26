# Nghiệm thu FEAT-020 — Thư viện văn bản: nạp, tách mục, hiệu lực, tìm kiếm

Người kiểm: QA (Multica), độc lập với Dev. Commit đã kiểm: `27eccbf` (nhánh `feat/FEAT-020-thu-vien-van-ban`, base `develop` `223e8af`).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch, toàn bộ test | `with_bench.sh 'new-site normcore-verify.test … --install-app normcore && run-tests --app normcore; drop-site'` → Ran 968 tests, OK, site đã xóa | Đạt |
| pytest unit + golden + độ phủ | 483 passed, 67 subtests; độ phủ costing+benchmark 99% (≥ 90%) | Đạt |
| golden_engine, golden_cls, build_rtm, check_conventions | golden exit 0; build_rtm không vấn đề mới; check_conventions exit 0 | Đạt |
| TC-LIB-01 | `test_TC_LIB_01_nap_pdf_tach_3_muc` (api/test_library.py): bản ghi "Chưa lập", sau tác vụ nền 3 mục cấp 1, "Đã lập" | Đạt |
| TC-LIB-02 | `test_TC_LIB_02_trung_so_hieu` (test_nc_legal_document.py) | Đạt |
| TC-LIB-03 | `test_TC_LIB_03_tep_hong_bao_loi` (api/test_library.py): "Lỗi", có lý do, thông báo người tải | Đạt |
| TC-LIB-04 | `test_TC_LIB_04_hieu_luc_theo_ngay` (api/test_library_validity.py): ngày giả lập | Đạt |
| TC-LIB-08 | `test_TC_LIB_08_tim_theo_cum_tu_va_ma_dich_vu` (api/test_library_search.py) | Đạt |
| FR-LIB-001..006, 010..012 | Mỗi FR có test `test_FR_LIB_*` (xem `docs/rtm-testref.md`) | Đạt |
| Quyền | `test_FR_ACC_002_…`, `test_FR_ACC_007_auditor_chi_doc` (NC Auditor chỉ đọc), test get_sections/get_source_view cần quyền đọc, test vai trò không quyền | Đạt |
| Soát diff test | Không có dòng test bị xóa; không skip/expectedFailure; mọi tệp test đều mới | Đạt |
| Phạm vi | 44 tệp, đều thuộc FEAT-020 và tệp chung đã khai trong thiết kế | Đạt |
| Tài liệu chỉ đọc | Không đổi srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI của PR #49 | `gh pr checks 49`: cả hai job pass | Đạt |
| Tính tiền / golden | FEAT không có phép tính tiền | Không áp dụng |
| Giao diện trình duyệt | Chưa kiểm: staging chưa có mã của PR (chưa merge); luồng và quyền đã kiểm qua test tích hợp trên site sạch | Chưa kiểm (ghi As-Built) |

**Verdict: accepted.**
