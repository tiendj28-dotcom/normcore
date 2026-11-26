# Nghiệm thu FEAT-023 — Gateway AI

Commit đã kiểm: `3d85819434e84d96434ae4589bc50511f4a25c80` (PR #50). Người kiểm: Tester iu (QA độc lập).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-AI-05 quá hạn | `test_TC_AI_05_qua_han_giu_du_lieu`: nhật ký "Quá hạn", thông báo lỗi, không tạo bản ghi mới, dữ liệu còn nguyên | Đạt |
| TC-AI-06 bộ dựng nội dung | `test_TC_AI_06_*` (unit/test_ai_guard.py): DocType kế toán/tính giá bị từ chối | Đạt |
| TC-AI-07 tắt AI | `test_TC_AI_07_tat_ai_an_nut_van_chay_thu_cong`: cờ boot tắt, tạo quy trình, khóa bộ định mức chạy tay. Phần giá tham chiếu chưa kiểm được (ASM-023-16, NC Benchmark Price chưa có) | Đạt (có ghi chú) |
| TC-AI-08 nhật ký đủ trường | `test_TC_AI_08_log_du_truong` (nhà cung cấp giả lập) | Đạt |
| TC-AI-09 hạn mức | `test_TC_AI_09_chan_han_muc` (1.200/1.000 → "Bị chặn hạn mức", NC Admin nhận 1 thông báo) và biên | Đạt |
| TC-AI-11 đổi địa chỉ | `test_TC_AI_11_doi_dia_chi`: lời gọi kế tiếp tới địa chỉ/giao thức mới | Đạt |
| TC-NFR-04 khóa | `test_TC_NFR_04_khoa_khong_lo`: khóa không có trong API, Version, log, Error Log | Đạt |

## Lệnh đã chạy
- golden_engine.py, golden_cls.py: ok. build_rtm.py, check_conventions.py: exit 0.
- pytest unit + golden (venv bench): 477 passed, độ phủ costing/benchmark 99%.
- `bench --site normcore.test migrate && run-tests --app normcore`: Ran 945 tests, OK.
- CI PR #50: 2 job pass.
- Soát diff: không test bị xóa/skip/nới; không sửa tài liệu chỉ đọc; phạm vi đúng FEAT-023.

## Hạn chế khi kiểm (nêu rõ)
- Không tạo được site sạch `normcore-verify.test`: môi trường thiếu `DB_ROOT_PASSWORD` (MariaDB 1698). Toàn bộ test bench chạy trên site dev `normcore.test` đã migrate, không phải site mới.
- Chưa kiểm giao diện bằng Playwright (không có tài khoản test theo vai trò). Quyền theo vai trò được kiểm qua test API (`test_get_ai_status_moi_nguoi_dung`).
