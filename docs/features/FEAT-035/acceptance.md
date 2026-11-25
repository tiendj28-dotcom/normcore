# Nghiệm thu FEAT-035 — Sản lượng cận lâm sàng và xuất kho

Commit đã kiểm: xem `verdict.json` (head PR #43 sau khi thêm test quyền của QA). Người kiểm: Tester iu (QA độc lập).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-CLS-34 (sản lượng Thực tế, mã LIS đổi sang mã dịch vụ, cột phụ trống được chấp nhận) | `test_TC_CLS_34_ma_lis_doi_sang_ma_dich_vu_cot_trong_duoc_chap_nhan` (`api/test_importer_cls_volume.py`), unit `test_TC_CLS_34_...`; chạy xanh | Đạt |
| TC-CLS-35 (mã hệ thống lạ, số âm: hai dòng lỗi, dòng khác vẫn lưu) | `test_TC_CLS_35_ma_he_thong_la_va_so_am_bao_loi_dong_dung_van_luu`, `test_TC_CLS_35_ma_dich_vu_ma_khoa_khong_khop_va_so_phu_sai`, unit `test_TC_CLS_35_so_am` | Đạt |
| TC-CLS-36 (xuất kho HC_GLU 94 hộp khoa XN, lưu theo mặt hàng, khoa, năm) | `test_TC_CLS_36_xuat_kho_theo_mat_hang_khoa_nam`, unit `test_TC_CLS_36_stock_hop_le` | Đạt |
| DI-14, FR-ACCT-012..015 | `test_DI_14_trung_nam_kich_ban_he_thong`, `test_trung_bon_truong`, `test_luu_va_trung_nam_khoa_mat_hang` | Đạt |
| Quyền: vai trò không quyền, NC Auditor, NC Department Head theo khoa | Test quyền của 3 DocType mới (Dev) cộng test QA bổ sung `test_quyen_truong_khoa_chi_doc_khoa_minh` cho NC Stock Issue Actual và NC Equipment Usage: Head chỉ thấy khoa được gán, không ghi; Auditor đọc mọi khoa, không ghi | Đạt |
| Bench `run-tests --app normcore` | `normcore.test` sau migrate: 736 test, 44 lỗi ngoài FEAT (xem Giới hạn); các module FEAT-035 (importer cls volume 8, stock issue 4, equipment usage 6) xanh | Đạt (FEAT-035) |
| CI "Test trên site Frappe v15" | run 45568804074 trên `1f4ba82`: xanh; CI của head cuối xem bình luận QA | Đạt |
| pytest unit + golden + độ phủ | 365 passed; costing 99% | Đạt |
| golden_engine, golden_cls, `check_conventions.py`, `build_rtm.py docs` | chạy không lỗi; VAN DE: 0 | Đạt |
| Diff test cũ | `api/test_importer.py` thêm 3 khóa vào danh sách bộ nhập, vẫn `assertEqual` đủ danh sách (ASM-035-09, Lead duyệt); `api/test_system.py` là mã sản phẩm, không phải test; không xóa, skip, nới | Đạt |
| Tài liệu chỉ đọc | không bị sửa | Đạt |
| Phạm vi | NC Service Volume không đổi (ASM-035-11); chỉ mở rộng khung nhập tương thích ngược (ASM-035-01) | Đạt |

## Giới hạn
- Không có site sạch cục bộ (QA thiếu `DB_ROOT_PASSWORD`, `bench new-site` bị MySQL từ chối). Lead quyết dùng job CI "Test trên site Frappe v15" thay (run 45568804074, dựng site mới, cài app, `run-tests --app normcore`); ghi ASM-035-13.
- Trên site dùng chung `normcore.test` có 44 lỗi: 41 `WorkflowPermissionError` Nháp → Đã ban hành và 3 trùng khóa `QT-DV-TEST-A-KHOA-TEST-v1`, ở test của FEAT khác (TC-ACC, TC-AUD, TC-CLS-44...). Nhiều khả năng do workflow hoặc dữ liệu từ nhánh khác trên site dùng chung (PR #45 FEAT-007 sửa workflow phê duyệt). Không lỗi nào ở TC-CLS-34/35/36. Không phải lý do rework.
- Giao diện SCR-DSK-037 và nút trên SCR-DSK-021 chưa kiểm bằng Playwright: staging chạy develop nên chưa có. Kiểm sau khi merge và deploy staging (như FEAT-033), không chặn In Review.
