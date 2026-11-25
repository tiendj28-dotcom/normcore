# As-Built: FEAT-007 Phê duyệt ba cấp, ban hành, in
- Phiên bản app 0.0.1; Dev: NORM-34; nghiệm thu: chờ QA (chưa có `acceptance.md`, `verdict.json`)

## 1. Luồng nghiệp vụ đã xây
Nháp → (Gửi duyệt, NC Clinician có quyền ghi quy trình) Chờ trưởng khoa duyệt → (Đồng ý, trưởng khoa cùng khoa) Chờ hội đồng thẩm định → (Thông qua, thư ký hội đồng) Chờ ban hành → (Ban hành, NC Director, bắt buộc số quyết định và ngày hiệu lực) Đã ban hành. "Từ chối" ở ba cấp chờ về Nháp, bắt buộc lý do, thông báo người soạn, lý do ghi vào sổ sự kiện (`NC Audit Event.detail`) và Comment "Workflow"; ý kiến thẩm định được giữ. Gửi duyệt kiểm FR-PROC-008, FR-PROC-012 và không còn đề xuất AI chưa xử lý, liệt kê hết lỗi một lần, giữ Nháp. Tác vụ ngày chuyển bản "Đã ban hành" cũ sang "Đã thay thế" khi bản mới đến ngày hiệu lực, và nhắc người duyệt khi chờ quá `approval_reminder_days` (mặc định 7). In PDF và xuất DOCX cùng nội dung; bản chưa ban hành có chữ "DỰ THẢO". Khác SRS/thiết kế: thư ký hội đồng là trường `NC Settings.council_secretary` (AMD-007-01); nội dung bị khóa ở cả ba trạng thái chờ (ASM-007-03, Lead đã duyệt).

## 2. DocType tạo mới hoặc thay đổi
- NC Review Comment (mới, module NC Core): `ref_doctype`, `ref_name`, `target_section`, `target_step_id`, `comment`, `resolved`, `review_state`. Chỉ `resolved` đổi được sau khi tạo; chỉ tạo khi quy trình đang chờ duyệt.
- NC Settings: thêm `approval_reminder_days` (mặc định 7), `council_secretary` (Link User, kiểm vai trò NC Council Member).
- NC Clinical Procedure: không thêm trường; controller khóa nội dung ngoài Nháp, chặn đổi trạng thái ngoài luồng duyệt, `on_trash` chỉ cho Nháp, `publish()` là lớp mỏng gọi `apply_action`; đặt `default_print_format`. Bỏ `flags.allow_publish`.
- Không cần patch dữ liệu (chỉ thêm trường, fixtures).

## 3. API, tác vụ nền, hook, fixtures
- `normcore/api/procedure_workflow.py`: `get_review`, `apply_action`, `add_review_comment`, `set_comment_resolved`, `download_pdf`, `download_docx`, `get_print_context` (Jinja), `supersede_due`, `send_approval_reminders`, `daily_job`.
- Logic thuần: `procedure/validation.py`, `procedure/approval.py`, `procedure/printing.py`, `exports/procedure_docx.py`.
- Hooks: `scheduler_events["daily"]` thêm `normcore.api.procedure_workflow.daily_job`; `jinja.methods`; `fixtures` thêm Workflow State (7), Workflow Action Master (5), Workflow `NC Clinical Procedure`.
- Print Format `NC Clinical Procedure Standard` (chuẩn của module NC Procedure, mẫu mặc định TBD-04). Thông báo là Notification Log (ASM-007-01).
- `core/audit.py::_log_state` ghi `flags.audit_detail` vào `detail`.
- Giao diện: chế độ thẩm định SCR-DSK-010 trong `procedure-editor` (thanh duyệt, tóm tắt khác biệt, ý kiến theo bước và phần), form Desk (chặn `before_workflow_action`, nút In PDF, Tải DOCX), chỉ báo danh sách 7 trạng thái, `vi.csv`.

## 4. Quyền và luồng trạng thái
NC Review Comment theo ma trận mục 4: Dept Head, Council, Director đọc/sửa/tạo; Clinician, Finance, Document Controller, Consultant, Admin, Auditor chỉ đọc; Resource Manager không có quyền. `apply_action` kiểm vai trò và phạm vi khoa trong mã (Council, Director chỉ có R trên DocType quy trình); NC Auditor và NC Finance bị `PermissionError`. Auditor tải PDF/DOCX bằng quyền đọc (ASM-007-09). Luồng ở `approval.TRANSITIONS`, khớp fixture Workflow (có test).

## 5. Cấu hình cần thiết khi triển khai
- `bench migrate` và `bench build --app normcore`.
- Cài `python-docx` (khai trong `pyproject.toml`): `bench pip install python-docx` hoặc `bench setup requirements`. Thiếu thư viện chỉ hỏng DOCX.
- Đặt "Thư ký hội đồng" ở Cài đặt Normcore (NC Settings); chưa đặt thì "Thông qua" bị từ chối với thông báo rõ.
- Cần `wkhtmltopdf` trên máy chủ cho PDF.
- Mỗi khoa cần `head_user` để trưởng khoa nhận thông báo gửi duyệt.

## 6. Test case đã chạy và kết quả
TC-PROC-05, 06, 07; TC-WF-01 (luồng 4 trạng thái, thông báo, ca âm), 02 (ba cấp), 03 (năm trạng thái, form và API), 04 (qua luồng thật và `supersede_due(today)`), 08; FR-WF-013; quyền NC Review Comment (Resource Manager, Auditor, Clinician); fixture Workflow khớp `TRANSITIONS`. Kết quả lệnh ở `docs/features/FEAT-007/implementation-log.md` và bình luận NORM-34. TC-PROC-07 loại M: QA mở PDF kiểm bằng mắt.

## 7. Giới hạn đã biết và nợ kỹ thuật
- PDF dựng từ HTML tự chứa (ASM-007-18); chữ chìm "DỰ THẢO" xoay chéo phụ thuộc bản `wkhtmltopdf`.
- Test cũ dựng quy trình "Đã ban hành" bằng helper `publish_procedure`/`to_state` trong `tests/utils.py` (ASM-007-16, Lead đã quyết).
- Giữ nút "Publish" ở form vì test cũ (ASM-007-17).
- Chưa làm: "Thu hồi", phiên bản sửa đổi, so sánh phiên bản (FEAT-008); sinh định mức (FEAT-012; để sẵn `approval.effective_procedure`); email thông báo, `core/notify.py` (FEAT-002).
- Giao diện chưa kiểm bằng mắt trên trình duyệt trong lượt Dev; QA kiểm bằng Playwright.
