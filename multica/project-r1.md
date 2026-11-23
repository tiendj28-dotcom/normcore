# Mô tả project — dán vào Multica: project "Normcore R1" → Description

<!-- Multica đưa tên và mô tả project vào mọi run của issue trong project. Làm tương tự cho R2, R3 (đổi danh sách FEAT). -->

---

**Mục tiêu:** hoàn thành bản phát hành R1 của normcore: 27 FEAT theo thứ tự trong `.autopilot/build-order.txt` (dòng có `|R1|`). "Kết quả trình diễn được" của R1 ở `docs/implementation-plan.md` mục 1.

**Điều phối:** người giao việc cho **Lead**. Lead giao từng bước cho một thành viên, **duyệt mọi câu hỏi và mọi lần Blocked** dựa trên tài liệu, và báo người khi PR sẵn sàng merge. Người chỉ merge PR.

**Luồng một FEAT** (một issue, một nhánh `feat/FEAT-NNN-<slug>`, một PR):
Todo (BA thiết kế) → Đang làm (Dev viết test + mã, mở PR) → Code review (Reviewer) → QA (kiểm định độc lập, hoàn thiện hồ sơ) → In Review (người merge) → Done.
Bị trả về: Reviewer/QA chuyển về Đang làm. Câu hỏi hoặc lỗi thiết kế: Blocked, Lead quyết. Bảng đầy đủ ở `multica/agents.md`.

**Phụ thuộc:** cột thứ ba trong `build-order.txt`. Một FEAT chỉ bắt đầu khi mọi FEAT nó phụ thuộc đã có `docs/features/FEAT-xxx/DONE` trên `develop`.

**Bench dev dùng chung:** mọi lệnh `bench` chạy qua `scripts/with_bench.sh '<lệnh>'` (khóa + trỏ mã về checkout của run).

**Ranh giới kỹ thuật:**
- Logic nghiệp vụ ở module Python thuần (`normcore/costing/*.py`…), test được bằng pytest không cần site. Controller DocType chỉ gọi vào đó.
- Một FEAT một lúc; không sửa ngoài phạm vi FEAT, không refactor tiện tay.
- Độ phủ ≥ 90% cho `normcore/costing/` và `normcore/benchmark/rules.py`.

**Bàn giao:** Definition of Done ở `CLAUDE.md` mục 8. QA chỉ chuyển sang In Review khi verdict `accepted` và PR đã có acceptance, verdict, As-Built, Test ref, DONE. Người merge thì issue tự sang Done; workflow deploy staging tự chạy sau đó.
