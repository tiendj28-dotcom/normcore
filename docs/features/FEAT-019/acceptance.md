# Acceptance — FEAT-019 (NORM-48), commit 1cbc317ddfaf3c3835ba117ed2250088962a0131

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-OUT-01 (Phụ lục II, III, V khớp mẫu, số khớp golden) | test_TC_OUT_01_phu_luc_ii_iii_v_khop_golden, test_TC_OUT_01_xuat_phu_luc_cot_khop_mau | Đạt |
| TC-OUT-02 (giải trình PDF, tổng 287.745,46) | test_TC_OUT_02_giai_trinh_pdf_nhom_cau_phan_buoc | Đạt |
| TC-OUT-03 (trang truy vết + nhật ký "Xuất tệp") | test_TC_OUT_03_thong_tin_truy_vet_va_nhat_ky | Đạt |
| TC-OUT-04 (bộ định mức 11 dòng Excel/PDF) | test_TC_OUT_04_bo_dinh_muc_excel_pdf_11_dong | Đạt |
| FR-OUT-003, FR-OUT-009 (không có TC riêng) | test_phu_luc_iv_xuat_duoc, test_ho_so_nen_chay_nen_va_loi | Đạt |
| Quyền: vai trò không quyền, NC Auditor | test_quyen_xuat_theo_vai_tro | Đạt |
| Site sạch normcore-verify.test, toàn bộ test | Ran 1821 tests, OK | Đạt |
| pytest unit + golden + độ phủ | 1083 passed; costing 99% | Đạt |
| golden, build_rtm, check_conventions | VAN DE: 0, rc=0 | Đạt |
| Diff test | không xóa, skip, nới test nào | Đạt |
| Tài liệu chỉ đọc | diff với origin/develop rỗng | Đạt |
| CI PR #71 | 2 job pass (trên commit trước khi merge develop lần cuối) | Đạt |

Giới hạn: chưa kiểm giao diện bằng trình duyệt (Playwright); giao diện chỉ có test_export_ui.py. TBD-01: mẫu Phụ lục là mẫu tạm (ASM-019-01). DEF-019-01 do Lead quyết, không chặn FEAT này.

## Bổ sung NORM-78 (sửa hộp thoại xuất khi mở từ NC Service Cost bằng Trưởng khoa)

Commit kiểm: `11e054f`. Kiểm bởi QA độc lập.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch `normcore-verify.test`: `run-tests --module normcore.api.test_export` | 7 test OK (gồm khẳng định `own_service.norm_set`, hai nút bộ định mức `enabled`, HEAD tải được `norm_set_xlsx/pdf` không kèm `run`, HEAD2 bị `PermissionError`) | Đạt |
| Test tĩnh `normcore.tests.unit.test_export_ui` | 8 test OK | Đạt |
| `scripts/check_conventions.py` | exit 0 | Đạt |
| CI PR #80 trên `11e054f` | "Tài liệu, golden, unit test" và "Test trên site Frappe v15" đều SUCCESS (chạy toàn bộ test) | Đạt |
| Diff test | Chỉ thêm khẳng định/test; không xóa, skip, nới | Đạt |
| Phạm vi, tài liệu chỉ đọc | 5 tệp FEAT-019/037; không chạm docs/golden, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| Kiểm giao diện bằng `thu-qa-head@example.com` ở SC-00016 | Chưa làm được: staging chưa có bản sửa (PR chưa merge/deploy). Theo issue, kiểm lại sau merge và deploy | Chờ sau deploy |
