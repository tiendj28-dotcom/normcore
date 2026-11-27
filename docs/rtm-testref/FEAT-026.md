# Test ref — FEAT-026 (NORM-80)

| FR | Test thật |
| :-- | :-- |
| FR-BM-001 | `test_TC_BM_06_don_vi_tham_chieu_bat_buoc`, `test_FR_BM_001_bon_truong_bat_buoc`, `test_FR_BM_001_loai_hinh_chi_cong_lap_hoac_tu_nhan`, `test_FR_BM_001_trung_ten_bi_tu_choi`, `test_quyen_feat_026_don_vi` (nc_benchmark_facility/test_nc_benchmark_facility.py); `test_FR_BM_001_chan_xoa_don_vi_dang_dung` (nc_benchmark_price/test_nc_benchmark_price.py) |
| FR-BM-002 | `test_TC_BM_01_nhap_tep_de_xuat_dich_vu`, `test_FR_BM_002_nhap_mau_khong_trung`, `test_FR_BM_002_mau_nhap_co_dung_cot`, `test_quyen_feat_026_nhap` (api/test_benchmark.py); `test_FR_BM_002_bat_buoc_khi_nhap_tay`, `test_FR_BM_002_ten_hoac_ma`, `test_FR_BM_002_xac_nhan_khi_chua_co_ma_bi_tu_choi` (nc_benchmark_price) |
| FR-BM-004 | `test_TC_BM_01_nhap_tep_de_xuat_dich_vu`, `test_FR_BM_004_xac_nhan_cap_khop` (api/test_benchmark.py); `test_FR_BM_004_trang_thai_ban_dau` (nc_benchmark_price); `test_FR_BM_004_so_khop_ten`, `test_initial_status` (tests/unit/test_benchmark_reference.py) |
| FR-BM-005 | `test_TC_BM_03_so_sanh_chi_dung_gia_da_xac_nhan` (api/test_benchmark.py); `test_FR_BM_005_loc_gia_da_xac_nhan` (tests/unit/test_benchmark_reference.py) |
| FR-BM-006 | `test_TC_BM_04_gia_hieu_chinh`, `test_FR_BM_006_thieu_chi_so`, `test_adjusted_price_lam_tron_half_up`, `test_adjust_du_chi_so` (tests/unit/test_benchmark_reference.py); `test_TC_BM_04_gia_hieu_chinh_tren_site` (api/test_benchmark.py); `test_FR_BM_006_chi_so_gia_theo_thang` (nc_cpi_index/test_nc_cpi_index.py) |
| FR-BM-007 | `test_TC_BM_02_tu_choi_dong_trung` (api/test_benchmark.py và nc_benchmark_price); `test_FR_BM_007_khoa_trung`, `test_FR_BM_007_find_duplicate` (tests/unit/test_benchmark_reference.py) |
| FR-BM-008 | `test_FR_BM_008_phieu_khao_sat` (api/test_benchmark.py, tests/unit/test_price_survey.py); `test_FR_BM_008_nhom_dich_vu_trong`, `test_quyen_feat_026_phieu` (api/test_benchmark.py); tests/unit/test_feat_026_ui.py |
