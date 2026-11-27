# Nghiệm thu FEAT-028 (NORM-81) — Bàn so sánh giá

Commit đã kiểm: `167e872ffedd7bfd69c1f08f09a6cb249dc317d7` (nhánh `feat/FEAT-028-price-compare`, PR #86). Người kiểm: Tester iu (không phải người viết).

| Tiêu chí | Bằng chứng (lệnh tự chạy) | Kết quả |
| :-- | :-- | :-- |
| Golden | `golden_engine.py`, `golden_cls.py` chạy sạch | Đạt |
| pytest unit + golden | 1228 passed, 191 subtests; độ phủ tổng 99% | Đạt |
| Độ phủ `benchmark/rules.py` ≥ 90% | rules.py 100%, stats.py 98%, reference.py 100% | Đạt |
| Test trên site sạch `normcore-verify.test` | `bench run-tests --app normcore`: Ran 2088 tests, OK; site đã xóa | Đạt |
| `check_conventions.py`, `build_rtm.py docs` | exit 0; Must chưa có TC: 0 | Đạt |
| TC-ADJ-01 (FR-ADJ-001) | `test_TC_ADJ_01_chon_gia_trong_24_thang` + bản trên site: giữ P 01/06/2026, loại Q (ngoài 24 tháng) | Đạt |
| TC-ADJ-02 (FR-ADJ-002) | `test_TC_ADJ_02_trung_vi_va_do_lech`: 280.000/+7,90%; 4 giá 290.000/+4,18% | Đạt |
| TC-ADJ-03 (FR-ADJ-003) | `test_TC_ADJ_03_chua_du_du_lieu`, `..._khong_sinh_goi_y_...` | Đạt |
| TC-ADJ-04 (FR-ADJ-005) | `test_TC_ADJ_04_goi_y_dv_test_a`: BR-ADJ-001 EQ1 0,4→0,5, BR-ADJ-002 L04 20→15 phút, có tác động, xếp giảm dần | Đạt |
| TC-ADJ-08 (FR-ADJ-010) | `test_TC_ADJ_08_co_cau_gia`, `test_FR_ADJ_010_...`: tổng cấu phần = giá thành | Đạt |
| FR-ADJ-004, 008 | test lọc đơn vị; từ chối cần lý do, lưu người/thời điểm, chặn "cần sửa quy trình" | Đạt |
| Quyền | test clinician không đọc, Auditor chỉ đọc, Trưởng khoa theo khoa, theo ma trận | Đạt |
| Soát diff test | Chỉ thêm (0 dòng xóa trong diff so với develop); không skip/nới; sửa review 1 (BR-ADJ-002 giữ trần định mức) có test `test_rule_002_dong_co_tran_dinh_muc_khong_tang_gia` | Đạt |
| Tài liệu chỉ đọc | Không có tệp srs/test-cases/use-cases/golden/CLAUDE.md/.claude/.autopilot/.github bị sửa | Đạt |
| CI PR #86 | "Test trên site Frappe v15" pass, "Tài liệu, golden, unit test" pass | Đạt |
| Giao diện Playwright (SCR-DSK-026) | Không chạy: staging chưa có nhánh này (chưa merge). Thay bằng `test_feat_028_ui.py` (pass) và test API trên site cho các vai trò | Ghi chú, không chặn |

Verdict: **accepted**.
