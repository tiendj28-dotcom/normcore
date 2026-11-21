# Verification Report: bộ tài liệu Normcore

> Sinh bởi `docs/tools/build_rtm.py` ngày 2026-11-21 cho bản 1.1. Kiểm tra cơ học về ID và cấu trúc; không thay cho rà soát nghiệp vụ.

## Số lượng

| Hạng mục | Số lượng | Bản 1.0 |
| :-- | --: | --: |
| Yêu cầu chức năng (FR) | 255 | 179 |
| trong đó mức Must / Should / Could | 196 / 54 / 5 | 146 / 30 / 3 |
| Nhóm chức năng | 21 | 18 |
| Yêu cầu phi chức năng (NFR) | 32 | 30 |
| Quy tắc nghiệp vụ (BR) | 42 | 25 |
| Use case | 26 | 18 |
| ADR | 18 | 16 |
| Màn hình (SCR) | 41 | 31 |
| Tính năng (FEAT) | 39 | 30 |
| Test case | 192 | 119 |
| Câu hỏi mở (TBD), kể cả câu đã đóng | 18 | 13 |

## Kết quả kiểm tra

| Kiểm tra | Kết quả |
| :-- | :-- |
| Mọi ID được dẫn (FR, NFR, BR, UC, ADR, SCR, FEAT, TC, TBD) đều tồn tại ở tài liệu định nghĩa | Đạt |
| Không mã nào bị định nghĩa trùng | Đạt |
| Mọi FR có ít nhất một use case | Đạt |
| Mọi FR mức Must thuộc một tính năng hoặc nền kỹ thuật | Đạt |
| Mọi FR (kể cả Should, Could) đã có Plan ref | Đạt |
| Mọi màn hình thuộc ít nhất một tính năng | Đạt |
| Đồ thị phụ thuộc: đủ 39 tính năng, không chu trình | Đạt |
| Thứ tự xây tôn trọng phụ thuộc; lát cắt đầu tiên ở bước 1 | Đạt |
| Khối Mermaid (17 khối): đóng đủ, nhãn có khoảng trắng nằm trong ngoặc kép, không có nút tên end | Đạt |
| Không yêu cầu nào của bản 1.0 bị mất hoặc bị bớt truy vết (use case, ADR, tính năng) so với `rtm.md` 1.0 | Đạt |
| Mọi yêu cầu mới của bản 1.1 có use case (FR), tính năng, và test case nếu là Must | Đạt |

Script chỉ kiểm cú pháp cơ bản của Mermaid. Lần dựng hình thử gần nhất bằng `mmdc` (mermaid-cli): 13/11/2026, bản 1.1, 17 khối, không lỗi. Khi sửa sơ đồ, dựng hình thử lại và cập nhật dòng này trong script.

## Vấn đề cần sửa

Không có.

## Khoảng trống đã biết (không chặn bàn giao)

- FR mức Must chưa có test case dự kiến (0): không có.
- FR mức Should hoặc Could chưa có test case dự kiến (26): FR-ACC-006, FR-LIB-004, FR-LIB-011, FR-LIB-012, FR-SVC-005, FR-SVC-010, FR-SVC-011, FR-PROC-005, FR-PROC-011, FR-PROC-013, FR-AI-006, FR-AI-007, FR-AI-014, FR-WF-012, FR-WF-013, FR-RES-013, FR-NORM-014, FR-NORM-016, FR-ACCT-011, FR-BM-008, FR-ADJ-004, FR-ADJ-008, FR-OUT-003, FR-OUT-009, FR-OUT-010, FR-NOTI-002. Test case cho các FR này được viết khi tính năng tương ứng đến lượt xây.
- NFR chưa có ADR dẫn tới (9): NFR-PERF-001, NFR-PERF-003, NFR-SCAL-001, NFR-SCAL-002, NFR-SEC-002, NFR-USE-004, NFR-MNT-002, NFR-LOC-001, NFR-OBS-002. Các NFR này được xử lý ở mục 8 và mục 10 của tài liệu kiến trúc hoặc ở nền kỹ thuật, không cần quyết định kiến trúc riêng.
- Câu hỏi mở ở Phụ lục B của SRS cần người có thẩm quyền chốt; trạng thái từng câu xem tại đó.
- Các tệp bản 1.1 (`srs.md`, `data-model.md`, `use-cases.md`, `architecture.md`, `ux-foundations.md`, `design.md`, `implementation-plan.md`, `test-cases.md`) được soạn lại từ bản 1.0 rồi chèn phần thêm. Script này chỉ so được truy vết theo mã với `rtm.md` 1.0; nó không so từng câu chữ. Khi đưa vào kho mã, nên `git diff` với bản 1.0 để xác nhận phần cũ không đổi ngoài các chỗ mang nhãn [1.1].

## Ghi chú

Các dòng dưới đây không phải lỗi: test case được đặt ở tính năng nơi yêu cầu được kiểm bằng số liệu (thường là tính năng tính giá), còn yêu cầu thuộc tính năng khai báo dữ liệu. Khi lập As-Built, ghi mã test case ở cả hai tính năng.

- TC-COST-14: FR-COST-015 không thuộc FEAT-017 (thuộc FEAT-015)
- TC-OUT-03: FR-AUD-004 không thuộc FEAT-019 (thuộc FEAT-003)
- TC-CLS-03: FR-NORM-019 không thuộc FEAT-036 (thuộc FEAT-034)
- TC-CLS-07: FR-RES-021 không thuộc FEAT-036 (thuộc FEAT-010)
- TC-CLS-09: FR-RES-023 không thuộc FEAT-036 (thuộc FEAT-010)
- TC-CLS-09: FR-RES-026 không thuộc FEAT-036 (thuộc FEAT-010)
- TC-CLS-11: FR-RES-007 không thuộc FEAT-036 (thuộc FEAT-010)
- TC-CLS-12: FR-RES-020 không thuộc FEAT-036 (thuộc FEAT-010)
- TC-CLS-13: FR-CLS-005 không thuộc FEAT-036 (thuộc FEAT-031)
- TC-CLS-13: FR-RES-022 không thuộc FEAT-036 (thuộc FEAT-010)
- TC-CLS-14: FR-COST-007 không thuộc FEAT-036 (thuộc FEAT-015)
- TC-CLS-37: FR-CMP-006 không thuộc FEAT-036 (thuộc FEAT-033)
