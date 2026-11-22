# Mô tả project — dán vào Multica: project "Normcore R1" → Description

<!-- Multica đưa tên và mô tả project vào mọi run của issue trong project. Làm tương tự cho R2, R3 (đổi danh sách FEAT). -->

---

**Mục tiêu:** hoàn thành bản phát hành R1 của normcore: 27 FEAT theo thứ tự trong `.autopilot/build-order.txt` (dòng có `|R1|`). "Kết quả trình diễn được" của R1 ở `docs/implementation-plan.md` mục 1.

**Một issue = một FEAT.** Issue đi qua các cột của workflow "Normcore Delivery":
Design → UI → Implement → Verify → Integrate → Done. Mỗi cột có agent và skill riêng; agent ở cột nào chỉ làm việc của cột đó rồi chuyển issue sang cột kế (hoặc trả về cột trước nếu workflow cho phép).

**Phụ thuộc:** cột thứ ba trong `build-order.txt`. Một FEAT chỉ bắt đầu Design khi mọi FEAT nó phụ thuộc đã có `docs/features/FEAT-xxx/DONE` trên `develop`. Nếu chưa: đặt wakeup chờ issue kia `done` (`multica issue wakeup create <issue> --until-issue <issue-kia> --until-issue-state done --instruction "..."`), comment lý do, kết thúc run.

**Ranh giới kỹ thuật:**
- Logic nghiệp vụ ở module Python thuần (`normcore/costing/*.py`…), test được bằng pytest không cần site. Controller DocType chỉ gọi vào đó.
- Một FEAT một lúc; không sửa ngoài phạm vi FEAT, không refactor tiện tay.
- Độ phủ ≥ 90% cho `normcore/costing/` và `normcore/benchmark/rules.py`.

**Bàn giao:** Definition of Done ở `CLAUDE.md` mục 8. Issue chỉ sang `done` sau khi PR đã merge vào `develop`, staging đã cập nhật và smoke test đạt (cột Integrate làm việc này).
