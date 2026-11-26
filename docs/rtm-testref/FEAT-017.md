# Test ref — FEAT-017 (NORM-43)

| FR | Test thật |
| :-- | :-- |
| FR-COST-004 | `test_TC_COST_02_cap1_K01_nhan_LABOR_MANAGEMENT` (tests/golden/test_allocation_golden.py); `TestLevel1` (tests/unit/test_allocation.py) |
| FR-COST-005 | `test_TC_COST_03_phan_con_lai_va_phan_bo_theo_ca`, `test_TC_COST_16_phan_con_lai_am_lay_0`, `test_V1_khong_phan_bo_khong_doi_soat_khau_hao` (tests/golden/test_allocation_golden.py); `test_TC_COST_16_phan_con_lai_am_tren_site`, `test_thieu_quy_tac_ghi_allocation_warnings` (nc_costing_run/test_nc_costing_run_allocation.py); `TestLevel2` (tests/unit/test_allocation.py) |
| FR-COST-008 | `test_TC_COST_05_bon_dong_doi_soat` (tests/golden/test_allocation_golden.py); `test_doi_soat_tren_site_khop_golden`, `test_tinh_lai_xoa_dong_doi_soat_cu` (nc_costing_run/test_nc_costing_run_allocation.py); `test_bao_cao_doi_soat_cot_va_quyen` (nc_reconciliation/test_nc_reconciliation.py); tests/unit/test_reconcile.py |
| FR-COST-009 | `test_TC_COST_10_khoa_khi_DRUG_SUPPLY_chua_giai_trinh` (nc_costing_run/test_nc_costing_run_allocation.py); `test_get_reconciliation_can_lock_va_blocked`, `test_quyen_doi_soat_clinician_bi_tu_choi`, `test_quyen_doi_soat_auditor_chi_doc` (api/test_costing_reconciliation.py); `TestLockBlockers` (tests/unit/test_reconcile.py) |
| FR-COST-014 | `test_TC_COST_08_V5_san_luong_bang_0` (tests/golden/test_allocation_golden.py); `test_ghi_chu_khi_san_luong_bang_0` (api/test_costing_reconciliation.py) |
| NFR-PERF-002 | `test_TC_COST_14_500_dich_vu_50000_dong_duoi_5_phut` (tests/test_costing_perf.py) |
