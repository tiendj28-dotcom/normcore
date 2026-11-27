# Nghiệm thu FEAT-025 (QA Multica, commit f2e4bd3)

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch normcore-verify.test, toàn bộ `run-tests --app normcore` | 1921 test, OK, site đã xóa | Đạt |
| pytest unit + golden + độ phủ | 1138 passed; costing+benchmark 98.89% | Đạt |
| golden_engine, golden_cls, check_conventions, build_rtm | thoát 0; build_rtm không thêm vấn đề mới (Must chưa có TC: 0) | Đạt |
| CI PR #74 | cả 2 job pass | Đạt |
| FR-AI-006 (1)(2) bằng quy tắc, không gọi AI | `test_FR_AI_006_nguon_luc_thieu_o_chuan_bi`, `..._khong_co_buoc_chuan_bi`, `..._buoc_thieu_nguoi_thuc_hien` | Đạt |
| FR-AI-006 (3) chống chỉ định do AI; lọc đề xuất | `test_FR_AI_006_kiem_tra_nhat_quan_co_ai`, `..._loc_de_xuat_chong_chi_dinh` | Đạt |
| UC-005 6a: AI không khả dụng vẫn trả (1)(2) | `test_UC005_6a_ai_khong_kha_dung_van_kiem_quy_tac`, `test_FR_AI_006_ai_tat_hoac_khong_co_chong_chi_dinh` | Đạt |
| FR-AI-007 đề xuất kèm độ tin cậy, nhãn `ai_suggested` | `test_FR_AI_007_khoi_tao_de_xuat_lien_ket`, `..._loc_ung_vien`, `..._loc_de_xuat_lien_ket` | Đạt |
| UC-009 8a: còn đề xuất chặn xác nhận | `test_UC009_8a_de_xuat_chua_xu_ly_chan_xac_nhan` | Đạt |
| Chấp nhận/bỏ/sửa gỡ nhãn; AI lỗi không đề xuất | `test_FR_AI_007_chap_nhan_bo_sua_de_xuat*`, `..._sua_truc_tiep_bo_nhan_de_xuat`, `..._ai_tat_hoac_loi_khong_de_xuat` | Đạt |
| Tác vụ nền không gọi được qua HTTP | `test_FR_AI_007_tac_vu_nen_khong_goi_duoc_qua_http` | Đạt |
| Quyền: không quyền, NC Auditor (chỉ đọc), Finance, khoa khác | `test_FR_AI_006_quyen_kiem_tra_nhat_quan`, `test_FR_AI_007_quyen_de_xuat_lien_ket` | Đạt |
| Chỉ dùng provider giả, dùng chung gateway/nhật ký AI | đọc test và diff | Đạt |
| Diff test: không xóa/skip/nới test cũ (chỉ thêm 6 tệp test); tài liệu chỉ đọc không đổi (data-model.md chỉ thêm `ai_confidence` theo AMD-025-01) | `git diff origin/develop...HEAD` | Đạt |

Ghi chú: site `normcore-verify.test` còn sót từ lần chạy bị cắt giờ đã được xóa trước khi chạy lại. TC-AI trong test-cases.md không gắn FR-AI-006/007; test mang mã FR/UC theo ASM-025-01.

Giới hạn: giao diện (SCR-DSK-009 nút "Kiểm tra nhất quán", form NC Norm Set) chưa kiểm bằng trình duyệt vì staging chưa có mã của PR và không có tài khoản test được cấp; chỉ có kiểm tĩnh `test_feat_025_ui.py`.
