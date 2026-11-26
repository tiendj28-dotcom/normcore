# FEAT-024 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-006 (nút "Soạn quy trình", AMD-004), SCR-DSK-008 ("Hộp thoại nhiều bước: xem nguồn sẽ dùng; nhập yêu cầu; chọn mục bổ sung — không có nguồn (cảnh báo); đang soạn (tiến độ); lỗi AI (cho soạn tay)"), SCR-DSK-009 ("Đề xuất AI chưa xử lý; chỗ Khác biệt, Chưa có căn cứ"), bảng thành phần "Bảng trích dẫn", "Thẻ bước"; `design.md` mục 3 ("Nhãn quan hệ trích dẫn": Theo hướng dẫn `green`, Khác biệt `orange`, Chưa có căn cứ `red`; "Dòng đề xuất của AI": nền nhấn nhẹ, nhãn "Đề xuất" `purple`, hai nút nhỏ "Chấp nhận" và "Bỏ"); `technical-design.md` (TD) mục 3.6. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.d/` (cùng cách FEAT-006/020); thông báo máy chủ tiếng Việt. Chạy được ở 1366 × 768; mọi thao tác dùng được bằng bàn phím (Tab, Enter, Esc); tương phản theo NFR-USE-004 — dùng `indicator-pill` và biến CSS của Desk, không tự đặt màu chữ.

## SCR-DSK-006 Dịch vụ kỹ thuật — nút "Soạn quy trình"

Loại: Form chuẩn NC Technical Service (mở rộng `nc_technical_service.js`).

- Nút `frm.add_custom_button(__("Draft procedure"), …)` ("Soạn quy trình"), nhóm trống (nút chính cạnh "Khởi tạo bộ định mức" nếu có). Hiện khi: bản ghi đã lưu, `frappe.model.can_create("NC Clinical Procedure")`. NC Auditor, NC Finance, vai trò chỉ đọc: không thấy nút.
- Bấm:
  - `normcore.ai.enabled()` = `false` (UC-004 1a, FR-AI-015): hộp thoại nhỏ chọn khoa (Link NC Department, BB, mặc định khoa đầu tiên của người dùng) → `normcore.api.procedure.create_procedure(technical_service, department)` → mở `/app/procedure-editor?name=<tên>`. Không có chữ "AI" nào trên màn hình.
  - AI bật: mở SCR-DSK-008.
- Lỗi `ExistingProcedureError` (1b) ở bất kỳ đường nào: `frappe.msgprint` của máy chủ đã hiện; thêm nút "Open existing procedure" ("Mở quy trình đang có") mở `existing_procedure` trong trình soạn.

## SCR-DSK-008 Yêu cầu soạn dự thảo (hộp thoại nhiều bước)

Loại: `frappe.ui.Dialog` (kích thước `large`, cao tối đa 80vh, cuộn trong thân) trong `normcore/public/js/ai_draft_dialog.js`, hàm `normcore.procedure.open_ai_draft_dialog({technical_service, service_name})`. Tiêu đề: "Draft procedure with AI — {0}" ("Soạn dự thảo quy trình bằng AI — {0}", {0} = mã · tên dịch vụ). Dòng chỉ bước trên cùng: "1. Sources · 2. Request · 3. Drafting" ("1. Nguồn · 2. Yêu cầu · 3. Soạn"), bước hiện tại in đậm, `aria-current="step"`.

### Bước 1 — Nguồn sẽ dùng
Trường: `department` (Link NC Department, BB, mặc định khoa đầu tiên trong phạm vi của người dùng). Đổi khoa → gọi `prepare_ai_draft(technical_service, department)`.

| Thành phần | Nội dung |
| :-- | :-- |
| Đang tải | "Loading sources…" ("Đang tải nguồn…"), `role="status"` |
| `existing` khác null (1b) | Khung `alert-warning`: "This service already has a {0} procedure for this department: {1}" ("Dịch vụ đã có quy trình {0} của khoa này: {1}", {0} = trạng thái, {1} = liên kết mở trình soạn). Nút "Next" khóa |
| Danh sách nguồn | Bảng: Văn bản (`doc_number`), Số mục, Tiêu đề; mỗi dòng có liên kết "View" ("Xem") mở `get_source_view(section)` trong cửa sổ phụ chỉ đọc. Dòng tóm tắt "{0} confirmed guideline sections in effect" ("{0} mục hướng dẫn đã xác nhận, còn hiệu lực") |
| `current_procedure` | Dòng "Current hospital procedure: {0} (v{1}) will also be sent" ("Quy trình hiện hành của bệnh viện: {0} (v{1}) cũng được gửi") |
| `no_sources = true` (2a, FR-AI-004) | Khung `alert-warning` (không phải lỗi): "This service has no confirmed guideline section in effect. The draft will be marked 'Unsupported' wherever there is no source." ("Dịch vụ chưa có mục hướng dẫn nào đã xác nhận và còn hiệu lực. Dự thảo sẽ mang nhãn "Chưa có căn cứ" ở mọi phần không có nguồn.") + ô Check BB để đi tiếp: "I understand and want to continue" ("Tôi hiểu và muốn soạn tiếp") → `confirm_no_source = 1`. Bước 2 vẫn cho chọn mục bổ sung |

Nút: "Next" ("Tiếp", chính), "Cancel" ("Hủy").

### Bước 2 — Yêu cầu
| Trường | Kiểu | Ghi chú |
| :-- | :-- | :-- |
| `doctor_request` | Small Text, BB, tối đa 5000 ký tự, cao 6 dòng | Nhãn "Request" ("Yêu cầu của người soạn"); mô tả dưới ô: "Department conditions, equipment, drugs, supplies, technique variants. Where you differ from the guideline, say so here; it becomes the deviation reason." ("Điều kiện của khoa, thiết bị, thuốc, vật tư, biến thể kỹ thuật. Chỗ nào khác hướng dẫn, ghi rõ ở đây; đó sẽ là lý do khác biệt.") Bộ đếm ký tự "{0}/5000" |
| Mục bổ sung | Ô tìm (Data) + danh sách kết quả | Nhãn "Additional sections (optional)" ("Mục bổ sung (không bắt buộc)"). Gõ ≥ 2 ký tự, chờ 300 ms → `search_extra_sources(query, technical_service)`; kết quả: Văn bản · Số mục · Tiêu đề, nút "Add" ("Thêm"). Mục đã chọn hiện thành thẻ có nút "×" (`aria-label` "Remove {0}" / "Bỏ {0}"); tối đa 20 (đạt 20 → khóa "Thêm", dòng "Up to 20 sections" / "Tối đa 20 mục") |

Nút: "Back" ("Quay lại"), "Draft" ("Soạn dự thảo", chính; khóa khi `doctor_request` trống). Dữ liệu đã nhập giữ khi quay lại bước 1.

### Bước 3 — Đang soạn / kết quả
Bấm "Soạn dự thảo" → `start_ai_draft(technical_service, department, doctor_request, extra_sections, confirm_no_source)`.

| Trạng thái | Hiển thị | Hành động |
| :-- | :-- | :-- |
| Lỗi đồng bộ (AI tắt, 1b, NoSourceError, mục bổ sung không hợp lệ) | Quay lại bước tương ứng (1 cho 1b/NoSource, 2 cho mục bổ sung), thông báo máy chủ trong `alert-danger` | Sửa rồi thử lại |
| `queued` / `running` | Thanh tiến độ vô định (`progress-bar-striped active`) + "AI is drafting… This can take up to {0} seconds." ("AI đang soạn… có thể mất tới {0} giây.", {0} = thời hạn cấu hình, lấy từ `get_ai_status`), `role="status"`, `aria-live="polite"`. Nghe `frappe.realtime.on("normcore_ai_draft")` theo `job_id`, dự phòng `get_ai_draft_status(job_id)` mỗi 3 giây | "Close" ("Đóng") — job vẫn chạy; khi xong có `frappe.show_alert` "Draft {0} is ready" ("Dự thảo {0} đã xong") kèm liên kết |
| `done` | Đóng hộp thoại, `frappe.show_alert` (`green`) "Draft {0} created. {1} citation(s) removed for not matching the source." ("Đã tạo dự thảo {0}. {1} trích dẫn bị loại vì không khớp nguyên văn nguồn.", vế sau chỉ khi `rejected > 0`), mở `/app/procedure-editor?name=<procedure>` | — |
| `failed` (4a, FR-AI-010) | `alert-danger` với `error` của máy chủ (ví dụ "Dịch vụ AI không phản hồi trong 180 giây. Dữ liệu của bạn được giữ nguyên; có thể soạn thủ công.") | "Retry" ("Thử lại", về bước 3 với cùng dữ liệu), "Draft manually" ("Soạn thủ công": `create_procedure(technical_service, department, doctor_request)` rồi mở trình soạn; yêu cầu đã nhập được lưu vào `doctor_request` của bản nháp, không mất), "Back" |
| `unknown` | "The drafting job can no longer be tracked. Check the procedure list." ("Không còn theo dõi được tác vụ soạn. Kiểm tra danh sách quy trình.") | "Retry", "Close" |

Esc đóng hộp thoại ở bước 1–2 (hỏi xác nhận nếu `doctor_request` đã có chữ: "Discard your request?" / "Bỏ yêu cầu đã nhập?").

## SCR-DSK-009 Trình soạn quy trình — mở rộng `ProcedureEditor.vue`

Loại: Desk Page Vue `procedure-editor` (FEAT-006). Chỉ thêm; bố cục, nút và hành vi cũ giữ nguyên (`test_procedure_editor_behavior.py` phải xanh). Dữ liệu thêm từ `get_procedure`: `ai_suggested` ở bước và nguồn lực, `ai_log`, `doctor_request`, `section_label` ở trích dẫn, và `relations` (TD 3.6: ánh xạ `"step:<id>"` / `"section:<nhãn>"` → các quan hệ khác nhau của đích đó, tính từ toàn bộ bảng trích dẫn, để vẽ nhãn trên thẻ mà không phải tải mọi trích dẫn).

| Vị trí | Thêm |
| :-- | :-- |
| Dưới tiêu đề (chỉ khi còn ≥ 1 `ai_suggested`) | Dải `nc-pe__notice` `role="note"`: "{0} AI suggestion(s) not yet handled. Accept or remove them before submitting." ("Còn {0} đề xuất AI chưa xử lý. Chấp nhận hoặc bỏ trước khi gửi duyệt.") + nút "Accept all" ("Chấp nhận tất cả", khi `can_edit`; `frappe.confirm` "Accept all {0} AI suggestions?" / "Chấp nhận cả {0} đề xuất AI?" → `accept_suggestions(procedure, all=1)`) + liên kết "Next suggestion" ("Đề xuất kế tiếp") cuộn và đặt focus tới thẻ đề xuất kế tiếp |
| Dưới tiêu đề (khi `ai_log` có giá trị, ở "Nháp") | Dòng nhỏ `text-muted`: "Drafted by AI. Section text was written by AI; check it before submitting." ("Do AI soạn. Văn bản các phần do AI viết; kiểm trước khi gửi duyệt.") (ASM-024-10) + liên kết "Request" ("Yêu cầu") mở popover chỉ đọc `doctor_request` |
| Thẻ bước có `ai_suggested` | Lớp `nc-pe__card--ai` (nền `var(--bg-purple)` hoặc `var(--subtle-fg)` nếu Desk không có), `indicator-pill purple` "Suggested" ("Đề xuất") ngay sau tiêu đề; trong `nc-pe__actions` (khi `can_edit`) thêm trước "Sửa": "Accept" ("Chấp nhận") → `accept_suggestions(procedure, step_ids=[id])`; "Remove" ("Bỏ") → `frappe.confirm` "Remove suggested step {0} with its resources and citations?" ("Bỏ bước đề xuất {0} cùng nguồn lực và trích dẫn của bước?") → `reject_suggestion(procedure, step_id)`. Nút "Xóa" cũ ẩn ở thẻ đề xuất (tránh hai nút xóa). Sau khi chấp nhận: thẻ về dạng thường |
| Dòng nguồn lực có `ai_suggested` | Lớp `nc-pe__row--ai`, `indicator-pill purple` "Suggested" trong ô Mã dòng; nút "Accept" → `accept_suggestions(procedure, resource_row_ids=[id])`, "Remove" → `delete_resource` có sẵn (`frappe.confirm` "Remove suggested resource {0}?" / "Bỏ nguồn lực đề xuất {0}?") |
| Tiêu đề phần và đầu thẻ bước | Mỗi quan hệ trong `relations[target]` một `nc-pe__rel` nhỏ (cùng lớp màu `relClass` đã có): "Khác biệt" `orange`, "Chưa có căn cứ" `red`; "Theo hướng dẫn" không hiện ở đây (đỡ nhiễu) |
| Bảng trích dẫn (cột phải) | Khi có `section_label`: hiện `section_label` thay cho `[legal_document, legal_section]`, kèm liên kết "Open source" ("Mở mục nguồn") gọi `get_source_view(legal_section)` (ux-foundations "mở được mục nguồn"). Trích dẫn "Khác biệt": lý do hiện như cũ, nút "Edit" cũ sửa được lý do (FR-AI-003) |
| Gửi duyệt bị từ chối (TC-AI-10) | Không đổi: thông báo máy chủ liệt kê "Bước S003 còn là đề xuất AI chưa xử lý"; thêm: mỗi mã bước/dòng trong thông báo là liên kết `jump` tới thẻ đó nếu `review` đang hiện lỗi dạng danh sách |

Trạng thái:
- **Chỉ đọc** (NC Auditor, vai trò không có quyền ghi, ngoài "Nháp"): vẫn thấy nhãn "Đề xuất", nhãn quan hệ, dải đếm (không nút "Chấp nhận tất cả"); không có nút "Chấp nhận", "Bỏ".
- **Đã ban hành**: không thể có `ai_suggested` (gửi duyệt đã chặn); không vẽ dải.
- **Đang tải / lỗi**: dùng `loading`, `error` có sẵn; lỗi của `accept_suggestions` / `reject_suggestion` hiện ở `error` (`role="alert"`), không tải lại trang.
- Mọi nút mới có `:disabled="busy"`, `aria-label` kèm mã bước/dòng (ví dụ "Accept S003" / "Chấp nhận S003").

## Kiểm (QA, Playwright trên staging, `vi`, 1366 × 768)

1. Form dịch vụ: Clinician thấy "Soạn quy trình"; Auditor không thấy. AI tắt → bấm tạo bản nháp trống, không có chữ AI.
2. Hộp thoại: dịch vụ có nguồn → danh sách nguồn đúng; dịch vụ không có nguồn → cảnh báo, phải tích ô mới "Tiếp"; Tab đi qua mọi trường theo thứ tự; Esc hỏi xác nhận khi đã nhập.
3. `site_config.normcore_ai_provider = "mock"` trên staging chỉ trả `{"mock": true}` → job `failed` với thông báo cấu trúc sai: kiểm nhánh lỗi, "Thử lại", "Soạn thủ công" (nhánh thành công kiểm bằng test tích hợp; smoke nhánh thành công cần provider thật, ngoài phạm vi test tự động).
4. Trình soạn với bản nháp AI dựng sẵn (dữ liệu test): nhãn "Đề xuất" tím, "Chấp nhận" / "Bỏ" bằng bàn phím, dải đếm giảm, "Khác biệt" / "Chưa có căn cứ" trên thẻ, gửi duyệt khi còn đề xuất bị từ chối và nêu bước.
