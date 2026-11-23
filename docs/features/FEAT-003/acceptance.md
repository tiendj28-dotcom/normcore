# Acceptance FEAT-003 — Kiểm định độc lập (NORM-21)

Kết luận: **accepted** (commit `b383b1fdcb7c25d4d9d05aa5ba0dc6b9240d33c0`, PR #23). ASM-066 (đổi 18 → 19) vẫn chờ tiendj28 duyệt trước In Review.

## Môi trường kiểm
- **Site sạch:** CI run 45070989693 trên `b383b1fdcb7c25d4d9d05aa5ba0dc6b9240d33c0`, job "Test trên site Frappe v15" (bench mới, site mới, cài app, `run-tests --app normcore`) pass. Giới hạn: không tạo được `normcore-verify.test` cục bộ vì runtime QA thiếu `DB_ROOT_PASSWORD`; Lead chấp nhận CI thay thế.
- **Cục bộ, site dùng chung:** `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`: 199 test, OK.
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark`: 93 passed, độ phủ costing 99%.
- `golden_engine.py`, `golden_cls.py` đạt; `build_rtm.py docs` không thêm vấn đề; CI job "Tài liệu, golden, unit test" pass.

## Độ phủ tiêu chí
| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| TC-AUD-01 / FR-AUD-001 | `test_TC_AUD_01_lich_su_va_su_kien`; NC Costing Run, xóa (AMD-006), không ghi trùng, bỏ Password | Đạt (đơn giá làm trên NC Job Title, ASM-066; thêm ca NC Item Price khi FEAT-009 merge) |
| TC-AUD-02 / FR-AUD-002 | `test_TC_AUD_02_ban_ghi_bat_bien`, `test_FR_AUD_002_khong_tao_ngoai_ma_may_chu` | Đạt |
| TC-AUD-03 / FR-AUD-003 | `test_TC_AUD_03_loc_theo_quy_trinh`, `test_FR_AUD_003_loc_nguoi_thoi_gian_va_quyen`, `..._to_time_chi_co_ngay...` | Đạt |
| FR-AUD-004 (điểm ghi) | `test_FR_AUD_004_ghi_xuat_tep` | Đạt |
| Vai trò không quyền + NC Auditor (DocType mới) | `test_permissions` (19 DocType, vai trò ngoài ma trận bị từ chối, Auditor chỉ đọc); lọc theo quyền trong `test_FR_AUD_003_loc_nguoi_thoi_gian_va_quyen` | Đạt |
| Soát diff test | chỉ `test_permissions.py` đổi tên, 18 → 19, docstring; không xóa/skip/nới | Đạt |
| Tài liệu chỉ đọc | không đổi (data-model, architecture đổi qua AMD-006) | Đạt |

## Giới hạn
- **Chưa kiểm UI bằng trình duyệt** (Playwright MCP không kết nối). SCR-DSK-030 kiểm ở smoke staging sau merge.
- Chưa tạo site cục bộ sạch (xem trên).
