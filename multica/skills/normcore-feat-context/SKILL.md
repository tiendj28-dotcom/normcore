---
name: normcore-feat-context
description: Lấy đúng ngữ cảnh của một FEAT normcore (FR, BR, TC, UC, màn hình, DocType, DI, ma trận quyền, đối chiếu golden, phụ thuộc) trong một tệp gọn, thay vì đọc cả srs.md, data-model.md, test-cases.md. Dùng ở đầu mọi giai đoạn của một FEAT.
---

# Normcore — Ngữ cảnh một FEAT

## Khi nào dùng
Đầu mọi run trên issue `FEAT-NNN ...` (design, ui, implement, verify, integrate), trước khi đọc tài liệu trong `docs/`.

## Các bước
1. Sinh tệp ngữ cảnh:
   ```
   python3 scripts/feat_context.py FEAT-NNN -o "$TMPDIR/FEAT-NNN-context.md"
   ```
2. Đọc tệp đó trước. Tệp gồm:
   - phụ thuộc và trạng thái DONE của từng FEAT phụ thuộc, kèm đường dẫn As-Built;
   - dòng FEAT trong `implementation-plan.md` mục 3 và các chỗ khác nhắc tới FEAT;
   - mọi FR của FEAT (đã mở rộng dạng `FR-PROC-001..007`), BR và NFR mà FR dẫn tới;
   - dòng trong `docs/golden/*.py` ứng với các BR-COST/ADJ/CLS liên quan;
   - use case đầy đủ, test case gắn FEAT hoặc FR, màn hình SCR-DSK;
   - đặc tả DocType, các DI liên quan, ma trận quyền;
   - các tệp đã có trong `docs/features/FEAT-NNN/`.
3. Chỉ mở tài liệu gốc khi cần chính xác từng chữ, hoặc khi tệp ghi "_không thấy_". Tìm bằng `grep -n "<mã>" docs/<tệp>.md`, không đọc cả tệp.

## Lưu ý
- Tệp ngữ cảnh là bản trích. Khi tệp và `docs/` khác nhau, `docs/` thắng.
- Không commit tệp ngữ cảnh. Nó nằm ở `$TMPDIR` và được sinh lại mỗi run.
- Script chỉ đọc. Nếu script lỗi hoặc thiếu một mục, ghi vào comment của run, rồi tra tài liệu gốc bằng grep.
