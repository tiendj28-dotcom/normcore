# Bộ sửa đổi 1.1 — hợp nhất phân hệ E (cận lâm sàng) vào bộ tài liệu A–D

> 13/11/2026 · Trạng thái: **đã gộp xong vào các tệp gốc**. Thư mục này chỉ còn để đối chiếu.

## Đây là gì

Thư mục này chứa phần thêm và đổi của từng tài liệu khi phân hệ E được hợp nhất. Toàn bộ nội dung đã nằm trong các tệp gốc ở `docs/`, tất cả ở bản 1.1. **Không gộp lần nữa. Không dùng thư mục này để xây dựng.** Đọc `docs/README.md` để biết thứ tự đọc.

| Tệp ở đây | Đã gộp vào | Ghi chú |
| :-- | :-- | :-- |
| `data-model.md` | `docs/data-model.md` | 9 DocType mới, 10 bảng con mới, 15 DocType mở rộng, vai trò NC Auditor, DI-09 đến DI-17 |
| `use-cases.md` | `docs/use-cases.md` | UC-019 đến UC-026; phần sửa của UC-008 và UC-012 |
| `architecture-ux.md` | `docs/architecture.md`, `docs/ux-foundations.md`, `docs/design.md` | ADR-017, ADR-018, sửa ADR-007; SCR-DSK-032 đến 041 và 10 màn hình sửa; nhãn trạng thái mới |
| `implementation-plan.md` | `docs/implementation-plan.md` | FEAT-031 đến FEAT-039; mở rộng FEAT-009, 010, 011; thứ tự xây; rủi ro |
| `test-cases.md` | `docs/test-cases.md` | Thành mục 1.1, mục 2A và mục 3.8. Số mục đổi khi gộp: "2.1, 2.2" ở đây là "2A.1, 2A.2" ở tệp gốc; "3.1 đến 3.4" là "3.8.1 đến 3.8.4" |
| `golden_cls.py` | `docs/golden/golden_cls.py` | Giống hệt |
| `rtm.md` | `docs/rtm.md` | Tệp gốc được sinh lại cho cả 255 FR và 32 NFR; tệp ở đây chỉ có phần thêm và sửa |
| `tools-build-rtm-delta.py` | Không gộp | Thay bằng `docs/tools/build_rtm.py`, chạy trên các tệp gốc |

## Khác biệt có chủ ý giữa tệp gốc và tệp ở đây

- Tệp gốc dùng nhãn **[1.1]** tại chỗ thay cho các bảng "thêm" và "sửa" tách riêng.
- `docs/test-cases.md` có thêm kịch bản đầu cuối E2E-04 và ghi chú [1.1] ở TC-ACC-04, TC-RES-01, TC-RES-04, biến thể V2 của mục 2.3.
- `docs/test-cases.md` có thêm mục 3.9: 22 test case cho các yêu cầu mức Must của bản 1.0 chưa có test. Phần này không thuộc bộ sửa đổi phân hệ E.
- `docs/ux-foundations.md` có thêm câu hỏi mở UXQ-06 và hai thành phần giao diện (khối "k được tính thế nào", nhãn cấp phát sinh).
- `docs/design.md` có thêm mô tả các thành phần đó và quy ước hiển thị hệ số k.

## Kết quả kiểm tra sau khi gộp (13/11/2026)

Chạy `python3 docs/tools/build_rtm.py docs`: 0 vấn đề. Chi tiết ở `docs/verification-report.md`. Phần cũ của các tệp gốc được soạn lại nên cần xem `git diff` với bản 1.0 khi đưa vào kho mã.

## Việc còn mở

Xem `docs/README.md` mục "Việc cần chốt trước khi dev bắt đầu từng phần" và `docs/srs.md` Phụ lục B (TBD-14 đến TBD-18).
