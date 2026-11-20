GIAI ĐOẠN: BOOTSTRAP (walking skeleton, FEAT-000)

Đọc `CLAUDE.md`, `docs/README.md`, `docs/architecture.md`, `docs/data-model.md` mục liên quan, `docs/implementation-plan.md` mục 2 và mục 6. Nếu có skill `agentic-sdlc-kit:project-scaffolding` thì dùng nó; nếu không, tự làm theo các bước dưới.

Việc phải làm, theo thứ tự:

1. Kiểm bộ tài liệu: chạy `python3 docs/golden/golden_engine.py`, `python3 docs/golden/golden_engine.py --no-depr`, `python3 docs/golden/golden_cls.py`, `python3 docs/tools/build_rtm.py docs`. Bất kỳ lệnh nào lỗi: ghi `.autopilot/HALT` kèm đầu ra và dừng.
2. Nếu thư mục `normcore/` (gói Python của app) chưa có: tạo app bằng `bench new-app normcore` trong `$BENCH_DIR` (không hỏi gì, dùng thông tin: title "Normcore", publisher "Medcons", license "Proprietary"), rồi chuyển mã sinh ra về gốc kho này sao cho kho này là gốc của app, và liên kết `$BENCH_DIR/apps/normcore` vào kho này. Giữ `docs/` và các tệp autopilot.
3. Tạo site test `normcore.test` (nếu chưa có), cài app, bật `allow_tests`.
4. Dựng cấu trúc gói và 6 Module Def theo `docs/architecture.md`; `required_apps = []`.
5. Dựng walking skeleton đúng `implementation-plan.md` mục 2 phần "Có thật": DocType tối thiểu, `costing/engine.py` tính dòng LABOR theo BR-COST-001, BR-COST-002, BR-COST-007, Desk Page `procedure-editor` tối thiểu, `ai/gateway.py` với provider giả lập và NC AI Log, fixtures 10 vai trò.
6. Nền kỹ thuật (mục 6): `scripts/check_conventions.py`; `normcore/tests/unit/`, `normcore/tests/golden/` (test golden đầu tiên: dòng L01, L03, L04, L09 khớp đến từng đồng); cấu hình pytest và độ phủ; `pre-commit` (ruff, ruff-format, eslint/prettier cho JS); kiểm tra `.github/workflows/ci.yml` và `deploy-staging.yml` có sẵn trong kho — sửa cho chạy được với cấu trúc thật của app nếu cần (không bỏ bước nào).
7. Tạo `docs/decisions/assumptions.md`, `conflicts.md`, thư mục `amendments/`, `defects/`, `docs/features/`, `docs/as-built/`.
8. Chạy toàn bộ: pytest, `bench run-tests --app normcore`, `check_conventions.py`. Phải xanh.
9. Commit lên `develop`, push, tạo PR rỗng nếu cần để CI chạy; đợi CI (`gh run watch`) xanh. Nếu `deploy-staging.yml` chạy: đợi xanh và kiểm điều kiện "Xong khi" của mục 2 trên staging bằng API (tạo dịch vụ, quy trình một bước, bộ định mức, lần tính giá; thấy dòng LABOR liên kết mã bước).
10. Viết `docs/as-built/FEAT-000.md` và tạo `docs/features/FEAT-000/DONE`.

Không được: làm tính năng nào khác ngoài skeleton; bỏ bước kiểm vì "sẽ làm sau".
