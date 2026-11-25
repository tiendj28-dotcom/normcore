# As-Built: FEAT-020 Thư viện văn bản: nạp, tách mục, hiệu lực, tìm kiếm
- Phiên bản app 0.0.1; issue NORM-53; nhánh `feat/FEAT-020-thu-vien-van-ban`. Chưa nghiệm thu (QA hoàn thiện ngày, người nghiệm thu, Test ref).

## 1. Luồng nghiệp vụ đã xây
NC Document Controller tạo văn bản (số hiệu, tên, loại, cơ quan, ngày ban hành, ngày hiệu lực, tệp PDF/DOCX riêng tư ≤ 100 MB) → lưu: kiểm trùng số hiệu (không phân biệt hoa thường và khoảng trắng), tính hiệu lực, "Chưa lập" → tác vụ nền (hàng đợi `long`): "Đang lập" → tách văn bản theo trang → tách mục → ghi NC Legal Section → "Đã lập"; lỗi thì "Lỗi" kèm lý do và Notification Log cho người lưu. Hằng ngày tính lại hiệu lực văn bản và mục. Tìm theo từ khóa/cụm từ, số hiệu hoặc mã dịch vụ; mở mục xem cạnh trang gốc PDF; sửa văn bản thuần của mục, bản trước nằm trong Version.

## 2. DocType tạo mới hoặc thay đổi
Mới: **NC Legal Document** (`LD-.#####`), **NC Legal Section** (`LS-.#######`, chỉ mục FULLTEXT `nc_section_ft` trên `heading`, `plain_text` tạo ở `on_doctype_update`). Hai trường HTML chỉ bố cục (`sections_html`, `source_view_html`) không có cột CSDL. Chưa có `supersessions` (FEAT-021), `service_mappings` (FEAT-022), "Tài liệu của hãng" và `related_resources` (FEAT-038): các FEAT đó mở rộng DocType này. Không patch.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/library.py`: `enqueue_index`, `index_document` (nền), `reindex`, `get_sections`, `get_source_view`, `search_sections`, `refresh_validity`, `refresh_section_validity`, `daily_job`. Logic thuần `normcore/library/`: `extract.py`, `sections.py`, `validity.py`, `search.py`. Hook: `scheduler_events["daily"]` thêm `normcore.api.library.daily_job`. Workspace "Normcore" thêm "Văn bản pháp lý", "Mục văn bản". Thêm `pypdf` vào `dependencies`, gói apt tùy chọn `tesseract-ocr`, `tesseract-ocr-vie`, `poppler-utils`. Giao diện: SCR-DSK-002 (danh sách, hộp thoại "Tìm trong nội dung", `Ctrl+Shift+F`), SCR-DSK-003 (form văn bản, danh sách mục, form mục cạnh trang gốc).

## 4. Quyền và luồng trạng thái
Dòng ma trận "Văn bản, mục, ánh xạ": NC Document Controller, NC Admin đọc/ghi/tạo; các vai trò khác và NC Auditor chỉ đọc; không ai xóa. Không phạm vi khoa. `reindex` cần quyền ghi (NC Auditor bị `PermissionError`); `search_sections`, `get_sections`, `get_source_view` cần quyền đọc (người dùng không có vai trò NC bị từ chối). Trạng thái lập chỉ mục: Chưa lập → Đang lập → Đã lập | Lỗi; Lỗi → Chưa lập khi "Lập lại chỉ mục" hoặc đổi tệp. Hiệu lực: Chưa hiệu lực / Còn hiệu lực / Hết hiệu lực (ngày hết hiệu lực vẫn còn hiệu lực, ASM-020-07).

## 5. Cấu hình cần thiết khi triển khai
- **`max_file_size`**: đặt `104857600` trong `site_config.json` (Frappe mặc định 10 MB) để nhận tệp đến 100 MB (NFR-SCAL-002, ASM-020-09).
- **OCR (tùy chọn):** cài `tesseract-ocr`, `tesseract-ocr-vie`, `poppler-utils` trên máy chủ; không có thì PDF không lớp văn bản được đặt "Lỗi" với lý do rõ.
- Worker hàng đợi `long` phải chạy để tác vụ lập chỉ mục chạy; scheduler bật cho tác vụ hằng ngày.
- `bench migrate` (DocType, chỉ mục FULLTEXT, Workspace). MariaDB `innodb_ft_min_token_size` mặc định 3: từ ngắn hơn đi nhánh `LIKE`.

## 6. Test case đã chạy và kết quả
TC-LIB-01 (`api/test_library.py::test_TC_LIB_01_nap_pdf_tach_3_muc`), TC-LIB-02 (`test_nc_legal_document.py::test_TC_LIB_02_trung_so_hieu`), TC-LIB-03 (`test_TC_LIB_03_tep_hong_bao_loi`), TC-LIB-04 (`api/test_library_validity.py`), TC-LIB-08 (`api/test_library_search.py`). Thêm: unit `test_library_sections.py`, `test_library_validity.py`, `test_library_search.py`, `test_library_ui_conventions.py`; site `test_extract.py` (PDF/DOCX/OCR giả). Lệnh và kết quả ở `docs/features/FEAT-020/implementation-log.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- **FR-LIB-004 (OCR) làm một phần (TBD-09, ASM-020-05):** phát hiện PDF không lớp văn bản và gọi bộ nhận dạng cắm được; bộ mặc định `pdftoppm` + `tesseract -l vie` chưa thử với văn bản quét thật và chưa có test chạy tesseract thật (test dùng bộ nhận dạng giả). Chất lượng nhận dạng chưa đo.
- **Luật tách mục (ASM-020-04) chưa thử với văn bản thật:** kế hoạch yêu cầu thử 3 văn bản thật của chuyên khoa thí điểm; luật nằm ở `library/sections.split_sections`, đổi được không sửa test TC. Văn bản "Điều N": dòng thân bài bắt đầu bằng "Điều N" cũng bị coi là tiêu đề.
- DOCX không có số trang: mục không có `page_from`/`page_to`, khung trang gốc thay bằng nút tải tệp (ASM-020-06).
- **Rủi ro cho FEAT-022:** lập lại chỉ mục giữ `name` mục theo `section_no` nhưng **xóa** mục không còn trong tệp mới, kéo theo ánh xạ dịch vụ của mục đó. FEAT-022 cần xử lý (ví dụ cảnh báo trước khi lập lại). `search_sections` chế độ "mã dịch vụ" đã có nhánh đọc `NC Section Service Map` (trường `technical_service`, `mapping_status`) nhưng chưa chạy được trước FEAT-022.
- Tìm kiếm trả tối đa 2.000 ứng viên mỗi truy vấn trước khi lọc cụm từ; chưa đo NFR-PERF-005 với 200.000 mục.
- Frappe từ chối tải PDF hỏng ngay ở bước tải tệp; "tệp hỏng" (TC-LIB-03) xảy ra khi tệp hỏng sau khi tải hoặc tệp thay trên đĩa. Test tạo tình huống bằng cách ghi đè nội dung trên đĩa.
- Chưa chụp màn hình 1366 × 768 (cần staging).
