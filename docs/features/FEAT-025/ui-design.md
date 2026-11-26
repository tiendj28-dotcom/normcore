# FEAT-025 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-009 ("kiểm tra nhất quán"; trạng thái "Đề xuất AI chưa xử lý"), SCR-DSK-014 ("Dòng đề xuất AI; dòng chưa liên kết"); `design.md` mục 3 ("Dòng đề xuất của AI": nền nhấn nhẹ, nhãn "Đề xuất" `purple`, hai nút nhỏ "Chấp nhận" và "Bỏ"); `technical-design.md` (TD) mục 3.4, 3.5; ui-design FEAT-012, FEAT-024 (giữ nguyên thành phần đã có). Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `normcore/translations/vi.d/FEAT-025.csv`; thông báo máy chủ tiếng Việt. Chạy được ở 1366 × 768; thao tác được bằng bàn phím (Tab, Enter, Esc); dùng `indicator-pill`, `alert-*` và biến CSS của Desk, không tự đặt màu chữ. FR-AI-015: AI tắt (`normcore.ai.enabled()` = false) thì không có nút hay chữ "AI" nào.

## SCR-DSK-009 Trình soạn quy trình — mở rộng `ProcedureEditor.vue`

### Nút "Kiểm tra nhất quán"
- Vị trí: thanh `nc-pe__bar`, cạnh các nút hiện có, kiểu `btn-default btn-sm`. Nhãn "Check consistency" ("Kiểm tra nhất quán").
- Hiện khi `doc.can_edit` (quyền ghi + "Nháp"). Bản đã ban hành, NC Auditor, NC Finance: không thấy nút. Hiện cả khi AI tắt (kiểm bằng quy tắc vẫn chạy, ASM-025-08).
- Bấm → `normcore.api.procedure.check_consistency(procedure)`; nút khóa, chữ "Checking…" ("Đang kiểm tra…"), `aria-busy="true"`. Có thay đổi chưa lưu trong ô đang sửa: lưu trước như các thao tác khác của trình soạn.

### Khung kết quả (panel bên phải, thay chỗ bảng trích dẫn khi mở; nút "Close" ("Đóng") hoặc Esc quay lại bảng trích dẫn)
Tiêu đề "Consistency check" ("Kiểm tra nhất quán") + giờ kiểm (`checked_on`, định dạng NFR-LOC-001). `role="region"`, `aria-live="polite"`.

| Nhóm | Nguồn dữ liệu | Hiển thị |
| :-- | :-- | :-- |
| "Resources used in steps but missing from preparation" ("Nguồn lực có ở bước nhưng thiếu ở phần chuẩn bị") | `rule_issues` kind `missing_in_preparation` | Mỗi mục một dòng: nhãn `orange`, tên nguồn lực, các mã bước là nút liên kết |
| "Prepared resources not used in any step" ("Nguồn lực chuẩn bị nhưng không dùng ở bước nào") | `unused_in_steps` | như trên |
| "No preparation step" | `no_preparation_step` | Một dòng `alert-warning`: message máy chủ |
| "Steps without performer" ("Bước thiếu người thực hiện") | `no_performer` | Nhãn `orange`, mã · tên bước (nút) |
| "Possible conflicts with contraindications" ("Có thể trái chống chỉ định") | `ai.issues` khi `ai.status = "done"` | Mỗi mục: nhãn `purple` "Suggested" ("Đề xuất"), đích (mã bước / mã dòng nguồn lực / tên phần), `explanation`, trích `excerpt` trong khối trích dẫn nhỏ. Không có nút Chấp nhận/Bỏ: đây là gợi ý để người soạn tự sửa |

- Nhóm rỗng: không hiện. Mọi nhóm quy tắc rỗng: dòng `alert-success` "No inconsistency found by rules" ("Không thấy điểm lệch theo quy tắc").
- Phần AI theo `ai.status`:
  - `done` + không mục: dòng nhỏ "AI found no conflict with contraindications" ("AI không thấy nội dung trái chống chỉ định"). `rejected > 0`: thêm "{0} AI suggestions were discarded as invalid" ("Đã loại {0} đề xuất AI không hợp lệ").
  - `failed` (UC-005 6a): `alert-warning` với `ai.message` của máy chủ ("Phần kiểm tra bằng AI chưa thực hiện: …"); các nhóm quy tắc vẫn hiện bình thường. Nút "Check again" ("Kiểm tra lại").
  - `skipped`: dòng nhỏ với `ai.message` ("Quy trình chưa ghi chống chỉ định; …").
  - `disabled`: không hiện gì về AI.
- Bấm mã bước / dòng nguồn lực: chọn và cuộn tới thẻ bước tương ứng (như chọn bước ở cột trái), đặt focus vào thẻ. Bấm tên phần: chọn phần đó.
- Kết quả không lưu (ASM-025-05): sửa quy trình sau khi kiểm thì khung hiện dòng nhỏ "Procedure changed since this check" ("Quy trình đã thay đổi sau lần kiểm này") + nút "Check again".
- Lỗi máy chủ (quyền, không ở Nháp): `frappe.msgprint` như các thao tác khác.

## SCR-DSK-014 Lưới định mức — mở rộng `NormGrid.vue`

### Dòng đề xuất (đã có nền nhấn `nc-ng__row--ai` và nhãn "Suggested" từ FEAT-012)
- Cạnh nhãn `purple` "Suggested" ("Đề xuất"): độ tin cậy "{0}%" (`ai_confidence`), `title`/`aria-label` "Suggestion confidence {0}%" ("Độ tin cậy của đề xuất {0}%").
- Ô nguồn lực hiện `resource_label` của bản ghi đề xuất; ô cấu phần hiện cấu phần đề xuất.
- Hai nút nhỏ trong ô hành động của dòng, chỉ khi `can('accept_link')`: "Accept" ("Chấp nhận") → `accept_link_suggestions(norm_set, [line_id])`; "Remove" ("Bỏ") → `reject_link_suggestion(norm_set, line_id)`. `aria-label` kèm mã dòng. Nút "Xác nhận" của dòng đề xuất không hiện (máy chủ cũng chặn).
- Sửa ô nguồn lực hoặc cấu phần của dòng đề xuất rồi lưu: máy chủ bỏ nhãn (ASM-025-10); lưới vẽ lại theo dữ liệu trả về.

### Dải đề xuất (trên lưới, dưới thanh nút)
- `ai_pending > 0`: `alert-info` "{0} lines have AI link suggestions to review" ("{0} dòng có đề xuất liên kết của AI cần xem") + nút "Accept all" ("Chấp nhận tất cả", `accept_link_suggestions(all=1)`, hỏi xác nhận một lần) + liên kết "Go to first" ("Tới dòng đầu") cuộn tới dòng đề xuất đầu tiên.
- Đang có tác vụ (`link_job` từ `create_norm_set` truyền qua tham số `?link_job=` khi mở lưới, hoặc từ `start_link_suggestion`): `alert-info` `role="status"` "AI is suggesting catalog links…" ("AI đang đề xuất liên kết danh mục…"). Nghe `frappe.realtime.on("normcore_ai_link")` và hỏi `get_link_suggestion_status` mỗi 3 giây làm dự phòng; `done` → nạp lại `get_norm_set`, thông báo `frappe.show_alert` "{0} suggestions added" ("Đã thêm {0} đề xuất"); `failed` → `alert-warning` "AI could not suggest links: {0}. You can link lines manually." ("AI chưa đề xuất được: {0}. Bạn có thể liên kết thủ công.").
- AI tắt: không có dải tác vụ, không có nút "Suggest links"; dải `ai_pending` vẫn hiện nếu bộ còn đề xuất cũ (để xử lý cho hết, FR-AI-008).

### Nút "Suggest links" ("Đề xuất liên kết")
- Thanh nút của lưới, `btn-default btn-sm`, chỉ khi `can('suggest_links')` (bộ "Nháp", quyền ghi, AI bật). Bấm → `start_link_suggestion(norm_set)`; `job_id = None` → `frappe.show_alert` với `message` máy chủ ("Không có dòng nào cần đề xuất").

### Khởi tạo bộ (`norm_create.js`)
- Sau `create_norm_set` thành công: mở lưới như cũ, thêm `link_job` vào tham số đường dẫn khi có. Không đổi hộp chọn hệ thống.

### Chặn xác nhận (UC-009 8a)
- "Confirm professionally" ("Xác nhận chuyên môn") khi còn đề xuất: máy chủ trả danh sách dòng (đã có ở FEAT-012, lý do "Còn đề xuất AI chưa xử lý"); hộp lỗi hiện nguyên văn, mỗi mã dòng là liên kết cuộn tới dòng.

## Kiểm (QA, Playwright trên staging, `vi`, 1366 × 768)
1. Trình soạn quy trình Nháp có bước thiếu nhân lực và nguồn lực lệch chuẩn bị → "Kiểm tra nhất quán" hiện đủ nhóm; bấm mã bước cuộn đúng thẻ.
2. Staging dùng provider `mock`: phần AI hiện "AI không thấy nội dung trái chống chỉ định" (mock trả không có `issues`); AI tắt → không có chữ AI.
3. Lưới bộ có dòng đề xuất (dữ liệu dựng bằng test/console): nhãn "Đề xuất" + độ tin cậy, Chấp nhận / Bỏ / Chấp nhận tất cả hoạt động; "Xác nhận chuyên môn" bị chặn khi còn đề xuất.
4. NC Auditor mở cả hai màn hình: không thấy nút "Kiểm tra nhất quán", "Đề xuất liên kết", "Chấp nhận", "Bỏ".
