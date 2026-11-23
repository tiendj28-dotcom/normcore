# Test ref — FEAT-001, FEAT-004 và FEAT-005 (ghi bởi kiểm định độc lập NORM-14, NORM-17)

| FR | Test thật |
| :-- | :-- |
| FR-ACC-001 | `test_TC_ACC_05_guest_bi_tu_choi`, `test_TC_ACC_05_desk_chuyen_ve_trang_dang_nhap` |
| FR-ACC-002 | `test_quyen_theo_vai_tro`, `test_auditor_chi_doc_duoc`, `test_TC_ACC_04_*` (unit/test_permission_matrix.py) |
| FR-ACC-003 | `test_TC_ACC_01_phamvi_khoa_ghi_doc`, `test_TC_ACC_01_doc_theo_q3`, `test_TC_ACC_01_chua_gan_khoa_khong_ghi_duoc`, `test_TC_ACC_01_vai_tro_khac_khong_bi_hep` |
| FR-ACC-004 | `test_TC_ACC_02_clinician_khong_xem_so_lieu_tai_chinh` |
| FR-ACC-005 | `test_TC_ACC_03_mo_ban_ghi_ngoai_pham_vi_khong_lo_gia_tri` |
| FR-ACC-006 | `test_FR_ACC_006_gan_va_bo_gan_co_hieu_luc_ngay`, `test_FR_ACC_006_vai_tro_khac_gan_khoa_bi_tu_choi`, `test_FR_ACC_006_nhieu_khoa_va_gan_lap_khong_trung` |
| FR-ADM-004 | `test_TC_ADM_04_khoa_thieu_truong_bat_buoc_bi_tu_choi`, `test_TC_ADM_04_khoa_can_lam_sang_co_trung_tam_chi_phi`, `test_TC_ADM_04_trung_tam_chi_phi_thieu_truong_bi_tu_choi` |
| FR-ADM-005 | `test_TC_ADM_05_xoa_danh_muc_dang_duoc_tham_chieu`, `test_TC_ADM_05_admin_xoa_duoc_danh_muc_khong_ai_tham_chieu`, `test_TC_ADM_05_vai_tro_khac_khong_xoa_duoc` |
| FR-ADM-002 | `test_TC_ADM_02_tai_mau_roi_nhap_lai_chinh_tep_do` (api/test_importer.py), 17 test `test_FR_ADM_002_*` (unit/test_importer.py) |
| FR-SVC-001 | `test_TC_SVC_01_nhap_danh_muc`, `test_FR_SVC_001_gan_chuyen_khoa`, `test_FR_SVC_001_cap_nhat_theo_ma`, `test_FR_SVC_001_chuyen_khoa_la`, `test_FR_SVC_001_tai_mau_nhap_lai`, `test_FR_SVC_001_vai_tro_chi_doc_bi_tu_choi` (nc_technical_service); `test_FR_SVC_001_*` (nc_specialty) |
| FR-SVC-002 | `test_TC_SVC_01_nhap_danh_muc`, `test_FR_SVC_002_thieu_ma` |
| FR-SVC-003 | `test_TC_SVC_04_nhieu_khoa`, `test_FR_SVC_003_trung_khoa_bi_tu_choi`, `test_FR_SVC_003_vai_tro_chi_doc_khong_sua` |
| FR-SVC-004 | `test_TC_SVC_03_tinh_trang_chuoi`, `test_FR_SVC_004_*` (api/test_service.py), `normcore/tests/unit/test_chain.py` |
