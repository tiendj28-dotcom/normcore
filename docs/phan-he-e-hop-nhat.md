# Phương án hợp nhất Phân hệ E vào bộ tài liệu A–D (giải quyết TBD-13)

> Phiên bản 1.0 · 13/11/2026 · Trạng thái: chủ dự án đã chấp thuận cả 11 đề xuất ở mục 6 ngày 13/11/2026. `docs/srs.md` đã lên bản 1.1 theo phương án này (thêm 76 FR, sửa 9 FR, sửa BR-COST-004, thêm BR-CLS-001 đến 017, đóng TBD-13). **Cập nhật sau khi gộp (13/11/2026):** mọi tài liệu của bộ A–D đã ở bản 1.1 và đã chứa phần của phân hệ E; `docs/sua-doi-1.1/` chỉ còn để đối chiếu. Tài liệu này là bản ghi quyết định, viết trước khi gộp. Khi gộp có hai chỗ làm khác bảng ánh xạ mục 4 dưới đây (sản lượng cận lâm sàng là DocType riêng; nội kiểm, chất chuẩn, ngoại kiểm không là dòng định mức), lý do ghi trong `sua-doi-1.1/data-model.md` mục 1.
> Đầu vào: `docs/srs.md` 1.0 và `docs/data-model.md` 1.0 (phân hệ A–D); bộ nháp Phân hệ E ở `claude/normcore-phan-he-e/`.

## 1. Kết luận

Phân hệ E được hợp nhất bằng cách **mở rộng chuỗi B–C sẵn có** (quy trình → bộ định mức → lần tính giá), không dựng một chuỗi song song. Bộ nháp Phân hệ E (123 FR, 35 DocType tiền tố `CLS`) trở thành tài liệu nguồn cho bản sửa đổi; nó không được đưa vào repo như một bộ độc lập vì trùng mã yêu cầu và trùng chức năng DocType với bộ A–D.

## 2. Quyết định đã chốt ngày 13/11/2026

| # | Quyết định | Lựa chọn |
| :-- | :-- | :-- |
| 1 | Cách xử lý Phân hệ E | Hợp nhất vào bộ A–D |
| 2 | Thời điểm | E cho hóa sinh và miễn dịch làm cùng R1 |
| 3 | Kịch bản sản lượng mặc định | Thực tế 12 tháng |
| 4 | Hình thức có máy ở bệnh viện thí điểm | Máy mua và máy đặt ngang nhau; kiểm thử ưu tiên như nhau |
| 5 | Phân bổ kiểm định, hiệu chuẩn | Mặc định theo giá trị tài sản (Phụ lục III TT 21), đổi được sang gắn trực tiếp thiết bị ở từng lần tính |
| 6 | Thiết bị hết thời gian khấu hao | Cho chọn ở từng lần tính: bằng 0 hoặc tiếp tục tính hao mòn |

Các quyết định có từ trước vẫn giữ: bệnh viện công, ứng dụng Frappe độc lập, AI đổi nhà cung cấp bằng cấu hình.

## 3. Nguyên tắc hợp nhất

- Một hệ mã, một mô hình dữ liệu, một bộ máy tính giá (ADR-003), một cơ chế ảnh chụp (ADR-004).
- Dịch vụ cận lâm sàng vẫn đi qua quy trình đã ban hành rồi mới có bộ định mức (FR-NORM-002). Ba công đoạn tiền phân tích, phân tích, hậu phân tích là các bước của quy trình.
- Bốn cấp phát sinh đầu của E (theo test, theo mẻ, theo ngày-máy, theo kỳ) là chi phí trực tiếp tính từ định mức. “Cấp 5” của E bị bỏ: chi phí chung của khoa và toàn viện đi theo phân bổ cấp 1 và cấp 2 sẵn có (BR-COST-010, BR-COST-011).
- Đối soát tài chính của E chính là BR-COST-015. E chỉ thêm đối soát vật chất (với xuất kho) và đối soát sản lượng (LIS, RIS với HIS).
- Mã đã cấp trong SRS 1.0 không đổi. Yêu cầu của E nhận mã mới: nối tiếp trong nhóm sẵn có khi mở rộng nhóm đó, hoặc thuộc ba nhóm mới CLS, QC, CMP.

## 4. Ánh xạ mô hình dữ liệu

| DocType trong bộ nháp E | Xử lý | DocType đích trong bộ A–D |
| :-- | :-- | :-- |
| CLS Department | Bỏ, dùng lại | NC Department (đã có loại Cận lâm sàng) |
| CLS Service, CLS Technical Catalog | Bỏ, mở rộng | NC Technical Service: thêm nhóm chuyên ngành CLS, đơn vị kết quả, cờ dịch vụ bộ, cờ gửi ngoài |
| CLS Service Code Map, CLS Panel Component | Thêm mới | NC Service Code Map, NC Panel Component (bảng con của NC Technical Service) |
| CLS Equipment, CLS Equipment Type | Bỏ, mở rộng | NC Equipment: thêm hình thức có máy, tiền thuê kỳ, tiêu chí chia, công suất điện chạy và chờ, loại thiết bị |
| CLS Equipment Component, CLS Equipment Allocation | Thêm mới | NC Equipment Component, NC Equipment Allocation (bảng con của NC Equipment) |
| CLS Compliance Record | Thêm mới | NC Equipment Compliance; thay cho trường `annual_calibration_cost` khi có bản ghi |
| CLS Item | Bỏ, mở rộng | NC Item: thêm loại Chất chuẩn và Vật liệu nội kiểm, số đơn vị định mức mỗi đơn vị mua, số test danh nghĩa, hạn dùng sau mở |
| CLS Price Source | Bỏ, mở rộng | NC Item Price: thêm nguồn Hợp đồng, hiệu lực đến, trạng thái xác minh |
| CLS Test System | Thêm mới | NC Test System |
| CLS QC Plan, CLS EQA Program, CLS EQA Service | Thêm mới | NC QC Plan, NC EQA Program, NC EQA Service |
| CLS Job Title Cost | Bỏ, dùng lại | NC Job Title, NC Job Title Rate trong bộ tham số |
| CLS Time Study | Bỏ, dùng lại | NC Time Study (theo bước, lấy trung vị) |
| CLS Cost Item, CLS Cost Component | Bỏ | Cấu phần của NC Norm Line và loại chi phí BR-COST-008 |
| CLS Norm Template | Thêm mới | NC Norm Template (mẫu dòng định mức theo nhóm chuyên ngành) |
| CLS Norm Sheet, CLS Norm Line | Bỏ, mở rộng | NC Norm Set: thêm hệ thống xét nghiệm, số xét nghiệm mỗi ống. NC Norm Line: thêm cấp phát sinh, cờ nhân hệ số k, cờ nhà cung cấp chịu |
| CLS Volume Period | Bỏ, mở rộng | NC Service Volume: thêm kịch bản, hệ thống xét nghiệm, số test nội kiểm, chuẩn, chạy lại, ngoại kiểm, tỷ lệ hao hụt, cỡ mẻ, phút khai thác máy |
| CLS Stock Issue Actual | Thêm mới | NC Stock Issue Actual |
| CLS Department Cost Actual, CLS Overhead Rate | Bỏ | NC Accounting Import và NC Allocation Rule |
| CLS Cost Run, CLS Cost Result, CLS Cost Result Line | Bỏ, mở rộng | NC Costing Run: thêm kịch bản sản lượng, cách phân bổ kiểm định hiệu chuẩn, cách tính thiết bị hết khấu hao. NC Service Cost, NC Service Cost Line: thêm hệ số k, hệ thống xét nghiệm |
| CLS Reconciliation Line | Bỏ, mở rộng | NC Reconciliation Line: thêm loại đối soát Vật chất và Sản lượng |
| CLS Settings, CLS Rule Setting | Bỏ, mở rộng | NC Settings: ngưỡng đối soát vật chất, số ngày nhắc hạn hồ sơ |
| CLS AI Request Log, CLS Import Log | Bỏ, dùng lại | NC AI Log, NC Audit Event |

Kết quả: bộ A–D thêm khoảng 11 DocType mới và mở rộng 10 DocType; không còn DocType tiền tố `CLS`.

## 5. Ánh xạ vai trò và nhóm yêu cầu

| Vai trò trong bộ nháp E | Vai trò trong bộ A–D |
| :-- | :-- |
| Chuyên viên định giá, Kế toán | NC Finance |
| Nhân viên khoa | NC Clinician (kỹ thuật viên khoa cận lâm sàng) |
| Trưởng khoa | NC Department Head |
| Cán bộ thiết bị | NC Resource Manager |
| Người duyệt | NC Director |
| Quản trị | NC Admin |
| Kiểm soát | Chưa có vai trò tương ứng; xem mục 6 |

| Nhóm FR của bộ nháp E | Đích trong SRS 1.1 | Ghi chú |
| :-- | :-- | :-- |
| SVC (7) | FR-SVC-008 trở đi, nhóm mới CLS | Hồ sơ dịch vụ, chặn trùng, ngừng dùng đã có ở SRS 1.0 |
| EQP (9), CMP (5) | FR-RES-016 trở đi, nhóm mới CMP | Sửa FR-RES-005, FR-RES-007 |
| SYS (6), QC (6) | Nhóm mới CLS và QC | Yêu cầu mới hoàn toàn |
| PRC (8) | FR-RES-016 trở đi | Phần lớn đã có ở FR-RES-001..004, 012, 014 |
| LAB (4) | Không thêm | Đã có ở FR-RES-010, FR-TS-001..005 |
| NRM (11) | FR-NORM-017 trở đi | Mẫu định mức, cấp phát sinh, số xét nghiệm mỗi ống, chống trùng nội kiểm |
| AI (8) | FR-AI-016 trở đi | Chỉ thêm việc AI đề xuất dòng định mức từ tài liệu hãng; phần còn lại đã có ở FR-AI-008..011 |
| VOL (8) | FR-ACCT-012 trở đi | Kịch bản sản lượng, số test phụ, xuất kho thực tế |
| CST (15), REC (6) | FR-COST-017 trở đi, quy tắc BR-CLS | Hệ số k, quy đổi theo mẻ, ngày, kỳ; đối soát vật chất và sản lượng |
| APR (6) | Không thêm | Khóa bộ định mức, khóa lần tính và duyệt phương án giá đã có ở FR-NORM-011, FR-COST-011, nhóm PRICE |
| RPT (8) | FR-OUT-011 trở đi | Báo cáo hạn hồ sơ, báo cáo thiếu dữ liệu; bảng giải trình đã có |
| IMP (5), SEC (4), AUD (3), INT (4) | Hầu như không thêm | Đã có ở FR-RES-012, FR-ADM-002, nhóm ACC, nhóm AUD; E không còn là phân hệ tách rời nên bỏ INT |

Ước lượng: khoảng 75 đến 85 yêu cầu mới, 6 đến 8 yêu cầu của SRS 1.0 bị sửa, 16 quy tắc tính của E chuyển thành BR-CLS-001 trở đi. Use case mới đánh số từ UC-019, màn hình từ SCR-DSK-032, tính năng từ FEAT-031, test case nhóm TC-CLS.

## 6. Điểm xung đột cần chủ dự án xác nhận

| Mã | Xung đột | Đề xuất |
| :-- | :-- | :-- |
| X-01 | Chọn đơn giá: SRS 1.0 lấy đơn giá có hiệu lực gần nhất (FR-RES-004); bộ nháp E ưu tiên theo loại nguồn | Sửa FR-RES-004: ưu tiên loại nguồn (trúng thầu, hợp đồng, hóa đơn, giá công bố, báo giá), cùng loại lấy bản gần nhất. Lý do: một báo giá mới không nên thay giá trúng thầu còn hiệu lực |
| X-02 | Bộ định mức: SRS 1.0 mỗi (dịch vụ, khoa) một bộ (DI-03); E cần một bộ cho mỗi hệ thống xét nghiệm | Sửa DI-03 thành (dịch vụ, khoa, hệ thống xét nghiệm); giá thành dịch vụ là bình quân gia quyền theo tỷ trọng |
| X-03 | Kiểm định, hiệu chuẩn: SRS 1.0 đưa vào đơn giá giờ máy của từng thiết bị (BR-COST-004); quyết định 5 chọn mặc định theo giá trị tài sản | Sửa BR-COST-004: thêm tham số cách phân bổ ở lần tính, mặc định theo giá trị tài sản, áp cho mọi thiết bị của Normcore chứ không riêng cận lâm sàng |
| X-04 | Thiết bị hết khấu hao: SRS 1.0 luôn bằng 0 (FR-RES-007); quyết định 6 cho chọn | Sửa FR-RES-007 và BR-COST-004: thêm tham số trong bộ tham số tính giá, mặc định bằng 0 |
| X-05 | Chia chi phí máy: SRS 1.0 theo giờ khai thác kế hoạch và hệ số sử dụng; E theo số kết quả thực tế hoặc phút chiếm máy thực tế | Giữ cách của SRS 1.0 cho thiết bị lâm sàng; thiết bị cận lâm sàng có thêm tiêu chí Số kết quả. Mỗi thiết bị một tiêu chí |
| X-06 | Ba kịch bản sản lượng: SRS 1.0 có một sản lượng cho mỗi dịch vụ, khoa, năm | Mỗi lần tính dùng một kịch bản; xem ba kịch bản bằng so sánh lần tính (FR-COST-013). Sản lượng đổi thì phân bổ cấp 2 cũng đổi theo |
| X-07 | Làm tròn: SRS 1.0 đơn giá 4 chữ số, thành tiền 2 chữ số; bộ nháp E giữ 6 chữ số | Theo SRS 1.0; riêng hệ số k giữ 6 chữ số. Tính lại 16 vector kiểm thử theo quy ước này |
| X-08 | Ngưỡng đối soát: SRS 1.0 mặc định 10%; bộ nháp E 5% | Theo SRS 1.0 cho đối soát tài chính; đối soát vật chất có ngưỡng riêng, mặc định 5% |
| X-09 | Phiên bản: SRS 1.0 tạo bản ghi phiên bản mới, không dùng amend; bộ nháp E dùng amend | Theo SRS 1.0 |
| X-10 | Vai trò Kiểm soát (chỉ đọc toàn bộ) | Thêm vai trò NC Auditor; sửa FR-ACC-002 từ 9 lên 10 vai trò |
| X-11 | Nguồn gửi AI: ADR-007 chỉ cho phép mục văn bản, quy trình, danh mục, bảng giá công khai | Thêm tài liệu hướng dẫn sử dụng của hãng vào danh sách cho phép; cần sửa ADR-007 |

Bốn câu hỏi mở của bộ nháp E chưa trả lời và không chặn bản sửa đổi: LIS có xuất được số test nội kiểm, chuẩn, chạy lại không; dịch vụ bộ tính theo bộ hay theo thông số; ngoại kiểm xếp vào loại chi phí nào của BR-COST-008; vật liệu nội kiểm dùng chung chia đều hay theo sản lượng.

## 7. Ảnh hưởng đến các tài liệu đã có

| Tài liệu | Ảnh hưởng |
| :-- | :-- |
| srs.md | Lên 1.1: phạm vi mục 1.2 thêm phân hệ E; ba nhóm FR mới; FR nối tiếp ở 7 nhóm; sửa FR-RES-004, 005, 007, FR-ACC-002, BR-COST-004; thêm BR-CLS; đóng TBD-13 |
| use-cases.md | Thêm khoảng 6 use case từ UC-019; sửa use case khai báo thiết bị và chạy tính giá |
| data-model.md | Theo mục 4; sửa DI-03, DI-05 |
| architecture.md | ADR mới cho mô hình cận lâm sàng trong bộ máy tính giá; sửa ADR-007; rà ADR-003, ADR-004 |
| ux-foundations.md, design.md | Màn hình mới: hệ thống xét nghiệm, kế hoạch chất lượng, hồ sơ tuân thủ, đối soát vật chất |
| implementation-plan.md | FEAT-010, FEAT-012, FEAT-015 mở rộng; thêm tính năng từ FEAT-031; R1 lớn hơn |
| test-cases.md, golden_engine.py | Nhóm TC-CLS; đưa 16 vector vào bộ dữ liệu vàng; test đã có của BR-COST-004 phải cập nhật |
| rtm.md, verification-report.md | Sinh lại bằng công cụ của bộ A–D |

## 8. Các bước tiếp theo

1. Chủ dự án xác nhận hoặc sửa mục 6.
2. Lập bản sửa đổi SRS 1.1: bảng FR mới, các dòng bị sửa, BR-CLS, lịch sử sửa đổi.
3. Cập nhật use case và mô hình dữ liệu.
4. Cập nhật kiến trúc, UX, kế hoạch, test case và bộ dữ liệu vàng; sinh lại RTM.
5. Đánh dấu bộ nháp `claude/normcore-phan-he-e/` là đã thay thế.

Bộ A–D hiện chỉ sửa được bằng cách ghi lại toàn bộ tệp. Bước 2 đến 4 nên chạy trong repo bằng Claude Code để vá từng tệp và chạy `build_rtm.py`; nếu làm trong phiên trò chuyện, mỗi tệp phải viết lại toàn bộ.
