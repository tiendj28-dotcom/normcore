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

## Kiểm lại ở commit 75f4942561fd11ae39bbb93d775fd2e75607caeb (sau sửa giao diện)

| Hạng mục | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Site sạch `normcore-verify.test`, toàn bộ test | Ran 1118 tests, OK, rc=0; site đã xóa | Đạt |
| pytest unit + golden, độ phủ | 567 passed, phủ 99% | Đạt |
| check_conventions, build_rtm | không lỗi mới | Đạt |
| Diff test từ `b06a8ed` | chỉ thêm test (test_norm.py, test_norm_grid_ui.py), không xóa/nới | Đạt |

### Giao diện bằng Playwright (site cục bộ từ nhánh PR, 1366×768, dữ liệu dựng bằng fixture, đã xóa site)

| Màn hình / TC | Vai trò | Kết quả |
| :-- | :-- | :-- |
| SCR-DSK-013 danh sách, cột Mã số, nút "Khởi tạo bộ định mức" | Clinician | Đạt (lỗi cũ đã sửa; ảnh 11) |
| SCR-DSK-014 mở lưới, nhãn nguồn lực nhân lực, không hộp thoại lỗi | Clinician, Dept Head | Đạt (lỗi cũ đã sửa; ảnh 12, 21) |
| TC-NORM-10 xóa đơn vị | Clinician | Đạt: "Dòng L004 thiếu: Đơn vị" |
| TC-NORM-07 đánh dấu loại trừ không lý do | Clinician | Đạt: yêu cầu chọn Lý do loại trừ thuộc danh sách |
| TC-NORM-04 hao hụt vượt trần 5% (nhập 9) | Clinician | Đạt: "hao hụt 9% vượt trần, cần nhập Lý do vượt trần"; nhập lý do thì lưu |
| TC-NORM-11 căn cứ "Định mức ban hành" + tham chiếu | Clinician | Đạt: API trả basis và basis_ref đã lưu |
| TC-NORM-12 xác nhận dòng | Clinician | Đạt: chỉ L004 hiện người xác nhận |
| TC-NORM-05 xác nhận bộ còn dòng chưa đủ | Dept Head | Đạt: từ chối, liệt kê "L005: Chưa xác nhận", "L006: Chưa xác nhận, Chưa liên kết danh mục", bộ vẫn Nháp |
| TC-NORM-09 thêm dòng điện không chọn bước | Dept Head | Đạt: bắt buộc chọn bước hoặc "Chung cho cả dịch vụ"; chọn chung thì thêm L007 |
| TC-NORM-06 khóa, sửa bị từ chối | Finance | Đạt (lần kiểm trước): "Đã khóa", `save_line` 403 |
| Auditor chỉ đọc | Auditor | Đạt (lần kiểm trước): không có nút Thêm dòng |

Ghi chú nhỏ (không chặn): ô "Gắn với" báo "Please select an item in the list." bằng tiếng Anh (thông báo gốc của trình duyệt); lưu căn cứ trên dòng chưa liên kết nguồn lực (L003) không có phản hồi nào trên giao diện, dòng đã liên kết thì lưu bình thường.

Kết luận: accepted.
