GIAI ĐOẠN: IMPLEMENT — {{FEAT}} (lần {{ATTEMPT}})

Đọc `CLAUDE.md`, `docs/features/{{FEAT}}/technical-design.md`, `ui-design.md`, `tasks.md`, `implementation-log.md` (nếu có). Nếu có skill `agentic-sdlc-kit:feature-implementation` thì dùng nó; nếu không, làm theo dưới.
{{REWORK_CONTEXT}}

Làm trên nhánh `feat/{{FEAT}}-*`, rebase lên `develop` mới nhất trước khi bắt đầu.

Với từng task chưa đánh dấu, theo thứ tự:
1. Viết test trước (tên test mang mã TC nếu task gắn TC), chạy để thấy đỏ.
2. Viết mã cho đạt. Đổi DocType thì `bench --site normcore.test migrate`.
3. Chạy đúng lệnh trong "done-when". Đạt thì đánh dấu `[x]`, thêm một dòng vào `implementation-log.md` (task, lệnh, kết quả, sha), commit.
4. Đỏ: sửa, tối đa 3 lần cho một task. Lần thứ 3 vẫn đỏ: xử lý theo `CLAUDE.md` mục 7 (về commit xanh, tạo `BLOCKED`, dừng).

Thực tế khác thiết kế: sửa thiết kế qua AMD (mục 7) rồi làm tiếp; không âm thầm làm khác thiết kế.

Kết thúc khi mọi task đã `[x]`, kể cả task "Kiểm toàn bộ". Push nhánh. Không tự viết `verdict.json`, không tự tạo `DONE`.
