# Nghiệm thu FEAT-029 (NORM-83) — Kịch bản điều chỉnh

Commit đã kiểm: `31c09fd83661c9373f9c8e281e1565c1ba24538c` (nhánh `feat/FEAT-029-kich-ban-dieu-chinh`, PR #87). Người kiểm: Tester iu (không phải người viết).

| Tiêu chí | Bằng chứng (lệnh tự chạy) | Kết quả |
| :-- | :-- | :-- |
| Golden | `golden_engine.py`, `golden_cls.py` chạy sạch | Đạt |
| pytest unit + golden | 1259 passed, 193 subtests; độ phủ tổng 99% (benchmark, costing ≥ 90%) | Đạt |
| Test trên site sạch `normcore-verify.test` | `bench run-tests --app normcore`: Ran 2146 tests, OK (RC=0); site đã xóa | Đạt |
| `check_conventions.py`, `build_rtm.py docs` | exit 0; Must chưa có TC: 0; không có VAN DE | Đạt |
| TC-ADJ-05 (FR-ADJ-006) | `test_TC_ADJ_05_kich_ban_tinh_lai_goc_khong_doi` (site) + `test_TC_ADJ_05_apply_thiet_bi_ve_golden` (unit): kịch bản ghi thay đổi, tính lại DV-TEST-A, lần gốc không đổi | Đạt |
| TC-ADJ-06 (FR-ADJ-007) | `test_TC_ADJ_06_yeu_cau_sua_quy_trinh`: không sửa bộ định mức, tạo NC Procedure Change Request, thông báo trưởng khoa | Đạt |
| TC-ADJ-07 (FR-ADJ-009) | `test_TC_ADJ_07_bo_dinh_muc_nhap_so_phut_moi`: bản nháp số phút mới, chờ xác nhận | Đạt |
| Quyền | `test_quyen_chap_nhan_va_xem_kich_ban`: Consultant/Admin/Auditor/Trưởng khoa khác khoa bị chặn chấp nhận; Auditor chỉ đọc, không tạo kịch bản; Trưởng khoa theo khoa; DocType mới có test quyền (clinician không đọc, Auditor chỉ đọc) | Đạt |
| Soát diff test | 0 dòng test bị xóa/đổi so với develop; không skip/nới | Đạt |
| Phạm vi | Thay đổi nằm trong FEAT-029 (api/price_compare.py mở rộng theo ASM-028-11; scenario_norm.py thay vì sửa api/norm.py) | Đạt |
| Tài liệu chỉ đọc | Không có tệp srs/test-cases/use-cases/golden/implementation-plan/CLAUDE.md/.claude/.autopilot/.github bị sửa | Đạt |
| CI PR #87 | "Test trên site Frappe v15" và "Tài liệu, golden, unit test" đều SUCCESS (head 31c09fd) | Đạt |
| Giao diện Playwright (SCR-DSK-026) | Không chạy: staging chưa có nhánh này (chưa merge). Thay bằng `test_feat_029_ui.py` (pass) và test API trên site theo vai trò | Ghi chú, không chặn |

Verdict: **accepted**.
