# Normcore — Bộ tài liệu phân tích nghiệp vụ bàn giao cho đội phát triển

> Phiên bản 1.1 · 13/11/2026 · Trạng thái: sẵn sàng bàn giao cho đội phát triển; chờ chủ dự án và chuyên gia nghiệp vụ rà soát các điểm nêu ở mục "Việc cần chốt"
> Nền tảng: Frappe Framework v15, ứng dụng độc lập (không cần ERPNext)

Bộ tài liệu này đặc tả phần mềm Normcore từ yêu cầu đến kế hoạch xây dựng. Phạm vi của bản 1.1 là năm phân hệ A đến E. **Phân hệ E (định mức KTKT và giá thành khối cận lâm sàng) đã được hợp nhất vào mọi tài liệu:** tất cả các tệp dưới đây ở bản 1.1, phần thêm và sửa mang nhãn **[1.1]**. Không còn tài liệu nào phải đọc kèm bản sửa đổi.

Bộ tài liệu được lập theo quy trình của bộ skill `agentic-sdlc-kit` (requirements-engineering, software-architecture, ux-foundations, implementation-planning), với đầu vào là tài liệu "Normcore – Ý tưởng sản phẩm", tài liệu ý tưởng phân hệ E và các quyết định dưới đây. Chưa có phỏng vấn người dùng cuối; các giả định và câu hỏi mở được ghi rõ.

## Quyết định đã chốt (13/11/2026)

| Quyết định | Lựa chọn |
| :-- | :-- |
| Khuôn tài liệu | Bộ đầy đủ theo SDLC |
| Khách hàng đầu tiên | Bệnh viện công (kế toán hành chính, sự nghiệp) |
| Cách triển khai | Ứng dụng Frappe độc lập |
| Dịch vụ AI | Để mở, đổi nhà cung cấp bằng cấu hình |
| Phân hệ E | Hợp nhất vào bộ A–D; hóa sinh và miễn dịch làm cùng bản phát hành 1 |
| Kịch bản sản lượng mặc định | Thực tế 12 tháng |
| Hình thức có máy ở bệnh viện thí điểm | Máy mua và máy đặt theo hóa chất, kiểm thử ngang nhau |
| Phân bổ kiểm định, hiệu chuẩn | Mặc định theo giá trị tài sản; đổi được ở từng lần tính |
| Thiết bị hết thời gian khấu hao | Chọn ở bộ tham số: bằng 0 (mặc định) hoặc tiếp tục tính |
| 11 điểm xung đột X-01 đến X-11 | Chấp thuận theo đề xuất ở `phan-he-e-hop-nhat.md` mục 6 |

## Thứ tự đọc

| # | Tệp | Nội dung | Ai cần đọc |
| :-: | :-- | :-- | :-- |
| 1 | `srs.md` | Phạm vi, người dùng, 255 yêu cầu chức năng viết theo EARS (21 nhóm), 32 yêu cầu phi chức năng, 42 quy tắc tính giá và điều chỉnh, 18 câu hỏi mở (1 đã đóng) | Mọi người |
| 2 | `use-cases.md` | 26 use case có luồng chính, luồng thay thế, luồng lỗi; 4 sơ đồ | Dev, kiểm thử |
| 3 | `architecture.md` | Kiến trúc, sơ đồ ngữ cảnh và thành phần, cấu trúc mã, 18 ADR | Dev |
| 4 | `data-model.md` | Đặc tả 70 DocType, ma trận quyền 10 vai trò, luồng trạng thái, 17 ràng buộc toàn vẹn | Dev |
| 5 | `ux-foundations.md`, `design.md` | 41 màn hình, điều hướng, 4 luồng chính; quy ước giao diện theo Frappe Desk | Dev giao diện |
| 6 | `implementation-plan.md` | 39 tính năng trong 8 epic, thứ tự xây, lát cắt đầu tiên, nền kỹ thuật, Definition of Done, mẫu As-Built | Trưởng nhóm dev |
| 7 | `test-cases.md` | 192 test case, hai bộ dữ liệu vàng (mục 2 và mục 2A), 4 kịch bản đầu cuối. Mọi yêu cầu mức Must đều có ít nhất một test case | Dev, kiểm thử |
| 8 | `golden/golden_engine.py`, `golden/golden_cls.py` | Cài đặt tham chiếu chạy được của bộ máy tính giá và của phần cận lâm sàng; kết quả mong đợi trong `test-cases.md` lấy từ hai tệp này | Dev bộ máy tính giá |
| 9 | `rtm.md` | Ma trận truy vết: yêu cầu → use case → ADR → tính năng; phụ lục test case theo yêu cầu; phụ lục thay đổi ở 1.1 | Chủ dự án, kiểm thử |
| 10 | `verification-report.md` | Kết quả kiểm tra chéo của cả bộ ở bản 1.1 | Chủ dự án, trưởng nhóm dev |
| 11 | `phan-he-e-hop-nhat.md` | Vì sao và bằng cách nào phân hệ E được hợp nhất; 6 quyết định, 11 điểm xung đột. Viết trước khi gộp: chỗ nào nói "nằm ở `sua-doi-1.1/`" thì nay đã ở tệp gốc | Chủ dự án, trưởng nhóm dev |

Thư mục `sua-doi-1.1/` giữ các bản sửa đổi đã dùng để gộp. Chỉ để đối chiếu; **không gộp lần nữa và không dùng để xây dựng**. Xóa được sau khi đội phát triển đã xem diff.

## Đã kiểm gì, chưa kiểm gì

Đã kiểm bằng máy (`tools/build_rtm.py`, kết quả ở `verification-report.md`): mọi mã được dẫn đều tồn tại; 255/255 yêu cầu chức năng có use case và thuộc một tính năng hoặc nền kỹ thuật; 41/41 màn hình thuộc một tính năng; đồ thị phụ thuộc đủ 39 tính năng, không chu trình; thứ tự xây tôn trọng phụ thuộc; không yêu cầu nào của bản 1.0 bị mất hay bị bớt truy vết; 196/196 yêu cầu mức Must có test case.

Đã chạy ngày 13/11/2026:

- `golden/golden_engine.py` (cả biến thể `--no-depr`) và `golden/golden_cls.py`: chạy không lỗi; mọi số ở `test-cases.md` mục 2.2 và mục 2A khớp kết quả chạy. Biến thể V1, V2, V3, V5 của mục 2.3 và số của TC-COST-16 cũng khớp khi gọi các hàm của `golden_engine.py` với đầu vào đã đổi (V2, V3, V5, TC-COST-16 không có lệnh chạy sẵn; V4 là kiểm hành vi báo lỗi, không có số để so).
- Cả 17 sơ đồ Mermaid của bộ tài liệu được dựng hình thử bằng `mmdc` (mermaid-cli): không lỗi.

Chưa kiểm:

- **Câu chữ của phần cũ.** Các tệp bản 1.1 được soạn lại từ bản 1.0 rồi chèn phần thêm; công cụ chỉ so truy vết theo mã, không so từng câu. Khi đưa vào kho mã, xem `git diff` với bản 1.0: ngoài các chỗ mang nhãn [1.1], nội dung phải giống bản cũ.
- **Nghiệp vụ.** Chưa có chuyên gia định giá, kế toán hay khoa xét nghiệm nào rà các quy tắc tính. Test case ở `test-cases.md` mục 3.9 do BA viết từ câu chữ của yêu cầu, chưa có người dùng nghiệp vụ nào xem.

## Hệ thống mã

| Tiền tố | Nghĩa | Định nghĩa ở |
| :-- | :-- | :-- |
| `FR-<nhóm>-NNN` | Yêu cầu chức năng (21 nhóm; CLS, QC, CMP thêm ở 1.1) | srs.md mục 3.1 |
| `NFR-<loại>-NNN` | Yêu cầu phi chức năng | srs.md mục 3.3 |
| `BR-COST-NNN`, `BR-ADJ-NNN`, `BR-CLS-NNN` | Quy tắc tính giá, quy tắc điều chỉnh, quy tắc tính cho cận lâm sàng | srs.md mục 3.4 |
| `TBD-NN` | Câu hỏi mở | srs.md Phụ lục B |
| `UC-NNN` | Use case (001 đến 026) | use-cases.md |
| `ADR-NNN` | Quyết định kiến trúc (001 đến 018) | architecture.md mục 9 |
| `SCR-DSK-NNN` | Màn hình (001 đến 041) | ux-foundations.md |
| `FEAT-NNN` | Tính năng, lát cắt dọc (001 đến 039) | implementation-plan.md mục 3 |
| `TC-<nhóm>-NN` | Test case; test của phân hệ E và của yêu cầu sửa thuộc nhóm `CLS` | test-cases.md mục 3 |
| `DI-NN` | Ràng buộc toàn vẹn dữ liệu (01 đến 17) | data-model.md mục 6 |

Mã đã cấp không đổi và không tái sử dụng. Yêu cầu bị bỏ được đánh dấu `Removed`, không xóa dòng. Yêu cầu sửa giữ nguyên mã và ghi "Sửa ở 1.1".

## Bắt đầu từ đâu

1. Đưa thư mục `docs/` vào kho mã của app `normcore`; xem diff với bản 1.0 nếu đã có.
2. Chạy `python3 docs/golden/golden_engine.py`, `python3 docs/golden/golden_cls.py` và `python3 docs/tools/build_rtm.py docs`; cả ba phải chạy không lỗi.
3. Dựng walking skeleton và nền kỹ thuật theo `implementation-plan.md` mục 2 và mục 6.
4. Xây theo `implementation-plan.md` mục 4. Lát cắt đầu tiên là FEAT-006. Phần cận lâm sàng nằm ở các bước 5a, 7a, 8a, 9a.
5. Mỗi tính năng: thiết kế chi tiết, xây, chạy test case của tính năng, viết `docs/as-built/FEAT-NNN.md`, ghi cột Test ref trong `rtm.md`.

## Việc cần chốt trước khi dev bắt đầu từng phần

| Mã | Việc | Ai chốt | Chặn |
| :-- | :-- | :-- | :-- |
| TBD-02 | Xác nhận công thức tích lũy và nghĩa vụ tài chính (BR-COST-013) | Tài chính kế toán | FEAT-015 |
| TBD-01 | Lấy mẫu biểu chính thức Phụ lục I đến V Thông tư 21/2024/TT-BYT | BA nghiệp vụ | FEAT-019, FEAT-026 |
| TBD-03 | Xây bảng ánh xạ tài khoản theo Thông tư 24/2024/TT-BTC | Tài chính kế toán | FEAT-016 |
| TBD-05 | Danh sách loại giá và cấp phê duyệt | BA nghiệp vụ | FEAT-011, FEAT-030 |
| TBD-06 | Bệnh viện và chuyên khoa thí điểm; cần một máy mua và một máy đặt | Chủ dự án | Nghiệm thu R1 |
| TBD-14 | Loại chi phí kế toán của phí ngoại kiểm, tiền thuê máy, hợp đồng liên doanh liên kết; tiền thuê có tính ở loại giá không kết cấu khấu hao không | Tài chính kế toán | Nghiệm thu FEAT-037 |
| TBD-15 | Vật liệu nội kiểm dùng chung chia đều hay theo sản lượng | Khoa xét nghiệm thí điểm, BA nghiệp vụ | Nghiệm thu FEAT-036 |
| TBD-16 | LIS có xuất được số test nội kiểm, chuẩn máy, chạy lại không | Bệnh viện thí điểm | Không chặn; có đường ước tính |
| TBD-17 | Dịch vụ bộ tính theo bộ hay theo thông số | BA nghiệp vụ | FR-SVC-010 (mức Should) |
| TBD-18 | Văn bản hiện hành về kiểm định, hiệu chuẩn, an toàn bức xạ; danh sách loại thiết bị bắt buộc có hồ sơ | BA nghiệp vụ | Không chặn; là dữ liệu cấu hình |
| Rà soát thiết kế | Bốn lựa chọn của BA: nội kiểm, chất chuẩn, ngoại kiểm tính từ kế hoạch chất lượng (không phải dòng định mức); dịch vụ cận lâm sàng thiếu sản lượng thì dừng tính; sản lượng cận lâm sàng là DocType riêng; ngưỡng đối soát sản lượng 2% | Chủ dự án | Trước FEAT-034 |
| Rà soát quy tắc | BR-COST-001 đến 016 và BR-CLS-001 đến 017 với văn bản gốc và thực tế bệnh viện | Chuyên gia định giá, kế toán, khoa xét nghiệm | Trước FEAT-015 và FEAT-036 |

Các câu hỏi mở khác xem `srs.md` Phụ lục B. Các quy tắc BR-COST và BR-CLS là thiết kế của Normcore dựa trên cấu trúc của Thông tư 21/2024/TT-BYT ở mức đã đối chiếu được (Điều 1 đến 8, Phụ lục I đến III); chúng chưa được chuyên gia xác nhận.

## Cách duy trì

- Sửa yêu cầu: sửa `srs.md` theo quy tắc mã bất biến, tăng phiên bản, ghi lịch sử sửa đổi, rồi cập nhật use case, kế hoạch và test case liên quan.
- Sau mỗi lần sửa tài liệu nguồn: chạy `python3 docs/tools/build_rtm.py docs` để sinh lại `rtm.md` và `verification-report.md`. Không sửa tay hai tệp này. Script được viết lại ở bản 1.1 (script của bản 1.0 không có trong kho tài liệu) và mang sẵn bảng đối chiếu với `rtm.md` 1.0.
- Mỗi tính năng khi đến lượt xây: bổ sung thiết kế chi tiết (hợp đồng API, migration) và thiết kế màn hình cho tính năng đó; khi nghiệm thu, viết `docs/as-built/FEAT-NNN.md` và ghi cột Test ref trong `rtm.md`.
- Bộ nháp `claude/normcore-phan-he-e/` (DocType tiền tố `CLS`) là tài liệu nguồn của bản 1.1, không dùng để xây dựng.
