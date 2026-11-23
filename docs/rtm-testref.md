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
| FR-AUD-001 | `test_TC_AUD_01_lich_su_va_su_kien`, `test_FR_AUD_001_khoa_bo_dinh_muc`, `test_FR_AUD_001_xoa_de_lai_su_kien_va_gia_tri_truoc`, `test_FR_AUD_001_lan_tinh_gia_thanh_cong_mot_su_kien_moi_lan_chuyen` (nc_core/.../test_nc_audit_event.py) |
| FR-AUD-002 | `test_TC_AUD_02_ban_ghi_bat_bien`, `test_FR_AUD_002_khong_tao_ngoai_ma_may_chu` |
| FR-AUD-003 | `test_TC_AUD_03_loc_theo_quy_trinh`, `test_FR_AUD_003_loc_nguoi_thoi_gian_va_quyen`, `test_FR_AUD_003_to_time_chi_co_ngay_lay_tron_ngay` |
| FR-AUD-004 | `test_FR_AUD_004_ghi_xuat_tep` (điểm ghi; luồng xuất thuộc FEAT-019) |

## FEAT-011 (kiểm định độc lập NORM-20)

| FR | Test thật |
| :-- | :-- |
| FR-RES-009 | `test_TC_CLS_50_bo_moi_co_ba_tham_so_mac_dinh`, `test_TC_CLS_50_mac_dinh_ba_tham_so_moi` |
| FR-RES-010 | `test_TC_RES_05_bac_si`, `test_TC_RES_05_dieu_duong`, `test_TC_RES_05_golden_don_gia_gio_cong`, `test_TC_RES_05_don_gia_gio_cong_tren_doc` |
| FR-RES-011 | `test_TC_RES_06_bo_da_khoa_khong_sua_duoc`, `test_TC_RES_06_bo_co_is_locked_khong_sua_duoc`, `test_TC_RES_06_nhan_ban_thanh_bo_moi_sua_duoc` |
| FR-RES-015 | `test_TC_RES_11_thieu_cap_phe_duyet_bi_tu_choi_roi_luu_duoc`, `test_TC_RES_11_cap_phe_duyet_ngoai_danh_sach_bi_tu_choi` |
