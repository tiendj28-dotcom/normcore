# Mô tả project — dán vào Multica: project "Normcore R1" → Description

<!-- Multica đưa tên và mô tả project vào mọi run của issue trong project. Làm tương tự cho R2, R3 (đổi danh sách FEAT). -->

---

**Mục tiêu:** hoàn thành bản phát hành R1 của normcore: 27 FEAT theo thứ tự trong `.autopilot/build-order.txt` (dòng có `|R1|`). "Kết quả trình diễn được" của R1 ở `docs/implementation-plan.md` mục 1.

**Điều phối:** squad do **Lead** điều phối; Lead chọn FEAT kế, giao từng bước, và là người duy nhất merge. Một FEAT đi qua: thiết kế + UI (Dev hoặc BA) → hiện thực (Dev) → review mã (Reviewer) → kiểm định độc lập (QA, khác người viết) → tích hợp (Lead). Bảng đầy đủ ở `multica/agents.md`. Xong một bước: comment kết quả, đặt issue `in_review`, @mention Lead; không tự giao việc cho agent khác.

**Phụ thuộc:** cột thứ ba trong `build-order.txt`. Một FEAT chỉ bắt đầu thiết kế khi mọi FEAT nó phụ thuộc đã có `docs/features/FEAT-xxx/DONE` trên `develop`. Nếu chưa: comment "chờ FEAT-xxx", @mention Lead, kết thúc run.

**Bench dev dùng chung:** mọi lệnh `bench` chạy qua `scripts/with_bench.sh '<lệnh>'` (khóa + trỏ mã về checkout của run). Không chạy bench trực tiếp.

**Ranh giới kỹ thuật:**
- Logic nghiệp vụ ở module Python thuần (`normcore/costing/*.py`…), test được bằng pytest không cần site. Controller DocType chỉ gọi vào đó.
- Một FEAT một lúc; không sửa ngoài phạm vi FEAT, không refactor tiện tay.
- Độ phủ ≥ 90% cho `normcore/costing/` và `normcore/benchmark/rules.py`.

**Bàn giao:** Definition of Done ở `CLAUDE.md` mục 8. Issue chỉ sang `done` sau khi PR đã merge vào `develop`, staging đã cập nhật và smoke test đạt và PR tạo `DONE` đã merge (Lead làm việc này).
