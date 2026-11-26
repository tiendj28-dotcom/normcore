# Nghiệm thu FEAT-012 (NORM-39) — QA (Multica), commit b06a8ed9617cd770e5273293907f12ddd8ab1155

| Hạng mục | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Test trên site sạch `normcore-verify.test` (cài app, `run-tests --app normcore`, xóa site, một lần gọi with_bench) | Ran 1115 tests, OK, rc=0 | Đạt |
| pytest unit + golden, độ phủ `costing` + `benchmark` | 566 passed; TOTAL 99% (≥ 90%) | Đạt |
| `golden_engine.py`, `golden_cls.py` | chạy thoát 0 | Đạt |
| `check_conventions.py`, `build_rtm.py docs` | không báo lỗi mới (Must chưa có TC: 0) | Đạt |
| CI PR #51 ở `b06a8ed` | 2 job SUCCESS | Đạt |
| Tài liệu chỉ đọc (srs, test-cases, use-cases, golden, plan, CLAUDE.md, .claude, .autopilot, .github) | không có trong diff | Đạt |
| Diff test: không xóa/skip/nới | 4 tệp test FEAT khác chỉ thêm `confirm_norm_set` trước `lock()` (do FR-NORM-011, Quyết định Lead Q1); `test_FR_AUD_001_khoa_bo_dinh_muc` đổi vế từ-trạng-thái theo ASM-012-17 (Quyết định Lead), assertion giữ nguyên ý | Đạt |
| TC-NORM-01..07, 09..12 | mỗi TC có test `test_TC_NORM_NN_*` (api/test_norm.py, unit, golden), đều qua trong 1115 test | Đạt |
| TC-NORM-03 khớp golden (L03=20, L09=10, L01=10); FR-NORM-016 11 dòng khớp `direct_lines` | tests/golden/test_norm_golden.py | Đạt |
| Quyền: vai trò không quyền (Council) và NC Auditor | `test_quyen_norm_set_council_khong_co_quyen`, `test_quyen_norm_set_auditor_chi_doc`, Finance/Clinician | Đạt |
| Hai lỗ đi vòng FR-NORM-010/011 của Code review lần 1 | test mới `test_TC_NORM_02_insert_truc_tiep...`, `test_khoa_tu_nhap_bi_tu_choi_va_bo_khoa_khong_sua_qua_client` đạt | Đạt |
| Giao diện bằng trình duyệt (SCR-DSK-013/014, 1366×768) | **Chưa kiểm** bằng Playwright; chỉ có test tĩnh `test_norm_grid_ui.py` và `bench build` | Giới hạn, ghi ở As-Built |

Kết luận: accepted.

## Kiểm giao diện bằng Playwright (site cục bộ từ nhánh PR, 1366×768, dữ liệu dựng bằng fixture, đã xóa site)

Kết luận cập nhật: **rework**. Phần mã/test đạt như trên, nhưng giao diện có 2 lỗi (ảnh đính ở bình luận NORM-39).

| Màn hình / TC | Vai trò | Kết quả |
| :-- | :-- | :-- |
| SCR-DSK-013 `/app/nc-norm-set` danh sách | Clinician | KHÔNG ĐẠT: cột Mã số hiện chuỗi `<a href=...>` thô (`nc_norm_set_list.js:10-13`); nút "Khởi tạo bộ định mức" hiện |
| SCR-DSK-014 `/app/norm-grid/<bộ>` mở lưới | Clinician | KHÔNG ĐẠT: hộp thoại lỗi "Bạn không có quyền Đọc hoặc Chọn đối với NC Job Title" (`NormGrid.vue:151`, `ncLink` 279-298; `frappe.client.validate_link` 403); ô nguồn lực dòng Nhân lực trống. Lưới, cảnh báo "Còn 6 dòng chưa đủ điều kiện", chi phí tạm tính vẫn hiện |
| TC-NORM-12 xác nhận dòng L004 | Clinician | Đạt: dòng hiện "✓ clin.ui", các dòng khác vẫn "Xác nhận" |
| Bộ ở "Đã xác nhận chuyên môn", nút theo vai trò | Finance | Đạt: có "Khóa", "Trả lại"; thông báo "Không sửa được" |
| TC-NORM-06 khóa, sửa bị từ chối | Finance | Đạt: bộ chuyển "Đã khóa", banner "Tạo phiên bản mới"; `save_line` sau khóa trả 403 |
| Auditor mở lưới | Auditor | Đạt: không có nút "Thêm dòng"; không hộp thoại lỗi |
| TC-NORM-04, 05, 07, 09, 10, 11 trên giao diện | — | Chưa kiểm (dừng vì lỗi ở trên); đã có test API/unit đạt |
