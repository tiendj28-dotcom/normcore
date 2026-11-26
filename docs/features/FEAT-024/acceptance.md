# Nghiệm thu FEAT-024 (QA Multica, commit 5388fab)

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch normcore-verify.test, toàn bộ `run-tests --app normcore` | 1691 test, OK, site đã xóa | Đạt |
| pytest unit + golden + độ phủ | 967 passed; costing 99% | Đạt |
| golden_engine, golden_cls, build_rtm, check_conventions | chạy OK, không thêm vấn đề mới | Đạt |
| CI PR #66 | cả 2 job pass | Đạt |
| TC-AI-01 (5 bước, trích dẫn, nguồn đã xác nhận) | `test_TC_AI_01_du_thao_5_buoc_co_trich_dan` | Đạt |
| TC-AI-02 (loại trích dẫn sai, "Chưa có căn cứ", nhật ký) | 3 test `test_TC_AI_02_*` | Đạt |
| TC-AI-03 (Khác biệt, lý do từ yêu cầu) | `test_TC_AI_03_khac_biet_lay_ly_do_tu_yeu_cau` | Đạt |
| TC-AI-04 (cảnh báo, Chưa có căn cứ) | `test_TC_AI_04_khong_co_nguon_canh_bao_roi_chua_co_can_cu` | Đạt |
| TC-AI-10 (từ chối gửi duyệt khi còn Đề xuất) | `test_TC_AI_10_con_de_xuat_tu_choi_gui_duyet` | Đạt |
| FR-AI-001..005, 008, UC-004 1a/1b/4a | có test cùng mã (rtm-testref) | Đạt |
| Quyền: vai không quyền, NC Auditor, khoa khác | `test_quyen_ai_draft` (PermissionError) | Đạt |
| Diff test: không xóa/skip/nới test cũ; tài liệu chỉ đọc không đổi | `git diff origin/develop...HEAD` | Đạt |
| Chỉ dùng provider giả lập | test dùng FakeProvider | Đạt |

Giới hạn: giao diện (SCR-DSK-008/009) chưa kiểm bằng trình duyệt vì staging chưa có mã của PR; chỉ có kiểm tĩnh `test_feat_024_ui.py`.
