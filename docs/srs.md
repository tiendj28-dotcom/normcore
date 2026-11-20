# Software Requirements Specification: Normcore

> Version: 1.1 · Status: Draft (chờ chủ dự án rà soát) · Last updated: 2026-11-13
> Requirement syntax: EARS (viết bằng tiếng Việt: **Khi** = When, **Trong khi** = While, **Ở nơi** = Where, **Nếu … thì** = If … then, **Hệ thống phải** = The system shall)

## Revision History

| Version | Date | Author | Changes |
| :------ | :--- | :----- | :------ |
| 1.0 | 2026-11-13 | BA (Claude, theo ý tưởng sản phẩm của chủ dự án) | Bản đặc tả đầu tiên. Lập từ tài liệu "Normcore – Ý tưởng sản phẩm" và 4 quyết định chốt ngày 13/11/2026 (mục 2.5). Chưa qua phỏng vấn người dùng cuối; các giả định nằm ở Phụ lục B. |
| 1.1 | 2026-11-13 | BA (Claude, theo quyết định của chủ dự án) | Hợp nhất phân hệ E (cận lâm sàng) theo TBD-13 và 11 điểm X-01 đến X-11 của `docs/phan-he-e-hop-nhat.md`. **Thêm 76 FR:** FR-ACC-007, 008; FR-LIB-013; FR-SVC-008 đến 011; FR-AI-016 đến 018; FR-RES-016 đến 026; FR-NORM-017 đến 025; FR-ACCT-012 đến 015; FR-COST-017 đến 032; FR-OUT-011, 012; FR-ADM-006; ba nhóm mới FR-CLS-001 đến 008, FR-QC-001 đến 008, FR-CMP-001 đến 007. **Thêm:** NFR-REL-003, NFR-CPL-003; IF-07, IF-08; BR-CLS-001 đến 017 (mục 3.4.5); G-06; C-09, C-10; A-07, A-08; REF-08 đến REF-10; TBD-14 đến TBD-18. **Sửa (giữ nguyên mã):** FR-ACC-002, FR-ACC-004, FR-RES-002, FR-RES-004, FR-RES-005, FR-RES-007, FR-RES-009, FR-COST-014 (ghi chú), FR-AUD-003, BR-COST-004, IF-04; mục 1.2, 2.1, 2.2, 2.3 và 3.4.3 cập nhật theo. **Đóng:** TBD-13. Không có yêu cầu nào bị bỏ. Tác động đến tài liệu khác: Phụ lục C. |

## 1. Introduction

### 1.1 Purpose

Tài liệu này đặc tả đầy đủ yêu cầu của phần mềm Normcore để đội phát triển xây dựng trên Frappe v15. Đây là nguồn gốc duy nhất cho yêu cầu; các tài liệu kiến trúc (`docs/architecture.md`), mô hình dữ liệu (`docs/data-model.md`), UX (`docs/ux-foundations.md`), kế hoạch build (`docs/implementation-plan.md`) và test case (`docs/test-cases.md`) đều dẫn chiếu ID trong tài liệu này.

Người đọc: lập trình viên Frappe, người kiểm thử, chủ dự án, chuyên gia nghiệp vụ định giá.

### 1.2 Product vision & scope

**Vấn đề.** Bệnh viện xây dựng quy trình kỹ thuật (QTKT), định mức kinh tế - kỹ thuật (KTKT) và giá dịch vụ khám bệnh, chữa bệnh (KCB) như ba việc rời nhau, trên Word và Excel. Quy trình đổi thì định mức không đổi theo; con số trong giá không truy được về căn cứ.

**Tầm nhìn.** Một chuỗi dữ liệu liền mạch: quy trình được phê duyệt là gốc; định mức bóc từ từng bước của quy trình; giá thành tính từ định mức và số liệu kế toán; giá đề xuất được so sánh và điều chỉnh có kiểm soát. Mỗi con số trong giá truy ngược được về một bước quy trình, một dòng định mức, một đơn giá có chứng từ hoặc một tiêu chí phân bổ.

**Trong phạm vi (v1.0).**

| Phân hệ | Nội dung |
| :-- | :-- |
| A. Quy trình | Thư viện văn bản pháp lý có quản lý hiệu lực; danh mục kỹ thuật; soạn QTKT có cấu trúc với AI hỗ trợ; phê duyệt ba cấp; quản lý phiên bản; in ban hành |
| B. Định mức | Bóc tách định mức theo bước và theo 6 cấu phần trực tiếp; khảo sát bấm giờ; xác nhận chuyên môn và tài chính |
| C. Giá thành | Danh mục nguồn lực và đơn giá; bộ tham số; nhập số liệu kế toán và sản lượng; phân bổ; tính giá; đối soát; bảng giải trình |
| D. So sánh và phương án giá | Kho giá tham chiếu; so sánh; gợi ý điều chỉnh theo quy tắc; kịch bản điều chỉnh; phương án giá và phê duyệt; xuất biểu theo Thông tư 21/2024/TT-BYT |
| E. Cận lâm sàng | Định mức và giá thành một kết quả xét nghiệm, một ca chẩn đoán hình ảnh: hệ thống xét nghiệm (dịch vụ gắn với thiết bị); hình thức có máy; kế hoạch nội kiểm, chuẩn máy, ngoại kiểm; hồ sơ kiểm định, hiệu chuẩn; hệ số tiêu hao thực tế; chi phí theo mẻ, theo ngày-máy, theo kỳ; đối soát vật chất với xuất kho và đối soát sản lượng |

Phân hệ E không phải một chuỗi riêng. Nó mở rộng chuỗi của phân hệ B và C: dịch vụ cận lâm sàng vẫn đi qua quy trình đã ban hành, bộ định mức, lần tính giá, phân bổ và phương án giá như mọi dịch vụ khác (C-09).

**Ngoài phạm vi (v1.0).**

- Kết nối trực tuyến với HIS, LIS, RIS, phần mềm kho và phần mềm kế toán (v1.0 nhập bằng tệp Excel).
- Theo dõi tiêu hao thực tế theo ca bệnh; cảnh báo vượt định mức theo thời gian thực.
- Bộ ánh xạ kế toán doanh nghiệp cho bệnh viện tư.
- Tự thu thập văn bản pháp lý từ internet; văn bản do người dùng nạp.
- Thanh toán, viện phí, bảo hiểm y tế.
- Ứng dụng di động riêng (dùng giao diện web đáp ứng trên máy tính bảng).
- Quản lý chất lượng xét nghiệm (ghi kết quả nội kiểm, biểu đồ kiểm soát, đánh giá ngoại kiểm). Normcore chỉ dùng kế hoạch và chi phí của các hoạt động này để tính giá.

**Ranh giới MVP.** Bản phát hành 1 gồm phân hệ B và C, phần soạn quy trình thủ công và luồng duyệt của phân hệ A, và phân hệ E cho hai nhóm chuyên ngành hóa sinh và miễn dịch (C-10). AI và thư viện văn bản thuộc bản phát hành 2; phân hệ D thuộc bản phát hành 3. Các nhóm cận lâm sàng còn lại (huyết học, vi sinh, giải phẫu bệnh, chẩn đoán hình ảnh, thăm dò chức năng) dùng cùng mô hình và được đưa vào ở các bản sau. Chi tiết ở `docs/implementation-plan.md`.

### 1.3 Goals & success metrics

| Mã | Mục tiêu | Thước đo |
| :-- | :-- | :-- |
| G-01 | Giá truy vết được | 100% dòng chi phí của một dịch vụ có liên kết đến bước quy trình và nguồn đơn giá hoặc quy tắc phân bổ |
| G-02 | Tính đúng, tính đủ | Chênh lệch đối soát giữa số đã tính và số kế toán của mỗi khoa nằm trong ngưỡng cấu hình (mặc định 10%) hoặc có giải trình |
| G-03 | Giảm công soạn quy trình | Bác sĩ có dự thảo đầy đủ cấu trúc trong không quá 15 phút kể từ lúc nhập yêu cầu |
| G-04 | Tính lại nhanh khi tham số đổi | Tính lại 500 dịch vụ trong không quá 5 phút |
| G-05 | Hồ sơ đạt yêu cầu thẩm định | Xuất được đủ các biểu theo Phụ lục II đến V Thông tư 21/2024/TT-BYT từ một lần tính giá |
| G-06 | Giá một kết quả cận lâm sàng phản ánh tiêu hao thực | 100% hệ thống xét nghiệm trong phạm vi tính giá có hệ số tiêu hao k; chênh lệch đối soát vật chất của mỗi mặt hàng nằm trong ngưỡng cấu hình (mặc định 5%) hoặc có giải trình |

### 1.4 Definitions, acronyms & abbreviations

Xem Phụ lục A.

### 1.5 References

| Mã | Tài liệu | Ghi chú |
| :-- | :-- | :-- |
| REF-01 | Normcore – Ý tưởng sản phẩm (13/11/2026) | Tài liệu đầu vào chính |
| REF-02 | Luật Khám bệnh, chữa bệnh 15/2023/QH15; Nghị định 96/2023/NĐ-CP | Khung giá dịch vụ KCB |
| REF-03 | Thông tư 21/2024/TT-BYT | Phương pháp định giá dịch vụ KCB; Phụ lục I đến V |
| REF-04 | Thông tư 23/2024/TT-BYT | Danh mục kỹ thuật trong KCB |
| REF-05 | Các quyết định "Hướng dẫn quy trình kỹ thuật" của Bộ Y tế theo chuyên khoa | Nguồn tri thức cho AI |
| REF-06 | Thông tư 24/2024/TT-BTC | Chế độ kế toán hành chính, sự nghiệp |
| REF-07 | Nghị định 60/2021/NĐ-CP, sửa đổi bởi Nghị định 111/2025/NĐ-CP | Cơ chế tự chủ tài chính đơn vị sự nghiệp công lập |
| REF-08 | Normcore – Phân hệ E: tài liệu ý tưởng và bộ nháp phân tích nghiệp vụ (13/11/2026) | Nguồn của các yêu cầu thêm ở bản 1.1; bộ nháp không dùng để xây dựng |
| REF-09 | Phương án hợp nhất Phân hệ E vào bộ tài liệu A–D (`docs/phan-he-e-hop-nhat.md`) | 6 quyết định và 11 điểm xung đột đã được chủ dự án chấp thuận ngày 13/11/2026 |
| REF-10 | Thông tư 01/2013/TT-BYT ngày 11/01/2013 hướng dẫn thực hiện quản lý chất lượng xét nghiệm tại cơ sở khám bệnh, chữa bệnh; Quyết định 2429/QĐ-BYT ngày 12/6/2017 ban hành tiêu chí đánh giá mức chất lượng phòng xét nghiệm y học | Căn cứ của nội kiểm, ngoại kiểm. Tên và ngày ban hành đã kiểm ngày 13/11/2026; nội dung chưa đối chiếu toàn văn. Một trang tra cứu văn bản ghi Thông tư 01/2013 đã được sửa đổi, bổ sung bởi Thông tư 25/2026/TT-BYT; nội dung sửa đổi chưa được kiểm. Xem TBD-18 |

REF-03 đã được đối chiếu ở mức Điều 1 đến 8 và Phụ lục I đến III. Phụ lục IV, V và REF-04, REF-06, REF-10 chưa được đối chiếu toàn văn (xem TBD-01, TBD-03, TBD-18).

## 2. Overall Description

### 2.1 Product perspective

Normcore là một ứng dụng Frappe v15 độc lập, cài trên một site riêng cho mỗi bệnh viện. Hệ thống không phụ thuộc ERPNext.

Tác nhân và hệ thống bên ngoài:

| Bên ngoài | Quan hệ |
| :-- | :-- |
| Người dùng bệnh viện (10 lớp, mục 2.3) | Dùng qua trình duyệt |
| Dịch vụ mô hình ngôn ngữ (AI) | Normcore gọi qua HTTPS; nhà cung cấp cấu hình được |
| Phần mềm kế toán của bệnh viện | Xuất tệp Excel; người dùng nạp vào Normcore |
| HIS | Xuất tệp sản lượng dịch vụ; người dùng nạp vào Normcore |
| LIS, RIS | Xuất tệp số kết quả trả và số test nội kiểm, chuẩn máy, chạy lại theo dịch vụ và thiết bị; người dùng nạp vào Normcore |
| Phần mềm kho, dược | Xuất tệp lượng xuất kho theo mặt hàng và khoa; người dùng nạp vào Normcore |
| Máy chủ email (tùy chọn) | Gửi thông báo |
| Cơ quan thẩm định giá | Nhận hồ sơ do Normcore xuất; không truy cập hệ thống |

### 2.2 Product functions (summary)

21 nhóm chức năng, đặc tả tại mục 3.1: truy cập và phân quyền (ACC), thư viện văn bản (LIB), danh mục kỹ thuật (SVC), soạn quy trình (PROC), hỗ trợ AI (AI), phê duyệt và phiên bản (WF), nguồn lực và tham số (RES), định mức (NORM), bấm giờ (TS), số liệu kế toán (ACCT), tính giá (COST), giá tham chiếu (BM), so sánh và điều chỉnh (ADJ), phương án giá (PRICE), đầu ra (OUT), nhật ký (AUD), thông báo (NOTI), quản trị (ADM), hệ thống xét nghiệm (CLS), kế hoạch chất lượng xét nghiệm (QC), hồ sơ tuân thủ thiết bị (CMP).

### 2.3 User classes & characteristics

| Lớp người dùng | Vai trò hệ thống | Bối cảnh và nhu cầu |
| :-- | :-- | :-- |
| Bác sĩ, điều dưỡng trưởng, kỹ thuật viên trưởng khoa cận lâm sàng (người soạn) | NC Clinician | Bận lâm sàng, dùng máy tính của khoa và máy tính bảng. Cần dự thảo nhanh, sửa dễ, không phải học phần mềm phức tạp. Ở khoa cận lâm sàng: khai hệ thống xét nghiệm, kế hoạch chất lượng và định mức |
| Trưởng khoa | NC Department Head | Chịu trách nhiệm chuyên môn. Cần xem khác biệt so với hướng dẫn của Bộ và duyệt nhanh |
| Thành viên hội đồng chuyên môn | NC Council Member | Thẩm định theo đợt. Cần ghi ý kiến gắn vào từng bước |
| Chuyên viên tài chính kế toán | NC Finance | Thành thạo Excel. Cần nạp số liệu, kiểm soát phân bổ, xuất biểu |
| Dược, Vật tư - Thiết bị y tế | NC Resource Manager | Quản lý danh mục và đơn giá có chứng từ; quản lý thiết bị, hình thức có máy và hồ sơ kiểm định, hiệu chuẩn |
| Kế hoạch tổng hợp, Quản lý chất lượng | NC Document Controller | Quản lý văn bản, danh mục kỹ thuật, phiên bản quy trình |
| Ban giám đốc | NC Director | Ban hành quy trình, phê duyệt giá. Cần bức tranh tổng hợp và điểm bất thường |
| Quản trị hệ thống | NC Admin | Cấu hình, người dùng, AI, sao lưu |
| Kiểm soát nội bộ, thanh tra | NC Auditor | Đọc toàn bộ dữ liệu và nhật ký để kiểm tra; không tạo, sửa, duyệt |
| Tư vấn triển khai (tùy chọn) | NC Consultant | Hỗ trợ khảo sát định mức và lập hồ sơ; quyền đọc rộng, quyền ghi hạn chế |

### 2.4 Operating environment

- Máy chủ: Frappe Framework v15, MariaDB, Redis, chạy trên Linux; triển khai tại hạ tầng bệnh viện hoặc đám mây.
- Máy trạm: trình duyệt Chrome hoặc Edge trên máy tính; Chrome hoặc Safari trên máy tính bảng từ 10 inch cho phiếu bấm giờ.
- Mạng: máy chủ cần đường ra internet tới dịch vụ AI nếu dùng AI qua API bên ngoài.

### 2.5 Constraints

| Mã | Ràng buộc | Nguồn |
| :-- | :-- | :-- |
| C-01 | Nền tảng Frappe Framework v15 | Chủ dự án |
| C-02 | Ứng dụng độc lập, không yêu cầu cài ERPNext | Quyết định 13/11/2026 |
| C-03 | Khách hàng đầu tiên là bệnh viện công; bộ ánh xạ kế toán theo chế độ hành chính, sự nghiệp (REF-06) làm trước | Quyết định 13/11/2026 |
| C-04 | Nhà cung cấp AI để mở, đổi được bằng cấu hình, không sửa mã | Quyết định 13/11/2026 |
| C-05 | Tên trường (fieldname) tiếng Anh, nhãn (label) tiếng Việt | Quy ước của nhóm phát triển |
| C-06 | Mỗi tính năng nghiệm thu phải có Definition of Done và tài liệu As-Built | Quy định của chủ dự án |
| C-07 | v1.0 không kết nối trực tuyến HIS và kế toán; chỉ nhập tệp | REF-01 |
| C-08 | AI không giữ quyền phê duyệt ở bất kỳ bước nào; phép tính giá do bộ máy tính toán cố định thực hiện | REF-01 |
| C-09 | Phân hệ E dùng chung mô hình dữ liệu, vai trò, bộ máy tính giá, ảnh chụp và luồng duyệt của phân hệ A đến D; không tạo DocType trùng chức năng với DocType đã có | Quyết định 13/11/2026 (REF-09) |
| C-10 | Phân hệ E cho hóa sinh và miễn dịch làm cùng bản phát hành 1; bệnh viện thí điểm có cả máy mua và máy đặt theo hóa chất, hai hình thức được kiểm thử ngang nhau | Quyết định 13/11/2026 (REF-09) |

### 2.6 Assumptions & dependencies

| Mã | Giả định |
| :-- | :-- |
| A-01 | Bệnh viện cung cấp tệp văn bản hướng dẫn QTKT của Bộ Y tế cho chuyên khoa thí điểm |
| A-02 | Phần mềm kế toán của bệnh viện xuất được chi phí theo tài khoản và theo khoa (hoặc bệnh viện chấp nhận phân bổ khi không tách được) |
| A-03 | HIS xuất được sản lượng dịch vụ theo mã dịch vụ và khoa trong năm |
| A-04 | Bệnh viện có mẫu trình bày quy trình ban hành; nếu chưa có, dùng mẫu mặc định của Normcore |
| A-05 | Đơn giá vật tư, thuốc nhập vào là giá đã gồm thuế GTGT (xem TBD-10) |
| A-06 | Mỗi bệnh viện một site; không dùng chung dữ liệu giữa các bệnh viện |
| A-07 | LIS xuất được số kết quả trả theo dịch vụ và thiết bị trong năm. Số test nội kiểm, chuẩn máy, chạy lại có thể không xuất được; khi đó hệ thống ước tính từ kế hoạch chất lượng (FR-QC-006, TBD-16) |
| A-08 | Bệnh viện có số liệu xuất kho theo mặt hàng và khoa trong năm; nếu không có, lần tính giá ghi "Chưa đối soát vật chất" (FR-COST-029) |

## 3. Specific Requirements

### 3.1 Functional requirements

Mức ưu tiên theo MoSCoW cho sản phẩm v1.0. Trạng thái mặc định `Active`. Dòng có ghi "Sửa ở 1.1" giữ nguyên mã và đổi nội dung so với bản 1.0.

#### 3.1.1 Truy cập và phân quyền (ACC)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-ACC-001 | Hệ thống phải yêu cầu người dùng đăng nhập bằng tài khoản của site trước khi truy cập bất kỳ dữ liệu Normcore nào. | Must | Active | Dùng cơ chế đăng nhập của Frappe; chính sách mật khẩu theo NFR-SEC-002. |
| FR-ACC-002 | Hệ thống phải cung cấp 10 vai trò nêu ở mục 2.3 và áp quyền đọc, tạo, sửa, duyệt theo ma trận quyền ở `docs/data-model.md` mục 4. | Must | Active | Một người dùng có thể giữ nhiều vai trò. Sửa ở 1.1: từ 9 lên 10 vai trò, thêm NC Auditor. |
| FR-ACC-003 | Trong khi người dùng chỉ có vai trò NC Clinician hoặc NC Department Head, hệ thống phải giới hạn quyền sửa quy trình, bộ định mức và phiếu bấm giờ trong các khoa người đó được gán. | Must | Active | Quyền đọc quy trình đã ban hành: toàn viện. |
| FR-ACC-004 | Hệ thống phải chỉ cho phép vai trò NC Finance, NC Director, NC Admin và NC Auditor xem số liệu kế toán đã nhập, kết quả phân bổ và bảng đối soát. | Must | Active | NC Consultant xem được khi được cấp riêng. Sửa ở 1.1: thêm NC Auditor. |
| FR-ACC-005 | Nếu người dùng mở bản ghi ngoài phạm vi quyền, thì hệ thống phải từ chối và hiển thị thông báo không đủ quyền mà không lộ nội dung bản ghi. | Must | Active | |
| FR-ACC-006 | Khi NC Admin gán hoặc bỏ gán người dùng khỏi một khoa, hệ thống phải áp phạm vi mới từ lần tải trang kế tiếp của người dùng đó. | Should | Active | |
| FR-ACC-007 | Hệ thống phải cho vai trò NC Auditor quyền chỉ đọc đối với mọi bản ghi nghiệp vụ và nhật ký, và không cho vai trò này quyền tạo, sửa, xóa hay duyệt. | Should | Active | Điểm X-10 của REF-09. |
| FR-ACC-008 | Trong khi người dùng chỉ có vai trò NC Clinician hoặc NC Department Head, hệ thống phải giới hạn quyền sửa hệ thống xét nghiệm và kế hoạch chất lượng trong các khoa người đó được gán. | Must | Active | Cùng nguyên tắc với FR-ACC-003. |

#### 3.1.2 Thư viện văn bản (LIB)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-LIB-001 | Khi NC Document Controller tải lên tệp PDF hoặc DOCX và nhập số hiệu, tên, loại văn bản, cơ quan ban hành, ngày ban hành, ngày hiệu lực, hệ thống phải tạo bản ghi văn bản với trạng thái lập chỉ mục "Chưa lập". | Must | Active | Loại: Luật, Nghị định, Thông tư, Quyết định, Công văn, Tài liệu nội bộ. Tệp tối đa theo NFR-SCAL-002. |
| FR-LIB-002 | Nếu số hiệu văn bản trùng với một bản ghi đã có, thì hệ thống phải từ chối lưu và chỉ ra bản ghi trùng. | Must | Active | So khớp không phân biệt hoa thường và khoảng trắng. |
| FR-LIB-003 | Khi văn bản được lưu kèm tệp, hệ thống phải tách nội dung thành các mục có số mục, tiêu đề, trang bắt đầu, trang kết thúc và văn bản thuần bằng tác vụ nền. | Must | Active | Với văn bản hướng dẫn QTKT, mỗi quy trình trong văn bản là một mục cấp 1. |
| FR-LIB-004 | Nếu tệp PDF không chứa lớp văn bản, thì hệ thống phải nhận dạng ký tự tiếng Việt trước khi tách mục. | Should | Active | Chất lượng nhận dạng: xem TBD-09. |
| FR-LIB-005 | Nếu việc tách mục hoặc nhận dạng ký tự thất bại, thì hệ thống phải đặt trạng thái lập chỉ mục "Lỗi", ghi lý do và thông báo cho người tải lên. | Must | Active | |
| FR-LIB-006 | Khi ngày hệ thống sang ngày mới, hệ thống phải cập nhật trạng thái hiệu lực của mọi văn bản và mục thành "Chưa hiệu lực", "Còn hiệu lực" hoặc "Hết hiệu lực" theo ngày hiệu lực và ngày hết hiệu lực. | Must | Active | Tác vụ định kỳ hằng ngày. |
| FR-LIB-007 | Khi người dùng khai báo văn bản A thay thế toàn bộ văn bản B từ một ngày, hệ thống phải ghi liên kết thay thế và đặt ngày hết hiệu lực của B bằng ngày liền trước ngày đó. | Must | Active | |
| FR-LIB-008 | Khi người dùng khai báo văn bản A thay thế một số mục của văn bản B, hệ thống phải đặt ngày hết hiệu lực cho đúng các mục được chọn và giữ nguyên hiệu lực các mục còn lại. | Must | Active | Ví dụ thực tế: một quyết định bãi bỏ một số quy trình trong quyết định cũ. |
| FR-LIB-009 | Khi một văn bản hoặc mục chuyển sang "Hết hiệu lực", hệ thống phải gắn cờ "Cần rà soát" cho mọi quy trình "Đã ban hành" có trích dẫn văn bản hoặc mục đó và thông báo cho trưởng khoa của khoa chủ trì. | Must | Active | |
| FR-LIB-010 | Khi người dùng tìm kiếm theo từ khóa, số hiệu hoặc mã dịch vụ, hệ thống phải trả về các mục khớp kèm số hiệu văn bản, số mục, trang và trạng thái hiệu lực. | Must | Active | Hiệu năng theo NFR-PERF-005. |
| FR-LIB-011 | Khi người dùng mở một mục, hệ thống phải hiển thị văn bản đã tách bên cạnh trang gốc của tệp để đối chiếu. | Should | Active | |
| FR-LIB-012 | Khi NC Document Controller sửa văn bản thuần của một mục, hệ thống phải lưu bản trước, người sửa và thời điểm sửa. | Should | Active | Dùng để sửa lỗi nhận dạng ký tự. |
| FR-LIB-013 | Khi NC Document Controller nạp tài liệu của hãng sản xuất (hướng dẫn sử dụng hóa chất, thiết bị), hệ thống phải lưu tài liệu với loại "Tài liệu của hãng", yêu cầu gắn với mặt hàng hoặc thiết bị liên quan và tách mục như FR-LIB-003. | Should | Active | Nguồn cho FR-AI-016. Số hiệu là mã tài liệu của hãng kèm phiên bản. |

#### 3.1.3 Danh mục kỹ thuật (SVC)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-SVC-001 | Khi NC Document Controller nhập tệp Excel danh mục kỹ thuật theo mẫu (mã, tên, chuyên khoa), hệ thống phải tạo mới hoặc cập nhật dịch vụ kỹ thuật theo mã. | Must | Active | Mã theo danh mục của REF-04. |
| FR-SVC-002 | Nếu một dòng nhập thiếu mã hoặc tên, hoặc trùng mã trong cùng tệp, thì hệ thống phải bỏ qua dòng đó và liệt kê trong báo cáo lỗi nhập. | Must | Active | |
| FR-SVC-003 | Khi người dùng gán khoa thực hiện cho một dịch vụ, hệ thống phải lưu quan hệ dịch vụ - khoa và cho phép một dịch vụ có nhiều khoa thực hiện. | Must | Active | |
| FR-SVC-004 | Khi người dùng mở một dịch vụ, hệ thống phải hiển thị tình trạng chuỗi của dịch vụ: quy trình hiện hành, bộ định mức hiện hành theo khoa, giá thành của lần tính gần nhất, giá đã duyệt theo loại giá. | Must | Active | |
| FR-SVC-005 | Khi hệ thống tách xong một văn bản hướng dẫn QTKT, hệ thống phải đề xuất ánh xạ từng mục quy trình với một dịch vụ kỹ thuật theo mã hoặc theo tên, kèm độ tin cậy. | Should | Active | Khớp chính xác theo mã: độ tin cậy 100%. |
| FR-SVC-006 | Khi NC Document Controller xác nhận hoặc sửa một ánh xạ, hệ thống phải lưu ánh xạ ở trạng thái "Đã xác nhận" kèm người xác nhận và thời điểm. | Must | Active | |
| FR-SVC-007 | Trong khi một ánh xạ chưa ở trạng thái "Đã xác nhận", hệ thống phải không dùng mục đó làm nguồn khi AI soạn dự thảo. | Must | Active | |
| FR-SVC-008 | Khi NC Document Controller đánh dấu một dịch vụ kỹ thuật thuộc khối cận lâm sàng, hệ thống phải yêu cầu nhóm chuyên ngành và đơn vị kết quả của dịch vụ. | Must | Active | Nhóm: Hóa sinh, Miễn dịch, Huyết học, Vi sinh, Giải phẫu bệnh, Chẩn đoán hình ảnh, Thăm dò chức năng, Khác. Đơn vị kết quả: Kết quả xét nghiệm, Ca chụp. Bản phát hành 1 nghiệm thu với Hóa sinh và Miễn dịch (C-10). |
| FR-SVC-009 | Khi người dùng khai mã của một dịch vụ trên HIS, LIS hoặc RIS, hệ thống phải lưu ánh xạ giữa dịch vụ và một hoặc nhiều mã ngoài, và từ chối gắn một mã ngoài của cùng hệ thống nguồn với hai dịch vụ. | Must | Active | Dùng khi nhập sản lượng (FR-ACCT-013). |
| FR-SVC-010 | Ở nơi dịch vụ được đánh dấu là dịch vụ bộ, hệ thống phải lưu danh sách thông số thành phần và cách tính giá thành: theo cả bộ hoặc theo từng thông số. | Should | Active | Ví dụ: điện giải đồ, tổng phân tích nước tiểu. Xem TBD-17. |
| FR-SVC-011 | Ở nơi dịch vụ được đánh dấu gửi ngoài, hệ thống phải lưu giá hợp đồng gửi mẫu, không yêu cầu bộ định mức và không tính giá thành từ định mức cho dịch vụ đó. | Could | Active | |

#### 3.1.4 Soạn quy trình có cấu trúc (PROC)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-PROC-001 | Khi người soạn tạo quy trình cho một dịch vụ kỹ thuật và một khoa chủ trì, hệ thống phải tạo bản nháp phiên bản 1 với các phần cố định: đại cương, chỉ định, chống chỉ định, thận trọng, chuẩn bị, các bước tiến hành, theo dõi và xử trí tai biến, tài liệu tham khảo. | Must | Active | |
| FR-PROC-002 | Nếu dịch vụ đã có một quy trình của cùng khoa chủ trì ở trạng thái "Nháp" hoặc đang trong luồng duyệt, thì hệ thống phải từ chối tạo bản mới và dẫn người dùng tới bản đang có. | Must | Active | |
| FR-PROC-003 | Khi người soạn thêm một bước, hệ thống phải yêu cầu giai đoạn (Chuẩn bị, Thực hiện, Theo dõi, Kết thúc), tên bước, mô tả, và gán cho bước một mã bước bất biến qua mọi phiên bản của quy trình. | Must | Active | Mã bước dạng `S` + số thứ tự cấp phát, không tái sử dụng. |
| FR-PROC-004 | Khi người soạn khai báo nguồn lực cho một bước, hệ thống phải lưu loại nguồn lực, tên, số lượng, đơn vị và, với nhân lực, chức danh và số người, dưới dạng dòng có cấu trúc gắn với mã bước. | Must | Active | Loại: Nhân lực, Thuốc, Hóa chất, Dịch truyền, Vật tư, Thiết bị, Phòng, Khác. |
| FR-PROC-005 | Khi người soạn nhập tên nguồn lực, hệ thống phải gợi ý các bản ghi khớp trong danh mục nguồn lực và cho phép để trống liên kết. | Should | Active | Liên kết bắt buộc ở bước định mức, không bắt buộc ở bước soạn. |
| FR-PROC-006 | Khi người soạn sắp xếp lại các bước, hệ thống phải cập nhật thứ tự hiển thị và giữ nguyên mã bước. | Must | Active | |
| FR-PROC-007 | Khi người soạn gắn trích dẫn cho một phần hoặc một bước, hệ thống phải lưu văn bản, mục, đoạn trích và loại quan hệ: "Theo hướng dẫn", "Khác biệt" hoặc "Chưa có căn cứ". | Must | Active | |
| FR-PROC-008 | Nếu một trích dẫn có loại quan hệ "Khác biệt" mà lý do để trống, thì hệ thống phải từ chối gửi duyệt quy trình. | Must | Active | |
| FR-PROC-009 | Khi người soạn lưu bản nháp, hệ thống phải ghi lịch sử thay đổi theo trường, theo bước và theo dòng nguồn lực, kèm người và thời điểm. | Must | Active | |
| FR-PROC-010 | Khi người dùng yêu cầu in một quy trình, hệ thống phải sinh tệp PDF theo mẫu ban hành từ dữ liệu có cấu trúc, gồm số hiệu, phiên bản, ngày hiệu lực và khối chữ ký. | Must | Active | Mẫu: xem TBD-04. Bản chưa ban hành in kèm chữ "DỰ THẢO". |
| FR-PROC-011 | Khi người dùng yêu cầu xuất DOCX một quy trình, hệ thống phải sinh tệp DOCX cùng nội dung với bản PDF. | Should | Active | |
| FR-PROC-012 | Nếu người soạn gửi duyệt một quy trình không có bước nào ở giai đoạn "Thực hiện", có bước thiếu mô tả, hoặc có dòng nguồn lực thiếu số lượng hay đơn vị, thì hệ thống phải liệt kê các lỗi và giữ quy trình ở trạng thái "Nháp". | Must | Active | |
| FR-PROC-013 | Khi người soạn sao chép quy trình từ một dịch vụ khác, hệ thống phải tạo bản nháp mới với mã bước cấp mới và ghi nguồn sao chép. | Could | Active | |

#### 3.1.5 Hỗ trợ AI (AI)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-AI-001 | Khi người soạn nhập yêu cầu (điều kiện của khoa, thiết bị, thuốc, vật tư, biến thể kỹ thuật) và yêu cầu soạn dự thảo, hệ thống phải gửi cho mô hình AI yêu cầu đó, các mục hướng dẫn còn hiệu lực đã ánh xạ với dịch vụ, các mục liên quan do người soạn chọn thêm và quy trình hiện hành của bệnh viện nếu có. | Must | Active | Nguồn bị giới hạn theo FR-SVC-007 và FR-AI-011. |
| FR-AI-002 | Khi AI trả kết quả, hệ thống phải tạo bản nháp quy trình có cấu trúc (phần, bước, nguồn lực) và gắn cho mỗi phần và mỗi bước ít nhất một trích dẫn hoặc nhãn "Chưa có căn cứ". | Must | Active | |
| FR-AI-003 | Khi nội dung dự thảo khác nội dung mục hướng dẫn tương ứng do yêu cầu của người soạn, hệ thống phải gắn nhãn "Khác biệt" cho phần hoặc bước đó và điền lý do đề xuất lấy từ yêu cầu của người soạn. | Must | Active | Người soạn sửa được lý do. |
| FR-AI-004 | Nếu dịch vụ không có mục hướng dẫn nào đã xác nhận và còn hiệu lực, thì hệ thống phải cảnh báo người soạn và chỉ soạn tiếp sau khi người soạn xác nhận. | Must | Active | Dự thảo khi đó mang nhãn "Chưa có căn cứ" ở mọi phần không có nguồn. |
| FR-AI-005 | Nếu đoạn trích trong một trích dẫn do AI trả về không xuất hiện nguyên văn trong mục nguồn, thì hệ thống phải loại trích dẫn đó và gắn nhãn "Chưa có căn cứ" cho phần hoặc bước liên quan. | Must | Active | So khớp sau khi chuẩn hóa khoảng trắng và dấu câu. |
| FR-AI-006 | Khi người soạn yêu cầu kiểm tra nhất quán, hệ thống phải liệt kê: nguồn lực có ở các bước nhưng thiếu ở phần chuẩn bị và ngược lại, bước thiếu người thực hiện, nội dung trái với chống chỉ định đã nêu. | Should | Active | Hai mục đầu kiểm bằng quy tắc; mục thứ ba do AI đề xuất. |
| FR-AI-007 | Khi bộ định mức được khởi tạo từ quy trình đã ban hành, hệ thống phải đề xuất cho mỗi dòng nguồn lực chưa liên kết một bản ghi danh mục khớp và cấu phần chi phí, kèm độ tin cậy. | Should | Active | |
| FR-AI-008 | Trong khi một đề xuất của AI chưa được người có quyền chấp nhận, hệ thống phải hiển thị đề xuất đó với nhãn "Đề xuất" và không đưa vào quy trình gửi duyệt, bộ định mức đã khóa hay phép tính giá. | Must | Active | |
| FR-AI-009 | Khi hệ thống gọi AI, hệ thống phải ghi nhật ký: mục đích, người gọi, bản ghi liên quan, mẫu lệnh và phiên bản, danh sách mục nguồn đã gửi, kết quả trả về, số token vào và ra, thời gian xử lý, trạng thái. | Must | Active | |
| FR-AI-010 | Nếu dịch vụ AI không phản hồi trong thời hạn cấu hình hoặc trả lỗi, thì hệ thống phải thông báo cho người dùng, giữ nguyên dữ liệu đang có và cho phép tiếp tục soạn thủ công. | Must | Active | Thời hạn mặc định 180 giây. |
| FR-AI-011 | Hệ thống phải không gửi cho AI dữ liệu nhập từ kế toán, kết quả tính giá, và bất kỳ trường dữ liệu định danh người bệnh nào. | Must | Active | Luôn đúng; kiểm bằng danh sách cho phép các nguồn được gửi. |
| FR-AI-012 | Khi NC Admin lưu cấu hình nhà cung cấp AI (loại giao thức, địa chỉ, mô hình, khóa, thời hạn, hạn mức tháng), hệ thống phải dùng cấu hình đó cho mọi lần gọi kế tiếp mà không cần triển khai lại. | Must | Active | Khóa lưu mã hóa theo NFR-SEC-004. |
| FR-AI-013 | Nếu số token lũy kế trong tháng vượt hạn mức cấu hình, thì hệ thống phải chặn các lần gọi AI mới và thông báo cho NC Admin. | Should | Active | |
| FR-AI-014 | Khi NC Admin sửa một mẫu lệnh, hệ thống phải tạo phiên bản mẫu lệnh mới và giữ phiên bản cũ. | Should | Active | |
| FR-AI-015 | Ở nơi tính năng AI bị tắt trong cấu hình, hệ thống phải ẩn các nút gọi AI và cho phép mọi luồng nghiệp vụ chạy thủ công. | Must | Active | |
| FR-AI-016 | Khi người dùng yêu cầu AI đề xuất định mức cho một hệ thống xét nghiệm, hệ thống phải gửi cho mô hình AI các mục tài liệu của hãng đã gắn với hóa chất và thiết bị của hệ thống đó cùng quy trình đã ban hành, và tạo các đề xuất về lượng hóa chất mỗi test, tần suất chuẩn máy, tần suất nội kiểm và hạn dùng sau mở. | Should | Active | Nguồn bị giới hạn theo FR-AI-011. Tài liệu của hãng phải được thêm vào danh sách cho phép nguồn gửi AI (điểm X-11 của REF-09). Thuộc bản phát hành 2. |
| FR-AI-017 | Khi AI trả một đề xuất định mức, hệ thống phải gắn cho đề xuất đó trích dẫn đến mục tài liệu nguồn hoặc nhãn "Chưa có căn cứ", và áp FR-AI-005 và FR-AI-008. | Should | Active | |
| FR-AI-018 | Nếu AI đề xuất một mặt hàng hoặc thiết bị không có trong danh mục, thì hệ thống phải giữ đề xuất ở dạng văn bản, không tạo bản ghi danh mục mới và yêu cầu người dùng liên kết thủ công. | Should | Active | |

#### 3.1.6 Phê duyệt và phiên bản quy trình (WF)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-WF-001 | Khi người soạn gửi duyệt một quy trình hợp lệ, hệ thống phải chuyển trạng thái sang "Chờ trưởng khoa duyệt" và thông báo cho trưởng khoa của khoa chủ trì. | Must | Active | Hợp lệ theo FR-PROC-008, FR-PROC-012, FR-AI-008. |
| FR-WF-002 | Khi trưởng khoa đồng ý, hệ thống phải chuyển trạng thái sang "Chờ hội đồng thẩm định" và thông báo cho các thành viên hội đồng. | Must | Active | |
| FR-WF-003 | Khi thành viên hội đồng ghi ý kiến, hệ thống phải lưu ý kiến gắn với phần hoặc bước cụ thể của quy trình. | Must | Active | |
| FR-WF-004 | Khi thư ký hội đồng ghi kết luận "Thông qua", hệ thống phải chuyển trạng thái sang "Chờ ban hành" và thông báo cho NC Director. | Must | Active | Thư ký hội đồng: người dùng có vai trò NC Council Member được đánh dấu thư ký. |
| FR-WF-005 | Khi NC Director ban hành, hệ thống phải yêu cầu số quyết định và ngày hiệu lực, khóa nội dung phiên bản và đặt trạng thái "Đã ban hành". | Must | Active | |
| FR-WF-006 | Khi một phiên bản mới đến ngày hiệu lực, hệ thống phải chuyển phiên bản "Đã ban hành" trước đó của cùng dịch vụ và khoa sang "Đã thay thế". | Must | Active | |
| FR-WF-007 | Khi người duyệt ở bất kỳ cấp nào từ chối, hệ thống phải yêu cầu lý do, trả quy trình về "Nháp" và thông báo cho người soạn. | Must | Active | |
| FR-WF-008 | Trong khi quy trình ở trạng thái "Đã ban hành", "Đã thay thế" hoặc "Đã thu hồi", hệ thống phải từ chối mọi chỉnh sửa nội dung. | Must | Active | |
| FR-WF-009 | Khi người có quyền yêu cầu sửa đổi một quy trình "Đã ban hành", hệ thống phải tạo bản nháp phiên bản kế tiếp, sao chép toàn bộ nội dung và giữ nguyên mã bước. | Must | Active | |
| FR-WF-010 | Khi người dùng so sánh hai phiên bản của một quy trình, hệ thống phải hiển thị khác biệt theo phần, theo bước và theo dòng nguồn lực. | Should | Active | |
| FR-WF-011 | Khi một phiên bản quy trình mới được ban hành, hệ thống phải gắn cờ "Cần cập nhật" cho các bộ định mức đang dựa trên phiên bản cũ và liệt kê mã bước được thêm, bị bỏ, bị đổi. | Must | Active | |
| FR-WF-012 | Khi NC Director thu hồi một quy trình, hệ thống phải yêu cầu lý do và chuyển trạng thái sang "Đã thu hồi". | Should | Active | |
| FR-WF-013 | Nếu một quy trình chờ duyệt ở một cấp quá số ngày cấu hình, thì hệ thống phải gửi nhắc cho người duyệt của cấp đó. | Could | Active | Mặc định 7 ngày. |

#### 3.1.7 Nguồn lực, đơn giá và tham số (RES)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-RES-001 | Khi NC Resource Manager tạo một mặt hàng (thuốc, hóa chất, dịch truyền, vật tư), hệ thống phải yêu cầu mã, tên, loại, đơn vị tính và số lần dùng, mặc định là 1. | Must | Active | |
| FR-RES-002 | Khi người dùng thêm đơn giá cho một mặt hàng, hệ thống phải yêu cầu giá đã gồm thuế GTGT, nguồn giá, số và ngày chứng từ, ngày bắt đầu hiệu lực, và cho phép nhập ngày hết hiệu lực. | Must | Active | Nguồn giá: Trúng thầu, Hợp đồng, Hóa đơn, Giá công bố, Báo giá. Sửa ở 1.1: thêm nguồn Hợp đồng và ngày hết hiệu lực. |
| FR-RES-003 | Nếu ngày chứng từ của đơn giá được dùng cũ hơn 24 tháng so với ngày tính giá, thì hệ thống phải gắn cảnh báo "Đơn giá quá hạn tham chiếu" trên dòng chi phí dùng đơn giá đó. | Must | Active | Theo khoản 2 Điều 7 REF-03. |
| FR-RES-004 | Khi một mặt hàng có nhiều đơn giá còn hiệu lực tại ngày tính giá, hệ thống phải dùng đơn giá thuộc loại nguồn có thứ tự ưu tiên cao nhất và, trong cùng loại nguồn, đơn giá có ngày bắt đầu hiệu lực gần nhất. | Must | Active | Thứ tự ưu tiên: Trúng thầu, Hợp đồng, Hóa đơn, Giá công bố, Báo giá. Còn hiệu lực: ngày bắt đầu hiệu lực không sau ngày tính giá và ngày tính giá không sau ngày hết hiệu lực nếu có. Sửa ở 1.1 (điểm X-01 của REF-09): bản 1.0 chỉ xét ngày bắt đầu hiệu lực gần nhất. |
| FR-RES-005 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu ngày đưa vào sử dụng, nguồn hình thành, hình thức có máy, tiêu chí chia chi phí và, với thiết bị có hình thức Mua, nguyên giá và thời gian sử dụng tính bằng năm; với thiết bị có tiêu chí chia Giờ kế hoạch, số giờ khai thác kế hoạch năm và hệ số sử dụng; và cho phép nhập chi phí bảo trì năm và chi phí kiểm định năm. | Must | Active | Hình thức có máy: FR-RES-019. Tiêu chí chia: FR-RES-022. Chi phí kiểm định năm nhập tay chỉ dùng khi thiết bị không có hồ sơ tuân thủ (FR-CMP-002). Sửa ở 1.1: bản 1.0 yêu cầu nguyên giá, thời gian sử dụng, giờ kế hoạch và hệ số sử dụng với mọi thiết bị. |
| FR-RES-006 | Khi thông tin thiết bị được lưu, hệ thống phải tính khấu hao năm và đơn giá giờ máy theo BR-COST-004. | Must | Active | |
| FR-RES-007 | Nếu thiết bị đã hết thời gian sử dụng tính đến ngày tính giá, thì hệ thống phải tính khấu hao năm theo lựa chọn trong bộ tham số của lần tính giá, hoặc bằng 0, hoặc tiếp tục bằng nguyên giá chia cho thời gian sử dụng, và vẫn tính chi phí bảo trì và kiểm định. | Must | Active | Mặc định bằng 0. Lựa chọn đã dùng được ghi trên bảng giải trình. Sửa ở 1.1 (điểm X-04 của REF-09): bản 1.0 luôn lấy bằng 0. Xem TBD-07. |
| FR-RES-008 | Khi người dùng khai báo một phòng, hệ thống phải yêu cầu diện tích, chi phí hạ tầng năm, số giờ khai thác năm và tính đơn giá giờ phòng theo BR-COST-005. | Must | Active | |
| FR-RES-009 | Khi NC Finance tạo bộ tham số tính giá, hệ thống phải yêu cầu ngày hiệu lực và các tham số: lương cơ sở, tỷ lệ đóng góp của đơn vị, số ngày làm việc năm, số giờ làm việc ngày, trần hao hụt, cách tính và tỷ lệ tích lũy, tỷ lệ nghĩa vụ tài chính, đơn vị làm tròn, ngưỡng đối soát, ngưỡng lệch so sánh, giá điện, giá nước, cách tính khấu hao của thiết bị đã hết thời gian sử dụng, ngưỡng đối soát vật chất và ngưỡng đối soát sản lượng. | Must | Active | Mặc định: khấu hao thiết bị hết thời gian sử dụng bằng 0; ngưỡng đối soát vật chất 5%; ngưỡng đối soát sản lượng 2%. Sửa ở 1.1: thêm ba tham số cuối. |
| FR-RES-010 | Khi NC Finance khai báo chi phí theo chức danh trong một bộ tham số, hệ thống phải tính chi phí năm và đơn giá giờ công theo BR-COST-001. | Must | Active | |
| FR-RES-011 | Trong khi một bộ tham số đang được một lần tính giá đã khóa sử dụng, hệ thống phải từ chối sửa bộ tham số đó và cho phép nhân bản thành bộ mới. | Must | Active | |
| FR-RES-012 | Khi người dùng nhập danh mục từ tệp Excel mẫu (mặt hàng, đơn giá, thiết bị, phòng, chức danh), hệ thống phải tạo mới hoặc cập nhật theo mã và báo cáo các dòng lỗi. | Must | Active | |
| FR-RES-013 | Khi người dùng gán hai hay nhiều mặt hàng vào cùng một nhóm tương đương, hệ thống phải lưu nhóm đó để dùng cho gợi ý thay thế. | Should | Active | Dùng bởi BR-ADJ-003. |
| FR-RES-014 | Khi người dùng đánh dấu một mặt hàng là "thanh toán riêng ngoài giá dịch vụ", hệ thống phải loại mặt hàng đó khỏi giá thành ở mọi lần tính giá và ghi lý do loại trên bảng giải trình. | Must | Active | |
| FR-RES-015 | Khi NC Finance khai báo một loại giá, hệ thống phải yêu cầu cấp phê duyệt (bệnh viện hoặc cơ quan có thẩm quyền) và các lựa chọn: có kết cấu khấu hao, có tích lũy. | Must | Active | Xem TBD-05. |
| FR-RES-016 | Khi người dùng xác minh một đơn giá, hệ thống phải yêu cầu tệp chứng từ đính kèm và lưu trạng thái "Đã xác minh" kèm người xác minh và thời điểm. | Should | Active | |
| FR-RES-017 | Nếu một dòng chi phí dùng đơn giá chưa ở trạng thái "Đã xác minh", thì hệ thống phải gắn cảnh báo "Đơn giá chưa xác minh" trên dòng chi phí đó. | Should | Active | Không chặn tính giá. |
| FR-RES-018 | Khi NC Resource Manager tạo mặt hàng loại hóa chất xét nghiệm, chất chuẩn hoặc vật liệu nội kiểm, hệ thống phải yêu cầu số đơn vị định mức trong một đơn vị mua và cho phép nhập số test danh nghĩa và hạn dùng sau mở tính bằng ngày. | Must | Active | Bổ sung hai loại mặt hàng: Chất chuẩn, Vật liệu nội kiểm. Đơn giá một đơn vị định mức theo BR-CLS-002. Ví dụ: hộp 200 test giá 6.000.000 đồng cho đơn giá 30.000 đồng mỗi test. |
| FR-RES-019 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu hình thức có máy: Mua, Thuê, Đặt theo hóa chất, hoặc Liên doanh, liên kết. | Must | Active | Mặc định Mua. |
| FR-RES-020 | Trong khi hình thức có máy là Thuê hoặc Liên doanh, liên kết, hệ thống phải yêu cầu chi phí năm theo hợp đồng và dùng số đó thay cho khấu hao năm. | Must | Active | BR-CLS-009. Loại chi phí kế toán: TBD-14. |
| FR-RES-021 | Trong khi hình thức có máy là Đặt theo hóa chất, hệ thống phải tính khấu hao năm bằng 0 và tính bằng 0 chi phí bảo trì và các linh kiện được đánh dấu "nhà cung cấp chịu". | Must | Active | BR-CLS-009, BR-CLS-010. |
| FR-RES-022 | Khi NC Resource Manager khai báo một thiết bị, hệ thống phải yêu cầu tiêu chí chia chi phí của thiết bị: Giờ kế hoạch, Số kết quả, hoặc Phút chiếm máy. | Must | Active | Mặc định Giờ kế hoạch (BR-COST-004). Hai tiêu chí còn lại theo BR-CLS-009. Mỗi thiết bị một tiêu chí (điểm X-05 của REF-09). |
| FR-RES-023 | Khi người dùng khai linh kiện lớn của một thiết bị, hệ thống phải yêu cầu tên, giá thay thế và tuổi thọ tính theo tháng, theo số kết quả hoặc theo giờ chạy, và cho phép đánh dấu "nhà cung cấp chịu". | Must | Active | BR-CLS-010. Ví dụ: bóng phát tia, điện cực, đèn. |
| FR-RES-024 | Khi một thiết bị dùng chung cho nhiều khoa, hệ thống phải lưu tỷ lệ phân bổ chi phí của thiết bị cho từng khoa. | Must | Active | |
| FR-RES-025 | Nếu tổng tỷ lệ phân bổ theo khoa của một thiết bị khác 100%, thì hệ thống phải từ chối lưu. | Must | Active | |
| FR-RES-026 | Khi NC Resource Manager khai báo một thiết bị cận lâm sàng, hệ thống phải cho phép nhập công suất điện khi chạy, công suất điện khi chờ, số giờ chạy và số giờ chờ mỗi ngày, và cờ cấp điện liên tục. | Should | Active | BR-CLS-012. |

#### 3.1.8 Định mức (NORM)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-NORM-001 | Khi người có quyền khởi tạo bộ định mức cho một dịch vụ và một khoa, hệ thống phải tạo bộ định mức nháp gắn với phiên bản quy trình "Đã ban hành" và sinh một dòng định mức cho mỗi dòng nguồn lực của quy trình. | Must | Active | |
| FR-NORM-002 | Nếu dịch vụ chưa có quy trình "Đã ban hành", thì hệ thống phải từ chối khởi tạo bộ định mức. | Must | Active | |
| FR-NORM-003 | Khi người dùng sửa một dòng định mức, hệ thống phải yêu cầu cấu phần, nguồn lực trong danh mục, số lượng, đơn vị và, với nhân lực, số người và số phút. | Must | Active | Cấu phần: Nhân lực, Thuốc và hóa chất, Vật tư, Thiết bị, Hạ tầng, Tiện ích. |
| FR-NORM-004 | Nếu người dùng nhập tỷ lệ hao hụt vượt trần trong bộ tham số hiệu lực, thì hệ thống phải yêu cầu ghi lý do trước khi lưu. | Must | Active | |
| FR-NORM-005 | Khi người dùng thêm dòng định mức không xuất phát từ dòng nguồn lực của quy trình, hệ thống phải yêu cầu gắn một mã bước hoặc đánh dấu "chung cho cả dịch vụ". | Must | Active | Ví dụ: điện, nước, giặt hấp. |
| FR-NORM-006 | Khi một dòng định mức có cả định mức của bệnh viện và định mức do cơ quan có thẩm quyền ban hành, hệ thống phải lấy lượng áp dụng bằng giá trị nhỏ hơn trong hai giá trị. | Must | Active | BR-COST-007; theo khoản 2 Điều 7 REF-03. |
| FR-NORM-007 | Khi một dòng định mức không có định mức do cơ quan có thẩm quyền ban hành, hệ thống phải lấy định mức của bệnh viện làm lượng áp dụng. | Must | Active | |
| FR-NORM-008 | Khi người dùng chọn căn cứ cho một dòng định mức, hệ thống phải lưu một trong các giá trị: Quy trình, Bấm giờ, Tiêu hao thực tế, Định mức ban hành, Ước tính, kèm tham chiếu. | Must | Active | |
| FR-NORM-009 | Khi người có vai trò NC Clinician hoặc NC Department Head xác nhận một dòng định mức, hệ thống phải lưu người xác nhận và thời điểm. | Must | Active | |
| FR-NORM-010 | Nếu bộ định mức còn dòng chưa xác nhận, dòng chưa liên kết danh mục hoặc đề xuất AI chưa xử lý, thì hệ thống phải từ chối chuyển bộ định mức sang "Đã xác nhận chuyên môn". | Must | Active | |
| FR-NORM-011 | Khi NC Finance xác nhận một bộ định mức "Đã xác nhận chuyên môn", hệ thống phải chuyển trạng thái sang "Đã khóa". | Must | Active | Chỉ bộ "Đã khóa" được dùng tính giá. |
| FR-NORM-012 | Trong khi bộ định mức ở trạng thái "Đã khóa", hệ thống phải từ chối sửa và cho phép tạo phiên bản bộ định mức mới. | Must | Active | |
| FR-NORM-013 | Khi người dùng đánh dấu loại trừ một dòng định mức, hệ thống phải yêu cầu lý do thuộc danh sách: Thanh toán riêng, Ngân sách nhà nước bảo đảm, Đã tính trong dịch vụ khác, Khác. | Must | Active | Theo khoản 3 Điều 1 REF-03. |
| FR-NORM-014 | Nếu cùng một nguồn lực xuất hiện ở hai dòng của cùng một bước, thì hệ thống phải cảnh báo trùng trước khi lưu. | Should | Active | |
| FR-NORM-015 | Khi người dùng tạo phiên bản bộ định mức mới theo một phiên bản quy trình mới, hệ thống phải mang sang các dòng có mã bước còn tồn tại, đánh dấu các dòng thuộc bước bị bỏ và liệt kê các bước mới chưa có dòng. | Must | Active | |
| FR-NORM-016 | Khi người dùng xem một bộ định mức, hệ thống phải hiển thị chi phí trực tiếp tạm tính theo từng bước và từng cấu phần với bộ tham số hiệu lực. | Should | Active | |
| FR-NORM-017 | Ở nơi dịch vụ có hệ thống xét nghiệm, hệ thống phải gắn mỗi bộ định mức với đúng một hệ thống xét nghiệm và cho phép mỗi hệ thống có một bộ định mức "Đã khóa" đang hiệu lực. | Must | Active | Điểm X-02 của REF-09. Ràng buộc DI-03 của mô hình dữ liệu đổi thành (dịch vụ, khoa, hệ thống xét nghiệm). Dịch vụ không có hệ thống xét nghiệm giữ nguyên một bộ cho mỗi (dịch vụ, khoa). |
| FR-NORM-018 | Khi người dùng sửa một dòng định mức của dịch vụ cận lâm sàng, hệ thống phải yêu cầu cấp phát sinh của dòng: Theo kết quả, Theo ống mẫu, Theo mẻ, Theo ngày-máy, hoặc Theo kỳ. | Must | Active | Mặc định Theo kết quả. Cách tính: BR-CLS-002 đến BR-CLS-005. Dòng của dịch vụ không thuộc khối cận lâm sàng luôn là Theo kết quả (một ca). |
| FR-NORM-019 | Khi người dùng khai một dòng thuốc, hóa chất hoặc vật tư có cấp phát sinh Theo kết quả, hệ thống phải cho phép bật cờ "nhân hệ số tiêu hao k" và, trong khi cờ bật, không áp tỷ lệ hao hụt của dòng. | Must | Active | Mặc định bật với hóa chất chính và vật tư tiêu hao theo test. Hao hụt đã nằm trong k (BR-CLS-001). |
| FR-NORM-020 | Nếu bộ định mức có dòng Theo ống mẫu mà chưa khai số xét nghiệm bình quân trên một ống mẫu, thì hệ thống phải từ chối chuyển bộ định mức sang "Đã xác nhận chuyên môn". | Must | Active | BR-CLS-003. |
| FR-NORM-021 | Khi NC Finance hoặc NC Admin lập mẫu định mức cho một nhóm chuyên ngành, hệ thống phải lưu danh sách khoản mục của mẫu, mỗi khoản mục có tên, cấu phần, cấp phát sinh mặc định và cờ bắt buộc. | Should | Active | Khoản mục mặc định cho nhóm xét nghiệm: vật tư lấy mẫu, hóa chất chính, hóa chất phụ trợ, vật tư tiêu hao theo test, nhân lực, thiết bị, điện nước, xử lý chất thải. |
| FR-NORM-022 | Khi người dùng khởi tạo bộ định mức cho dịch vụ thuộc nhóm chuyên ngành có mẫu định mức, hệ thống phải thêm các khoản mục bắt buộc của mẫu chưa có trong các dòng sinh từ quy trình, ở dạng dòng "chung cho cả dịch vụ" chưa có số lượng. | Should | Active | |
| FR-NORM-023 | Nếu bộ định mức thiếu dòng cho một khoản mục bắt buộc của mẫu và người dùng chưa ghi lý do không áp dụng, thì hệ thống phải từ chối chuyển bộ định mức sang "Đã xác nhận chuyên môn" và liệt kê khoản mục thiếu. | Should | Active | |
| FR-NORM-024 | Nếu một dòng định mức dùng mặt hàng đã có trong kế hoạch nội kiểm hoặc kế hoạch chuẩn máy của cùng hệ thống xét nghiệm, thì hệ thống phải từ chối lưu dòng đó. | Must | Active | Chống tính trùng: vật liệu nội kiểm và chất chuẩn được tính từ kế hoạch chất lượng (FR-COST-020). |
| FR-NORM-025 | Khi người dùng sao chép bộ định mức từ một hệ thống xét nghiệm khác của cùng dịch vụ, hệ thống phải tạo bộ định mức nháp mới, mang sang các dòng có mã bước còn tồn tại và ghi nguồn sao chép. | Could | Active | |

#### 3.1.9 Khảo sát bấm giờ (TS)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-TS-001 | Khi người khảo sát tạo phiếu bấm giờ cho một dịch vụ và một khoa, hệ thống phải nạp danh sách bước của quy trình "Đã ban hành". | Must | Active | |
| FR-TS-002 | Khi người khảo sát ghi một ca, hệ thống phải lưu cho từng bước: chức danh, số người, số phút nhân lực và số phút máy theo từng thiết bị. | Must | Active | Không lưu thông tin định danh người bệnh. |
| FR-TS-003 | Khi một dịch vụ có số ca khảo sát từ mức tối thiểu cấu hình trở lên, hệ thống phải tính trung vị số phút theo bước, theo chức danh và theo thiết bị. | Must | Active | Mức tối thiểu mặc định 5 ca; xem TBD-12. |
| FR-TS-004 | Khi người dùng chọn áp kết quả bấm giờ vào một bộ định mức nháp, hệ thống phải cập nhật số phút của các dòng nhân lực và thiết bị tương ứng và đặt căn cứ là "Bấm giờ". | Must | Active | |
| FR-TS-005 | Nếu số ca khảo sát ít hơn mức tối thiểu, thì hệ thống phải cảnh báo và yêu cầu người dùng xác nhận trước khi áp kết quả. | Should | Active | |

#### 3.1.10 Số liệu kế toán và phân bổ (ACCT)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-ACCT-001 | Khi NC Finance tải tệp Excel số liệu chi phí theo mẫu (mã tài khoản, tên tài khoản, mã trung tâm chi phí, số tiền) cho một năm tài chính, hệ thống phải tạo lần nhập ở trạng thái "Nháp" và hiển thị số dòng và tổng tiền. | Must | Active | |
| FR-ACCT-002 | Nếu tệp có dòng thiếu mã tài khoản, số tiền không phải số, hoặc mã trung tâm chi phí không tồn tại, thì hệ thống phải liệt kê các dòng lỗi và không cho chốt lần nhập. | Must | Active | |
| FR-ACCT-003 | Khi lần nhập được tạo, hệ thống phải gán loại chi phí cho từng dòng theo bảng ánh xạ tài khoản của chế độ kế toán được chọn. | Must | Active | Loại chi phí: xem BR-COST-008. |
| FR-ACCT-004 | Khi NC Finance sửa loại chi phí của một dòng hoặc đánh dấu loại trừ, hệ thống phải yêu cầu lý do và lưu người sửa. | Must | Active | |
| FR-ACCT-005 | Nếu lần nhập còn dòng chưa được gán loại chi phí, thì hệ thống phải từ chối chốt lần nhập. | Must | Active | |
| FR-ACCT-006 | Khi NC Finance chốt lần nhập, hệ thống phải khóa các dòng và ghi tổng theo trung tâm chi phí và loại chi phí. | Must | Active | |
| FR-ACCT-007 | Khi NC Finance nhập tệp sản lượng dịch vụ theo khoa cho một năm, hệ thống phải lưu sản lượng theo dịch vụ - khoa và báo lỗi các mã dịch vụ hoặc mã khoa không tồn tại. | Must | Active | |
| FR-ACCT-008 | Khi NC Finance khai báo một quy tắc phân bổ, hệ thống phải yêu cầu cấp phân bổ (Hỗ trợ sang Lâm sàng, hoặc Lâm sàng sang Dịch vụ), loại chi phí và tiêu chí phân bổ. | Must | Active | Tiêu chí: BR-COST-009. |
| FR-ACCT-009 | Khi ứng dụng được cài đặt, hệ thống phải nạp bảng ánh xạ tài khoản mặc định cho chế độ kế toán hành chính, sự nghiệp và cho phép NC Finance sửa. | Must | Active | Nội dung bảng mặc định: TBD-03. |
| FR-ACCT-010 | Khi NC Finance nhập số liệu tiêu chí của trung tâm chi phí cho một năm (số nhân lực, diện tích, doanh thu), hệ thống phải lưu để dùng cho phân bổ cấp 1. | Must | Active | |
| FR-ACCT-011 | Khi người dùng nhập lần thứ hai cho cùng một năm tài chính, hệ thống phải tạo lần nhập mới và giữ nguyên lần nhập cũ. | Should | Active | |
| FR-ACCT-012 | Khi NC Finance nhập sản lượng, hệ thống phải yêu cầu kịch bản sản lượng của số liệu: Thực tế 12 tháng, Kế hoạch, hoặc Công suất. | Must | Active | Mặc định Thực tế 12 tháng (REF-09). Số liệu nhập theo FR-ACCT-007 khi không chọn kịch bản thuộc kịch bản Thực tế 12 tháng. |
| FR-ACCT-013 | Khi NC Finance nhập tệp sản lượng cận lâm sàng theo mẫu, hệ thống phải lưu theo dịch vụ, khoa, hệ thống xét nghiệm và kịch bản: số kết quả trả, số test nội kiểm, số test chuẩn máy, số test chạy lại, số test ngoại kiểm, tỷ lệ hao hụt, cỡ mẻ bình quân, số ngày chạy máy và, với thiết bị chia theo Phút chiếm máy, tổng số phút khai thác của thiết bị. | Must | Active | Nguồn: LIS, RIS (IF-07). Chỉ số kết quả trả là bắt buộc; các cột còn lại để trống được (FR-QC-006). Mã ngoài được đổi sang mã dịch vụ theo FR-SVC-009. |
| FR-ACCT-014 | Nếu tệp sản lượng cận lâm sàng có mã dịch vụ, mã khoa hoặc mã hệ thống xét nghiệm không tồn tại, hoặc có số âm, thì hệ thống phải liệt kê các dòng lỗi và không lưu các dòng đó. | Must | Active | |
| FR-ACCT-015 | Khi NC Finance nhập tệp xuất kho thực tế theo mẫu, hệ thống phải lưu lượng xuất theo mặt hàng, khoa và năm tài chính. | Must | Active | IF-08. Dùng cho đối soát vật chất (FR-COST-026). |

#### 3.1.11 Tính giá thành (COST)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-COST-001 | Khi NC Finance tạo một lần tính giá, hệ thống phải yêu cầu năm tài chính, ngày tính giá, bộ tham số, lần nhập kế toán đã chốt, loại giá và phạm vi khoa hoặc dịch vụ. | Must | Active | |
| FR-COST-002 | Nếu trong phạm vi có dịch vụ chưa có bộ định mức "Đã khóa", thì hệ thống phải liệt kê các dịch vụ đó và chỉ tính các dịch vụ đủ điều kiện sau khi người dùng xác nhận. | Must | Active | |
| FR-COST-003 | Khi lần tính giá chạy, hệ thống phải tính chi phí trực tiếp của từng dòng định mức không bị loại trừ theo BR-COST-001 đến BR-COST-007. | Must | Active | |
| FR-COST-004 | Khi lần tính giá chạy, hệ thống phải phân bổ chi phí của các trung tâm chi phí hỗ trợ sang các trung tâm chi phí lâm sàng theo quy tắc phân bổ cấp 1. | Must | Active | BR-COST-010. |
| FR-COST-005 | Khi lần tính giá chạy, hệ thống phải xác định cho mỗi trung tâm chi phí lâm sàng phần chi phí chưa được tính từ định mức theo từng loại chi phí và phân bổ phần đó cho các dịch vụ theo quy tắc phân bổ cấp 2. | Must | Active | BR-COST-011. |
| FR-COST-006 | Khi lần tính giá chạy, hệ thống phải tính cho mỗi dịch vụ giá thành toàn bộ, tích lũy, nghĩa vụ tài chính, giá tính toán và giá làm tròn theo BR-COST-012 đến BR-COST-014. | Must | Active | |
| FR-COST-007 | Ở nơi loại giá không kết cấu khấu hao, hệ thống phải loại các khoản khấu hao thiết bị và hạ tầng khỏi giá thành và ghi rõ việc loại trên bảng giải trình. | Must | Active | BR-COST-016. Bảo trì và kiểm định vẫn được tính. |
| FR-COST-008 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát theo trung tâm chi phí và loại chi phí gồm: số đã tính, số kế toán, chênh lệch tuyệt đối và chênh lệch phần trăm. | Must | Active | BR-COST-015. |
| FR-COST-009 | Nếu chênh lệch phần trăm của một dòng đối soát vượt ngưỡng trong bộ tham số, thì hệ thống phải đánh dấu dòng đó "Vượt ngưỡng" và yêu cầu NC Finance ghi giải trình trước khi khóa lần tính giá. | Must | Active | |
| FR-COST-010 | Khi người dùng mở bảng giải trình của một dịch vụ, hệ thống phải hiển thị từng dòng chi phí với bước quy trình, nguồn lực, lượng áp dụng, đơn giá, thành tiền, và chứng từ đơn giá hoặc quy tắc phân bổ cùng giá trị tiêu chí. | Must | Active | |
| FR-COST-011 | Khi NC Finance khóa một lần tính giá, hệ thống phải lưu ảnh chụp toàn bộ đầu vào đã dùng (định mức, đơn giá, tham số, số liệu kế toán, sản lượng) cùng kết quả. | Must | Active | Bảo đảm tái lập theo NFR-REL-001. |
| FR-COST-012 | Trong khi một lần tính giá ở trạng thái "Đã khóa", hệ thống phải từ chối tính lại và cho phép nhân bản thành lần tính giá mới. | Must | Active | |
| FR-COST-013 | Khi người dùng so sánh hai lần tính giá, hệ thống phải hiển thị chênh lệch giá thành theo dịch vụ và theo cấu phần. | Should | Active | |
| FR-COST-014 | Nếu sản lượng của một dịch vụ bằng 0 hoặc thiếu, thì hệ thống phải không phân bổ chi phí cấp 2 cho dịch vụ đó, gắn cảnh báo và vẫn tính chi phí trực tiếp. | Must | Active | Sửa ghi chú ở 1.1: dịch vụ có hệ thống xét nghiệm theo FR-COST-023, vì chi phí trực tiếp của các dịch vụ này cần sản lượng để tính. |
| FR-COST-015 | Khi một lần tính giá có hơn 50 dịch vụ, hệ thống phải chạy bằng tác vụ nền và hiển thị tiến độ. | Should | Active | |
| FR-COST-016 | Nếu một dòng định mức không có đơn giá hiệu lực tại ngày tính giá, thì hệ thống phải dừng tính dịch vụ đó, ghi lỗi nêu rõ dòng thiếu đơn giá và tiếp tục tính các dịch vụ khác. | Must | Active | |
| FR-COST-017 | Khi NC Finance tạo một lần tính giá, hệ thống phải yêu cầu kịch bản sản lượng và cách phân bổ chi phí kiểm định, hiệu chuẩn: Theo giá trị tài sản, hoặc Gắn trực tiếp thiết bị. | Must | Active | Mặc định: Thực tế 12 tháng; Theo giá trị tài sản (REF-09). Mỗi lần tính dùng một kịch bản; so sánh các kịch bản bằng FR-COST-013 (điểm X-06). |
| FR-COST-018 | Khi lần tính giá chạy, hệ thống phải tính hệ số tiêu hao k của từng hệ thống xét nghiệm trong phạm vi theo BR-CLS-001 từ sản lượng của kịch bản được chọn. | Must | Active | |
| FR-COST-019 | Khi lần tính giá chạy, hệ thống phải tính chi phí cho một kết quả của từng dòng định mức cận lâm sàng theo cấp phát sinh của dòng, theo BR-CLS-002 đến BR-CLS-005. | Must | Active | |
| FR-COST-020 | Khi lần tính giá chạy, hệ thống phải tính chi phí vật liệu nội kiểm, chất chuẩn và ngoại kiểm cho một kết quả từ kế hoạch chất lượng theo BR-CLS-006 đến BR-CLS-008 và ghi thành các dòng chi phí riêng. | Must | Active | |
| FR-COST-021 | Khi lần tính giá chạy, hệ thống phải tính chi phí thiết bị của dịch vụ theo hình thức có máy và tiêu chí chia của thiết bị, theo BR-COST-004 và BR-CLS-009 đến BR-CLS-012. | Must | Active | |
| FR-COST-022 | Khi một dịch vụ trong một khoa có nhiều hệ thống xét nghiệm, hệ thống phải tính chi phí trực tiếp của từng hệ thống, lưu kết quả từng hệ thống và lấy bình quân gia quyền theo tỷ trọng sản lượng làm chi phí trực tiếp của dịch vụ. | Must | Active | BR-CLS-013. |
| FR-COST-023 | Nếu một hệ thống xét nghiệm thiếu sản lượng của kịch bản được chọn, có số kết quả trả bằng 0, hoặc có dòng Theo mẻ mà thiếu cỡ mẻ bình quân, thì hệ thống phải dừng tính dịch vụ đó, ghi lỗi nêu rõ dữ liệu thiếu và tiếp tục tính các dịch vụ khác. | Must | Active | Ngoại lệ của FR-COST-014 cho dịch vụ có hệ thống xét nghiệm. |
| FR-COST-024 | Khi lần tính giá chạy cho dịch vụ có hệ thống xét nghiệm, hệ thống phải dùng tổng số kết quả trả của các hệ thống trong kịch bản được chọn làm sản lượng của dịch vụ trong phân bổ cấp 2 và đối soát. | Must | Active | BR-COST-011, BR-COST-015. |
| FR-COST-025 | Nếu số test tiêu thụ của một hệ thống xét nghiệm trong thời hạn dùng sau mở của hóa chất chính nhỏ hơn số test danh nghĩa của một đơn vị mua, thì hệ thống phải gắn cảnh báo "Sản lượng thấp" trên kết quả của dịch vụ. | Should | Active | BR-CLS-016. |
| FR-COST-026 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát vật chất theo khoa và mặt hàng gồm: lượng tính được, lượng xuất kho thực tế, chênh lệch tuyệt đối và chênh lệch phần trăm. | Must | Active | BR-CLS-014. |
| FR-COST-027 | Nếu chênh lệch phần trăm của một dòng đối soát vật chất vượt ngưỡng đối soát vật chất trong bộ tham số, thì hệ thống phải đánh dấu dòng đó "Vượt ngưỡng" và yêu cầu NC Finance ghi giải trình trước khi khóa lần tính giá. | Must | Active | Mặc định 5%. |
| FR-COST-028 | Khi lần tính giá hoàn tất, hệ thống phải lập bảng đối soát sản lượng so số kết quả trả với sản lượng dịch vụ từ HIS của từng dịch vụ và khoa, và gắn cảnh báo cho dòng lệch quá ngưỡng đối soát sản lượng. | Should | Active | BR-CLS-015. Không chặn khóa lần tính giá. |
| FR-COST-029 | Nếu một khoa trong phạm vi không có số liệu xuất kho thực tế của năm tài chính, thì hệ thống phải ghi "Chưa đối soát vật chất" cho khoa đó trên lần tính giá và chỉ cho khóa sau khi NC Finance xác nhận. | Must | Active | |
| FR-COST-030 | Khi người dùng mở phân tích độ nhạy của một dịch vụ, hệ thống phải tính lại giá thành theo sản lượng, đơn giá hoặc hình thức có máy giả định và không ghi kết quả vào lần tính giá. | Should | Active | |
| FR-COST-031 | Khi người dùng mở bảng giải trình của một dịch vụ cận lâm sàng, hệ thống phải hiển thị thêm cho từng dòng chi phí: hệ thống xét nghiệm, cấp phát sinh, hệ số k cùng các số tạo nên k, mẫu số đã dùng để chia và nhãn "Ước tính từ kế hoạch" nếu có. | Must | Active | Bổ sung cho FR-COST-010. |
| FR-COST-032 | Khi NC Finance khóa một lần tính giá có dịch vụ cận lâm sàng, hệ thống phải đưa thêm vào ảnh chụp: hệ thống xét nghiệm, kế hoạch chất lượng, hồ sơ tuân thủ, thông tin thiết bị và linh kiện, và lượng xuất kho đã dùng. | Must | Active | Bổ sung cho FR-COST-011. |

#### 3.1.12 Giá tham chiếu (BM)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-BM-001 | Khi người dùng tạo một đơn vị tham chiếu, hệ thống phải yêu cầu tên, tỉnh hoặc thành phố, loại hình và hạng hoặc cấp chuyên môn. | Must | Active | |
| FR-BM-002 | Khi người dùng nhập giá tham chiếu bằng tay hoặc bằng tệp Excel mẫu, hệ thống phải yêu cầu đơn vị, dịch vụ (mã hoặc tên gốc), giá, loại giá, ngày hiệu lực và nguồn (số văn bản hoặc đường dẫn). | Must | Active | |
| FR-BM-003 | Khi người dùng nạp tệp bảng giá PDF của một đơn vị, hệ thống phải dùng AI trích tên dịch vụ, giá và ngày hiệu lực thành các dòng giá tham chiếu ở trạng thái "Đề xuất". | Should | Active | Tệp bảng giá công khai không thuộc dữ liệu cấm của FR-AI-011. |
| FR-BM-004 | Khi một dòng giá tham chiếu có tên dịch vụ gốc chưa gắn mã, hệ thống phải đề xuất dịch vụ khớp và yêu cầu người dùng xác nhận. | Must | Active | |
| FR-BM-005 | Trong khi một dòng giá tham chiếu chưa ở trạng thái "Đã xác nhận", hệ thống phải không đưa dòng đó vào so sánh. | Must | Active | |
| FR-BM-006 | Khi NC Finance nhập chỉ số giá tiêu dùng theo tháng, hệ thống phải tính giá tham chiếu hiệu chỉnh theo BR-ADJ-009. | Should | Active | Nguồn chỉ số: TBD-11. |
| FR-BM-007 | Nếu một dòng giá tham chiếu trùng đơn vị, dịch vụ, loại giá và ngày hiệu lực với dòng đã có, thì hệ thống phải từ chối lưu. | Must | Active | |
| FR-BM-008 | Khi người dùng lập phiếu khảo sát giá cho một nhóm dịch vụ, hệ thống phải sinh tệp theo cấu trúc Phụ lục I của REF-03. | Should | Active | |

#### 3.1.13 So sánh và điều chỉnh (ADJ)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-ADJ-001 | Khi người dùng mở so sánh cho một lần tính giá, hệ thống phải chọn cho từng dịch vụ các giá tham chiếu đã xác nhận, cùng loại giá, có ngày hiệu lực trong 24 tháng trước ngày tính giá, mỗi đơn vị lấy giá mới nhất. | Must | Active | Theo Điều 4 REF-03. |
| FR-ADJ-002 | Khi một dịch vụ có từ 3 đơn vị tham chiếu trở lên, hệ thống phải tính giá thấp nhất, trung vị, cao nhất và độ lệch phần trăm của giá tính toán so với trung vị. | Must | Active | BR-ADJ-008. |
| FR-ADJ-003 | Nếu một dịch vụ có ít hơn 3 đơn vị tham chiếu, thì hệ thống phải gắn nhãn "Chưa đủ dữ liệu so sánh" và không sinh gợi ý điều chỉnh dựa trên so sánh cho dịch vụ đó. | Must | Active | Theo khoản 2 Điều 2 REF-03. |
| FR-ADJ-004 | Khi người dùng lọc đơn vị tham chiếu theo tỉnh hoặc thành phố, hạng và loại hình, hệ thống phải tính lại thống kê so sánh theo tập đã lọc. | Should | Active | |
| FR-ADJ-005 | Khi độ lệch của một dịch vụ vượt ngưỡng lệch so sánh trong bộ tham số, hệ thống phải sinh gợi ý điều chỉnh theo BR-ADJ-001 đến BR-ADJ-007, mỗi gợi ý nêu cấu phần, giá trị hiện tại, giá trị đề xuất, tác động ước tính đến giá và có cần sửa quy trình hay không. | Must | Active | Gợi ý sinh bằng quy tắc, không bằng AI. |
| FR-ADJ-006 | Khi người dùng chấp nhận một gợi ý không cần sửa quy trình, hệ thống phải ghi thay đổi vào một kịch bản điều chỉnh và tính lại giá của dịch vụ trong kịch bản đó. | Must | Active | |
| FR-ADJ-007 | Nếu một gợi ý hoặc một thay đổi do người dùng đề xuất làm thêm, bỏ hoặc đổi bước hay nguồn lực của quy trình, thì hệ thống phải từ chối áp trực tiếp và tạo yêu cầu sửa đổi quy trình gửi khoa chủ trì. | Must | Active | Luồng quay lại theo FR-WF-009. |
| FR-ADJ-008 | Khi người dùng từ chối một gợi ý, hệ thống phải yêu cầu lý do và lưu cùng gợi ý. | Should | Active | |
| FR-ADJ-009 | Khi một kịch bản điều chỉnh làm đổi dòng định mức, hệ thống phải tạo phiên bản bộ định mức mới ở trạng thái nháp để xác nhận lại theo FR-NORM-009 đến FR-NORM-011. | Must | Active | |
| FR-ADJ-010 | Khi người dùng xem một dịch vụ trong so sánh, hệ thống phải hiển thị giá trị và tỷ trọng của từng cấu phần trong giá thành. | Must | Active | |

#### 3.1.14 Phương án giá (PRICE)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-PRICE-001 | Khi NC Finance lập phương án giá từ một lần tính giá đã khóa hoặc một kịch bản điều chỉnh, hệ thống phải tạo cho từng dịch vụ một dòng gồm giá thành toàn bộ, giá tính toán, trung vị tham chiếu và giá đề xuất, mặc định bằng giá làm tròn. | Must | Active | |
| FR-PRICE-002 | Khi người dùng sửa giá đề xuất khác giá làm tròn, hệ thống phải yêu cầu ghi căn cứ điều chỉnh. | Must | Active | |
| FR-PRICE-003 | Nếu giá đề xuất của một dịch vụ thấp hơn giá thành toàn bộ, thì hệ thống phải cảnh báo và yêu cầu NC Director xác nhận riêng dòng đó khi phê duyệt. | Must | Active | |
| FR-PRICE-004 | Khi NC Finance gửi duyệt phương án giá, hệ thống phải chuyển trạng thái sang "Chờ khoa xác nhận" và thông báo cho trưởng khoa của các khoa có dịch vụ trong phương án. | Must | Active | |
| FR-PRICE-005 | Khi mọi khoa liên quan đã xác nhận, hệ thống phải chuyển phương án giá sang "Chờ phê duyệt" và thông báo cho NC Director. | Must | Active | |
| FR-PRICE-006 | Khi NC Director phê duyệt một phương án thuộc loại giá do bệnh viện quyết định, hệ thống phải khóa phương án và ghi giá đã duyệt cùng ngày áp dụng vào từng dịch vụ. | Must | Active | |
| FR-PRICE-007 | Khi NC Director phê duyệt một phương án thuộc loại giá do cơ quan có thẩm quyền quyết định, hệ thống phải khóa phương án ở trạng thái "Đã duyệt nội bộ, chờ trình". | Must | Active | |
| FR-PRICE-008 | Khi người dùng ghi kết quả phê duyệt của cơ quan có thẩm quyền (số văn bản, ngày, giá được duyệt), hệ thống phải lưu giá được duyệt bên cạnh giá đã trình và ghi vào từng dịch vụ. | Should | Active | |
| FR-PRICE-009 | Khi người duyệt ở bất kỳ cấp nào từ chối phương án giá, hệ thống phải yêu cầu lý do và trả phương án về "Nháp". | Must | Active | |
| FR-PRICE-010 | Khi giá đã duyệt của một dịch vụ thay đổi, hệ thống phải giữ lịch sử giá theo loại giá và ngày áp dụng. | Must | Active | |

#### 3.1.15 Đầu ra và báo cáo (OUT)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-OUT-001 | Khi người dùng xuất phương án giá, hệ thống phải sinh tệp Excel theo cấu trúc Phụ lục II của REF-03 cho từng dịch vụ. | Must | Active | Mẫu biểu chính thức: TBD-01. |
| FR-OUT-002 | Khi người dùng xuất bảng tính giá thành theo yếu tố chi phí, hệ thống phải sinh tệp Excel theo cấu trúc Phụ lục III của REF-03. | Must | Active | TBD-01. |
| FR-OUT-003 | Khi người dùng xuất bảng tính giá thành theo phương pháp phân bổ, hệ thống phải sinh tệp Excel theo cấu trúc Phụ lục IV của REF-03. | Should | Active | TBD-01. |
| FR-OUT-004 | Khi người dùng xuất danh mục dịch vụ đề nghị định giá, hệ thống phải sinh tệp Excel theo cấu trúc Phụ lục V của REF-03. | Must | Active | TBD-01. |
| FR-OUT-005 | Khi người dùng xuất bảng giải trình của một dịch vụ, hệ thống phải sinh tệp PDF gồm các dòng chi phí theo FR-COST-010, nhóm theo cấu phần và theo bước. | Must | Active | |
| FR-OUT-006 | Khi người dùng xuất một bộ định mức, hệ thống phải sinh tệp Excel và PDF liệt kê các dòng định mức theo bước, kèm căn cứ và người xác nhận. | Must | Active | |
| FR-OUT-007 | Khi người dùng xuất bảng so sánh giá, hệ thống phải sinh tệp Excel gồm đơn vị tham chiếu, giá, ngày hiệu lực, nguồn và các thống kê so sánh. | Must | Active | |
| FR-OUT-008 | Khi hệ thống sinh một tệp xuất, hệ thống phải ghi ở chân trang hoặc trang thông tin: mã lần tính giá, bộ tham số, thời điểm xuất và người xuất. | Must | Active | |
| FR-OUT-009 | Khi người dùng yêu cầu xuất toàn bộ hồ sơ của một phương án giá, hệ thống phải đóng gói các tệp thành một tệp nén bằng tác vụ nền. | Could | Active | |
| FR-OUT-010 | Khi người dùng mở trang chủ Normcore, hệ thống phải hiển thị số dịch vụ theo tình trạng chuỗi: chưa có quy trình, có quy trình, có định mức đã khóa, đã tính giá, đã duyệt giá. | Should | Active | Lọc theo khoa trong phạm vi quyền. |
| FR-OUT-011 | Khi người dùng xuất bộ định mức của một hệ thống xét nghiệm, hệ thống phải đưa thêm vào tệp của FR-OUT-006: cấp phát sinh của từng dòng, kế hoạch nội kiểm, chuẩn máy, ngoại kiểm và hệ số k của lần tính giá gần nhất. | Must | Active | |
| FR-OUT-012 | Khi người dùng mở báo cáo thiếu dữ liệu của một phạm vi tính giá, hệ thống phải liệt kê các dịch vụ thiếu đơn giá, thiếu sản lượng, thiếu bấm giờ, thiếu kế hoạch chất lượng hoặc thiếu hồ sơ tuân thủ. | Must | Active | Chạy được trước khi tạo lần tính giá. |

#### 3.1.16 Nhật ký (AUD)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-AUD-001 | Khi một bản ghi nghiệp vụ được tạo, sửa, chuyển trạng thái hoặc xóa, hệ thống phải ghi người thực hiện, thời điểm, giá trị trước và giá trị sau. | Must | Active | |
| FR-AUD-002 | Hệ thống phải không cho phép bất kỳ vai trò nào sửa hoặc xóa nhật ký qua giao diện hoặc API. | Must | Active | |
| FR-AUD-003 | Khi NC Admin, NC Director hoặc NC Auditor tra cứu nhật ký theo bản ghi, người dùng hoặc khoảng thời gian, hệ thống phải trả về các sự kiện khớp theo thứ tự thời gian. | Must | Active | Sửa ở 1.1: thêm NC Auditor. |
| FR-AUD-004 | Khi người dùng xuất một tệp chứa số liệu tài chính, hệ thống phải ghi nhật ký xuất gồm người xuất, loại tệp và bản ghi nguồn. | Should | Active | |

#### 3.1.17 Thông báo (NOTI)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-NOTI-001 | Khi một bản ghi chuyển đến bước cần một người dùng hoặc một vai trò xử lý, hệ thống phải tạo thông báo trong ứng dụng cho đối tượng đó kèm liên kết đến bản ghi. | Must | Active | |
| FR-NOTI-002 | Ở nơi máy chủ email được cấu hình, hệ thống phải gửi thêm email cho các thông báo của FR-NOTI-001. | Should | Active | |
| FR-NOTI-003 | Khi người dùng mở trang chủ Normcore, hệ thống phải hiển thị danh sách việc đang chờ người đó xử lý. | Must | Active | |

#### 3.1.18 Quản trị (ADM)

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-ADM-001 | Khi ứng dụng được cài đặt trên một site, hệ thống phải tạo sẵn các vai trò, luồng duyệt, loại giá mẫu, mẫu in và mẫu lệnh AI mặc định. | Must | Active | |
| FR-ADM-002 | Khi người dùng yêu cầu tệp mẫu nhập liệu của một danh mục, hệ thống phải cung cấp tệp Excel mẫu có tiêu đề cột và một dòng ví dụ. | Must | Active | |
| FR-ADM-003 | Khi NC Admin thay đổi một tham số vận hành (số ca bấm giờ tối thiểu, số ngày nhắc duyệt, thời hạn gọi AI), hệ thống phải áp giá trị mới cho các thao tác kế tiếp. | Must | Active | |
| FR-ADM-004 | Khi NC Admin khai báo khoa, phòng và trung tâm chi phí, hệ thống phải yêu cầu mã, tên, loại (Lâm sàng, Cận lâm sàng, Hỗ trợ) và liên kết khoa với trung tâm chi phí. | Must | Active | |
| FR-ADM-005 | Nếu người dùng xóa một bản ghi danh mục đang được bản ghi khác tham chiếu, thì hệ thống phải từ chối xóa và nêu bản ghi tham chiếu. | Must | Active | |
| FR-ADM-006 | Khi NC Admin thay đổi số ngày nhắc hạn hồ sơ tuân thủ hoặc danh sách loại thiết bị bắt buộc có hồ sơ tuân thủ, hệ thống phải áp giá trị mới cho các thao tác kế tiếp. | Should | Active | Số ngày nhắc mặc định 30. Danh sách loại thiết bị: TBD-18. |

#### 3.1.19 Hệ thống xét nghiệm (CLS)

Nhóm mới ở bản 1.1. "Hệ thống xét nghiệm" là tổ hợp một dịch vụ cận lâm sàng, một khoa và một thiết bị chính. Khái niệm này dùng cho cả xét nghiệm và chẩn đoán hình ảnh. Dịch vụ cận lâm sàng vẫn cần quy trình "Đã ban hành" trước khi có bộ định mức (FR-NORM-002); ba công đoạn tiền phân tích, phân tích, hậu phân tích là các bước của quy trình.

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-CLS-001 | Khi người dùng tạo một hệ thống xét nghiệm, hệ thống phải yêu cầu mã, dịch vụ, khoa, thiết bị chính và tỷ trọng sản lượng, và cho phép nhập tỷ lệ chạy lại ước tính và tỷ lệ hao hụt ước tính. | Must | Active | Hai tỷ lệ ước tính dùng khi sản lượng không có số thực tế (BR-CLS-001). |
| FR-CLS-002 | Hệ thống phải cho phép một dịch vụ trong một khoa có nhiều hệ thống xét nghiệm. | Must | Active | Ví dụ: cùng một xét nghiệm chạy trên hai máy với hóa chất và hình thức có máy khác nhau. |
| FR-CLS-003 | Nếu tổng tỷ trọng sản lượng của các hệ thống xét nghiệm đang dùng của một dịch vụ trong một khoa khác 100%, thì hệ thống phải dừng tính dịch vụ đó trong lần tính giá, ghi lỗi và tiếp tục tính các dịch vụ khác. | Must | Active | Không áp dụng khi tỷ trọng lấy theo FR-CLS-004. |
| FR-CLS-004 | Khi sản lượng của kịch bản được chọn có số kết quả trả theo từng hệ thống xét nghiệm, hệ thống phải tính tỷ trọng từ số kết quả trả đó thay cho tỷ trọng khai tay. | Should | Active | BR-CLS-013. |
| FR-CLS-005 | Khi người dùng tạo hệ thống xét nghiệm có thiết bị chính chia chi phí theo Phút chiếm máy, hệ thống phải yêu cầu số phút chiếm máy của một ca. | Should | Active | Dùng cho chẩn đoán hình ảnh; ngoài phạm vi nghiệm thu của bản phát hành 1. |
| FR-CLS-006 | Trong khi một hệ thống xét nghiệm được đánh dấu ngừng dùng, hệ thống phải không đưa hệ thống đó vào các lần tính giá mới và giữ nguyên các lần tính giá đã khóa. | Should | Active | |
| FR-CLS-007 | Khi người dùng mở một hệ thống xét nghiệm, hệ thống phải hiển thị bộ định mức hiện hành, kế hoạch chất lượng, sản lượng của kịch bản mặc định, và hệ số k cùng giá thành một kết quả của lần tính giá gần nhất. | Should | Active | |
| FR-CLS-008 | Khi người dùng nhập từ tệp Excel mẫu các hệ thống xét nghiệm, kế hoạch chất lượng hoặc hồ sơ tuân thủ, hệ thống phải tạo mới hoặc cập nhật theo mã và báo cáo các dòng lỗi. | Should | Active | Cùng cơ chế với FR-RES-012. |

#### 3.1.20 Kế hoạch chất lượng xét nghiệm (QC)

Nhóm mới ở bản 1.1. Normcore lưu kế hoạch và chi phí của nội kiểm, chuẩn máy, ngoại kiểm để tính giá; không ghi kết quả kiểm tra chất lượng.

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-QC-001 | Khi người dùng lập kế hoạch nội kiểm cho một hệ thống xét nghiệm, hệ thống phải yêu cầu vật liệu nội kiểm, số mức, số lần chạy mỗi ngày, lượng dùng mỗi lần, số ngày chạy mỗi năm và số thông số dùng chung vật liệu. | Must | Active | BR-CLS-006. |
| FR-QC-002 | Khi người dùng lập kế hoạch chuẩn máy cho một hệ thống xét nghiệm, hệ thống phải yêu cầu chất chuẩn, số điểm chuẩn, số lần lặp, số lần chuẩn mỗi năm và chi phí chất chuẩn mỗi lần. | Must | Active | BR-CLS-007. |
| FR-QC-003 | Khi người dùng khai một chương trình ngoại kiểm, hệ thống phải yêu cầu đơn vị triển khai, các dịch vụ tham gia, số đợt mỗi năm, số mẫu mỗi đợt, phí chương trình năm và phí vận chuyển năm. | Must | Active | BR-CLS-008. |
| FR-QC-004 | Khi lần tính giá chạy, hệ thống phải chia phí của một chương trình ngoại kiểm đều cho các dịch vụ tham gia, trừ khi người dùng đã khai tỷ lệ riêng cho từng dịch vụ. | Must | Active | |
| FR-QC-005 | Nếu tổng tỷ lệ riêng của các dịch vụ trong một chương trình ngoại kiểm khác 100%, thì hệ thống phải từ chối lưu chương trình. | Must | Active | |
| FR-QC-006 | Khi sản lượng của kịch bản được chọn không có số test nội kiểm, chuẩn máy, chạy lại hoặc ngoại kiểm thực tế, hệ thống phải suy ra các số đó từ kế hoạch chất lượng và các tỷ lệ ước tính, và gắn nhãn "Ước tính từ kế hoạch" trên kết quả. | Must | Active | BR-CLS-001. Xem TBD-16. |
| FR-QC-007 | Nếu một hệ thống xét nghiệm thuộc nhóm chuyên ngành xét nghiệm không có kế hoạch nội kiểm, thì hệ thống phải cảnh báo trên bộ định mức của hệ thống đó. | Should | Active | Không chặn khóa bộ định mức. |
| FR-QC-008 | Nếu người dùng chọn cho kế hoạch nội kiểm một mặt hàng không thuộc loại Vật liệu nội kiểm, hoặc cho kế hoạch chuẩn máy một mặt hàng không thuộc loại Chất chuẩn, thì hệ thống phải từ chối lưu. | Must | Active | Hóa chất tiêu hao khi nội kiểm và chuẩn máy đã nằm trong hệ số k. |

#### 3.1.21 Hồ sơ tuân thủ thiết bị (CMP)

Nhóm mới ở bản 1.1. Áp dụng cho mọi thiết bị của Normcore, không riêng thiết bị cận lâm sàng (điểm X-03 của REF-09).

| ID | Requirement | Priority | Status | Notes / rules |
| :-- | :---------- | :------- | :----- | :------------ |
| FR-CMP-001 | Khi NC Resource Manager tạo hồ sơ tuân thủ cho một thiết bị, hệ thống phải yêu cầu loại hồ sơ, chu kỳ tính bằng tháng, đơn vị thực hiện, chi phí mỗi lần, ngày thực hiện, ngày hết hạn và tệp chứng từ. | Must | Active | Loại: Kiểm định, Hiệu chuẩn, Kiểm xạ, Giấy phép an toàn bức xạ, Khác. |
| FR-CMP-002 | Khi lần tính giá chạy, hệ thống phải quy chi phí của mỗi hồ sơ tuân thủ còn hạn tại ngày tính giá về chi phí năm theo chu kỳ và dùng tổng đó làm chi phí kiểm định, hiệu chuẩn năm của thiết bị thay cho số nhập tay. | Must | Active | BR-CLS-011. Thiết bị không có hồ sơ nào: dùng số nhập tay của FR-RES-005. |
| FR-CMP-003 | Khi lần tính giá dùng cách phân bổ Theo giá trị tài sản, hệ thống phải gom chi phí kiểm định, hiệu chuẩn năm của mọi thiết bị trong một khoa và chia cho từng thiết bị theo tỷ lệ giá trị tài sản. | Must | Active | Mặc định (REF-09). BR-CLS-011. |
| FR-CMP-004 | Khi lần tính giá dùng cách phân bổ Gắn trực tiếp thiết bị, hệ thống phải lấy chi phí kiểm định, hiệu chuẩn năm của từng thiết bị bằng chi phí hồ sơ của chính thiết bị đó. | Must | Active | BR-CLS-011. |
| FR-CMP-005 | Khi một hồ sơ tuân thủ còn không quá số ngày cấu hình đến ngày hết hạn, hệ thống phải thông báo cho NC Resource Manager và trưởng khoa của khoa quản lý thiết bị. | Should | Active | Tác vụ định kỳ hằng ngày; thông báo theo FR-NOTI-001. |
| FR-CMP-006 | Nếu một thiết bị thuộc loại bắt buộc có hồ sơ tuân thủ mà không có hồ sơ còn hạn tại ngày tính giá, thì hệ thống phải gắn cảnh báo trên lần tính giá và vẫn tính. | Must | Active | Danh sách loại thiết bị bắt buộc là dữ liệu cấu hình (FR-ADM-006, TBD-18). |
| FR-CMP-007 | Khi người dùng mở báo cáo hồ sơ tuân thủ, hệ thống phải liệt kê theo khoa các hồ sơ đã hết hạn và các hồ sơ sắp hết hạn. | Should | Active | |

### 3.2 External interface requirements

**Giao diện người dùng.** Một bề mặt duy nhất: giao diện Desk của Frappe trên trình duyệt, tiếng Việt. Danh mục màn hình ở `docs/ux-foundations.md`.

**Giao diện phần mềm.**

| Mã | Giao diện | Hướng | Định dạng |
| :-- | :-- | :-- | :-- |
| IF-01 | Dịch vụ mô hình ngôn ngữ | Normcore gọi ra | HTTPS, JSON; hai bộ chuyển đổi: giao thức tương thích OpenAI Chat Completions và giao thức Anthropic Messages |
| IF-02 | Số liệu chi phí kế toán | Nhập vào | Tệp Excel theo mẫu Normcore |
| IF-03 | Sản lượng dịch vụ từ HIS | Nhập vào | Tệp Excel theo mẫu Normcore |
| IF-04 | Danh mục (dịch vụ, mặt hàng, đơn giá, thiết bị, phòng, chức danh, giá tham chiếu, hệ thống xét nghiệm, kế hoạch chất lượng, hồ sơ tuân thủ) | Nhập vào | Tệp Excel theo mẫu Normcore |
| IF-05 | Hồ sơ xuất | Xuất ra | Excel, PDF, DOCX |
| IF-06 | Email | Normcore gọi ra | SMTP qua cấu hình Email Account của Frappe |
| IF-07 | Sản lượng cận lâm sàng từ LIS, RIS (số kết quả trả, số test nội kiểm, chuẩn máy, chạy lại, ngoại kiểm, cỡ mẻ, số ngày chạy, phút khai thác) | Nhập vào | Tệp Excel theo mẫu Normcore |
| IF-08 | Lượng xuất kho thực tế theo mặt hàng và khoa | Nhập vào | Tệp Excel theo mẫu Normcore |

**Giao diện phần cứng.** Không có.

**Giao diện truyền thông.** HTTPS cho mọi truy cập của người dùng và mọi lần gọi dịch vụ ngoài.

### 3.3 Non-functional requirements

| ID | Category | Requirement (metric, target, condition) | Priority |
| :-- | :------- | :-------------------------------------- | :------- |
| NFR-PERF-001 | Performance | 95% lượt mở danh sách và form hoàn tất trong 2 giây với 50 người dùng đồng thời trên cấu hình máy chủ khuyến nghị. | Must |
| NFR-PERF-002 | Performance | Một lần tính giá 500 dịch vụ, 50.000 dòng định mức hoàn tất trong 5 phút. | Must |
| NFR-PERF-003 | Performance | Tính lại chi phí trực tiếp tạm tính của một bộ định mức 200 dòng trong 3 giây. | Should |
| NFR-PERF-004 | Performance | 95% lần soạn dự thảo bằng AI trả kết quả trong 180 giây; giao diện hiển thị tiến độ trong lúc chờ. | Should |
| NFR-PERF-005 | Performance | 95% lượt tìm kiếm trong thư viện văn bản trả kết quả trong 3 giây với 2.000 văn bản và 200.000 mục. | Should |
| NFR-SCAL-001 | Capacity | Một site vận hành được với 200 tài khoản, 5.000 dịch vụ kỹ thuật, 500.000 dòng định mức, 20 lần tính giá mỗi năm trong 10 năm. | Must |
| NFR-SCAL-002 | Capacity | Thư viện nhận tệp đến 100 MB mỗi tệp và 2.000 văn bản mỗi site. | Should |
| NFR-AVL-001 | Availability | Khả dụng 99,5% mỗi tháng trong khung 07:00 đến 19:00 các ngày làm việc. | Should |
| NFR-AVL-002 | Recoverability | Sao lưu cơ sở dữ liệu và tệp hằng ngày, lưu 30 ngày; RPO 24 giờ; RTO 8 giờ. | Must |
| NFR-REL-001 | Reliability | Chạy lại một lần tính giá với cùng ảnh chụp đầu vào cho kết quả trùng đến từng đồng ở mọi dịch vụ. | Must |
| NFR-REL-002 | Reliability | Phép tính tiền dùng số thập phân chính xác; không dùng số thực dấu phẩy động. | Must |
| NFR-REL-003 | Reliability | Hệ số tiêu hao k được tính bằng số thập phân chính xác và lưu với 6 chữ số thập phân; chạy lại cùng ảnh chụp cho cùng giá trị k ở mọi hệ thống xét nghiệm. | Must |
| NFR-SEC-001 | Security | Mọi truy cập qua HTTPS với TLS 1.2 trở lên. | Must |
| NFR-SEC-002 | Security | Mật khẩu tối thiểu 8 ký tự theo chính sách mật khẩu của Frappe bật ở mức 2 trở lên; phiên hết hạn sau 8 giờ. | Must |
| NFR-SEC-003 | Security | 100% DocType nghiệp vụ có khai báo quyền theo vai trò; không DocType nào để quyền mở cho mọi người dùng đã đăng nhập. | Must |
| NFR-SEC-004 | Security | Khóa truy cập dịch vụ AI lưu ở dạng mã hóa, không hiển thị lại trên giao diện và không ghi vào nhật ký. | Must |
| NFR-SEC-005 | Security | 0 lần gọi AI chứa dữ liệu thuộc nhóm cấm của FR-AI-011, kiểm bằng kiểm thử tự động trên bộ dựng nội dung gửi AI. | Must |
| NFR-SEC-006 | Security | Nhật ký AI và nhật ký thay đổi được lưu tối thiểu 10 năm. | Should |
| NFR-USE-001 | Usability | 100% nhãn, thông báo và tệp xuất bằng tiếng Việt. | Must |
| NFR-USE-002 | Usability | Sau 60 phút hướng dẫn, người soạn tạo được một dự thảo quy trình 10 bước và gửi duyệt trong 15 phút. | Should |
| NFR-USE-003 | Usability | Phiếu bấm giờ thao tác được trên máy tính bảng màn hình từ 768 px bề ngang, mỗi lần ghi một bước không quá 3 lần chạm. | Should |
| NFR-USE-004 | Accessibility | Các trang tùy biến đạt tương phản chữ tối thiểu 4,5:1 và thao tác được bằng bàn phím. | Should |
| NFR-CMP-001 | Compatibility | Chạy trên Frappe Framework v15, không cần ERPNext; trình duyệt Chrome và Edge hai phiên bản mới nhất. | Must |
| NFR-CPL-001 | Compliance | 100% dòng chi phí trong bảng giải trình có liên kết đến bước quy trình hoặc quy tắc phân bổ, và đến nguồn đơn giá. | Must |
| NFR-CPL-002 | Compliance | Cấu trúc cột của các tệp xuất theo Phụ lục II đến V khớp mẫu chính thức của REF-03 khi đối chiếu từng cột. | Must |
| NFR-CPL-003 | Compliance | 100% dòng chi phí cận lâm sàng trong bảng giải trình hiển thị cấp phát sinh, mẫu số đã dùng để chia và nguồn của mẫu số (số thực tế hoặc ước tính từ kế hoạch). | Must |
| NFR-MNT-001 | Maintainability | Bộ máy tính giá có kiểm thử đơn vị phủ tối thiểu 90% số dòng mã; bộ dữ liệu vàng ở `docs/test-cases.md` chạy trong CI. | Must |
| NFR-MNT-002 | Maintainability | Mỗi tính năng nghiệm thu có tài liệu As-Built và đạt Definition of Done ở `docs/implementation-plan.md` mục 6. | Must |
| NFR-MNT-003 | Maintainability | 100% fieldname bằng tiếng Anh dạng snake_case; 100% label bằng tiếng Việt. | Must |
| NFR-LOC-001 | Localization | Số hiển thị theo định dạng `1.234.567`; tiền là đồng Việt Nam không có phần lẻ; ngày theo `dd/mm/yyyy`; múi giờ Asia/Ho_Chi_Minh. | Must |
| NFR-OBS-001 | Observability | Mọi tác vụ nền (tách văn bản, gọi AI, tính giá, xuất tệp) ghi trạng thái, thời gian chạy và lỗi; NC Admin xem được trong ứng dụng. | Must |
| NFR-OBS-002 | Observability | Số token và số lần gọi AI theo tháng xem được theo mục đích sử dụng. | Should |

Lưu ý: mã nhóm NFR-CMP (Compatibility) và mã nhóm FR-CMP (hồ sơ tuân thủ thiết bị) là hai nhóm khác nhau; tiền tố NFR và FR phân biệt chúng.

### 3.4 Other requirements

#### 3.4.1 Quy tắc tính giá (BR-COST)

Mọi phép tính dùng số thập phân chính xác. Đơn giá giữ đến 4 chữ số thập phân; thành tiền mỗi dòng làm tròn đến 2 chữ số thập phân; chỉ giá cuối làm tròn theo đơn vị làm tròn.

| Mã | Quy tắc |
| :-- | :-- |
| BR-COST-001 | **Đơn giá giờ công.** Chi phí năm của chức danh = lương cơ sở × (hệ số lương + hệ số phụ cấp được tính) × 12 × (1 + tỷ lệ đóng góp) + thu nhập khác được tính trong năm. Đơn giá giờ công = chi phí năm ÷ (số ngày làm việc năm × số giờ làm việc ngày). Cho phép nhập thẳng chi phí năm thay cho công thức. |
| BR-COST-002 | **Chi phí nhân lực của dòng** = số phút áp dụng ÷ 60 × số người × đơn giá giờ công của chức danh. |
| BR-COST-003 | **Chi phí thuốc, hóa chất, vật tư của dòng** = lượng áp dụng × (1 + tỷ lệ hao hụt) × đơn giá ÷ số lần dùng. |
| BR-COST-004 | **Đơn giá giờ máy** = (khấu hao năm + bảo trì năm + kiểm định, hiệu chuẩn năm) ÷ (giờ khai thác kế hoạch năm × hệ số sử dụng). Khấu hao năm = nguyên giá ÷ thời gian sử dụng (năm); khi đã hết thời gian sử dụng thì bằng 0 hoặc giữ nguyên theo lựa chọn trong bộ tham số (FR-RES-007). Kiểm định, hiệu chuẩn năm của thiết bị xác định theo BR-CLS-011 và cách phân bổ của lần tính giá. Chi phí thiết bị của dòng = số phút máy áp dụng ÷ 60 × đơn giá giờ máy. Quy tắc này áp cho thiết bị có tiêu chí chia Giờ kế hoạch và hình thức Mua; hình thức và tiêu chí khác theo BR-CLS-009. *Sửa ở 1.1 (điểm X-03, X-04 của REF-09): bản 1.0 lấy kiểm định năm từ số nhập tay của từng thiết bị và luôn lấy khấu hao bằng 0 khi hết thời gian sử dụng.* |
| BR-COST-005 | **Đơn giá giờ phòng** = chi phí hạ tầng năm ÷ giờ khai thác năm. Chi phí hạ tầng của dòng = số phút ÷ 60 × đơn giá giờ phòng. |
| BR-COST-006 | **Chi phí tiện ích của dòng** = lượng áp dụng × đơn giá tiện ích (điện theo kWh, nước theo m³, hoặc đơn giá của mặt hàng tiện ích). |
| BR-COST-007 | **Lượng áp dụng.** Nếu dòng có định mức do cơ quan có thẩm quyền ban hành: lượng áp dụng = giá trị nhỏ hơn giữa định mức của bệnh viện và định mức ban hành. Nếu không có: lượng áp dụng = định mức của bệnh viện. |
| BR-COST-008 | **Loại chi phí kế toán.** Mỗi dòng số liệu kế toán thuộc một trong các loại: `LABOR` (tiền lương và các khoản theo lương), `DRUG_SUPPLY` (thuốc, hóa chất, vật tư), `DEPRECIATION` (khấu hao tài sản), `UTILITY` (điện, nước, nhiên liệu, xử lý chất thải, vệ sinh), `MANAGEMENT` (chi phí quản lý và chi phí chung khác), `EXCLUDED` (không tính vào giá). |
| BR-COST-009 | **Tiêu chí phân bổ.** `LABOR_MIN` (tổng phút nhân lực áp dụng × sản lượng), `MACHINE_MIN` (tổng phút máy × sản lượng), `VOLUME` (sản lượng), `DIRECT_COST` (chi phí trực tiếp × sản lượng), `REVENUE` (doanh thu), `HEADCOUNT` (số nhân lực), `AREA` (diện tích). Ba tiêu chí cuối chỉ dùng ở cấp 1. |
| BR-COST-010 | **Phân bổ cấp 1.** Với mỗi trung tâm chi phí hỗ trợ và mỗi loại chi phí: phần của trung tâm lâm sàng k = số tiền × tiêu chí của k ÷ tổng tiêu chí của mọi trung tâm lâm sàng. Phân bổ một lần, không phân bổ vòng giữa các trung tâm hỗ trợ. |
| BR-COST-011 | **Phân bổ cấp 2.** Với mỗi trung tâm lâm sàng và mỗi loại chi phí: phần còn lại = (số kế toán của trung tâm + phần nhận từ cấp 1) − tổng chi phí trực tiếp cùng loại đã tính từ định mức của các dịch vụ thuộc trung tâm (chi phí đơn vị × sản lượng). Nếu phần còn lại nhỏ hơn 0 thì lấy bằng 0 và ghi nhận ở đối soát. Phần của dịch vụ s cho một ca = phần còn lại × tiêu chí của s ÷ tổng tiêu chí ÷ sản lượng của s. Loại `MANAGEMENT` không có chi phí trực tiếp nên phân bổ toàn bộ. |
| BR-COST-012 | **Giá thành toàn bộ một ca** = tổng chi phí trực tiếp các dòng + tổng các khoản phân bổ cấp 2. |
| BR-COST-013 | **Tích lũy và nghĩa vụ tài chính.** Tích lũy = giá thành toàn bộ × tỷ lệ tích lũy (cách tính `ON_COST`), hoặc giá thành toàn bộ × tỷ lệ ÷ (1 − tỷ lệ) (cách tính `ON_PRICE`), hoặc 0 khi loại giá không có tích lũy. Giá tính toán = (giá thành toàn bộ + tích lũy) ÷ (1 − tỷ lệ nghĩa vụ tài chính). Xem TBD-02. |
| BR-COST-014 | **Giá làm tròn** = giá tính toán làm tròn đến bội số gần nhất của đơn vị làm tròn, nửa đơn vị làm tròn lên. |
| BR-COST-015 | **Đối soát.** Với mỗi trung tâm lâm sàng và loại chi phí: số đã tính = Σ (chi phí trực tiếp đơn vị cùng loại × sản lượng); số kế toán = số của trung tâm + phần nhận từ cấp 1; chênh lệch phần trăm = (số đã tính − số kế toán) ÷ số kế toán × 100. Dòng bị đánh dấu "Vượt ngưỡng" khi: (a) chênh lệch phần trăm lớn hơn ngưỡng đối soát ở bất kỳ loại chi phí nào, nghĩa là định mức đang cao hơn thực chi; hoặc (b) với loại `DRUG_SUPPLY`, chênh lệch phần trăm nhỏ hơn âm ngưỡng đối soát, nghĩa là có tiêu hao thực tế chưa được định mức. Với `LABOR`, `DEPRECIATION`, `UTILITY`, số đã tính thấp hơn số kế toán là bình thường (phần gián tiếp được phân bổ cấp 2) và chỉ hiển thị để theo dõi. Loại `MANAGEMENT` không lập dòng đối soát. |
| BR-COST-016 | **Loại giá không kết cấu khấu hao.** Khấu hao năm của thiết bị lấy bằng 0 (đơn giá giờ máy chỉ còn bảo trì và kiểm định); đơn giá giờ phòng lấy bằng 0; số kế toán loại `DEPRECIATION` không được phân bổ cấp 2 và không lập dòng đối soát. Bảng giải trình ghi rõ các khoản bị loại. |

Ánh xạ cấu phần định mức sang loại chi phí kế toán: Nhân lực → `LABOR`; Thuốc và hóa chất, Vật tư → `DRUG_SUPPLY`; Thiết bị, Hạ tầng → `DEPRECIATION`; Tiện ích → `UTILITY`.

#### 3.4.2 Quy tắc so sánh và gợi ý điều chỉnh (BR-ADJ)

| Mã | Hướng | Điều kiện kích hoạt | Gợi ý | Cần sửa quy trình |
| :-- | :-- | :-- | :-- | :-- |
| BR-ADJ-001 | Giảm | Thiết bị trong dịch vụ có hệ số sử dụng dưới 0,5 | Rà soát hệ số sử dụng và giờ khai thác; nêu tác động khi nâng lên 0,5 | Không |
| BR-ADJ-002 | Giảm | Số phút định mức của một dòng cao hơn trung vị bấm giờ trên 15% | Đưa số phút về trung vị bấm giờ | Không |
| BR-ADJ-003 | Giảm | Mặt hàng có mặt hàng cùng nhóm tương đương với đơn giá thấp hơn | Thay bằng mặt hàng tương đương giá thấp nhất | Có |
| BR-ADJ-004 | Giảm | Tỷ lệ hao hụt của dòng vượt trần hao hụt | Đưa tỷ lệ hao hụt về trần | Không |
| BR-ADJ-005 | Giảm hoặc tăng | Tỷ lệ tích lũy khác 0 và loại giá cho phép tích lũy | Nêu tác động của mỗi 1 điểm phần trăm tích lũy | Không |
| BR-ADJ-006 | Tăng | Dịch vụ có dòng thiết bị nhưng thiết bị không có chi phí bảo trì; hoặc không có dòng hạ tầng; hoặc không có dòng tiện ích | Bổ sung cấu phần còn thiếu | Không |
| BR-ADJ-007 | Tăng | Đơn giá dùng trong dịch vụ quá 24 tháng; hoặc bộ tham số không phải bộ hiệu lực mới nhất | Cập nhật đơn giá hoặc bộ tham số | Không |
| BR-ADJ-008 | Thống kê | Luôn áp dụng | Trung vị của n giá: sắp tăng dần, n lẻ lấy giá trị giữa, n chẵn lấy trung bình hai giá trị giữa. Độ lệch % = (giá tính toán − trung vị) ÷ trung vị × 100 | Không áp dụng |
| BR-ADJ-009 | Hiệu chỉnh | Có chỉ số giá tiêu dùng của tháng hiệu lực và tháng tính giá | Giá hiệu chỉnh = giá × chỉ số tháng tính giá ÷ chỉ số tháng hiệu lực | Không áp dụng |

Gợi ý được xếp theo tác động ước tính đến giá, từ lớn đến nhỏ. Không quy tắc nào được đề xuất bỏ bước hay giảm số lượng nguồn lực chuyên môn; thay đổi loại đó chỉ đến từ người dùng và đi theo FR-ADJ-007.

#### 3.4.3 Vòng đời bản ghi

| Đối tượng | Trạng thái |
| :-- | :-- |
| Quy trình | Nháp → Chờ trưởng khoa duyệt → Chờ hội đồng thẩm định → Chờ ban hành → Đã ban hành → Đã thay thế / Đã thu hồi. Từ chối ở mọi cấp: về Nháp |
| Bộ định mức | Nháp → Đã xác nhận chuyên môn → Đã khóa → Đã thay thế |
| Lần nhập kế toán | Nháp → Đã chốt |
| Lần tính giá | Nháp → Đang tính → Đã tính → Đã khóa. Lỗi: Tính lỗi |
| Giá tham chiếu | Đề xuất → Đã xác nhận / Loại bỏ |
| Phương án giá | Nháp → Chờ khoa xác nhận → Chờ phê duyệt → Đã duyệt / Đã duyệt nội bộ, chờ trình → Đã được cấp thẩm quyền duyệt. Từ chối: về Nháp |
| Đơn giá (thêm ở 1.1) | Chưa xác minh → Đã xác minh |
| Hệ thống xét nghiệm (thêm ở 1.1) | Đang dùng → Ngừng dùng |
| Hồ sơ tuân thủ (thêm ở 1.1) | Còn hạn → Sắp hết hạn → Hết hạn; trạng thái tính theo ngày hết hạn và số ngày nhắc |

Bộ định mức của hệ thống xét nghiệm và lần tính giá có dịch vụ cận lâm sàng dùng chung vòng đời ở trên; phiên bản mới là bản ghi mới, không dùng cơ chế amend của Frappe (điểm X-09 của REF-09).

#### 3.4.4 Lưu trữ dữ liệu

Quy trình đã ban hành, bộ định mức đã khóa, lần tính giá đã khóa và phương án giá đã duyệt không bị xóa. Thời hạn lưu tối thiểu 10 năm (TBD-08).

#### 3.4.5 Quy tắc tính cho khối cận lâm sàng (BR-CLS)

Thêm ở bản 1.1. Các quy tắc này tính chi phí trực tiếp của dịch vụ có hệ thống xét nghiệm. Quy ước làm tròn của mục 3.4.1 giữ nguyên; riêng hệ số k giữ 6 chữ số thập phân (điểm X-07 của REF-09).

Ký hiệu, tính cho một hệ thống xét nghiệm trong một năm theo kịch bản sản lượng của lần tính giá: `Qbn` số kết quả trả cho người bệnh; `Qnk` số test nội kiểm; `Qchuan` số test chuẩn máy; `Qlai` số test chạy lại; `Qngk` số test ngoại kiểm; `h` tỷ lệ hao hụt (thể tích chết, hết hạn sau mở); `D` số ngày chạy máy. Tính cho một thiết bị trong một khoa: `Qtb` tổng số kết quả trả của mọi dịch vụ chạy trên thiết bị; `Mtb` tổng số phút khai thác; `m` số phút chiếm máy của một ca.

| Mã | Quy tắc |
| :-- | :-- |
| BR-CLS-001 | **Hệ số tiêu hao k** = (Qbn + Qnk + Qchuan + Qlai + Qngk) ÷ ((1 − h) × Qbn), làm tròn 6 chữ số thập phân trước khi dùng. Khi thiếu số thực tế: Qnk = số mức × số lần mỗi ngày × D; Qchuan = số lần chuẩn năm × số điểm chuẩn × số lần lặp; Qngk = số đợt × số mẫu mỗi đợt; Qlai = tỷ lệ chạy lại ước tính × Qbn, làm tròn đến số nguyên; h = tỷ lệ hao hụt ước tính. Với chẩn đoán hình ảnh: Qnk = Qchuan = Qngk = 0 và h = 0, tức k = 1 + Qlai ÷ Qbn. Ví dụ: Qbn 12.000, Qnk 600, Qchuan 48, Qlai 240, Qngk 12, h 3% cho k = 12.900 ÷ 11.640 = 1,108247. |
| BR-CLS-002 | **Dòng Theo kết quả.** Đơn giá một đơn vị định mức = đơn giá của đơn vị mua ÷ số đơn vị định mức trong một đơn vị mua. Dòng bật cờ nhân k: chi phí = lượng áp dụng × đơn giá một đơn vị định mức × k, không áp tỷ lệ hao hụt của dòng. Dòng không bật cờ: theo BR-COST-003. Ví dụ: 1 test × 30.000 đồng × 1,108247 = 33.247,41 đồng. |
| BR-CLS-003 | **Dòng Theo ống mẫu.** Chi phí cho một kết quả = chi phí của dòng cho một ống mẫu ÷ số xét nghiệm bình quân trên một ống mẫu. |
| BR-CLS-004 | **Dòng Theo mẻ.** Chi phí cho một kết quả = chi phí của dòng cho một mẻ ÷ cỡ mẻ bình quân của kịch bản sản lượng. |
| BR-CLS-005 | **Dòng Theo ngày-máy và Theo kỳ.** Chi phí năm = chi phí của dòng cho một ngày × D (Theo ngày-máy), hoặc chi phí năm của dòng (Theo kỳ). Chi phí cho một kết quả = chi phí năm ÷ Qbn khi dòng gắn với hệ thống xét nghiệm; khi dòng gắn với thiết bị thì chia theo tiêu chí chia của thiết bị như BR-CLS-009. |
| BR-CLS-006 | **Vật liệu nội kiểm.** Chi phí cho một kết quả = lượng dùng mỗi lần × số mức × số lần mỗi ngày × D × đơn giá ÷ số thông số dùng chung vật liệu ÷ Qbn. Xem TBD-15. |
| BR-CLS-007 | **Chất chuẩn.** Chi phí cho một kết quả = chi phí chất chuẩn mỗi lần × số lần chuẩn năm ÷ Qbn. Hóa chất tiêu hao khi chuẩn máy đã nằm trong k và không cộng ở đây. |
| BR-CLS-008 | **Ngoại kiểm.** Tính ở cấp dịch vụ: chi phí cho một kết quả = (phí chương trình năm + phí vận chuyển năm) × tỷ lệ của dịch vụ ÷ tổng Qbn của các hệ thống xét nghiệm của dịch vụ. Tỷ lệ mặc định = 1 ÷ số dịch vụ tham gia chương trình. |
| BR-CLS-009 | **Chi phí thiết bị theo hình thức có máy và tiêu chí chia.** Chi phí máy năm: Mua = khấu hao năm theo BR-COST-004; Thuê và Liên doanh, liên kết = chi phí năm theo hợp đồng; Đặt theo hóa chất = 0. Chi phí thiết bị năm = (chi phí máy năm + bảo trì năm + linh kiện tính theo tháng của BR-CLS-010 + kiểm định, hiệu chuẩn năm của BR-CLS-011) × tỷ lệ phân bổ của thiết bị cho khoa. Chia cho một kết quả: tiêu chí Giờ kế hoạch theo BR-COST-004 (dùng chi phí thiết bị năm ở trên làm tử số); tiêu chí Số kết quả = chi phí thiết bị năm ÷ Qtb; tiêu chí Phút chiếm máy = chi phí thiết bị năm ÷ Mtb × m. |
| BR-CLS-010 | **Linh kiện lớn.** Tuổi thọ theo tháng: chi phí năm = giá thay thế × 12 ÷ tuổi thọ tháng, cộng vào chi phí thiết bị năm. Tuổi thọ theo số kết quả: chi phí cho một kết quả = giá thay thế ÷ tuổi thọ. Tuổi thọ theo giờ chạy: chi phí cho một kết quả = giá thay thế ÷ tuổi thọ giờ × m ÷ 60. Trong khi thiết bị có hình thức Đặt theo hóa chất, bảo trì và linh kiện được đánh dấu "nhà cung cấp chịu" bằng 0. |
| BR-CLS-011 | **Kiểm định, hiệu chuẩn.** Chi phí năm của một hồ sơ tuân thủ = chi phí mỗi lần × 12 ÷ chu kỳ tháng. Cách Gắn trực tiếp thiết bị: chi phí năm của thiết bị = tổng chi phí năm các hồ sơ còn hạn của chính thiết bị. Cách Theo giá trị tài sản: chi phí năm của thiết bị = tổng chi phí năm các hồ sơ của mọi thiết bị trong khoa × giá trị tài sản của thiết bị ÷ tổng giá trị tài sản các thiết bị của khoa. Giá trị tài sản là nguyên giá; thiết bị không có nguyên giá (thuê, đặt) dùng giá trị ghi trên hợp đồng, nếu không có thì thiết bị đó được tính theo cách Gắn trực tiếp. Áp dụng cho mọi thiết bị. |
| BR-CLS-012 | **Điện của thiết bị.** Chi phí điện một ngày = (công suất khi chạy × số giờ chạy + công suất khi chờ × số giờ chờ) × giá điện. D = 365 khi thiết bị cấp điện liên tục. Chi phí năm chia cho một kết quả theo tiêu chí chia của thiết bị như BR-CLS-009. Chỉ tính khi thiết bị có khai công suất; khi đó bộ định mức không khai thêm dòng tiện ích điện cho thiết bị này. |
| BR-CLS-013 | **Dịch vụ nhiều hệ thống xét nghiệm.** Chi phí trực tiếp của dịch vụ = Σ (tỷ trọng của hệ thống × chi phí trực tiếp của hệ thống), tổng tỷ trọng bằng 100%. Khi có số kết quả trả theo hệ thống: tỷ trọng = Qbn của hệ thống ÷ tổng Qbn của dịch vụ trong khoa. |
| BR-CLS-014 | **Đối soát vật chất.** Lượng tính được của một mặt hàng trong một khoa = Σ theo hệ thống (lượng áp dụng × k × Qbn với dòng nhân k; lượng áp dụng × Qbn với dòng Theo kết quả khác) + lượng của các dòng Theo ống mẫu, Theo mẻ, Theo ngày-máy, Theo kỳ quy về năm + lượng theo kế hoạch nội kiểm và chuẩn máy. Lượng xuất kho đổi về đơn vị định mức theo số đơn vị định mức trong một đơn vị mua. Chênh lệch phần trăm = (lượng xuất kho − lượng tính được) ÷ lượng xuất kho × 100. Dòng "Vượt ngưỡng" khi trị tuyệt đối của chênh lệch phần trăm lớn hơn ngưỡng đối soát vật chất. |
| BR-CLS-015 | **Đối soát sản lượng.** Chênh lệch phần trăm = (số kết quả trả − sản lượng dịch vụ từ HIS) ÷ sản lượng dịch vụ từ HIS × 100, theo dịch vụ và khoa. Dòng mang cảnh báo khi trị tuyệt đối lớn hơn ngưỡng đối soát sản lượng. |
| BR-CLS-016 | **Cảnh báo sản lượng thấp.** Số test tiêu thụ trong thời hạn dùng sau mở = (Qbn + Qnk + Qchuan + Qlai + Qngk) × hạn dùng sau mở (ngày) ÷ 365. Nếu số này nhỏ hơn số test danh nghĩa của một đơn vị mua của hóa chất chính, hệ thống gắn cảnh báo "Sản lượng thấp" để người dùng rà soát tỷ lệ hao hụt h. |
| BR-CLS-017 | **Quan hệ với BR-COST.** Chi phí tính theo BR-CLS-002 đến BR-CLS-012 là chi phí trực tiếp của dịch vụ và đi tiếp qua BR-COST-011 đến BR-COST-016 không đổi; "cấp 5" của bộ nháp phân hệ E bị bỏ, chi phí chung đi theo phân bổ cấp 1 và cấp 2. Loại chi phí kế toán của các khoản mới: hóa chất, vật tư, vật liệu nội kiểm, chất chuẩn → `DRUG_SUPPLY`; khấu hao, bảo trì, linh kiện, kiểm định, hiệu chuẩn → `DEPRECIATION`; điện → `UTILITY`. Phí ngoại kiểm, tiền thuê máy và chi phí hợp đồng liên doanh, liên kết tạm xếp `DRUG_SUPPLY`, `DEPRECIATION`, `DEPRECIATION` và cho NC Finance đổi trong bộ tham số; xem TBD-14. |

## Appendix A — Glossary

| Thuật ngữ | Nghĩa |
| :-- | :-- |
| QTKT | Quy trình kỹ thuật: tài liệu hướng dẫn thực hiện một dịch vụ kỹ thuật theo trình tự bước |
| Định mức KTKT | Định mức kinh tế - kỹ thuật: lượng nguồn lực cần để thực hiện một ca dịch vụ |
| Dịch vụ kỹ thuật | Một kỹ thuật trong danh mục kỹ thuật KCB, có mã và tên chuẩn |
| Cấu phần | Nhóm chi phí của một dòng định mức: Nhân lực, Thuốc và hóa chất, Vật tư, Thiết bị, Hạ tầng, Tiện ích |
| Lượng áp dụng | Lượng dùng để tính tiền sau khi áp BR-COST-007 |
| Trung tâm chi phí | Đơn vị gom chi phí kế toán, thường là khoa hoặc phòng; loại Lâm sàng (có dịch vụ) hoặc Hỗ trợ |
| Phân bổ cấp 1 | Đưa chi phí trung tâm hỗ trợ sang trung tâm lâm sàng |
| Phân bổ cấp 2 | Đưa chi phí chưa tính từ định mức của trung tâm lâm sàng xuống từng dịch vụ |
| Giá thành toàn bộ | Tổng chi phí trực tiếp và chi phí phân bổ của một ca dịch vụ |
| Giá tính toán | Giá thành toàn bộ cộng tích lũy và nghĩa vụ tài chính, trước khi làm tròn |
| Loại giá | Nhóm giá có cùng cấp phê duyệt và cùng cơ cấu chi phí được kết cấu |
| Giá tham chiếu | Giá cùng dịch vụ của đơn vị khác, dùng để so sánh |
| Kịch bản điều chỉnh | Bản sao của một lần tính giá với các thay đổi được chấp nhận |
| Mã bước | Mã bất biến của một bước quy trình qua các phiên bản |
| HIS | Phần mềm quản lý bệnh viện |
| As-Built | Tài liệu mô tả tính năng đúng như đã xây dựng |
| LIS, RIS | Phần mềm quản lý thông tin xét nghiệm; phần mềm quản lý thông tin chẩn đoán hình ảnh |
| Hệ thống xét nghiệm | Tổ hợp một dịch vụ cận lâm sàng, một khoa và một thiết bị chính, kèm bộ định mức và kế hoạch chất lượng riêng |
| Kết quả trả | Một kết quả xét nghiệm hoặc một ca chụp đã trả cho người bệnh; đơn vị tính giá của dịch vụ cận lâm sàng |
| Hệ số tiêu hao k | Tỷ số giữa số test thực dùng (gồm nội kiểm, chuẩn máy, chạy lại, ngoại kiểm, hao hụt) và số kết quả trả |
| Nội kiểm | Chạy mẫu kiểm tra chất lượng hằng ngày trong phòng xét nghiệm |
| Ngoại kiểm | Tham gia chương trình so sánh kết quả do đơn vị bên ngoài tổ chức |
| Chuẩn máy | Hiệu chuẩn phép đo bằng chất chuẩn trước khi chạy mẫu |
| Cấp phát sinh | Mức mà một khoản chi phí phát sinh: theo kết quả, theo ống mẫu, theo mẻ, theo ngày-máy, theo kỳ |
| Hình thức có máy | Cách bệnh viện có thiết bị: mua, thuê, đặt theo hóa chất, liên doanh liên kết |
| Máy đặt | Thiết bị do nhà cung cấp đặt tại bệnh viện kèm cam kết mua hóa chất; bệnh viện không tính khấu hao |
| Hồ sơ tuân thủ | Bản ghi một lần kiểm định, hiệu chuẩn, kiểm xạ hoặc cấp phép của thiết bị, có chu kỳ và chi phí |
| Kịch bản sản lượng | Bộ số sản lượng dùng cho một lần tính giá: thực tế 12 tháng, kế hoạch hoặc công suất |
| Đối soát vật chất | So lượng vật tư, hóa chất tính được từ định mức với lượng xuất kho thực tế |

## Appendix B — Open questions / TBD

| Mã | Câu hỏi | Ảnh hưởng | Người chốt |
| :-- | :-- | :-- | :-- |
| TBD-01 | Lấy mẫu biểu chính thức Phụ lục I đến V Thông tư 21/2024/TT-BYT và đối chiếu từng cột | FR-OUT-001..004, FR-BM-008, NFR-CPL-002 | BA nghiệp vụ |
| TBD-02 | Xác nhận cách tính tích lũy và nghĩa vụ tài chính theo Điều 6 và Điều 8 Thông tư 21 và thực tế của bệnh viện | BR-COST-013 | Tài chính kế toán |
| TBD-03 | Xây bảng ánh xạ tài khoản mặc định theo Thông tư 24/2024/TT-BTC sang 6 loại chi phí | FR-ACCT-009, BR-COST-008 | Tài chính kế toán |
| TBD-04 | Mẫu trình bày quy trình ban hành của bệnh viện thí điểm | FR-PROC-010 | Bệnh viện thí điểm |
| TBD-05 | Danh sách loại giá của bệnh viện công và cấp phê duyệt từng loại theo Luật KCB 2023 | FR-RES-015, FR-PRICE-006, FR-PRICE-007 | BA nghiệp vụ |
| TBD-06 | Bệnh viện và chuyên khoa thí điểm, số dịch vụ mẫu | Dữ liệu kiểm thử nghiệm thu | Chủ dự án |
| TBD-07 | Quy định thời gian sử dụng và tỷ lệ khấu hao tài sản tại đơn vị sự nghiệp công lập; lộ trình kết cấu khấu hao vào giá | BR-COST-004, FR-COST-007, FR-RES-007 | Tài chính kế toán |
| TBD-08 | Thời hạn lưu trữ hồ sơ giá và quy trình | Mục 3.4.4, NFR-SEC-006 | Chủ dự án |
| TBD-09 | Mức chất lượng nhận dạng ký tự chấp nhận được với văn bản quét | FR-LIB-004 | Đội phát triển |
| TBD-10 | Đơn giá đầu vào dùng giá gồm thuế GTGT trong mọi trường hợp hay có ngoại lệ | FR-RES-002, A-05 | Tài chính kế toán |
| TBD-11 | Nguồn chỉ số giá tiêu dùng và cách hiệu chỉnh theo khoản 3 Điều 5 Thông tư 21 | FR-BM-006, BR-ADJ-009 | BA nghiệp vụ |
| TBD-12 | Số ca bấm giờ tối thiểu và phương pháp khảo sát thời gian lao động được chấp nhận | FR-TS-003 | BA nghiệp vụ |
| TBD-13 | **Đã chốt ngày 13/11/2026.** Phân hệ E được hợp nhất vào SRS ở bản 1.1 và làm cùng bản phát hành 1 cho hóa sinh, miễn dịch (C-09, C-10, REF-09) | Đã xử lý ở bản 1.1; xem Revision History và Phụ lục C | Chủ dự án (đã chốt) |
| TBD-14 | Loại chi phí kế toán của phí ngoại kiểm, tiền thuê máy và chi phí hợp đồng liên doanh, liên kết; tiền thuê máy có được tính ở loại giá không kết cấu khấu hao hay không | BR-CLS-017, BR-COST-016, FR-RES-020 | Tài chính kế toán |
| TBD-15 | Vật liệu nội kiểm dùng chung cho nhiều thông số chia đều theo số thông số hay theo sản lượng của từng thông số | BR-CLS-006 | Khoa xét nghiệm thí điểm, BA nghiệp vụ |
| TBD-16 | LIS của bệnh viện thí điểm có xuất được số test nội kiểm, chuẩn máy, chạy lại theo dịch vụ và thiết bị hay không | FR-ACCT-013, FR-QC-006, độ chính xác của k | Bệnh viện thí điểm |
| TBD-17 | Dịch vụ bộ tính giá thành theo cả bộ hay theo từng thông số | FR-SVC-010 | BA nghiệp vụ |
| TBD-18 | Văn bản hiện hành về kiểm định, hiệu chuẩn phương tiện đo, an toàn bức xạ và quản lý chất lượng xét nghiệm (REF-10); danh sách loại thiết bị bắt buộc có hồ sơ tuân thủ | FR-CMP-006, FR-ADM-006, FR-QC-001..003 | BA nghiệp vụ |

## Appendix C — Tác động của bản 1.1 đến tài liệu khác

Bản 1.1 đổi yêu cầu mà các tài liệu dưới đây đã dựa vào. **Trạng thái ngày 13/11/2026: mọi việc trong bảng đã làm xong; tất cả các tài liệu dưới đây ở bản 1.1.** Bảng được giữ lại làm bản ghi về phạm vi tác động. Bộ sửa đổi đã dùng để gộp còn ở `docs/sua-doi-1.1/`, chỉ để đối chiếu. `docs/rtm.md` và `docs/verification-report.md` đã được sinh lại cho cả bộ bằng `docs/tools/build_rtm.py`. Bộ dữ liệu vàng cận lâm sàng là tệp riêng `docs/golden/golden_cls.py`; `docs/golden/golden_engine.py` không đổi.

| Tài liệu | Việc cần làm | Mã liên quan |
| :-- | :-- | :-- |
| `docs/use-cases.md` | Thêm use case cho: khai hệ thống xét nghiệm và kế hoạch chất lượng; quản lý hồ sơ tuân thủ; nhập sản lượng cận lâm sàng và xuất kho; đối soát vật chất. Sửa use case khai báo nguồn lực (UC-008) và chạy tính giá (UC-012) | FR-CLS, FR-QC, FR-CMP, FR-ACCT-012..015, FR-COST-017..032 |
| `docs/data-model.md` | Thêm và mở rộng DocType theo mục 4 của REF-09; sửa DI-03, DI-05; thêm NC Auditor vào ma trận quyền | FR-NORM-017, FR-ACC-002, FR-ACC-007 |
| `docs/architecture.md` | ADR mới cho mô hình cận lâm sàng trong bộ máy tính giá; sửa ADR-007 (thêm tài liệu của hãng vào danh sách cho phép); rà ADR-003 và ADR-004 | FR-AI-016, FR-COST-018..022, FR-COST-032 |
| `docs/ux-foundations.md`, `docs/design.md` | Màn hình mới: hệ thống xét nghiệm, kế hoạch chất lượng, hồ sơ tuân thủ, nhập sản lượng cận lâm sàng, đối soát vật chất; sửa form thiết bị, form lần tính giá, lưới định mức | FR-RES-019..026, FR-NORM-018, FR-NORM-019 |
| `docs/implementation-plan.md` | Mở rộng FEAT-009 (đơn giá), FEAT-010 (thiết bị), FEAT-011 (bộ tham số), FEAT-012, FEAT-015; thêm tính năng mới cho phân hệ E; cập nhật phạm vi bản phát hành 1 | Toàn bộ yêu cầu thêm ở 1.1 |
| `docs/test-cases.md`, `docs/golden/golden_engine.py` | Sửa test đã có của FR-RES-004, FR-RES-007, BR-COST-004; thêm nhóm test cho BR-CLS; đưa các vector kiểm thử của bộ nháp phân hệ E vào bộ dữ liệu vàng sau khi tính lại theo quy ước làm tròn của mục 3.4.1 | BR-CLS-001..017, NFR-REL-003 |
| `docs/rtm.md`, `docs/verification-report.md` | Sinh lại bằng `docs/tools/build_rtm.py` sau khi gộp. Truy vết của 76 yêu cầu chức năng mới, 2 yêu cầu phi chức năng mới và 9 yêu cầu sửa đã có ở `docs/sua-doi-1.1/rtm.md` | Toàn bộ |
