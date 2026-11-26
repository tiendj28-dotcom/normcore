# As-Built: FEAT-024 Soạn dự thảo quy trình bằng AI
- Phiên bản app 0.0.1; Dev: NORM-63; nghiệm thu: QA (Multica), `docs/features/FEAT-024/acceptance.md`

## 1. Luồng nghiệp vụ đã xây
Người soạn mở dịch vụ, chọn "Soạn quy trình" (SCR-DSK-006). AI tắt: tạo bản nháp trống (UC-004 1a). AI bật: hộp thoại ba bước (SCR-DSK-008): xem nguồn (mục đã xác nhận, còn hiệu lực, quy trình hiện hành), nhập yêu cầu và chọn thêm mục, theo dõi tiến độ. `start_ai_draft` xếp tác vụ vào hàng đợi `long`; `run_ai_draft` gọi gateway, kiểm từng trích dẫn nguyên văn (`ai/citation.py`), dựng bản nháp (`procedure/ai_draft.py`): 7 phần văn bản, bước và nguồn lực mang `ai_suggested = 1`, trích dẫn "Theo hướng dẫn"/"Khác biệt", "Chưa có căn cứ" ở phần/bước không còn trích dẫn. Trích dẫn sai bị loại, số loại ghi vào NC AI Log. Trình soạn (SCR-DSK-009) hiện nhãn "Đề xuất", "Chấp nhận", "Bỏ", "Chấp nhận tất cả"; gửi duyệt bị từ chối khi còn đề xuất.

## 2. DocType tạo mới hoặc thay đổi
Không DocType hay trường mới (`doctor_request`, `ai_log`, `citations`, `ai_suggested` đã có từ FEAT-006). Controller NC Clinical Procedure: DI-08 (đoạn trích nguyên văn trong mục NC Legal Section được dẫn).

## 3. API, tác vụ nền, hook
- `api/procedure.py`: `prepare_ai_draft`, `search_extra_sources`, `start_ai_draft`, `run_ai_draft` (nền), `get_ai_draft_status`, `accept_suggestions`, `reject_suggestion`; `create_procedure` nhận `doctor_request`; `get_procedure` trả thêm `ai_suggested`, `ai_log`, `doctor_request`, `relations`, `section_label`.
- `ai/gateway.py::complete` thêm `postprocess`; `ai/prompts_install.py::ensure_draft_procedure_v2`.
- `hooks.py`: `doctype_js` cho NC Technical Service nạp `ai_draft_dialog.js`. Bản dịch `translations/vi.d/FEAT-024.csv`.

## 4. Quyền
Không đổi ma trận. Mọi API mới yêu cầu quyền tạo/sửa quy trình và phạm vi khoa; NC Auditor, NC Finance, Clinician khoa khác bị từ chối; trạng thái job chỉ người tạo đọc.

## 5. Cấu hình cần thiết khi triển khai
Cần NC AI Settings bật và worker hàng đợi `long`. Mẫu `DRAFT_PROCEDURE-v2` tự cài ở lần soạn AI đầu tiên (ASM-024-15).

## 6. Test case đã chạy và kết quả
TC-AI-01, 02, 03, 04, 10: xem `docs/rtm-testref/FEAT-024.md` và `implementation-log.md`. Chỉ dùng provider giả lập.

## 7. Giới hạn đã biết
- ASM-024-01..15 (`docs/decisions/assumptions/FEAT-024.md`); ASM-024-15 lệch thiết kế 3.5 (không patch/after_install cho mẫu v2).
- ASM-024-10: văn bản 7 phần do AI viết không có cờ "Đề xuất" riêng.
- Staging dùng provider `mock` chỉ trả `{"mock": true}`: nhánh thành công chỉ kiểm bằng test tích hợp.
- Giao diện SCR-DSK-008/009 chưa kiểm bằng trình duyệt (staging chưa có mã PR).
- Chất lượng mẫu lệnh trên bộ 10 dịch vụ mẫu chưa chấm (rủi ro của kế hoạch).
