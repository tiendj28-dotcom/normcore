# Acceptance FEAT-006 — Kiểm định lại sau NORM-15, NORM-22, NORM-23, NORM-27 (NORM-16)

Kết luận: **accepted.** Phần A đạt ở HEAD `3a28d84fa5fc36546ebf51c3a82e45d627d9f19c`; Phần B (Playwright trên staging có đủ bản sửa NORM-22, NORM-23, NORM-27) đạt mọi mã. Lỗi `.finally` trên `frappe.call` (làm kẹt `busy`, hỏng K3, hiện dải lỗi sai sau khi tạo/sao chép) đã được NORM-27 sửa và có test hành vi; console không còn lỗi `finally`. Theo ASM-099 (Quyết định Lead), kết quả Playwright thay cho câu trả lời của người duyệt.

## Môi trường kiểm
Nhánh `ai/NORM-16-reverify-006` = `origin/develop` @ `73029ce` (PR #34) gộp vào; HEAD kiểm `3a28d84fa5fc36546ebf51c3a82e45d627d9f19c`. Phần A: site sạch `normcore-verify.test` qua `scripts/with_bench.sh` (đã xóa). Phần B: staging http://112.213.88.40:8100 (deploy `73029ce` thành công 13:08 UTC), Chromium 1366×768, locale `vi`, tài khoản NC Clinician (khoa K01) và NC Auditor; không dùng Administrator để kiểm (chỉ dùng STG_ADMIN để tạo dữ liệu thử). Không sửa mã sản phẩm, không thêm test.

## Phần A (ở HEAD `3a28d84fa5fc36546ebf51c3a82e45d627d9f19c`)
| Lệnh | Kết quả | Đạt |
| :-- | :-- | :-: |
| `bench --site normcore-verify.test run-tests --app normcore` | Ran 486 tests, OK | Đạt |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` | 216 passed, độ phủ 98,73% | Đạt |
| `golden_engine.py`, `--no-depr`, `golden_cls.py` | cả ba thoát 0 | Đạt |
| `python3 scripts/check_conventions.py` | thoát 0 | Đạt |
| `build_rtm.py` trên bản sao `docs` | thoát 0, Must chưa có TC: 0 | Đạt |
| Diff tài liệu chỉ đọc (`golden`, `srs.md`, `test-cases.md`, `use-cases.md`, `implementation-plan.md`, `CLAUDE.md`, `.claude`, `.github`, `.autopilot`) từ lần kiểm trước | rỗng | Đạt |
| Diff test từ lần kiểm trước (NORM-23, NORM-27, FEAT khác) | không skip/xfail; chỉ đổi số DocType trong `test_permissions` do FEAT khác thêm DocType | Đạt |

Các mục Phần A đã kiểm ở lượt trước và không đổi (mã FEAT-006 chỉ đổi ở `ProcedureEditor.vue` và test hành vi): A10 bốn đột biến làm test đỏ (bỏ lưu văn bản; bỏ lưu mục; trích dẫn của phần mất trường; sao chép bỏ hai trường), A11 gọi API theo NC Clinician / NC Auditor / NC Finance (6 hàm ghi bị `PermissionError`), diff PR #17 không xóa/skip/nới test, ASM-046 không trái FR-PROC-007, TC-PROC-09 kiểm đủ văn bản, mục, đoạn trích, quan hệ kể cả khi sao chép (FR-PROC-013).

## Phần B — kết quả từng mã (ảnh theo mã đính kèm ở bình luận NORM-16)
Dữ liệu thử (STG_ADMIN tạo, không sửa/xóa bản ghi có sẵn): NC Technical Service `THU-NORM16-X`, `-Y`, `-Z`, `-W`, `-V`; NC Job Title "Điều dưỡng" (`DD`) đã có. Bản Nháp `QT-THU-NORM16-*-K01-v1` do NC Clinician tạo qua giao diện.

| Mã | Kết quả | Điều thấy được |
| :-- | :-: | :-- |
| L1 | Đạt | Cột Mã số, Trạng thái, Dịch vụ kỹ thuật, Khoa chủ trì, Phiên bản; tiêu đề "Quy trình kỹ thuật"; không cuộn ngang |
| L2, L4, L5 | Đạt | Lọc đúng; "Mở trình soạn" mở đúng bản; NC Auditor không có nút thêm |
| L3 | Đạt | Nháp chấm xám, Đã ban hành xanh, đều có chữ |
| E1 | Đạt | Tạo dịch vụ W/K01: bản Nháp đủ 8 phần, **không có dải lỗi**, "Đang tải…" tắt |
| E2 | Đạt | Tạo lần hai: dải đỏ "Dịch vụ đã có quy trình cho khoa này:" + liên kết mở đúng bản Nháp |
| E3 | Đạt | Lưu phần rồi tải lại: còn nguyên |
| E4 | Đạt | Bỏ trống tên bị chặn; ba lần thêm liên tiếp, không tải lại: S001, S002, S003 |
| E5 | Đạt | S001 Xuống hai lần, S003 Lên một lần, liên tiếp: S003, S002, S001, mã giữ nguyên |
| E6 | Đạt | Xóa S002 (có hộp xác nhận), thêm bước: S003, S001, S004, liên tiếp |
| E7 | Đạt | Gợi ý chức danh; đơn vị "phút" chỉ đọc; R001 15 phút 2 người, sửa 20 phút vẫn R001 (liên tiếp) |
| E8 | Đạt | Vật tư không có trong danh mục lưu được (R002), không liên kết |
| E9 | Đạt | Cột phải hiện "Theo hướng dẫn", "Thông tư 43/2013/TT-BYT — Điều 5", đoạn trích |
| E10 | Đạt | "Khác biệt" ở Chỉ định đủ văn bản, mục, đoạn trích, lý do; chọn qua lại chỉ hiện trích dẫn của mục đang chọn |
| E11 | Đạt | Mặc định "Chưa có căn cứ"; sửa Mục giữ Văn bản; xóa có hộp xác nhận |
| E12 | Đạt | Sao chép W → V: bản Nháp mở đúng, **không có dải lỗi**, bước S001..S003, nguồn lực đi theo bước |
| E13 | Đạt | Dòng thời gian: "thay đổi giá trị cho Số lượng từ 15 đến 20 ở hàng #1", "Mô tả từ … đến …" (trước/sau, người, thời điểm) |
| E14 | Đạt | Xóa S001 còn nguồn lực: hộp xác nhận rồi dải lỗi tiếng Việt, S001 còn nguyên |
| E15 | Đạt | Dải đỏ `role="alert"` "Không thể tìm thấy Dịch vụ kỹ thuật: …", không hộp thoại Desk |
| G1 | Đạt | NC Auditor mở bản Nháp: "Bạn chỉ có quyền xem quy trình này."; không còn nút ghi/tạo/sao chép; ô văn bản readonly |
| G2 | Đạt | Bản ban hành: chỉ đọc, không nút sửa |
| U1, U2 | Đạt | Biểu mẫu ở 1366×768 không cuộn ngang/chồng lấn; 100% tiếng Việt |
| K1, K2 | Đạt | Tab qua mọi điều khiển không kẹt; viền focus 2px ở 34/34 điều khiển |
| **K3** | **Đạt** | Bàn phím, 3 bước (W) và 2 bước (X): Enter trên "Xuống" ở bước đầu → tiêu điểm ở lại nút, Enter lần nữa chuyển tiếp được; bước giữa Lên/Xuống; bước cuối "Lên"; ở biên (nút vừa bấm bị khóa) tiêu điểm sang nút còn lại của cùng bước (ASM-064), không rơi về `BODY` |
| K4, K5 | Đạt | Enter mở biểu mẫu và lưu; Esc đóng biểu mẫu trích dẫn không lưu |
| **K6** | **Đạt** | Chỉ bàn phím, không tải lại trang: thêm nguồn lực (R003), nút "Xóa" không bị khóa, xóa qua hộp xác nhận bằng Enter; thêm trích dẫn bằng phím hiện đúng văn bản, mục, đoạn trích |
| C1 | Đạt | Nhãn quan hệ 5,42 / 5,44 / 5,36 (≥ 4,5) |
| C2–C5 | Đạt | 7,81 / 11,73 và 10,57 / placeholder 7,04 / nhãn trạng thái 7,81 |
| Console | Đạt | Không còn `TypeError: …finally is not a function` ở mọi luồng |

## Ghi chú không chặn nghiệm thu
- Khi xóa một dòng nguồn lực vừa thêm bằng bàn phím trong cùng phiên (không tải lại), console có một yêu cầu `delete_resource` lặp lại trả 417 ("Không thấy dòng nguồn lực R00N"); kết quả hiển thị đúng và không có dải lỗi. Nên điều tra ở FEAT sau (nghi hộp xác nhận Enter gọi hai lần); không trái FR/NFR.
- Hai tài khoản thử được đặt `language = vi` (ASM-099).
- Ngoài phạm vi: dữ liệu `THU-NORM16-*` còn trên staging (không ai có quyền xóa theo ma trận).
