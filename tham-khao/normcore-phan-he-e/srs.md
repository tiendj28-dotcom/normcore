# Đặc tả yêu cầu phần mềm (SRS): Normcore – Phân hệ E (Định mức KTKT khối cận lâm sàng)

> Phiên bản: 1.0 · Trạng thái: Draft (chờ rà soát nghiệp vụ) · Cập nhật: 13/11/2026
> Requirement syntax: EARS
> Trạng thái mọi yêu cầu: Active, trừ khi ghi khác ở cột Ghi chú. Ưu tiên: M = Must, S = Should, C = Could.

## Lịch sử sửa đổi

| Phiên bản | Ngày | Người soạn | Thay đổi |
| :-- | :-- | :-- | :-- |
| 1.0 | 13/11/2026 | BA (Claude soạn, chờ duyệt) | Bản đặc tả đầu tiên, dựng từ tài liệu ý tưởng Phân hệ E. |

## 1. Giới thiệu

### 1.1 Mục đích
Tài liệu đặc tả đầy đủ yêu cầu của Phân hệ E thuộc ứng dụng Normcore (Frappe v15). Người đọc: dev IT, kiến trúc sư, kiểm thử, chủ sản phẩm. Đây là nguồn chuẩn cho các bước kiến trúc, UX, lập kế hoạch và thiết kế chi tiết.

### 1.2 Tầm nhìn và phạm vi
**Vấn đề.** Bệnh viện phải có định mức KTKT để lập giá dịch vụ theo phương pháp chi phí của Thông tư 21/2024/TT-BYT. Với dịch vụ cận lâm sàng (CLS), giá thành do máy, hóa chất và hệ thống chất lượng quyết định; nhiều chi phí phát sinh theo mẻ, theo ngày, theo năm chứ không theo từng người bệnh. Bảng tính tay thường tính thiếu (nội kiểm, ngoại kiểm, chạy lại, kiểm định) hoặc tính trùng (máy đặt vẫn tính khấu hao).

**Tầm nhìn.** Mỗi con số trong giá thành 1 kết quả CLS truy được về một dòng định mức, một đơn giá có chứng từ, một số liệu sản lượng và một công thức cố định.

**Trong phạm vi.**
- Danh mục gốc: dịch vụ CLS, thiết bị, mặt hàng, nguồn giá, hệ thống xét nghiệm, kế hoạch nội kiểm và chuẩn máy, chương trình ngoại kiểm, hồ sơ tuân thủ thiết bị, chi phí nhân lực, bấm giờ.
- Phiếu định mức CLS có AI hỗ trợ soạn dự thảo và luồng duyệt.
- Sản lượng kỳ, số liệu xuất kho và chi phí khoa để đối soát.
- Bộ máy tính giá thành, ba phép đối soát, luồng trình duyệt và khóa tham số.
- Báo cáo, hồ sơ xuất, truy vết “vì sao giá này”, nhập liệu hàng loạt.
- Nhóm dịch vụ: xét nghiệm (hóa sinh, miễn dịch, huyết học, vi sinh, sinh học phân tử, giải phẫu bệnh), chẩn đoán hình ảnh (X-quang, CT, MRI, siêu âm), nội soi chẩn đoán, thăm dò chức năng.

**Ngoài phạm vi.**
- Cộng tích lũy, nghĩa vụ tài chính và ban hành giá dịch vụ (Phân hệ C).
- So sánh giá với đơn vị khác (Phân hệ D).
- Soạn và duyệt quy trình kỹ thuật (Phân hệ A).
- Quản lý kho, mua sắm, tài sản, kế toán (hệ thống khác); Phân hệ E chỉ nhận số liệu.
- Kết nối trực tiếp máy xét nghiệm.

**Ranh giới bản đầu (MVP).** Xét nghiệm hóa sinh và miễn dịch, nhập liệu bằng tệp, toàn bộ yêu cầu mức M. Mô hình dữ liệu hỗ trợ chẩn đoán hình ảnh ngay từ đầu.

### 1.3 Mục tiêu và thước đo thành công

| Mã | Mục tiêu | Thước đo |
| :-- | :-- | :-- |
| G1 | Tính đúng | Kết quả phần mềm khớp 100% bộ vector kiểm thử TV-01..TV-16 (docs/calculation-rules.md). |
| G2 | Tính đủ | Đối soát tài chính của khoa thí điểm lệch không quá 5% so với sổ kế toán. |
| G3 | Giải trình được | 100% dòng chi phí trong lần tính đã duyệt có nguồn giá kèm chứng từ. |
| G4 | Nhanh hơn bảng tính | Lập xong định mức 50 dịch vụ trong 10 ngày làm việc với 1 chuyên viên định giá. |
| G5 | Tái lập | Chạy lại lần tính với cùng ảnh chụp tham số cho kết quả giống hệt. |

### 1.4 Định nghĩa
Xem Phụ lục A.

### 1.5 Tài liệu tham chiếu
- Tài liệu ý tưởng “Normcore – Phân hệ E: Định mức KTKT và giá thành 1 test khối cận lâm sàng” (13/11/2026).
- Thông tư 21/2024/TT-BYT (phương pháp định giá dịch vụ KCB) và Phụ lục III, IV.
- Thông tư 23/2024/TT-BYT (danh mục kỹ thuật).
- Thông tư 10/2026/TT-BYT (tiêu chuẩn, định mức sử dụng máy móc, thiết bị chuyên dùng y tế).
- docs/use-cases.md, docs/data-model.md, docs/calculation-rules.md, docs/test-scenarios.md, docs/implementation-plan.md, docs/rtm.md.

## 2. Mô tả tổng quan

### 2.1 Bối cảnh sản phẩm
Phân hệ E là một module trong app Normcore, cùng site Frappe với các phân hệ A–D. Tác nhân và hệ thống ngoài:

| Bên ngoài | Quan hệ với Phân hệ E |
| :-- | :-- |
| Phân hệ A (QTKT) | Cung cấp quy trình kỹ thuật đã duyệt làm đầu vào định mức. |
| Phân hệ C (giá thành và giá) | Cung cấp hệ số phân bổ cấp 5; nhận giá thành đã duyệt. |
| Phân hệ D (so sánh) | Đọc giá thành đã duyệt. |
| LIS, RIS/PACS, HIS | Nguồn sản lượng; bản đầu qua tệp, sau qua API. |
| Kho, kế toán | Nguồn xuất kho thực tế và chi phí khoa; qua tệp. |
| ERPNext (tùy chọn) | Liên kết Item, Supplier, Asset khi cùng site. |
| Dịch vụ AI | Soạn dự thảo định mức từ tài liệu. |

### 2.2 Chức năng chính
18 nhóm chức năng, đặc tả ở mục 3.1: SVC, EQP, SYS, PRC, QC, CMP, LAB, NRM, AI, VOL, CST, REC, APR, RPT, IMP, SEC, AUD, INT.

### 2.3 Nhóm người dùng

| Vai trò (Role trên Frappe) | Là ai | Nhu cầu chính |
| :-- | :-- | :-- |
| NC Pricing Officer – Chuyên viên định giá | Phòng Tài chính kế toán hoặc Kế hoạch tổng hợp | Dựng định mức, chạy tính, đối soát, lập hồ sơ. Người dùng chính. |
| NC Department User – Nhân viên khoa | Kỹ thuật viên khoa xét nghiệm, chẩn đoán hình ảnh | Khai định mức, bấm giờ, kế hoạch chất lượng của khoa mình. |
| NC Department Head – Trưởng khoa | Trưởng khoa CLS | Xác nhận định mức của khoa. |
| NC Equipment Officer – Cán bộ thiết bị | Phòng Vật tư thiết bị y tế | Hồ sơ thiết bị, kiểm định, hiệu chuẩn, bảo trì. |
| NC Accountant – Kế toán | Phòng Tài chính kế toán | Nguồn giá, chi phí nhân lực, chi phí khoa, thẩm định. |
| NC Approver – Người duyệt | Hội đồng, lãnh đạo bệnh viện | Duyệt lần tính, khóa tham số. |
| NC Auditor – Kiểm soát | Kiểm toán nội bộ, thanh tra | Chỉ đọc, truy vết. |
| NC Administrator – Quản trị | IT | Cấu hình, phân quyền, nhập liệu. |

Người dùng thao tác trên máy tính bàn trong giờ hành chính; trưởng khoa và người duyệt có thể dùng điện thoại để xem và duyệt.

### 2.4 Môi trường vận hành
Frappe Framework v15, MariaDB, máy chủ Linux của bệnh viện hoặc đám mây trong nước; truy cập qua trình duyệt.

### 2.5 Ràng buộc
- C1. Xây trên Frappe v15, không sửa lõi; fieldname tiếng Anh, label tiếng Việt.
- C2. Kết quả xuất phải theo cấu phần chi phí của Thông tư 21/2024/TT-BYT.
- C3. Phép tính giá thành do mã xác định thực hiện; AI chỉ đề xuất dữ liệu đầu vào.
- C4. Không lưu, không gửi dữ liệu định danh người bệnh.
- C5. Mọi tính năng nghiệm thu phải có Definition of Done và tài liệu As-Built.

### 2.6 Giả định và phụ thuộc
- A1. Normcore chạy độc lập trên Frappe; liên kết ERPNext là tùy chọn.
- A2. Phân hệ E giữ danh mục mặt hàng và thiết bị riêng (CLS Item, CLS Equipment).
- A3. Kịch bản sản lượng mặc định là thực tế 12 tháng; hội đồng đổi được khi khóa tham số.
- A4. VAT đầu vào tính vào chi phí theo mặc định, cấu hình được.
- A5. Bản đầu nhập sản lượng, xuất kho, chi phí khoa bằng tệp XLSX.
- A6. Khi Phân hệ C chưa sẵn sàng, hệ số phân bổ cấp 5 nhập tay trong Phân hệ E.
- A7. Bệnh viện cung cấp được số test nội kiểm, chuẩn máy, chạy lại; nếu không, hệ thống ước tính từ kế hoạch chất lượng.

## 3. Yêu cầu cụ thể

### 3.1 Yêu cầu chức năng

#### 3.1.1 SVC – Danh mục dịch vụ CLS

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-SVC-001 | Hồ sơ dịch vụ | Hệ thống phải lưu mỗi dịch vụ CLS với mã nội bộ duy nhất, tên, nhóm chuyên ngành, khoa thực hiện và đơn vị kết quả. | M | Nhóm chuyên ngành: xem Phụ lục A. |
| FR-SVC-002 | Kiểm tra mã TT 23 | Khi người dùng nhập mã kỹ thuật theo TT 23/2024/TT-BYT cho một dịch vụ, hệ thống phải kiểm tra mã đó có trong danh mục kỹ thuật đã nạp. | M | Danh mục TT 23 nạp bằng tệp. |
| FR-SVC-003 | Ánh xạ mã ngoài | Hệ thống phải cho ánh xạ một dịch vụ CLS với một hoặc nhiều mã của HIS, LIS, RIS. | M | Dùng khi nhập sản lượng. |
| FR-SVC-004 | Dịch vụ bộ | Ở nơi dịch vụ được đánh dấu là dịch vụ bộ, hệ thống phải lưu danh sách thông số thành phần và cách tính giá thành theo cả bộ hoặc theo từng thông số. | S | Ví dụ tổng phân tích máu, điện giải đồ. |
| FR-SVC-005 | Chặn trùng | Nếu người dùng lưu dịch vụ có mã nội bộ trùng, hoặc cùng mã TT 23 và cùng khoa với một dịch vụ đang hoạt động, thì hệ thống phải từ chối và chỉ ra bản ghi trùng. | M | |
| FR-SVC-006 | Ngừng dùng | Khi người dùng ngừng sử dụng một dịch vụ, hệ thống phải giữ bản ghi cùng lịch sử giá thành và loại dịch vụ khỏi các lần tính mới. | M | Không xóa. |
| FR-SVC-007 | Gửi ngoài | Ở nơi dịch vụ được đánh dấu gửi ngoài, hệ thống phải loại dịch vụ khỏi tính định mức và lưu giá hợp đồng gửi mẫu. | C | |

#### 3.1.2 EQP – Thiết bị và hình thức có máy

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-EQP-001 | Hồ sơ thiết bị | Hệ thống phải lưu hồ sơ thiết bị gồm mã, tên, model, hãng, số seri, khoa, nguyên giá, ngày đưa vào sử dụng, thời gian khấu hao, công suất thiết kế, công suất điện khi chạy và khi chờ. | M | |
| FR-EQP-002 | Hình thức có máy | Hệ thống phải ghi nhận hình thức có máy của mỗi thiết bị là Mua, Thuê, Đặt theo hóa chất hoặc Liên doanh liên kết. | M | |
| FR-EQP-003 | Máy đặt | Trong khi hình thức có máy là Đặt theo hóa chất, hệ thống phải đặt khấu hao bằng 0 và khóa các dòng chi phí được đánh dấu do nhà cung cấp chịu. | M | QT-08, KT-01. |
| FR-EQP-004 | Máy thuê | Trong khi hình thức có máy là Thuê, hệ thống phải dùng tiền thuê của kỳ thay cho khấu hao. | M | QT-08. |
| FR-EQP-005 | Linh kiện lớn | Hệ thống phải cho khai linh kiện lớn của thiết bị với giá thay thế và tuổi thọ tính theo tháng, số ca hoặc số giờ. | M | Bóng phát tia, heli, đầu dò, điện cực. QT-09. |
| FR-EQP-006 | Thiếu dữ liệu khấu hao | Nếu thiết bị hình thức Mua thiếu nguyên giá, ngày đưa vào sử dụng hoặc thời gian khấu hao, thì hệ thống phải chặn đưa thiết bị vào lần tính và nêu trường thiếu. | M | KT-02. |
| FR-EQP-007 | Thiết bị dùng chung | Hệ thống phải cho khai tỷ lệ phân bổ một thiết bị dùng chung cho nhiều khoa. | M | Ly tâm, tủ lạnh, tủ an toàn sinh học. |
| FR-EQP-008 | Tổng tỷ lệ 100% | Nếu tổng tỷ lệ phân bổ của một thiết bị khác 100%, thì hệ thống phải từ chối lưu. | M | KT-05. |
| FR-EQP-009 | Liên kết Asset | Ở nơi ERPNext được cài cùng site, hệ thống phải cho liên kết thiết bị với bản ghi Asset và lấy nguyên giá, ngày sử dụng từ đó. | C | |

#### 3.1.3 SYS – Hệ thống xét nghiệm

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-SYS-001 | Hồ sơ hệ thống | Hệ thống phải lưu mỗi hệ thống xét nghiệm là tổ hợp gồm một dịch vụ, một thiết bị chính, một phiếu định mức và một kế hoạch chất lượng. | M | Đơn vị tính của phân hệ. |
| FR-SYS-002 | Nhiều hệ thống | Hệ thống phải cho một dịch vụ có nhiều hệ thống xét nghiệm, mỗi hệ thống mang một tỷ trọng sản lượng. | M | |
| FR-SYS-003 | Tổng tỷ trọng | Nếu tổng tỷ trọng các hệ thống xét nghiệm đang hoạt động của một dịch vụ khác 100%, thì hệ thống phải chặn đưa dịch vụ vào lần tính. | M | KT-06. |
| FR-SYS-004 | Bình quân gia quyền | Khi tính giá thành một dịch vụ có nhiều hệ thống xét nghiệm, hệ thống phải tính từng hệ thống rồi lấy bình quân gia quyền theo tỷ trọng. | M | QT-14. |
| FR-SYS-005 | Phút chiếm máy | Hệ thống phải lưu số phút chiếm máy của mỗi dịch vụ trên thiết bị chính. | M | Bắt buộc với chẩn đoán hình ảnh. |
| FR-SYS-006 | Tiêu chí chia máy | Hệ thống phải cho chọn tiêu chí chia chi phí của từng thiết bị theo số kết quả hoặc theo phút chiếm máy. | M | QT-08. |

#### 3.1.4 PRC – Mặt hàng và nguồn giá

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-PRC-001 | Hồ sơ mặt hàng | Hệ thống phải lưu mỗi mặt hàng với mã, tên, loại, đơn vị tính, quy cách, số test danh nghĩa mỗi hộp và hạn dùng sau mở. | M | Loại: hóa chất chính, hóa chất phụ trợ, chất chuẩn, vật liệu nội kiểm, vật tư, linh kiện. |
| FR-PRC-002 | Nhiều nguồn giá | Hệ thống phải lưu nhiều nguồn giá cho một mặt hàng, mỗi nguồn gồm loại nguồn, đơn giá, thuế suất VAT, ngày hiệu lực từ và đến, số chứng từ và tệp đính kèm. | M | Loại nguồn: trúng thầu, hợp đồng, hóa đơn, báo giá. |
| FR-PRC-003 | Chọn giá | Khi tính giá thành, hệ thống phải chọn đơn giá của mỗi mặt hàng theo thứ tự ưu tiên loại nguồn đã cấu hình, trong các nguồn còn hiệu lực tại ngày tính. | M | QT-01. |
| FR-PRC-004 | Thiếu giá | Nếu một mặt hàng trong phiếu định mức không có nguồn giá còn hiệu lực tại ngày tính, thì hệ thống phải đánh dấu dòng là thiếu giá và chặn trình duyệt lần tính. | M | KT-03. |
| FR-PRC-005 | Xác minh chứng từ | Nếu nguồn giá không có tệp chứng từ đính kèm, thì hệ thống phải từ chối chuyển nguồn giá sang trạng thái Đã xác minh. | M | KT-04. |
| FR-PRC-006 | Giá mới có hiệu lực | Khi một nguồn giá mới được xác minh, hệ thống phải liệt kê các dịch vụ bị ảnh hưởng và chênh lệch giá thành ước tính so với lần tính đã duyệt gần nhất. | S | UC-13. |
| FR-PRC-007 | VAT đầu vào | Hệ thống phải tính đơn giá đầu vào gồm VAT hoặc không gồm VAT theo cấu hình của đơn vị. | M | Mặc định gồm VAT. QT-01. |
| FR-PRC-008 | Liên kết Item | Ở nơi ERPNext được cài cùng site, hệ thống phải cho liên kết mặt hàng với Item và nhà cung cấp với Supplier. | C | |

#### 3.1.5 QC – Nội kiểm, chuẩn máy, ngoại kiểm

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-QC-001 | Kế hoạch nội kiểm | Hệ thống phải lưu kế hoạch nội kiểm của mỗi hệ thống xét nghiệm gồm vật liệu, số mức, số lần mỗi ngày, lượng dùng mỗi lần, số ngày chạy mỗi năm và số thông số dùng chung vật liệu. | M | QT-05. |
| FR-QC-002 | Kế hoạch chuẩn máy | Hệ thống phải lưu kế hoạch chuẩn máy gồm chất chuẩn, số điểm chuẩn, số lần lặp, số lần chuẩn mỗi năm và chi phí chất chuẩn mỗi lần. | M | QT-06. |
| FR-QC-003 | Chương trình ngoại kiểm | Hệ thống phải lưu chương trình ngoại kiểm gồm đơn vị triển khai, các dịch vụ tham gia, số đợt mỗi năm, số mẫu mỗi đợt, phí chương trình và phí vận chuyển. | M | QT-07. |
| FR-QC-004 | Chia phí ngoại kiểm | Khi tính giá thành, hệ thống phải chia phí ngoại kiểm đều cho các dịch vụ tham gia, trừ khi người dùng đã khai tỷ lệ riêng. | M | QT-07. |
| FR-QC-005 | Ước tính từ kế hoạch | Khi sản lượng kỳ không có số test nội kiểm hoặc chuẩn máy thực tế, hệ thống phải suy ra từ kế hoạch chất lượng và gắn nhãn Ước tính từ kế hoạch. | M | QT-02. |
| FR-QC-006 | Thiếu kế hoạch | Nếu một hệ thống xét nghiệm thuộc nhóm xét nghiệm không có kế hoạch nội kiểm, thì hệ thống phải cảnh báo trên phiếu định mức. | S | KT-13, cảnh báo. |

#### 3.1.6 CMP – Hồ sơ tuân thủ thiết bị

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-CMP-001 | Hồ sơ tuân thủ | Hệ thống phải lưu hồ sơ tuân thủ của thiết bị gồm loại, chu kỳ tháng, đơn vị thực hiện, chi phí mỗi lần, ngày thực hiện, ngày hết hạn và chứng từ. | M | Loại: kiểm định, hiệu chuẩn, kiểm xạ, giấy phép bức xạ, bảo trì, liều kế, khác. |
| FR-CMP-002 | Quy về năm | Khi tính giá thành, hệ thống phải quy chi phí mỗi hồ sơ tuân thủ về chi phí năm theo chu kỳ. | M | QT-10. |
| FR-CMP-003 | Nhắc hạn | Khi một hồ sơ tuân thủ còn không quá số ngày cấu hình đến ngày hết hạn, hệ thống phải gửi thông báo cho cán bộ thiết bị. | S | Mặc định 30 ngày. |
| FR-CMP-004 | Thiếu hồ sơ | Nếu thiết bị thuộc loại bắt buộc có hồ sơ tuân thủ mà không có hồ sơ còn hạn, thì hệ thống phải cảnh báo trên lần tính. | M | KT-14, cảnh báo. |
| FR-CMP-005 | Hai cách phân bổ | Hệ thống phải cho chọn ở mỗi lần tính cách phân bổ chi phí kiểm định, hiệu chuẩn: gắn trực tiếp thiết bị hoặc theo tổng giá trị tài sản. | M | QT-10. Theo Phụ lục III TT 21. |

#### 3.1.7 LAB – Nhân lực và bấm giờ

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-LAB-001 | Chi phí chức danh | Hệ thống phải lưu chi phí năm và số giờ làm việc chuẩn mỗi năm của từng chức danh để tính đơn giá phút. | M | QT-11. |
| FR-LAB-002 | Phiếu bấm giờ | Hệ thống phải lưu phiếu bấm giờ gồm dịch vụ, công đoạn, chức danh, số phút mỗi mẫu, số phút mỗi mẻ, người đo và ngày đo. | M | Công đoạn: tiền phân tích, phân tích, hậu phân tích. |
| FR-LAB-003 | Trung bình lần đo | Khi một công đoạn của một dịch vụ có nhiều phiếu bấm giờ còn hiệu lực, hệ thống phải dùng trung bình cộng các lần đo. | M | QT-11. |
| FR-LAB-004 | Chưa bấm giờ | Nếu dòng nhân lực của phiếu định mức không có phiếu bấm giờ, thì hệ thống phải chặn gửi duyệt phiếu. | M | KT-07. |

#### 3.1.8 NRM – Phiếu định mức CLS

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-NRM-001 | Phiếu và dòng | Hệ thống phải lưu phiếu định mức của mỗi hệ thống xét nghiệm với các dòng gồm khoản mục, mặt hàng hoặc nguồn lực, cấp phát sinh, định lượng, đơn vị tính và nguồn chứng cứ. | M | Cấp 1–5, Phụ lục A. |
| FR-NRM-002 | Tạo từ mẫu | Khi người dùng tạo phiếu từ mẫu định mức của nhóm chuyên ngành, hệ thống phải chép các khoản mục bắt buộc của nhóm vào phiếu. | M | |
| FR-NRM-003 | Thiếu khoản mục | Nếu phiếu thiếu khoản mục bắt buộc của nhóm, thì hệ thống phải chặn gửi duyệt và liệt kê khoản mục thiếu. | M | KT-08. |
| FR-NRM-004 | Thanh toán riêng | Trong khi một dòng mang cờ Thanh toán riêng, hệ thống phải loại dòng khỏi giá thành và vẫn hiển thị dòng trong hồ sơ. | M | KT-09. |
| FR-NRM-005 | Số xét nghiệm mỗi ống | Hệ thống phải lưu số xét nghiệm bình quân trên một ống mẫu để chia chi phí tiền phân tích. | M | QT-12. |
| FR-NRM-006 | Thiếu số xét nghiệm mỗi ống | Nếu phiếu có dòng tiền phân tích mà chưa khai số xét nghiệm bình quân trên một ống, thì hệ thống phải chặn gửi duyệt. | M | KT-10. |
| FR-NRM-007 | Xác nhận từng dòng | Hệ thống phải ghi trạng thái xác nhận của từng dòng là Đề xuất, Đã xác nhận hoặc Từ chối, cùng người và thời điểm xác nhận. | M | |
| FR-NRM-008 | Phiên bản | Khi người dùng sửa một phiếu đã duyệt, hệ thống phải tạo phiên bản mới và giữ phiên bản cũ ở chế độ chỉ đọc. | M | Dùng cơ chế amend của Frappe. |
| FR-NRM-009 | Chống trùng nội kiểm | Nếu dòng thuộc khoản mục vật liệu nội kiểm chứa mặt hàng loại hóa chất chính, thì hệ thống phải từ chối lưu dòng. | M | KT-11. |
| FR-NRM-010 | So sánh phiên bản | Khi người dùng chọn hai phiên bản của một phiếu, hệ thống phải hiển thị các dòng thêm, bớt và thay đổi. | S | |
| FR-NRM-011 | Sao chép phiếu | Khi người dùng sao chép phiếu sang hệ thống xét nghiệm khác, hệ thống phải tạo phiếu nháp với mọi dòng ở trạng thái Đề xuất. | S | |

#### 3.1.9 AI – Đề xuất định mức

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-AI-001 | Soạn dự thảo | Khi người dùng yêu cầu AI soạn định mức cho một phiếu, hệ thống phải tạo các dòng dự thảo từ tài liệu hãng, quy trình kỹ thuật đã duyệt và kế hoạch chất lượng đính kèm phiếu. | S | |
| FR-AI-002 | Dẫn nguồn | Khi AI tạo một dòng dự thảo, hệ thống phải ghi tên tài liệu và số trang làm nguồn của dòng. | S | |
| FR-AI-003 | Không có nguồn | Nếu AI không chỉ ra được nguồn cho một dòng, thì hệ thống phải gắn nhãn Không có nguồn cho dòng đó. | S | |
| FR-AI-004 | Chờ xác nhận | Trong khi một dòng do AI tạo ở trạng thái Đề xuất, hệ thống phải loại dòng khỏi mọi phép tính. | M | KT-12. |
| FR-AI-005 | Không dùng AI để tính | Hệ thống phải thực hiện mọi phép tính giá thành bằng mã xác định, không gọi mô hình AI. | M | Ràng buộc C3. |
| FR-AI-006 | Chỉ dùng danh mục | Nếu AI đề xuất mặt hàng không có trong danh mục mặt hàng, thì hệ thống phải gắn nhãn Chưa ánh xạ và không tạo mặt hàng mới. | S | |
| FR-AI-007 | AI lỗi | Nếu dịch vụ AI không phản hồi trong thời gian cấu hình, thì hệ thống phải báo lỗi và giữ nguyên phiếu để nhập tay. | S | Mặc định 120 giây. |
| FR-AI-008 | Nhật ký AI | Khi hệ thống gọi AI, hệ thống phải ghi người gọi, tài liệu đầu vào, phiên bản mô hình, thời điểm và số dòng trả về. | S | |

#### 3.1.10 VOL – Sản lượng và số liệu đối soát

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-VOL-001 | Sản lượng kỳ | Hệ thống phải lưu sản lượng theo hệ thống xét nghiệm và kỳ gồm số kết quả trả, số test nội kiểm, chuẩn máy, chạy lại, ngoại kiểm, tỷ lệ hao hụt, số ca và tổng phút khai thác. | M | QT-02. |
| FR-VOL-002 | Ba kịch bản | Hệ thống phải lưu sản lượng theo ba kịch bản: thực tế 12 tháng, kế hoạch và công suất. | M | |
| FR-VOL-003 | Không có sản lượng | Nếu số kết quả trả của một hệ thống xét nghiệm trong kịch bản chính bằng 0 hoặc để trống, thì hệ thống phải loại hệ thống đó khỏi lần tính và liệt kê trong danh sách Không có sản lượng. | M | KT-15. |
| FR-VOL-004 | Sản lượng thấp | Nếu sản lượng trong thời hạn dùng sau mở của hóa chất chính nhỏ hơn số test danh nghĩa của một hộp, thì hệ thống phải cảnh báo Sản lượng thấp. | S | KT-16, cảnh báo. |
| FR-VOL-005 | Xuất kho thực tế | Hệ thống phải lưu lượng xuất kho thực tế theo mặt hàng, khoa và kỳ. | M | Đối soát vật chất. |
| FR-VOL-006 | Chi phí khoa | Hệ thống phải lưu chi phí thực tế của khoa theo cấu phần chi phí và kỳ. | M | Đối soát tài chính. |
| FR-VOL-007 | Số dịch vụ HIS | Hệ thống phải lưu số dịch vụ đã ghi nhận trên HIS theo dịch vụ và kỳ. | S | Đối soát sản lượng. |
| FR-VOL-008 | Đồng bộ API | Ở nơi kết nối LIS hoặc RIS được bật, hệ thống phải nhận sản lượng kỳ qua API và ghi nguồn là Tự động. | C | Sau bản đầu. |

#### 3.1.11 CST – Tính giá thành

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-CST-001 | Chạy lần tính | Khi người dùng chạy một lần tính cho một kỳ và một phạm vi dịch vụ, hệ thống phải tính giá thành 1 kết quả của từng dịch vụ theo các quy tắc QT-01 đến QT-15. | M | docs/calculation-rules.md. |
| FR-CST-002 | Hệ số tiêu hao | Khi tính chi phí cấp 1, hệ thống phải nhân định mức với hệ số tiêu hao thực tế k của hệ thống xét nghiệm. | M | QT-02, QT-03. |
| FR-CST-003 | Chi phí theo mẻ | Khi tính chi phí cấp 2, hệ thống phải chia chi phí một mẻ cho số mẫu bình quân một mẻ. | M | QT-04. |
| FR-CST-004 | Chi phí theo ngày | Khi tính chi phí cấp 3, hệ thống phải nhân chi phí ngày với số ngày chạy rồi chia cho sản lượng của thiết bị hoặc hệ thống trong kỳ. | M | QT-05. |
| FR-CST-005 | Chi phí theo kỳ | Khi tính chi phí cấp 4, hệ thống phải chia chi phí kỳ của thiết bị hoặc thông số theo tiêu chí chia của thiết bị đó. | M | QT-06..QT-10. |
| FR-CST-006 | Chi phí cấp 5 | Khi tính chi phí cấp 5, hệ thống phải áp hệ số phân bổ nhận từ Phân hệ C hoặc nhập tay. | M | QT-13. |
| FR-CST-007 | Ảnh chụp tham số | Khi một lần tính chạy xong, hệ thống phải lưu ảnh chụp toàn bộ định mức, đơn giá, sản lượng và cấu hình đã dùng. | M | NFR-REL-001. |
| FR-CST-008 | Kết quả theo dòng | Khi một lần tính chạy xong, hệ thống phải lưu kết quả từng dòng gồm khoản mục, cấp, lượng, đơn giá, thành tiền cho 1 kết quả, nguồn giá và quy tắc đã áp dụng. | M | |
| FR-CST-009 | Tổng hợp theo TT 21 | Khi một lần tính chạy xong, hệ thống phải tổng hợp giá thành của mỗi dịch vụ theo các cấu phần chi phí của TT 21/2024/TT-BYT. | M | Phụ lục A, cấu phần. |
| FR-CST-010 | Làm tròn | Hệ thống phải giữ sáu chữ số thập phân trong phép tính trung gian và làm tròn đến đồng ở giá thành cuối của dịch vụ. | M | QT-15. |
| FR-CST-011 | Khóa sau duyệt | Trong khi lần tính ở trạng thái Đã duyệt, hệ thống phải từ chối mọi thay đổi vào lần tính đó. | M | Tính lại tạo lần mới. |
| FR-CST-012 | Ba kịch bản | Khi chạy một lần tính, hệ thống phải tính giá thành cho cả ba kịch bản sản lượng và đánh dấu kịch bản chính. | M | |
| FR-CST-013 | Lỗi từng dịch vụ | Nếu phép tính của một dịch vụ gặp lỗi, thì hệ thống phải ghi lỗi cho dịch vụ đó và tiếp tục tính các dịch vụ còn lại. | M | |
| FR-CST-014 | Chạy nền | Khi lần tính có hơn 20 dịch vụ, hệ thống phải chạy ở chế độ nền và thông báo cho người chạy khi hoàn tất. | M | |
| FR-CST-015 | Độ nhạy | Khi người dùng mở phân tích độ nhạy của một dịch vụ, hệ thống phải tính lại giá thành theo sản lượng, đơn giá hoặc hình thức có máy giả định mà không ghi vào lần tính. | S | UC-14. |

#### 3.1.12 REC – Đối soát

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-REC-001 | Đối soát vật chất | Khi lần tính chạy xong, hệ thống phải so lượng tiêu hao tính được của từng mặt hàng với lượng xuất kho thực tế của khoa trong kỳ và tính tỷ lệ lệch. | M | QT-16. |
| FR-REC-002 | Đối soát tài chính | Khi lần tính chạy xong, hệ thống phải so tổng chi phí tính được của khoa theo từng cấu phần với chi phí thực tế của khoa trong kỳ. | M | QT-16. |
| FR-REC-003 | Đối soát sản lượng | Khi lần tính chạy xong, hệ thống phải so số kết quả trả với số dịch vụ ghi nhận trên HIS của từng dịch vụ. | S | QT-16. |
| FR-REC-004 | Vượt ngưỡng | Nếu tỷ lệ lệch của một dòng đối soát vượt ngưỡng cấu hình, thì hệ thống phải yêu cầu giải trình bằng văn bản cho dòng đó trước khi cho trình duyệt. | M | KT-17. Mặc định 5%, 5%, 2%. |
| FR-REC-005 | Lưu giải trình | Khi người dùng nhập giải trình cho một dòng đối soát, hệ thống phải lưu nội dung, người viết, thời điểm và tệp đính kèm. | M | |
| FR-REC-006 | Thiếu số liệu đối soát | Nếu kỳ tính không có số liệu xuất kho hoặc chi phí khoa, thì hệ thống phải ghi trạng thái đối soát là Không đủ số liệu và yêu cầu người duyệt xác nhận bỏ qua. | M | |

#### 3.1.13 APR – Luồng duyệt và khóa tham số

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-APR-001 | Luồng phiếu định mức | Hệ thống phải đưa phiếu định mức qua các trạng thái Nháp, Chờ khoa xác nhận, Chờ thẩm định, Đã duyệt và Từ chối. | M | Frappe Workflow. |
| FR-APR-002 | Luồng lần tính | Hệ thống phải đưa lần tính qua các trạng thái Nháp, Đã tính, Đã đối soát, Trình hội đồng, Đã duyệt và Trả lại. | M | Frappe Workflow. |
| FR-APR-003 | Ghi vết chuyển trạng thái | Khi một phiếu định mức hoặc lần tính chuyển trạng thái, hệ thống phải ghi người thực hiện, thời điểm và ý kiến. | M | |
| FR-APR-004 | Chặn trình duyệt | Nếu lần tính còn vi phạm quy tắc kiểm tra mức Chặn, thì hệ thống phải từ chối chuyển sang Trình hội đồng và liệt kê vi phạm. | M | KT mức Chặn. |
| FR-APR-005 | Khóa tham số | Khi người duyệt duyệt lần tính, hệ thống phải khóa kịch bản sản lượng chính, tiêu chí chia máy, cách phân bổ kiểm định hiệu chuẩn, ngưỡng đối soát và yêu cầu đính kèm biên bản. | M | |
| FR-APR-006 | Trả lại có lý do | Nếu người duyệt trả lại hoặc từ chối mà không nhập lý do, thì hệ thống phải từ chối thao tác. | M | |

#### 3.1.14 RPT – Báo cáo và hồ sơ

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-RPT-001 | Bảng định mức | Khi người dùng xuất bảng định mức KTKT của một dịch vụ trong lần tính, hệ thống phải tạo tệp PDF và XLSX liệt kê mọi dòng định mức, đơn giá và thành tiền. | M | |
| FR-RPT-002 | Bảng giá thành | Khi người dùng xuất bảng giá thành của lần tính, hệ thống phải tạo tệp liệt kê giá thành từng dịch vụ theo cấu phần chi phí TT 21. | M | |
| FR-RPT-003 | Thuyết minh | Khi người dùng xuất thuyết minh của lần tính, hệ thống phải nêu tham số đã khóa, sản lượng, tiêu chí phân bổ và các cảnh báo còn mở. | M | |
| FR-RPT-004 | Phụ lục chứng từ | Khi người dùng xuất phụ lục chứng từ của lần tính, hệ thống phải liệt kê mọi nguồn giá đã dùng với số chứng từ và tệp đính kèm. | M | |
| FR-RPT-005 | Vì sao giá này | Khi người dùng mở giá thành của một dịch vụ, hệ thống phải cho truy xuống từng dòng chi phí, công thức, số liệu đầu vào và chứng từ. | M | UC-12. |
| FR-RPT-006 | So sánh hai lần tính | Khi người dùng chọn hai lần tính, hệ thống phải hiển thị chênh lệch giá thành từng dịch vụ tách theo nguyên nhân: đơn giá, định mức, sản lượng. | S | |
| FR-RPT-007 | Hạn hồ sơ tuân thủ | Hệ thống phải cung cấp báo cáo hồ sơ tuân thủ sắp hết hạn và đã hết hạn theo khoa. | S | |
| FR-RPT-008 | Thiếu dữ liệu | Hệ thống phải cung cấp báo cáo các dịch vụ thiếu dữ liệu để tính: thiếu giá, thiếu sản lượng, thiếu bấm giờ, thiếu hồ sơ. | M | |

#### 3.1.15 IMP – Nhập liệu hàng loạt

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-IMP-001 | Mẫu nhập | Hệ thống phải cung cấp mẫu XLSX cho dịch vụ, thiết bị, mặt hàng, nguồn giá, sản lượng kỳ, xuất kho thực tế, chi phí khoa và danh mục kỹ thuật TT 23. | M | |
| FR-IMP-002 | Kiểm tra theo dòng | Khi người dùng nhập tệp, hệ thống phải kiểm tra từng dòng và báo lỗi theo số dòng và tên cột. | M | |
| FR-IMP-003 | Không ghi dòng lỗi | Nếu một dòng của tệp nhập không hợp lệ, thì hệ thống phải bỏ dòng đó và vẫn ghi các dòng hợp lệ. | M | |
| FR-IMP-004 | Nhập thử | Khi người dùng chọn chế độ nhập thử, hệ thống phải trả kết quả kiểm tra mà không ghi dữ liệu. | S | |
| FR-IMP-005 | Nhật ký nhập | Khi một lần nhập kết thúc, hệ thống phải lưu tệp, người nhập, thời điểm, số dòng thành công và số dòng lỗi. | M | |

#### 3.1.16 SEC – Phân quyền

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-SEC-001 | Quyền theo vai trò | Hệ thống phải cấp quyền đọc, tạo, sửa, duyệt theo ma trận vai trò ở docs/data-model.md mục 4. | M | |
| FR-SEC-002 | Giới hạn theo khoa | Trong khi người dùng chỉ có vai trò của khoa, hệ thống phải chỉ cho người đó thấy dữ liệu của khoa được gán. | M | User Permission theo khoa. |
| FR-SEC-003 | Che chi phí lương | Hệ thống phải chỉ cho vai trò Kế toán, Chuyên viên định giá và Quản trị xem chi phí năm của chức danh. | M | Permission level. |
| FR-SEC-004 | Cấu hình | Hệ thống phải chỉ cho vai trò Quản trị sửa ngưỡng, thứ tự ưu tiên nguồn giá và bật tắt quy tắc kiểm tra. | M | |

#### 3.1.17 AUD – Nhật ký và truy vết

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-AUD-001 | Nhật ký thay đổi | Khi một trường của danh mục gốc, phiếu định mức hoặc nguồn giá thay đổi, hệ thống phải ghi giá trị cũ, giá trị mới, người sửa và thời điểm. | M | Track Changes. |
| FR-AUD-002 | Không xóa dữ liệu đã dùng | Nếu người dùng xóa một bản ghi đã tham gia lần tính đã duyệt, thì hệ thống phải từ chối và đề nghị ngừng sử dụng. | M | |
| FR-AUD-003 | Chứng từ bất biến | Trong khi một nguồn giá đã được dùng trong lần tính đã duyệt, hệ thống phải từ chối thay tệp chứng từ của nguồn giá đó. | M | Sửa bằng nguồn giá mới. |

#### 3.1.18 INT – Tích hợp với các phân hệ khác

| ID | Tên ngắn | Yêu cầu | ƯT | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| FR-INT-001 | Chuyển sang Phân hệ C | Khi lần tính được duyệt, hệ thống phải cung cấp cho Phân hệ C giá thành từng dịch vụ theo cấu phần chi phí. | M | |
| FR-INT-002 | Nhận hệ số phân bổ | Khi Phân hệ C công bố hệ số phân bổ của kỳ, hệ thống phải dùng hệ số đó cho chi phí cấp 5 của các lần tính mới. | S | A6: nhập tay khi chưa có. |
| FR-INT-003 | QTKT đổi phiên bản | Khi quy trình kỹ thuật liên kết với một dịch vụ có phiên bản mới được duyệt, hệ thống phải gắn nhãn Cần rà soát cho phiếu định mức của dịch vụ. | S | |
| FR-INT-004 | API chỉ đọc | Hệ thống phải cung cấp API chỉ đọc trả giá thành đã duyệt theo dịch vụ và kỳ cho người gọi có quyền. | S | Phân hệ D và hệ thống ngoài. |

### 3.2 Yêu cầu giao diện ngoài

**Giao diện người dùng.** Dùng Desk của Frappe: form, list, report, workspace riêng “Định mức CLS”. Màn hình cần thiết kế riêng: bảng điều khiển lần tính, bảng đối soát, “vì sao giá này”, so sánh phiên bản phiếu, phân tích độ nhạy. Nhãn tiếng Việt.

**Giao diện phần cứng.** Không có.

**Giao diện phần mềm.**

| Mã | Đối tác | Hướng | Nội dung | Hình thức |
| :-- | :-- | :-- | :-- | :-- |
| IF-01 | LIS, RIS | Vào | Sản lượng kỳ theo mã dịch vụ ngoài | Tệp XLSX; API REST sau bản đầu |
| IF-02 | Kho | Vào | Xuất kho thực tế theo mặt hàng, khoa, kỳ | Tệp XLSX |
| IF-03 | Kế toán | Vào | Chi phí khoa theo cấu phần, kỳ | Tệp XLSX |
| IF-04 | HIS | Vào | Số dịch vụ ghi nhận theo kỳ | Tệp XLSX |
| IF-05 | Phân hệ C | Ra, vào | Giá thành theo cấu phần; hệ số phân bổ | Gọi nội bộ trong site |
| IF-06 | Phân hệ A | Vào | Quy trình kỹ thuật đã duyệt, sự kiện đổi phiên bản | Gọi nội bộ trong site |
| IF-07 | Dịch vụ AI | Ra, vào | Tài liệu kỹ thuật; dòng định mức dự thảo | HTTPS API |
| IF-08 | Hệ thống ngoài | Ra | Giá thành đã duyệt | REST API chỉ đọc |

**Giao diện truyền thông.** HTTPS; thông báo qua Notification và email của Frappe.

### 3.3 Yêu cầu phi chức năng

| ID | Nhóm | Yêu cầu (thước đo, mục tiêu, điều kiện) | ƯT |
| :-- | :-- | :-- | :-- |
| NFR-PERF-001 | Hiệu năng | Lần tính 500 dịch vụ với ba kịch bản hoàn tất trong 10 phút trên máy chủ 4 vCPU, 8 GB RAM. | M |
| NFR-PERF-002 | Hiệu năng | Màn hình “vì sao giá này” của một dịch vụ có không quá 60 dòng tải trong 3 giây ở phân vị 95. | M |
| NFR-PERF-003 | Hiệu năng | Nhập tệp 10.000 dòng hoàn tất trong 5 phút. | S |
| NFR-CAP-001 | Dung lượng | Hỗ trợ 3.000 dịch vụ, 500 thiết bị, 20.000 mặt hàng, 50.000 nguồn giá và giữ kết quả các lần tính trong 10 năm. | M |
| NFR-REL-001 | Tin cậy | Chạy lại lần tính với cùng ảnh chụp tham số cho giá thành giống hệt đến từng đồng. | M |
| NFR-REL-002 | Tin cậy | Kết quả của bộ vector kiểm thử TV-01..TV-16 khớp giá trị kỳ vọng, sai số 0 đồng ở kết quả cuối. | M |
| NFR-REL-003 | Tin cậy | Sao lưu hằng ngày; RPO không quá 24 giờ, RTO không quá 8 giờ. | M |
| NFR-SEC-001 | Bảo mật | Mọi phương thức whitelisted kiểm tra quyền theo Role và User Permission; kiểm thử phân quyền không còn phương thức nào trả dữ liệu ngoài quyền. | M |
| NFR-SEC-002 | Bảo mật | Mọi kết nối dùng HTTPS với TLS 1.2 trở lên. | M |
| NFR-SEC-003 | Bảo mật | Dữ liệu gửi dịch vụ AI chỉ gồm tài liệu kỹ thuật và danh mục; không có trường định danh người bệnh, không có chi phí lương. | M |
| NFR-SEC-004 | Bảo mật | Nhật ký thay đổi và nhật ký duyệt giữ tối thiểu 10 năm và không sửa, xóa được qua giao diện. | M |
| NFR-USA-001 | Dễ dùng | 100% nhãn, thông báo lỗi và biểu xuất bằng tiếng Việt. | M |
| NFR-USA-002 | Dễ dùng | Trưởng khoa xác nhận xong một phiếu 40 dòng trong 15 phút, đo với 3 người dùng thật. | S |
| NFR-COM-001 | Tương thích | Chạy trên Frappe v15, MariaDB 10.6 trở lên, Python 3.10 trở lên; hỗ trợ hai phiên bản mới nhất của Chrome và Edge. | M |
| NFR-COM-002 | Tương thích | Cài và gỡ app không cần sửa lõi Frappe hay ERPNext; chạy được khi không có ERPNext. | M |
| NFR-MNT-001 | Bảo trì | Bộ máy tính có kiểm thử đơn vị phủ ít nhất 90% dòng lệnh; mỗi quy tắc QT và KT có ít nhất một ca kiểm thử. | M |
| NFR-MNT-002 | Bảo trì | Quy tắc kiểm tra bật, tắt và đổi mức Chặn hoặc Cảnh báo bằng cấu hình, không sửa mã. | S |
| NFR-LEG-001 | Tuân thủ | Cấu trúc cấu phần chi phí của biểu xuất là dữ liệu cấu hình, đổi được khi văn bản thay thế TT 21 có hiệu lực mà không sửa mã. | S |
| NFR-LOC-001 | Bản địa hóa | Tiền tệ VND, định dạng số và ngày theo Việt Nam, múi giờ Asia/Ho_Chi_Minh. | M |
| NFR-OBS-001 | Vận hành | Mỗi lần tính ghi thời lượng, số dịch vụ, số lỗi; tác vụ nền thất bại gửi thông báo cho Quản trị trong 5 phút. | S |

### 3.4 Yêu cầu khác
- Lưu trữ: không xóa cứng dữ liệu đã tham gia lần tính đã duyệt (FR-AUD-002).
- Tài liệu: mỗi epic bàn giao kèm As-Built theo mẫu ở docs/implementation-plan.md.

## Phụ lục A – Thuật ngữ

| Thuật ngữ | Nghĩa |
| :-- | :-- |
| CLS | Cận lâm sàng: xét nghiệm, chẩn đoán hình ảnh, nội soi chẩn đoán, thăm dò chức năng. |
| Kết quả trả | Một kết quả xét nghiệm hoặc một ca chẩn đoán hình ảnh trả cho người bệnh. Đơn vị tính giá thành. |
| Test danh nghĩa | Số test ghi trên hộp hóa chất. |
| Hệ số tiêu hao k | Số test danh nghĩa phải tiêu để có 1 kết quả trả (QT-02). |
| Hệ thống xét nghiệm | Tổ hợp dịch vụ, thiết bị chính, phiếu định mức và kế hoạch chất lượng. Dùng cho cả chẩn đoán hình ảnh. |
| Cấp phát sinh | 1 theo test; 2 theo mẻ; 3 theo ngày-máy; 4 theo kỳ gắn thiết bị hoặc thông số; 5 theo khoa và toàn viện. |
| Nội kiểm | Kiểm tra chất lượng nội bộ bằng vật liệu kiểm chứng, chạy theo ngày. |
| Ngoại kiểm | Chương trình đánh giá chất lượng từ bên ngoài, tham gia theo năm. |
| Chuẩn máy | Hiệu chuẩn phép đo bằng chất chuẩn, theo lô hóa chất hoặc định kỳ. |
| Hồ sơ tuân thủ | Kiểm định, hiệu chuẩn, kiểm xạ, giấy phép bức xạ, bảo trì của thiết bị. |
| Máy đặt | Thiết bị do nhà cung cấp hóa chất đặt tại bệnh viện; chi phí máy nằm trong giá hóa chất. |
| Phút chiếm máy | Thời gian thiết bị bị một dịch vụ chiếm dụng, tính bằng phút. |
| Lần tính | Một lần chạy bộ máy tính cho một kỳ và một phạm vi, có ảnh chụp tham số. |
| Cấu phần chi phí | Nhân công; thuốc, hóa chất, vật tư; điện, nước và hậu cần; duy tu, bảo dưỡng, kiểm định, hiệu chuẩn; khấu hao; quản lý. |
| Nhóm chuyên ngành | Hóa sinh, miễn dịch, huyết học, vi sinh, sinh học phân tử, giải phẫu bệnh, X-quang, CT, MRI, siêu âm, nội soi, thăm dò chức năng. |

## Phụ lục B – Câu hỏi mở

| Mã | Câu hỏi | Giả định đang dùng | Ảnh hưởng nếu đổi |
| :-- | :-- | :-- | :-- |
| OQ-01 | Kịch bản sản lượng chính là thực tế 12 tháng, kế hoạch hay công suất? | Thực tế 12 tháng (A3) | Chỉ đổi cấu hình mặc định. |
| OQ-02 | Bệnh viện thí điểm dùng máy mua hay máy đặt là chính? | Hỗ trợ cả bốn hình thức | Thứ tự ưu tiên kiểm thử. |
| OQ-03 | LIS có xuất được số test nội kiểm, chuẩn máy, chạy lại không? | Không chắc; có đường ước tính (FR-QC-005) | Độ chính xác của k. |
| OQ-04 | Dịch vụ bộ tính theo cả bộ hay theo thông số? | Cho chọn theo dịch vụ (FR-SVC-004) | Không. |
| OQ-05 | Kiểm định, hiệu chuẩn gắn trực tiếp thiết bị hay phân bổ theo giá trị tài sản? | Cho chọn theo lần tính (FR-CMP-005) | Không. |
| OQ-06 | Normcore chạy cùng site ERPNext hay độc lập? | Độc lập, liên kết tùy chọn (A1, A2) | Mô hình dữ liệu mặt hàng, thiết bị. |
| OQ-07 | Khách hàng đầu là bệnh viện công hay tư? | Cả hai; chế độ khấu hao là dữ liệu nhập | Mẫu biểu, nguồn chi phí nhân lực. |
| OQ-08 | Dịch vụ AI dùng API đám mây hay tự host? | Chưa chốt; đặc tả theo giao diện IF-07 | NFR-SEC-003, hạ tầng. |
| OQ-09 | Ngưỡng đối soát 5%, 5%, 2% có phù hợp? | Mặc định, cấu hình được | Không. |
| OQ-10 | Các văn bản về kiểm định, hiệu chuẩn, an toàn bức xạ, khấu hao hiện hành là gì? | Chưa tra; không mã hóa cứng trong hệ thống | Danh sách loại thiết bị bắt buộc có hồ sơ. |
