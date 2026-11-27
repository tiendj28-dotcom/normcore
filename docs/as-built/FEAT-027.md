# As-Built: FEAT-027 Trích bảng giá PDF bằng AI
- Phiên bản app 0.0.1; Dev: NORM-82; nghiệm thu: QA (Multica), `docs/features/FEAT-027/acceptance.md`

## 1. Luồng nghiệp vụ đã xây
- **FR-BM-003 (UC-013 2a).** Trên form NC Benchmark Facility, nút "Trích bảng giá PDF (AI)" mở hộp thoại: tệp PDF, loại giá, số văn bản nguồn, ngày hiệu lực mặc định. Máy chủ tách chữ theo trang (`library/extract.py`), gọi gateway với mẫu lệnh `EXTRACT_PRICE_LIST-v2` (tác vụ nền `queue="long"`), rồi mỗi dòng hợp lệ thành một NC Benchmark Price có `ai_log`, `status = "Đề xuất"` (luật `before_insert` của FEAT-026, ASM-026-02). `source_url = tệp#page=N` để mở đúng trang gốc khi rà soát.
- **FR-BM-004, 005, 007.** Dùng lại mã FEAT-026: đề xuất dịch vụ khớp bằng quy tắc (không dùng AI, ASM-027-09), dòng "Đề xuất" không vào `get_comparable_prices`, dòng trùng bị từ chối và được báo (các dòng khác vẫn tạo, ASM-027-08).
- **FR-AI-010, UC-013 2c.** AI lỗi, quá hạn, bị chặn hạn mức hoặc trả JSON thiếu `rows`: không tạo dòng nào, báo lỗi kèm gợi ý nhập tay hoặc Excel; giao diện có hai nút "Nhập tay", "Nhập từ Excel".
- **FR-AI-011.** Chỉ gửi chữ của tệp (`guard.price_list_pages`, nhận đối tượng `Page`, từ chối dict/bản ghi) và hai biến `facility_name`, `file_name`. `FORBIDDEN_DOCTYPES` không đổi; không gửi bản ghi giá đã lưu.
- **FR-AI-015.** Nút chỉ hiện khi `normcore.ai.enabled()`; máy chủ `gateway.ensure_enabled()`. AI tắt: nhập tay và Excel của FEAT-026 vẫn chạy.
- Bỏ dòng: thiếu tên, giá không hợp lệ, thiếu ngày (không có ngày mặc định), tên không thấy trong chữ của tệp (đếm vào `rejected_citations` của NC AI Log; đổi bằng `pdf_extract.REQUIRE_NAME_IN_SOURCE`). Tối đa 30 trang mỗi tệp (`MAX_PAGES`).

## 2. DocType
Không DocType mới, không đổi trường, không patch. NC Benchmark Price (FEAT-026) dùng nguyên các trường `ai_log`, `source_file`, `source_url`.

## 3. API, hook
- `api/benchmark_ai.py`: `start_price_list_extraction`, `get_price_list_extraction_status` (whitelist), `run_price_list_extraction` (tác vụ nền). Trạng thái ở cache 3600 s + realtime `normcore_price_list_ai`.
- `benchmark/pdf_extract.py` (thuần), `ai/guard.py::price_list_pages`, `ai/prompts_install.py::ensure_extract_price_list_v2` (cài lười, không ghi đè bản Admin đã sửa).
- Giao diện: `public/js/benchmark_pdf_ai.js` qua `hook_registry/FEAT-027.json`; bản dịch `translations/vi.d/FEAT-027.csv`. Không sửa JS và bản dịch của FEAT-026.
- Tệp mẫu test: `nc_benchmark/doctype/nc_benchmark_price/test_files/bang_gia_4_dong.pdf` (sinh bằng `make_samples.run`).

## 4. Quyền
Tạo giá tham chiếu (data-model mục 4): NC Finance, NC Consultant. NC Clinician, NC Auditor, vai khác: `PermissionError`, không NC AI Log. Trạng thái tác vụ chỉ người khởi chạy (hoặc Administrator) đọc được.

## 5. Cấu hình cần thiết khi triển khai
AI bật và đã có khóa API (FEAT-023). Bộ nhận dạng ký tự (tesseract, pdftoppm) nếu muốn nhận tệp PDF quét ảnh.

## 6. Test case đã chạy và kết quả
TC-BM-05: xanh. Phần giá tham chiếu của TC-AI-07 (ASM-023-16): `test_FR_AI_015_tat_ai_gia_tham_chieu_thu_cong` xanh (ASM-027-12). Xem `docs/rtm-testref/FEAT-027.md`, `implementation-log.md`. Không gọi AI thật (provider giả lập).

## 7. Giới hạn đã biết
- ASM-027-01..12 (`docs/decisions/assumptions/FEAT-027.md`).
- PDF dạng bảng: `pypdf` có thể tách tên và giá thành các dòng rời; AI vẫn đọc được nhưng tên đứt dòng có thể bị loại "Không thấy trong tệp".
- Giao diện SCR-DSK-025 chưa kiểm bằng trình duyệt (không có tài khoản vai trò thường); phủ bằng test_feat_027_ui.py và test quyền API.
- Tệp mẫu test dùng wkhtmltopdf nên có lớp văn bản chuẩn; PDF thực tế có thể khác.
