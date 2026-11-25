# Acceptance bản sửa NORM-31 (FEAT-004 `import_set`, kèm 2 góp ý FEAT-016)

Kết luận: **accepted**. Hồ sơ FEAT-004/FEAT-016 (As-Built, Test ref, `DONE`) đã có từ trước, không tạo lại.

Commit đã kiểm: `562225fb530bf7073f9fdb19c9abca45d01cfcfd` (HEAD PR #40, nhánh `fix/NORM-31-import-set`). Kiểm độc lập bởi QA.

## Lệnh đã chạy

| Lệnh | Kết quả |
| :-- | :-- |
| `golden_engine.py`, `golden_cls.py` | thoát 0 |
| `build_rtm.py docs` | `VAN DE: 0` |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 314 passed, độ phủ costing 99% |
| site sạch `normcore-verify.test`: new-site, install-app, `run-tests --app normcore`, drop-site (một lần gọi `with_bench.sh`) | Ran 659 tests, OK; site đã xóa |
| `check_conventions.py` | thoát 0 |
| `gh pr checks 40` | cả hai job pass |
| Harness JS `import_excel_harness.js` chạy với `import_excel.js` của `origin/develop` | `route_ok`, `route_before_load`, `reopen_other` cho giá trị/tệp sai: test bắt được lỗi thật |

Ghi chú môi trường: `DB_ROOT_PASSWORD` không có sẵn; dùng tài khoản root DB `bench_admin` (từ `~/.bench-db.cnf`) với `--db-root-username/--db-root-password`.

## Tiêu chí → bằng chứng

| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| S1 `import_set` chọn sẵn bộ nhập (N31-01) | `test_N31_01_*` (2 test, cả trường hợp danh sách tải sau) | Đạt |
| S1 khóa sai/không quyền, không có tham số: giữ hành vi cũ, không báo lỗi (N31-02, 03, 06) | `test_N31_02/03/06`: `msgprint_calls == []`, `consoleErrors == []`, giá trị `sets[0]` | Đạt |
| S1 mở lại với bộ khác đổi bộ, xóa tệp; tham số bị tiêu thụ (N31-04, 05) | `test_N31_04/05` | Đạt |
| S1 quyền thật ở máy chủ không đổi | Diff không chạm API/DocType; `list_import_sets` đã lọc quyền, chỉ chọn trong danh sách đó | Đạt |
| S2 thông báo âm dùng nhãn tiếng Việt (N31-07, 08) | `test_N31_07` (unit), `test_N31_08` (site, `ValidationError` chứa "Số nhân lực không được âm", không chứa `headcount`) | Đạt |
| S3 hộp thoại "Sửa loại chi phí" ghi số dòng + mã tài khoản, không tự lấy dòng 1 (N31-09…11) | `test_N31_09/10/11` (có thoát HTML mã tài khoản) | Đạt |
| Test FEAT-004/016 hiện có giữ nguyên | Diff test chỉ thêm; không xóa/skip/nới assertion | Đạt |
| Phạm vi, tài liệu chỉ đọc | 16 tệp đúng S1/S2/S3 + hồ sơ; không chạm srs, test-cases, golden, CLAUDE.md, .claude, .github | Đạt |

## Kiểm giao diện

Chưa kiểm Playwright trên staging (http://112.213.88.40:8100): bản sửa chưa deploy (staging chạy develop). Hành vi giao diện được kiểm bằng harness chạy mã JS thật trong Node. Đề nghị người merge xem nhanh nút "Nhập từ Excel" từ danh sách NC Service Volume sau deploy.
