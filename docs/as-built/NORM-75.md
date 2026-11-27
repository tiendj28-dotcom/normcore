# As-Built: NORM-75 lọc khoa gõ tay + Tab trên danh sách NC Technical Service

## 1. Thay đổi
- `nc_technical_service_list.js`: lắng nghe `change`/`blur` ở ô "Khoa thực hiện"; khi khoa hiện tại khác khoa lần tính gần nhất thì tính lại bộ lọc mã dịch vụ (bỏ kết quả cũ bằng `seq`). Không đổi API, DocType, quyền.
- Test: `normcore/tests/unit/test_service_list_behavior.py` và harness `js/service_list_harness.js`.

## 2. Giới hạn
- Harness giả lập ô Link, không phải trình duyệt; đã kiểm tay trên staging (Playwright, Clinician Test).
- Gõ tay + Tab có thể gọi tính lại hai lần (blur và onchange); kết quả vẫn đúng nhờ `seq`.
- Ghi chú nhỏ của Reviewer (tham số `typed_tab` không dùng trong harness) chưa xử lý.

Người nghiệm thu: QA (Multica).
