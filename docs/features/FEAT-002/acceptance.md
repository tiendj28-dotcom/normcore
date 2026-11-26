# Nghiệm thu FEAT-002 — Trang chủ, việc chờ xử lý, thông báo, tham số vận hành

Người kiểm: QA (Multica, Tester iu). Commit đã kiểm: `d0a4f8129cc2d48d4d19a0bc7f65993dcce796f8` (HEAD PR #54).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-NOTI-01 (FR-NOTI-001, 003) | `test_TC_NOTI_01_gui_duyet_thong_bao_va_trang_chu_truong_khoa`, `..._viec_cho_dung_nguoi`, `..._auditor_khong_co_viec` (api/test_home.py): gửi duyệt → Trưởng khoa có Notification Log kèm liên kết; `get_home` liệt kê việc; NC Auditor và vai trò không quyền không có việc; Guest bị từ chối | Đạt |
| TC-ADM-03 (FR-ADM-003) | `test_TC_ADM_03_doi_so_ca_toi_thieu_ap_ngay`, `test_FR_ADM_003_*`; quyền NC Settings theo ma trận (NC Admin, NC Auditor, vai trò khác) | Đạt phần tham số; phần trung vị/cảnh báo thiếu ca thuộc FEAT-014 (Lead chọn PA1, ASM-002-13) |
| FR-NOTI-002 (email) | `test_FR_NOTI_002_email_khi_co_may_chu`, `..._khong_may_chu_van_thong_bao` | Đạt |
| FR-OUT-010 (tình trạng chuỗi) | `test_FR_OUT_010_*` (unit + api), lọc khoa và phạm vi quyền; "đã duyệt giá" = 0 kèm ASM-002-06 | Đạt |
| Chạy lại site sạch `normcore-verify.test` | `bench run-tests --app normcore`: Ran 1226 tests, OK (site tạo và xóa trong một lần gọi có khóa) | Đạt |
| pytest unit + golden + độ phủ | 631 passed; costing+benchmark phủ 99% (≥ 90%) | Đạt |
| golden_engine, golden_cls, build_rtm, check_conventions | chạy, không lỗi mới; check_conventions rc=0 | Đạt |
| Soát diff test | Không có test bị xóa, skip, nới; test FEAT-007 giữ nguyên | Đạt |
| Phạm vi / tài liệu chỉ đọc | Diff 31 tệp đều thuộc FEAT-002; không đụng srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI PR #54 | `gh pr checks 54`: "Test trên site Frappe v15" pass, "Tài liệu, golden, unit test" pass | Đạt |

## Giới hạn
- Chưa kiểm bằng trình duyệt (Playwright): nhánh PR chưa có trên staging 112.213.88.40:8100 và tôi không có tài khoản test cho từng vai trò; kiểm vai trò không quyền và NC Auditor được thực hiện bằng test bench (quyền, `get_home`).
- `get_home` dùng 9 truy vấn (thiết kế ≤ 6), ASM-002-16; chưa đo 300 dịch vụ.
