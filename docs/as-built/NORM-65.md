# As-Built: NORM-65 NC Procedure Citation đổi sang Link (trả nợ ASM-046)

## 1. Thay đổi
- `NC Procedure Citation.legal_document` → Link NC Legal Document; `legal_section` → Link NC Legal Section (đúng `docs/data-model.md`). Cột CSDL vẫn varchar(140).
- `api/procedure.py`: chọn mục thì văn bản lấy từ mục; mục không thuộc văn bản đã chọn bị từ chối; chỉ văn bản vẫn được. Thêm `list_legal_documents`, `list_legal_sections` (cần quyền đọc thư viện).
- `ProcedureEditor.vue`: hai ô chọn (văn bản, rồi mục của văn bản đó) thay hai ô nhập tự do.

## 2. Patch `normcore.patches.link_procedure_citation_legal` (post_model_sync)
Giá trị cũ khớp được (tên `LD-/LS-…`, số hiệu, mã mục chuẩn hóa) → tên bản ghi. Không khớp → "[Căn cứ cũ: …]" ở đầu `quote`, Link để trống; không mất dữ liệu. Chạy lại không đổi gì thêm. Logic thuần ở `normcore/procedure/citation_link.py`. Chi tiết: `docs/decisions/assumptions/NORM-65.md`.

## 3. Giới hạn
- Không thêm ràng buộc BB cho `legal_section` (ASM-NORM65-01); DI-08 thuộc FEAT-021.
- Dòng không khớp được cần người nhập lại Link theo "[Căn cứ cũ: …]" trong đoạn trích.
