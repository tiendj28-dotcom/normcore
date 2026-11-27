# Nghiệm thu FEAT-038 — AI đề xuất định mức từ tài liệu của hãng

Commit đã kiểm: `0541907`. Người kiểm: Tester iu (QA, không viết FEAT này).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-CLS-41 (chỉ gửi mục đã gắn HC_GLU, quy trình, mặt hàng, thiết bị; không đơn giá, không sản lượng) | `api/test_cls_norm_ai.py::test_TC_CLS_41_noi_dung_gui_chi_gom_muc_da_gan` (provider giả; kiểm tập khóa nguồn/biến, chuỗi cấm, NC AI Log) | Đạt |
| TC-CLS-42 (3 đề xuất: 2 trích dẫn đúng, 1 "Chưa có căn cứ"; đều nhãn "Đề xuất", không vào phép tính) | `test_TC_CLS_42_trich_dan_va_nhan_de_xuat`, `..._ngoai_nguon_da_gui_bi_loai`, `..._khong_vao_phep_tinh`; unit `test_ai_cls_norm.py::test_TC_CLS_42_*` | Đạt |
| TC-CLS-43 (mặt hàng ngoài danh mục: không tạo mặt hàng, giữ dạng văn bản) | `test_TC_CLS_43_mat_hang_ngoai_danh_muc`; unit `test_TC_CLS_43_ma_ngoai_danh_muc` | Đạt |
| Quyền DocType mới NC AI Norm Suggestion (vai trò không quyền, NC Auditor chỉ đọc) | `test_quyen_nc_ai_norm_suggestion_doctype` | Đạt |
| Site sạch `normcore-verify.test` (new-site, install-app, run-tests, drop-site, một lần gọi) | Ran 1967 tests, OK, rc=0, mã `0541907` | Đạt |
| pytest unit + golden + độ phủ | 1164 passed; costing/benchmark tổng 99% | Đạt |
| golden_engine, golden_cls, check_conventions | chạy được; check_conventions rc=0 | Đạt |
| build_rtm | Chạy được; chỉ sinh lại `rtm.md`, `verification-report.md` (đã hoàn nguyên, không đưa vào commit) | Đạt |
| Soát diff test | Không dòng test bị xóa; không skip; test cũ không đổi giá trị | Đạt |
| Tài liệu chỉ đọc | Diff không chạm docs/golden, srs, test-cases, use-cases, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| Phạm vi (không sửa `api/norm.py`, `public/js/norm_grid/`) | Diff chỉ có tệp thuộc FEAT-038; API mới ở `api/cls_norm_ai.py` | Đạt |
| CI PR #83 | Hai job pass (Test trên site Frappe, Tài liệu/golden/unit) | Đạt |

Ghi chú: kiểm giao diện bằng trình duyệt chưa thực hiện (staging chưa có nhánh này, không có tài khoản test cho vai trò); giao diện được bao phủ bằng `test_feat_038_ui.py` và test API/DocType trong bench. Chất lượng đề xuất trên tài liệu thật chưa chấm (provider giả).
