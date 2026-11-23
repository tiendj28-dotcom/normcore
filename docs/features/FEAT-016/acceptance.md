# Nghiệm thu FEAT-016 — Số liệu kế toán, sản lượng, quy tắc phân bổ

Người kiểm: QA (Multica, Tester iu). Commit kiểm: `6bc6d062a3967ca3fa2245610a1550970b90737c`. Thời điểm: 2026-11-23T12:59:07Z.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-ACCT-01..09 | Mỗi TC có test cùng mã (`test_TC_ACCT_NN_*`) ở nc_accounting_import, nc_account_mapping, nc_service_volume, nc_cost_center_driver, nc_allocation_rule, api/test_importer_accounting, unit/test_accounting, golden/test_accounting_golden. Assertion đối chiếu số golden (tổng theo trung tâm/loại, 20÷50=40%) | Đạt |
| FR-ACCT-011 | `test_FR_ACCT_011_lan_nhap_thu_hai_cung_nam_giu_lan_cu` | Đạt |
| Bench toàn bộ | `bench --site normcore.test migrate` rồi `run-tests --app normcore`: Ran 574 tests, OK | Đạt (xem ghi chú 1) |
| pytest unit + golden | 266 passed; độ phủ normcore/costing 99% (≥ 90%) | Đạt |
| golden_engine, golden_cls | exit 0 | Đạt |
| check_conventions.py | không lỗi | Đạt |
| build_rtm.py docs | không thêm vấn đề mới (các dòng cảnh báo có sẵn ở FEAT khác) | Đạt |
| Quyền: vai trò ngoài ma trận, NC Auditor | `tests/test_permissions.py` (37 DocType, `assertEqual`) xanh; Finance W, Auditor chỉ đọc | Đạt |
| Diff test | Không xóa/skip/nới test. Chỉ đổi `test_permissions.py` 30→37 và danh sách Finance ở test_importer.py theo quyết định Lead (ASM-128), vẫn `assertEqual` | Đạt |
| Tài liệu chỉ đọc | Không sửa srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github. `docs/data-model.md` sửa theo AMD-010 (không thuộc danh sách chỉ đọc) | Đạt |
| CI PR #35 | 2 job pass ở head 6bc6d06 | Đạt |

## Ghi chú và giới hạn
1. Không có `DB_ROOT_PASSWORD` trong môi trường QA nên không tạo được site sạch `normcore-verify.test`; chạy trên `normcore.test` sau `migrate` (cùng khóa bench). CI của PR chạy trên site sạch và xanh. Site `normcore-verify.test` còn sót trong bench (từ lần tạo dở), cần người có quyền root xóa.
2. Giao diện (SCR-DSK-020/021) chưa kiểm bằng trình duyệt: không có tài khoản test theo vai trò; chỉ kiểm bằng test quy ước giao diện và API.
