# As-Built: FEAT-020 Thư viện văn bản: nạp, tách mục, hiệu lực, tìm kiếm
- Phiên bản app 0.0.1; ngày nghiệm thu: 2026-11-26; người nghiệm thu: QA (Multica, NORM-53)

## 1. Luồng nghiệp vụ đã xây
NC Document Controller tạo NC Legal Document, nhập số hiệu, tên, loại, cơ quan, ngày ban hành/hiệu lực và đính tệp PDF/DOCX (≤ 100 MB) → bản ghi "Chưa lập" (số hiệu trùng sau chuẩn hóa bị từ chối, nêu bản ghi trùng) → tác vụ nền (hàng đợi `long`) tách văn bản và mục, ghi NC Legal Section, "Đang lập" → "Đã lập"; lỗi thì "Lỗi" kèm lý do và Notification Log cho người tải. PDF không có lớp văn bản đi qua bộ OCR cắm được (`tesseract` `vie` + `pdftoppm` nếu có; không có thì "Lỗi" với lý do rõ). Tác vụ hằng ngày cập nhật hiệu lực của văn bản và mục. Tìm kiếm theo từ khóa/cụm từ/số hiệu/mã dịch vụ; form mục hiển thị văn bản đã tách cạnh trang gốc; sửa văn bản thuần lưu bản trước (Version).

## 2. DocType tạo mới hoặc thay đổi
Mới, module NC Library: NC Legal Document, NC Legal Section (chỉ mục FULLTEXT `nc_section_ft` trên heading, plain_text). Không có DocType của FEAT khác bị đổi cấu trúc.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/library.py`: `reindex`, `get_sections`, `get_source_view`, `search_sections`, `index_document` (nền), `daily_job`. Logic thuần `normcore/library/` (`extract.py`, `sections.py`, `search.py`, `validity.py`). Hook: `daily` thêm `normcore.api.library.daily_job`. Lối tắt Workspace, `vi.csv`; `pyproject.toml` thêm `pypdf` (và gói OCR apt khai báo).

## 4. Quyền và luồng trạng thái
Theo `data-model.md` mục 4 (dòng văn bản/mục): NC Document Controller và NC Admin ghi; các vai khác đọc; NC Auditor chỉ đọc. `get_sections`, `get_source_view`, `search_sections` kiểm quyền đọc tường minh. Trạng thái lập chỉ mục: Chưa lập → Đang lập → Đã lập | Lỗi. Hiệu lực: Chưa hiệu lực / Còn hiệu lực / Hết hiệu lực theo ngày.

## 5. Cấu hình cần thiết khi triển khai
`bench migrate`; cài `pypdf`; muốn OCR cần `tesseract-ocr`, `tesseract-ocr-vie`, `poppler-utils` trên máy chủ và worker hàng đợi `long` đang chạy.

## 6. Test case đã chạy và kết quả
TC-LIB-01, 02, 03, 04, 08 và các test `test_FR_LIB_*` (xem `docs/rtm-testref.md`). Site sạch: bench run-tests 968 OK; pytest 483 passed, độ phủ 99%. Chi tiết ở `docs/features/FEAT-020/acceptance.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- Chưa kiểm giao diện bằng trình duyệt (staging chưa có mã của PR); luồng kiểm qua test tích hợp. Chất lượng OCR chưa thử trên văn bản thật (TBD-09).
- Văn bản có thể kẹt ở "Đang lập" nếu worker chết giữa chừng (`api/library.py:128-133`, `:162`); cách gỡ hiện nay là thay tệp. Nên có issue riêng.
- `get_sections` có `page_length` tối đa 500 thay vì 100 như thiết kế (lệch nhỏ, được Lead chấp nhận).
- Vị trí đoạn trích tìm kiếm có thể lệch khi văn bản ở dạng NFD; chỉ ảnh hưởng hiển thị.
- Tên trường ánh xạ dịch vụ dự đoán trước (`api/library.py:302-311`): FEAT-022 phải kiểm lại cho khớp khi thiết kế.
- Chưa có: thay thế văn bản (FEAT-021), ánh xạ dịch vụ (FEAT-022), "Tài liệu của hãng" (FEAT-038).
