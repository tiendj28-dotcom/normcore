# Test ref — FEAT-030 (NORM-84)

| FR | Test thật |
| :-- | :-- |
| FR-PRICE-001 | `test_FR_PRICE_001_build_items`, `test_FR_PRICE_001_build_items_dang_duoi_gia_thanh` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_01_lap_tu_lan_tinh_khoa`, `test_TC_PRICE_01_lan_tinh_chua_khoa_bi_tu_choi`, `test_tao_phuong_an_can_quyen` (api/test_price_proposal.py); `test_lan_tinh_chua_khoa_bi_tu_choi` (nc_price_proposal/test_nc_price_proposal.py) |
| FR-PRICE-002 | `test_FR_PRICE_002_needs_basis`, `test_FR_PRICE_002_submit_errors_thieu_can_cu`, `test_FR_PRICE_002_submit_errors_khac` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_02_thieu_can_cu_tu_choi_gui`, `test_gui_duyet_loai_benh_vien_can_ngay_ap_dung` (api/test_price_proposal.py) |
| FR-PRICE-003 | `test_FR_PRICE_003_is_below_cost`, `test_FR_PRICE_003_approve_errors` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_03_duoi_gia_thanh_can_xac_nhan_dong` (api/test_price_proposal.py); `test_dong_duoi_gia_thanh_duoc_danh_dau` (nc_price_proposal) |
| FR-PRICE-004 | `test_FR_PRICE_004_departments`, `test_FR_PRICE_004_005_confirm` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_04_hai_khoa_xac_nhan_lan_luot` (api/test_price_proposal.py) |
| FR-PRICE-005 | `test_FR_PRICE_004_005_confirm` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_04_hai_khoa_xac_nhan_lan_luot`, `test_FR_NOTI_003_viec_cho` (api/test_price_proposal.py) |
| FR-PRICE-006 | `test_FR_PRICE_006_007_approved_state` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_05_duyet_ghi_lich_su_gia` (api/test_price_proposal.py) |
| FR-PRICE-007 | `test_FR_PRICE_006_007_approved_state` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_06_cap_tham_quyen_ghi_ket_qua` (api/test_price_proposal.py) |
| FR-PRICE-008 | `test_FR_PRICE_008_authority_errors` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_06_cap_tham_quyen_ghi_ket_qua` (api/test_price_proposal.py) |
| FR-PRICE-009 | `test_FR_PRICE_009_reset` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_07_tu_choi_ve_nhap_bao_tai_chinh` (api/test_price_proposal.py) |
| FR-PRICE-010 | `test_FR_PRICE_010_history_rows`, `test_FR_PRICE_010_history_conflicts` (tests/unit/test_price_proposal_logic.py); `test_TC_PRICE_05_duyet_ghi_lich_su_gia`, `test_FR_PRICE_010_lich_su_chi_them` (api/test_price_proposal.py) |
| FR-OUT-007 | `test_TC_OUT_05_cot_va_du_lieu_tu_lan_tinh`, `test_TC_OUT_05_nguon_phuong_an_co_cot_gia_de_xuat_va_thong_tin`, `test_dinh_dang_tien_ngay`, `test_khong_co_gia_tham_chieu_van_xuat_duoc` (tests/unit/test_exports_price_comparison.py); `test_TC_OUT_05_xuat_bang_so_sanh_gia` (api/test_price_proposal.py) |
| Quyền DocType | `test_quyen_clinician_khong_doc`, `test_quyen_auditor_chi_doc`, `test_quyen_truong_khoa_theo_khoa`, `test_quyen_consultant_chi_doc`, `test_quyen_finance_tao_xoa_nhap`, `test_sua_ngoai_api_bi_chan`, `test_auditor_khong_co_transition` (nc_price_proposal/test_nc_price_proposal.py); `test_quyen_hanh_dong` (api/test_price_proposal.py) |
| Workflow | `test_workflow_khop_transitions` (nc_price_proposal/test_nc_price_proposal.py) |
| Phạm vi khoa theo bảng con | tests/unit/test_scope_child.py, tests/unit/test_scope_registry.py |
| Giao diện | tests/unit/test_feat_030_ui.py |
