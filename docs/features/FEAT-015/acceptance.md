# Acceptance FEAT-015 — Tính chi phí trực tiếp, giá và bảng giải trình

Người nghiệm thu: QA (Multica, Tester iu), 2026-11-26. Commit đã kiểm: xem `verdict.json`. PR #57.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-COST-01 (11 dòng, tổng 183.963,06) | `test_TC_COST_01_thanh_tien_11_dong_DV_TEST_A` so với `golden_engine.direct_lines`, kèm assert literal 183963.06; test site `test_TC_COST_01_tren_site_tong_truc_tiep_va_gia` | Đạt |
| TC-COST-04 (giá thành, tích lũy, giá tính toán, làm tròn) | `test_TC_COST_04_gia_thanh_tich_luy_lam_tron` so với `golden_engine.run` cho cả hai dịch vụ | Đạt |
| TC-COST-06 (V1, khấu hao bị loại) | `test_TC_COST_06_V1_khong_khau_hao`; QA bổ sung assert tích lũy 11.205,46, giá tính toán 235.314,56, giá làm tròn 235.300 (test-cases mục 2.3); `test_TC_COST_06_bang_giai_trinh_ghi_khau_hao_bi_loai` | Đạt |
| TC-COST-07 (V4) | DV-TEST-A lỗi nêu L05, DV-TEST-B thành công; cả mức engine, runner và trên site | Đạt |
| TC-COST-12 (V3) | `test_TC_COST_12_V3_ON_PRICE` | Đạt |
| TC-COST-13 | `test_TC_COST_13_lam_tron_302150_va_302149_99` → 302.200 / 302.100 | Đạt |
| TC-COST-15 | `test_TC_COST_15_dong_giai_trinh_du_nguon`, `test_TC_COST_15_get_explanation_du_truong` | Đạt |
| TC-COST-17 | `test_TC_COST_17_dich_vu_chua_khoa_bi_liet_ke_va_bo_qua`, `..._check_scope_liet_ke` | Đạt |
| TC-COST-19 | `test_TC_COST_19_tao_lan_tinh_thieu_dau_vao_bi_tu_choi` | Đạt |
| FR-COST-015 (>50 dịch vụ chạy nền) | `test_FR_COST_015_tren_50_dich_vu_chay_nen_co_tien_do` | Đạt |
| Quyền | Clinician bị từ chối, Auditor chỉ đọc, Trưởng khoa theo khoa (`api/test_costing.py`) | Đạt |
| Site sạch | `normcore-verify.test` tạo mới, cài app, `run-tests --app normcore`: Ran 1245 tests, OK; site đã xóa | Đạt |
| pytest unit + golden | 658 passed, 164 subtests; độ phủ costing + benchmark 98,94% (≥ 90) | Đạt |
| golden_engine.py, golden_cls.py | thoát 0 | Đạt |
| build_rtm.py docs | VAN DE: 0 | Đạt |
| check_conventions.py | thoát 0 | Đạt |
| Diff test | Test cũ chỉ thêm `**costing_run_inputs()` / import / `SCOPED`; không xóa, skip, nới assert (đúng Q1, ASM-015-21) | Đạt |
| Tài liệu chỉ đọc | Không đổi srs, test-cases, use-cases, implementation-plan, golden, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI PR #57 | cả hai job pass (gh pr checks) | Đạt |

## Giới hạn
- Giao diện SCR-DSK-022/023 **chưa kiểm bằng trình duyệt**: QA không có tài khoản test theo vai trò cho staging. Giao diện được kiểm bằng `unit/test_costing_ui.py`, `test_form_buttons_i18n.py` và test API theo vai trò.
- Góp ý không chặn: `test_nc_costing_run.py:259` có assert luôn đúng với `direct_labor` (tổng 183.963,06 vẫn được kiểm ở nơi khác); ASM-015-17/18 trùng ý với 22/21.
