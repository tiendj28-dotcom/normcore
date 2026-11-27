# As-Built FEAT-038 — AI đề xuất định mức từ tài liệu của hãng

Issue NORM-79. FR: FR-LIB-013, FR-AI-016..018. UC-025. SCR-DSK-003 (phần tài liệu của hãng), SCR-DSK-014, SCR-DSK-033. TC: TC-CLS-41..43. Bản phát hành R2.
Giới hạn: giao diện (`cls_norm_suggest.js`, khối `// FEAT-038` ở `nc_qc_plan.js`, `nc_norm_set.js`, `nc_legal_document.js`) kiểm bằng test unit đọc mã (`test_feat_038_ui.py`) và `bench build`; chưa kiểm bằng trình duyệt. Chất lượng đề xuất trên tài liệu thật chưa chấm: staging dùng provider `mock`, nhánh thành công chỉ kiểm bằng test tích hợp với provider giả.

## Đã làm
- **Tài liệu của hãng (FR-LIB-013):** NC Legal Document thêm loại "Tài liệu của hãng" và bảng con `related_resources` (NC Document Resource Link: `linked_doctype` NC Item/NC Equipment, `linked_name`). Loại này bắt buộc có ít nhất một dòng, không trùng; loại khác giữ bảng, không báo lỗi (ASM-038-02). Hàm thuần `library/manufacturer.py::resource_link_errors`. Tách mục dùng nguyên luồng FEAT-020.
- **DocType mới NC AI Norm Suggestion (AMD-038-01):** lưu đề xuất bốn loại (lượng hóa chất mỗi test, tần suất chuẩn máy, tần suất nội kiểm, hạn dùng sau mở) cùng trích dẫn, căn cứ, trạng thái Đề xuất → Đã chấp nhận | Đã bỏ (một chiều). Quyền theo dòng "Hệ thống xét nghiệm, kế hoạch chất lượng…", phạm vi khoa theo `department`, không ai xóa. Không DocType tính giá nào đọc nó (FR-AI-008).
- **Phần thuần `norm/ai_cls_norm.py`:** phạm vi nguồn (`system_resources`, `docs_in_scope`), kiểm đầu ra AI (`parse_suggestions`: trích dẫn nguyên văn qua `ai/citation.py`, mã ngoài danh mục), kế hoạch chấp nhận (`plan_accept`). `ai/guard.py::manufacturer_sections` chỉ cho mục của tài liệu trong phạm vi; `ALLOWED_SOURCES` không đổi.
- **API `api/cls_norm_ai.py`:** `start_cls_norm_suggestion`, `run_cls_norm_suggestion` (nền, hàng đợi `long`), `get_cls_norm_suggestion_status`, `list_cls_norm_suggestions`, `accept_cls_norm_suggestion`, `reject_cls_norm_suggestion`, `link_cls_norm_suggestion`. Dùng chung gateway, mẫu lệnh (`SUGGEST_CLS_NORM-v2`, cài lười), NC AI Log; không kênh gọi AI mới. Không sửa `api/norm.py`, `public/js/norm_grid/`.
- **Chấp nhận** ghi vào bản ghi đích bằng quyền của người dùng: dòng bộ định mức Nháp (`basis` "Ước tính", `basis_ref` = số hiệu + mục, xóa xác nhận dòng), dòng kế hoạch chất lượng, `open_stability_days` của NC Item (Resource Mgr, Finance, Admin). Lỗi đích giữ đề xuất ở "Đề xuất".
- **Giao diện:** dải "N đề xuất AI chưa xử lý", nút "AI đề xuất định mức" (chỉ khi AI bật và có quyền sửa; ở NC Norm Set chỉ bộ Nháp), nút "Xem đề xuất AI", hộp thoại có Chấp nhận, Bỏ, Liên kết. `vi.d/FEAT-038.csv`.

## Ghi chú
- ASM-038-01..16 trong `docs/decisions/assumptions/FEAT-038.md`. ASM-038-15: thêm `NC AI Norm Suggestion` vào danh sách `SCOPED` của `test_scope_registry.py` (ngoại lệ CLAUDE.md mục 3 luật 1, theo AMD-038-01). ASM-038-16: dải đề xuất là khối riêng thay vì headline.
- `docs/data-model.md` đã thêm khối NC AI Norm Suggestion (3.5) và ghi chú mục 4 theo AMD-038-01.
- Lần chạy thành công đổi đề xuất chờ cũ của hệ thống sang "Đã bỏ" (ASM-038-11).

## Test đã chạy
Site sạch sau merge develop: `bench run-tests --app normcore` 1966 test OK. pytest unit + golden 1164 passed, độ phủ `normcore/costing` + `normcore/benchmark` 98,89%; `ai_cls_norm.py` 100%. `check_conventions.py` thoát 0; `build_rtm.py` VAN DE: 0. TC-CLS-41..43: `test_TC_CLS_41_noi_dung_gui_chi_gom_muc_da_gan`, `test_TC_CLS_42_trich_dan_va_nhan_de_xuat`, `test_TC_CLS_43_mat_hang_ngoai_danh_muc`.
