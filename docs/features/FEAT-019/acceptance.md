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

## Kiểm lại NORM-77 / PR #82 (AMD-019-02, bundle chống cache) — commit d280047

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch normcore-verify.test, toàn bộ test | `bench run-tests --app normcore` in OK; `bench build` ra `normcore_export.bundle.PUCLAKKQ.js` trong assets.json | Đạt |
| pytest unit + golden + độ phủ | 1143 passed, độ phủ 99% | Đạt |
| golden, build_rtm, check_conventions | rc=0, VAN DE: 0 | Đạt |
| Diff test | chỉ đổi giá trị mong đợi `test_hook_registry_khai_bao_tep` (ASM-019-18, Lead quyết), thêm `test_bundle_nap_hop_thoai_chong_cache`, bỏ test dò chuỗi của PR #79; test 1 lựa chọn giữ nguyên; không skip | Đạt |
| Tài liệu chỉ đọc | diff với origin/develop rỗng | Đạt |
| CI PR #82 | 2 job pass | Đạt |

Giới hạn: chưa kiểm trình duyệt trên staging vì PR #82 chưa merge. Sau khi merge và staging deploy, kiểm lại trên NORM-73 (không Ctrl+Shift+R) bằng tài khoản không phải Administrator.
