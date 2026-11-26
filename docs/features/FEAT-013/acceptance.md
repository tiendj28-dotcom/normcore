# Nghiệm thu FEAT-013: Phiên bản bộ định mức theo quy trình mới

Commit đã kiểm: `275b3dc815ce66f7e0dad0872bcdbbeea63cd6a4` (nhánh `feat/FEAT-013-norm-set-version`, PR #59). Người kiểm: Tester iu (QA độc lập).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-NORM-08 (FR-NORM-015): S001, S003, S004 mang sang; S002 đánh dấu; S005 trong danh sách chưa có dòng | `test_TC_NORM_08_phien_ban_theo_quy_trinh_moi` (api) kiểm cờ `step_removed` {S001:0,S002:1,S003:0,S004:0}, giữ `line_id`, `steps_without_lines == ["S005"]`, bộ nguồn không đổi; 13 test `test_TC_NORM_08_*` ở `test_norm_carry.py` | Đạt |
| Biên: bộ đã thay thế, tự bỏ nháp, không trùng, xóa dòng có cờ, client không tự ghi cờ | 8 test `test_FR_NORM_015_*` | Đạt |
| Quyền: vai không quyền, NC Auditor, Finance, khoa khác bị từ chối `new_version` | `test_quyen_new_version_auditor_finance_khoa_khac` | Đạt |
| Chạy từ đầu trên site sạch `normcore-verify.test` (với_bench, một lần gọi, site đã xóa) | `Ran 1317 tests ... OK`, BENCH_RC=0 | Đạt |
| pytest unit + golden + độ phủ | 695 passed; `normcore/costing` + `benchmark` phủ 99% (≥90%) | Đạt |
| golden_engine, golden_cls, build_rtm, check_conventions | chạy sạch, không vấn đề mới | Đạt |
| Soát diff test | không có dòng test bị xóa/sửa/skip; chỉ thêm test | Đạt |
| Phạm vi và tài liệu chỉ đọc | diff không chạm srs, test-cases, golden, CLAUDE.md, .github, .claude; `data-model.md` sửa theo AMD-013-01 đã ghi | Đạt |
| CI PR #59 | cả hai job SUCCESS trên `275b3dc` | Đạt |

Ghi chú: kiểm giao diện (SCR-DSK-014) bằng Playwright chưa thực hiện vì mã PR chưa có trên staging; hành vi lưới được phủ bởi `test_norm_grid_ui.py` và các test API (`get_norm_set`: nhóm "Bước đã bỏ", `steps_without_lines`, `actions`).
