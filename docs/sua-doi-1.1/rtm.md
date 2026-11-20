# Sửa đổi 1.1 — Ma trận truy vết (bổ sung cho `docs/rtm.md` 1.0)

> Phiên bản 1.1-delta · 13/11/2026 · Sinh bằng `docs/sua-doi-1.1/tools-build-rtm-delta.py` từ `docs/srs.md` 1.1 và các tệp trong `docs/sua-doi-1.1/`. Dòng FR-COST-014 có thêm ghi chú viết tay.
> Chỉ gồm yêu cầu **mới** và yêu cầu **sửa** ở bản 1.1. Các dòng khác của `docs/rtm.md` 1.0 giữ nguyên. Cột "Test ref" do bước nghiệm thu ghi.

## 1. Tóm tắt

| Chỉ số | Giá trị |
| :-- | --: |
| Yêu cầu chức năng mới | 76 |
| Yêu cầu phi chức năng mới | 2 |
| Yêu cầu chức năng sửa | 9 |
| Yêu cầu mới có use case | 76 / 76 |
| Yêu cầu mới có tính năng (FEAT) | 78 / 78 |
| Yêu cầu mới mức Must có test case | 50 / 50 |
| Use case mới, tính năng mới, test case mới | 8, 9, 51 |
| Lỗi kiểm tra chéo | 0 |

Cột "Design ref" là `_TBD_` ở các yêu cầu chỉ cần thiết kế chi tiết của tính năng, không cần quyết định kiến trúc; cách ghi này giống bản 1.0.

## 2. Yêu cầu mới

| Req ID | Requirement (short) | Priority | Thay đổi | Source | Use case(s) | Design ref | Plan ref | Test case | Test ref |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| FR-ACC-007 | Hệ thống phải cho vai trò NC Auditor quyền chỉ đọc đối với mọi bản ghi nghiệp… | Should | Mới | REF-08, REF-09 | UC-026 | _TBD_ | FEAT-039 | TC-CLS-44 | _TBD_ |
| FR-ACC-008 | Trong khi người dùng chỉ có vai trò NC Clinician hoặc NC Department Head, hệ… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-22 | _TBD_ |
| FR-ACCT-012 | Khi NC Finance nhập sản lượng, hệ thống phải yêu cầu kịch bản sản lượng của… | Must | Mới | REF-08, REF-09 | UC-022 | ADR-018 | FEAT-035 | TC-CLS-34 | _TBD_ |
| FR-ACCT-013 | Khi NC Finance nhập tệp sản lượng cận lâm sàng theo mẫu, hệ thống phải lưu… | Must | Mới | REF-08, REF-09 | UC-022 | ADR-012, ADR-018 | FEAT-035 | TC-CLS-34 | _TBD_ |
| FR-ACCT-014 | Nếu tệp sản lượng cận lâm sàng có mã dịch vụ, mã khoa hoặc mã hệ thống xét… | Must | Mới | REF-08, REF-09 | UC-022 | ADR-018 | FEAT-035 | TC-CLS-35 | _TBD_ |
| FR-ACCT-015 | Khi NC Finance nhập tệp xuất kho thực tế theo mẫu, hệ thống phải lưu lượng… | Must | Mới | REF-08, REF-09 | UC-022 | ADR-012, ADR-018 | FEAT-035 | TC-CLS-36 | _TBD_ |
| FR-ADM-006 | Khi NC Admin thay đổi số ngày nhắc hạn hồ sơ tuân thủ hoặc danh sách loại… | Should | Mới | REF-08, REF-09 | UC-020 | _TBD_ | FEAT-033 | TC-CLS-28 | _TBD_ |
| FR-AI-016 | Khi người dùng yêu cầu AI đề xuất định mức cho một hệ thống xét nghiệm, hệ… | Should | Mới | REF-08, REF-09 | UC-025 | ADR-007 | FEAT-038 | TC-CLS-41 | _TBD_ |
| FR-AI-017 | Khi AI trả một đề xuất định mức, hệ thống phải gắn cho đề xuất đó trích dẫn… | Should | Mới | REF-08, REF-09 | UC-025 | ADR-007 | FEAT-038 | TC-CLS-42 | _TBD_ |
| FR-AI-018 | Nếu AI đề xuất một mặt hàng hoặc thiết bị không có trong danh mục, thì hệ… | Should | Mới | REF-08, REF-09 | UC-025 | _TBD_ | FEAT-038 | TC-CLS-43 | _TBD_ |
| FR-CLS-001 | Khi người dùng tạo một hệ thống xét nghiệm, hệ thống phải yêu cầu mã, dịch… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-20 | _TBD_ |
| FR-CLS-002 | Hệ thống phải cho phép một dịch vụ trong một khoa có nhiều hệ thống xét… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-20 | _TBD_ |
| FR-CLS-003 | Nếu tổng tỷ trọng sản lượng của các hệ thống xét nghiệm đang dùng của một… | Must | Mới | REF-08, REF-09 | UC-012 | _TBD_ | FEAT-036 | TC-CLS-15 | _TBD_ |
| FR-CLS-004 | Khi sản lượng của kịch bản được chọn có số kết quả trả theo từng hệ thống xét… | Should | Mới | REF-08, REF-09 | UC-012 | ADR-018 | FEAT-036 | TC-CLS-10 | _TBD_ |
| FR-CLS-005 | Khi người dùng tạo hệ thống xét nghiệm có thiết bị chính chia chi phí theo… | Should | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-13 | _TBD_ |
| FR-CLS-006 | Trong khi một hệ thống xét nghiệm được đánh dấu ngừng dùng, hệ thống phải… | Should | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-23 | _TBD_ |
| FR-CLS-007 | Khi người dùng mở một hệ thống xét nghiệm, hệ thống phải hiển thị bộ định mức… | Should | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-20 | _TBD_ |
| FR-CLS-008 | Khi người dùng nhập từ tệp Excel mẫu các hệ thống xét nghiệm, kế hoạch chất… | Should | Mới | REF-08, REF-09 | UC-019 | ADR-012 | FEAT-031 | TC-CLS-23 | _TBD_ |
| FR-CMP-001 | Khi NC Resource Manager tạo hồ sơ tuân thủ cho một thiết bị, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-020 | _TBD_ | FEAT-033 | TC-CLS-27 | _TBD_ |
| FR-CMP-002 | Khi lần tính giá chạy, hệ thống phải quy chi phí của mỗi hồ sơ tuân thủ còn… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-07 | _TBD_ |
| FR-CMP-003 | Khi lần tính giá dùng cách phân bổ Theo giá trị tài sản, hệ thống phải gom… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-07 | _TBD_ |
| FR-CMP-004 | Khi lần tính giá dùng cách phân bổ Gắn trực tiếp thiết bị, hệ thống phải lấy… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-08 | _TBD_ |
| FR-CMP-005 | Khi một hồ sơ tuân thủ còn không quá số ngày cấu hình đến ngày hết hạn, hệ… | Should | Mới | REF-08, REF-09 | UC-020 | _TBD_ | FEAT-033 | TC-CLS-28 | _TBD_ |
| FR-CMP-006 | Nếu một thiết bị thuộc loại bắt buộc có hồ sơ tuân thủ mà không có hồ sơ còn… | Must | Mới | REF-08, REF-09 | UC-012 | _TBD_ | FEAT-033 | TC-CLS-37 | _TBD_ |
| FR-CMP-007 | Khi người dùng mở báo cáo hồ sơ tuân thủ, hệ thống phải liệt kê theo khoa các… | Should | Mới | REF-08, REF-09 | UC-020 | _TBD_ | FEAT-033 | TC-CLS-28 | _TBD_ |
| FR-COST-017 | Khi NC Finance tạo một lần tính giá, hệ thống phải yêu cầu kịch bản sản lượng… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-018 | FEAT-036 | TC-CLS-08 | _TBD_ |
| FR-COST-018 | Khi lần tính giá chạy, hệ thống phải tính hệ số tiêu hao k của từng hệ thống… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-01, TC-CLS-02 | _TBD_ |
| FR-COST-019 | Khi lần tính giá chạy, hệ thống phải tính chi phí cho một kết quả của từng… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-03, TC-CLS-04, TC-CLS-05 | _TBD_ |
| FR-COST-020 | Khi lần tính giá chạy, hệ thống phải tính chi phí vật liệu nội kiểm, chất… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-06 | _TBD_ |
| FR-COST-021 | Khi lần tính giá chạy, hệ thống phải tính chi phí thiết bị của dịch vụ theo… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-07, TC-CLS-09 | _TBD_ |
| FR-COST-022 | Khi một dịch vụ trong một khoa có nhiều hệ thống xét nghiệm, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-10 | _TBD_ |
| FR-COST-023 | Nếu một hệ thống xét nghiệm thiếu sản lượng của kịch bản được chọn, có số kết… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-15 | _TBD_ |
| FR-COST-024 | Khi lần tính giá chạy cho dịch vụ có hệ thống xét nghiệm, hệ thống phải dùng… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017, ADR-018 | FEAT-036 | TC-CLS-51 | _TBD_ |
| FR-COST-025 | Nếu số test tiêu thụ của một hệ thống xét nghiệm trong thời hạn dùng sau mở… | Should | Mới | REF-08, REF-09 | UC-012 | _TBD_ | FEAT-036 | TC-CLS-37 | _TBD_ |
| FR-COST-026 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát vật chất theo khoa… | Must | Mới | REF-08, REF-09 | UC-023 | ADR-018 | FEAT-037 | TC-CLS-16 | _TBD_ |
| FR-COST-027 | Nếu chênh lệch phần trăm của một dòng đối soát vật chất vượt ngưỡng đối soát… | Must | Mới | REF-08, REF-09 | UC-023 | ADR-018 | FEAT-037 | TC-CLS-17 | _TBD_ |
| FR-COST-028 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát sản lượng so số… | Should | Mới | REF-08, REF-09 | UC-023 | ADR-018 | FEAT-037 | TC-CLS-18 | _TBD_ |
| FR-COST-029 | Nếu một khoa trong phạm vi không có số liệu xuất kho thực tế của năm tài… | Must | Mới | REF-08, REF-09 | UC-023 | ADR-018 | FEAT-037 | TC-CLS-19 | _TBD_ |
| FR-COST-030 | Khi người dùng mở phân tích độ nhạy của một dịch vụ, hệ thống phải tính lại… | Should | Mới | REF-08, REF-09 | UC-024 | _TBD_ | FEAT-037 | TC-CLS-40 | _TBD_ |
| FR-COST-031 | Khi người dùng mở bảng giải trình của một dịch vụ cận lâm sàng, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-38 | _TBD_ |
| FR-COST-032 | Khi NC Finance khóa một lần tính giá có dịch vụ cận lâm sàng, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-004 | FEAT-036 | TC-CLS-38 | _TBD_ |
| FR-LIB-013 | Khi NC Document Controller nạp tài liệu của hãng sản xuất (hướng dẫn sử dụng… | Should | Mới | REF-08, REF-09 | UC-025 | ADR-007 | FEAT-038 | TC-CLS-41 | _TBD_ |
| FR-NORM-017 | Ở nơi dịch vụ có hệ thống xét nghiệm, hệ thống phải gắn mỗi bộ định mức với… | Must | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-29, TC-CLS-33 | _TBD_ |
| FR-NORM-018 | Khi người dùng sửa một dòng định mức của dịch vụ cận lâm sàng, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-30 | _TBD_ |
| FR-NORM-019 | Khi người dùng khai một dòng thuốc, hóa chất hoặc vật tư có cấp phát sinh… | Must | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-03, TC-CLS-30 | _TBD_ |
| FR-NORM-020 | Nếu bộ định mức có dòng Theo ống mẫu mà chưa khai số xét nghiệm bình quân… | Must | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-32 | _TBD_ |
| FR-NORM-021 | Khi NC Finance hoặc NC Admin lập mẫu định mức cho một nhóm chuyên ngành, hệ… | Should | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-29 | _TBD_ |
| FR-NORM-022 | Khi người dùng khởi tạo bộ định mức cho dịch vụ thuộc nhóm chuyên ngành có… | Should | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-29 | _TBD_ |
| FR-NORM-023 | Nếu bộ định mức thiếu dòng cho một khoản mục bắt buộc của mẫu và người dùng… | Should | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-32 | _TBD_ |
| FR-NORM-024 | Nếu một dòng định mức dùng mặt hàng đã có trong kế hoạch nội kiểm hoặc kế… | Must | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-31 | _TBD_ |
| FR-NORM-025 | Khi người dùng sao chép bộ định mức từ một hệ thống xét nghiệm khác của cùng… | Could | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-33 | _TBD_ |
| FR-OUT-011 | Khi người dùng xuất bộ định mức của một hệ thống xét nghiệm, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-021 | _TBD_ | FEAT-034 | TC-CLS-33 | _TBD_ |
| FR-OUT-012 | Khi người dùng mở báo cáo thiếu dữ liệu của một phạm vi tính giá, hệ thống… | Must | Mới | REF-08, REF-09 | UC-024 | _TBD_ | FEAT-037 | TC-CLS-39 | _TBD_ |
| FR-QC-001 | Khi người dùng lập kế hoạch nội kiểm cho một hệ thống xét nghiệm, hệ thống… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-032 | TC-CLS-24 | _TBD_ |
| FR-QC-002 | Khi người dùng lập kế hoạch chuẩn máy cho một hệ thống xét nghiệm, hệ thống… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-032 | TC-CLS-24 | _TBD_ |
| FR-QC-003 | Khi người dùng khai một chương trình ngoại kiểm, hệ thống phải yêu cầu đơn vị… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-032 | TC-CLS-24 | _TBD_ |
| FR-QC-004 | Khi lần tính giá chạy, hệ thống phải chia phí của một chương trình ngoại kiểm… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-10 | _TBD_ |
| FR-QC-005 | Nếu tổng tỷ lệ riêng của các dịch vụ trong một chương trình ngoại kiểm khác… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-032 | TC-CLS-25 | _TBD_ |
| FR-QC-006 | Khi sản lượng của kịch bản được chọn không có số test nội kiểm, chuẩn máy,… | Must | Mới | REF-08, REF-09 | UC-012 | ADR-017 | FEAT-036 | TC-CLS-02 | _TBD_ |
| FR-QC-007 | Nếu một hệ thống xét nghiệm thuộc nhóm chuyên ngành xét nghiệm không có kế… | Should | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-032 | TC-CLS-26 | _TBD_ |
| FR-QC-008 | Nếu người dùng chọn cho kế hoạch nội kiểm một mặt hàng không thuộc loại Vật… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-032 | TC-CLS-25 | _TBD_ |
| FR-RES-016 | Khi người dùng xác minh một đơn giá, hệ thống phải yêu cầu tệp chứng từ đính… | Should | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-009 | TC-CLS-46 | _TBD_ |
| FR-RES-017 | Nếu một dòng chi phí dùng đơn giá chưa ở trạng thái "Đã xác minh", thì hệ… | Should | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-009 | TC-CLS-46 | _TBD_ |
| FR-RES-018 | Khi NC Resource Manager tạo mặt hàng loại hóa chất xét nghiệm, chất chuẩn… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-009 | TC-CLS-47 | _TBD_ |
| FR-RES-019 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu hình… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-48 | _TBD_ |
| FR-RES-020 | Trong khi hình thức có máy là Thuê hoặc Liên doanh, liên kết, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-12, TC-CLS-48 | _TBD_ |
| FR-RES-021 | Trong khi hình thức có máy là Đặt theo hóa chất, hệ thống phải tính khấu hao… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-07 | _TBD_ |
| FR-RES-022 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu tiêu chí… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-13, TC-CLS-48 | _TBD_ |
| FR-RES-023 | Khi người dùng khai linh kiện lớn của một thiết bị, hệ thống phải yêu cầu… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-09 | _TBD_ |
| FR-RES-024 | Khi một thiết bị dùng chung cho nhiều khoa, hệ thống phải lưu tỷ lệ phân bổ… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-49 | _TBD_ |
| FR-RES-025 | Nếu tổng tỷ lệ phân bổ theo khoa của một thiết bị khác 100%, thì hệ thống… | Must | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-49 | _TBD_ |
| FR-RES-026 | Khi NC Resource Manager khai báo một thiết bị cận lâm sàng, hệ thống phải cho… | Should | Mới | REF-08, REF-09 | UC-008 | _TBD_ | FEAT-010 | TC-CLS-09 | _TBD_ |
| FR-SVC-008 | Khi NC Document Controller đánh dấu một dịch vụ kỹ thuật thuộc khối cận lâm… | Must | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | TC-CLS-20 | _TBD_ |
| FR-SVC-009 | Khi người dùng khai mã của một dịch vụ trên HIS, LIS hoặc RIS, hệ thống phải… | Must | Mới | REF-08, REF-09 | UC-019, UC-022 | _TBD_ | FEAT-031 | TC-CLS-21 | _TBD_ |
| FR-SVC-010 | Ở nơi dịch vụ được đánh dấu là dịch vụ bộ, hệ thống phải lưu danh sách thông… | Should | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ | _TBD_ |
| FR-SVC-011 | Ở nơi dịch vụ được đánh dấu gửi ngoài, hệ thống phải lưu giá hợp đồng gửi… | Could | Mới | REF-08, REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ | _TBD_ |
| NFR-REL-003 | Hệ số tiêu hao k được tính bằng số thập phân chính xác và lưu với 6 chữ số… | Must | Mới | REF-08, REF-09 | — | ADR-017 | FEAT-036 | TC-CLS-01 | _TBD_ |
| NFR-CPL-003 | 100% dòng chi phí cận lâm sàng trong bảng giải trình hiển thị cấp phát sinh,… | Must | Mới | REF-08, REF-09 | — | ADR-017 | FEAT-036 | TC-CLS-38 | _TBD_ |

## 3. Yêu cầu sửa

Use case, tính năng và test case ở bảng này là phần **thêm** vào dòng tương ứng của `docs/rtm.md` 1.0.

| Req ID | Requirement (short) | Priority | Thay đổi | Source | Use case(s) | Design ref | Plan ref | Test case | Test ref |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| FR-ACC-002 | Hệ thống phải cung cấp 10 vai trò nêu ở mục 2.3 và áp quyền đọc, tạo, sửa,… | Must | Sửa | REF-09 | UC-026 | Như 1.0 | FEAT-039 | TC-CLS-44 | _TBD_ |
| FR-ACC-004 | Hệ thống phải chỉ cho phép vai trò NC Finance, NC Director, NC Admin và NC… | Must | Sửa | REF-09 | UC-026 | Như 1.0 | FEAT-039 | TC-CLS-44 | _TBD_ |
| FR-RES-002 | Khi người dùng thêm đơn giá cho một mặt hàng, hệ thống phải yêu cầu giá đã… | Must | Sửa | REF-09 | Như 1.0 | Như 1.0 | FEAT-009 | TC-CLS-46 | _TBD_ |
| FR-RES-004 | Khi một mặt hàng có nhiều đơn giá còn hiệu lực tại ngày tính giá, hệ thống… | Must | Sửa | REF-09 | Như 1.0 | Như 1.0 | FEAT-009 | TC-CLS-45 | _TBD_ |
| FR-RES-005 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu ngày đưa… | Must | Sửa | REF-09 | Như 1.0 | Như 1.0 | FEAT-010 | TC-CLS-48 | _TBD_ |
| FR-RES-007 | Nếu thiết bị đã hết thời gian sử dụng tính đến ngày tính giá, thì hệ thống… | Must | Sửa | REF-09 | Như 1.0 | Như 1.0 | FEAT-010 | TC-CLS-11 | _TBD_ |
| FR-RES-009 | Khi NC Finance tạo bộ tham số tính giá, hệ thống phải yêu cầu ngày hiệu lực… | Must | Sửa | REF-09 | Như 1.0 | Như 1.0 | FEAT-011 | TC-CLS-50 | _TBD_ |
| FR-COST-014 | Nếu sản lượng của một dịch vụ bằng 0 hoặc thiếu, thì hệ thống phải không phân… | Must | Sửa | REF-09 | Như 1.0 | Như 1.0 | Như 1.0 | Như 1.0 (chỉ sửa ghi chú; ngoại lệ kiểm ở TC-CLS-15) | _TBD_ |
| FR-AUD-003 | Khi NC Admin, NC Director hoặc NC Auditor tra cứu nhật ký theo bản ghi, người… | Must | Sửa | REF-09 | UC-026 | Như 1.0 | FEAT-039 | TC-CLS-44 | _TBD_ |
