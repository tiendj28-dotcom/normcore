# Nghiệm thu FEAT-039 — Vai trò kiểm soát nội bộ (NC Auditor)

Nhánh `feat/FEAT-039-kiem-soat-noi-bo` tại `6b1ad93`. Người kiểm: QA (Multica), độc lập với người viết.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-CLS-44 (FR-ACC-007): đọc số liệu, nhật ký; sửa/xóa/duyệt bị từ chối; quét quyền sạch | `test_TC_CLS_44_*` (7 hàm TC-CLS-44 ở `tests/test_feat_039.py`, `unit/test_readonly.py`, `test_permission_matrix.py::test_TC_CLS_44_nc06_*`) đều OK trong `run-tests --app normcore`: 511 tests OK | Đạt |
| Quét quyền tự áp cho DocType `NC ` mới | `nc_doctypes()` lấy động; `test_TC_CLS_44_quet_bat_custom_docperm`, `..._quet_bat_workflow` | Đạt |
| TC-ACC-04 giữ đạt; TC-AUD-03 với NC Auditor | `test_TC_ACC_04_*` cũ không sửa, vẫn xanh; `test_TC_AUD_03_auditor_loc_theo_quy_trinh` | Đạt |
| Không đổi quyền 9 vai trò khác | `test_TC_CLS_44_vai_tro_khac_khong_bi_hep`; diff không đụng fixture vai trò | Đạt |
| Chạy từ đầu | golden thoát 0; pytest unit+golden 233 passed, phủ 98,73%; `check_conventions.py` thoát 0; `build_rtm.py docs` không thêm vấn đề; `migrate` + `run-tests --app normcore` OK | Đạt (xem giới hạn) |
| Soát diff test | Chỉ thêm test; không xóa/skip/nới test cũ. Tài liệu chỉ đọc không đổi | Đạt |
| Phạm vi | `scripts/check_conventions.py` (NC-06) nằm trong thiết kế T02 | Đạt |
| CI PR #36 | Cả hai job pass tại `6b1ad93` | Đạt |
| Giao diện (Playwright, staging, tài khoản NC Auditor) | `/app/normcore` mở được (khối Nhật ký 5); danh sách NC Norm Set, NC Costing Run, NC Service Cost không có nút Mới; form `DM-SMOKE-20261121160328-K01-v1` (Đã khóa), `TG-2026-005`, `SC-00015` không có nút Lưu/Xóa/Duyệt/Khóa (NC Costing Run chỉ có "Xem kết quả tính giá", chỉ đọc). Ảnh ở `screens/` | Đạt |
| Ghi qua API với NC Auditor (set_value, delete, insert) | cả ba bị từ chối | Đạt |

## Giới hạn
- Không tạo được site sạch `normcore-verify.test` (QA thiếu `DB_ROOT_PASSWORD`, MariaDB từ chối root). Đã chạy toàn bộ test trên `normcore.test` sau `migrate`; CI của PR cài mới trên site sạch và xanh.
- ASM-131: DocType đối soát, bộ định mức nhập khẩu chưa có; kiểm lại khi FEAT liên quan xong.
