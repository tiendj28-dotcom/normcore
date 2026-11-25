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

## FEAT-010 (kiểm định độc lập NORM-19)

| FR | Test thật |
| :-- | :-- |
| FR-RES-005 | `test_FR_RES_005_thieu_nguon_hinh_thanh_bi_tu_choi`, `test_FR_RES_005_trung_ma_bi_tu_choi`, `test_FR_RES_005_thong_bao_tieng_viet_khong_lo_ten_truong` |
| FR-RES-006 | `test_TC_RES_03_eq1_khau_hao_va_don_gia_gio`, `test_TC_RES_03_api_eq1`, `test_FR_RES_006_thieu_ban_ghi` |
| FR-RES-007 | `test_TC_RES_04_v2_zero`, `test_TC_RES_04_v2_continue`, `test_TC_RES_04_v2_het_thoi_gian_su_dung_theo_bo_tham_so` |
| FR-RES-008 | `test_TC_RES_10_thieu_gio_khai_thac_bi_tu_choi_roi_r1_luu_duoc`, `test_FR_RES_008_gio_khong_hop_le_bi_tu_choi`, `test_FR_RES_008_trung_ma_bi_tu_choi` |
| FR-RES-012 | `test_FR_RES_012_nhap_phong`, `test_FR_RES_012_tai_mau_roi_nhap_lai_khong_trung` (api/test_importer_equipment.py) |
| FR-RES-019 | `test_TC_CLS_48_thue_thieu_chi_phi_hop_dong_bi_tu_choi`, `test_TC_CLS_48_mua_thieu_nguyen_gia_bi_tu_choi`, `test_FR_RES_019_dat_theo_hoa_chat_luu_duoc_gia_tri_hop_dong` |
| FR-RES-020 | `test_TC_CLS_48_thue_thieu_chi_phi_hop_dong_bi_tu_choi` (phần còn lại thuộc TC-CLS-12, FEAT-036) |
| FR-RES-021 | `test_FR_RES_021_dat_theo_hoa_chat_khong_khau_hao` (TC-CLS-07 thuộc FEAT-036) |
| FR-RES-022 | `test_TC_CLS_48_thieu_tieu_chi_chia_bi_tu_choi`, `test_TC_CLS_48_chia_theo_so_ket_qua_khong_can_gio_ke_hoach` |
| FR-RES-023 | `test_FR_RES_023_linh_kien_theo_thang_va_khong_hop_le`, `test_FR_RES_023_thieu_tuoi_tho_theo_bi_tu_choi` |
| FR-RES-024 | `test_TC_CLS_49_ty_le_theo_khoa`, `test_TC_CLS_49_ty_le_khoa` |
| FR-RES-025 | `test_TC_CLS_49_ty_le_theo_khoa`, `test_FR_RES_025_khoa_quan_ly_ngoai_bang_ty_le_bang_0` |
| FR-RES-026 | `test_FR_RES_026_luu_truong_dien` |

# Test ref — FEAT-009 (ghi bởi kiểm định độc lập NORM-18)

| FR | Test thật |
| :-- | :-- |
| FR-RES-001 | `test_TC_RES_09_thieu_don_vi_tinh_bi_tu_choi_roi_luu_duoc`, `test_FR_RES_001_thieu_ma_ten_loai_bi_tu_choi`, `test_FR_RES_001_so_lan_dung_phai_tu_1` |
| FR-RES-002 | `test_TC_CLS_46_nguon_hop_dong_co_ngay_het_hieu_luc_luu_duoc`, `test_FR_RES_002_thieu_truong_bat_buoc_bi_tu_choi`, `test_FR_RES_002_nam_nguon_gia` |
| FR-RES-003 | `test_TC_RES_02_chung_tu_cu_25_thang_canh_bao_van_tinh`, `test_TC_RES_02_chung_tu_cu_25_thang`, `test_FR_RES_003_dung_24_thang_khong_canh_bao` |
| FR-RES-004 | `test_TC_RES_01_ba_gia_cung_nguon`, `test_TC_CLS_45_chon_gia_theo_nguon_roi_ngay`, `test_TC_CLS_45_nguon_truoc_ngay_hieu_luc_sau`, `test_FR_RES_004_thu_tu_nguon` |
| FR-RES-012 | `test_FR_RES_012_don_gia_tao_cap_nhat_nhap_lai`, `test_TC_RES_08_nhap_tep_hai_dong_thieu_don_vi_tinh` (phần mặt hàng, đơn giá) |
| FR-RES-013 | `test_FR_RES_013_nhom_tuong_duong` |
| FR-RES-014 | `test_TC_RES_07_thanh_toan_rieng_bang_0_co_ly_do`, `test_TC_RES_07_dong_vat_chat_khop_golden_engine` |
| FR-RES-016 | `test_TC_CLS_46_xac_minh_khi_chua_co_tep_bi_tu_choi`, `test_FR_RES_016_xac_minh_co_tep_ghi_nguoi_va_thoi_diem` |
| FR-RES-017 | `test_TC_CLS_46_chua_xac_minh_van_tinh_co_canh_bao`, `test_FR_RES_017_chua_xac_minh` |
| FR-RES-018 | `test_TC_CLS_47_quy_doi_don_vi_dinh_muc_hc_glu`, `test_TC_CLS_47_don_gia_dinh_muc_khop_golden_cls`, `test_FR_RES_018_hoa_chat_can_so_don_vi_dinh_muc_duong` |

# Test ref — FEAT-033 (ghi bởi kiểm định độc lập NORM-26)

| FR | Test thật |
| :-- | :-- |
| FR-CMP-001 | `test_TC_CLS_27_thieu_chung_tu_bi_tu_choi`, `test_validate_record_thieu_truong_nen_tep` |
| FR-CMP-005 | `test_TC_CLS_28_nhac_han_thong_bao_va_doi_so_ngay`, `test_due_for_reminder` |
| FR-CMP-006 (phần dữ liệu; cảnh báo ở FEAT-036) | `test_has_valid_record`, `test_missing_required`, `test_is_valid_on_bien` |
| FR-CMP-007 | `test_TC_CLS_28_bao_cao_liet_ke_ho_so_sap_het_han_theo_khoa`, `test_build_expiry_report_thu_tu_va_loc` |
| FR-ADM-006 | `test_TC_CLS_28_nhac_han_thong_bao_va_doi_so_ngay`, `test_reminder_days_mac_dinh_va_loi` |

## FEAT-016 (NORM-28)

| FR | Test thật |
| :-- | :-- |
| FR-ACCT-001 | `test_TC_ACCT_01_nap_tep_vang_ra_ban_nhap` |
| FR-ACCT-002 | `test_TC_ACCT_02_loi_dong`, `test_TC_ACCT_02_khong_chot_khi_con_dong_loi`, `test_TC_ACCT_02_loi_dong_khong_chot_duoc` |
| FR-ACCT-003 | `test_TC_ACCT_03_dong_chua_gan`, `test_TC_ACCT_03_dong_chua_gan_chan_chot` |
| FR-ACCT-004 | `test_TC_ACCT_04_doi_loai_khong_ly_do`, `test_TC_ACCT_04_update_line_can_ly_do_va_luu_nguoi_sua`, `test_TC_ACCT_04_sua_truc_tiep_khong_ly_do_bi_tu_choi` |
| FR-ACCT-005 | `test_TC_ACCT_05_ma_dich_vu_la_bao_loi_dong_dung_van_luu`, `test_TC_ACCT_05_mac_dinh_kich_ban_va_trung_bon_truong` |
| FR-ACCT-006 | `test_TC_ACCT_06_chot_ghi_tong_khop_golden_va_khoa`, `test_TC_ACCT_06_tong_tep_vang_khop_golden` |
| FR-ACCT-007 | `test_TC_ACCT_09_tieu_chi_nam_va_ty_le_cap1`, `test_TC_ACCT_09_ty_le_cap1_k01_khop_golden` |
| FR-ACCT-008 | `test_TC_ACCT_07_cap1_moi_tieu_chi`, `test_TC_ACCT_07_cap2_headcount_bi_tu_choi`, `test_TC_ACCT_07_cap2_labor_min_hop_le`, `test_TC_ACCT_07_thieu_tieu_chi_cap2_headcount_cap2_labor_min` |
| FR-ACCT-009 | `test_TC_ACCT_08_bang_mac_dinh_va_lan_nhap_moi_theo_gia_tri_da_doi` |
| FR-ACCT-010 | `test_TC_ACCT_09_nhap_tieu_chi` |
| FR-ACCT-011 | `test_FR_ACCT_011_lan_nhap_thu_hai_cung_nam_giu_lan_cu` |

# Test ref — FEAT-031 (ghi bởi kiểm định độc lập NORM-30)

| FR | Test thật |
| :-- | :-- |
| FR-SVC-008 | `test_TC_CLS_20_danh_dau_can_lam_sang_yeu_cau_nhom_va_don_vi`, `test_TC_CLS_20_khong_can_lam_sang_khong_bat_buoc`, `test_FR_SVC_008_bo_co_can_lam_sang_khi_con_he_thong_bi_tu_choi` |
| FR-SVC-009 | `test_TC_CLS_21_ma_ngoai_gan_hai_dich_vu_bi_tu_choi`, `test_TC_CLS_21_lap_trong_cung_dich_vu`, `test_TC_CLS_21_chi_muc_duy_nhat_o_co_so_du_lieu` |
| FR-SVC-010 | `test_FR_SVC_010_dich_vu_bo` |
| FR-SVC-011 | `test_FR_SVC_011_gui_ngoai_can_gia`, `test_FR_SVC_011_dich_vu_gui_ngoai_khong_tinh_tu_dinh_muc`, `test_FR_SVC_011_co_gui_ngoai_cu_khi_da_bo_can_lam_sang_van_tinh` |
| FR-CLS-001 | `test_TC_CLS_20_hai_he_thong_cung_ton_tai`, `test_TC_CLS_20_thieu_truong_bat_buoc_bi_tu_choi`, `test_TC_CLS_20_dich_vu_phai_can_lam_sang` |
| FR-CLS-002 | `test_TC_CLS_20_hai_he_thong_cung_ton_tai`, `test_get_service_systems` |
| FR-CLS-005 | `test_FR_CLS_005_phut_chiem_may` |
| FR-CLS-006 | `test_TC_CLS_23_ngung_dung_khong_vao_lan_tinh_moi_lan_da_khoa_giu_nguyen`, `test_TC_CLS_23_norm_sets_to_cost` (unit) |
| FR-CLS-007 | `test_TC_CLS_20_khoi_tinh_trang_du_bon_muc`, `test_TC_CLS_20_canh_bao_tong_ty_trong_va_ngung_dung` |
| FR-CLS-008 | `test_TC_CLS_23_dong_thiet_bi_la_bao_loi_dong_dung_duoc_luu`, `test_cap_nhat_theo_ma_va_loi_nghiep_vu_thanh_loi_dong` |
| FR-ACC-008 | `test_TC_CLS_22_clinician_khoa_khac_khong_sua_duoc` (nc_test_system), `test_TC_CLS_22_clinician_khoa_khac_bi_tu_choi` (api/test_test_system.py), `test_khoa_khong_duoc_gan_thanh_loi_dong` |
