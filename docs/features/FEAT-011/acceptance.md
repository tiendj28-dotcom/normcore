# Nghiệm thu FEAT-011 (QA, commit abc67e02cfe866e03d29b104161203e92ddce330)

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-RES-05 (BS, DD, golden) | test_TC_RES_05_* (unit + DocType), pytest 110 passed | Đạt |
| TC-RES-06 (khóa, nhân bản) | test_TC_RES_06_* trong bench | Đạt |
| TC-RES-11 (loại giá) | test_TC_RES_11_* trong bench | Đạt |
| TC-CLS-50 (ZERO, 5%, 2%) | test_TC_CLS_50_* | Đạt |
| Golden engine/cls | chạy lại, ok | Đạt |
| pytest unit+golden, độ phủ costing | 110 passed, 99% | Đạt |
| bench run-tests toàn app (normcore.test sau migrate) | Ran 247 tests, OK | Đạt (xem ghi chú) |
| check_conventions, build_rtm | không lỗi mới, Must chưa có TC: 0 | Đạt |
| Diff test | chỉ đổi 19→20 DocType ở test_permissions (do thêm NC Price Category, ASM-076); không xóa/skip | Đạt |
| Tài liệu chỉ đọc | không đổi | Đạt |
| CI PR #24 | 2 job pass | Đạt |

## Ghi chú giới hạn
- Không tạo được site sạch normcore-verify.test: môi trường QA không có DB_ROOT_PASSWORD (MariaDB từ chối root). Đã chạy toàn bộ test trên normcore.test sau migrate; CI của PR chạy trên site mới và xanh.
- Playwright MCP không kết nối được nên chưa kiểm giao diện bằng trình duyệt; quyền (vai trò không có quyền, NC Auditor) được phủ bởi test_permissions (20 DocType) và test_nc_price_category.
