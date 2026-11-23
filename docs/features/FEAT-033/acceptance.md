# Nghiệm thu FEAT-033 — Hồ sơ tuân thủ thiết bị

Commit đã kiểm: `d9be0cb`. Người kiểm: Tester iu (QA độc lập).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-CLS-27 (thiếu chứng từ bị từ chối, đủ thì lưu, Còn hạn) | `test_TC_CLS_27_thieu_chung_tu_bi_tu_choi` trong `test_nc_equipment_compliance.py`; chạy xanh trong run-tests | Đạt |
| TC-CLS-28 (nhắc hạn, đổi số ngày, báo cáo hạn) | `test_TC_CLS_28_nhac_han_thong_bao_va_doi_so_ngay` (`api/test_compliance.py`), `test_TC_CLS_28_bao_cao_...` (báo cáo) | Đạt |
| FR-CMP-006 hàm thuần "có hồ sơ còn hạn tại ngày X" | `normcore/costing/compliance.py`, unit test xanh | Đạt |
| Quyền: vai trò không có quyền, NC Auditor | `test_permissions.py` (29 DocType), test DocType mới | Đạt |
| `bench run-tests --app normcore` (site dev `normcore.test`, sau migrate) | 465 test, OK | Đạt |
| pytest unit + golden + độ phủ | 199 passed; costing 98% (compliance.py 98%) | Đạt |
| golden_engine, golden_cls | chạy không lỗi | Đạt |
| `check_conventions.py` | exit 0 | Đạt |
| `build_rtm.py docs` | Must chưa có TC: 0, không phát sinh mới | Đạt |
| Diff test cũ | `test_importer.py`, `test_permissions.py` chỉ cập nhật kỳ vọng (thêm `nc_equipment_compliance`, 27→29 DocType) theo ASM-105 Lead duyệt; không xóa/skip/nới | Đạt |
| Tài liệu chỉ đọc | không bị sửa | Đạt |
| CI PR #32 | 2 check pass | Đạt |

## Giới hạn
- Không tạo được site sạch `normcore-verify.test`: biến `DB_ROOT_PASSWORD` không có trong môi trường QA, và site cùng tên đã tồn tại sẵn. Bộ test chạy trên `normcore.test` (dev, sau migrate) thay thế. CI của PR chạy trên site Frappe mới và xanh.
- Chưa kiểm giao diện bằng Playwright (không có tài khoản test theo vai trò); quyền được kiểm qua test bench.
