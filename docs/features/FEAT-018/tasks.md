# FEAT-018: Tasks

Quy ước:
- Mỗi task một commit `FEAT-018 Tnn: …`; viết test trước mã.
- Mọi lệnh `bench` chạy qua `scripts/with_bench.sh`, migrate và test trong cùng một lần gọi.
- **Không sửa tệp test cũ.** Test mới để trong tệp mới, theo technical-design mục 6, 7.
- **Điều kiện bắt đầu (ASM-018-01):** `git fetch && git merge origin/develop && git cat-file -e origin/develop:normcore/costing/snapshot.py` thành công. Chưa có `snapshot.py` (NORM-42 FEAT-036 chưa merge) thì Blocked "chờ NORM-42", mention Lead.

- [x] T01 Logic thuần `snapshot.py` (technical-design mục 3.1) và `reconcile.depreciation_centers` (3.2): `VERSION = 2`, khóa map tuple, `build(..., allocation, meta)`, `pack`, `unpack`, `recompute`, `reproduce` gọi `recompute`, `diff_rows`; viết `tests/unit/test_costing_snapshot_lock.py` (mọi nhánh ở tiêu chí #8 phần ảnh chụp) — done-when:
  - `pytest normcore/tests/unit/test_costing_snapshot_lock.py normcore/tests/unit/test_costing_snapshot.py normcore/tests/unit/test_reconcile.py` xanh (tệp FEAT-036, FEAT-017 không sửa);
  - `grep -rn "import frappe" normcore/costing/` không in gì.
- [x] T02 Logic thuần `costing/compare.py` (mục 3.3); viết `tests/unit/test_costing_compare.py` (tiêu chí #8 phần so sánh) — done-when: `pytest normcore/tests/unit/test_costing_compare.py` xanh.
- [x] T03 Golden: `tests/golden/test_snapshot_compare_golden.py` gồm `test_TC_COST_09_recompute_tu_anh_chup_vang` và `test_TC_COST_18_chenh_lech_V1_theo_cau_phan` (tiêu chí #7; số lấy từ `golden_engine.run()`, `run(False)`, không chép; −63.636,36 so thêm với TC-COST-18) — done-when:
  - `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_engine.py --no-depr` thoát 0;
  - `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` xanh.
- [x] T04 DocType và controller (mục 2.1, 4.1–4.3):
  - `nc_costing_run.json`: section "Ảnh chụp đầu vào", `snapshot_file`, `snapshot_hash`; `no_copy` cho `progress`, `allocation_warnings`;
  - `validate` (khóa cứng bản ghi "Đã khóa", trường ảnh chụp chỉ do Khóa ghi), `on_trash`;
  - `run_costing` câu từ chối riêng cho "Đã khóa"; `lock_costing` mở rộng; `verify_snapshot`, `duplicate_run`;
  - `loader.capture_snapshot` thêm `allocation`, `meta`; `loader.eligible_from_results`, `loader.stored_rows`;
  - `writer.service_cost_values`, `recon_values`, `expected_rows` (giá trị ghi không đổi); `execute_costing` dùng `reconcile.depreciation_centers`;
  - fixture `costing_fixtures.make_price_category_no_depr()` (chỉ thêm hàm);
  - test site mới `nc_costing/doctype/nc_costing_run/test_nc_costing_run_lock.py`;
  - chuỗi vào `normcore/translations/vi.d/FEAT-018.csv`

  done-when: `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run_lock && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run_allocation && bench --site normcore.test run-tests --module normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run'` in `OK`. Tệp mới phải có:
  - `test_TC_COST_09_tinh_lai_tu_anh_chup_trung_moi_truong`;
  - `test_TC_COST_11_da_khoa_tu_choi_tinh_nhan_ban_ra_nhap`;
  - `test_khoa_tu_choi_khi_dau_vao_doi_sau_lan_tinh`;
  - `test_kiem_tra_tai_lap_phat_hien_tep_bi_sua`;
  - `test_ban_ghi_da_khoa_khong_sua_khong_xoa`;
  - `test_TC_CLS_38_khoa_that_tai_lap_tu_anh_chup` (khi FEAT-036 đã trên develop, ASM-018-12).
- [x] T05 API (mục 5) và đo thời gian khóa: `verify_snapshot`, `duplicate_run`, `compare_runs`; mở rộng `lock_run`, `get_run_results`; test `normcore/api/test_costing_lock.py` gồm `test_TC_COST_18_so_sanh_goc_voi_V1`, `test_quyen_khoa_nhan_ban_so_sanh_theo_vai_tro` (tiêu chí #6, #9) — done-when:
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_costing_lock && bench --site normcore.test run-tests --module normcore.api.test_costing && bench --site normcore.test run-tests --module normcore.api.test_costing_reconciliation'` in `OK`;
  - implementation-log ghi thời gian khóa đo thật với 500 dịch vụ (dựng bằng dữ liệu của `tests/test_costing_perf.py`, đo một lần, không thêm TC; ASM-018-11).
- [x] T06 Giao diện SCR-DSK-022 bổ sung, theo `ui-design.md`: `nc_costing_run.js` (nút "Nhân bản", "Kiểm tra tái lập", "So sánh với lần tính khác", dải "Đã khóa" kèm mã băm, section ảnh chụp, câu báo khóa từ chối khi đầu vào đổi); `vi.d/FEAT-018.csv`; test tĩnh mới `tests/unit/test_costing_lock_ui.py` — done-when: `pytest normcore/tests/unit/test_form_buttons_i18n.py normcore/tests/unit/test_ui_conventions.py normcore/tests/unit/test_vi_csv_order.py normcore/tests/unit/test_costing_ui.py normcore/tests/unit/test_reconciliation_ui.py normcore/tests/unit/test_costing_lock_ui.py` xanh.
- [x] T07 Giao diện: Script Report `nc_costing/report/nc_costing_run_comparison/` ("So sánh hai lần tính giá": JSON, `.py`, `.js`), theo `ui-design.md` — done-when:
  - lệnh pytest của T06 xanh;
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore && bench --site normcore.test run-tests --module normcore.nc_costing.report.nc_costing_run_comparison.test_nc_costing_run_comparison'` in `OK` (tệp có `test_bao_cao_so_sanh_cot_cay_va_quyen`: cột, dòng dịch vụ `indent` 0, cấu phần `indent` 1, số DV-TEST-A −63.636,36, NC Clinician bị từ chối, NC Auditor đọc được).
- [x] T08 Hồ sơ: `docs/as-built/FEAT-018.md`; Test ref ở `docs/rtm-testref/FEAT-018.md`; cập nhật trạng thái ASM-018-*; `implementation-log.md` — done-when: `python3 docs/tools/build_rtm.py docs` in `VAN DE: 0`.
- [ ] T09 Kiểm toàn bộ — done-when: pytest, `bench run-tests --app normcore`, `check_conventions.py`, golden đều xanh. Cụ thể:
  - `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py`;
  - `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`;
  - `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`;
  - `python3 scripts/check_conventions.py`;
  - `git diff origin/develop --stat -- '*test*.py'` chỉ có tệp mới; `git diff origin/develop -- '*test*.py' | grep -E '^-'` chỉ in dòng tiêu đề `---`;
  - đã `git merge origin/develop` và chạy lại toàn bộ trước khi mở PR.
