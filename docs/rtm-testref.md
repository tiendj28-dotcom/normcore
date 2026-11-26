# Test ref — FEAT-001, FEAT-004 và FEAT-005 (ghi bởi kiểm định độc lập NORM-14, NORM-17)

| FR | Test thật |
| :-- | :-- |
| FR-ACC-001 | `test_TC_ACC_05_guest_bi_tu_choi`, `test_TC_ACC_05_desk_chuyen_ve_trang_dang_nhap` |
| FR-ACC-002 | `test_quyen_theo_vai_tro`, `test_auditor_chi_doc_duoc`, `test_TC_ACC_04_*` (unit/test_permission_matrix.py), `test_TC_CLS_44_nc06_*` (unit/test_permission_matrix.py) |
| FR-ACC-007 | `test_TC_CLS_44_quet_quyen_sach`, `test_TC_CLS_44_quet_bat_custom_docperm`, `test_TC_CLS_44_quet_bat_workflow`, `test_TC_CLS_44_doc_so_lieu_nhat_ky`, `test_TC_CLS_44_sua_bo_dinh_muc_bi_tu_choi`, `test_TC_CLS_44_ghi_xoa_duyet_bi_tu_choi`, `test_TC_CLS_44_vai_tro_khac_khong_bi_hep` (tests/test_feat_039.py); unit/test_readonly.py |
| FR-ACC-003 | `test_TC_ACC_01_phamvi_khoa_ghi_doc`, `test_TC_ACC_01_doc_theo_q3`, `test_TC_ACC_01_chua_gan_khoa_khong_ghi_duoc`, `test_TC_ACC_01_vai_tro_khac_khong_bi_hep` |
| FR-ACC-004 | `test_TC_ACC_02_clinician_khong_xem_so_lieu_tai_chinh`, `test_TC_CLS_44_doc_so_lieu_nhat_ky` |
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
| FR-AUD-003 | `test_TC_AUD_03_loc_theo_quy_trinh`, `test_FR_AUD_003_loc_nguoi_thoi_gian_va_quyen`, `test_FR_AUD_003_to_time_chi_co_ngay_lay_tron_ngay`, `test_TC_AUD_03_auditor_loc_theo_quy_trinh` |
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

# Test ref — FEAT-006 (ghi bởi kiểm định độc lập NORM-16)

| FR | Test thật |
| :-- | :-- |
| FR-PROC-001 | `test_TC_PROC_01_tao_ban_nhap`, `test_luu_phan` (api/test_procedure.py) |
| FR-PROC-002 | `test_TC_PROC_02_tao_lan_hai_bi_tu_choi_va_dan_toi_ban_co`, `test_DI_02_chi_mot_ban_dang_soan_cho_moi_dich_vu_khoa`, `test_Q3_tu_choi_tao_va_sao_chep_khi_da_ban_hanh` |
| FR-PROC-003 | `test_TC_PROC_03_tich_hop_sap_lai_xoa_them`, `test_TC_PROC_03_ma_buoc_bat_bien`, `test_TC_PROC_03_ma_buoc_bat_bien_khi_sap_lai_va_xoa` (unit/test_procedure_logic.py), `test_yeu_cau_giai_doan_ten_mo_ta` |
| FR-PROC-004 | `test_TC_PROC_04_nguon_luc_nhan_luc`, `test_TC_PROC_04_nguon_luc_nhan_luc_co_ma_dong_bat_bien`, `test_nhan_luc_phai_tinh_bang_phut` |
| FR-PROC-005 | `test_FR_PROC_005_goi_y_va_de_trong_lien_ket` |
| FR-PROC-006 | `test_TC_PROC_03_tich_hop_sap_lai_xoa_them`, `test_reorder_chi_nhan_hoan_vi_day_du`, `test_move_len_xuong_va_chan_bien`, `test_K3_*` (unit/test_procedure_editor_behavior.py) |
| FR-PROC-007 | `test_TC_PROC_09_trich_dan` (văn bản, mục, đoạn trích, quan hệ), `test_FR_PROC_007_trich_dan_dung_mot_dich`, `test_FR_PROC_007_quan_he_mac_dinh_chua_co_can_cu` |
| FR-PROC-009 | `test_TC_PROC_08_lich_su_truoc_sau_nguoi_thoi_diem`, `test_TC_PROC_08_moc_thoi_gian_va_nguoi_cho_ca_hai_thay_doi` |
| FR-PROC-013 | `test_FR_PROC_013_sao_chep`, `test_FR_PROC_013_sao_chep_cap_ma_moi_va_anh_xa`, `test_E12_sao_chep_thanh_cong_khong_hien_dai_loi` |

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

# Test ref — FEAT-007 (Dev NORM-34 ghi; QA độc lập NORM-44 kiểm định, accepted)

| FR | Test thật |
| :-- | :-- |
| FR-PROC-008 | `test_TC_PROC_05_khac_biet_thieu_ly_do` (api/test_procedure_workflow.py), `test_TC_PROC_05_*` (unit/test_procedure_validation.py) |
| FR-PROC-010 | `test_TC_PROC_07_ban_nhap_co_du_thao`, `test_TC_PROC_07_ban_ban_hanh_day_du`, `test_TC_PROC_07_pdf_bat_dau_bang_pdf`, `test_TC_PROC_07_quyen_tai` (api/test_procedure_print.py), `test_TC_PROC_07_*` (unit/test_procedure_printing.py) |
| FR-PROC-011 | `test_TC_PROC_07_docx_va_ghi_xuat_tep`, `test_docx_cung_noi_dung_voi_ngu_canh` (unit) |
| FR-PROC-012 | `test_TC_PROC_06_liet_ke_du_ba_loi` (tích hợp), `test_TC_PROC_06_liet_ke_du_ba_loi` (unit/test_procedure_validation.py) |
| FR-WF-001 | `test_TC_WF_01_luong_bon_trang_thai_va_thong_bao`, `test_workflow_fixture_khop_transitions` |
| FR-WF-002 | `test_TC_WF_01_luong_bon_trang_thai_va_thong_bao`, `test_TC_WF_01_ca_am` |
| FR-WF-003 | `test_TC_WF_08_y_kien_theo_buoc_hien_cho_nguoi_soan_sau_khi_bi_tra_lai`, `test_quyen_review_comment_cac_vai_tro` (nc_review_comment) |
| FR-WF-004 | `test_TC_WF_01_luong_bon_trang_thai_va_thong_bao`, `test_TC_WF_01_ca_am`, `test_chua_cau_hinh_thu_ky` |
| FR-WF-005 | `test_TC_WF_01_luong_bon_trang_thai_va_thong_bao`, `test_TC_WF_01_ca_am` |
| FR-WF-006 | `test_TC_WF_04_phien_ban_cu_thay_the_dung_ngay_hieu_luc`, `test_TC_WF_04_ngay_hieu_luc_hom_nay_thay_ngay_khi_ban_hanh` (api/test_procedure_workflow_jobs.py), `test_TC_WF_04_*` (unit/test_procedure_approval.py) |
| FR-WF-007 | `test_TC_WF_02_tu_choi_o_ca_ba_cap` |
| FR-WF-008 | `test_TC_WF_03_sua_mo_ta_buoc_qua_form_va_api_bi_tu_choi` (nc_clinical_procedure), `test_khong_doi_trang_thai_bang_luu_thuong`, `test_khong_xoa_khi_dang_cho_duyet` |
| FR-WF-013 | `test_FR_WF_013_nhac_khi_qua_han`, `test_FR_WF_013_theo_cau_hinh_so_ngay` |
# Test ref — FEAT-035 (Dev ghi, QA kiểm định độc lập; thêm test quyền theo khoa của QA: `test_quyen_truong_khoa_chi_doc_khoa_minh` ở nc_stock_issue_actual và nc_equipment_usage)

| FR | Test thật |
| :-- | :-- |
| FR-ACCT-012 | `test_mac_dinh_kich_ban_va_lay_dich_vu_khoa_tu_he_thong`, `test_DI_14_trung_nam_kich_ban_he_thong` (nc_test_system_volume); `test_trung_bon_truong` (nc_equipment_usage); `test_TC_CLS_34_ma_lis_doi_sang_ma_dich_vu_cot_trong_duoc_chap_nhan` (kịch bản Kế hoạch lưu riêng) |
| FR-ACCT-013 | `test_TC_CLS_34_ma_lis_doi_sang_ma_dich_vu_cot_trong_duoc_chap_nhan`, `test_nguon_ma_trong_dung_ma_noi_bo`, `test_cap_nhat_giu_o_trong`, `test_phut_khai_thac` (api/test_importer_cls_volume.py); `test_o_test_phu_de_trong_la_null`, `test_thiet_bi_phut_chiem_may_luu_duoc_va_mac_dinh_kich_ban`, `test_thiet_bi_so_ket_qua_bi_tu_choi`; `test_TC_CLS_34_ma_lis_doi_sang_ma_dich_vu` (unit, `test_resolve_service`) |
| FR-ACCT-014 | `test_TC_CLS_35_ma_he_thong_la_va_so_am_bao_loi_dong_dung_van_luu`, `test_TC_CLS_35_ma_dich_vu_ma_khoa_khong_khop_va_so_phu_sai`, `test_so_am_va_thieu_qbn`, unit `test_TC_CLS_35_so_am` |
| FR-ACCT-015 | `test_TC_CLS_36_xuat_kho_theo_mat_hang_khoa_nam` (api/test_importer_cls_volume.py), `test_luu_va_trung_nam_khoa_mat_hang`, `test_luong_am` (nc_stock_issue_actual), unit `test_TC_CLS_36_stock_hop_le` |
| FR-ACC-002, FR-ACC-003, FR-ACC-007 | `test_quyen_theo_ma_tran`, `test_auditor_khong_ghi_duoc`, `test_clinician_khong_doc`, `test_department_head_chi_doc_khoa_minh` (nc_test_system_volume); `test_quyen_auditor_clinician_head` (nc_equipment_usage); `test_quyen` (nc_stock_issue_actual); `test_quyen_auditor_director_va_tep_mau`; `normcore.tests.test_permissions` |
| FR-CLS-007 (mục sản lượng) | `test_FR_CLS_007_muc_san_luong_uoc_tinh_khi_test_phu_trong` (api/test_test_system.py), `TestVolumeStatus` (unit) |

## FEAT-020 (ghi bởi QA, NORM-53)

| FR | Test thật |
| :-- | :-- |
| FR-LIB-001 | `test_TC_LIB_01_nap_pdf_tach_3_muc` (api/test_library.py), `test_FR_LIB_001_tao_ban_ghi_chua_lap_va_tinh_hieu_luc`, `test_FR_LIB_001_tep_qua_100mb_bi_tu_choi`, `test_FR_LIB_001_thieu_truong_bat_buoc_bi_tu_choi` (nc_legal_document) |
| FR-LIB-002 | `test_TC_LIB_02_trung_so_hieu` (nc_legal_document), `test_FR_LIB_002_so_hieu_khong_phan_biet_hoa_thuong_va_khoang_trang` |
| FR-LIB-003 | `test_TC_LIB_01_nap_pdf_tach_3_muc`, `test_FR_LIB_003_qtkt_moi_quy_trinh_la_mot_muc_cap_1`, `test_FR_LIB_003_pdf_dung_so_trang_va_chu_tieng_viet`, `test_FR_LIB_003_lap_lai_giu_ten_muc_va_go_muc_cu` |
| FR-LIB-004 | `test_FR_LIB_004_ocr_gia_tra_van_ban_thi_tach_muc_binh_thuong`, `test_FR_LIB_004_pdf_khong_lop_van_ban_khong_ocr_bao_loi`, `test_FR_LIB_004_needs_ocr` |
| FR-LIB-005 | `test_TC_LIB_03_tep_hong_bao_loi` (api/test_library.py), `test_FR_LIB_005_pdf_hong_bao_loi`, `test_FR_LIB_005_docx_hong_bao_loi` |
| FR-LIB-006 | `test_TC_LIB_04_hieu_luc_theo_ngay` (api/test_library_validity.py), `test_FR_LIB_006_tac_vu_ngay_chay_duoc`, `test_FR_LIB_006_tac_vu_ngay_dang_ky_trong_hooks` |
| FR-LIB-010 | `test_TC_LIB_08_tim_theo_cum_tu_va_ma_dich_vu` (api/test_library_search.py), `test_FR_LIB_010_tim_theo_so_hieu`, `test_FR_LIB_010_cum_tu_phai_khop_lien_tiep`, `test_FR_LIB_010_co_chi_muc_fulltext` |
| FR-LIB-011 | `test_FR_LIB_011_get_source_view_tra_tep_va_trang`, `test_FR_LIB_011_get_source_view_can_quyen_doc`, `test_FR_LIB_011_get_source_view_docx_khong_co_trang` |
| FR-LIB-012 | `test_FR_LIB_012_sua_van_ban_thuan_luu_ban_truoc` |

# Test ref — FEAT-032 (Dev NORM-35 ghi; QA độc lập NORM-45 kiểm định, accepted)

| FR | Test thật |
| :-- | :-- |
| FR-QC-001 | `test_TC_CLS_24_ke_hoach_du_truong_luu_duoc`, `test_TC_CLS_24_thieu_truong_bi_tu_choi_den_khi_du`, `test_TC_CLS_24_so_khong_bi_tu_choi` (nc_qc_plan), `test_TC_CLS_24_thieu_truong_dau`, `test_TC_CLS_24_thieu_truong_dong_noi_kiem` (unit/test_qc_plans.py) |
| FR-QC-002 | `test_TC_CLS_24_thieu_truong_bi_tu_choi_den_khi_du` (nc_qc_plan), `test_TC_CLS_24_thieu_truong_dong_chuan_may` (unit) |
| FR-QC-003 | `test_TC_CLS_24_chuong_trinh_du_truong_luu_duoc`, `test_TC_CLS_24_thieu_truong_bi_tu_choi` (nc_eqa_program), `test_TC_CLS_24_thieu_truong` (unit) |
| FR-QC-005 | `test_TC_CLS_25_50_va_40_bi_tu_choi`, `test_TC_CLS_25_60_va_40_luu_duoc`, `test_TC_CLS_25_de_trong_chia_deu` (nc_eqa_program), `test_TC_CLS_25_50_va_40_bi_tu_choi` (unit) |
| FR-QC-007 | `test_TC_CLS_26_he_thong_hoa_sinh_khong_ke_hoach_noi_kiem_canh_bao`, `test_TC_CLS_26_ke_hoach_khong_dong_noi_kiem_van_canh_bao`, `test_TC_CLS_26_co_noi_kiem_het_canh_bao`, `test_TC_CLS_26_nhom_khac_khong_canh_bao` (api/test_qc_plan.py), `test_TC_CLS_26_*` (unit) — một phần: gắn vào bộ định mức và "vẫn khóa được" ở FEAT-034 |
| FR-QC-008 | `test_TC_CLS_25_vat_lieu_noi_kiem_sai_loai`, `test_TC_CLS_25_chat_chuan_sai_loai` (nc_qc_plan), `test_TC_CLS_25_vat_lieu_sai_loai`, `test_TC_CLS_25_chat_chuan_sai_loai` (unit) |
# Test ref — FEAT-023 (Dev NORM-55 ghi; QA kiểm định độc lập, accepted)

| FR | Test thật |
| :-- | :-- |
| FR-AI-009 | `test_TC_AI_08_log_du_truong` (nc_ai_settings), `test_gateway_mock_tra_json_co_dinh_va_ghi_mot_log` (nc_ai_log) |
| FR-AI-010 | `test_TC_AI_05_qua_han_giu_du_lieu` (nc_ai_settings), `test_qua_han` (unit/test_ai_providers_openai.py) |
| FR-AI-011 | `test_TC_AI_06_*` (unit/test_ai_guard.py) |
| FR-AI-012 | `test_TC_AI_11_doi_dia_chi`, `test_UC017_4c_bat_ai_kiem_ket_noi` (nc_ai_settings), `test_gui_dung_giao_thuc` (unit/test_ai_providers_openai.py) |
| FR-AI-013 | `test_TC_AI_09_chan_han_muc`, `test_TC_AI_09_bien_bang_han_muc_khong_chan` (nc_ai_settings), `test_budget_exceeded_cac_bien` (unit/test_ai_guard.py) |
| FR-AI-014 | `test_FR_AI_014_*` (nc_prompt_template), `test_new_prompt_version` (api/test_ai.py), unit/test_ai_prompts.py |
| FR-AI-015 | `test_TC_AI_07_tat_ai_an_nut_van_chay_thu_cong` (api/test_ai.py; phần "giá tham chiếu" chưa kiểm được vì NC Benchmark Price chưa có trên develop, ASM-023-16), unit/test_ai_ui_conventions.py |
| NFR-SEC-004 | `test_TC_NFR_04_khoa_khong_lo` (nc_ai_settings), `test_loi_khong_lo_khoa` (unit/test_ai_providers_openai.py) |

## FEAT-002

# Test ref — FEAT-002 (Dev ghi; QA kiểm định độc lập: accepted)

| FR | Test thật |
| :-- | :-- |
| FR-NOTI-001 | `test_TC_NOTI_01_gui_duyet_thong_bao_va_trang_chu_truong_khoa` (api/test_home.py), `test_FR_NOTI_001_notify_bo_administrator_guest_va_user_tat`, `test_FR_NOTI_001_notify_gop_trung_va_goi_lai_khong_tao_them`, `test_FR_NOTI_001_notify_co_lien_ket_ban_ghi` (core/test_notify.py) |
| FR-NOTI-002 | `test_FR_NOTI_002_email_khi_co_may_chu`, `test_FR_NOTI_002_khong_may_chu_van_thong_bao` (core/test_notify.py) |
| FR-NOTI-003 | `test_TC_NOTI_01_gui_duyet_thong_bao_va_trang_chu_truong_khoa`, `test_TC_NOTI_01_viec_cho_dung_nguoi`, `test_TC_NOTI_01_auditor_khong_co_viec`, `test_quyen_get_home_guest` (api/test_home.py), `test_FR_NOTI_003_*` (core/test_notify.py) |
| FR-OUT-010 | `test_FR_OUT_010_*` (unit/test_chain_stages.py), `test_FR_OUT_010_dem_theo_tinh_trang_chuoi`, `test_FR_OUT_010_loc_khoa_va_pham_vi`, `test_FR_OUT_010_bo_loc_danh_sach_dich_vu`, `test_FR_OUT_010_so_truy_van_get_home` (api/test_home.py), `test_workspace_co_block_trang_chu` (tests/test_feat_002.py) |
| FR-ADM-003 | `test_TC_ADM_03_doi_so_ca_toi_thieu_ap_ngay` (**một phần** của TC-ADM-03, Lead chọn PA1, ASM-002-13; phần trung vị/cảnh báo thiếu ca là `test_TC_ADM_03_ket_qua_bam_gio_3_ca` của FEAT-014), `test_FR_ADM_003_so_ngay_nhac_ap_ngay`, `test_FR_ADM_003_thoi_han_ai_ap_ngay`, `test_nc_settings_*`, `test_quyen_nc_settings_*` (nc_settings/test_nc_settings.py) |
# Test ref — FEAT-022 (Dev NORM-54 ghi)

| FR | Test thật |
| :-- | :-- |
| FR-SVC-005 | `test_FR_SVC_005_de_xuat_sau_lap_chi_muc`, `test_FR_SVC_005_lap_lai_giu_da_xac_nhan`, `test_FR_SVC_005_loi_de_xuat_khong_lam_van_ban_loi`, `test_FR_SVC_005_de_xuat_lai_va_quyen`, `test_SCR_DSK_004_loc_chua_xac_nhan` (api/test_library_mapping.py), unit/test_library_mapping.py |
| FR-SVC-006 | `test_FR_SVC_006_xac_nhan_luu_nguoi_va_thoi_diem`, `test_FR_SVC_006_quyen_anh_xa` (api/test_library_mapping.py), `test_FR_SVC_006_validate_dong_dau` (nc_section_service_map) |
| FR-SVC-007 | `test_TC_SVC_02_chi_muc_da_xac_nhan_vao_nguon_ai`, `test_FR_SVC_007_nguon_chi_truong_cho_phep` (api/test_library_mapping.py) |
| TC-SVC-02 | `test_TC_SVC_02_chi_muc_da_xac_nhan_vao_nguon_ai` |
# Test ref — FEAT-008 (QA Multica kiểm định, accepted)

| FR | Test thật |
| :-- | :-- |
| FR-WF-009 | `test_TC_WF_05_sua_doi_giu_ma_buoc`, `test_sua_doi_da_co_ban_nhap_tra_ban_dang_co`, `test_sua_doi_tu_choi_trang_thai_va_quyen`, `test_sua_doi_tu_choi_ban_ban_hanh_cu_hon` (api/test_procedure_revision.py); unit/test_procedure_versioning.py |
| FR-WF-010 | `test_TC_WF_07_so_sanh_phien_ban`, `test_so_sanh_kiem_quyen_va_cung_quy_trinh` (api/test_procedure_compare.py); `test_TC_WF_07_diff_theo_phan_buoc_nguon_luc` (unit/test_procedure_diff.py); unit/test_feat_008_ui.py. Phần hiển thị loại M: QA kiểm bằng Playwright |
| FR-WF-011 | `test_TC_WF_06_ban_hanh_gan_co_bo_dinh_muc` (api/test_procedure_norm_flag.py); `test_TC_WF_06_step_changes_them_bo_doi` (unit/test_procedure_diff.py) |
| FR-WF-012 | `test_FR_WF_012_thu_hoi_co_ly_do`, `test_FR_WF_012_thu_hoi_tu_choi`, `test_FR_WF_012_sai_trang_thai` (api/test_procedure_withdraw.py); `TestWithdraw` (unit/test_procedure_approval.py) |
## FEAT-012 (NORM-39, ghi bởi Dev; QA kiểm định lại)

| FR | Test thật |
| :-- | :-- |
| FR-NORM-001 | `test_TC_NORM_01_khoi_tao_6_dong_mang_ma_buoc_va_dong_goc` (api/test_norm.py), `test_khoi_tao_tu_quy_trinh_da_ban_hanh` (nc_norm_set), `unit/test_norm_init.py` |
| FR-NORM-002 | `test_TC_NORM_02_quy_trinh_nhap_tu_choi_qua_api` (api/test_norm.py), `test_TC_NORM_02_quy_trinh_nhap_tu_choi_khoi_tao`, `test_TC_NORM_02_insert_truc_tiep_tu_quy_trinh_nhap_bi_tu_choi` |
| FR-NORM-003 | `test_TC_NORM_10_thieu_don_vi_thieu_so_phut_tu_choi` (api/test_norm.py, nc_norm_set), `unit/test_norm_validation.py` |
| FR-NORM-004 | `test_TC_NORM_04_vuot_tran_hao_hut_can_ly_do` (api/test_norm.py, nc_norm_set) |
| FR-NORM-005 | `test_TC_NORM_09_dong_them_phai_gan_buoc_hoac_chung` |
| FR-NORM-006, FR-NORM-007 | `test_TC_NORM_03_luong_ap_dung_L03_L09_L01` (golden/test_norm_golden.py) |
| FR-NORM-008 | `test_TC_NORM_11_can_cu_va_tham_chieu` |
| FR-NORM-009 | `test_TC_NORM_12_xac_nhan_mot_dong`, `test_dong_sua_sau_xac_nhan_mat_xac_nhan` |
| FR-NORM-010 | `test_TC_NORM_05_con_dong_chua_xac_nhan_chua_lien_ket_tu_choi`, `unit/test_norm_validation.py::TestConfirmBlockers` |
| FR-NORM-011 | `test_TC_NORM_06_khoa_tu_choi_sua_tao_phien_ban_moi`, `test_khoa_tu_nhap_bi_tu_choi_qua_api`, `test_khoa_tu_nhap_bi_tu_choi_va_bo_khoa_khong_sua_qua_client`, `test_tra_lai_can_ly_do` |
| FR-NORM-012 | `test_TC_NORM_06_khoa_tu_choi_sua_tao_phien_ban_moi`, `test_da_xac_nhan_chuyen_mon_khoa_noi_dung`, `test_new_version_nguon_khong_khoa_bi_tu_choi` |
| FR-NORM-013 | `test_TC_NORM_07_loai_tru_can_ly_do_trong_danh_sach` (api/test_norm.py, nc_norm_set) |
| FR-NORM-014 | `test_FR_NORM_014_canh_bao_trung`, `unit/test_norm_validation.py::TestDuplicates` |
| FR-NORM-016 | `test_FR_NORM_016_11_dong_khop_direct_lines`, `test_FR_NORM_016_tong_theo_buoc_cau_phan` (golden/test_norm_golden.py), `unit/test_norm_provisional.py`, `test_FR_NORM_016_get_norm_set_co_chi_phi_tam_tinh` |
| Quyền (FR-ACC-003, FR-ACC-007) | `test_quyen_norm_set_council_khong_co_quyen`, `test_quyen_norm_set_auditor_chi_doc`, `test_quyen_norm_set_finance_khong_sua_khong_xac_nhan`, `test_quyen_norm_set_clinician_khong_confirm_set_lock`, `test_quyen_norm_set_clinician_khoa_khac_khong_ghi` |
| Giao diện SCR-DSK-013, 014 | `unit/test_norm_grid_ui.py`, `unit/test_form_buttons_i18n.py` |

## FEAT-013 (NORM-51, ghi bởi Dev; QA kiểm định lại)

| FR | Test thật |
| :-- | :-- |
| FR-NORM-015 | `test_TC_NORM_08_phien_ban_theo_quy_trinh_moi`, `test_FR_NORM_015_dong_buoc_bo_chan_xac_nhan`, `test_FR_NORM_015_xu_ly_dong_buoc_bo`, `test_FR_NORM_015_xoa_dong_co_co`, `test_FR_NORM_015_co_buoc_bo_khong_ghi_tu_client`, `test_FR_NORM_015_tu_bo_nhap_va_khong_tao_trung`, `test_FR_NORM_015_khong_co_quy_trinh_moi_giu_hanh_vi_cu`, `test_FR_NORM_015_bo_da_thay_the_tu_choi`, `test_quyen_new_version_auditor_finance_khoa_khac` (api/test_norm_version.py); `test_TC_NORM_08_carry_lines_*`, `TestRemovedFlag` (unit/test_norm_carry.py); `TestStepRemoved` (unit/test_norm_validation.py); `TestNormGridFeat013` (unit/test_norm_grid_ui.py) |
## FEAT-015 (NORM-41, ghi bởi Dev; QA kiểm định lại)

| FR | Test thật |
| :-- | :-- |
| FR-COST-001 | `test_TC_COST_19_tao_lan_tinh_thieu_dau_vao_bi_tu_choi`, `test_khoa_dau_vao_khi_da_tinh` (nc_costing_run) |
| FR-COST-002 | `test_TC_COST_17_dich_vu_chua_khoa_bi_liet_ke_va_bo_qua` (nc_costing_run), `test_TC_COST_17_check_scope_liet_ke` (api/test_costing.py), `unit/test_costing_runner.py::test_TC_COST_17_eligibility` |
| FR-COST-003 | `test_TC_COST_01_thanh_tien_11_dong_DV_TEST_A` (golden/test_costing_golden.py), `test_TC_COST_01_tren_site_tong_truc_tiep_va_gia` (nc_costing_run), `unit/test_costing_engine.py`, `unit/test_costing_rates.py` |
| FR-COST-006 | `test_TC_COST_04_gia_thanh_tich_luy_lam_tron`, `test_TC_COST_12_V3_ON_PRICE` (golden/test_costing_golden.py), `test_TC_COST_13_lam_tron_302150_va_302149_99` (unit/test_costing_engine.py) |
| FR-COST-007 | `test_TC_COST_06_V1_khong_khau_hao` (golden), `test_TC_COST_06_bang_giai_trinh_ghi_khau_hao_bi_loai` (nc_costing_run), `test_TC_COST_06_ghi_chu_khau_hao_bi_loai` (api/test_costing.py), `test_TC_COST_06_loai_gia_khong_khau_hao_don_gia_gio_may` (nc_equipment) |
| FR-COST-010 | `test_TC_COST_15_dong_giai_trinh_du_nguon` (nc_costing_run), `test_TC_COST_15_get_explanation_du_truong` (api/test_costing.py) |
| FR-COST-015 | `test_FR_COST_015_tren_50_dich_vu_chay_nen_co_tien_do` (nc_costing_run) |
| FR-COST-016 | `test_TC_COST_07_V4_thieu_don_gia_THUOCX`, `test_TC_COST_07_chay_runner_dich_vu_khac_van_tinh` (golden), `test_TC_COST_07_V4_tren_site_dich_vu_khac_van_tinh` (nc_costing_run) |
| Quyền (FR-ACC-003, FR-ACC-007) | `test_quyen_costing_clinician_bi_tu_choi`, `test_quyen_costing_auditor_chi_doc`, `test_quyen_bang_giai_trinh_truong_khoa_theo_khoa` (api/test_costing.py) |
| Giao diện SCR-DSK-022, 023 | `unit/test_costing_ui.py`, `unit/test_form_buttons_i18n.py` |
