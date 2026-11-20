# Kịch bản kiểm thử nghiệm thu – Normcore Phân hệ E

> Phiên bản 1.0 · 13/11/2026 · Dạng Cho (Given) – Khi (When) – Thì (Then). Số liệu lấy từ bộ vector TV trong docs/calculation-rules.md; các số khác là giả định kiểm thử.
> Một tính năng đạt nghiệm thu khi mọi kịch bản gắn với FR của nó đạt và có As-Built.

## 1. Danh mục gốc

| ID | Kịch bản | Cho | Khi | Thì | Truy vết |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TS-01 | Tạo dịch vụ hợp lệ | Danh mục TT 23 và khoa đã nạp | Tạo dịch vụ đủ trường, thêm 1 mã LIS và 1 mã HIS | Lưu thành công; hai mã ngoài tra ngược ra đúng dịch vụ | FR-SVC-001, FR-SVC-003 |
| TS-02 | Mã TT 23 không tồn tại | Mã không có trong danh mục | Nhập mã đó cho dịch vụ | Báo lỗi, không lưu mã | FR-SVC-002 |
| TS-03 | Trùng dịch vụ | Đã có dịch vụ cùng mã TT 23 và cùng khoa, đang Hoạt động | Lưu dịch vụ thứ hai | Từ chối, chỉ ra bản ghi trùng | FR-SVC-005 |
| TS-04 | Ngừng dịch vụ đã dùng | Dịch vụ có kết quả trong lần tính Đã duyệt | Xóa dịch vụ; sau đó chuyển Ngừng | Xóa bị từ chối; Ngừng thành công; lần tính mới không còn dịch vụ; lịch sử còn nguyên | FR-SVC-006, FR-AUD-002 |
| TS-05 | Máy đặt | Thiết bị hình thức Đặt theo hóa chất, có dòng bảo trì do nhà cung cấp chịu | Chạy tính | K08 = 0; dòng bảo trì = 0 và không sửa được | FR-EQP-002, FR-EQP-003, KT-01, TV-08 |
| TS-06 | Thiếu dữ liệu khấu hao | Thiết bị Mua không có thời gian khấu hao | Chạy tính | Dịch vụ dùng thiết bị bị chặn, nêu trường thiếu | FR-EQP-006, KT-02 |
| TS-07 | Tổng phân bổ khác 100% | Thiết bị dùng chung khai 60% và 30% | Lưu | Từ chối lưu | FR-EQP-007, FR-EQP-008, KT-05 |
| TS-08 | Chọn giá theo ưu tiên | Mặt hàng có báo giá 28.000 còn hạn, trúng thầu 30.000 còn hạn, hợp đồng 29.000 hết hạn | Chạy tính | Dùng 30.000, ghi nguồn trúng thầu | FR-PRC-001, FR-PRC-002, FR-PRC-003, QT-01 |
| TS-09 | VAT đầu vào | Nguồn giá 100.000 chưa gồm VAT, thuế suất 5% | Tính với cấu hình gồm VAT; rồi tắt cấu hình | 105.000; rồi 100.000 | FR-PRC-007, QT-01 |
| TS-10 | Thiếu giá | Một mặt hàng trong phiếu không có nguồn giá còn hạn | Chạy tính rồi Trình hội đồng | Dòng mang nhãn thiếu giá; trình duyệt bị chặn; báo cáo thiếu dữ liệu liệt kê dịch vụ này | FR-PRC-004, FR-RPT-008, KT-03 |
| TS-11 | Xác minh không chứng từ | Nguồn giá không có tệp | Chuyển Đã xác minh | Từ chối | FR-PRC-005, KT-04 |
| TS-12 | Tổng tỷ trọng khác 100% | Dịch vụ có hai hệ thống 60% và 30% | Chạy tính | Dịch vụ bị chặn | FR-SYS-001, FR-SYS-002, FR-SYS-003, KT-06 |
| TS-13 | Hồ sơ tuân thủ hai cách | Cách A: dữ liệu TV-10. Cách B: khoa có hai máy nguyên giá 3,6 tỷ và 1,2 tỷ, tổng chi phí hồ sơ của khoa 14.000.000 | Chạy tính lần lượt hai cách | Cả hai cho 35 đồng mỗi kết quả ở máy A | FR-CMP-001, FR-CMP-002, FR-CMP-005, QT-10 |
| TS-14 | Nhắc hạn và thiếu hồ sơ | Hồ sơ kiểm định còn 20 ngày; một máy X-quang không có giấy phép còn hạn | Tác vụ nhắc hạn chạy; chạy tính | Cán bộ thiết bị nhận thông báo; lần tính có cảnh báo KT-14 và vẫn tính | FR-CMP-003, FR-CMP-004, FR-RPT-007 |
| TS-50 | Máy thuê | Thiết bị hình thức Thuê, tiền thuê 450.000.000 mỗi kỳ; Qtb 300.000; chia theo số kết quả | Chạy tính | K08 = 1.500, lấy từ tiền thuê, không tính khấu hao | FR-EQP-004, QT-08 |

## 2. Phiếu định mức

| ID | Kịch bản | Cho | Khi | Thì | Truy vết |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TS-15 | Tạo từ mẫu, thiếu khoản mục | Mẫu nhóm miễn dịch | Tạo phiếu từ mẫu, xóa dòng K05, gửi duyệt | Phiếu có đủ khoản mục bắt buộc lúc tạo; gửi duyệt bị chặn, liệt kê K05 | FR-NRM-001, FR-NRM-002, FR-NRM-003, KT-08 |
| TS-16 | Thanh toán riêng | Dòng K17 thuốc cản quang mang cờ Thanh toán riêng | Chạy tính và xuất bảng định mức | Dòng không vào giá thành; vẫn có trong bảng định mức | FR-NRM-004, KT-09 |
| TS-17 | Tiền phân tích | Vật tư ống mẫu 6.000; chưa khai số xét nghiệm mỗi ống | Gửi duyệt; khai 4 rồi chạy tính | Lần đầu bị chặn; sau đó K01 = 1.500 | FR-NRM-005, FR-NRM-006, KT-10, TV-12 |
| TS-18 | Chống trùng nội kiểm | Mặt hàng loại Hóa chất chính | Thêm vào dòng K05 | Từ chối lưu dòng | FR-NRM-009, KT-11 |
| TS-19 | Bấm giờ | Hai phiếu bấm giờ 1,4 và 1,6 phút mỗi mẫu; dữ liệu còn lại như TV-11 | Chạy tính; rồi vô hiệu cả hai phiếu và gửi duyệt phiếu mới | 1,5 phút mỗi mẫu, K11 = 4.600; sau đó gửi duyệt bị chặn | FR-LAB-001, FR-LAB-002, FR-LAB-003, FR-LAB-004, KT-07, TV-11 |
| TS-20 | Dòng AI | AI trả 5 dòng: 3 có nguồn, 1 không nguồn, 1 mặt hàng ngoài danh mục | Xem phiếu; chạy tính khi chưa xác nhận | 5 dòng Đề xuất, đúng hai nhãn; không tạo mặt hàng mới; không dòng nào vào phép tính; có nhật ký gọi AI | FR-AI-001, FR-AI-002, FR-AI-003, FR-AI-004, FR-AI-006, FR-AI-008, KT-12 |
| TS-21 | AI quá thời gian | Dịch vụ AI không phản hồi | Yêu cầu soạn dự thảo | Báo lỗi sau thời gian cấu hình; phiếu không đổi | FR-AI-007 |
| TS-22 | Luồng duyệt phiếu | Phiếu Nháp hợp lệ | Gửi khoa; trưởng khoa xác nhận từng dòng; kế toán duyệt | Qua đủ trạng thái; mỗi bước có người, thời điểm, ý kiến; trả lại không lý do bị từ chối | FR-APR-001, FR-APR-003, FR-APR-006, FR-NRM-007 |
| TS-23 | Phiên bản | Phiếu Đã duyệt | Sửa định lượng một dòng | Tạo phiên bản mới; bản cũ chỉ đọc; so sánh chỉ ra đúng dòng đổi | FR-NRM-008, FR-NRM-010 |

## 3. Tính giá thành

| ID | Kịch bản | Cho | Khi | Thì | Truy vết |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TS-24 | Hệ số k với số thực tế | Dữ liệu TV-01 | Chạy tính | k = 1,108247; K02 = 33.247,41 | FR-CST-002, FR-VOL-001, TV-01 |
| TS-25 | Sản lượng thấp | Dữ liệu TV-02; hạn dùng sau mở 30 ngày, hộp 200 test | Chạy tính | k = 1,618557; K02 = 48.556,71; có cảnh báo KT-16 | FR-VOL-004, KT-16, TV-02 |
| TS-26 | Ước tính từ kế hoạch | Không có số test nội kiểm, chuẩn, ngoại kiểm; kế hoạch: 2 mức, 1 lần mỗi ngày, 300 ngày; 12 lần chuẩn, 2 điểm, 2 lần lặp; 4 đợt ngoại kiểm, 3 mẫu mỗi đợt | Chạy tính | Qnk 600, Qchuan 48, Qngk 12; k như TV-01; nhãn Ước tính từ kế hoạch | FR-QC-005, QT-02 |
| TS-27 | Nội kiểm, chuẩn, ngoại kiểm | Dữ liệu TV-05, TV-06, TV-07 | Chạy tính | K05 = 60; K06 = 400; K07 = 125 | FR-QC-001, FR-QC-002, FR-QC-003, FR-QC-004, FR-CST-004 |
| TS-28 | Giá thành tổng hợp | Dữ liệu TV-16 | Chạy tính | Z = 46.303; NC 4.600; VT 36.394; DN 49; DT 760; KH 1.500; QL 3.000; mỗi dòng có nguồn giá và mã quy tắc; nhật ký AI không có lời gọi nào trong lúc tính | FR-CST-001, FR-CST-006, FR-CST-008, FR-CST-009, FR-CST-010, FR-EQP-001, FR-AI-005, TV-16 |
| TS-29 | Chia theo phút | Dữ liệu TV-14 | Chạy tính cho ca 10 phút và ca 20 phút | 202.222 và 404.444 | FR-SYS-005, FR-SYS-006, FR-EQP-005, FR-CST-005, TV-14 |
| TS-30 | Nhiều hệ thống | Dữ liệu TV-15 | Chạy tính | 42.400 | FR-SYS-004, TV-15 |
| TS-31 | Ba kịch bản | Có sản lượng Thực tế, Kế hoạch, Công suất | Chạy tính | Ba kết quả cho mỗi dịch vụ; đúng một kết quả đánh dấu chính | FR-CST-012, FR-VOL-002 |
| TS-32 | Lỗi và loại trừ | 3 dịch vụ: A hợp lệ, B thiếu cỡ mẻ cho dòng cấp 2, C không có sản lượng | Chạy tính | A Đạt; B Lỗi có thông báo; C Loại, nằm trong danh sách Không có sản lượng | FR-CST-003, FR-CST-013, FR-VOL-003, KT-15 |
| TS-33 | Tái lập | Lần tính đã chạy | Chạy lại từ ảnh chụp tham số sau khi đã đổi đơn giá hiện hành | Kết quả giống hệt lần đầu | FR-CST-007, NFR-REL-001 |
| TS-34 | Chạy nền | Phạm vi 25 dịch vụ | Chạy tính | Chạy nền; người chạy nhận thông báo khi xong; có thời lượng và số dịch vụ | FR-CST-014, NFR-OBS-001 |
| TS-35 | Hiệu năng | 500 dịch vụ, ba kịch bản, máy chủ 4 vCPU 8 GB | Chạy tính | Hoàn tất trong 10 phút | NFR-PERF-001 |
| TS-36 | Độ nhạy | Dịch vụ của TV-01 | Mở độ nhạy, đổi sản lượng thành 1.200 | Hiện K02 = 48.556,71 cạnh 33.247,41; lần tính không đổi | FR-CST-015 |

## 4. Đối soát, duyệt, hồ sơ

| ID | Kịch bản | Cho | Khi | Thì | Truy vết |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TS-37 | Đối soát vật chất vượt ngưỡng | Lượng tính được 13.298,964 test; xuất kho 14.000 test; ngưỡng 5% | Hoàn tất đối soát; rồi nhập giải trình | Lệch 5,0074%; bị chặn; sau giải trình thì qua | FR-REC-001, FR-REC-004, FR-REC-005, FR-VOL-005, KT-17 |
| TS-38 | Đối soát tài chính | Chi phí khoa thực tế theo cấu phần đã nạp | Chạy tính | Có bảng lệch theo sáu cấu phần | FR-REC-002, FR-VOL-006 |
| TS-39 | Thiếu số liệu đối soát | Kỳ không có số liệu xuất kho | Chạy tính; Trình hội đồng | Trạng thái Không đủ số liệu; chỉ trình được khi người duyệt xác nhận bỏ qua | FR-REC-006 |
| TS-40 | Duyệt lần tính | Lần tính Đã đối soát | Trình; duyệt không biên bản; duyệt có biên bản; sửa sau duyệt | Duyệt không biên bản bị từ chối; sau duyệt tham số bị khóa; mọi sửa đổi bị từ chối | FR-APR-002, FR-APR-004, FR-APR-005, FR-CST-011 |
| TS-41 | Vì sao giá này | Lần tính của TS-28 | Mở dịch vụ, mở cấu phần VT, mở dòng K02 | Thấy lượng 1, k 1,108247, đơn giá 30.000, quy tắc QT-03, nguồn giá và tệp chứng từ; tải trong 3 giây | FR-RPT-005, NFR-PERF-002 |
| TS-42 | Xuất hồ sơ | Lần tính Đã duyệt | Xuất bốn loại hồ sơ | Có bảng định mức (PDF, XLSX), bảng giá thành theo cấu phần, thuyết minh có tham số đã khóa và cảnh báo, phụ lục chứng từ đủ mọi nguồn giá đã dùng | FR-RPT-001, FR-RPT-002, FR-RPT-003, FR-RPT-004 |
| TS-43 | Chuyển sang Phân hệ C và API | Lần tính vừa duyệt | Phân hệ C đọc; hệ thống ngoài gọi API có quyền và không có quyền | Phân hệ C nhận giá thành theo cấu phần; API trả đúng với người có quyền, từ chối người không quyền | FR-INT-001, FR-INT-004 |
| TS-44 | Nguồn giá mới | Lần tính Đã duyệt dùng giá 30.000; xác minh nguồn mới 33.000 | Mở danh sách ảnh hưởng; tạo lần tính mới; so sánh | Liệt kê đúng dịch vụ dùng mặt hàng; so sánh quy chênh lệch về nguyên nhân đơn giá | FR-PRC-006, FR-RPT-006 |

## 5. Nhập liệu, phân quyền, truy vết

| ID | Kịch bản | Cho | Khi | Thì | Truy vết |
| :-- | :-- | :-- | :-- | :-- | :-- |
| TS-45 | Nhập tệp | Tệp sản lượng 100 dòng, 3 dòng sai mã ngoài | Nhập thử; nhập chính thức | Nhập thử không ghi gì, báo 3 lỗi theo dòng và cột; nhập chính thức ghi 97 dòng; có nhật ký | FR-IMP-001, FR-IMP-002, FR-IMP-003, FR-IMP-004, FR-IMP-005 |
| TS-46 | Giới hạn theo khoa | Người dùng khoa Xét nghiệm | Mở danh sách phiếu định mức; gọi phương thức lấy phiếu của khoa Chẩn đoán hình ảnh | Chỉ thấy khoa mình; lời gọi trực tiếp bị từ chối | FR-SEC-001, FR-SEC-002, NFR-SEC-001 |
| TS-47 | Che chi phí lương | Người dùng vai trò Trưởng khoa | Mở chi phí chức danh | Không thấy trường chi phí năm | FR-SEC-003 |
| TS-48 | Cấu hình | Người dùng vai trò Chuyên viên định giá | Sửa ngưỡng trong cấu hình | Bị từ chối; Quản trị sửa được | FR-SEC-004 |
| TS-49 | Nhật ký và chứng từ bất biến | Nguồn giá đã dùng trong lần tính Đã duyệt | Sửa đơn giá của một nguồn giá chưa dùng; thay tệp của nguồn giá đã dùng | Lần sửa có giá trị cũ, mới, người, thời điểm; thay tệp bị từ chối | FR-AUD-001, FR-AUD-003 |

## 6. Phạm vi chưa có kịch bản

Các yêu cầu mức C (FR-SVC-007, FR-EQP-009, FR-PRC-008, FR-VOL-008) và một số yêu cầu mức S (FR-SVC-004, FR-QC-006, FR-NRM-011, FR-VOL-007, FR-REC-003, FR-INT-002, FR-INT-003) chưa có kịch bản riêng; bổ sung khi các epic E7, E8 vào kế hoạch.
