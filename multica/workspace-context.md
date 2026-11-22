# Workspace Context — dán vào Multica: Settings → General → Context

<!-- Phần dưới đường kẻ là nội dung dán. Multica đưa Context vào MỌI agent của workspace, nên giữ ngắn. -->

---

Workspace này xây app **normcore** (định giá dịch vụ kỹ thuật bệnh viện) trên **Frappe Framework v15**, app độc lập, không ERPNext. Repo: `mvl26/normcore`, nhánh chính `develop` (staging), `main` (production).

Luật làm việc nằm trong `CLAUDE.md` ở gốc repo. Đọc nó trước mọi việc; khi Context này và `CLAUDE.md` khác nhau, `CLAUDE.md` thắng.

Năm điều không bao giờ được làm:
1. Sửa `docs/golden/`, `docs/srs.md`, `docs/test-cases.md`, `docs/use-cases.md`, `docs/implementation-plan.md`, `CLAUDE.md`, `.claude/`, `.autopilot/`.
2. Tự chế công thức tính giá. Mọi con số phải khớp `docs/golden/*.py`.
3. Sửa, skip hay nới test để cho qua.
4. Push `--force`, push thẳng `main`, chạm production.
5. Gọi nhà cung cấp AI thật trong test.

Quy ước Multica:
- Mỗi issue FEAT có tiêu đề dạng `FEAT-NNN <tên>`. Nhánh: `feat/FEAT-NNN-<slug>`. **Tiêu đề PR bắt đầu bằng mã issue** (ví dụ `NORM-12 FEAT-006: ...`) để Multica tự gắn PR vào issue.
- Trạng thái của FEAT nằm trong `docs/features/FEAT-NNN/` (technical-design, tasks, implementation-log, acceptance, verdict.json, DONE). Đọc chúng trước để biết FEAT đang ở đâu.
- Giả định tự chọn ghi `ASM-NNN` vào `docs/decisions/assumptions.md`; mâu thuẫn ghi `CF-NNN`; sửa thiết kế ghi `AMD-NNN`; lỗi tài liệu chỉ đọc ghi `DEF-NNN`.
- Kết thúc mỗi run bằng một comment: đã làm gì, lệnh kiểm nào đã chạy và kết quả, việc còn lại.
- Viết tiếng Việt trong comment, tài liệu, nhãn giao diện. Mã và fieldname tiếng Anh.

Lệnh kiểm chuẩn:
`python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py && python3 docs/tools/build_rtm.py docs`
`pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark`
`cd $BENCH_DIR && bench --site normcore.test run-tests --app normcore`
`python3 scripts/check_conventions.py`
