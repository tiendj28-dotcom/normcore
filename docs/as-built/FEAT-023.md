# As-Built: FEAT-023 Gateway AI: cấu hình, bộ chuyển đổi, nhật ký, hạn mức, chặn nguồn
- Phiên bản app 0.0.1; Dev: NORM-55; nghiệm thu: chờ QA (chưa có `acceptance.md`, `verdict.json`)

## 1. Luồng nghiệp vụ đã xây
NC Admin mở "Cấu hình AI" (`/app/nc-ai-settings`), nhập giao thức (OpenAI-compatible hoặc Anthropic Messages), địa chỉ, mô hình, khóa, thời hạn, hạn mức token tháng; chọn "Kiểm tra kết nối". Bật AI (0→1) tự kiểm tra kết nối, thất bại thì không lưu trạng thái bật (UC-017 4c). Mỗi lời gọi `gateway.complete` đọc cấu hình lúc đó, kiểm hạn mức, lấy mẫu lệnh đang dùng, dựng lệnh, gọi bộ chuyển đổi, kiểm lược đồ đầu ra rồi ghi đúng một NC AI Log (thành công, lỗi, quá hạn, bị chặn hạn mức). Vượt hạn mức: chặn, ghi nhật ký, Notification Log cho từng NC Admin một lần mỗi tháng. Sửa mẫu lệnh = "Tạo phiên bản mới".

## 2. DocType tạo mới hoặc thay đổi
- NC AI Settings (Single, mới): `enabled`, `protocol`, `base_url`, `model`, `api_key` (Password), `timeout_seconds`, `max_output_tokens`, `monthly_token_budget`, `usage_html`. NC Admin đọc/ghi, NC Auditor đọc.
- NC Prompt Template (mới): tên `{template_code}-v{version}`; nội dung bất biến; mỗi mã tối đa một bản đang dùng. 7 bản `*-v1` cài bằng `after_install` và patch `add_default_prompt_templates`.
- NC AI Log: thêm `prompt_template`.

## 3. API, tác vụ nền, hook, fixtures
- `normcore/api/ai.py`: `get_ai_status`, `test_connection`, `get_ai_usage`, `new_prompt_version`, `boot_session` (hook, đặt `frappe.boot.normcore_ai_enabled`). `normcore_ai.js` (`app_include_js`): `normcore.ai.enabled()`, `normcore.ai.toggle()`.
- `ai/guard.py` (danh sách cho phép nguồn gửi AI; mọi DocType kế toán, tính giá, giá bị từ chối), `ai/prompts.py` (Jinja sandbox, kiểm lược đồ), `ai/providers/openai_compat.py`, `http.py`; `gateway.py` mở rộng: `get_settings`, `is_enabled`, `ensure_enabled`, `monthly_usage`, `ping`, `_notify_budget`.
- Giao diện: form NC AI Settings (nút "Kiểm tra kết nối", dòng sử dụng, dải trạng thái), form + danh sách NC Prompt Template, indicator danh sách NC AI Log; hai lối tắt Workspace "Cấu hình AI", "Mẫu lệnh AI".

## 4. Quyền và luồng trạng thái
NC AI Settings, NC Prompt Template: NC Admin đọc/ghi/tạo, NC Auditor đọc, vai trò khác không; không ai xóa. NC AI Log giữ nguyên quyền.

## 5. Cấu hình cần thiết khi triển khai
Nhập cấu hình ở NC AI Settings. Khóa dự phòng khi ô khóa trống: biến môi trường `NORMCORE_AI_API_KEY` hoặc `site_config.normcore_ai_api_key`. `site_config.normcore_ai_provider = "mock"` buộc dùng nhà cung cấp giả lập (smoke). Chạy `bench migrate` để nạp 7 mẫu lệnh mặc định.

## 6. Test case đã chạy và kết quả
TC-AI-05, TC-AI-06, TC-AI-08, TC-AI-09, TC-AI-11, TC-NFR-04 và TC-AI-07 (phần có thể kiểm): xem `implementation-log.md` và `docs/rtm-testref.md` mục FEAT-023. Mọi test dùng nhà cung cấp giả lập hoặc transport giả, không gọi mạng.

## 7. Giới hạn đã biết và nợ kỹ thuật
- ASM-023-01..16 (`docs/decisions/assumptions/FEAT-023.md`). ASM-023-04 sửa theo Quyết định Lead: chặn khi lũy kế **>** hạn mức.
- ASM-023-03: gateway không tự chặn khi AI tắt; API của từng nút AI (FEAT-024 trở đi) phải gọi `gateway.ensure_enabled()`.
- TC-AI-07: phần "giá tham chiếu bằng tay" chưa kiểm được vì NC Benchmark Price chưa có trên develop (ASM-023-16).
- TC-AI-08 dùng một lời gọi gateway bằng nhà cung cấp giả lập, không chờ TC-AI-01 (ASM-023-13).
- Thời hạn HTTP là thời hạn đọc từng lần của `requests`, không phải tổng thời gian.
- Hai lời gọi song song sát hạn mức có thể cùng qua (vượt tối đa một lời gọi).
