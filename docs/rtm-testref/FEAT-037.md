# Test ref — FEAT-037 (NORM-46)

| FR | Test thật |
| :-- | :-- |
| FR-COST-026 | `test_TC_CLS_16_V6_xuat_94_hop` (tests/golden/test_reconcile_cls_golden.py); `test_TC_CLS_16_khong_vuot_xuat_94_hop` (nc_costing_run/test_nc_costing_physical.py); `TestQuantities`, `TestRows` (tests/unit/test_reconcile_physical.py); `test_khong_doi_soat_vat_chat_khi_ke_hoach` (nc_costing_run/test_nc_costing_physical.py); `test_cot_va_dong_vat_chat` (nc_physical_reconciliation/test_nc_physical_reconciliation.py) |
| FR-COST-027 | `test_TC_CLS_17_V6_xuat_100_hop_golden` (tests/golden/test_reconcile_cls_golden.py); `test_TC_CLS_17_V6_xuat_100_hop` (tests/unit/test_reconcile_physical.py); `test_TC_CLS_17_vuot_nguong_chan_khoa` (nc_costing_run/test_nc_costing_physical.py); `test_giai_trinh_va_khoa` (api/test_costing_physical.py) |
| FR-COST-028 | `test_TC_CLS_18_V7_san_luong` (tests/golden/test_reconcile_cls_golden.py); `TestVolume` (tests/unit/test_reconcile_physical.py); `test_TC_CLS_18_canh_bao_san_luong_khong_chan_khoa` (nc_costing_run/test_nc_costing_physical.py); `test_bang_san_luong` (nc_physical_reconciliation/test_nc_physical_reconciliation.py) |
| FR-COST-029 | `test_TC_CLS_19_chua_doi_soat_vat_chat` (nc_costing_run/test_nc_costing_physical.py); `test_chua_doi_soat_dem_khoa` (api/test_costing_physical.py); `test_khoa_chua_doi_soat` (tests/unit/test_reconcile_physical.py) |
| FR-COST-030 | `test_TC_CLS_40_do_nhay_khong_ghi`, `test_gia_dinh_khong_hop_le`, `test_quyen_truong_khoa_ngoai_khoa`, `test_quyen_auditor_doc_duoc_clinician_khong` (api/test_costing_sensitivity.py); `test_Qbn_GLU_A_6000_khac_goc_va_dau_vao_khong_doi`, `test_san_luong_0_bao_loi` (tests/unit/test_sensitivity.py); tests/unit/test_sensitivity_ui.py |
| FR-OUT-012 | `test_TC_CLS_39_ba_dich_vu_thieu`, `test_khong_thieu_gi`, `test_truong_khoa_bi_ep_khoa`, `test_clinician_khong_mo_duoc` (nc_missing_data/test_nc_missing_data.py); tests/unit/test_missing_data.py |
