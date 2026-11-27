# Nghiệm thu FEAT-030 (NORM-84)

Người nghiệm thu: QA (Multica). Commit kiểm: 9cede4db3ff54a51132e6f9c07defc5b31e0ddf4. Verdict: **accepted**.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-PRICE-01 (FR-PRICE-001) 302.100 / 92.600 | test_TC_PRICE_01_lap_tu_lan_tinh_khoa chạy trên site sạch, pass | Đạt |
| TC-PRICE-02 (FR-PRICE-002) thiếu căn cứ bị từ chối | test_TC_PRICE_02_thieu_can_cu_tu_choi_gui, pass | Đạt |
| TC-PRICE-03 (FR-PRICE-003) 280.000 cần xác nhận dòng | test_TC_PRICE_03_duoi_gia_thanh_can_xac_nhan_dong, pass | Đạt |
| TC-PRICE-04 (FR-PRICE-004/005) hai khoa | test_TC_PRICE_04_hai_khoa_xac_nhan_lan_luot, pass | Đạt |
| TC-PRICE-05 (FR-PRICE-006/010) lịch sử giá | test_TC_PRICE_05_duyet_ghi_lich_su_gia, pass | Đạt |
| TC-PRICE-06 (FR-PRICE-007/008) cơ quan có thẩm quyền | test_TC_PRICE_06_cap_tham_quyen_ghi_ket_qua, pass | Đạt |
| TC-PRICE-07 (FR-PRICE-009) từ chối về Nháp | test_TC_PRICE_07_tu_choi_ve_nhap_bao_tai_chinh, pass | Đạt |
| TC-OUT-05 (FR-OUT-007) | test_TC_OUT_05_xuat_bang_so_sanh_gia + 2 test unit, pass | Đạt |
| Quyền: vai không quyền, NC Auditor | test_quyen_clinician_khong_doc, test_quyen_auditor_chi_doc, test_auditor_khong_co_transition, test_quyen_hanh_dong, pass | Đạt |
| Site sạch normcore-verify.test, toàn bộ bench | Ran 2163 tests, OK, rc=0 | Đạt |
| pytest unit + golden + độ phủ | 1273 passed; costing/benchmark tổng 98% | Đạt |
| golden_engine, golden_cls, check_conventions, build_rtm | chạy xong, check_conventions rc=0, không vấn đề mới | Đạt |
| Diff test | Không xóa/skip/nới. Đổi duy nhất: test_home 9 -> 10 (ASM-030-18, theo quyết định BA/Lead) | Đạt |
| Tài liệu chỉ đọc, phạm vi | Không đổi docs/srs, test-cases, use-cases, golden, plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI PR #88 | Cả hai job pass | Đạt |

## Giới hạn
Chưa kiểm bằng trình duyệt (Playwright) màn hình SCR-DSK-027: không có tài khoản test theo vai trò cho staging trong run này. Luồng được kiểm qua test API/DocType trên site sạch; giao diện chỉ có test unit (test_feat_030_ui.py).
