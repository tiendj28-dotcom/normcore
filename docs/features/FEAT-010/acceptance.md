# Nghiệm thu FEAT-010 — Thiết bị, phòng (NORM-19)

Nhánh `feat/FEAT-010-thiet-bi-phong` (PR 25) tại `8c0ab4f93a914fde01cb4bdac7684236a1a4c957`. Người kiểm: QA (Multica).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-RES-03 EQ1: khấu hao năm 150.000.000; giờ máy 176.136,3636 | `test_TC_RES_03_eq1_khau_hao_va_don_gia_gio` (DocType), `test_TC_RES_03_eq1`, `test_TC_RES_03_api_eq1`, golden | Đạt |
| TC-RES-04 V2, ZERO → 0; 34.090,9091 (CONTINUE có test) | `test_TC_RES_04_v2_zero`, `_continue`, `..._theo_bo_tham_so`, api, golden | Đạt |
| TC-RES-10 phòng thiếu giờ khai thác bị từ chối; R1 đủ thì lưu | `test_TC_RES_10_thieu_gio_khai_thac_bi_tu_choi_roi_r1_luu_duoc`, `_phong_r1`, api, golden | Đạt |
| TC-CLS-48 Thuê thiếu hợp đồng / Mua thiếu nguyên giá / thiếu tiêu chí chia | 4 test `test_TC_CLS_48_*` | Đạt |
| TC-CLS-49 60%+30% từ chối; 60%+40% lưu | `test_TC_CLS_49_ty_le_theo_khoa`, `_ty_le_khoa` | Đạt |
| FR-RES-005..008, 019..026, 012 (thiết bị, phòng) | test `test_FR_RES_*` tương ứng + bộ nhập `api/test_importer_equipment.py` | Đạt |
| Quyền: vai trò không quyền, NC Auditor | `test_FR_ACC_002_*`, `test_FR_ACC_007_auditor_chi_doc_khong_sua`, `test_permissions` (25 DocType) | Đạt |

## Chạy lại
- `with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`: **Ran 315 tests OK**.
- pytest unit + golden: 133 passed; độ phủ costing 98%. golden_engine/golden_cls chạy sạch. `check_conventions.py` 0 lỗi; `build_rtm.py`: VAN DE 0.
- Diff test: không xóa, skip, nới. Chỉ đổi `test_permissions.py` (20→25 DocType) và `api/test_importer.py` (thêm khóa `nc_equipment`, `nc_room`) theo duyệt của người chủ squad (ASM-084). Tài liệu chỉ đọc không bị sửa.
- CI PR: "Tài liệu, golden, unit test" pass; "Test trên site Frappe v15" còn pending lúc kiểm (HEAD vừa push).

## Giới hạn
- Không tạo được site sạch `normcore-verify.test` (QA thiếu `DB_ROOT_PASSWORD`); chạy trên `normcore.test` sau migrate. CI cài mới trên site mới.
- Playwright MCP không kết nối: giao diện SCR-DSK-018 chưa kiểm bằng trình duyệt; có test quy ước giao diện (unit).
- PR 26 merge trước thì PR này phải gộp `develop` lại (theo Lead).
