# FEAT-023 — Thiết kế giao diện

Căn cứ: `ux-foundations.md` SCR-DSK-029 "Cấu hình AI và mẫu lệnh" (loại F — form chuẩn; nội dung: nhà cung cấp, khóa, hạn mức; mẫu lệnh có phiên bản; trạng thái: Kiểm tra kết nối, AI tắt, vượt hạn mức), nhóm "Quản trị" của sơ đồ điều hướng; `design.md` mục 3 (indicator), 4, 5, 6; ADR-010 (form chuẩn khi đủ dùng); API ở `technical-design.md` mục 3.6. Chiến lược code-native: Form/List chuẩn của Desk cộng JS form, **không** viết Desk Page Vue. Mọi chuỗi qua `__()` (JS) / `_()` (Python), bản dịch ở `normcore/translations/vi.csv`.

SCR-DSK-029 hiện thực bằng hai form chuẩn liên kết với nhau: NC AI Settings (Single) và danh sách + form NC Prompt Template. Nhật ký AI (NC AI Log) là SCR-DSK-030, chỉ thêm liên kết từ màn hình này.

## 1. SCR-DSK-029a — Cấu hình AI (Form Single `NC AI Settings`)

**Lối vào**: workspace Normcore, nhóm "Quản trị", liên kết "Cấu hình AI" (`/app/nc-ai-settings`) và "Mẫu lệnh AI" (`/app/nc-prompt-template`). Liên kết chỉ hiện với vai trò có quyền đọc (Desk tự ẩn theo quyền: NC Admin, NC Auditor).

**Bố cục** (một cột trên 768 px, hai cột trên 1366 px — Column Break của Desk):

1. **Dải trạng thái** (`frm.dashboard.set_headline_alert`, đầu form), một trong:
   - AI tắt: indicator `gray` "AI đang tắt" + câu "Các nút gọi AI đang ẩn; mọi nghiệp vụ làm thủ công được."
   - AI bật, chưa vượt: indicator `green` "AI đang bật".
   - Vượt hạn mức (`get_ai_usage().blocked`): indicator `red` "Vượt hạn mức" + "Đã dùng {used} / {budget} token tháng {month}. Lời gọi AI mới bị chặn đến hết tháng hoặc khi tăng hạn mức."
   - Indicator trên tiêu đề form (`frm.page.set_indicator`) dùng cùng chữ và màu.
2. **Section "Nhà cung cấp"**: `enabled` (Bật AI) · `protocol` (Giao thức) · `base_url` (Địa chỉ; mô tả: "OpenAI-compatible: gốc API gồm /v1, ví dụ http://may-chu:8000/v1. Anthropic: để trống dùng địa chỉ mặc định.") · `model` (Mô hình) · `api_key` (Khóa; ô Password của Desk, chỉ hiện dấu `*` sau khi lưu; mô tả: "Khóa lưu mã hóa, không hiển thị lại. Nhập khóa mới để thay.").
   - `base_url` có `mandatory_depends_on: eval:doc.protocol=='OpenAI-compatible'`; `model` có `mandatory_depends_on: eval:doc.enabled`.
3. **Section "Giới hạn"**: `timeout_seconds` (Thời hạn (giây), mô tả "Mặc định 180") · `max_output_tokens` · `monthly_token_budget` (Hạn mức token tháng, mô tả "0 = không giới hạn") · `usage_html` (Đã dùng tháng này): một dòng "Đã dùng 1.200 / 1.000 token — tháng 11/2026" (số định dạng `1.234.567`, NFR-LOC-001), nạp từ `get_ai_usage` khi `refresh`; hạn mức 0 → "Đã dùng 1.200 token — không giới hạn".
4. **Liên kết nhanh** (dưới section Giới hạn, `usage_html` kèm): "Xem nhật ký AI" → `/app/nc-ai-log`; "Mẫu lệnh AI" → `/app/nc-prompt-template`.

**Hành động** (nút trên thanh form, chỉ khi `frappe.model.can_write("NC AI Settings")`, tức NC Admin):
- **"Kiểm tra kết nối"** (nút chính khi form không bẩn). Form có thay đổi chưa lưu → `frappe.msgprint(__("Lưu cấu hình trước khi kiểm tra kết nối."))`, không gọi. Gọi `normcore.api.ai.test_connection` với `freeze: true`, `freeze_message: __("Đang kiểm tra kết nối…")`:
  - `ok` → `frappe.show_alert({message: __("Kết nối thành công ({0} ms)"), indicator: "green"})`.
  - `status = "Quá hạn"` / `"Lỗi"` → `frappe.msgprint({title: __("Kiểm tra kết nối thất bại"), indicator: "red", message: <message trả về, đã che khóa>})`.
- **Bật AI** bằng ô `enabled` rồi Lưu (Ctrl+S): máy chủ tự kiểm tra kết nối (technical-design 3.5). Thất bại → lỗi lưu chuẩn của Desk "Kiểm tra kết nối thất bại: … AI chưa được bật."; ô vẫn tích trên form nhưng chưa lưu (form bẩn), dải trạng thái giữ "AI đang tắt" (UC-017 4c). Thành công → `show_alert` "Đã bật AI", reload boot không bắt buộc (người dùng khác thấy khi tải lại trang).
- **Tắt AI**: bỏ tích `enabled`, Lưu. Hộp xác nhận trước khi lưu (`frm.validate` phía khách khi `enabled` 1→0): "Sau khi tắt, các nút gọi AI bị ẩn với mọi người dùng. Tiếp tục?".
- Phím tắt: Ctrl+S lưu (chuẩn Desk). Không thêm phím tắt riêng.

**Trạng thái**:
- Đang tải: `usage_html` hiện "Đang tải…" đến khi `get_ai_usage` trả về; lỗi gọi → "Không tải được số liệu sử dụng." (chữ `--text-muted`).
- Rỗng (lần đầu, chưa cấu hình): dải "AI đang tắt" + câu "Nhập giao thức, mô hình, khóa rồi bật AI. Chọn "Kiểm tra kết nối" để thử."
- Không có quyền (vai trò khác): Desk trả trang "Không có quyền" chuẩn; liên kết workspace không hiện.
- Chỉ đọc (NC Auditor): mọi ô khóa (Desk theo DocPerm), không nút "Kiểm tra kết nối", không lưu; vẫn thấy dải trạng thái và `usage_html`. Ô Khóa hiện `*****` hoặc trống — không bao giờ giá trị rõ.

## 2. SCR-DSK-029b — Mẫu lệnh AI (List + Form `NC Prompt Template`)

**Danh sách** (`nc_prompt_template_list.js`):
- Cột: Mã mẫu, Phiên bản, Đang dùng; bộ lọc chuẩn Mã mẫu, Đang dùng. Sắp xếp mặc định `template_code` rồi `version` giảm dần.
- Indicator (`get_indicator`): `is_active` → `green` "Đang dùng"; không → `darkgrey` "Ngừng dùng" (design.md [1.1]).
- Nút "Thêm" chuẩn chỉ với NC Admin (DocPerm create). Trống: "Chưa có mẫu lệnh. Mẫu mặc định được cài cùng ứng dụng; tạo mẫu mới bằng nút Thêm."

**Form**:
- Bố cục: `template_code` · `version` (chỉ đọc, tự cấp) · `is_active` | Section "Nội dung": `system_prompt` (Long Text) · `user_prompt` (Long Text, mô tả "Jinja: dùng {{ variables }}, {{ sources }}") · `output_schema` (Code, `options: JSON`).
- Bản mới (chưa lưu): mọi ô sửa được; lưu → tên `{template_code}-v{version}`.
- **Bản đã lưu**: dải "Mẫu lệnh đã tạo không sửa được. Chọn "Tạo phiên bản mới" để sửa." (design.md mục 3 "Bản ghi chỉ đọc"); `template_code`, `system_prompt`, `user_prompt`, `output_schema` đặt `read_only` phía khách (`frm.set_df_property`); máy chủ cũng chặn. Chỉ `is_active` sửa được.
- Nút **"Tạo phiên bản mới"** (NC Admin, bản đã lưu): `frappe.ui.Dialog` tiêu đề "Phiên bản mới của {template_code}", ba trường điền sẵn nội dung bản đang xem: "Lệnh hệ thống" (Long Text, BB), "Lệnh người dùng (Jinja)" (Long Text, BB), "Lược đồ JSON đầu ra" (Code JSON, BB); câu "Bản mới sẽ được dùng ngay; bản v{version} được giữ lại và thôi dùng."; nút chính "Tạo phiên bản". Gọi `normcore.api.ai.new_prompt_version`; thành công → `frappe.set_route("Form", "NC Prompt Template", r.name)` + `show_alert` "Đã tạo phiên bản v{n}". Lỗi (cú pháp Jinja, JSON sai) → hiện trong hộp thoại (`frappe.msgprint` đỏ), hộp thoại giữ nguyên nội dung đã gõ.
- Bật **"Đang dùng"** ở một bản cũ rồi Lưu → xác nhận "Các phiên bản khác của {template_code} sẽ thôi dùng."; sau lưu `show_alert`.
- Liên kết "Xem nhật ký dùng mẫu này" → `/app/nc-ai-log?prompt_template={name}`.

**Trạng thái**: đang tải (chuẩn Desk); không có quyền (chuẩn Desk); NC Auditor chỉ đọc: không nút "Tạo phiên bản mới", không lưu được.

## 3. Cơ chế ẩn nút AI (FR-AI-015) — dùng chung cho FEAT sau

Không có màn hình riêng. `normcore/public/js/normcore_ai.js` (nạp qua `app_include_js`):
- `normcore.ai.enabled()` → `!!frappe.boot.normcore_ai_enabled`.
- Quy ước cho FEAT-024 trở đi: chỉ thêm nút AI khi `normcore.ai.enabled()`; khi tắt, không hiện nút và không hiện thông báo thay thế (luồng thủ công là mặc định). Trang Vue gọi `get_ai_status` khi tải nếu không đọc được boot.
- Lời gọi AI trả `status` "Quá hạn" / "Lỗi" / "Bị chặn hạn mức": nơi gọi hiện `frappe.msgprint` đỏ với `error` của `AIResult`, giữ nguyên dữ liệu trên màn hình (FR-AI-010). Quy ước này ghi để FEAT-024 dùng; FEAT-023 không có nút AI nghiệp vụ (ASM-023-16).

## 4. NC AI Log (SCR-DSK-030, chỉ đổi nhỏ)

Form chuẩn hiện thêm trường "Mẫu lệnh" (`prompt_template`, liên kết tới phiên bản). Indicator danh sách theo `status`: Thành công `green`, Lỗi `red`, Quá hạn `orange`, Bị chặn hạn mức `red` — mọi màu có chữ.

## 5. Kiểm giao diện

- 1366 × 768 và 768 px: form chuẩn Desk; Section dùng Column Break tự xuống một cột. Hộp thoại "Tạo phiên bản mới" dùng `size: "large"`, cuộn bên trong.
- Bàn phím: mọi ô, nút là điều khiển chuẩn Desk (Tab, Enter, Esc đóng hộp thoại, Ctrl+S lưu).
- Tương phản 4,5:1 (NFR-USE-004): chỉ dùng indicator và biến CSS của Desk; màu luôn đi kèm chữ.
- Chuỗi mới vào `vi.csv` (giữ thứ tự chữ cái, không trùng khóa — `check_conventions.py`).
- NFR-SEC-004: không chỗ nào trên giao diện hiển thị khóa; thông báo lỗi lấy từ máy chủ đã che khóa.
