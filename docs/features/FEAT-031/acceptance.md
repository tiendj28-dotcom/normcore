# Nghiệm thu FEAT-031 — Dịch vụ cận lâm sàng và hệ thống xét nghiệm

Người kiểm: QA (Multica, Tester iu), độc lập với người viết. Issue NORM-30. Mã đã merge (PR #33), kiểm trên HEAD develop `73029ce31ecd49ff5075d384d460f96a150d1fe2`. Verdict: **accepted**.

## 1. Chạy lại từ đầu

| Lệnh | Kết quả |
| :-- | :-- |
| `with_bench.sh`: new-site `normcore-verify.test` + install-app + `run-tests --app normcore` + drop-site (một lần gọi) | Ran 486 tests, OK |
| `golden_engine.py`, `golden_cls.py` | thoát 0 |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 216 passed, 59 subtests; phủ 99% (`costing/test_systems.py` 100%) |
| `check_conventions.py` | thoát 0 |
| `build_rtm.py docs` | VAN DE: 0 |
| CI PR #33 và CI develop `73029ce31ecd49ff5075d384d460f96a150d1fe2` | xanh; "Deploy staging" run 45180887291 thành công |

## 2. Tiêu chí (technical-design mục 6) và TC

| # | Tiêu chí / TC | Bằng chứng | Đạt |
| :-: | :-- | :-- | :-: |
| 1 | TC-CLS-20 / FR-SVC-008: thiếu nhóm hoặc đơn vị kết quả bị từ chối | `test_TC_CLS_20_danh_dau_can_lam_sang_yeu_cau_nhom_va_don_vi` | Đạt |
| 2 | TC-CLS-20 / FR-CLS-001, 002: GLU-A và GLU-B cùng tồn tại; thiếu trường bắt buộc bị từ chối; 2% và 3% được lưu | `test_TC_CLS_20_hai_he_thong_cung_ton_tai`, `..._thieu_truong_bat_buoc_bi_tu_choi`; staging: THU-GLU-A (75%, 2, 3) và THU-GLU-B (25%) | Đạt |
| 3 | TC-CLS-20 / FR-CLS-007: form hiện khối tình trạng bốn mục; cảnh báo tổng tỷ trọng, ngừng dùng | `api/test_test_system.py::test_TC_CLS_20_*`; Playwright (mục 4) | Đạt |
| 4 | TC-CLS-21 / FR-SVC-009: mã LIS trùng với dịch vụ khác bị từ chối | `test_TC_CLS_21_ma_ngoai_gan_hai_dich_vu_bi_tu_choi`, `..._chi_muc_duy_nhat_o_co_so_du_lieu`; staging: gắn LIS THU-L100 cho THU-URE khi THU-GLU đã có thì bị từ chối, thông báo nêu THU-GLU | Đạt |
| 5 | TC-CLS-22 / FR-ACC-008: Clinician khoa khác không sửa được | `test_TC_CLS_22_clinician_khoa_khac_khong_sua_duoc`, `api/test_test_system.py::test_TC_CLS_22_*`; Playwright: thu-clin2 (khoa THU-VS) mở THU-GLU-A thấy "Không được phép" | Đạt |
| 6 | TC-CLS-23 / FR-CLS-006: GLU-B ngừng dùng không vào lần tính mới; lần "Đã khóa" giữ nguyên. Mục Reviewer bắt sửa (`0bd6688`) | `test_TC_CLS_23_ngung_dung_khong_vao_lan_tinh_moi_lan_da_khoa_giu_nguyen`: lần cũ chạy `run_costing()` thật rồi đặt "Đã khóa"; lần mới chạy `run_costing()` thật, `test_systems_in_scope()` = ["GLU-A"], 1 NC Service Cost; so snapshot (`modified`, số dòng, số tiền) của lần cũ không đổi | Đạt |
| 7 | TC-CLS-23 / FR-CLS-008: tệp 3 dòng, 1 dòng mã thiết bị lạ | `api/test_importer_test_system.py::test_TC_CLS_23_dong_thiet_bi_la_bao_loi_dong_dung_duoc_luu`: created=2, error_count=1, lỗi nêu "EQ_X" và "Mã thiết bị chính"; nhập lại không tạo trùng | Đạt |
| 8 | FR-SVC-011: bộ lọc gửi ngoài có `is_paraclinical: 1` (Reviewer bắt sửa) | `nc_costing_run.py:47`; `test_FR_SVC_011_dich_vu_gui_ngoai_khong_tinh_tu_dinh_muc`, `..._co_gui_ngoai_cu_khi_da_bo_can_lam_sang_van_tinh` | Đạt |
| 9 | FR-CLS-005, FR-SVC-010, FR-SVC-011 (giá), ràng buộc xóa thiết bị | `test_FR_CLS_005_phut_chiem_may`, `test_FR_SVC_010_dich_vu_bo`, `test_FR_SVC_011_gui_ngoai_can_gia`, `test_FR_ADM_005_xoa_thiet_bi_dang_duoc_he_thong_tham_chieu`, `test_FR_SVC_008_bo_co_can_lam_sang_khi_con_he_thong_bi_tu_choi` | Đạt |
| 10 | Quyền NC Test System theo data-model mục 4; vai trò không quyền; NC Auditor chỉ đọc | `test_quyen_theo_ma_tran_va_auditor`, `test_vai_tro_khong_co_quyen_bi_tu_choi`, `api/test_test_system.py::test_auditor_doc_duoc`, `test_vai_tro_khong_quyen_bi_tu_choi`, `test_importer_test_system::test_quyen_nhap_vai_tro_chi_doc_va_auditor_bi_tu_choi`; `check_conventions.py` thoát 0 | Đạt |
| 11 | `test_permissions.py` 27 → 30 theo ASM-113 | Diff PR #33: chỉ `test_co_27_…` đổi thành `test_co_30_…` (số đếm 27 → 30 và docstring); assertion khác giữ nguyên | Đạt |
| 12 | Hàm thuần `costing/test_systems.py`, `procedure/service_rules.py` | `tests/unit/test_test_systems.py`, `test_service_rules.py`; phủ 100% | Đạt |

## 3. Soát diff PR #33

- Không test nào bị xóa, skip, nới hay đổi giá trị mong đợi; chỉ `test_permissions.py` đổi số đếm có Quyết định Lead (ASM-113).
- Không sửa `docs/golden/`, `srs.md`, `test-cases.md`, `use-cases.md`, `implementation-plan.md`, `CLAUDE.md`, `.claude/`, `.autopilot/`, `.github/`.
- Phạm vi: các tệp đều thuộc FEAT-031 (DocType, API, bộ nhập, giao diện, `vi.csv`, Workspace, `check_conventions.py` thêm dòng ma trận cho NC Test System).

## 4. Giao diện (Playwright, staging http://112.213.88.40:8100, deploy từ `73029ce31ecd49ff5075d384d460f96a150d1fe2`)

Tài khoản thử: `thu-clin@example.com` (NC Clinician, khoa THU-HS), `thu-clin2@example.com` (NC Clinician, khoa THU-VS), ngôn ngữ vi, cửa sổ 1366 × 900. Dữ liệu thử tiền tố THU- (khoa THU-HS, THU-VS; thiết bị THU-EQ-A, THU-EQ-B; dịch vụ THU-GLU, THU-URE; hệ thống THU-GLU-A 75%, THU-GLU-B 25%).

| Màn hình | Quan sát | Ảnh | Đạt |
| :-- | :-- | :-- | :-: |
| SCR-DSK-006 (THU-GLU) | Khối "Cận lâm sàng": nhóm "Hóa sinh", đơn vị "Kết quả xét nghiệm", bảng mã ngoài (LIS / THU-L100), Gửi ngoài, Là dịch vụ bộ; mục "Hệ thống xét nghiệm": "Khoa THU Hóa sinh — tổng tỷ trọng 100%", THU-GLU-A (THU Máy A, 75, Đang dùng), THU-GLU-B (THU Máy B, 25, Đang dùng), nút "Thêm hệ thống xét nghiệm" | scr-dsk-006.png | Đạt |
| SCR-DSK-032 danh sách | 2 hệ thống THU-GLU-A, THU-GLU-B | scr-dsk-032-list.png | Đạt |
| SCR-DSK-032 form THU-GLU-A | Khối "Tình trạng": Bộ định mức, Kế hoạch chất lượng, Sản lượng kịch bản mặc định, Hệ số k và giá thành, đều "Chưa có" (ASM-115); nút "Ngừng dùng" | scr-dsk-032-form.png | Đạt |
| SCR-DSK-032 tổng tỷ trọng | Sau khi ngừng THU-GLU-B: "Tổng tỷ trọng của dịch vụ THU-GLU tại khoa THU-HS là 75.0%, khác 100%" | scr-dsk-032-canh-bao-ty-trong.png | Đạt |
| SCR-DSK-032 ngừng dùng | THU-GLU-B: chỉ báo "Ngừng dùng", thông báo "Hệ thống đã ngừng dùng: không vào các lần tính giá mới", nút "Dùng lại" | scr-dsk-032-ngung-dung.png | Đạt |
| TC-CLS-22 (UI) | Clinician khoa THU-VS mở THU-GLU-A: "Không được phép" | tc-cls-22-khoa-khac.png | Đạt |

Ghi chú: lần mở đầu, Clinician chưa được gán khoa THU-HS thấy "Chưa có hệ thống xét nghiệm" ở SCR-DSK-006 (đúng phạm vi khoa theo FR-ACC-008); sau khi gán khoa thì danh sách hiện đủ.

## 5. Giới hạn

- Cảnh báo "thiếu kế hoạch nội kiểm" của SCR-DSK-032 chưa kiểm được: kế hoạch chất lượng thuộc FEAT-032 (khối tình trạng luôn "Chưa có" đến lúc đó, ASM-115).
- Nút "Nhập từ Excel" chỉ mở trang nhập (FEAT-004 chưa đọc `import_set`); bộ nhập kiểm bằng API và test.
- Chưa mở bằng trình duyệt luồng nhập tệp Excel và luồng ngừng dùng bấm nút (ngừng dùng thử qua API trên staging).
- Dữ liệu thử THU-* còn trên staging.
