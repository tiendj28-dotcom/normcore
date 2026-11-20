# Requirements Traceability Matrix: Normcore

> Source: docs/srs.md v1.1, docs/use-cases.md v1.1 · Last updated: 2026-11-13
> Cột Design ref do kiến trúc ghi (ADR có trường "Requirements addressed" dẫn yêu cầu đó); thiết kế chi tiết từng tính năng sẽ ghi nối thêm.
> Cột Plan ref do kế hoạch triển khai ghi (mã tính năng hoặc Foundations). Cột Test ref do giai đoạn kiểm thử ghi khi nghiệm thu; test case dự kiến xem Phụ lục A.
> Tệp này được sinh bằng `docs/tools/build_rtm.py`; chạy lại sau mỗi lần sửa tài liệu nguồn. Không sửa tay.
> Bản 1.1: 255 FR và 32 NFR. So với bản 1.0: thêm 76 FR và 2 NFR, sửa 9 FR (giữ nguyên mã); danh sách ở Phụ lục B.

| Req ID | Requirement (short) | Priority | Status | Source | Use case(s) | Design ref | Plan ref | Test ref |
| :----- | :------------------ | :------- | :----- | :----- | :---------- | :--------- | :------- | :------- |
| FR-ACC-001 | Hệ thống phải yêu cầu người dùng đăng nhập bằng tài khoản của site trước khi… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | FEAT-001 | _TBD_ |
| FR-ACC-002 | Hệ thống phải cung cấp 10 vai trò nêu ở mục 2.3 và áp quyền đọc, tạo, sửa,… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017, UC-026 | _TBD_ | FEAT-001, FEAT-039 | _TBD_ |
| FR-ACC-003 | Trong khi người dùng chỉ có vai trò NC Clinician hoặc NC Department Head, hệ… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | FEAT-001 | _TBD_ |
| FR-ACC-004 | Hệ thống phải chỉ cho phép vai trò NC Finance, NC Director, NC Admin và NC… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017, UC-026 | _TBD_ | FEAT-001, FEAT-039 | _TBD_ |
| FR-ACC-005 | Nếu người dùng mở bản ghi ngoài phạm vi quyền, thì hệ thống phải từ chối và… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | FEAT-001 | _TBD_ |
| FR-ACC-006 | Khi NC Admin gán hoặc bỏ gán người dùng khỏi một khoa, hệ thống phải áp phạm… | Should | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | FEAT-001 | _TBD_ |
| FR-ACC-007 | Hệ thống phải cho vai trò NC Auditor quyền chỉ đọc đối với mọi bản ghi nghiệp… | Should | Active | REF-08; REF-09 | UC-026 | _TBD_ | FEAT-039 | _TBD_ |
| FR-ACC-008 | Trong khi người dùng chỉ có vai trò NC Clinician hoặc NC Department Head, hệ… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-LIB-001 | Khi NC Document Controller tải lên tệp PDF hoặc DOCX và nhập số hiệu, tên,… | Must | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-002 | Nếu số hiệu văn bản trùng với một bản ghi đã có, thì hệ thống phải từ chối… | Must | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-003 | Khi văn bản được lưu kèm tệp, hệ thống phải tách nội dung thành các mục có số… | Must | Active | REF-01 | UC-001 | ADR-009 | FEAT-020 | _TBD_ |
| FR-LIB-004 | Nếu tệp PDF không chứa lớp văn bản, thì hệ thống phải nhận dạng ký tự tiếng… | Should | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-005 | Nếu việc tách mục hoặc nhận dạng ký tự thất bại, thì hệ thống phải đặt trạng… | Must | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-006 | Khi ngày hệ thống sang ngày mới, hệ thống phải cập nhật trạng thái hiệu lực… | Must | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-007 | Khi người dùng khai báo văn bản A thay thế toàn bộ văn bản B từ một ngày, hệ… | Must | Active | REF-01 | UC-002 | _TBD_ | FEAT-021 | _TBD_ |
| FR-LIB-008 | Khi người dùng khai báo văn bản A thay thế một số mục của văn bản B, hệ thống… | Must | Active | REF-01 | UC-002 | _TBD_ | FEAT-021 | _TBD_ |
| FR-LIB-009 | Khi một văn bản hoặc mục chuyển sang "Hết hiệu lực", hệ thống phải gắn cờ… | Must | Active | REF-01 | UC-002 | _TBD_ | FEAT-021 | _TBD_ |
| FR-LIB-010 | Khi người dùng tìm kiếm theo từ khóa, số hiệu hoặc mã dịch vụ, hệ thống phải… | Must | Active | REF-01 | UC-001 | ADR-006 | FEAT-020 | _TBD_ |
| FR-LIB-011 | Khi người dùng mở một mục, hệ thống phải hiển thị văn bản đã tách bên cạnh… | Should | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-012 | Khi NC Document Controller sửa văn bản thuần của một mục, hệ thống phải lưu… | Should | Active | REF-01 | UC-001 | _TBD_ | FEAT-020 | _TBD_ |
| FR-LIB-013 | Khi NC Document Controller nạp tài liệu của hãng sản xuất (hướng dẫn sử dụng… | Should | Active | REF-08; REF-09 | UC-025 | ADR-007 | FEAT-038 | _TBD_ |
| FR-SVC-001 | Khi NC Document Controller nhập tệp Excel danh mục kỹ thuật theo mẫu (mã,… | Must | Active | REF-01 | UC-003 | ADR-012 | FEAT-005 | _TBD_ |
| FR-SVC-002 | Nếu một dòng nhập thiếu mã hoặc tên, hoặc trùng mã trong cùng tệp, thì hệ… | Must | Active | REF-01 | UC-003 | _TBD_ | FEAT-005 | _TBD_ |
| FR-SVC-003 | Khi người dùng gán khoa thực hiện cho một dịch vụ, hệ thống phải lưu quan hệ… | Must | Active | REF-01 | UC-003 | _TBD_ | FEAT-005 | _TBD_ |
| FR-SVC-004 | Khi người dùng mở một dịch vụ, hệ thống phải hiển thị tình trạng chuỗi của… | Must | Active | REF-01 | UC-003 | _TBD_ | FEAT-005 | _TBD_ |
| FR-SVC-005 | Khi hệ thống tách xong một văn bản hướng dẫn QTKT, hệ thống phải đề xuất ánh… | Should | Active | REF-01 | UC-003 | ADR-006 | FEAT-022 | _TBD_ |
| FR-SVC-006 | Khi NC Document Controller xác nhận hoặc sửa một ánh xạ, hệ thống phải lưu… | Must | Active | REF-01 | UC-003 | ADR-006 | FEAT-022 | _TBD_ |
| FR-SVC-007 | Trong khi một ánh xạ chưa ở trạng thái "Đã xác nhận", hệ thống phải không… | Must | Active | REF-01 | UC-003 | ADR-006 | FEAT-022 | _TBD_ |
| FR-SVC-008 | Khi NC Document Controller đánh dấu một dịch vụ kỹ thuật thuộc khối cận lâm… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-SVC-009 | Khi người dùng khai mã của một dịch vụ trên HIS, LIS hoặc RIS, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-019, UC-022 | _TBD_ | FEAT-031 | _TBD_ |
| FR-SVC-010 | Ở nơi dịch vụ được đánh dấu là dịch vụ bộ, hệ thống phải lưu danh sách thông… | Should | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-SVC-011 | Ở nơi dịch vụ được đánh dấu gửi ngoài, hệ thống phải lưu giá hợp đồng gửi… | Could | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-PROC-001 | Khi người soạn tạo quy trình cho một dịch vụ kỹ thuật và một khoa chủ trì, hệ… | Must | Active | REF-01 | UC-004 | _TBD_ | FEAT-006 | _TBD_ |
| FR-PROC-002 | Nếu dịch vụ đã có một quy trình của cùng khoa chủ trì ở trạng thái "Nháp"… | Must | Active | REF-01 | UC-004 | _TBD_ | FEAT-006 | _TBD_ |
| FR-PROC-003 | Khi người soạn thêm một bước, hệ thống phải yêu cầu giai đoạn (Chuẩn bị, Thực… | Must | Active | REF-01 | UC-005 | ADR-002 | FEAT-006 | _TBD_ |
| FR-PROC-004 | Khi người soạn khai báo nguồn lực cho một bước, hệ thống phải lưu loại nguồn… | Must | Active | REF-01 | UC-005 | ADR-002 | FEAT-006 | _TBD_ |
| FR-PROC-005 | Khi người soạn nhập tên nguồn lực, hệ thống phải gợi ý các bản ghi khớp trong… | Should | Active | REF-01 | UC-005 | _TBD_ | FEAT-006 | _TBD_ |
| FR-PROC-006 | Khi người soạn sắp xếp lại các bước, hệ thống phải cập nhật thứ tự hiển thị… | Must | Active | REF-01 | UC-005 | ADR-002 | FEAT-006 | _TBD_ |
| FR-PROC-007 | Khi người soạn gắn trích dẫn cho một phần hoặc một bước, hệ thống phải lưu… | Must | Active | REF-01 | UC-005 | ADR-010 | FEAT-006 | _TBD_ |
| FR-PROC-008 | Nếu một trích dẫn có loại quan hệ "Khác biệt" mà lý do để trống, thì hệ thống… | Must | Active | REF-01 | UC-005, UC-006 | _TBD_ | FEAT-007 | _TBD_ |
| FR-PROC-009 | Khi người soạn lưu bản nháp, hệ thống phải ghi lịch sử thay đổi theo trường,… | Must | Active | REF-01 | UC-005 | ADR-014 | FEAT-006 | _TBD_ |
| FR-PROC-010 | Khi người dùng yêu cầu in một quy trình, hệ thống phải sinh tệp PDF theo mẫu… | Must | Active | REF-01 | UC-006 | ADR-015 | FEAT-007 | _TBD_ |
| FR-PROC-011 | Khi người dùng yêu cầu xuất DOCX một quy trình, hệ thống phải sinh tệp DOCX… | Should | Active | REF-01 | UC-006 | ADR-015 | FEAT-007 | _TBD_ |
| FR-PROC-012 | Nếu người soạn gửi duyệt một quy trình không có bước nào ở giai đoạn "Thực… | Must | Active | REF-01 | UC-006 | _TBD_ | FEAT-007 | _TBD_ |
| FR-PROC-013 | Khi người soạn sao chép quy trình từ một dịch vụ khác, hệ thống phải tạo bản… | Could | Active | REF-01 | UC-005 | _TBD_ | FEAT-006 | _TBD_ |
| FR-AI-001 | Khi người soạn nhập yêu cầu (điều kiện của khoa, thiết bị, thuốc, vật tư,… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | ADR-006 | FEAT-024 | _TBD_ |
| FR-AI-002 | Khi AI trả kết quả, hệ thống phải tạo bản nháp quy trình có cấu trúc (phần,… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | ADR-007 | FEAT-024 | _TBD_ |
| FR-AI-003 | Khi nội dung dự thảo khác nội dung mục hướng dẫn tương ứng do yêu cầu của… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | _TBD_ | FEAT-024 | _TBD_ |
| FR-AI-004 | Nếu dịch vụ không có mục hướng dẫn nào đã xác nhận và còn hiệu lực, thì hệ… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | _TBD_ | FEAT-024 | _TBD_ |
| FR-AI-005 | Nếu đoạn trích trong một trích dẫn do AI trả về không xuất hiện nguyên văn… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | ADR-007 | FEAT-024 | _TBD_ |
| FR-AI-006 | Khi người soạn yêu cầu kiểm tra nhất quán, hệ thống phải liệt kê: nguồn lực… | Should | Active | REF-01; ràng buộc C-04, C-08 | UC-005 | _TBD_ | FEAT-025 | _TBD_ |
| FR-AI-007 | Khi bộ định mức được khởi tạo từ quy trình đã ban hành, hệ thống phải đề xuất… | Should | Active | REF-01; ràng buộc C-04, C-08 | UC-009 | _TBD_ | FEAT-025 | _TBD_ |
| FR-AI-008 | Trong khi một đề xuất của AI chưa được người có quyền chấp nhận, hệ thống… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004, UC-009 | ADR-007 | FEAT-024 | _TBD_ |
| FR-AI-009 | Khi hệ thống gọi AI, hệ thống phải ghi nhật ký: mục đích, người gọi, bản ghi… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | ADR-005 | FEAT-023 | _TBD_ |
| FR-AI-010 | Nếu dịch vụ AI không phản hồi trong thời hạn cấu hình hoặc trả lỗi, thì hệ… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | ADR-005 | FEAT-023 | _TBD_ |
| FR-AI-011 | Hệ thống phải không gửi cho AI dữ liệu nhập từ kế toán, kết quả tính giá, và… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004 | ADR-007, ADR-008 | FEAT-023 | _TBD_ |
| FR-AI-012 | Khi NC Admin lưu cấu hình nhà cung cấp AI (loại giao thức, địa chỉ, mô hình,… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-017 | ADR-005 | FEAT-023 | _TBD_ |
| FR-AI-013 | Nếu số token lũy kế trong tháng vượt hạn mức cấu hình, thì hệ thống phải chặn… | Should | Active | REF-01; ràng buộc C-04, C-08 | UC-017 | ADR-005 | FEAT-023 | _TBD_ |
| FR-AI-014 | Khi NC Admin sửa một mẫu lệnh, hệ thống phải tạo phiên bản mẫu lệnh mới và… | Should | Active | REF-01; ràng buộc C-04, C-08 | UC-017 | _TBD_ | FEAT-023 | _TBD_ |
| FR-AI-015 | Ở nơi tính năng AI bị tắt trong cấu hình, hệ thống phải ẩn các nút gọi AI và… | Must | Active | REF-01; ràng buộc C-04, C-08 | UC-004, UC-017 | ADR-005 | FEAT-023 | _TBD_ |
| FR-AI-016 | Khi người dùng yêu cầu AI đề xuất định mức cho một hệ thống xét nghiệm, hệ… | Should | Active | REF-08; REF-09 | UC-025 | ADR-007 | FEAT-038 | _TBD_ |
| FR-AI-017 | Khi AI trả một đề xuất định mức, hệ thống phải gắn cho đề xuất đó trích dẫn… | Should | Active | REF-08; REF-09 | UC-025 | ADR-007 | FEAT-038 | _TBD_ |
| FR-AI-018 | Nếu AI đề xuất một mặt hàng hoặc thiết bị không có trong danh mục, thì hệ… | Should | Active | REF-08; REF-09 | UC-025 | _TBD_ | FEAT-038 | _TBD_ |
| FR-WF-001 | Khi người soạn gửi duyệt một quy trình hợp lệ, hệ thống phải chuyển trạng… | Must | Active | REF-01 | UC-006 | ADR-011 | FEAT-007 | _TBD_ |
| FR-WF-002 | Khi trưởng khoa đồng ý, hệ thống phải chuyển trạng thái sang "Chờ hội đồng… | Must | Active | REF-01 | UC-006 | ADR-011 | FEAT-007 | _TBD_ |
| FR-WF-003 | Khi thành viên hội đồng ghi ý kiến, hệ thống phải lưu ý kiến gắn với phần… | Must | Active | REF-01 | UC-006 | ADR-011 | FEAT-007 | _TBD_ |
| FR-WF-004 | Khi thư ký hội đồng ghi kết luận "Thông qua", hệ thống phải chuyển trạng thái… | Must | Active | REF-01 | UC-006 | ADR-011 | FEAT-007 | _TBD_ |
| FR-WF-005 | Khi NC Director ban hành, hệ thống phải yêu cầu số quyết định và ngày hiệu… | Must | Active | REF-01 | UC-006 | ADR-011 | FEAT-007 | _TBD_ |
| FR-WF-006 | Khi một phiên bản mới đến ngày hiệu lực, hệ thống phải chuyển phiên bản "Đã… | Must | Active | REF-01 | UC-006 | _TBD_ | FEAT-007 | _TBD_ |
| FR-WF-007 | Khi người duyệt ở bất kỳ cấp nào từ chối, hệ thống phải yêu cầu lý do, trả… | Must | Active | REF-01 | UC-006 | ADR-011 | FEAT-007 | _TBD_ |
| FR-WF-008 | Trong khi quy trình ở trạng thái "Đã ban hành", "Đã thay thế" hoặc "Đã thu… | Must | Active | REF-01 | UC-006 | _TBD_ | FEAT-007 | _TBD_ |
| FR-WF-009 | Khi người có quyền yêu cầu sửa đổi một quy trình "Đã ban hành", hệ thống phải… | Must | Active | REF-01 | UC-002, UC-007 | _TBD_ | FEAT-008 | _TBD_ |
| FR-WF-010 | Khi người dùng so sánh hai phiên bản của một quy trình, hệ thống phải hiển… | Should | Active | REF-01 | UC-007 | _TBD_ | FEAT-008 | _TBD_ |
| FR-WF-011 | Khi một phiên bản quy trình mới được ban hành, hệ thống phải gắn cờ "Cần cập… | Must | Active | REF-01 | UC-007 | ADR-002 | FEAT-008 | _TBD_ |
| FR-WF-012 | Khi NC Director thu hồi một quy trình, hệ thống phải yêu cầu lý do và chuyển… | Should | Active | REF-01 | UC-007 | _TBD_ | FEAT-008 | _TBD_ |
| FR-WF-013 | Nếu một quy trình chờ duyệt ở một cấp quá số ngày cấu hình, thì hệ thống phải… | Could | Active | REF-01 | UC-006 | _TBD_ | FEAT-007 | _TBD_ |
| FR-RES-001 | Khi NC Resource Manager tạo một mặt hàng (thuốc, hóa chất, dịch truyền, vật… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-002 | Khi người dùng thêm đơn giá cho một mặt hàng, hệ thống phải yêu cầu giá đã… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-003 | Nếu ngày chứng từ của đơn giá được dùng cũ hơn 24 tháng so với ngày tính giá,… | Must | Active | REF-01; REF-03 | UC-008, UC-012 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-004 | Khi một mặt hàng có nhiều đơn giá còn hiệu lực tại ngày tính giá, hệ thống… | Must | Active | REF-01 | UC-008, UC-012 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-005 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu ngày đưa… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-006 | Khi thông tin thiết bị được lưu, hệ thống phải tính khấu hao năm và đơn giá… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-007 | Nếu thiết bị đã hết thời gian sử dụng tính đến ngày tính giá, thì hệ thống… | Must | Active | REF-01 | UC-008, UC-012 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-008 | Khi người dùng khai báo một phòng, hệ thống phải yêu cầu diện tích, chi phí… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-009 | Khi NC Finance tạo bộ tham số tính giá, hệ thống phải yêu cầu ngày hiệu lực… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-011 | _TBD_ |
| FR-RES-010 | Khi NC Finance khai báo chi phí theo chức danh trong một bộ tham số, hệ thống… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-011 | _TBD_ |
| FR-RES-011 | Trong khi một bộ tham số đang được một lần tính giá đã khóa sử dụng, hệ thống… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-011 | _TBD_ |
| FR-RES-012 | Khi người dùng nhập danh mục từ tệp Excel mẫu (mặt hàng, đơn giá, thiết bị,… | Must | Active | REF-01 | UC-008 | ADR-012 | FEAT-009, FEAT-010, FEAT-011 | _TBD_ |
| FR-RES-013 | Khi người dùng gán hai hay nhiều mặt hàng vào cùng một nhóm tương đương, hệ… | Should | Active | REF-01 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-014 | Khi người dùng đánh dấu một mặt hàng là "thanh toán riêng ngoài giá dịch vụ",… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-015 | Khi NC Finance khai báo một loại giá, hệ thống phải yêu cầu cấp phê duyệt… | Must | Active | REF-01 | UC-008 | _TBD_ | FEAT-011 | _TBD_ |
| FR-RES-016 | Khi người dùng xác minh một đơn giá, hệ thống phải yêu cầu tệp chứng từ đính… | Should | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-017 | Nếu một dòng chi phí dùng đơn giá chưa ở trạng thái "Đã xác minh", thì hệ… | Should | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-018 | Khi NC Resource Manager tạo mặt hàng loại hóa chất xét nghiệm, chất chuẩn… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-009 | _TBD_ |
| FR-RES-019 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu hình… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-020 | Trong khi hình thức có máy là Thuê hoặc Liên doanh, liên kết, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-021 | Trong khi hình thức có máy là Đặt theo hóa chất, hệ thống phải tính khấu hao… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-022 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu tiêu chí… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-023 | Khi người dùng khai linh kiện lớn của một thiết bị, hệ thống phải yêu cầu… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-024 | Khi một thiết bị dùng chung cho nhiều khoa, hệ thống phải lưu tỷ lệ phân bổ… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-025 | Nếu tổng tỷ lệ phân bổ theo khoa của một thiết bị khác 100%, thì hệ thống… | Must | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-RES-026 | Khi NC Resource Manager khai báo một thiết bị cận lâm sàng, hệ thống phải cho… | Should | Active | REF-08; REF-09 | UC-008 | _TBD_ | FEAT-010 | _TBD_ |
| FR-NORM-001 | Khi người có quyền khởi tạo bộ định mức cho một dịch vụ và một khoa, hệ thống… | Must | Active | REF-01 | UC-009 | ADR-002 | FEAT-012 | _TBD_ |
| FR-NORM-002 | Nếu dịch vụ chưa có quy trình "Đã ban hành", thì hệ thống phải từ chối khởi… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-003 | Khi người dùng sửa một dòng định mức, hệ thống phải yêu cầu cấu phần, nguồn… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-004 | Nếu người dùng nhập tỷ lệ hao hụt vượt trần trong bộ tham số hiệu lực, thì hệ… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-005 | Khi người dùng thêm dòng định mức không xuất phát từ dòng nguồn lực của quy… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-006 | Khi một dòng định mức có cả định mức của bệnh viện và định mức do cơ quan có… | Must | Active | REF-01; REF-03 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-007 | Khi một dòng định mức không có định mức do cơ quan có thẩm quyền ban hành, hệ… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-008 | Khi người dùng chọn căn cứ cho một dòng định mức, hệ thống phải lưu một trong… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-009 | Khi người có vai trò NC Clinician hoặc NC Department Head xác nhận một dòng… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-010 | Nếu bộ định mức còn dòng chưa xác nhận, dòng chưa liên kết danh mục hoặc đề… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-011 | Khi NC Finance xác nhận một bộ định mức "Đã xác nhận chuyên môn", hệ thống… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-012 | Trong khi bộ định mức ở trạng thái "Đã khóa", hệ thống phải từ chối sửa và… | Must | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-013 | Khi người dùng đánh dấu loại trừ một dòng định mức, hệ thống phải yêu cầu lý… | Must | Active | REF-01; REF-03 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-014 | Nếu cùng một nguồn lực xuất hiện ở hai dòng của cùng một bước, thì hệ thống… | Should | Active | REF-01 | UC-009 | _TBD_ | FEAT-012 | _TBD_ |
| FR-NORM-015 | Khi người dùng tạo phiên bản bộ định mức mới theo một phiên bản quy trình… | Must | Active | REF-01 | UC-009 | ADR-002 | FEAT-013 | _TBD_ |
| FR-NORM-016 | Khi người dùng xem một bộ định mức, hệ thống phải hiển thị chi phí trực tiếp… | Should | Active | REF-01 | UC-009 | ADR-010 | FEAT-012 | _TBD_ |
| FR-NORM-017 | Ở nơi dịch vụ có hệ thống xét nghiệm, hệ thống phải gắn mỗi bộ định mức với… | Must | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-018 | Khi người dùng sửa một dòng định mức của dịch vụ cận lâm sàng, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-019 | Khi người dùng khai một dòng thuốc, hóa chất hoặc vật tư có cấp phát sinh… | Must | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-020 | Nếu bộ định mức có dòng Theo ống mẫu mà chưa khai số xét nghiệm bình quân… | Must | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-021 | Khi NC Finance hoặc NC Admin lập mẫu định mức cho một nhóm chuyên ngành, hệ… | Should | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-022 | Khi người dùng khởi tạo bộ định mức cho dịch vụ thuộc nhóm chuyên ngành có… | Should | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-023 | Nếu bộ định mức thiếu dòng cho một khoản mục bắt buộc của mẫu và người dùng… | Should | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-024 | Nếu một dòng định mức dùng mặt hàng đã có trong kế hoạch nội kiểm hoặc kế… | Must | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-NORM-025 | Khi người dùng sao chép bộ định mức từ một hệ thống xét nghiệm khác của cùng… | Could | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-TS-001 | Khi người khảo sát tạo phiếu bấm giờ cho một dịch vụ và một khoa, hệ thống… | Must | Active | REF-01 | UC-010 | _TBD_ | FEAT-014 | _TBD_ |
| FR-TS-002 | Khi người khảo sát ghi một ca, hệ thống phải lưu cho từng bước: chức danh, số… | Must | Active | REF-01 | UC-010 | _TBD_ | FEAT-014 | _TBD_ |
| FR-TS-003 | Khi một dịch vụ có số ca khảo sát từ mức tối thiểu cấu hình trở lên, hệ thống… | Must | Active | REF-01 | UC-010 | _TBD_ | FEAT-014 | _TBD_ |
| FR-TS-004 | Khi người dùng chọn áp kết quả bấm giờ vào một bộ định mức nháp, hệ thống… | Must | Active | REF-01 | UC-010 | _TBD_ | FEAT-014 | _TBD_ |
| FR-TS-005 | Nếu số ca khảo sát ít hơn mức tối thiểu, thì hệ thống phải cảnh báo và yêu… | Should | Active | REF-01 | UC-010 | _TBD_ | FEAT-014 | _TBD_ |
| FR-ACCT-001 | Khi NC Finance tải tệp Excel số liệu chi phí theo mẫu (mã tài khoản, tên tài… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | ADR-012 | FEAT-016 | _TBD_ |
| FR-ACCT-002 | Nếu tệp có dòng thiếu mã tài khoản, số tiền không phải số, hoặc mã trung tâm… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | ADR-012 | FEAT-016 | _TBD_ |
| FR-ACCT-003 | Khi lần nhập được tạo, hệ thống phải gán loại chi phí cho từng dòng theo bảng… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | ADR-013 | FEAT-016 | _TBD_ |
| FR-ACCT-004 | Khi NC Finance sửa loại chi phí của một dòng hoặc đánh dấu loại trừ, hệ thống… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | ADR-013 | FEAT-016 | _TBD_ |
| FR-ACCT-005 | Nếu lần nhập còn dòng chưa được gán loại chi phí, thì hệ thống phải từ chối… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | _TBD_ | FEAT-016 | _TBD_ |
| FR-ACCT-006 | Khi NC Finance chốt lần nhập, hệ thống phải khóa các dòng và ghi tổng theo… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | _TBD_ | FEAT-016 | _TBD_ |
| FR-ACCT-007 | Khi NC Finance nhập tệp sản lượng dịch vụ theo khoa cho một năm, hệ thống… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | ADR-012 | FEAT-016 | _TBD_ |
| FR-ACCT-008 | Khi NC Finance khai báo một quy tắc phân bổ, hệ thống phải yêu cầu cấp phân… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | _TBD_ | FEAT-016 | _TBD_ |
| FR-ACCT-009 | Khi ứng dụng được cài đặt, hệ thống phải nạp bảng ánh xạ tài khoản mặc định… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | ADR-013 | FEAT-016 | _TBD_ |
| FR-ACCT-010 | Khi NC Finance nhập số liệu tiêu chí của trung tâm chi phí cho một năm (số… | Must | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | _TBD_ | FEAT-016 | _TBD_ |
| FR-ACCT-011 | Khi người dùng nhập lần thứ hai cho cùng một năm tài chính, hệ thống phải tạo… | Should | Active | REF-01; ràng buộc C-03, C-07 | UC-011 | _TBD_ | FEAT-016 | _TBD_ |
| FR-ACCT-012 | Khi NC Finance nhập sản lượng, hệ thống phải yêu cầu kịch bản sản lượng của… | Must | Active | REF-08; REF-09 | UC-022 | ADR-018 | FEAT-035 | _TBD_ |
| FR-ACCT-013 | Khi NC Finance nhập tệp sản lượng cận lâm sàng theo mẫu, hệ thống phải lưu… | Must | Active | REF-08; REF-09 | UC-022 | ADR-012, ADR-018 | FEAT-035 | _TBD_ |
| FR-ACCT-014 | Nếu tệp sản lượng cận lâm sàng có mã dịch vụ, mã khoa hoặc mã hệ thống xét… | Must | Active | REF-08; REF-09 | UC-022 | ADR-018 | FEAT-035 | _TBD_ |
| FR-ACCT-015 | Khi NC Finance nhập tệp xuất kho thực tế theo mẫu, hệ thống phải lưu lượng… | Must | Active | REF-08; REF-09 | UC-022 | ADR-012, ADR-018 | FEAT-035 | _TBD_ |
| FR-COST-001 | Khi NC Finance tạo một lần tính giá, hệ thống phải yêu cầu năm tài chính,… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-015 | _TBD_ |
| FR-COST-002 | Nếu trong phạm vi có dịch vụ chưa có bộ định mức "Đã khóa", thì hệ thống phải… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-015 | _TBD_ |
| FR-COST-003 | Khi lần tính giá chạy, hệ thống phải tính chi phí trực tiếp của từng dòng… | Must | Active | REF-01 | UC-012 | ADR-003 | FEAT-015 | _TBD_ |
| FR-COST-004 | Khi lần tính giá chạy, hệ thống phải phân bổ chi phí của các trung tâm chi… | Must | Active | REF-01 | UC-012 | ADR-003 | FEAT-017 | _TBD_ |
| FR-COST-005 | Khi lần tính giá chạy, hệ thống phải xác định cho mỗi trung tâm chi phí lâm… | Must | Active | REF-01 | UC-012 | ADR-003 | FEAT-017 | _TBD_ |
| FR-COST-006 | Khi lần tính giá chạy, hệ thống phải tính cho mỗi dịch vụ giá thành toàn bộ,… | Must | Active | REF-01 | UC-012 | ADR-003 | FEAT-015 | _TBD_ |
| FR-COST-007 | Ở nơi loại giá không kết cấu khấu hao, hệ thống phải loại các khoản khấu hao… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-015 | _TBD_ |
| FR-COST-008 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát theo trung tâm chi… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-017 | _TBD_ |
| FR-COST-009 | Nếu chênh lệch phần trăm của một dòng đối soát vượt ngưỡng trong bộ tham số,… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-017 | _TBD_ |
| FR-COST-010 | Khi người dùng mở bảng giải trình của một dịch vụ, hệ thống phải hiển thị… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-015 | _TBD_ |
| FR-COST-011 | Khi NC Finance khóa một lần tính giá, hệ thống phải lưu ảnh chụp toàn bộ đầu… | Must | Active | REF-01 | UC-012 | ADR-004 | FEAT-018 | _TBD_ |
| FR-COST-012 | Trong khi một lần tính giá ở trạng thái "Đã khóa", hệ thống phải từ chối tính… | Must | Active | REF-01 | UC-012 | ADR-004 | FEAT-018 | _TBD_ |
| FR-COST-013 | Khi người dùng so sánh hai lần tính giá, hệ thống phải hiển thị chênh lệch… | Should | Active | REF-01 | UC-012 | _TBD_ | FEAT-018 | _TBD_ |
| FR-COST-014 | Nếu sản lượng của một dịch vụ bằng 0 hoặc thiếu, thì hệ thống phải không phân… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-017 | _TBD_ |
| FR-COST-015 | Khi một lần tính giá có hơn 50 dịch vụ, hệ thống phải chạy bằng tác vụ nền và… | Should | Active | REF-01 | UC-012 | ADR-009 | FEAT-015 | _TBD_ |
| FR-COST-016 | Nếu một dòng định mức không có đơn giá hiệu lực tại ngày tính giá, thì hệ… | Must | Active | REF-01 | UC-012 | _TBD_ | FEAT-015 | _TBD_ |
| FR-COST-017 | Khi NC Finance tạo một lần tính giá, hệ thống phải yêu cầu kịch bản sản lượng… | Must | Active | REF-08; REF-09 | UC-012 | ADR-018 | FEAT-036 | _TBD_ |
| FR-COST-018 | Khi lần tính giá chạy, hệ thống phải tính hệ số tiêu hao k của từng hệ thống… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-019 | Khi lần tính giá chạy, hệ thống phải tính chi phí cho một kết quả của từng… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-020 | Khi lần tính giá chạy, hệ thống phải tính chi phí vật liệu nội kiểm, chất… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-021 | Khi lần tính giá chạy, hệ thống phải tính chi phí thiết bị của dịch vụ theo… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-022 | Khi một dịch vụ trong một khoa có nhiều hệ thống xét nghiệm, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-023 | Nếu một hệ thống xét nghiệm thiếu sản lượng của kịch bản được chọn, có số kết… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-024 | Khi lần tính giá chạy cho dịch vụ có hệ thống xét nghiệm, hệ thống phải dùng… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017, ADR-018 | FEAT-036 | _TBD_ |
| FR-COST-025 | Nếu số test tiêu thụ của một hệ thống xét nghiệm trong thời hạn dùng sau mở… | Should | Active | REF-08; REF-09 | UC-012 | _TBD_ | FEAT-036 | _TBD_ |
| FR-COST-026 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát vật chất theo khoa… | Must | Active | REF-08; REF-09 | UC-023 | ADR-018 | FEAT-037 | _TBD_ |
| FR-COST-027 | Nếu chênh lệch phần trăm của một dòng đối soát vật chất vượt ngưỡng đối soát… | Must | Active | REF-08; REF-09 | UC-023 | ADR-018 | FEAT-037 | _TBD_ |
| FR-COST-028 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát sản lượng so số… | Should | Active | REF-08; REF-09 | UC-023 | ADR-018 | FEAT-037 | _TBD_ |
| FR-COST-029 | Nếu một khoa trong phạm vi không có số liệu xuất kho thực tế của năm tài… | Must | Active | REF-08; REF-09 | UC-023 | ADR-018 | FEAT-037 | _TBD_ |
| FR-COST-030 | Khi người dùng mở phân tích độ nhạy của một dịch vụ, hệ thống phải tính lại… | Should | Active | REF-08; REF-09 | UC-024 | _TBD_ | FEAT-037 | _TBD_ |
| FR-COST-031 | Khi người dùng mở bảng giải trình của một dịch vụ cận lâm sàng, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-COST-032 | Khi NC Finance khóa một lần tính giá có dịch vụ cận lâm sàng, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-012 | ADR-004 | FEAT-036 | _TBD_ |
| FR-BM-001 | Khi người dùng tạo một đơn vị tham chiếu, hệ thống phải yêu cầu tên, tỉnh… | Must | Active | REF-01 | UC-013 | _TBD_ | FEAT-026 | _TBD_ |
| FR-BM-002 | Khi người dùng nhập giá tham chiếu bằng tay hoặc bằng tệp Excel mẫu, hệ thống… | Must | Active | REF-01 | UC-013 | ADR-012 | FEAT-026 | _TBD_ |
| FR-BM-003 | Khi người dùng nạp tệp bảng giá PDF của một đơn vị, hệ thống phải dùng AI… | Should | Active | REF-01 | UC-013 | _TBD_ | FEAT-027 | _TBD_ |
| FR-BM-004 | Khi một dòng giá tham chiếu có tên dịch vụ gốc chưa gắn mã, hệ thống phải đề… | Must | Active | REF-01 | UC-013 | _TBD_ | FEAT-026 | _TBD_ |
| FR-BM-005 | Trong khi một dòng giá tham chiếu chưa ở trạng thái "Đã xác nhận", hệ thống… | Must | Active | REF-01 | UC-013 | _TBD_ | FEAT-026 | _TBD_ |
| FR-BM-006 | Khi NC Finance nhập chỉ số giá tiêu dùng theo tháng, hệ thống phải tính giá… | Should | Active | REF-01 | UC-013 | _TBD_ | FEAT-026 | _TBD_ |
| FR-BM-007 | Nếu một dòng giá tham chiếu trùng đơn vị, dịch vụ, loại giá và ngày hiệu lực… | Must | Active | REF-01 | UC-013 | _TBD_ | FEAT-026 | _TBD_ |
| FR-BM-008 | Khi người dùng lập phiếu khảo sát giá cho một nhóm dịch vụ, hệ thống phải… | Should | Active | REF-01; REF-03 | UC-013 | _TBD_ | FEAT-026 | _TBD_ |
| FR-ADJ-001 | Khi người dùng mở so sánh cho một lần tính giá, hệ thống phải chọn cho từng… | Must | Active | REF-01; REF-03 | UC-014 | _TBD_ | FEAT-028 | _TBD_ |
| FR-ADJ-002 | Khi một dịch vụ có từ 3 đơn vị tham chiếu trở lên, hệ thống phải tính giá… | Must | Active | REF-01 | UC-014 | _TBD_ | FEAT-028 | _TBD_ |
| FR-ADJ-003 | Nếu một dịch vụ có ít hơn 3 đơn vị tham chiếu, thì hệ thống phải gắn nhãn… | Must | Active | REF-01; REF-03 | UC-014 | _TBD_ | FEAT-028 | _TBD_ |
| FR-ADJ-004 | Khi người dùng lọc đơn vị tham chiếu theo tỉnh hoặc thành phố, hạng và loại… | Should | Active | REF-01 | UC-014 | _TBD_ | FEAT-028 | _TBD_ |
| FR-ADJ-005 | Khi độ lệch của một dịch vụ vượt ngưỡng lệch so sánh trong bộ tham số, hệ… | Must | Active | REF-01 | UC-014 | ADR-008 | FEAT-028 | _TBD_ |
| FR-ADJ-006 | Khi người dùng chấp nhận một gợi ý không cần sửa quy trình, hệ thống phải ghi… | Must | Active | REF-01 | UC-014 | ADR-008 | FEAT-029 | _TBD_ |
| FR-ADJ-007 | Nếu một gợi ý hoặc một thay đổi do người dùng đề xuất làm thêm, bỏ hoặc đổi… | Must | Active | REF-01 | UC-014 | ADR-008 | FEAT-029 | _TBD_ |
| FR-ADJ-008 | Khi người dùng từ chối một gợi ý, hệ thống phải yêu cầu lý do và lưu cùng gợi… | Should | Active | REF-01 | UC-014 | _TBD_ | FEAT-028 | _TBD_ |
| FR-ADJ-009 | Khi một kịch bản điều chỉnh làm đổi dòng định mức, hệ thống phải tạo phiên… | Must | Active | REF-01 | UC-014 | _TBD_ | FEAT-029 | _TBD_ |
| FR-ADJ-010 | Khi người dùng xem một dịch vụ trong so sánh, hệ thống phải hiển thị giá trị… | Must | Active | REF-01 | UC-014 | ADR-010 | FEAT-028 | _TBD_ |
| FR-PRICE-001 | Khi NC Finance lập phương án giá từ một lần tính giá đã khóa hoặc một kịch… | Must | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-PRICE-002 | Khi người dùng sửa giá đề xuất khác giá làm tròn, hệ thống phải yêu cầu ghi… | Must | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-PRICE-003 | Nếu giá đề xuất của một dịch vụ thấp hơn giá thành toàn bộ, thì hệ thống phải… | Must | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-PRICE-004 | Khi NC Finance gửi duyệt phương án giá, hệ thống phải chuyển trạng thái sang… | Must | Active | REF-01 | UC-015 | ADR-011 | FEAT-030 | _TBD_ |
| FR-PRICE-005 | Khi mọi khoa liên quan đã xác nhận, hệ thống phải chuyển phương án giá sang… | Must | Active | REF-01 | UC-015 | ADR-011 | FEAT-030 | _TBD_ |
| FR-PRICE-006 | Khi NC Director phê duyệt một phương án thuộc loại giá do bệnh viện quyết… | Must | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-PRICE-007 | Khi NC Director phê duyệt một phương án thuộc loại giá do cơ quan có thẩm… | Must | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-PRICE-008 | Khi người dùng ghi kết quả phê duyệt của cơ quan có thẩm quyền (số văn bản,… | Should | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-PRICE-009 | Khi người duyệt ở bất kỳ cấp nào từ chối phương án giá, hệ thống phải yêu cầu… | Must | Active | REF-01 | UC-015 | ADR-011 | FEAT-030 | _TBD_ |
| FR-PRICE-010 | Khi giá đã duyệt của một dịch vụ thay đổi, hệ thống phải giữ lịch sử giá theo… | Must | Active | REF-01 | UC-015 | _TBD_ | FEAT-030 | _TBD_ |
| FR-OUT-001 | Khi người dùng xuất phương án giá, hệ thống phải sinh tệp Excel theo cấu trúc… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-002 | Khi người dùng xuất bảng tính giá thành theo yếu tố chi phí, hệ thống phải… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-003 | Khi người dùng xuất bảng tính giá thành theo phương pháp phân bổ, hệ thống… | Should | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-004 | Khi người dùng xuất danh mục dịch vụ đề nghị định giá, hệ thống phải sinh tệp… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-005 | Khi người dùng xuất bảng giải trình của một dịch vụ, hệ thống phải sinh tệp… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-006 | Khi người dùng xuất một bộ định mức, hệ thống phải sinh tệp Excel và PDF liệt… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-007 | Khi người dùng xuất bảng so sánh giá, hệ thống phải sinh tệp Excel gồm đơn vị… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-030 | _TBD_ |
| FR-OUT-008 | Khi hệ thống sinh một tệp xuất, hệ thống phải ghi ở chân trang hoặc trang… | Must | Active | REF-01; REF-03 | UC-016 | ADR-015 | FEAT-019 | _TBD_ |
| FR-OUT-009 | Khi người dùng yêu cầu xuất toàn bộ hồ sơ của một phương án giá, hệ thống… | Could | Active | REF-01; REF-03 | UC-016 | ADR-009 | FEAT-019 | _TBD_ |
| FR-OUT-010 | Khi người dùng mở trang chủ Normcore, hệ thống phải hiển thị số dịch vụ theo… | Should | Active | REF-01 | UC-018 | _TBD_ | FEAT-002 | _TBD_ |
| FR-OUT-011 | Khi người dùng xuất bộ định mức của một hệ thống xét nghiệm, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-021 | _TBD_ | FEAT-034 | _TBD_ |
| FR-OUT-012 | Khi người dùng mở báo cáo thiếu dữ liệu của một phạm vi tính giá, hệ thống… | Must | Active | REF-08; REF-09 | UC-024 | _TBD_ | FEAT-037 | _TBD_ |
| FR-AUD-001 | Khi một bản ghi nghiệp vụ được tạo, sửa, chuyển trạng thái hoặc xóa, hệ thống… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-018 | ADR-014 | FEAT-003 | _TBD_ |
| FR-AUD-002 | Hệ thống phải không cho phép bất kỳ vai trò nào sửa hoặc xóa nhật ký qua giao… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-018 | ADR-014 | FEAT-003 | _TBD_ |
| FR-AUD-003 | Khi NC Admin, NC Director hoặc NC Auditor tra cứu nhật ký theo bản ghi, người… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-018, UC-026 | ADR-014 | FEAT-003, FEAT-039 | _TBD_ |
| FR-AUD-004 | Khi người dùng xuất một tệp chứa số liệu tài chính, hệ thống phải ghi nhật ký… | Should | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-016 | ADR-014 | FEAT-003 | _TBD_ |
| FR-NOTI-001 | Khi một bản ghi chuyển đến bước cần một người dùng hoặc một vai trò xử lý, hệ… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-002, UC-006 | ADR-011 | FEAT-002 | _TBD_ |
| FR-NOTI-002 | Ở nơi máy chủ email được cấu hình, hệ thống phải gửi thêm email cho các thông… | Should | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-006 | _TBD_ | FEAT-002 | _TBD_ |
| FR-NOTI-003 | Khi người dùng mở trang chủ Normcore, hệ thống phải hiển thị danh sách việc… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-018 | _TBD_ | FEAT-002 | _TBD_ |
| FR-ADM-001 | Khi ứng dụng được cài đặt trên một site, hệ thống phải tạo sẵn các vai trò,… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | Foundations | _TBD_ |
| FR-ADM-002 | Khi người dùng yêu cầu tệp mẫu nhập liệu của một danh mục, hệ thống phải cung… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-008 | ADR-012 | FEAT-004 | _TBD_ |
| FR-ADM-003 | Khi NC Admin thay đổi một tham số vận hành (số ca bấm giờ tối thiểu, số ngày… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | FEAT-002 | _TBD_ |
| FR-ADM-004 | Khi NC Admin khai báo khoa, phòng và trung tâm chi phí, hệ thống phải yêu cầu… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-017 | _TBD_ | FEAT-001 | _TBD_ |
| FR-ADM-005 | Nếu người dùng xóa một bản ghi danh mục đang được bản ghi khác tham chiếu,… | Must | Active | BA đề xuất (yêu cầu nền của hệ thống) | UC-008 | _TBD_ | FEAT-001 | _TBD_ |
| FR-ADM-006 | Khi NC Admin thay đổi số ngày nhắc hạn hồ sơ tuân thủ hoặc danh sách loại… | Should | Active | REF-08; REF-09 | UC-020 | _TBD_ | FEAT-033 | _TBD_ |
| FR-CLS-001 | Khi người dùng tạo một hệ thống xét nghiệm, hệ thống phải yêu cầu mã, dịch… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-CLS-002 | Hệ thống phải cho phép một dịch vụ trong một khoa có nhiều hệ thống xét… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-CLS-003 | Nếu tổng tỷ trọng sản lượng của các hệ thống xét nghiệm đang dùng của một… | Must | Active | REF-08; REF-09 | UC-012 | _TBD_ | FEAT-036 | _TBD_ |
| FR-CLS-004 | Khi sản lượng của kịch bản được chọn có số kết quả trả theo từng hệ thống xét… | Should | Active | REF-08; REF-09 | UC-012 | ADR-018 | FEAT-036 | _TBD_ |
| FR-CLS-005 | Khi người dùng tạo hệ thống xét nghiệm có thiết bị chính chia chi phí theo… | Should | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-CLS-006 | Trong khi một hệ thống xét nghiệm được đánh dấu ngừng dùng, hệ thống phải… | Should | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-CLS-007 | Khi người dùng mở một hệ thống xét nghiệm, hệ thống phải hiển thị bộ định mức… | Should | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-031 | _TBD_ |
| FR-CLS-008 | Khi người dùng nhập từ tệp Excel mẫu các hệ thống xét nghiệm, kế hoạch chất… | Should | Active | REF-08; REF-09 | UC-019 | ADR-012 | FEAT-031 | _TBD_ |
| FR-QC-001 | Khi người dùng lập kế hoạch nội kiểm cho một hệ thống xét nghiệm, hệ thống… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-032 | _TBD_ |
| FR-QC-002 | Khi người dùng lập kế hoạch chuẩn máy cho một hệ thống xét nghiệm, hệ thống… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-032 | _TBD_ |
| FR-QC-003 | Khi người dùng khai một chương trình ngoại kiểm, hệ thống phải yêu cầu đơn vị… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-032 | _TBD_ |
| FR-QC-004 | Khi lần tính giá chạy, hệ thống phải chia phí của một chương trình ngoại kiểm… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-QC-005 | Nếu tổng tỷ lệ riêng của các dịch vụ trong một chương trình ngoại kiểm khác… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-032 | _TBD_ |
| FR-QC-006 | Khi sản lượng của kịch bản được chọn không có số test nội kiểm, chuẩn máy,… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-QC-007 | Nếu một hệ thống xét nghiệm thuộc nhóm chuyên ngành xét nghiệm không có kế… | Should | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-032 | _TBD_ |
| FR-QC-008 | Nếu người dùng chọn cho kế hoạch nội kiểm một mặt hàng không thuộc loại Vật… | Must | Active | REF-08; REF-09 | UC-019 | _TBD_ | FEAT-032 | _TBD_ |
| FR-CMP-001 | Khi NC Resource Manager tạo hồ sơ tuân thủ cho một thiết bị, hệ thống phải… | Must | Active | REF-08; REF-09 | UC-020 | _TBD_ | FEAT-033 | _TBD_ |
| FR-CMP-002 | Khi lần tính giá chạy, hệ thống phải quy chi phí của mỗi hồ sơ tuân thủ còn… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-CMP-003 | Khi lần tính giá dùng cách phân bổ Theo giá trị tài sản, hệ thống phải gom… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-CMP-004 | Khi lần tính giá dùng cách phân bổ Gắn trực tiếp thiết bị, hệ thống phải lấy… | Must | Active | REF-08; REF-09 | UC-012 | ADR-017 | FEAT-036 | _TBD_ |
| FR-CMP-005 | Khi một hồ sơ tuân thủ còn không quá số ngày cấu hình đến ngày hết hạn, hệ… | Should | Active | REF-08; REF-09 | UC-020 | _TBD_ | FEAT-033 | _TBD_ |
| FR-CMP-006 | Nếu một thiết bị thuộc loại bắt buộc có hồ sơ tuân thủ mà không có hồ sơ còn… | Must | Active | REF-08; REF-09 | UC-012 | _TBD_ | FEAT-033 | _TBD_ |
| FR-CMP-007 | Khi người dùng mở báo cáo hồ sơ tuân thủ, hệ thống phải liệt kê theo khoa các… | Should | Active | REF-08; REF-09 | UC-020 | _TBD_ | FEAT-033 | _TBD_ |
| NFR-PERF-001 | 95% lượt mở danh sách và form hoàn tất trong 2 giây với 50 người dùng đồng… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | _TBD_ | _TBD_ |
| NFR-PERF-002 | Một lần tính giá 500 dịch vụ, 50.000 dòng định mức hoàn tất trong 5 phút. | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-003, ADR-009 | _TBD_ | _TBD_ |
| NFR-PERF-003 | Tính lại chi phí trực tiếp tạm tính của một bộ định mức 200 dòng trong 3 giây. | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | _TBD_ | _TBD_ |
| NFR-PERF-004 | 95% lần soạn dự thảo bằng AI trả kết quả trong 180 giây; giao diện hiển thị… | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-009 | _TBD_ | _TBD_ |
| NFR-PERF-005 | 95% lượt tìm kiếm trong thư viện văn bản trả kết quả trong 3 giây với 2.000… | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-006 | _TBD_ | _TBD_ |
| NFR-SCAL-001 | Một site vận hành được với 200 tài khoản, 5.000 dịch vụ kỹ thuật, 500.000… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | _TBD_ | _TBD_ |
| NFR-SCAL-002 | Thư viện nhận tệp đến 100 MB mỗi tệp và 2.000 văn bản mỗi site. | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | _TBD_ | _TBD_ |
| NFR-AVL-001 | Khả dụng 99,5% mỗi tháng trong khung 07:00 đến 19:00 các ngày làm việc. | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-016 | _TBD_ | _TBD_ |
| NFR-AVL-002 | Sao lưu cơ sở dữ liệu và tệp hằng ngày, lưu 30 ngày; RPO 24 giờ; RTO 8 giờ. | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-016 | Foundations | _TBD_ |
| NFR-REL-001 | Chạy lại một lần tính giá với cùng ảnh chụp đầu vào cho kết quả trùng đến… | Must | Active | REF-01 (có giải trình) | — | ADR-003, ADR-004 | _TBD_ | _TBD_ |
| NFR-REL-002 | Phép tính tiền dùng số thập phân chính xác; không dùng số thực dấu phẩy động. | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-003 | _TBD_ | _TBD_ |
| NFR-REL-003 | Hệ số tiêu hao k được tính bằng số thập phân chính xác và lưu với 6 chữ số… | Must | Active | REF-08; REF-09 | — | ADR-017 | FEAT-036 | _TBD_ |
| NFR-SEC-001 | Mọi truy cập qua HTTPS với TLS 1.2 trở lên. | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-016 | Foundations | _TBD_ |
| NFR-SEC-002 | Mật khẩu tối thiểu 8 ký tự theo chính sách mật khẩu của Frappe bật ở mức 2… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | Foundations | _TBD_ |
| NFR-SEC-003 | 100% DocType nghiệp vụ có khai báo quyền theo vai trò; không DocType nào để… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-016 | Foundations | _TBD_ |
| NFR-SEC-004 | Khóa truy cập dịch vụ AI lưu ở dạng mã hóa, không hiển thị lại trên giao diện… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-005 | _TBD_ | _TBD_ |
| NFR-SEC-005 | 0 lần gọi AI chứa dữ liệu thuộc nhóm cấm của FR-AI-011, kiểm bằng kiểm thử tự… | Must | Active | REF-01 mục 12; ràng buộc C-08 | — | ADR-007 | _TBD_ | _TBD_ |
| NFR-SEC-006 | Nhật ký AI và nhật ký thay đổi được lưu tối thiểu 10 năm. | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-014 | _TBD_ | _TBD_ |
| NFR-USE-001 | 100% nhãn, thông báo và tệp xuất bằng tiếng Việt. | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-010 | Foundations | _TBD_ |
| NFR-USE-002 | Sau 60 phút hướng dẫn, người soạn tạo được một dự thảo quy trình 10 bước và… | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-010 | _TBD_ | _TBD_ |
| NFR-USE-003 | Phiếu bấm giờ thao tác được trên máy tính bảng màn hình từ 768 px bề ngang,… | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-010 | _TBD_ | _TBD_ |
| NFR-USE-004 | Các trang tùy biến đạt tương phản chữ tối thiểu 4,5:1 và thao tác được bằng… | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | _TBD_ | _TBD_ |
| NFR-CMP-001 | Chạy trên Frappe Framework v15, không cần ERPNext; trình duyệt Chrome và Edge… | Must | Active | Ràng buộc C-01, C-02 | — | ADR-001 | _TBD_ | _TBD_ |
| NFR-CPL-001 | 100% dòng chi phí trong bảng giải trình có liên kết đến bước quy trình hoặc… | Must | Active | REF-01 (tính đúng, tính đủ, có giải trình) | — | ADR-002 | _TBD_ | _TBD_ |
| NFR-CPL-002 | Cấu trúc cột của các tệp xuất theo Phụ lục II đến V khớp mẫu chính thức của… | Must | Active | REF-03 | — | ADR-015 | _TBD_ | _TBD_ |
| NFR-CPL-003 | 100% dòng chi phí cận lâm sàng trong bảng giải trình hiển thị cấp phát sinh,… | Must | Active | REF-08; REF-09 | — | ADR-017 | FEAT-036 | _TBD_ |
| NFR-MNT-001 | Bộ máy tính giá có kiểm thử đơn vị phủ tối thiểu 90% số dòng mã; bộ dữ liệu… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-003 | Foundations | _TBD_ |
| NFR-MNT-002 | Mỗi tính năng nghiệm thu có tài liệu As-Built và đạt Definition of Done ở… | Must | Active | Ràng buộc C-06 | — | _TBD_ | Foundations | _TBD_ |
| NFR-MNT-003 | 100% fieldname bằng tiếng Anh dạng snake_case; 100% label bằng tiếng Việt. | Must | Active | Ràng buộc C-05 | — | ADR-001 | Foundations | _TBD_ |
| NFR-LOC-001 | Số hiển thị theo định dạng `1.234.567`; tiền là đồng Việt Nam không có phần… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | Foundations | _TBD_ |
| NFR-OBS-001 | Mọi tác vụ nền (tách văn bản, gọi AI, tính giá, xuất tệp) ghi trạng thái,… | Must | Active | BA đề xuất, chờ chủ dự án xác nhận | — | ADR-009 | Foundations | _TBD_ |
| NFR-OBS-002 | Số token và số lần gọi AI theo tháng xem được theo mục đích sử dụng. | Should | Active | BA đề xuất, chờ chủ dự án xác nhận | — | _TBD_ | Foundations | _TBD_ |

## Phụ lục A — Test case dự kiến theo yêu cầu

Bảng này chỉ để tra cứu; không thay cho cột Test ref.

| Req ID | Test case dự kiến |
| :-- | :-- |
| FR-ACC-001 | TC-ACC-05 |
| FR-ACC-002 | TC-ACC-04, TC-CLS-44 |
| FR-ACC-003 | TC-ACC-01 |
| FR-ACC-004 | TC-ACC-02, TC-CLS-44 |
| FR-ACC-005 | TC-ACC-03 |
| FR-ACC-007 | TC-CLS-44 |
| FR-ACC-008 | TC-CLS-22 |
| FR-LIB-001 | TC-LIB-01 |
| FR-LIB-002 | TC-LIB-02 |
| FR-LIB-003 | TC-LIB-01 |
| FR-LIB-005 | TC-LIB-03 |
| FR-LIB-006 | TC-LIB-04 |
| FR-LIB-007 | TC-LIB-05 |
| FR-LIB-008 | TC-LIB-06 |
| FR-LIB-009 | TC-LIB-07 |
| FR-LIB-010 | TC-LIB-08 |
| FR-LIB-013 | TC-CLS-41 |
| FR-SVC-001 | TC-SVC-01 |
| FR-SVC-002 | TC-SVC-01 |
| FR-SVC-003 | TC-SVC-04 |
| FR-SVC-004 | TC-SVC-03 |
| FR-SVC-006 | TC-SVC-02 |
| FR-SVC-007 | TC-SVC-02 |
| FR-SVC-008 | TC-CLS-20 |
| FR-SVC-009 | TC-CLS-21 |
| FR-PROC-001 | TC-PROC-01 |
| FR-PROC-002 | TC-PROC-02 |
| FR-PROC-003 | TC-PROC-03 |
| FR-PROC-004 | TC-PROC-04 |
| FR-PROC-006 | TC-PROC-03 |
| FR-PROC-007 | TC-PROC-09 |
| FR-PROC-008 | TC-PROC-05 |
| FR-PROC-009 | TC-PROC-08 |
| FR-PROC-010 | TC-PROC-07 |
| FR-PROC-012 | TC-PROC-06 |
| FR-AI-001 | TC-AI-01 |
| FR-AI-002 | TC-AI-01 |
| FR-AI-003 | TC-AI-03 |
| FR-AI-004 | TC-AI-04 |
| FR-AI-005 | TC-AI-02 |
| FR-AI-008 | TC-AI-10 |
| FR-AI-009 | TC-AI-08 |
| FR-AI-010 | TC-AI-05 |
| FR-AI-011 | TC-AI-06 |
| FR-AI-012 | TC-AI-11 |
| FR-AI-013 | TC-AI-09 |
| FR-AI-015 | TC-AI-07 |
| FR-AI-016 | TC-CLS-41 |
| FR-AI-017 | TC-CLS-42 |
| FR-AI-018 | TC-CLS-43 |
| FR-WF-001 | TC-WF-01 |
| FR-WF-002 | TC-WF-01 |
| FR-WF-003 | TC-WF-08 |
| FR-WF-004 | TC-WF-01 |
| FR-WF-005 | TC-WF-01 |
| FR-WF-006 | TC-WF-04 |
| FR-WF-007 | TC-WF-02 |
| FR-WF-008 | TC-WF-03 |
| FR-WF-009 | TC-WF-05 |
| FR-WF-010 | TC-WF-07 |
| FR-WF-011 | TC-WF-06 |
| FR-RES-001 | TC-RES-09 |
| FR-RES-002 | TC-CLS-46 |
| FR-RES-003 | TC-RES-02 |
| FR-RES-004 | TC-RES-01, TC-CLS-45 |
| FR-RES-005 | TC-CLS-48 |
| FR-RES-006 | TC-RES-03 |
| FR-RES-007 | TC-RES-04, TC-CLS-11 |
| FR-RES-008 | TC-RES-10 |
| FR-RES-009 | TC-CLS-50 |
| FR-RES-010 | TC-RES-05 |
| FR-RES-011 | TC-RES-06 |
| FR-RES-012 | TC-RES-08 |
| FR-RES-014 | TC-RES-07 |
| FR-RES-015 | TC-RES-11 |
| FR-RES-016 | TC-CLS-46 |
| FR-RES-017 | TC-CLS-46 |
| FR-RES-018 | TC-CLS-47 |
| FR-RES-019 | TC-CLS-48 |
| FR-RES-020 | TC-CLS-12, TC-CLS-48 |
| FR-RES-021 | TC-CLS-07 |
| FR-RES-022 | TC-CLS-13, TC-CLS-48 |
| FR-RES-023 | TC-CLS-09 |
| FR-RES-024 | TC-CLS-49 |
| FR-RES-025 | TC-CLS-49 |
| FR-RES-026 | TC-CLS-09 |
| FR-NORM-001 | TC-NORM-01 |
| FR-NORM-002 | TC-NORM-02 |
| FR-NORM-003 | TC-NORM-10 |
| FR-NORM-004 | TC-NORM-04 |
| FR-NORM-005 | TC-NORM-09 |
| FR-NORM-006 | TC-NORM-03 |
| FR-NORM-007 | TC-NORM-03 |
| FR-NORM-008 | TC-NORM-11 |
| FR-NORM-009 | TC-NORM-12 |
| FR-NORM-010 | TC-NORM-05 |
| FR-NORM-011 | TC-NORM-06 |
| FR-NORM-012 | TC-NORM-06 |
| FR-NORM-013 | TC-NORM-07 |
| FR-NORM-015 | TC-NORM-08 |
| FR-NORM-017 | TC-CLS-29, TC-CLS-33 |
| FR-NORM-018 | TC-CLS-30 |
| FR-NORM-019 | TC-CLS-03, TC-CLS-30 |
| FR-NORM-020 | TC-CLS-32 |
| FR-NORM-021 | TC-CLS-29 |
| FR-NORM-022 | TC-CLS-29 |
| FR-NORM-023 | TC-CLS-32 |
| FR-NORM-024 | TC-CLS-31 |
| FR-NORM-025 | TC-CLS-33 |
| FR-TS-001 | TC-TS-04 |
| FR-TS-002 | TC-TS-05 |
| FR-TS-003 | TC-TS-01 |
| FR-TS-004 | TC-TS-02 |
| FR-TS-005 | TC-TS-03 |
| FR-ACCT-001 | TC-ACCT-01 |
| FR-ACCT-002 | TC-ACCT-02 |
| FR-ACCT-003 | TC-ACCT-01 |
| FR-ACCT-004 | TC-ACCT-04 |
| FR-ACCT-005 | TC-ACCT-03 |
| FR-ACCT-006 | TC-ACCT-06 |
| FR-ACCT-007 | TC-ACCT-05 |
| FR-ACCT-008 | TC-ACCT-07 |
| FR-ACCT-009 | TC-ACCT-08 |
| FR-ACCT-010 | TC-ACCT-09 |
| FR-ACCT-012 | TC-CLS-34 |
| FR-ACCT-013 | TC-CLS-34 |
| FR-ACCT-014 | TC-CLS-35 |
| FR-ACCT-015 | TC-CLS-36 |
| FR-COST-001 | TC-COST-19 |
| FR-COST-002 | TC-COST-17 |
| FR-COST-003 | TC-COST-01 |
| FR-COST-004 | TC-COST-02 |
| FR-COST-005 | TC-COST-03, TC-COST-16 |
| FR-COST-006 | TC-COST-04, TC-COST-12, TC-COST-13 |
| FR-COST-007 | TC-COST-06, TC-CLS-14 |
| FR-COST-008 | TC-COST-05 |
| FR-COST-009 | TC-COST-05, TC-COST-10 |
| FR-COST-010 | TC-COST-15 |
| FR-COST-011 | TC-COST-09 |
| FR-COST-012 | TC-COST-11 |
| FR-COST-013 | TC-COST-18 |
| FR-COST-014 | TC-COST-08 |
| FR-COST-015 | TC-COST-14 |
| FR-COST-016 | TC-COST-07 |
| FR-COST-017 | TC-CLS-08 |
| FR-COST-018 | TC-CLS-01, TC-CLS-02 |
| FR-COST-019 | TC-CLS-03, TC-CLS-04, TC-CLS-05 |
| FR-COST-020 | TC-CLS-06 |
| FR-COST-021 | TC-CLS-07, TC-CLS-09 |
| FR-COST-022 | TC-CLS-10 |
| FR-COST-023 | TC-CLS-15 |
| FR-COST-024 | TC-CLS-51 |
| FR-COST-025 | TC-CLS-37 |
| FR-COST-026 | TC-CLS-16 |
| FR-COST-027 | TC-CLS-17 |
| FR-COST-028 | TC-CLS-18 |
| FR-COST-029 | TC-CLS-19 |
| FR-COST-030 | TC-CLS-40 |
| FR-COST-031 | TC-CLS-38 |
| FR-COST-032 | TC-CLS-38 |
| FR-BM-001 | TC-BM-06 |
| FR-BM-002 | TC-BM-01 |
| FR-BM-003 | TC-BM-05 |
| FR-BM-004 | TC-BM-01 |
| FR-BM-005 | TC-BM-03 |
| FR-BM-006 | TC-BM-04 |
| FR-BM-007 | TC-BM-02 |
| FR-ADJ-001 | TC-ADJ-01 |
| FR-ADJ-002 | TC-ADJ-02 |
| FR-ADJ-003 | TC-ADJ-03 |
| FR-ADJ-005 | TC-ADJ-04 |
| FR-ADJ-006 | TC-ADJ-05 |
| FR-ADJ-007 | TC-ADJ-06 |
| FR-ADJ-009 | TC-ADJ-07 |
| FR-ADJ-010 | TC-ADJ-08 |
| FR-PRICE-001 | TC-PRICE-01 |
| FR-PRICE-002 | TC-PRICE-02 |
| FR-PRICE-003 | TC-PRICE-03 |
| FR-PRICE-004 | TC-PRICE-04 |
| FR-PRICE-005 | TC-PRICE-04 |
| FR-PRICE-006 | TC-PRICE-05 |
| FR-PRICE-007 | TC-PRICE-06 |
| FR-PRICE-008 | TC-PRICE-06 |
| FR-PRICE-009 | TC-PRICE-07 |
| FR-PRICE-010 | TC-PRICE-05 |
| FR-OUT-001 | TC-OUT-01 |
| FR-OUT-002 | TC-OUT-01 |
| FR-OUT-004 | TC-OUT-01 |
| FR-OUT-005 | TC-OUT-02 |
| FR-OUT-006 | TC-OUT-04 |
| FR-OUT-007 | TC-OUT-05 |
| FR-OUT-008 | TC-OUT-03 |
| FR-OUT-011 | TC-CLS-33 |
| FR-OUT-012 | TC-CLS-39 |
| FR-AUD-001 | TC-AUD-01 |
| FR-AUD-002 | TC-AUD-02 |
| FR-AUD-003 | TC-AUD-03, TC-CLS-44 |
| FR-AUD-004 | TC-OUT-03 |
| FR-NOTI-001 | TC-NOTI-01 |
| FR-NOTI-003 | TC-NOTI-01 |
| FR-ADM-001 | TC-ADM-01 |
| FR-ADM-002 | TC-ADM-02 |
| FR-ADM-003 | TC-ADM-03 |
| FR-ADM-004 | TC-ADM-04 |
| FR-ADM-005 | TC-ADM-05 |
| FR-ADM-006 | TC-CLS-28 |
| FR-CLS-001 | TC-CLS-20 |
| FR-CLS-002 | TC-CLS-20 |
| FR-CLS-003 | TC-CLS-15 |
| FR-CLS-004 | TC-CLS-10 |
| FR-CLS-005 | TC-CLS-13 |
| FR-CLS-006 | TC-CLS-23 |
| FR-CLS-007 | TC-CLS-20 |
| FR-CLS-008 | TC-CLS-23 |
| FR-QC-001 | TC-CLS-24 |
| FR-QC-002 | TC-CLS-24 |
| FR-QC-003 | TC-CLS-24 |
| FR-QC-004 | TC-CLS-10 |
| FR-QC-005 | TC-CLS-25 |
| FR-QC-006 | TC-CLS-02 |
| FR-QC-007 | TC-CLS-26 |
| FR-QC-008 | TC-CLS-25 |
| FR-CMP-001 | TC-CLS-27 |
| FR-CMP-002 | TC-CLS-07 |
| FR-CMP-003 | TC-CLS-07 |
| FR-CMP-004 | TC-CLS-08 |
| FR-CMP-005 | TC-CLS-28 |
| FR-CMP-006 | TC-CLS-37 |
| FR-CMP-007 | TC-CLS-28 |
| NFR-PERF-001 | TC-NFR-01 |
| NFR-PERF-002 | TC-COST-14 |
| NFR-AVL-002 | TC-NFR-02 |
| NFR-REL-001 | TC-COST-09, TC-CLS-38 |
| NFR-REL-003 | TC-CLS-01 |
| NFR-SEC-004 | TC-NFR-04 |
| NFR-SEC-005 | TC-CLS-41 |
| NFR-USE-003 | TC-NFR-05 |
| NFR-CPL-001 | TC-COST-15 |
| NFR-CPL-002 | TC-OUT-01 |
| NFR-CPL-003 | TC-CLS-38 |
| NFR-MNT-003 | TC-NFR-03 |

## Phụ lục B — Thay đổi ở bản 1.1

**Yêu cầu mới (78):** FR-ACC-007, FR-ACC-008, FR-LIB-013, FR-SVC-008, FR-SVC-009, FR-SVC-010, FR-SVC-011, FR-AI-016, FR-AI-017, FR-AI-018, FR-RES-016, FR-RES-017, FR-RES-018, FR-RES-019, FR-RES-020, FR-RES-021, FR-RES-022, FR-RES-023, FR-RES-024, FR-RES-025, FR-RES-026, FR-NORM-017, FR-NORM-018, FR-NORM-019, FR-NORM-020, FR-NORM-021, FR-NORM-022, FR-NORM-023, FR-NORM-024, FR-NORM-025, FR-ACCT-012, FR-ACCT-013, FR-ACCT-014, FR-ACCT-015, FR-COST-017, FR-COST-018, FR-COST-019, FR-COST-020, FR-COST-021, FR-COST-022, FR-COST-023, FR-COST-024, FR-COST-025, FR-COST-026, FR-COST-027, FR-COST-028, FR-COST-029, FR-COST-030, FR-COST-031, FR-COST-032, FR-OUT-011, FR-OUT-012, FR-ADM-006, FR-CLS-001, FR-CLS-002, FR-CLS-003, FR-CLS-004, FR-CLS-005, FR-CLS-006, FR-CLS-007, FR-CLS-008, FR-QC-001, FR-QC-002, FR-QC-003, FR-QC-004, FR-QC-005, FR-QC-006, FR-QC-007, FR-QC-008, FR-CMP-001, FR-CMP-002, FR-CMP-003, FR-CMP-004, FR-CMP-005, FR-CMP-006, FR-CMP-007, NFR-REL-003, NFR-CPL-003.

**Yêu cầu sửa, giữ nguyên mã (9):** FR-ACC-002, FR-ACC-004, FR-RES-002, FR-RES-004, FR-RES-005, FR-RES-007, FR-RES-009, FR-AUD-003, FR-COST-014. Nội dung sửa ghi ở cột ghi chú của `docs/srs.md`.

**Dòng của yêu cầu có từ bản 1.0 được ghi thêm truy vết ở bản 1.1**

| Req ID | Cột | Thêm |
| :-- | :-- | :-- |
| FR-ACC-002 | Use case | UC-026 |
| FR-ACC-002 | Plan ref | FEAT-039 |
| FR-ACC-004 | Use case | UC-026 |
| FR-ACC-004 | Plan ref | FEAT-039 |
| FR-AUD-003 | Use case | UC-026 |
| FR-AUD-003 | Plan ref | FEAT-039 |

Không dòng nào của bản 1.0 bị bớt truy vết.
