# Workspace Context — dán vào Multica: Settings → General → Context

<!-- Phần dưới đường kẻ là nội dung dán. Multica đưa Context vào MỌI agent của workspace, nên giữ ngắn. -->

---

Workspace này xây app **normcore** (định giá dịch vụ kỹ thuật bệnh viện) trên **Frappe Framework v15**, app độc lập, không ERPNext. Repo: `mvl26/normcore`, nhánh nền `develop` (staging), `main` (production).

Luật làm việc nằm trong `CLAUDE.md` ở gốc repo; đọc trước mọi việc. Cách chia việc: squad do **Lead** điều phối và **duyệt** mọi câu hỏi, mọi lần Blocked; người chỉ merge PR. Chi tiết vai và trạng thái: `multica/agents.md`.

Năm điều không bao giờ được làm:
1. Sửa `docs/golden/`, `docs/srs.md`, `docs/test-cases.md`, `docs/use-cases.md`, `docs/implementation-plan.md`, `CLAUDE.md`, `.claude/`, `.autopilot/`, `.github/`.
2. Tự chế công thức tính giá. Mọi con số phải khớp `docs/golden/*.py`.
3. Sửa, skip hay nới test để cho qua.
4. Push `--force`, merge vào `develop`/`main` (chỉ người merge), chạm production.
5. Gọi nhà cung cấp AI thật trong test.

Quy ước:
- Mỗi FEAT một issue, tiêu đề `FEAT-NNN <tên>`. Nhánh `feat/FEAT-NNN-<slug>`. **Tiêu đề PR bắt đầu bằng mã issue** (ví dụ `NORM-12 FEAT-006: ...`) để Multica tự gắn PR.
- Đầu mỗi run trên issue FEAT: skill `normcore-feat-context` (`python3 scripts/feat_context.py FEAT-NNN`) để lấy đúng FR, BR, TC, DocType, quyền.
- Trạng thái FEAT nằm trong `docs/features/FEAT-NNN/` (technical-design, ui-design, tasks, implementation-log, acceptance, verdict.json, DONE).
- Thiếu thông tin: tra `CLAUDE.md` mục 2 và 6 trước; không có câu trả lời thì hỏi Lead (bình luận + Blocked). Giả định ghi `ASM-NNN`, mâu thuẫn `CF-NNN`, sửa thiết kế `AMD-NNN`, lỗi tài liệu chỉ đọc `DEF-NNN`.
- Bench dev dùng chung: mọi lệnh `bench` chạy qua `scripts/with_bench.sh '<lệnh>'`, migrate và test trong cùng một lần gọi.
- Viết tiếng Việt trong bình luận, tài liệu, nhãn giao diện. Mã và fieldname tiếng Anh.

Lệnh kiểm chuẩn:
`python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py && python3 docs/tools/build_rtm.py docs`
`pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark`
`scripts/with_bench.sh 'bench --site normcore.test run-tests --app normcore'`
`python3 scripts/check_conventions.py`
