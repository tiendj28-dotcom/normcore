# FEAT-026 — Biên bản nghiệm thu (QA Multica)

Commit đã kiểm: `8b26db29d52bbd047dba2788f0da28ed5b12ef39`. Người kiểm: Tester iu (không viết FEAT này).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Chạy lại trên site sạch `normcore-verify.test` (new-site, install-app, run-tests --app normcore, drop-site, một lần gọi qua with_bench.sh) | "Ran 2029 tests ... OK" | Đạt |
| pytest unit + golden + độ phủ | 1192 passed, 190 subtests; `normcore/benchmark/reference.py` 100%, tổng costing+benchmark 99% (≥ 90%) | Đạt |
| golden_engine.py, golden_cls.py, build_rtm.py docs | chạy xong, "VAN DE: 0" | Đạt |
| check_conventions.py | exit 0 | Đạt |
| TC-BM-01 (FR-BM-002, 004) | `test_TC_BM_01_nhap_tep_de_xuat_dich_vu`: 5 dòng tạo (thử không ghi, ghi mới ghi), 2 dòng tên gốc có dịch vụ đề xuất, trạng thái "Đề xuất", chưa xác nhận | Đạt |
| TC-BM-02 (FR-BM-007) | `test_TC_BM_02_tu_choi_dong_trung`: dòng trùng bị từ chối ở cả chế độ thử và ghi, kể cả trùng theo tên chuẩn hóa; số dòng không đổi | Đạt |
| TC-BM-03 (FR-BM-005) | `test_TC_BM_03_so_sanh_chi_dung_gia_da_xac_nhan`: 3 giá "Đã xác nhận" có mặt, giá "Đề xuất" bị loại | Đạt |
| TC-BM-04 (FR-BM-006) | `test_TC_BM_04_gia_hieu_chinh` (unit) và `..._tren_site`: 200.000 × 104 ÷ 100 = 208.000,00; thiếu chỉ số thì không hiệu chỉnh và nêu tháng thiếu | Đạt |
| TC-BM-06 (FR-BM-001) | `test_TC_BM_06_don_vi_tham_chieu_bat_buoc`: thiếu tỉnh/thành bị từ chối, đủ trường lưu được | Đạt |
| FR-BM-008 | `test_FR_BM_008_phieu_khao_sat`, quyền phiếu; mẫu thay được (TBD-01, ASM) | Đạt |
| Quyền (vai không quyền, Auditor) | test `test_quyen_feat_026_*` trên site; perm_matrix 3 DocType; check_conventions đạt | Đạt |
| Soát diff test | Chỉ 2 test cũ đổi: `test_importer.py` (thêm nc_benchmark_price vào danh sách bộ nhập), `test_scope_registry.py` (9 → 10 delete_guard); đều do thiết kế, có BA duyệt (ASM-026-14/15), không xóa/skip/nới | Đạt |
| Tài liệu chỉ đọc | Không đổi srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI PR #84 | "Test trên site Frappe v15" pass; "Tài liệu, golden, unit test" pass | Đạt |

## Giới hạn
- Giao diện chưa kiểm bằng trình duyệt (Playwright): không có tài khoản test theo vai trò. Kiểm quyền và luồng qua test trên site và API.
- Mẫu Phụ lục I là cấu trúc giả định (TBD-01).
