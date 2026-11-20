GIAI ĐOẠN: DESIGN — {{FEAT}}

Đọc `CLAUDE.md`. Nếu có skill `agentic-sdlc-kit:detailed-design` thì dùng nó; nếu không, làm theo dưới.

Đầu vào:
- Dòng {{FEAT}} ở `docs/implementation-plan.md` mục 3 (FR, UC, màn hình, khối, DocType) và tiêu chí nghiệm thu nếu có.
- Từng FR, BR, NFR được dẫn trong `docs/srs.md`; use case trong `docs/use-cases.md`; DocType trong `docs/data-model.md`; ADR trong `docs/architecture.md`; test case có mã khớp trong `docs/test-cases.md`.
- Mã nguồn hiện có (các FEAT đã DONE): hợp đồng API, DocType, hàm đã có. Đọc `docs/as-built/*.md` trước để không tạo trùng.
{{DEFECT_CONTEXT}}

Đầu ra trong `docs/features/{{FEAT}}/`:

1. `technical-design.md`:
   - Phạm vi: liệt kê FR được làm; FR nào chỉ "một phần" thì nói phần nào.
   - DocType mới/đổi: trường, kiểu, bắt buộc, quyền, luồng trạng thái, DI áp dụng. Chỉ dùng DocType có trong `data-model.md`; cần DocType mới thì viết AMD theo `CLAUDE.md` mục 7 trước.
   - API whitelisted: tên hàm, tham số, kết quả, mã lỗi, kiểm quyền.
   - Logic thuần: module, hàm, ánh xạ tới BR và tới hàm golden tương ứng.
   - Bảng tiêu chí nghiệm thu: mỗi dòng = một điều kiện kiểm được + mã TC + mã FR.
   - Giả định áp dụng (ASM) và rủi ro.
2. `tasks.md`: các task có thứ tự, mỗi task nhỏ (một commit), định dạng
   `- [ ] T01 <việc> — done-when: <lệnh kiểm cụ thể và kết quả mong đợi>`.
   Task cuối luôn là: `- [ ] Txx Kiểm toàn bộ — done-when: pytest, bench run-tests --app normcore, check_conventions.py, golden đều xanh`.

Không viết mã sản phẩm ở giai đoạn này. Commit tài liệu lên nhánh `feat/{{FEAT}}-<slug>` (tạo từ `develop` mới nhất nếu chưa có).
