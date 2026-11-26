# As-Built: FEAT-025 Kiểm tra nhất quán và đề xuất liên kết định mức
- Phiên bản app 0.0.1; Dev: NORM-71; nghiệm thu: QA (Multica), `docs/features/FEAT-025/acceptance.md`

## 1. Luồng nghiệp vụ đã xây
- **FR-AI-006 (UC-005 bước 6, 6a).** Ở trình soạn quy trình (SCR-DSK-009), người có quyền sửa bản nháp bấm "Kiểm tra nhất quán". `check_consistency` chạy đồng bộ, không ghi gì vào quy trình, trả: (1) nguồn lực lệch giữa các bước và phần "Chuẩn bị" (hai chiều, bỏ qua Nhân lực; không có bước Chuẩn bị thì báo một mục), (2) bước thiếu nguồn lực Nhân lực, hai mục này bằng quy tắc thuần (`procedure/consistency.py`), (3) nội dung có thể trái chống chỉ định do AI đề xuất qua gateway (mẫu `CONSISTENCY_CHECK`); đoạn trích phải khớp nguyên văn trong chống chỉ định, đích đúng một trong bước, dòng nguồn lực, phần. AI tắt: không có phần AI; chống chỉ định trống: bỏ qua; AI lỗi/quá hạn/hết hạn mức: vẫn trả (1)(2) và báo "Phần kiểm tra bằng AI chưa thực hiện".
- **FR-AI-007 (UC-009 bước 2–4, 8a).** Bộ mới tạo từ quy trình đã ban hành, AI bật, có dòng chưa liên kết: `NCNormSet.after_insert` khởi tác vụ nền `run_link_suggestion` lọc ứng viên NC Item (đang dùng, trừ chất chuẩn/vật liệu nội kiểm) và NC Equipment bằng độ tương đồng từ (`norm/ai_link.py::shortlist`), AI chỉ được chọn trong danh sách ứng viên, ghi `resource`, `component`, `ai_suggested = 1`, `ai_confidence` (0–100). Theo AMD-025-02, giao diện nằm ở form NC Norm Set (`nc_norm_set.js`): nút "Đề xuất liên kết" (bộ Nháp, quyền ghi, AI bật), dải "{0} dòng có đề xuất…", nút "Xem đề xuất liên kết" mở hộp thoại có độ tin cậy, "Chấp nhận", "Bỏ", "Chấp nhận tất cả". Lưới (SCR-DSK-014) giữ như FEAT-012 (nhãn "Đề xuất", không độ tin cậy, không nút). Sửa `resource`/`resource_doctype`/`component` của dòng đề xuất ở mọi đường ghi thì mất nhãn (controller). Còn đề xuất thì chặn xác nhận dòng và chuyển "Đã xác nhận chuyên môn" (có từ FEAT-012, FEAT-025 thêm test).

## 2. DocType tạo mới hoặc thay đổi
Không DocType mới. NC Norm Line thêm `ai_confidence` (Percent, chỉ đọc; AMD-025-01); `docs/data-model.md` 3.5 đã áp. `bench migrate` tự thêm cột, không cần patch. Controller NC Norm Set: `AI_LINK_FIELDS`, `guard_ai_fields`, `after_insert` (chỉ đường `norm_action = "ai_link"` đặt được `ai_suggested`/`ai_confidence`; đường khác bị khôi phục).

## 3. API, tác vụ nền, hook
- `api/procedure.py`: `check_consistency`.
- `api/norm_link.py` (mới; `api/norm.py` và `norm_grid/` giữ nguyên như develop): `start_link_suggestion`, `run_link_suggestion` (nền, hàng đợi `long`), `get_link_suggestion_status`, `accept_link_suggestions`, `reject_link_suggestion`, `list_link_suggestions`.
- `ai/prompts_install.py`: `_ensure_v2`, `ensure_consistency_check_v2`, `ensure_suggest_norm_link_v2` (cài lười, ASM-025-11).
- Giao diện: `ProcedureEditor.vue`, `nc_norm_set.js`; bản dịch `translations/vi.d/FEAT-025.csv`.

## 4. Quyền
Không đổi ma trận. `check_consistency`: quyền ghi quy trình + "Nháp". Các API đề xuất: quyền ghi bộ định mức + "Nháp" + vai trò soạn (Clinician, Dept Head). NC Auditor, NC Finance, Clinician khoa khác: `PermissionError`; trạng thái tác vụ chỉ người tạo đọc. NC Auditor đọc được `ai_confidence`.

## 5. Cấu hình cần thiết khi triển khai
NC AI Settings bật và worker hàng đợi `long` (đề xuất liên kết). Mẫu `CONSISTENCY_CHECK-v2`, `SUGGEST_NORM_LINK-v2` tự cài ở lần gọi đầu.

## 6. Test case đã chạy và kết quả
`test-cases.md` chưa có TC cho FR-AI-006, FR-AI-007 (ASM-025-01): test mang mã FR/UC. Xem `docs/rtm-testref/FEAT-025.md` và `implementation-log.md`. Chỉ dùng provider giả lập.

## 7. Giới hạn đã biết
- AMD-025-02/ASM-025-15: giao diện và API chuyển khỏi lưới/`api/norm.py`; DEF-025-01: test `test_luoi_va_api_norm_khong_doi` chặn mọi FEAT sau sửa hai chỗ đó (chờ người quyết).
- ASM-025-01..15 (`docs/decisions/assumptions/FEAT-025.md`); ASM-025-13 lệch thiết kế 3.4/3.5: `purpose` của `gateway.complete` là mã mẫu lệnh.
- `check_consistency` gọi AI đồng bộ: `timeout_seconds` lớn hơn thời hạn yêu cầu web (gunicorn mặc định 120 giây) có thể bị cắt trước gateway; đổi sang hàng đợi nếu đo thấy chậm (ASM-025-06).
- Ứng viên lọc bằng độ tương đồng từ có thể bỏ sót bản ghi khớp nghĩa nhưng khác chữ; người dùng liên kết tay.
- Không đề xuất cho dòng Phòng và Nhân lực (ASM-025-09). Kết quả kiểm nhất quán không lưu (ASM-025-05); không tự lưu ô đang sửa dở trước khi kiểm (ASM-025-14).
- Staging dùng provider `mock` chỉ trả `{"mock": true}`: nhánh có kết quả chỉ kiểm bằng test tích hợp. Giao diện chưa kiểm bằng trình duyệt; chất lượng mẫu lệnh trên dữ liệu thật chưa chấm.
