# Nghiệm thu FEAT-021: Thay thế văn bản và hàng đợi rà soát

Commit đã kiểm: `4489a1a3391b642b461172ff8c03c8cb400317e1` (PR #67). Người kiểm: Tester iu (QA độc lập). Lần kiểm này thay thế kết quả rework trước đó.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-LIB-05 (FR-LIB-007) | `test_TC_LIB_05_thay_toan_bo` | Đạt |
| TC-LIB-06 (FR-LIB-008) | `test_TC_LIB_06_thay_mot_phan` | Đạt |
| TC-LIB-07 (FR-LIB-009) | `test_TC_LIB_07_gan_co_thong_bao_hang_doi` | Đạt |
| UC-002 bước 7, luồng 5a | `test_FR_LIB_009_khong_can_sua_go_co`, `test_FR_LIB_009_khong_co_quy_trinh_trich_dan` | Đạt |
| Quyền (vai không quyền, NC Auditor) | `PermissionError` ở api/test_library_supersession.py, api/test_review_queue.py | Đạt |
| Site sạch `normcore-verify.test` | `bench run-tests --app normcore`: Ran 1772 tests, OK; site đã xóa | Đạt |
| pytest unit + golden | 1045 passed, độ phủ 99% | Đạt |
| check_conventions | không mục nào thuộc FEAT-021 | Đạt |
| Diff test | không test bị xóa/skip/nới so với develop | Đạt |
| Tài liệu chỉ đọc | không bị sửa | Đạt |
| CI PR #67 | job tài liệu pass; job site ở commit merge-sync đang chạy lúc kiểm (CI `692908a` đã xanh, FEAT-021 không đổi) | Đạt (theo dõi) |

Hạn chế: vai trò kiểm ở mức API/test; chưa thao tác giao diện bằng Playwright.
