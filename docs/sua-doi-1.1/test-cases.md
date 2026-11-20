# Sửa đổi 1.1 — Test case (bổ sung cho `docs/test-cases.md` 1.0)

> Phiên bản 1.1-delta · 13/11/2026 · Nguồn: `docs/srs.md` 1.1, `docs/sua-doi-1.1/golden_cls.py`
> Thêm 51 test case, mã TC-CLS-01 đến TC-CLS-51. Toàn bộ test của bản sửa đổi dùng chung nhóm mã CLS để không trùng số với các nhóm của bản 1.0. Loại: **U** đơn vị tự động; **I** tích hợp tự động trên site; **M** kiểm tay khi nghiệm thu.

## 1. Test case 1.0 phải rà lại

| Yêu cầu sửa | Việc cần làm với test case 1.0 có cột FR chứa yêu cầu này |
| :-- | :-- |
| FR-RES-004 | Đổi kết quả mong đợi: chọn theo thứ tự nguồn trước, rồi đến ngày hiệu lực. Ca cũ "hai đơn giá, lấy bản mới nhất" vẫn đúng khi hai đơn giá cùng loại nguồn |
| FR-RES-005 | Thêm ca cho trường bắt buộc theo hình thức có máy và tiêu chí chia |
| FR-RES-007 | Kết quả cũ (khấu hao bằng 0) là trường hợp bộ tham số chọn ZERO; thêm ca CONTINUE (TC-CLS-11) |
| FR-RES-009 | Thêm ba tham số mới vào dữ liệu kiểm |
| FR-ACC-002, FR-ACC-004, FR-AUD-003 | Thêm NC Auditor vào ma trận kiểm quyền (TC-CLS-44) |
| BR-COST-004 (TC-COST-01, TC-COST-06) | Kết quả của bộ dữ liệu vàng 1.0 không đổi: EQ1 là thiết bị duy nhất của K01 và không có hồ sơ tuân thủ. Giữ nguyên |

## 2. Bộ dữ liệu vàng cho khối cận lâm sàng

Mọi số liệu ở mục này là **số thử nghiệm**. Kết quả mong đợi do `docs/sua-doi-1.1/golden_cls.py` tính; phần cận lâm sàng của bộ máy tính giá phải ra đúng các số này: thành tiền đến 2 chữ số thập phân, hệ số k đến 6 chữ số. Phạm vi: chi phí trực tiếp một kết quả; phân bổ và làm tròn giá dùng bộ dữ liệu vàng 1.0.

### 2.1 Đầu vào

**Tham số:** giá điện 3.000 đồng/kWh; ngày tính giá 31/12/2026; khấu hao thiết bị hết thời gian sử dụng: ZERO; ngưỡng đối soát vật chất 5%, sản lượng 2%; đơn giá giờ công kỹ thuật viên 59.644,8864 (chức danh DD của bộ dữ liệu vàng 1.0); cách phân bổ kiểm định: Theo giá trị tài sản.

**Mặt hàng**

| Mã | Vai trò | Giá đơn vị mua | Đơn vị định mức mỗi đơn vị mua | Đơn giá một đơn vị định mức |
| :-- | :-- | --: | --: | --: |
| HC_GLU | Hóa chất chính; 200 test danh nghĩa; hạn dùng sau mở 30 ngày | 6.000.000 | 200 | 30.000 |
| ONG | Ống lấy mẫu | 6.000 | 1 | 6.000 |
| CUVET | Vật tư tiêu hao theo test | 1.200 | 1 | 1.200 |
| DD_RUA | Dung dịch rửa, dùng theo mẻ | 50.000 | 1 | 50.000 |
| HC_PT | Hóa chất phụ trợ, dùng theo ngày-máy | 120.000 | 1 | 120.000 |
| QC_L | Vật liệu nội kiểm, lọ 5 mL | 900.000 | 5 | 180.000 |

**Thiết bị**

| Mã | Khoa | Hình thức | Dữ liệu | Tiêu chí chia |
| :-- | :-- | :-- | :-- | :-- |
| EQ_A | XN | Mua | Nguyên giá 3.600.000.000; 10 năm; đưa vào sử dụng 01/01/2022; bảo trì 120.000.000; linh kiện Đèn 24.000.000 mỗi 12 tháng; linh kiện Điện cực 9.000.000 mỗi 30.000 kết quả; điện 2 kW × 8 giờ chạy, 0,5 kW × 16 giờ chờ, cấp điện liên tục; hồ sơ hiệu chuẩn 8.000.000 mỗi 12 tháng | Số kết quả; Qtb 300.000 |
| EQ_B | XN | Đặt theo hóa chất | Giá trị hợp đồng 1.200.000.000; bảo trì 40.000.000 do nhà cung cấp chịu; hồ sơ hiệu chuẩn 6.000.000 mỗi 12 tháng | Số kết quả; Qtb 100.000 |
| EQ_C | K3 | Thuê | Chi phí hợp đồng 450.000.000 mỗi năm | Số kết quả; Qtb 300.000 |
| EQ_CT | CDHA | Mua | Nguyên giá 28.000.000.000; 8 năm; đưa vào sử dụng 01/01/2024; bảo trì 140.000.000 | Phút chiếm máy; Mtb 180.000 |

**Hệ thống xét nghiệm của dịch vụ GLU, khoa XN**

| Mã | Thiết bị | Qbn | Số test phụ | Khác |
| :-- | :-- | --: | :-- | :-- |
| GLU-A | EQ_A | 12.000 | Thực tế: nội kiểm 600, chuẩn máy 48, chạy lại 240, ngoại kiểm 12; hao hụt 3% | 300 ngày chạy; cỡ mẻ 40; 4 xét nghiệm mỗi ống |
| GLU-B | EQ_B | 4.000 | Không có số thực tế; tỷ lệ chạy lại ước tính 2%, hao hụt ước tính 3% | Như trên |

**Kế hoạch chất lượng (dùng cho cả hai hệ thống):** nội kiểm QC_L, 2 mức, 1 lần mỗi ngày, 0,2 mL mỗi lần, 20 thông số dùng chung; chuẩn máy 2 điểm × 2 lần lặp, 12 lần mỗi năm, 400.000 mỗi lần. **Ngoại kiểm:** phí 24.000.000, vận chuyển 1.200.000, 3 đợt × 4 mẫu, 21 dịch vụ tham gia, chia đều.

**Bộ định mức (giống nhau cho hai hệ thống)**

| Dòng | Cấp phát sinh | Cấu phần | Nguồn lực | Lượng | Nhân k | Gắn với |
| :-- | :-- | :-- | :-- | --: | :-: | :-- |
| L01 | Theo ống mẫu | SUPPLY | ONG | 1 | | |
| L02 | Theo kết quả | DRUG | HC_GLU | 1 | Có | |
| L03 | Theo kết quả | SUPPLY | CUVET | 1 | Có | |
| L04 | Theo mẻ | DRUG | DD_RUA | 1 | | |
| L05 | Theo ngày-máy | DRUG | HC_PT | 1 | | Thiết bị |
| L06 | Theo kết quả | LABOR | Kỹ thuật viên | 1,5 phút | | |
| L07 | Theo kết quả | EQUIPMENT | Thiết bị chính | | | |

### 2.2 Kết quả mong đợi

**Hệ số k:** GLU-A: tổng 12.900 test, k = 1,108247. GLU-B: nội kiểm 600, chuẩn máy 48, chạy lại 80, ngoại kiểm 12, tổng 4.740 test, k = 1,221649, nhãn "Ước tính từ kế hoạch".

**Thiết bị, cách Theo giá trị tài sản:** EQ_A: khấu hao 360.000.000; kiểm định 10.500.000; chi phí thiết bị năm 514.500.000. EQ_B: khấu hao 0; bảo trì 0; kiểm định 3.500.000; chi phí thiết bị năm 3.500.000.

**Chi phí trực tiếp một kết quả**

| Dòng | Quy tắc | GLU-A | GLU-B |
| :-- | :-- | --: | --: |
| L01 ống mẫu | BR-CLS-003 | 1.500,00 | 1.500,00 |
| L02 hóa chất chính | BR-CLS-002 | 33.247,41 | 36.649,47 |
| L03 vật tư theo test | BR-CLS-002 | 1.329,90 | 1.465,98 |
| L04 dung dịch rửa | BR-CLS-004 | 1.250,00 | 1.250,00 |
| L05 hóa chất phụ trợ | BR-CLS-005 | 120,00 | 360,00 |
| L06 nhân lực | BR-COST-002 | 1.491,12 | 1.491,12 |
| L07 thiết bị | BR-CLS-009 | 1.715,00 | 35,00 |
| Linh kiện theo số kết quả | BR-CLS-010 | 300,00 | 0,00 |
| Điện của thiết bị | BR-CLS-012 | 87,60 | 0,00 |
| Vật liệu nội kiểm | BR-CLS-006 | 90,00 | 270,00 |
| Chất chuẩn | BR-CLS-007 | 400,00 | 1.200,00 |
| **Cộng** | | **41.531,03** | **44.221,57** |

**Dịch vụ GLU:** tỷ trọng 75% và 25% (từ Qbn); bình quân gia quyền 42.203,67; ngoại kiểm 75,00; chi phí trực tiếp của dịch vụ 42.278,67.

**Biến thể**

| Mã | Thay đổi | Kết quả |
| :-- | :-- | :-- |
| V1 | Cách phân bổ Gắn trực tiếp thiết bị | Kiểm định EQ_A 8.000.000, thiết bị 1.706,67 mỗi kết quả; EQ_B 6.000.000, 60,00 mỗi kết quả; dịch vụ GLU 42.278,67 |
| V2 | Ngày tính giá 01/01/2033 (EQ_A hết thời gian sử dụng) | ZERO: thiết bị 515,00; CONTINUE: 1.715,00 |
| V3 | EQ_C máy thuê | 1.500,00 mỗi kết quả |
| V4 | EQ_CT chia theo phút | Chi phí năm 3.640.000.000; đơn giá phút 20.222,2222; ca 10 phút 202.222,22; ca 20 phút 404.444,44 |
| V5 | Loại giá không kết cấu khấu hao | EQ_A 515,00; EQ_C 1.500,00 (tiền thuê vẫn tính, chờ TBD-14) |
| V6 | Đối soát vật chất HC_GLU của khoa XN | Lượng tính được 18.185,56 test. Xuất 94 hộp (18.800 test): lệch 3,27%, không vượt. Xuất 100 hộp (20.000 test): lệch 9,07%, vượt ngưỡng |
| V7 | Đối soát sản lượng GLU, 16.000 kết quả trả | HIS 15.800: lệch 1,27%, không cảnh báo. HIS 15.500: lệch 3,23%, cảnh báo |
| V8 | Cảnh báo sản lượng thấp, HC_GLU | Tổng 12.900 test: 1.060,27 test trong 30 ngày, không cảnh báo. 4.740: 389,59, không. 1.900: 156,16, cảnh báo |

## 3. Test case

### 3.1 Tính giá cận lâm sàng

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-CLS-01 | FR-COST-018, NFR-REL-003 | FEAT-036 | U | Bộ dữ liệu vàng, GLU-A | k = 1,108247; chạy lại cho cùng giá trị |
| TC-CLS-02 | FR-COST-018, FR-QC-006 | FEAT-036 | U | Bộ dữ liệu vàng, GLU-B | Các số test phụ suy từ kế hoạch; k = 1,221649; nhãn "Ước tính từ kế hoạch" |
| TC-CLS-03 | FR-COST-019, FR-NORM-019 | FEAT-036 | U | Dòng L02, L03 của hai hệ thống | Đúng bảng 2.2; không áp hao hụt của dòng |
| TC-CLS-04 | FR-COST-019 | FEAT-036 | U | Dòng L01, L04 | 1.500,00 và 1.250,00 |
| TC-CLS-05 | FR-COST-019 | FEAT-036 | U | Dòng L05 gắn thiết bị | 120,00 với EQ_A; 360,00 với EQ_B |
| TC-CLS-06 | FR-COST-020 | FEAT-036 | U | Kế hoạch chất lượng | Nội kiểm 90,00 và 270,00; chất chuẩn 400,00 và 1.200,00; là dòng chi phí riêng |
| TC-CLS-07 | FR-COST-021, FR-CMP-002, FR-CMP-003, FR-RES-021 | FEAT-036 | U | Cách Theo giá trị tài sản | Kiểm định 10.500.000 và 3.500.000; thiết bị 1.715,00 và 35,00; EQ_B khấu hao và bảo trì bằng 0 |
| TC-CLS-08 | FR-COST-017, FR-CMP-004 | FEAT-036 | U | Biến thể V1; kiểm giá trị mặc định khi tạo lần tính | Đúng V1; mặc định là Thực tế 12 tháng và Theo giá trị tài sản |
| TC-CLS-09 | FR-COST-021, FR-RES-023, FR-RES-026 | FEAT-036 | U | Linh kiện và điện của EQ_A | 300,00 và 87,60 |
| TC-CLS-10 | FR-COST-022, FR-QC-004, FR-CLS-004 | FEAT-036 | U | Dịch vụ GLU | 41.531,03; 44.221,57; bình quân 42.203,67; ngoại kiểm 75,00; tổng 42.278,67; kết quả từng hệ thống được lưu |
| TC-CLS-11 | FR-RES-007 | FEAT-036 | U | Biến thể V2 | ZERO 515,00; CONTINUE 1.715,00; lựa chọn hiện trên bảng giải trình |
| TC-CLS-12 | FR-RES-020 | FEAT-036 | U | Biến thể V3 | 1.500,00; không có khấu hao |
| TC-CLS-13 | FR-RES-022, FR-CLS-005 | FEAT-036 | U | Biến thể V4 | 20.222,2222; 202.222,22; 404.444,44 |
| TC-CLS-14 | FR-COST-007 | FEAT-036 | U | Biến thể V5 | EQ_A 515,00; bảng giải trình ghi khấu hao bị loại |
| TC-CLS-15 | FR-COST-023, FR-CLS-003 | FEAT-036 | U | (a) GLU-B không có sản lượng; (b) Qbn bằng 0; (c) có dòng Theo mẻ, thiếu cỡ mẻ; (d) tỷ trọng khai tay 60% và 30%, không có Qbn theo hệ thống | Mỗi ca: dịch vụ GLU dừng với lỗi nêu đúng dữ liệu thiếu; dịch vụ khác trong lần tính vẫn tính |
| TC-CLS-37 | FR-COST-025, FR-CMP-006 | FEAT-036 | U | Biến thể V8; EQ_A thuộc loại bắt buộc có hồ sơ và hồ sơ đã hết hạn | Cảnh báo "Sản lượng thấp" đúng V8; lần tính có cảnh báo thiếu hồ sơ và vẫn tính |
| TC-CLS-38 | FR-COST-031, FR-COST-032, NFR-CPL-003, NFR-REL-001 | FEAT-036 | I | Khóa lần tính; sửa kế hoạch chất lượng và hồ sơ tuân thủ; tái lập từ ảnh chụp | Bảng giải trình có hệ thống, cấp phát sinh, k và các số tạo nên k, mẫu số, nguồn mẫu số ở mọi dòng; tái lập cho kết quả trùng |
| TC-CLS-51 | FR-COST-024 | FEAT-036 | U | Dịch vụ GLU cùng một dịch vụ lâm sàng trong lần tính | Phân bổ cấp 2 và đối soát tài chính dùng sản lượng 16.000 cho GLU |

### 3.2 Đối soát, báo cáo, độ nhạy

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-CLS-16 | FR-COST-026 | FEAT-037 | U | Biến thể V6, xuất 94 hộp | 18.185,56; 18.800; 3,27%; không vượt |
| TC-CLS-17 | FR-COST-027 | FEAT-037 | I | Biến thể V6, xuất 100 hộp; khóa khi chưa giải trình | 9,07%, "Vượt ngưỡng"; từ chối khóa; khóa được sau khi ghi giải trình |
| TC-CLS-18 | FR-COST-028 | FEAT-037 | U | Biến thể V7 | 1,27% không cảnh báo; 3,23% cảnh báo; không chặn khóa |
| TC-CLS-19 | FR-COST-029 | FEAT-037 | I | Khoa XN không có số liệu xuất kho | Dòng "Chưa đối soát vật chất"; chỉ khóa được sau khi tài chính xác nhận kèm lý do |
| TC-CLS-39 | FR-OUT-012 | FEAT-037 | I | Phạm vi có một dịch vụ thiếu đơn giá, một thiếu sản lượng, một hệ thống thiếu kế hoạch chất lượng | Báo cáo liệt kê đúng ba dịch vụ với đúng loại thiếu |
| TC-CLS-40 | FR-COST-030 | FEAT-037 | I | Mở độ nhạy của GLU; đổi Qbn của GLU-A thành 6.000 | Giá thành thử khác gốc; lần tính giá và kết quả gốc không đổi |

### 3.3 Dữ liệu gốc của phân hệ

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-CLS-20 | FR-SVC-008, FR-CLS-001, FR-CLS-002, FR-CLS-007 | FEAT-031 | I | Đánh dấu GLU là cận lâm sàng; tạo GLU-A và GLU-B | Yêu cầu nhóm chuyên ngành và đơn vị kết quả; hai hệ thống cùng tồn tại; form hiện khối tình trạng |
| TC-CLS-21 | FR-SVC-009 | FEAT-031 | I | Gắn mã LIS "L100" cho GLU rồi cho dịch vụ khác | Lần hai bị từ chối |
| TC-CLS-22 | FR-ACC-008 | FEAT-031 | I | Người dùng NC Clinician của khoa khác sửa GLU-A | Từ chối |
| TC-CLS-23 | FR-CLS-006, FR-CLS-008 | FEAT-031 | I | Ngừng dùng GLU-B; tạo lần tính mới; nhập hệ thống từ tệp mẫu có 1 dòng mã thiết bị lạ | GLU-B không vào lần tính mới, lần đã khóa giữ nguyên; dòng lỗi được báo, dòng đúng được lưu |
| TC-CLS-24 | FR-QC-001, FR-QC-002, FR-QC-003 | FEAT-032 | I | Lập kế hoạch nội kiểm, chuẩn máy, chương trình ngoại kiểm thiếu từng trường bắt buộc | Từ chối cho đến khi đủ trường |
| TC-CLS-25 | FR-QC-005, FR-QC-008 | FEAT-032 | I | Chọn HC_GLU làm vật liệu nội kiểm; nhập tỷ lệ ngoại kiểm 50% và 40% | Cả hai bị từ chối |
| TC-CLS-26 | FR-QC-007 | FEAT-032 | I | Hệ thống nhóm Hóa sinh không có kế hoạch nội kiểm | Cảnh báo trên bộ định mức; vẫn khóa được |
| TC-CLS-27 | FR-CMP-001 | FEAT-033 | I | Tạo hồ sơ thiếu tệp chứng từ; rồi đủ | Lần đầu từ chối; lần sau lưu, trạng thái Còn hạn |
| TC-CLS-28 | FR-CMP-005, FR-CMP-007, FR-ADM-006 | FEAT-033 | I | Hồ sơ còn 20 ngày; số ngày nhắc 30; chạy tác vụ ngày; đổi số ngày nhắc thành 10 | Thông báo đến Vật tư - Thiết bị và trưởng khoa; báo cáo hạn liệt kê hồ sơ; sau khi đổi, hồ sơ về Còn hạn |
| TC-CLS-29 | FR-NORM-017, FR-NORM-021, FR-NORM-022 | FEAT-034 | I | Lập mẫu nhóm Hóa sinh; khởi tạo bộ định mức cho GLU-A | Bộ gắn GLU-A; khoản mục bắt buộc chưa có trong quy trình được thêm ở dạng dòng chung, chưa có lượng |
| TC-CLS-30 | FR-NORM-018, FR-NORM-019 | FEAT-034 | I | Đặt cấp phát sinh cho từng dòng; bật cờ k cho dòng Theo mẻ; bật cờ k cho dòng có hao hụt 5% | Cờ k chỉ bật được ở dòng Theo kết quả loại thuốc, vật tư; bật thì hao hụt về 0 |
| TC-CLS-31 | FR-NORM-024 | FEAT-034 | I | Thêm dòng định mức dùng QC_L | Từ chối lưu dòng |
| TC-CLS-32 | FR-NORM-020, FR-NORM-023 | FEAT-034 | I | Xác nhận chuyên môn khi thiếu số xét nghiệm mỗi ống; khi thiếu một khoản mục bắt buộc | Từ chối, nêu lý do; qua được sau khi nhập số hoặc đánh dấu "Không áp dụng" |
| TC-CLS-33 | FR-NORM-017, FR-NORM-025, FR-OUT-011 | FEAT-034 | I | Sao chép bộ của GLU-A sang GLU-B; khóa cả hai; xuất | Hai bộ "Đã khóa" cùng hiệu lực; tệp xuất có cấp phát sinh, kế hoạch chất lượng, k |
| TC-CLS-34 | FR-ACCT-012, FR-ACCT-013 | FEAT-035 | I | Nạp tệp sản lượng kịch bản Thực tế, dùng mã LIS; cột số test phụ của GLU-B để trống | Lưu theo hệ thống và kịch bản; mã LIS đổi sang mã dịch vụ; cột trống được chấp nhận |
| TC-CLS-35 | FR-ACCT-014 | FEAT-035 | I | Tệp có 1 dòng mã hệ thống lạ, 1 dòng số âm | Hai dòng lỗi được liệt kê và không lưu; dòng khác được lưu |
| TC-CLS-36 | FR-ACCT-015 | FEAT-035 | I | Nạp xuất kho HC_GLU 94 hộp cho khoa XN | Lưu theo mặt hàng, khoa, năm |

### 3.4 AI, quyền và các yêu cầu sửa

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-CLS-41 | FR-LIB-013, FR-AI-016, NFR-SEC-005 | FEAT-038 | I | Nạp tài liệu của hãng gắn HC_GLU; yêu cầu đề xuất cho GLU-A với nhà cung cấp giả lập | Nội dung gửi chỉ gồm mục tài liệu đã gắn, quy trình, tên mặt hàng và thiết bị; không có đơn giá, sản lượng |
| TC-CLS-42 | FR-AI-017 | FEAT-038 | I | AI trả 3 đề xuất: 2 có trích dẫn đúng, 1 trích dẫn không có trong tài liệu | 2 đề xuất có trích dẫn; 1 mang "Chưa có căn cứ"; cả 3 mang nhãn "Đề xuất" và không vào phép tính |
| TC-CLS-43 | FR-AI-018 | FEAT-038 | I | AI đề xuất mặt hàng không có trong danh mục | Không tạo mặt hàng; đề xuất giữ dạng văn bản |
| TC-CLS-44 | FR-ACC-007, FR-ACC-002, FR-ACC-004, FR-AUD-003 | FEAT-039 | I | Người dùng NC Auditor mở số liệu kế toán, đối soát, nhật ký; thử sửa một bộ định mức | Đọc được tất cả; mọi thao tác ghi, xóa, duyệt bị từ chối; script quét quyền không thấy quyền ghi nào của NC Auditor |
| TC-CLS-45 | FR-RES-004 | FEAT-009 | U | Mặt hàng có giá Trúng thầu hiệu lực 01/2025 và Báo giá hiệu lực 06/2026; ngày tính 31/12/2026. Thêm ca giá Trúng thầu có ngày hết hiệu lực 30/06/2026 | Ca 1 lấy giá Trúng thầu; ca 2 lấy Báo giá |
| TC-CLS-46 | FR-RES-002, FR-RES-016, FR-RES-017 | FEAT-009 | I | Thêm đơn giá nguồn Hợp đồng có ngày hết hiệu lực; xác minh khi chưa có tệp; tính giá với đơn giá chưa xác minh | Lưu được; xác minh bị từ chối cho đến khi có tệp; dòng chi phí mang cảnh báo "Đơn giá chưa xác minh" |
| TC-CLS-47 | FR-RES-018 | FEAT-009 | U | HC_GLU: 6.000.000 mỗi hộp, 200 đơn vị định mức | Đơn giá một đơn vị định mức 30.000,0000 |
| TC-CLS-48 | FR-RES-005, FR-RES-019, FR-RES-020, FR-RES-022 | FEAT-010 | I | Tạo thiết bị Thuê không nhập chi phí hợp đồng; thiết bị Mua không nhập nguyên giá; thiết bị chia theo Số kết quả không nhập giờ kế hoạch | Hai ca đầu bị từ chối; ca ba lưu được |
| TC-CLS-49 | FR-RES-024, FR-RES-025 | FEAT-010 | I | Khai tỷ lệ theo khoa 60% và 30% | Từ chối lưu; 60% và 40% thì lưu được |
| TC-CLS-50 | FR-RES-009 | FEAT-011 | I | Tạo bộ tham số mới | Ba tham số mới có mặc định ZERO, 5%, 2% |

FR mức Should hoặc Could chưa có test case ở bản này: FR-SVC-010, FR-SVC-011.
