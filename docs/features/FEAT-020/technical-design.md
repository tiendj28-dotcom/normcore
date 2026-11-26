# FEAT-020 — Thư viện văn bản: nạp, tách mục, hiệu lực, tìm kiếm — Thiết kế kỹ thuật

Issue NORM-53. Nguồn: `srs.md` FR-LIB-001..006, FR-LIB-010..012, NFR-SCAL-002, NFR-PERF-005; `use-cases.md` UC-001; `data-model.md` mục 3.2 (NC Legal Document, NC Legal Section) và mục 4 (dòng "Văn bản, mục, ánh xạ"); `architecture.md` ADR-006, cấu trúc `library/`; `ux-foundations.md` SCR-DSK-002, SCR-DSK-003; TC-LIB-01, 02, 03, 04, 08. Phụ thuộc FEAT-004 (DONE). Giả định ở `docs/decisions/assumptions/FEAT-020.md` (ASM-020-01..).

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-LIB-001 | DocType NC Legal Document (trường của data-model, trừ phần của FEAT sau — mục 2.3); tệp PDF/DOCX, ≤ 100 MB; lưu xong `index_status` = "Chưa lập" |
| FR-LIB-002 | Kiểm trùng số hiệu sau chuẩn hóa (NFC, bỏ mọi khoảng trắng, không phân biệt hoa thường); lỗi nêu bản ghi trùng |
| FR-LIB-003 | Tác vụ nền (hàng đợi `long`) tách văn bản → tách mục → ghi NC Legal Section; "Đang lập" → "Đã lập" |
| FR-LIB-004 | **Một phần**: phát hiện PDF không có lớp văn bản; gọi bộ nhận dạng ký tự qua giao diện cắm được; bộ mặc định dùng `tesseract` (ngôn ngữ `vie`) + `pdftoppm` nếu có trên máy chủ, không có thì lập chỉ mục "Lỗi" với lý do rõ (TBD-09, ASM-020-05) |
| FR-LIB-005 | Mọi lỗi tách văn bản/tách mục/nhận dạng → "Lỗi", `index_error` tiếng Việt, Notification Log cho người tải lên |
| FR-LIB-006 | Hàm thuần tính hiệu lực; tính khi lưu và tác vụ hằng ngày cho mọi văn bản và mục |
| FR-LIB-010 | API tìm kiếm: từ khóa/cụm từ (FULLTEXT + so khớp cụm), số hiệu, mã dịch vụ; trả số hiệu, số mục, tiêu đề, trang, hiệu lực, đoạn trích |
| FR-LIB-011 | Form NC Legal Section: văn bản đã tách bên cạnh trang gốc của tệp PDF (khung xem PDF mở đúng `page_from`) |
| FR-LIB-012 | Sửa `plain_text`/`heading` của mục: bản trước, người sửa, thời điểm lưu bằng `track_changes` (Version của Frappe); xem được trên form |

Không làm: khai báo thay thế, `supersessions`, cờ "Cần rà soát" (FR-LIB-007..009, FEAT-021); `service_mappings` và NC Section Service Map (FR-SVC-005..007, FEAT-022); loại "Tài liệu của hãng" và `related_resources` (FR-LIB-013, FEAT-038); liên kết NC Procedure Citation với văn bản (giữ kiểu Data như hiện tại).

## 2. DocType (mô-đun NC Library)

Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1. Mã đặt trong `normcore/nc_library/doctype/`.

### 2.1 Mới — NC Legal Document
Naming `LD-.#####`. `title_field` = `title`, `search_fields` = `doc_number,title`, `show_title_field_in_link` = 1.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| doc_number | Số hiệu | Data | Có | `in_list_view`, `in_standard_filter`; duy nhất sau chuẩn hóa (2.4) |
| title | Tên văn bản | Data | Có | `in_list_view` |
| doc_type | Loại | Select | Có | `Luật` / `Nghị định` / `Thông tư` / `Quyết định` / `Công văn` / `Tài liệu nội bộ` (FEAT-038 thêm "Tài liệu của hãng", ASM-020-02); `in_standard_filter` |
| issuer | Cơ quan ban hành | Data | Có | |
| issue_date | Ngày ban hành | Date | Có | |
| effective_date | Ngày hiệu lực | Date | Có | |
| expiry_date | Ngày hết hiệu lực | Date | | ≥ `effective_date`. Nhập tay được ở FEAT này; FEAT-021 đặt tự động khi bị thay thế |
| validity_status | Hiệu lực | Select, `read_only`, `no_copy` | | `Chưa hiệu lực` / `Còn hiệu lực` / `Hết hiệu lực`; `in_list_view`, `in_standard_filter` |
| is_procedure_guideline | Là hướng dẫn QTKT | Check | | Quyết định luật tách mục (mục 3.2) |
| file | Tệp | Attach | Có | Private; đuôi `.pdf`/`.docx`; ≤ 100 MB |
| index_status | Lập chỉ mục | Select, `read_only`, `no_copy` | | `Chưa lập` / `Đang lập` / `Đã lập` / `Lỗi`; `in_list_view`, `in_standard_filter` |
| index_error | Lỗi lập chỉ mục | Small Text, `read_only`, `no_copy` | | Hiện khi `index_status` = Lỗi |
| sections_html | Các mục | HTML | | Chỉ bố cục, không có cột CSDL; JS vẽ danh sách mục (ui-design) |

`links` (Connections): NC Legal Section theo `legal_document`, nhóm "Mục".

### 2.2 Mới — NC Legal Section
Naming `LS-.#######`. `title_field` = `heading`.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| legal_document | Văn bản | Link NC Legal Document | Có | `read_only` trên form; `in_list_view`, `in_standard_filter`, `search_index` |
| section_no | Số mục | Data | Có | `read_only`; duy nhất trong một văn bản; giữ khi lập lại chỉ mục (3.4) |
| heading | Tiêu đề | Data | | Sửa được (FR-LIB-012) |
| page_from | Trang từ | Int | | `read_only`; trống với DOCX |
| page_to | Trang đến | Int | | `read_only` |
| plain_text | Văn bản thuần | Long Text | Có | Sửa được (FR-LIB-012). Chỉ mục FULLTEXT (2.5) |
| expiry_date | Ngày hết hiệu lực | Date | | Riêng của mục (FEAT-021 đặt khi thay thế một phần); nhập tay được |
| validity_status | Hiệu lực | Select, `read_only`, `no_copy` | | Như văn bản; tính theo 3.3 |
| source_view_html | Trang gốc | HTML | | Chỉ bố cục; khung xem trang gốc (FR-LIB-011) |

Không có `service_mappings` ở FEAT này (FEAT-022 thêm).

### 2.3 Trường của data-model để FEAT sau
`supersessions` (FEAT-021), `related_resources` + lựa chọn "Tài liệu của hãng" (FEAT-038), `service_mappings` (FEAT-022). Các FEAT đó **mở rộng** DocType này, không tạo lại (ASM-020-02). Hai trường HTML `sections_html`, `source_view_html` không phải dữ liệu, không cần AMD (tiền lệ `chain_status_html` của NC Technical Service).

### 2.4 Kiểm tra khi lưu (`validate`, controller gọi hàm thuần)

| Điều kiện | Kết quả |
| :-- | :-- |
| `normalize_doc_number(doc_number)` trùng văn bản khác | `DuplicateDocNumberError` (lớp con `frappe.ValidationError`): "Số hiệu {0} trùng với văn bản {1} ({2})" — {1} là liên kết tới bản ghi trùng (TC-LIB-02). So với mọi bản ghi (≤ 2.000, NFR-SCAL-002) bằng một truy vấn `name, doc_number`, chuẩn hóa ở Python (ASM-020-03) |
| `expiry_date` < `effective_date` | "Ngày hết hiệu lực phải từ ngày hiệu lực trở đi" |
| `file` không phải `/private/files/…` | "Tệp văn bản phải là tệp riêng tư" |
| đuôi tệp không là `.pdf`/`.docx` | "Chỉ nhận tệp PDF hoặc DOCX" |
| `File.file_size` > 100 MB | "Tệp vượt 100 MB" (NFR-SCAL-002; ASM-020-09) |
| luôn | `validity_status` = `compute_validity(effective_date, expiry_date, hôm nay)` |
| bản ghi mới, hoặc `file` / `is_procedure_guideline` đổi | `index_status` = "Chưa lập", `index_error` = trống; sau commit xếp tác vụ lập chỉ mục (4) |

`on_update`: nếu `effective_date`/`expiry_date` đổi → tính lại `validity_status` các mục (3.3). NC Legal Section `validate`: (`legal_document`, `section_no`) không trùng; `plain_text` không rỗng; `validity_status` theo 3.3.

Không ai xóa được NC Legal Document, NC Legal Section qua quyền (không thuộc `DELETE_ALLOWED`, Q2 NORM-12). Mục cũ bị gỡ khi lập lại chỉ mục do máy chủ làm (`ignore_permissions`).

### 2.5 Chỉ mục FULLTEXT (ADR-006)
`on_doctype_update()` trong `nc_legal_section.py`: nếu chưa có thì `ALTER TABLE \`tabNC Legal Section\` ADD FULLTEXT INDEX nc_section_ft (heading, plain_text)`; idempotent (kiểm `SHOW INDEX`). Chạy khi `bench migrate`.

### 2.6 Quyền (data-model mục 4, dòng "Văn bản, mục, ánh xạ": `R R R R R W R R W R`)
- Cả hai DocType: NC Document Controller, NC Admin: read, write, create (không delete); Clinician, Dept Head, Council, Finance, Resource Manager, Director, Consultant, Auditor: chỉ read. Không phạm vi khoa.
- `scripts/check_conventions.py`: thêm dòng `MATRIX["Văn bản, mục, ánh xạ"] = "R R R R R W R R W R"` và `DOCTYPE_ROW` cho hai DocType. Không thêm `DELETE_ALLOWED`.
- `normcore/tests/test_permissions.py` lấy danh sách DocType từ data-model và thư mục, không có số cứng: không cần sửa test cũ.

### 2.7 Migration và phụ thuộc
DocType mới, không patch. `pyproject.toml`: thêm `pypdf` vào `dependencies` (đã có trong env do Frappe kéo theo; ghi rõ để không phụ thuộc ngầm); `[deploy.dependencies.apt] packages = ["tesseract-ocr", "tesseract-ocr-vie", "poppler-utils"]` cho nhận dạng ký tự (tùy chọn khi vận hành). `hooks.py`: thêm `"normcore.api.library.daily_job"` vào `scheduler_events["daily"]`.

## 3. Logic thuần — `normcore/library/` (không import `frappe`)

### 3.1 `extract.py` — tách văn bản theo trang

| Hàm | FR | Mô tả |
| :-- | :-- | :-- |
| `class ExtractionError(Exception)` | FR-LIB-005 | Thông điệp tiếng Việt, dùng làm `index_error` |
| `file_kind(filename)` | FR-LIB-001 | `"pdf"` / `"docx"`; khác → `ExtractionError("Chỉ nhận tệp PDF hoặc DOCX")` |
| `extract_pages(content: bytes, filename, ocr=None) -> list[Page]` | FR-LIB-003, 004 | `Page(number: int \| None, text: str)`. PDF: `pypdf.PdfReader` (import trong hàm), mỗi trang một `Page(number=i+1)`. DOCX: `python-docx`, nối đoạn văn và ô bảng theo thứ tự thành một `Page(number=None)` (DOCX không có trang cố định, ASM-020-06). Đọc lỗi (tệp hỏng, mã hóa, rỗng) → `ExtractionError("Không đọc được tệp: <lý do ngắn>")` |
| `needs_ocr(pages)` | FR-LIB-004 | PDF mà tổng ký tự chữ (không tính khoảng trắng) < 20 × số trang (ASM-020-05) |
| (trong `extract_pages`) | FR-LIB-004 | `needs_ocr` đúng: `ocr is None` → `ExtractionError("Tệp PDF không có lớp văn bản và máy chủ chưa có bộ nhận dạng ký tự")`; ngược lại `pages = ocr(content)`; `ocr` ném lỗi hoặc vẫn rỗng → `ExtractionError("Nhận dạng ký tự thất bại: …")` |
| `tesseract_ocr(content) -> list[Page]` | FR-LIB-004 | Bộ mặc định: `pdftoppm -r 300` ra ảnh từng trang rồi `tesseract <ảnh> - -l vie`, qua `subprocess` với thời hạn. `available_ocr()` trả `tesseract_ocr` khi `shutil.which("tesseract")` và `shutil.which("pdftoppm")` có, ngược lại `None` |

`pypdf`, `docx` import bên trong hàm để `sections.py`, `validity.py`, `search.py` chạy pytest không cần gói nào ngoài chuẩn. Test của `extract.py` chạy trên site (bench có `pypdf`, `python-docx`), vì bước unit của CI chỉ cài `pytest pytest-cov openpyxl` và BA/Dev không sửa `.github/` (ASM-020-10).

### 3.2 `sections.py` — tách mục

`split_sections(pages, is_procedure_guideline) -> list[Section]`, `Section(section_no, heading, page_from, page_to, plain_text)`. Duyệt từng dòng (giữ số trang của dòng), nhận dòng tiêu đề cấp 1:

| Loại văn bản | Dòng tiêu đề cấp 1 | `section_no` | `heading` |
| :-- | :-- | :-- | :-- |
| `is_procedure_guideline` | `^\s*(\d{1,4})\s*[.)]\s+(.+)$` và phần chữ của (2) có ≥ 80% chữ in hoa, dài ≥ 3 ký tự (mẫu "12. ĐO ĐIỆN TIM"; các dòng "I. ĐẠI CƯƠNG", "1. Bác sĩ" không phải tiêu đề cấp 1) | số, ví dụ `"12"` | (2) đã gọn khoảng trắng |
| không phải hướng dẫn | `^\s*Điều\s+(\d+[a-zđ]?)\s*[.:]?\s*(.*)$` | `"Điều 5"` | (2), trống thì `"Điều 5"` |

- Mỗi mục: `plain_text` = các dòng từ tiêu đề đến trước tiêu đề kế tiếp (gồm dòng tiêu đề), `page_from` = trang của dòng tiêu đề, `page_to` = trang của dòng cuối không rỗng.
- Phần trước tiêu đề đầu tiên, nếu có chữ: mục `section_no` = `"0"`, `heading` = `"Phần mở đầu"` (ASM-020-04).
- Không nhận được tiêu đề nào: mỗi trang có chữ là một mục `section_no` = `"Trang N"`, `heading` = `"Trang N"`; DOCX không trang → một mục `"1"`, `heading` = dòng đầu (ASM-020-04).
- `section_no` lặp trong cùng văn bản (đánh số lại từ đầu ở phụ lục): lần thứ k thêm hậu tố `"-k"` (`"3-2"`).
- Không có chữ nào sau khi tách → `ExtractionError("Không tách được mục nào từ tệp")`.
- `heading` cắt còn 140 ký tự (giới hạn Data).

### 3.3 `validity.py` — hiệu lực (FR-LIB-006)

| Hàm | Mô tả |
| :-- | :-- |
| `compute_validity(effective_date, expiry_date, today)` | `today < effective_date` → `Chưa hiệu lực`; `expiry_date` có và `today > expiry_date` → `Hết hiệu lực`; còn lại `Còn hiệu lực`. Ngày hết hiệu lực vẫn còn hiệu lực (khớp FR-LIB-007 "ngày liền trước", ASM-020-07) |
| `compute_section_validity(doc_status, section_expiry_date, today)` | `doc_status` khác `Còn hiệu lực` → bằng `doc_status`; `section_expiry_date` có và `today > section_expiry_date` → `Hết hiệu lực`; còn lại `Còn hiệu lực` |
| `changed(rows, today)` | Nhận dòng `(name, effective/expiry hoặc doc_status/expiry, status_hiện_tại)`, trả các dòng cần đổi và trạng thái mới — để tác vụ ngày chỉ ghi dòng đổi |

### 3.4 `search.py` — tìm kiếm (FR-LIB-010, ADR-006)

| Hàm | Mô tả |
| :-- | :-- |
| `normalize_doc_number(s)` | `unicodedata.normalize("NFC")`, bỏ mọi khoảng trắng, `casefold()`. `"123/qđ-byt"` ≡ `"123/QĐ-BYT"` ≡ `"123 / QĐ-BYT"` (FR-LIB-002) |
| `normalize_text(s)` | NFC, gọn khoảng trắng, `casefold()` — để so cụm từ và dựng đoạn trích |
| `tokenize(q)` | Tách từ theo khoảng trắng/dấu câu, bỏ ký tự đặc biệt của boolean mode (`+-<>()~*"@`) |
| `build_fulltext_query(q, min_token=3)` | Chuỗi BOOLEAN MODE `+tu1 +tu2 …` chỉ gồm từ dài ≥ `min_token`; không còn từ nào → `None` (khi đó API so `LIKE` thuần) |
| `matches_phrase(text, q)` | `normalize_text(q)` nằm trong `normalize_text(text)` |
| `make_snippet(text, q, width=200)` | Đoạn quanh chỗ khớp đầu tiên, thêm `…` hai đầu; không khớp → đầu văn bản |
| `section_matches_service(heading, service_name)` | `normalize_text(service_name)` nằm trong `normalize_text(heading)` (dùng cho tìm theo mã dịch vụ, ASM-020-08) |
| `rank(results)` | Sắp: hiệu lực (`Còn` → `Chưa` → `Hết`), số hiệu văn bản, thứ tự số mục tự nhiên (`2` < `10`) |

Không có phép tính tiền; không đối chiếu golden. Unit test thuần: `normcore/tests/unit/test_library_sections.py`, `test_library_validity.py`, `test_library_search.py` (độ phủ mục tiêu ≥ 90% cho ba tệp, không bắt buộc bởi CI).

## 4. API và tác vụ — `normcore/api/library.py`

| Hàm | Loại | Tham số → kết quả | Quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `enqueue_index(name, user)` | nội bộ | Gọi từ controller sau `validate` đặt "Chưa lập": `frappe.enqueue("normcore.api.library.index_document", queue="long", timeout=1800, enqueue_after_commit=True, name=name, notify_user=user)` | — |
| `index_document(name, notify_user=None)` | tác vụ nền | Đặt "Đang lập" (commit) → đọc nội dung tệp (`File.get_content()`) → `extract_pages(..., ocr=available_ocr())` → `split_sections` → ghi mục (3.4 dưới) → "Đã lập". Mọi `ExtractionError`/ngoại lệ: rollback phần mục, "Lỗi", `index_error` = thông điệp (ngoại lệ lạ: "Lỗi hệ thống khi lập chỉ mục", ghi `frappe.log_error`), Notification Log (type `Alert`) cho `notify_user` (mặc định `owner`) tiêu đề "Lập chỉ mục văn bản {doc_number} thất bại: {lý do}", liên kết tới văn bản (ASM-020-11) | chạy quyền hệ thống |
| `reindex(legal_document)` | `@frappe.whitelist()` | Đặt "Chưa lập", xóa lỗi, xếp tác vụ; trả `{"index_status": "Chưa lập"}`. Dùng sau khi thay tệp hoặc để chạy lại (UC-001 4b) | `frappe.has_permission("NC Legal Document", "write", doc)` không thì `frappe.PermissionError`; đang "Đang lập" → `ValidationError` "Văn bản đang được lập chỉ mục" |
| `get_sections(legal_document, start=0, page_length=100)` | `@frappe.whitelist()` | `{"total", "rows": [{name, section_no, heading, page_from, page_to, validity_status}]}` sắp theo thứ tự tự nhiên của `section_no` | read trên văn bản |
| `get_source_view(section)` | `@frappe.whitelist()` | `{"file_url", "file_kind": "pdf"\|"docx", "page_from", "page_to", "doc_number", "section_no"}` cho khung trang gốc | read trên mục |
| `search_sections(query, mode="auto", doc_type=None, validity_status=None, start=0, page_length=20)` | `@frappe.whitelist()` | Xem dưới. Trả `{"mode", "total", "rows": [{section, legal_document, doc_number, doc_title, section_no, heading, page_from, page_to, validity_status, snippet, match}]}` | read trên NC Legal Section, không thì `PermissionError`; `query` rỗng hoặc < 2 ký tự → `ValidationError` "Nhập ít nhất 2 ký tự"; `page_length` ≤ 100 |
| `refresh_validity(today=None)` | nội bộ | Tính lại `validity_status` mọi văn bản rồi mọi mục (bằng `validity.changed`), ghi `frappe.db.set_value(..., update_modified=False)` chỉ dòng đổi; trả `{"documents": n, "sections": m}` | — |
| `daily_job()` | scheduler daily | `refresh_validity()` | — |

**Ghi mục khi lập chỉ mục:** khóa theo (`legal_document`, `section_no`): mục đã có → cập nhật `heading`, trang, `plain_text` (giữ `name`, `expiry_date`, và các bảng con FEAT sau thêm); mục mới → tạo; mục cũ không còn → xóa (`ignore_permissions`). `validity_status` mục theo 3.3. Sửa tay trước đó bị ghi đè nhưng còn trong Version (ASM-020-12).

**`search_sections`** — `mode`:
- `auto`: `query` chuẩn hóa trùng `service_code` của NC Technical Service, hoặc `external_code` trong NC Service Code Map → `service`; trùng `normalize_doc_number` của một văn bản → `doc_number`; còn lại `text`.
- `text`: `WHERE MATCH(heading, plain_text) AGAINST (%s IN BOOLEAN MODE)` với `build_fulltext_query`, rồi giữ dòng `matches_phrase(heading + plain_text, query)`; nếu `build_fulltext_query` trả `None` → `plain_text LIKE %query%` (collation của CSDL không phân biệt hoa thường). `match` = `"Nội dung"`.
- `doc_number`: mọi mục của văn bản đó, `match` = `"Số hiệu"`.
- `service`: (a) nếu bảng `tabNC Section Service Map` tồn tại (sau FEAT-022): mục có ánh xạ `Đã xác nhận` tới dịch vụ, `match` = `"Ánh xạ dịch vụ"`; (b) mục cấp 1 của văn bản hướng dẫn QTKT có `section_matches_service(heading, service_name)`, `match` = `"Tên dịch vụ"`. Hợp hai nhóm, bỏ trùng (ASM-020-08).
- Lọc thêm `doc_type`, `validity_status` (của mục). Sắp bằng `rank`; phân trang sau khi lọc. Mục tiêu NFR-PERF-005 (3 giây, 200.000 mục) nhờ FULLTEXT; nhánh `LIKE` chỉ cho truy vấn toàn từ ngắn.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | Tạo NC Legal Document đủ trường, tệp PDF mẫu có lớp văn bản 3 quy trình (`is_procedure_guideline` = 1): ngay sau `insert` `index_status` = "Chưa lập"; gọi `index_document(name)`: có đúng 3 NC Legal Section, `section_no` "1","2","3", `heading` đúng tên quy trình, `page_from`/`page_to` đúng trang mẫu, `plain_text` chứa câu trong quy trình; văn bản "Đã lập" | TC-LIB-01 | FR-LIB-001, FR-LIB-003 |
| 2 | Có văn bản `123/QĐ-BYT`; tạo `123/qđ-byt` (và `123 / QĐ-BYT`): `DuplicateDocNumberError`, thông điệp chứa `name` bản ghi đã có | TC-LIB-02 | FR-LIB-002 |
| 3 | Tệp "PDF" hỏng: sau `index_document` văn bản "Lỗi", `index_error` không rỗng, có Notification Log cho người tải lên liên kết tới văn bản; không có mục nào | TC-LIB-03 | FR-LIB-005 |
| 4 | Văn bản `effective_date` = mai; `refresh_validity(today=hôm nay)` → "Chưa hiệu lực" (văn bản và mục); `refresh_validity(today=mai)` → "Còn hiệu lực" | TC-LIB-04 | FR-LIB-006 |
| 5 | Sau TC-LIB-01: `search_sections` với một cụm từ trong quy trình 2 trả mục "2" kèm `doc_number`, `section_no`, `page_from`, `validity_status`; với `service_code` của một NC Technical Service có tên trùng tiêu đề quy trình 3 trả mục "3" | TC-LIB-08 | FR-LIB-010 |
| 6 | `split_sections`: hướng dẫn QTKT (tiêu đề in hoa, dòng La Mã không phải mục), văn bản "Điều N", phần mở đầu, không tiêu đề → theo trang, số mục lặp, DOCX một trang; `compute_validity`/`compute_section_validity` ở biên (ngày = hiệu lực, = hết hiệu lực, + 1); `normalize_doc_number`, `build_fulltext_query`, `make_snippet` | (đơn vị) | FR-LIB-002, 003, 006, 010 |
| 7 | PDF không lớp văn bản: `ocr=None` → "Lỗi" với lý do "không có lớp văn bản"; `ocr` giả trả văn bản → tách mục bình thường, "Đã lập" | — | FR-LIB-004, FR-LIB-005 |
| 8 | Tệp DOCX mẫu: lập chỉ mục được, mục không có trang; tệp `.xlsx` hoặc tệp public bị từ chối khi lưu | — | FR-LIB-001, FR-LIB-003 |
| 9 | Lập lại chỉ mục cùng tệp: `name` các mục giữ nguyên; `reindex` bởi NC Auditor → `PermissionError` | — | FR-LIB-003, FR-ACC-007 |
| 10 | NC Document Controller sửa `plain_text` của mục: có Version chứa giá trị cũ, giá trị mới, `owner` = người sửa, `creation` = thời điểm | — | FR-LIB-012 |
| 11 | `get_source_view` trả `file_url`, `page_from` của mục; form mục có khung xem (kiểm quy ước giao diện ở unit) | — | FR-LIB-011 |
| 12 | Quyền: Doc Controller, Admin tạo/sửa được; Clinician, Finance, Auditor chỉ đọc (lưu bị `PermissionError`); người dùng không có vai trò NC nào không đọc được và `search_sections` bị `PermissionError`; không ai xóa được | — | FR-ACC-002, FR-ACC-007 |

Tên test: `test_TC_LIB_01_nap_pdf_tach_3_muc`, `test_TC_LIB_02_trung_so_hieu`, `test_TC_LIB_03_tep_hong_bao_loi`, `test_TC_LIB_04_hieu_luc_theo_ngay`, `test_TC_LIB_08_tim_theo_cum_tu_va_ma_dich_vu`; test khác `test_FR_LIB_0NN_*`.

**Chú ý cho test TC-LIB-08:** InnoDB chỉ đưa dòng vào chỉ mục FULLTEXT khi commit. Test tìm kiếm phải `frappe.db.commit()` sau khi tạo dữ liệu và tự xóa dữ liệu ở `tearDown` (`frappe.db.delete` + commit), không dựa vào rollback của `FrappeTestCase`.

**Tệp mẫu cho test:** `normcore/nc_library/doctype/nc_legal_document/test_files/` — `qtkt_3_quy_trinh.pdf` (4 trang: quy trình 1 trang 1–2, quy trình 2 trang 3, quy trình 3 trang 4; tiêu đề in hoa "1. …", "2. …", "3. …"; có dòng "I. ĐẠI CƯƠNG"… trong mỗi quy trình; không có phần mở đầu), `qtkt_mau.docx`, `khong_lop_van_ban.pdf` (trang trắng, sinh bằng `pypdf.PdfWriter.add_blank_page`), `hong.pdf` (byte `%PDF-1.4` rồi rác). Kèm `make_samples.py` ghi cách sinh (PDF qua `frappe.utils.pdf.get_pdf` từ HTML có ngắt trang, chạy bằng `scripts/with_bench.sh`) để tái tạo; test chỉ đọc tệp đã commit.

## 6. Giả định và rủi ro
Chi tiết ở `docs/decisions/assumptions/FEAT-020.md`:
- **ASM-020-01** Tìm/nạp chạy cho mọi vai trò có R theo ma trận; không phạm vi khoa.
- **ASM-020-02** Chỉ tạo các trường thuộc FR của FEAT-020; FEAT-021/022/038 mở rộng.
- **ASM-020-03** Chuẩn hóa số hiệu: NFC + bỏ khoảng trắng + casefold; kiểm ở `validate`, không thêm cột khóa.
- **ASM-020-04** Luật tách mục (QTKT: số + tiêu đề in hoa; khác: "Điều N"; phần mở đầu "0"; dự phòng theo trang).
- **ASM-020-05** OCR: ngưỡng phát hiện; bộ `tesseract`+`pdftoppm` tùy chọn; không có thì "Lỗi" (TBD-09). FR-LIB-004 làm một phần, ghi As-Built.
- **ASM-020-06** DOCX không có số trang; `page_from`/`page_to` trống, không có khung trang gốc (chỉ nút tải tệp).
- **ASM-020-07** Ngày hết hiệu lực tính là còn hiệu lực trong ngày đó.
- **ASM-020-08** Tìm theo mã dịch vụ trước FEAT-022: khớp tên dịch vụ với tiêu đề mục cấp 1 của văn bản hướng dẫn; sau FEAT-022 cộng ánh xạ đã xác nhận.
- **ASM-020-09** Giới hạn 100 MB kiểm ở controller; vận hành cần đặt `max_file_size` = 104857600 trong `site_config.json` (mặc định Frappe 10 MB).
- **ASM-020-10** Test `extract.py` chạy trên site, không ở bước unit CI.
- **ASM-020-11** Thông báo lỗi bằng Notification Log (tiền lệ ASM-100) cho người lưu/lập lại chỉ mục.
- **ASM-020-12** Lập lại chỉ mục giữ `name` mục theo `section_no`, ghi đè sửa tay (còn trong Version), xóa mục không còn.
- Rủi ro: chất lượng tách mục trên văn bản thật (TBD-09, kế hoạch yêu cầu thử 3 văn bản thật của chuyên khoa thí điểm) — luật tách ở một hàm, đổi được; FULLTEXT với từ tiếng Việt ngắn (`innodb_ft_min_token_size` = 3) — xử lý bằng nhánh `LIKE` và lọc cụm từ; xóa mục khi lập lại chỉ mục sẽ mất ánh xạ của FEAT-022 — FEAT-022 cần xem lại (ghi vào As-Built).
