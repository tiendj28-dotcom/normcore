# Nghiệm thu FEAT-021: kết quả rework

Commit đã kiểm: `7e85dd14e4b634a65418fe796f9467713946d67f` (head PR #67 sau khi merge develop có NORM-65).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch `normcore-verify.test` | Ran 1684 tests, FAILED (errors=3) | Không đạt |
| TC-LIB-07 | `test_TC_LIB_07_gan_co_thong_bao_hang_doi`: LinkValidationError "Could not find Row #1: Mục văn bản: 3" trong `make_cited` (api/test_library_supersession.py:169) | Không đạt |
| FR-LIB-009 | `test_FR_LIB_009_khop_trich_dan_tu_do`, `test_FR_LIB_009_khong_co_quy_trinh_trich_dan`: cùng lỗi Link ("Văn bản: tt/b3", "Văn bản: TT/KHAC") | Không đạt |
| pytest unit + golden | 984 passed, độ phủ 99% | Đạt |
| TC-LIB-05, 06 | test đạt ở lần chạy trên site sạch | Đạt |

Nguyên nhân: NORM-65 đổi `legal_document`, `legal_section` của NC Procedure Citation sang Link; fixture `make_cited` của FEAT-021 và ASM-021-01 (khớp theo tên hoặc số hiệu gõ tay) không còn đúng.
