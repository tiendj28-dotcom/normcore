# As-Built: NORM-66 chẩn đoán 403 của NC Auditor trên NC Service Cost (staging)

## 1. Thay đổi
- `normcore/core/permissions.py`: hook `has_permission` tách phần quyết định ra `_decide` (logic giữ nguyên), và khi kết quả là `False` ghi một Error Log tiêu đề `NC hook quyền từ chối` (JSON: user, ptype, doctype, name, roles, departments). Lỗi khi ghi log bị nuốt, không đổi kết quả quyền.
- Không đổi hành vi cấp hay từ chối quyền.

## 2. Cách dùng
Sau khi deploy staging, đăng nhập Auditor, mở một NC Service Cost, rồi đọc `Error Log` có `method = "NC hook quyền từ chối"` bằng tài khoản quản trị. Không có bản ghi nào nghĩa là 403 không đến từ hook này.

## 3. Giới hạn
Chỉ phục vụ chẩn đoán; gỡ hoặc giữ tùy quyết định sau khi tìm ra nguyên nhân (ASM-NORM66-02).
