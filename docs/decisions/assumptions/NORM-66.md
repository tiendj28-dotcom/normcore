# Giả định của NORM-66

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-NORM66-02 | — | FR-ACC-007 | Hook phạm vi ghi Error Log mỗi lần từ chối, chỉ để chẩn đoán 403 của NC Auditor không tái hiện được ở test (Quyết định Lead, phương án 2, bình luận trên NORM-66). Không đổi hành vi quyền. Gỡ khi đã rõ nguyên nhân | `core/permissions.py::_log_deny` | Theo Quyết định Lead |
