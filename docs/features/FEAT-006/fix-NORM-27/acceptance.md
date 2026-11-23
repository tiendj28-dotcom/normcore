# Acceptance bản sửa NORM-27 (FEAT-006: `.finally` trên jQuery Deferred)

Kết luận: **accepted** cho bản sửa. Hồ sơ FEAT-006 (verdict, Test ref, As-Built, `DONE`) và kiểm Playwright trên staging làm ở NORM-16 sau khi PR #34 merge, không thuộc tệp này.

Commit đã kiểm: `f4c950394617d827a53f5156a9bbada6610ed6a1` (HEAD PR #34, nhánh `fix/NORM-27-deferred-finally`). Kiểm độc lập bởi QA.

## Lệnh đã chạy

| Lệnh | Kết quả |
| :-- | :-- |
| `golden_engine.py`, `golden_cls.py` | thoát 0 |
| `build_rtm.py docs` | `VAN DE: 0` |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 188 passed, độ phủ 98% |
| `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'` | Ran 426 tests, OK |
| `check_conventions.py` | thoát 0 |
| `gh pr checks 34` | cả hai job pass |

Ghi chú môi trường: biến `DB_ROOT_PASSWORD` không có trong môi trường QA nên không tạo được site `normcore-verify.test` (new-site báo Access denied). Đã chạy `run-tests` trên site dev `normcore.test` sau `migrate`, đúng lệnh kiểm chuẩn ở CLAUDE.md. Thư mục rỗng/dở `~/frappe-bench/sites/normcore-verify.test` do lần new-site hỏng còn lại, cần người có quyền root DB dọn.

## Tiêu chí → bằng chứng

| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| Sửa gốc: `.finally` trên Deferred ở `load()`/`run()` và chỗ khác | Diff `ProcedureEditor.vue` 5 dòng: `call()` bọc `Promise.resolve(frappe.call(...))`, `run()` bọc `Promise.resolve(fn())`. `frappe.call` chỉ còn trong `call()`; mọi `.then/.catch/.finally` đều đi qua `call()`/`run()` | Đạt |
| Test chạy được, không đọc chuỗi mã | `procedure_editor_harness.js` chạy khối `<script>` thật trong Node, `frappe.call` giả là Deferred không có `.finally` | Đạt |
| (a) `busy` về false khi thành công và lỗi | `test_E4_busy_ve_false_sau_khi_thanh_cong`, `test_E4_busy_ve_false_sau_khi_loi` | Đạt |
| (b) không lỗi console | mọi test khẳng định `consoleErrors == []` (bắt `console.error` và `unhandledRejection`) | Đạt |
| (c) tạo/sao chép thành công không hiện dải lỗi | `test_E1_tao_thanh_cong_khong_hien_dai_loi`, `test_E12_sao_chep_thanh_cong_khong_hien_dai_loi`: `error`/`existing` rỗng, không gọi `find_existing`, `loading` false | Đạt |
| (d) tiêu điểm sau Lên/Xuống, kể cả biên | `test_K3_xuong_giua_*`, `test_K3_len_giua_*`, `test_K3_bien_xuong_cuoi_*`, `test_K3_bien_len_dau_*` | Đạt |
| Test bắt được lỗi thật | QA chạy harness với `ProcedureEditor.vue` của `origin/develop`: cả 6 kịch bản đã thử (step_ok, step_error, create_ok, copy_ok, move_S1_down, move_S2_down) đổ với `fn(...).catch(...).finally is not a function`; với bản sửa đều xanh | Đạt |
| Không sửa/skip/nới test cũ | `git diff origin/develop...HEAD --stat`: chỉ 3 tệp, 2 tệp test là tệp mới; thiếu Node thì test báo lỗi, không skip | Đạt |
| Phạm vi, tài liệu chỉ đọc | Không đổi hành vi khác, không chạm docs/golden, CLAUDE.md, .github | Đạt |

## Giới hạn
E5, E6, K6 dùng chung `run()` với E4 nên được phủ gián tiếp. Harness dùng vm tối giản, không phải Vue và DOM thật: việc xác nhận tiêu điểm và dải lỗi trên giao diện thật (E1, E4–E7, E12, K3, K6) làm bằng Playwright trên staging ở NORM-16 sau merge.
