# Test ref — FEAT-028 (NORM-81)

| FR | Test thật |
| :-- | :-- |
| FR-ADJ-001 | `test_TC_ADJ_01_chon_gia_trong_24_thang`, `test_select_prices_sau_ngay_tinh_va_hoa_ngay`, `test_window_start` (tests/unit/test_benchmark_stats.py); `test_FR_ADJ_001_chi_gia_xac_nhan_cung_loai_gia`, `test_TC_ADJ_01_cua_so_24_thang_tren_site` (api/test_price_compare.py) |
| FR-ADJ-002 | `test_TC_ADJ_02_trung_vi_va_do_lech`, `test_median`, `test_deviation_median_zero`, `test_use_adjusted` (tests/unit/test_benchmark_stats.py) |
| FR-ADJ-003 | `test_FR_ADJ_003_duoi_nguong_chua_du_du_lieu` (tests/unit/test_benchmark_stats.py); `test_TC_ADJ_03_chua_du_du_lieu`, `test_TC_ADJ_03_khong_sinh_goi_y_khi_chua_du_du_lieu` (api/test_price_compare.py) |
| FR-ADJ-004 | `test_FR_ADJ_004_loc_don_vi` (tests/unit/test_benchmark_stats.py); `test_FR_ADJ_004_loc_tinh_lai` (api/test_price_compare.py) |
| FR-ADJ-005 | `test_TC_ADJ_04_goi_y_dv_test_a`, `test_FR_ADJ_005_trong_nguong_khong_goi_y`, `test_FR_ADJ_005_lech_am_chi_quy_tac_tang`, `test_rule_001_…` đến `test_rule_007_…` (tests/unit/test_benchmark_rules.py); `test_FR_ADJ_005_sinh_goi_y_vuot_nguong`, `test_FR_ADJ_005_sinh_lai_khong_trung`, `test_FR_ADJ_005_trong_nguong_khong_goi_y` (api/test_price_compare.py) |
| FR-ADJ-008 | `test_FR_ADJ_008_tu_choi_can_ly_do`, `test_FR_ADJ_008_chap_nhan_luu_nguoi_va_thoi_diem`, `test_FR_ADJ_008_chap_nhan_can_sua_quy_trinh_bi_chan`, `test_quyen_quyet_dinh_goi_y` (api/test_price_compare.py); `test_FR_ADJ_008_validate_tu_choi_can_ly_do`, `test_sua_ngoai_api_bi_chan` (nc_adjustment_suggestion/test_nc_adjustment_suggestion.py) |
| FR-ADJ-010 | `test_FR_ADJ_010_co_cau_tong_bang_gia_thanh` (tests/unit/test_benchmark_stats.py); `test_TC_ADJ_08_co_cau_gia` (api/test_price_compare.py) |
| Quyền DocType | `test_quyen_clinician_khong_doc`, `test_quyen_auditor_chi_doc`, `test_quyen_truong_khoa_theo_khoa`, `test_quyen_theo_ma_tran`, `test_quyen_finance_tao` (nc_adjustment_suggestion); `test_quyen_so_sanh_truong_khoa_auditor` (api/test_price_compare.py) |
| Giao diện | tests/unit/test_feat_028_ui.py |
