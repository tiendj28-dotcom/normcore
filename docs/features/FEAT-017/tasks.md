# FEAT-017: Tasks

Quy ước:
- Mỗi task một commit `FEAT-017 Tnn: …`; viết test trước mã.
- Mọi lệnh `bench` chạy qua `scripts/with_bench.sh`, migrate và test trong cùng một lần gọi.
- **Không sửa tệp test cũ.** Test mới để trong tệp mới, theo technical-design mục 7.
- **T03 chờ Quyết định Lead Q1** (technical-design mục 10). T01 và T02 làm trước được.

- [ ] T01 Logic thuần: `costing/allocation.py` và `costing/reconcile.py` (technical-design mục 3.1, 3.2), không import `frappe`; viết `tests/unit/test_allocation.py`, `tests/unit/test_reconcile.py` (mọi nhánh ở tiêu chí #9) — done-when:
  - `pytest normcore/tests/unit/test_allocation.py normcore/tests/unit/test_reconcile.py` xanh;
  - `grep -rn "import frappe" normcore/costing/` không in gì.
- [ ] T02 Golden: viết `tests/golden/test_allocation_golden.py` gồm `test_TC_COST_02_cap1_K01_nhan_LABOR_MANAGEMENT`, `test_TC_COST_03_phan_con_lai_va_phan_bo_theo_ca`, `test_TC_COST_05_bon_dong_doi_soat`, `test_TC_COST_08_V5_san_luong_bang_0`, `test_TC_COST_16_phan_con_lai_am_lay_0`, `test_V1_khong_phan_bo_khong_doi_soat_khau_hao`. Đầu vào và số mong đợi lấy từ `golden_engine` (`run()`, `run(False)`, vá `VOLUME`/`ACCOUNTING` bằng `mock.patch.dict`), không chép số — done-when:
  - `pytest normcore/tests/golden` xanh;
  - `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_engine.py --no-depr` thoát 0;
  - `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` xanh.
- [ ] T03 (theo Quyết định Lead Q1) DocType:
  - DocType mới `nc_reconciliation_line` (mục 2.1): JSON, controller với `before_insert`, `validate`, `on_trash`;
  - thêm trường `allocation_warnings` vào `nc_costing_run.json` (AMD-017-01), áp AMD-017-01 vào `docs/data-model.md`;
  - nhãn và thông báo vào `vi.csv`;
  - thêm một dòng `DOCTYPE_ROW` vào `scripts/check_conventions.py` theo phương án Lead chọn

  done-when:
  - `python3 scripts/check_conventions.py` thoát 0;
  - `python3 docs/tools/build_rtm.py docs` in `VAN DE: 0`;
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.tests.test_permissions'` in `OK`.
- [ ] T04 Lớp CSDL và controller (mục 4):
  - `loader.allocation_context`;
  - `allocate_pools(results, actx=None)`, `_run` (ghi tiêu chí, `mark_volume`), `execute_costing` (xóa và ghi dòng đối soát, `allocation_warnings`, tiến độ 0–90–100), `lock_costing`;
  - `writer.write_reconciliation`;
  - fixture `costing_fixtures.make_golden_allocation`;
  - test site mới `nc_costing_run/test_nc_costing_run_allocation.py`

  done-when: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run_allocation && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run'` in `OK`. Tệp mới phải có:
  - `test_TC_COST_10_khoa_khi_DRUG_SUPPLY_chua_giai_trinh`;
  - `test_doi_soat_tren_site_khop_golden` (4 dòng, số khớp golden; DV-TEST-A giá thành 287.745,46);
  - `test_tinh_lai_xoa_dong_doi_soat_cu`;
  - `test_thieu_quy_tac_ghi_allocation_warnings`;
  - `test_quyen_doi_soat_khong_tao_tay_khong_sua_so` (qua `doc.insert`, `frappe.client.set_value`);
  - test cũ `test_nc_costing_run.py` vẫn xanh mà không sửa.
- [ ] T05 API (mục 5): viết `get_reconciliation`, `save_explanation`, `lock_run`; mở rộng `get_run_results` (`has_volume_warning`, `recon_blocked`) và `get_explanation`; viết test `normcore/api/test_costing_reconciliation.py` — done-when: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_costing_reconciliation && bench --site normcore.test run-tests --module normcore.api.test_costing'` in `OK`. Phải có:
  - `test_quyen_doi_soat_clinician_bi_tu_choi`;
  - `test_quyen_doi_soat_auditor_chi_doc` (đọc được; `save_explanation`, `lock_run` → PermissionError);
  - `test_get_reconciliation_can_lock_va_blocked`;
  - test cũ `api/test_costing.py` vẫn xanh mà không sửa.
- [ ] T06 Hiệu năng NFR-PERF-002: viết `normcore/tests/test_costing_perf.py::test_TC_COST_14_500_dich_vu_50000_dong_duoi_5_phut` (sinh dữ liệu bằng `frappe.db.bulk_insert`; kiểm `enqueue(queue="long")`, tiến độ tăng dần tới 100, dưới 300 giây). Tối ưu `writer` nếu cần (mục 4.3) — done-when:
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.tests.test_costing_perf'` in `OK`;
  - implementation-log ghi thời gian đo thật: pha tính, pha ghi, tổng.
- [ ] T07 Giao diện SCR-DSK-022 bổ sung, theo `ui-design.md`:
  - `nc_costing_run.js`: nút "Khóa", nút "Bảng đối soát", dải cảnh báo phân bổ, cột cảnh báo sản lượng, câu báo mất giải trình khi tính lại;
  - `vi.csv`

  done-when: `pytest normcore/tests/unit/test_form_buttons_i18n.py normcore/tests/unit/test_ui_conventions.py normcore/tests/unit/test_vi_csv_order.py normcore/tests/unit/test_costing_ui.py normcore/tests/unit/test_reconciliation_ui.py` xanh (`test_reconciliation_ui.py` là tệp test tĩnh mới).
- [ ] T08 Giao diện SCR-DSK-024: Script Report `nc_costing/report/nc_reconciliation/` (Bảng đối soát: JSON, `.py`, `.js` gồm hộp thoại giải trình và nút Khóa); form và list `nc_reconciliation_line.js`, `nc_reconciliation_line_list.js`; `vi.csv` — done-when:
  - lệnh pytest của T07 xanh;
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore && bench --site normcore.test run-tests --module normcore.nc_costing.report.nc_reconciliation.test_nc_reconciliation'` in `OK` (tệp có `test_bao_cao_doi_soat_cot_va_quyen`).
- [ ] T09 Hồ sơ: viết `docs/as-built/FEAT-017.md`; ghi Test ref (`docs/rtm-testref.md` mục `## FEAT-017`, hoặc `docs/rtm-testref/FEAT-017.md` nếu đã có trên develop); cập nhật trạng thái ASM-017-*; viết implementation-log — done-when: `python3 docs/tools/build_rtm.py docs` in `VAN DE: 0`.
- [ ] T10 Kiểm toàn bộ — done-when: pytest, `bench run-tests --app normcore`, `check_conventions.py`, golden đều xanh. Cụ thể:
  - `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py`;
  - `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`;
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`;
  - `python3 scripts/check_conventions.py`;
  - `git diff origin/develop --stat -- '*test*.py'` chỉ có tệp mới; `git diff origin/develop -- '*test*.py' | grep -E '^-'` chỉ in dòng tiêu đề `---`;
  - đã `git merge origin/develop` và chạy lại toàn bộ trước khi mở PR.
