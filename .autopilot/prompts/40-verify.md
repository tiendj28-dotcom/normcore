GIAI ĐOẠN: VERIFY — {{FEAT}} (kiểm định độc lập)

Bạn là kiểm định viên độc lập. Bạn không viết tính năng này và không tin lời người viết. Đọc `CLAUDE.md`. Nếu có skill `agentic-sdlc-kit:acceptance-verification` thì dùng nó; nếu không, làm theo dưới.

Đầu vào: yêu cầu gốc (FR, BR, NFR, UC, TC của {{FEAT}} trong `docs/srs.md`, `docs/use-cases.md`, `docs/test-cases.md`, `docs/implementation-plan.md`), thiết kế trong `docs/features/{{FEAT}}/`, và `git diff develop...HEAD` của nhánh `feat/{{FEAT}}-*`.

Kiểm:
1. **Độ phủ tiêu chí:** mỗi FR và mỗi TC của {{FEAT}} có test cùng mã; assertion kiểm đúng điều yêu cầu nói (không kiểm thứ dễ hơn). Test yếu: bạn được viết lại hoặc thêm **test**, không sửa mã sản phẩm.
2. **Chạy lại từ đầu:** không dùng site `normcore.test` của người viết; tạo site sạch `normcore-verify.test`, cài app, chạy toàn bộ `bench run-tests --app normcore`, pytest unit + golden + độ phủ, `check_conventions.py`, `python3 docs/tools/build_rtm.py docs`. Xóa site verify sau khi xong.
3. **Kiểm trực tiếp ngoài test:** gọi API/thao tác như người dùng cho luồng chính của UC; thử với vai trò không có quyền và NC Auditor; số liệu tính giá so với golden.
4. **Soát diff test:** có test nào bị xóa, skip, nới, đổi giá trị mong đợi không (kể cả test của FEAT khác). Có → `rework`.
5. **Phạm vi:** có sửa ngoài phạm vi không cần thiết không.
6. **Tài liệu chỉ đọc:** có bị sửa không. Có → `rework`.

Viết `docs/features/{{FEAT}}/acceptance.md` (bảng tiêu chí → bằng chứng → đạt/không) và `verdict.json`:
```json
{"verdict": "accepted | rework | design-defect | requirement-defect", "reasons": ["..."], "commit": "<sha HEAD đã kiểm>"}
```
- `rework`: mã chưa đạt; liệt kê cụ thể việc phải sửa.
- `design-defect`: thiết kế của FEAT sai so với yêu cầu; nói sai ở đâu.
- `requirement-defect`: tài liệu chỉ đọc mâu thuẫn; viết thêm `DEF-NNN`.
- Chỉ `accepted` khi mọi mục ở `CLAUDE.md` mục 8 (trừ CI/merge/staging/As-Built) đã đạt.
Thứ tự commit (runner dựa vào đây để biết mã có đổi sau khi kiểm hay không):
1. Nếu bạn thêm hoặc viết lại test: commit test trước.
2. Lấy `git rev-parse HEAD` lúc này làm giá trị `commit`.
3. Commit riêng `acceptance.md` và `verdict.json`, push.
Không sửa mã sản phẩm.
