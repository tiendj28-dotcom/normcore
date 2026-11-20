# Test Cases: Normcore

> Version: 1.1 · Last updated: 2026-11-13
> Nguồn: `docs/srs.md` v1.1, `docs/use-cases.md` v1.1. Bộ dữ liệu vàng chạy được: `docs/golden/golden_engine.py` (bộ máy tính giá, bản 1.0) và `docs/golden/golden_cls.py` (khối cận lâm sàng, bản 1.1).
> Tài liệu này là bộ test case nghiệm thu ở mức sản phẩm. Test case chi tiết của từng tính năng được bổ sung khi tính năng đến lượt xây dựng; kết quả kiểm thử được ghi vào cột Test ref của `docs/rtm.md` khi nghiệm thu.
> Bản 1.1 gộp `docs/sua-doi-1.1/test-cases.md`: thêm mục 1.1, mục 2A, mục 3.8 (51 test case TC-CLS-01 đến TC-CLS-51) và kịch bản E2E-04. Mục 3.9 bổ sung 22 test case cho các yêu cầu mức Must của bản 1.0 chưa có test. Tổng số test case: 119 của bản 1.0 + 51 + 22 = 192. Phần thêm mang nhãn **[1.1]**. Cả hai bộ dữ liệu vàng đã được chạy lại ngày 13/11/2026; các số ở mục 2 và mục 2A khớp kết quả chạy.

## 1. Quy ước

- Mã: `TC-<nhóm>-<số>`. Mỗi test case nêu FR nó kiểm và tính năng (FEAT) chứa nó.
- Loại: **U** kiểm thử đơn vị tự động; **I** kiểm thử tích hợp tự động trên site; **E** kiểm thử đầu cuối; **M** kiểm thử tay khi nghiệm thu.
- Dữ liệu: bộ dữ liệu vàng ở mục 2 dùng cho mọi test case tính giá. Các test case AI dùng nhà cung cấp giả lập trả kết quả cố định.
- **[1.1]** Toàn bộ test case của bản sửa đổi 1.1 dùng chung nhóm mã `CLS` (mục 3.8), kể cả test của yêu cầu thuộc nhóm khác, để không trùng số với các nhóm của bản 1.0. Test case tính giá cận lâm sàng dùng bộ dữ liệu vàng ở mục 2A. Riêng 22 test case ở mục 3.9 kiểm yêu cầu của bản 1.0 nên mang mã của nhóm gốc với số nối tiếp.

### 1.1 Test case 1.0 phải rà lại **[1.1]**

Các yêu cầu dưới đây đã sửa ở SRS 1.1. Test case 1.0 có cột FR chứa yêu cầu này phải được rà lại khi tính năng tương ứng đến lượt xây dựng.

| Yêu cầu sửa | Việc cần làm với test case 1.0 có cột FR chứa yêu cầu này |
| :-- | :-- |
| FR-RES-004 | Đổi kết quả mong đợi: chọn theo thứ tự nguồn trước, rồi đến ngày hiệu lực. Ca cũ "hai đơn giá, lấy bản mới nhất" vẫn đúng khi hai đơn giá cùng loại nguồn |
| FR-RES-005 | Thêm ca cho trường bắt buộc theo hình thức có máy và tiêu chí chia |
| FR-RES-007 | Kết quả cũ (khấu hao bằng 0) là trường hợp bộ tham số chọn ZERO; thêm ca CONTINUE (TC-CLS-11) |
| FR-RES-009 | Thêm ba tham số mới vào dữ liệu kiểm |
| FR-ACC-002, FR-ACC-004, FR-AUD-003 | Thêm NC Auditor vào ma trận kiểm quyền (TC-CLS-44) |
| BR-COST-004 (TC-COST-01, TC-COST-06) | Kết quả của bộ dữ liệu vàng 1.0 không đổi: EQ1 là thiết bị duy nhất của K01 và không có hồ sơ tuân thủ. Giữ nguyên |

## 2. Bộ dữ liệu vàng cho bộ máy tính giá

Mọi số liệu ở mục này là **số thử nghiệm**, không phải số thực tế hay mức quy định. Kết quả mong đợi do `docs/golden/golden_engine.py` tính; bộ máy tính giá của Normcore phải ra đúng các số này đến từng đồng.

### 2.1 Đầu vào

**Bộ tham số**

| Tham số | Giá trị |
| :-- | --: |
| Lương cơ sở | 2.500.000 |
| Tỷ lệ đóng góp của đơn vị | 23,5% |
| Ngày làm việc năm × giờ làm việc ngày | 264 × 8 = 2.112 giờ |
| Cách tính tích lũy, tỷ lệ | ON_COST, 5% |
| Tỷ lệ nghĩa vụ tài chính | 0% |
| Đơn vị làm tròn | 100 |
| Ngưỡng đối soát | 10% |
| Ngày tính giá | 31/12/2026 |

**Chức danh**

| Mã | Hệ số lương | Hệ số phụ cấp được tính | Chi phí năm | Đơn giá giờ công |
| :-- | --: | --: | --: | --: |
| BS | 4,40 | 0,60 | 185.250.000 | 87.713,0682 |
| DD | 3,00 | 0,40 | 125.970.000 | 59.644,8864 |

**Mặt hàng**

| Mã | Đơn giá | Số lần dùng | Ghi chú |
| :-- | --: | --: | :-- |
| GANG | 3.000 | 1 | |
| THUOCX | 25.000 | 1 | |
| DUNGCU | 2.000.000 | 200 | Dùng nhiều lần |
| DIEN | 3.000 | 1 | Tiện ích, theo kWh |
| THUOCY | 80.000 | 1 | Thanh toán riêng ngoài giá |

**Thiết bị và phòng**

| Mã | Dữ liệu | Kết quả |
| :-- | :-- | :-- |
| EQ1 | Nguyên giá 1.200.000.000; thời gian sử dụng 8 năm; đưa vào sử dụng 01/01/2022; bảo trì 30.000.000; kiểm định 6.000.000; 2.112 giờ kế hoạch; hệ số sử dụng 0,5 | Khấu hao năm 150.000.000; đơn giá giờ máy 176.136,3636 |
| R1 | Chi phí hạ tầng năm 52.800.000; 2.112 giờ | Đơn giá giờ phòng 25.000 |

**Bộ định mức của DV-TEST-A (khoa K01, sản lượng 4.000 ca)**

| Dòng | Bước | Cấu phần | Nguồn lực | Định mức bệnh viện | Định mức ban hành | Khác |
| :-- | :-- | :-- | :-- | --: | --: | :-- |
| L01 | S001 | LABOR | DD, 1 người | 10 phút | | |
| L02 | S001 | SUPPLY | GANG | 2 | | |
| L03 | S002 | LABOR | BS, 1 người | 20 phút | 25 phút | |
| L04 | S002 | LABOR | DD, 1 người | 20 phút | | |
| L05 | S002 | DRUG | THUOCX | 1 | | Hao hụt 5% |
| L06 | S002 | SUPPLY | DUNGCU | 1 | | |
| L07 | S002 | EQUIPMENT | EQ1 | 20 phút | | |
| L08 | S002 | INFRA | R1 | 30 phút | | |
| L09 | S003 | LABOR | DD, 1 người | 15 phút | 10 phút | |
| L10 | chung | UTILITY | DIEN | 0,5 kWh | | |
| L11 | S002 | DRUG | THUOCY | 1 | | Loại trừ: thanh toán riêng |

**Bộ định mức của DV-TEST-B (khoa K01, sản lượng 6.000 ca):** L01, S001, LABOR, DD, 30 phút; L02, S001, SUPPLY, GANG, 1.

**Số liệu kế toán đã gán loại chi phí**

| Trung tâm chi phí | Loại | LABOR | DRUG_SUPPLY | DEPRECIATION | UTILITY | MANAGEMENT |
| :-- | :-- | --: | --: | --: | --: | --: |
| K01 | Lâm sàng | 700.000.000 | 260.000.000 | 300.000.000 | 40.000.000 | 100.000.000 |
| HC | Hỗ trợ | 300.000.000 | | | | 400.000.000 |

**Tiêu chí và quy tắc phân bổ.** Cấp 1: HEADCOUNT, K01 có 20 người, K02 có 30 người. Cấp 2: LABOR theo LABOR_MIN; DRUG_SUPPLY theo VOLUME; DEPRECIATION theo MACHINE_MIN; UTILITY theo VOLUME; MANAGEMENT theo LABOR_MIN.

### 2.2 Kết quả mong đợi

**Chi phí trực tiếp DV-TEST-A**

| Dòng | Lượng áp dụng | Đơn giá | Thành tiền | Quy tắc |
| :-- | --: | --: | --: | :-- |
| L01 | 10 | 59.644,8864 | 9.940,81 | BR-COST-002 |
| L02 | 2 | 3.000 | 6.000,00 | BR-COST-003 |
| L03 | 20 | 87.713,0682 | 29.237,69 | BR-COST-007: lấy 20 vì nhỏ hơn 25 |
| L04 | 20 | 59.644,8864 | 19.881,63 | |
| L05 | 1 | 25.000 | 26.250,00 | Hao hụt 5% |
| L06 | 1 | 2.000.000 | 10.000,00 | Chia 200 lần dùng |
| L07 | 20 | 176.136,3636 | 58.712,12 | BR-COST-004 |
| L08 | 30 | 25.000 | 12.500,00 | BR-COST-005 |
| L09 | 10 | 59.644,8864 | 9.940,81 | BR-COST-007: lấy 10 vì nhỏ hơn 15 |
| L10 | 0,5 | 3.000 | 1.500,00 | BR-COST-006 |
| L11 | 0 | 0 | 0,00 | Loại trừ |
| **Tổng** | | | **183.963,06** | |

Theo loại chi phí: LABOR 69.000,94; DRUG_SUPPLY 42.250,00; DEPRECIATION 71.212,12; UTILITY 1.500,00.

**Phân bổ cấp 1.** K01 nhận 20 ÷ 50 = 40% của HC: LABOR 120.000.000; MANAGEMENT 160.000.000.

**Phân bổ cấp 2 và đối soát của K01**

| Loại | Số đã tính | Số kế toán (gồm cấp 1) | Phần còn lại | Chênh lệch % | Vượt ngưỡng |
| :-- | --: | --: | --: | --: | :-- |
| LABOR | 454.938.400 | 820.000.000 | 365.061.600 | −44,52 | Không |
| DRUG_SUPPLY | 187.000.000 | 260.000.000 | 73.000.000 | −28,08 | **Có** |
| DEPRECIATION | 284.848.480 | 300.000.000 | 15.151.520 | −5,05 | Không |
| UTILITY | 6.000.000 | 40.000.000 | 34.000.000 | −85,00 | Không |
| MANAGEMENT | không đối soát | 260.000.000 | 260.000.000 | | |

**Kết quả theo dịch vụ**

| Chỉ tiêu | DV-TEST-A | DV-TEST-B |
| :-- | --: | --: |
| Chi phí trực tiếp | 183.963,06 | 32.822,44 |
| Phân bổ LABOR | 52.151,66 | 26.075,83 |
| Phân bổ DRUG_SUPPLY | 7.300,00 | 7.300,00 |
| Phân bổ DEPRECIATION | 3.787,88 | 0,00 |
| Phân bổ UTILITY | 3.400,00 | 3.400,00 |
| Phân bổ MANAGEMENT | 37.142,86 | 18.571,43 |
| **Giá thành toàn bộ** | **287.745,46** | **88.169,70** |
| Tích lũy 5% | 14.387,27 | 4.408,49 |
| Giá tính toán | 302.132,73 | 92.578,19 |
| **Giá làm tròn** | **302.100** | **92.600** |

### 2.3 Biến thể

| Biến thể | Thay đổi | Kết quả mong đợi của DV-TEST-A |
| :-- | :-- | :-- |
| V1 Không kết cấu khấu hao | Loại giá có `include_depreciation` tắt | Đơn giá giờ máy 34.090,9091; L07 = 11.363,64; L08 = 0; chi phí trực tiếp 124.114,58; không phân bổ DEPRECIATION; giá thành 224.109,10; tích lũy 11.205,46; giá tính toán 235.314,56; giá làm tròn 235.300 |
| V2 Thiết bị hết thời gian sử dụng | EQ1 đưa vào sử dụng 01/01/2015 | L07 = 11.363,64; chi phí trực tiếp 136.614,58; phân bổ DEPRECIATION 51.136,36; giá thành toàn bộ vẫn 287.745,46 vì phần còn lại của số kế toán được phân bổ cấp 2. **[1.1]** Đây là kết quả khi bộ tham số chọn ZERO (mặc định); trường hợp CONTINUE ở TC-CLS-11 |
| V3 Tích lũy ON_PRICE | `accumulation_mode` = ON_PRICE | Tích lũy 15.144,50; giá tính toán 302.889,96; giá làm tròn 302.900 |
| V4 Thiếu đơn giá | Xóa đơn giá của THUOCX | DV-TEST-A báo lỗi nêu dòng L05; DV-TEST-B vẫn tính, chi phí trực tiếp 32.822,44 |
| V5 Sản lượng bằng 0 | Sản lượng DV-TEST-B = 0 | DV-TEST-B: chi phí trực tiếp 32.822,44, mọi khoản phân bổ bằng 0, có cảnh báo |

## 2A. Bộ dữ liệu vàng cho khối cận lâm sàng **[1.1]**

Mọi số liệu ở mục này là **số thử nghiệm**. Kết quả mong đợi do `docs/golden/golden_cls.py` tính; phần cận lâm sàng của bộ máy tính giá phải ra đúng các số này: thành tiền đến 2 chữ số thập phân, hệ số k đến 6 chữ số. Phạm vi: chi phí trực tiếp một kết quả; phân bổ và làm tròn giá dùng bộ dữ liệu vàng 1.0.

### 2A.1 Đầu vào

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

### 2A.2 Kết quả mong đợi

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

### 2A.3 Biến thể

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

## 3. Test case theo nhóm chức năng

### 3.1 Truy cập và phân quyền

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-ACC-01 | FR-ACC-003 | FEAT-001 | I | Người dùng NC Clinician của khoa K01 mở sửa một quy trình nháp của khoa K02 | Từ chối sửa; quy trình đã ban hành của K02 vẫn đọc được |
| TC-ACC-02 | FR-ACC-004 | FEAT-001 | I | NC Clinician gọi API và mở danh sách NC Accounting Import, NC Reconciliation Line | Danh sách trống, API trả lỗi quyền |
| TC-ACC-03 | FR-ACC-005 | FEAT-001 | I | NC Resource Manager mở đường dẫn trực tiếp tới một NC Costing Run | Thông báo không đủ quyền; phản hồi không chứa trường nào của bản ghi |
| TC-ACC-04 | FR-ACC-002 | FEAT-001 | U | Quét khai báo quyền của mọi DocType `NC ` | Không DocType nào có quyền cho vai trò `All`; khớp ma trận ở `docs/data-model.md` mục 4. **[1.1]** Ma trận nay có 10 vai trò, gồm NC Auditor (xem TC-CLS-44) |

### 3.2 Thư viện văn bản và danh mục kỹ thuật

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-LIB-01 | FR-LIB-001, FR-LIB-003 | FEAT-020 | I | Tải một tệp PDF có lớp văn bản gồm 3 quy trình | Bản ghi tạo với "Chưa lập"; sau tác vụ nền có 3 mục cấp 1, đủ số mục, tiêu đề, trang; trạng thái "Đã lập" |
| TC-LIB-02 | FR-LIB-002 | FEAT-020 | I | Tạo văn bản số `123/qđ-byt` khi đã có `123/QĐ-BYT` | Từ chối, chỉ ra bản ghi trùng |
| TC-LIB-03 | FR-LIB-005 | FEAT-020 | I | Tải tệp hỏng | Trạng thái "Lỗi", có lý do, người tải nhận thông báo |
| TC-LIB-04 | FR-LIB-006 | FEAT-020 | I | Văn bản có ngày hiệu lực là ngày mai; chạy tác vụ ngày với ngày giả lập | Hôm nay "Chưa hiệu lực"; ngày mai "Còn hiệu lực" |
| TC-LIB-05 | FR-LIB-007 | FEAT-021 | I | Khai báo A thay toàn bộ B từ 01/07 | B có ngày hết hiệu lực 30/06; từ 01/07 mọi mục của B "Hết hiệu lực" |
| TC-LIB-06 | FR-LIB-008 | FEAT-021 | I | Khai báo A thay mục 2 và 5 của B | Chỉ mục 2 và 5 hết hiệu lực; các mục khác còn hiệu lực |
| TC-LIB-07 | FR-LIB-009 | FEAT-021 | I | Quy trình đã ban hành có trích dẫn mục 2 của B; mục 2 hết hiệu lực | Quy trình có cờ "Cần rà soát"; trưởng khoa nhận thông báo; quy trình xuất hiện ở hàng đợi rà soát |
| TC-LIB-08 | FR-LIB-010 | FEAT-020 | I | Tìm theo một cụm từ có trong mục và theo mã dịch vụ | Trả về mục khớp kèm số hiệu, số mục, trang, hiệu lực |
| TC-SVC-01 | FR-SVC-001, FR-SVC-002 | FEAT-005 | I | Nhập tệp 10 dòng: 1 dòng thiếu tên, 2 dòng trùng mã | 7 dịch vụ được tạo; báo cáo lỗi liệt kê 3 dòng với lý do |
| TC-SVC-02 | FR-SVC-006, FR-SVC-007 | FEAT-022 | I | Một mục có ánh xạ "Đề xuất" với dịch vụ X; soạn dự thảo cho X | Mục không nằm trong nguồn gửi AI; sau khi xác nhận ánh xạ thì có |
| TC-SVC-03 | FR-SVC-004 | FEAT-005 | I | Mở dịch vụ đã có quy trình ban hành, bộ định mức khóa, lần tính giá | Hiển thị đủ bốn mục tình trạng chuỗi với liên kết |

### 3.3 Quy trình, AI, phê duyệt

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-PROC-01 | FR-PROC-001 | FEAT-006 | I | Tạo quy trình cho dịch vụ X, khoa K01 | Bản nháp phiên bản 1 có đủ 8 phần cố định |
| TC-PROC-02 | FR-PROC-002 | FEAT-006 | I | Tạo lần hai khi bản nháp còn | Từ chối, dẫn tới bản nháp đang có |
| TC-PROC-03 | FR-PROC-003, FR-PROC-006 | FEAT-006 | U | Thêm 3 bước, đổi thứ tự bước 1 và 3, xóa bước 2, thêm bước mới | Mã bước của bước cũ không đổi; bước mới nhận `S004`, không tái dùng `S002` |
| TC-PROC-04 | FR-PROC-004 | FEAT-006 | I | Khai báo nguồn lực nhân lực có chức danh, số người | Lưu thành dòng có cấu trúc gắn mã bước và có mã dòng bất biến |
| TC-PROC-05 | FR-PROC-008 | FEAT-007 | I | Có trích dẫn "Khác biệt" trống lý do; gửi duyệt | Từ chối gửi; nêu trích dẫn thiếu lý do |
| TC-PROC-06 | FR-PROC-012 | FEAT-007 | I | Quy trình không có bước "Thực hiện", một bước thiếu mô tả, một nguồn lực thiếu đơn vị | Liệt kê đủ 3 lỗi; trạng thái vẫn "Nháp" |
| TC-PROC-07 | FR-PROC-010 | FEAT-007 | M | In bản nháp và bản đã ban hành | Bản nháp có chữ "DỰ THẢO"; bản ban hành có số quyết định, phiên bản, ngày hiệu lực, khối chữ ký |
| TC-PROC-08 | FR-PROC-009 | FEAT-006 | I | Sửa mô tả một bước và số lượng một nguồn lực | Lịch sử ghi giá trị trước, sau, người, thời điểm cho cả hai |
| TC-AI-01 | FR-AI-001, FR-AI-002 | FEAT-024 | I | Nhà cung cấp giả lập trả dự thảo 5 bước có trích dẫn đúng | Bản nháp có 5 bước, nguồn lực, mỗi phần và bước có trích dẫn; nguồn gửi đi chỉ gồm mục đã xác nhận, còn hiệu lực |
| TC-AI-02 | FR-AI-005 | FEAT-024 | U | Kết quả giả lập có 1 trích dẫn với đoạn trích không có trong mục nguồn | Trích dẫn bị loại; bước liên quan mang "Chưa có căn cứ"; nhật ký ghi 1 trích dẫn bị loại |
| TC-AI-03 | FR-AI-003 | FEAT-024 | I | Yêu cầu nêu dùng thiết bị khác hướng dẫn; kết quả giả lập đánh dấu khác biệt | Bước mang nhãn "Khác biệt" với lý do lấy từ yêu cầu |
| TC-AI-04 | FR-AI-004 | FEAT-024 | I | Dịch vụ không có mục đã xác nhận | Cảnh báo; sau khi xác nhận, dự thảo mang "Chưa có căn cứ" ở phần không có nguồn |
| TC-AI-05 | FR-AI-010 | FEAT-023 | I | Nhà cung cấp giả lập không phản hồi quá thời hạn | Thông báo lỗi; dữ liệu đã nhập còn nguyên; không có bản nháp dở; nhật ký ghi "Quá hạn" |
| TC-AI-06 | FR-AI-011 | FEAT-023 | U | Gọi bộ dựng nội dung với từng DocType kế toán, tính giá | Mọi lần đều bị từ chối; chỉ DocType trong danh sách cho phép đi qua |
| TC-AI-07 | FR-AI-015 | FEAT-023 | I | Tắt AI trong cấu hình | Các nút gọi AI ẩn; tạo quy trình, bộ định mức, giá tham chiếu bằng tay vẫn chạy |
| TC-AI-08 | FR-AI-009 | FEAT-023 | I | Sau TC-AI-01 | Có một NC AI Log với đủ mục đích, người gọi, bản ghi, mẫu lệnh và phiên bản, mục nguồn, token, thời gian, trạng thái |
| TC-AI-09 | FR-AI-013 | FEAT-023 | I | Hạn mức tháng 1.000 token, lũy kế 1.200 | Lần gọi mới bị chặn; NC Admin nhận thông báo; nhật ký ghi "Bị chặn hạn mức" |
| TC-AI-10 | FR-AI-008 | FEAT-024 | I | Bản nháp còn 1 bước mang nhãn "Đề xuất"; gửi duyệt | Từ chối gửi; nêu bước chưa xử lý |
| TC-AI-11 | FR-AI-012 | FEAT-023 | I | Đổi giao thức và địa chỉ trong cấu hình; gọi lại | Lời gọi kế tiếp đi tới địa chỉ mới, không khởi động lại dịch vụ |
| TC-WF-01 | FR-WF-001, FR-WF-002, FR-WF-004, FR-WF-005 | FEAT-007 | E | Gửi duyệt, trưởng khoa đồng ý, thư ký thông qua, giám đốc ban hành với số quyết định và ngày | Qua đủ 4 trạng thái; mỗi bước có thông báo đúng người; cuối cùng "Đã ban hành" |
| TC-WF-02 | FR-WF-007 | FEAT-007 | I | Trưởng khoa từ chối không ghi lý do; rồi ghi lý do | Lần đầu bị yêu cầu lý do; lần hai về "Nháp", người soạn nhận thông báo |
| TC-WF-03 | FR-WF-008 | FEAT-007 | I | Sửa mô tả bước của quy trình đã ban hành qua giao diện và API | Cả hai bị từ chối |
| TC-WF-04 | FR-WF-006 | FEAT-007 | I | Ban hành phiên bản 2 với ngày hiệu lực tương lai; chạy tác vụ ngày đến ngày đó | Trước ngày: phiên bản 1 còn "Đã ban hành"; đến ngày: phiên bản 1 "Đã thay thế" |
| TC-WF-05 | FR-WF-009 | FEAT-008 | I | Chọn "Sửa đổi" trên quy trình đã ban hành có 4 bước | Bản nháp phiên bản 2 có 4 bước với đúng mã bước cũ |
| TC-WF-06 | FR-WF-011 | FEAT-008 | I | Phiên bản 2 bỏ `S002`, thêm `S005`, đổi nguồn lực `S003`; ban hành | Bộ định mức dựa trên phiên bản 1 có cờ "Cần cập nhật" và ghi: thêm S005, bỏ S002, đổi S003 |
| TC-WF-07 | FR-WF-010 | FEAT-008 | M | So sánh phiên bản 1 và 2 | Hiển thị khác biệt theo phần, bước, dòng nguồn lực |
| TC-WF-08 | FR-WF-003 | FEAT-007 | I | Thành viên hội đồng ghi ý kiến ở bước `S002` | Ý kiến lưu với mã bước; hiển thị tại bước đó cho người soạn sau khi bị trả lại |

### 3.4 Nguồn lực, định mức, bấm giờ

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-RES-01 | FR-RES-004 | FEAT-009 | U | Mặt hàng có đơn giá hiệu lực 01/01, 01/06 và 01/01 năm sau; ngày tính giá 31/12 | Chọn đơn giá 01/06. **[1.1]** Ba đơn giá cùng loại nguồn; ca khác loại nguồn ở TC-CLS-45 |
| TC-RES-02 | FR-RES-003 | FEAT-009 | U | Đơn giá có ngày chứng từ cũ hơn ngày tính giá 25 tháng | Dòng chi phí có cảnh báo "Đơn giá quá hạn tham chiếu"; vẫn tính |
| TC-RES-03 | FR-RES-006 | FEAT-010 | U | Dữ liệu EQ1 ở mục 2.1 | Khấu hao năm 150.000.000; đơn giá giờ máy 176.136,3636 |
| TC-RES-04 | FR-RES-007 | FEAT-010 | U | Biến thể V2 | Khấu hao 0; đơn giá giờ máy 34.090,9091. **[1.1]** Bộ tham số chọn ZERO; ca CONTINUE ở TC-CLS-11 |
| TC-RES-05 | FR-RES-010 | FEAT-011 | U | Chức danh BS, DD ở mục 2.1 | Chi phí năm và đơn giá giờ công đúng bảng |
| TC-RES-06 | FR-RES-011 | FEAT-011 | I | Sửa bộ tham số đã được lần tính giá khóa dùng | Từ chối; nhân bản được |
| TC-RES-07 | FR-RES-014 | FEAT-009 | U | THUOCY đánh dấu thanh toán riêng | Dòng L11 có thành tiền 0 và lý do loại trên bảng giải trình |
| TC-RES-08 | FR-RES-012 | FEAT-009 | I | Nhập tệp mặt hàng có 2 dòng thiếu đơn vị tính | Các dòng hợp lệ được tạo; báo cáo liệt kê 2 dòng lỗi |
| TC-NORM-01 | FR-NORM-001 | FEAT-012 | I | Quy trình đã ban hành có 6 dòng nguồn lực; khởi tạo bộ định mức | Bộ nháp có 6 dòng, mỗi dòng mang mã bước và mã dòng nguồn lực gốc |
| TC-NORM-02 | FR-NORM-002 | FEAT-012 | I | Dịch vụ chỉ có quy trình nháp | Từ chối khởi tạo |
| TC-NORM-03 | FR-NORM-006, FR-NORM-007 | FEAT-012 | U | Dòng L03, L09 và L01 của bộ dữ liệu vàng | Lượng áp dụng 20, 10 và 10 |
| TC-NORM-04 | FR-NORM-004 | FEAT-012 | I | Trần hao hụt 5%; nhập 8% không lý do | Yêu cầu lý do trước khi lưu |
| TC-NORM-05 | FR-NORM-010 | FEAT-012 | I | Bộ còn 1 dòng chưa xác nhận, 1 dòng chưa liên kết danh mục; chuyển "Đã xác nhận chuyên môn" | Từ chối; liệt kê 2 dòng |
| TC-NORM-06 | FR-NORM-011, FR-NORM-012 | FEAT-012 | I | Tài chính khóa bộ; sau đó sửa một dòng | Bộ "Đã khóa"; sửa bị từ chối; tạo phiên bản mới được |
| TC-NORM-07 | FR-NORM-013 | FEAT-012 | I | Đánh dấu loại trừ không chọn lý do | Yêu cầu lý do thuộc danh sách |
| TC-NORM-08 | FR-NORM-015 | FEAT-013 | I | Sau TC-WF-06, tạo phiên bản bộ định mức mới | Dòng của S001, S003, S004 được mang sang; dòng của S002 bị đánh dấu; S005 nằm trong danh sách bước chưa có dòng |
| TC-NORM-09 | FR-NORM-005 | FEAT-012 | I | Thêm dòng điện không có trong quy trình | Phải chọn mã bước hoặc "chung cho cả dịch vụ" |
| TC-TS-01 | FR-TS-003 | FEAT-014 | U | 5 ca với số phút bước S002 của BS: 18, 22, 20, 25, 19; thêm ca thứ 6: 21 | Trung vị 20; sau ca thứ 6: 20,5 |
| TC-TS-02 | FR-TS-004 | FEAT-014 | I | Áp kết quả vào bộ định mức nháp | Số phút dòng tương ứng cập nhật; căn cứ "Bấm giờ" |
| TC-TS-03 | FR-TS-005 | FEAT-014 | I | Chỉ có 3 ca; chọn áp | Cảnh báo, yêu cầu xác nhận |

### 3.5 Kế toán và tính giá

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-ACCT-01 | FR-ACCT-001, FR-ACCT-003 | FEAT-016 | I | Nạp tệp chi phí của bộ dữ liệu vàng ở dạng tài khoản | Lần nhập "Nháp" với số dòng và tổng đúng; mỗi dòng có loại chi phí theo bảng ánh xạ |
| TC-ACCT-02 | FR-ACCT-002 | FEAT-016 | I | Tệp có 1 dòng số tiền là chữ, 1 dòng mã trung tâm chi phí lạ | Liệt kê 2 dòng lỗi; không chốt được |
| TC-ACCT-03 | FR-ACCT-005 | FEAT-016 | I | Một dòng có tài khoản không khớp bảng ánh xạ; chốt | Từ chối chốt, nêu dòng chưa gán |
| TC-ACCT-04 | FR-ACCT-004 | FEAT-016 | I | Đổi loại chi phí một dòng không ghi lý do | Yêu cầu lý do; lưu người sửa |
| TC-ACCT-05 | FR-ACCT-007 | FEAT-016 | I | Tệp sản lượng có 1 mã dịch vụ không tồn tại | Báo lỗi dòng đó; các dòng khác được lưu |
| TC-COST-01 | FR-COST-003 | FEAT-015 | U | Bộ dữ liệu vàng | Thành tiền 11 dòng của DV-TEST-A đúng bảng mục 2.2; tổng 183.963,06 |
| TC-COST-02 | FR-COST-004 | FEAT-017 | U | Bộ dữ liệu vàng | K01 nhận LABOR 120.000.000 và MANAGEMENT 160.000.000 |
| TC-COST-03 | FR-COST-005 | FEAT-017 | U | Bộ dữ liệu vàng | Phần còn lại và phân bổ theo ca đúng bảng mục 2.2 cho cả hai dịch vụ |
| TC-COST-04 | FR-COST-006 | FEAT-015 | U | Bộ dữ liệu vàng | Giá thành, tích lũy, giá tính toán, giá làm tròn đúng bảng mục 2.2 |
| TC-COST-05 | FR-COST-008, FR-COST-009 | FEAT-017 | U | Bộ dữ liệu vàng | 4 dòng đối soát đúng số; chỉ DRUG_SUPPLY vượt ngưỡng; không có dòng MANAGEMENT |
| TC-COST-06 | FR-COST-007 | FEAT-015 | U | Biến thể V1 | Đúng kết quả V1; bảng giải trình ghi khấu hao bị loại |
| TC-COST-07 | FR-COST-016 | FEAT-015 | U | Biến thể V4 | DV-TEST-A lỗi nêu L05; DV-TEST-B thành công |
| TC-COST-08 | FR-COST-014 | FEAT-017 | U | Biến thể V5 | Đúng kết quả V5 |
| TC-COST-09 | FR-COST-011, NFR-REL-001 | FEAT-018 | I | Tính, khóa; đổi đơn giá GANG; tính lại từ ảnh chụp | Kết quả trùng lần đầu ở mọi trường; đơn giá mới không ảnh hưởng |
| TC-COST-10 | FR-COST-009 | FEAT-017 | I | Khóa khi dòng DRUG_SUPPLY chưa có giải trình | Từ chối khóa; sau khi ghi giải trình thì khóa được |
| TC-COST-11 | FR-COST-012 | FEAT-018 | I | Chọn "Tính" trên lần tính giá đã khóa | Từ chối; nhân bản tạo lần mới ở "Nháp" |
| TC-COST-12 | FR-COST-006 | FEAT-015 | U | Biến thể V3 | Đúng kết quả V3 |
| TC-COST-13 | FR-COST-006 | FEAT-015 | U | Giá tính toán 302.150,00 và 302.149,99 với đơn vị làm tròn 100 | 302.200 và 302.100 |
| TC-COST-14 | NFR-PERF-002, FR-COST-015 | FEAT-017 | I | 500 dịch vụ, 50.000 dòng định mức sinh tự động | Hoàn tất trong 5 phút; chạy nền; có tiến độ |
| TC-COST-15 | FR-COST-010, NFR-CPL-001 | FEAT-015 | I | Mở bảng giải trình DV-TEST-A | Mọi dòng trực tiếp có mã bước (hoặc "chung"), nguồn lực, lượng, đơn giá, nguồn đơn giá; mọi dòng phân bổ có quy tắc, tiêu chí, tổng tiêu chí, số tiền |
| TC-COST-16 | FR-COST-005 | FEAT-017 | U | Đặt số kế toán DEPRECIATION của K01 bằng 200.000.000 | Phần còn lại 0; phân bổ DEPRECIATION bằng 0; chênh lệch +42,42%; dòng vượt ngưỡng |
| TC-COST-17 | FR-COST-002 | FEAT-015 | I | Phạm vi có 1 dịch vụ chưa có bộ định mức khóa | Liệt kê dịch vụ đó; sau xác nhận chỉ tính các dịch vụ còn lại |
| TC-COST-18 | FR-COST-013 | FEAT-018 | I | So sánh lần tính gốc với biến thể V1 | Chênh lệch DV-TEST-A: giá thành −63.636,36; hiển thị theo cấu phần |

### 3.6 Giá tham chiếu, so sánh, phương án giá, đầu ra

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-BM-01 | FR-BM-002, FR-BM-004 | FEAT-026 | I | Nhập tệp 5 dòng, 2 dòng chỉ có tên gốc | 5 dòng được tạo; 2 dòng có dịch vụ đề xuất chờ xác nhận |
| TC-BM-02 | FR-BM-007 | FEAT-026 | I | Nhập lại một dòng trùng đơn vị, dịch vụ, loại giá, ngày | Từ chối dòng trùng |
| TC-BM-03 | FR-BM-005 | FEAT-026 | I | Dịch vụ có 3 giá "Đã xác nhận" và 1 giá "Đề xuất" | So sánh chỉ dùng 3 giá |
| TC-BM-04 | FR-BM-006 | FEAT-026 | U | Giá 200.000 hiệu lực tháng có chỉ số 100; tháng tính giá chỉ số 104 | Giá hiệu chỉnh 208.000 |
| TC-BM-05 | FR-BM-003 | FEAT-027 | I | Nhà cung cấp giả lập trả 4 dòng từ tệp PDF | 4 dòng "Đề xuất" có liên kết nhật ký AI; chưa tham gia so sánh |
| TC-ADJ-01 | FR-ADJ-001 | FEAT-028 | U | Đơn vị P có giá ngày 01/01/2025 và 01/06/2026; đơn vị Q có giá ngày 01/10/2024; ngày tính giá 31/12/2026 | Lấy giá 01/06/2026 của P; loại giá của Q vì ngoài 24 tháng |
| TC-ADJ-02 | FR-ADJ-002 | FEAT-028 | U | Giá tính toán 302.132,73; giá tham chiếu 250.000, 280.000, 300.000; thêm 320.000 | Trung vị 280.000, lệch +7,90%; với 4 giá: trung vị 290.000, lệch +4,18% |
| TC-ADJ-03 | FR-ADJ-003 | FEAT-028 | I | Dịch vụ có 2 đơn vị tham chiếu | Nhãn "Chưa đủ dữ liệu so sánh"; không có gợi ý dựa trên so sánh |
| TC-ADJ-04 | FR-ADJ-005 | FEAT-028 | U | DV-TEST-A với trung vị 250.000 (lệch +20,85%), hệ số sử dụng EQ1 = 0,4, trung vị bấm giờ L04 = 15 phút | Có gợi ý BR-ADJ-001 cho EQ1 và BR-ADJ-002 cho L04, mỗi gợi ý có giá trị hiện tại, đề xuất, tác động; xếp theo tác động giảm dần |
| TC-ADJ-05 | FR-ADJ-006 | FEAT-029 | I | Chấp nhận gợi ý BR-ADJ-001 | Kịch bản ghi thay đổi; giá DV-TEST-A trong kịch bản được tính lại; lần tính gốc không đổi |
| TC-ADJ-06 | FR-ADJ-007 | FEAT-029 | I | Chấp nhận gợi ý BR-ADJ-003 (thay mặt hàng) | Không sửa bộ định mức; tạo NC Procedure Change Request; trưởng khoa nhận thông báo |
| TC-ADJ-07 | FR-ADJ-009 | FEAT-029 | I | Chấp nhận gợi ý BR-ADJ-002 | Tạo phiên bản bộ định mức nháp với số phút mới, chờ xác nhận lại |
| TC-ADJ-08 | FR-ADJ-010 | FEAT-028 | I | Mở DV-TEST-A trong so sánh | Hiển thị giá trị và tỷ trọng từng cấu phần, tổng bằng giá thành toàn bộ |
| TC-PRICE-01 | FR-PRICE-001 | FEAT-030 | I | Lập phương án từ lần tính giá vàng đã khóa | 2 dòng; giá đề xuất mặc định 302.100 và 92.600 |
| TC-PRICE-02 | FR-PRICE-002 | FEAT-030 | I | Sửa giá đề xuất DV-TEST-A thành 295.000 không ghi căn cứ; gửi duyệt | Từ chối gửi; yêu cầu căn cứ |
| TC-PRICE-03 | FR-PRICE-003 | FEAT-030 | I | Giá đề xuất 280.000 (dưới giá thành 287.745,46); giám đốc phê duyệt không tích xác nhận dòng | Từ chối phê duyệt cho đến khi xác nhận riêng dòng đó |
| TC-PRICE-04 | FR-PRICE-004, FR-PRICE-005 | FEAT-030 | E | Phương án có dịch vụ của 2 khoa; lần lượt từng trưởng khoa xác nhận | Sau khoa thứ nhất: vẫn "Chờ khoa xác nhận"; sau khoa thứ hai: "Chờ phê duyệt" |
| TC-PRICE-05 | FR-PRICE-006, FR-PRICE-010 | FEAT-030 | I | Phê duyệt phương án loại giá do bệnh viện quyết định, ngày áp dụng 01/01/2027 | Phương án khóa; dịch vụ có dòng lịch sử giá mới; giá cũ còn trong lịch sử |
| TC-PRICE-06 | FR-PRICE-007, FR-PRICE-008 | FEAT-030 | I | Phê duyệt phương án loại giá do cơ quan có thẩm quyền quyết định; rồi ghi kết quả phê duyệt | Trạng thái "Đã duyệt nội bộ, chờ trình"; sau khi ghi: lưu giá được duyệt cạnh giá đã trình |
| TC-PRICE-07 | FR-PRICE-009 | FEAT-030 | I | Trưởng khoa từ chối với lý do | Phương án về "Nháp"; tài chính nhận thông báo |
| TC-OUT-01 | FR-OUT-001, FR-OUT-002, FR-OUT-004, NFR-CPL-002 | FEAT-019 | M | Xuất Phụ lục II, III, V từ phương án vàng | Cấu trúc cột khớp mẫu chính thức; số khớp bảng mục 2.2 |
| TC-OUT-02 | FR-OUT-005 | FEAT-019 | M | Xuất bảng giải trình DV-TEST-A | PDF nhóm theo cấu phần và bước; tổng 287.745,46 |
| TC-OUT-03 | FR-OUT-008, FR-AUD-004 | FEAT-019 | I | Xuất một tệp bất kỳ | Tệp có mã lần tính giá, bộ tham số, thời điểm, người xuất; có sự kiện nhật ký "Xuất tệp" |
| TC-OUT-04 | FR-OUT-006 | FEAT-019 | M | Xuất bộ định mức DV-TEST-A | Excel và PDF có 11 dòng theo bước, căn cứ, người xác nhận |
| TC-OUT-05 | FR-OUT-007 | FEAT-030 | I | Xuất bảng so sánh giá | Excel có đơn vị, giá, ngày, nguồn, thống kê |

### 3.7 Nhật ký, thông báo, phi chức năng

| Mã | FR / NFR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-AUD-01 | FR-AUD-001 | FEAT-003 | I | Sửa một đơn giá; ban hành một quy trình | Có lịch sử theo trường cho đơn giá; có sự kiện chuyển trạng thái cho quy trình |
| TC-AUD-02 | FR-AUD-002 | FEAT-003 | I | NC Admin sửa và xóa NC Audit Event, NC AI Log qua giao diện và API | Mọi thao tác bị từ chối |
| TC-AUD-03 | FR-AUD-003 | FEAT-003 | I | NC Director lọc nhật ký theo một quy trình | Các sự kiện theo thứ tự thời gian |
| TC-NOTI-01 | FR-NOTI-001, FR-NOTI-003 | FEAT-002 | I | Gửi duyệt một quy trình | Trưởng khoa có thông báo kèm liên kết; trang chủ của trưởng khoa liệt kê việc này |
| TC-NFR-01 | NFR-PERF-001 | Foundations | I | 50 người dùng giả lập mở danh sách và form | 95% lượt trong 2 giây |
| TC-NFR-02 | NFR-AVL-002 | Foundations | M | Khôi phục site staging từ bản sao lưu đêm trước | Hoàn tất trong 8 giờ; dữ liệu đến thời điểm sao lưu |
| TC-NFR-03 | NFR-MNT-003 | Foundations | U | Quét mọi DocType `NC ` | Mọi fieldname khớp `^[a-z][a-z0-9_]*$`; mọi label có ký tự tiếng Việt hoặc là thuật ngữ được cho phép |
| TC-NFR-04 | NFR-SEC-004 | FEAT-023 | I | Lưu khóa AI; đọc lại qua API và xem nhật ký | Khóa không trả về dạng rõ; không xuất hiện trong nhật ký |
| TC-NFR-05 | NFR-USE-003 | FEAT-014 | M | Ghi một ca 6 bước trên máy tính bảng 768 px | Mỗi bước không quá 3 lần chạm; không phải cuộn ngang |

### 3.8 Phân hệ E (cận lâm sàng) và các yêu cầu sửa ở bản 1.1 **[1.1]**

Dữ liệu: bộ dữ liệu vàng ở mục 2A. Biến thể V1 đến V8 nhắc ở mục này là biến thể của mục 2A.3, không phải của mục 2.3.

#### 3.8.1 Tính giá cận lâm sàng

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-CLS-01 | FR-COST-018, NFR-REL-003 | FEAT-036 | U | Bộ dữ liệu vàng, GLU-A | k = 1,108247; chạy lại cho cùng giá trị |
| TC-CLS-02 | FR-COST-018, FR-QC-006 | FEAT-036 | U | Bộ dữ liệu vàng, GLU-B | Các số test phụ suy từ kế hoạch; k = 1,221649; nhãn "Ước tính từ kế hoạch" |
| TC-CLS-03 | FR-COST-019, FR-NORM-019 | FEAT-036 | U | Dòng L02, L03 của hai hệ thống | Đúng bảng 2A.2; không áp hao hụt của dòng |
| TC-CLS-04 | FR-COST-019 | FEAT-036 | U | Dòng L01, L04 | 1.500,00 và 1.250,00 |
| TC-CLS-05 | FR-COST-019 | FEAT-036 | U | Dòng L05 gắn thiết bị | 120,00 với EQ_A; 360,00 với EQ_B |
| TC-CLS-06 | FR-COST-020 | FEAT-036 | U | Kế hoạch chất lượng | Nội kiểm 90,00 và 270,00; chất chuẩn 400,00 và 1.200,00; là dòng chi phí riêng |
| TC-CLS-07 | FR-COST-021, FR-CMP-002, FR-CMP-003, FR-RES-021 | FEAT-036 | U | Cách Theo giá trị tài sản | Kiểm định 10.500.000 và 3.500.000; thiết bị 1.715,00 và 35,00; EQ_B khấu hao và bảo trì bằng 0 |
| TC-CLS-08 | FR-COST-017, FR-CMP-004 | FEAT-036 | U | Biến thể V1 (mục 2A.3); kiểm giá trị mặc định khi tạo lần tính | Đúng V1; mặc định là Thực tế 12 tháng và Theo giá trị tài sản |
| TC-CLS-09 | FR-COST-021, FR-RES-023, FR-RES-026 | FEAT-036 | U | Linh kiện và điện của EQ_A | 300,00 và 87,60 |
| TC-CLS-10 | FR-COST-022, FR-QC-004, FR-CLS-004 | FEAT-036 | U | Dịch vụ GLU | 41.531,03; 44.221,57; bình quân 42.203,67; ngoại kiểm 75,00; tổng 42.278,67; kết quả từng hệ thống được lưu |
| TC-CLS-11 | FR-RES-007 | FEAT-036 | U | Biến thể V2 (mục 2A.3) | ZERO 515,00; CONTINUE 1.715,00; lựa chọn hiện trên bảng giải trình |
| TC-CLS-12 | FR-RES-020 | FEAT-036 | U | Biến thể V3 (mục 2A.3) | 1.500,00; không có khấu hao |
| TC-CLS-13 | FR-RES-022, FR-CLS-005 | FEAT-036 | U | Biến thể V4 (mục 2A.3) | 20.222,2222; 202.222,22; 404.444,44 |
| TC-CLS-14 | FR-COST-007 | FEAT-036 | U | Biến thể V5 (mục 2A.3) | EQ_A 515,00; bảng giải trình ghi khấu hao bị loại |
| TC-CLS-15 | FR-COST-023, FR-CLS-003 | FEAT-036 | U | (a) GLU-B không có sản lượng; (b) Qbn bằng 0; (c) có dòng Theo mẻ, thiếu cỡ mẻ; (d) tỷ trọng khai tay 60% và 30%, không có Qbn theo hệ thống | Mỗi ca: dịch vụ GLU dừng với lỗi nêu đúng dữ liệu thiếu; dịch vụ khác trong lần tính vẫn tính |
| TC-CLS-37 | FR-COST-025, FR-CMP-006 | FEAT-036 | U | Biến thể V8 (mục 2A.3); EQ_A thuộc loại bắt buộc có hồ sơ và hồ sơ đã hết hạn | Cảnh báo "Sản lượng thấp" đúng V8 (mục 2A.3); lần tính có cảnh báo thiếu hồ sơ và vẫn tính |
| TC-CLS-38 | FR-COST-031, FR-COST-032, NFR-CPL-003, NFR-REL-001 | FEAT-036 | I | Khóa lần tính; sửa kế hoạch chất lượng và hồ sơ tuân thủ; tái lập từ ảnh chụp | Bảng giải trình có hệ thống, cấp phát sinh, k và các số tạo nên k, mẫu số, nguồn mẫu số ở mọi dòng; tái lập cho kết quả trùng |
| TC-CLS-51 | FR-COST-024 | FEAT-036 | U | Dịch vụ GLU cùng một dịch vụ lâm sàng trong lần tính | Phân bổ cấp 2 và đối soát tài chính dùng sản lượng 16.000 cho GLU |

#### 3.8.2 Đối soát, báo cáo, độ nhạy

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-CLS-16 | FR-COST-026 | FEAT-037 | U | Biến thể V6 (mục 2A.3), xuất 94 hộp | 18.185,56; 18.800; 3,27%; không vượt |
| TC-CLS-17 | FR-COST-027 | FEAT-037 | I | Biến thể V6 (mục 2A.3), xuất 100 hộp; khóa khi chưa giải trình | 9,07%, "Vượt ngưỡng"; từ chối khóa; khóa được sau khi ghi giải trình |
| TC-CLS-18 | FR-COST-028 | FEAT-037 | U | Biến thể V7 (mục 2A.3) | 1,27% không cảnh báo; 3,23% cảnh báo; không chặn khóa |
| TC-CLS-19 | FR-COST-029 | FEAT-037 | I | Khoa XN không có số liệu xuất kho | Dòng "Chưa đối soát vật chất"; chỉ khóa được sau khi tài chính xác nhận kèm lý do |
| TC-CLS-39 | FR-OUT-012 | FEAT-037 | I | Phạm vi có một dịch vụ thiếu đơn giá, một thiếu sản lượng, một hệ thống thiếu kế hoạch chất lượng | Báo cáo liệt kê đúng ba dịch vụ với đúng loại thiếu |
| TC-CLS-40 | FR-COST-030 | FEAT-037 | I | Mở độ nhạy của GLU; đổi Qbn của GLU-A thành 6.000 | Giá thành thử khác gốc; lần tính giá và kết quả gốc không đổi |

#### 3.8.3 Dữ liệu gốc của phân hệ

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

#### 3.8.4 AI, quyền và các yêu cầu sửa

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

### 3.9 Bổ sung cho yêu cầu mức Must của bản 1.0 chưa có test case **[1.1]**

Bản 1.0 để lại 22 yêu cầu mức Must chưa có test case dự kiến. Mục này bổ sung đủ. Mã thuộc nhóm của yêu cầu, số nối tiếp số lớn nhất của bản 1.0; nhóm `ADM` là nhóm mới. Dữ liệu: bộ dữ liệu vàng ở mục 2.

| Mã | FR | FEAT | Loại | Tiền điều kiện và bước | Kết quả mong đợi |
| :-- | :-- | :-- | :-: | :-- | :-- |
| TC-ACC-05 | FR-ACC-001 | FEAT-001 | I | Khi chưa đăng nhập: gọi API lấy danh sách NC Technical Service và mở một trang Desk của Normcore | API trả lỗi chưa xác thực; trang chuyển về màn hình đăng nhập; không bản ghi nào được trả về |
| TC-SVC-04 | FR-SVC-003 | FEAT-005 | I | Gán khoa K01 rồi khoa K02 làm khoa thực hiện của dịch vụ X | Lưu được cả hai quan hệ dịch vụ - khoa; form dịch vụ liệt kê hai khoa |
| TC-PROC-09 | FR-PROC-007 | FEAT-006 | I | Gắn cho bước `S001` một trích dẫn "Theo hướng dẫn" tới một mục văn bản; gắn cho phần Chỉ định một trích dẫn "Khác biệt" kèm lý do | Mỗi trích dẫn lưu văn bản, mục, đoạn trích và loại quan hệ; bảng trích dẫn hiển thị đúng trích dẫn khi chọn bước hoặc phần đó |
| TC-RES-09 | FR-RES-001 | FEAT-009 | I | Tạo mặt hàng thiếu đơn vị tính; rồi tạo với đủ mã, tên, loại, đơn vị tính và không nhập số lần dùng | Lần đầu bị từ chối, nêu trường thiếu; lần sau lưu được với số lần dùng bằng 1 |
| TC-RES-10 | FR-RES-008 | FEAT-010 | I | Tạo phòng thiếu số giờ khai thác năm; rồi tạo phòng R1 với dữ liệu ở mục 2.1 | Lần đầu bị từ chối; R1 lưu được, đơn giá giờ phòng 25.000 |
| TC-RES-11 | FR-RES-015 | FEAT-011 | I | Tạo loại giá không chọn cấp phê duyệt; rồi tạo loại giá do bệnh viện quyết định, tắt kết cấu khấu hao, bật tích lũy | Lần đầu bị từ chối; lần sau lưu được với đúng ba lựa chọn đã nhập |
| TC-NORM-10 | FR-NORM-003 | FEAT-012 | I | Sửa một dòng vật tư và xóa đơn vị; sửa một dòng nhân lực và xóa số phút | Cả hai lần bị từ chối lưu, nêu trường thiếu |
| TC-NORM-11 | FR-NORM-008 | FEAT-012 | I | Chọn căn cứ "Định mức ban hành" cho dòng L03 kèm số văn bản tham chiếu; gửi qua API một giá trị căn cứ ngoài danh sách | Căn cứ và tham chiếu được lưu; giá trị ngoài năm giá trị cho phép bị từ chối |
| TC-NORM-12 | FR-NORM-009 | FEAT-012 | I | NC Clinician của khoa K01 xác nhận dòng L01 của bộ định mức nháp | Dòng L01 lưu người xác nhận và thời điểm; các dòng khác vẫn ở trạng thái chưa xác nhận |
| TC-TS-04 | FR-TS-001 | FEAT-014 | I | Tạo phiếu bấm giờ cho dịch vụ có quy trình đã ban hành gồm 4 bước, khoa K01 | Phiếu có đủ 4 bước với đúng mã bước và thứ tự của quy trình |
| TC-TS-05 | FR-TS-002 | FEAT-014 | I | Ghi một ca: bước `S002` có BS 1 người 20 phút, DD 1 người 20 phút, thiết bị EQ1 20 phút máy | Lưu theo bước: chức danh, số người, số phút nhân lực, số phút máy theo thiết bị; phiếu và ca không có trường định danh người bệnh |
| TC-ACCT-06 | FR-ACCT-006 | FEAT-016 | I | Chốt lần nhập của bộ dữ liệu vàng; rồi sửa số tiền một dòng | Trạng thái "Đã chốt"; tổng theo trung tâm và loại chi phí đúng bảng mục 2.1; sửa bị từ chối |
| TC-ACCT-07 | FR-ACCT-008 | FEAT-016 | I | Khai quy tắc phân bổ thiếu tiêu chí; khai quy tắc cấp 2 cho LABOR theo HEADCOUNT; khai quy tắc cấp 2 cho LABOR theo LABOR_MIN | Hai lần đầu bị từ chối (thiếu tiêu chí; HEADCOUNT chỉ dùng ở cấp 1 theo BR-COST-009); lần ba lưu được |
| TC-ACCT-08 | FR-ACCT-009 | FEAT-016 | I | Cài ứng dụng trên site trống; NC Finance đổi loại chi phí của một tài khoản trong bảng ánh xạ; nạp một tệp chi phí có tài khoản đó | Sau cài đặt có bảng ánh xạ mặc định của chế độ hành chính, sự nghiệp; lần nhập mới gán loại chi phí theo giá trị đã đổi. Nội dung bảng mặc định chờ TBD-03 |
| TC-ACCT-09 | FR-ACCT-010 | FEAT-016 | I | Nhập tiêu chí năm của trung tâm chi phí: K01 20 người, K02 30 người | Lưu theo trung tâm chi phí và năm; phân bổ cấp 1 của bộ dữ liệu vàng dùng tỷ lệ 20 ÷ 50 = 40% cho K01 |
| TC-COST-19 | FR-COST-001 | FEAT-015 | I | Tạo lần tính giá thiếu bộ tham số; tạo với lần nhập kế toán còn "Nháp"; rồi tạo với đủ năm tài chính, ngày tính giá, bộ tham số, lần nhập đã chốt, loại giá, phạm vi | Hai lần đầu bị từ chối; lần ba tạo được ở trạng thái "Nháp" |
| TC-BM-06 | FR-BM-001 | FEAT-026 | I | Tạo đơn vị tham chiếu thiếu tỉnh, thành phố; rồi tạo với đủ tên, tỉnh hoặc thành phố, loại hình, hạng | Lần đầu bị từ chối; lần sau lưu được |
| TC-ADM-01 | FR-ADM-001 | Foundations | I | Cài ứng dụng trên một site Frappe v15 trống | Có sẵn 10 vai trò `NC `, luồng duyệt quy trình và phương án giá, loại giá mẫu, mẫu in, mẫu lệnh AI mặc định; không cần thao tác tay |
| TC-ADM-02 | FR-ADM-002 | FEAT-004 | I | Tải tệp mẫu nhập liệu của danh mục mặt hàng; nhập lại chính tệp đó | Tệp Excel có đủ tiêu đề cột và một dòng ví dụ; nhập lại tạo được mặt hàng ví dụ, không có dòng lỗi |
| TC-ADM-03 | FR-ADM-003 | FEAT-002 | I | Đổi số ca bấm giờ tối thiểu từ 5 thành 3; mở kết quả bấm giờ của một dịch vụ có 3 ca | Trung vị được tính và không còn cảnh báo thiếu ca; không cần khởi động lại dịch vụ |
| TC-ADM-04 | FR-ADM-004 | FEAT-001 | I | Tạo khoa thiếu loại; rồi tạo khoa K03 loại Cận lâm sàng và gắn với một trung tâm chi phí | Lần đầu bị từ chối; lần sau lưu được, khoa liên kết với trung tâm chi phí |
| TC-ADM-05 | FR-ADM-005 | FEAT-001 | I | Xóa mặt hàng GANG khi mặt hàng đang được một dòng định mức tham chiếu | Từ chối xóa; thông báo nêu bản ghi đang tham chiếu |

## 4. Kịch bản nghiệm thu đầu cuối

Bốn kịch bản (bản 1.0: ba) chạy trên site staging với dữ liệu của khoa thí điểm, trước mỗi bản phát hành.

| Mã | Kịch bản | Use case | Điều kiện đạt |
| :-- | :-- | :-- | :-- |
| E2E-01 | Từ yêu cầu của bác sĩ đến quy trình ban hành | UC-004, UC-005, UC-006 | Một bác sĩ của khoa thí điểm tạo được dự thảo, chỉnh sửa, và quy trình được ban hành qua đủ ba cấp; bản PDF in đúng mẫu |
| E2E-02 | Từ quy trình ban hành đến lần tính giá đã khóa | UC-008, UC-009, UC-010, UC-011, UC-012 | Bộ định mức được khóa; lần tính giá chạy xong; bảng đối soát có giải trình; kết quả khớp bảng tính tay của chuyên viên tài chính trên 3 dịch vụ mẫu |
| E2E-03 | Từ lần tính giá đến hồ sơ phương án giá | UC-013, UC-014, UC-015, UC-016 | Có so sánh với ít nhất 3 đơn vị; một gợi ý được chấp nhận và giá được tính lại; phương án được duyệt; xuất đủ Phụ lục II, III, V và bảng giải trình |
| E2E-04 **[1.1]** | Từ hệ thống xét nghiệm đến giá một kết quả đã đối soát | UC-019, UC-020, UC-021, UC-022, UC-012, UC-023 | Khoa xét nghiệm thí điểm khai được hệ thống, kế hoạch chất lượng, hồ sơ tuân thủ và bộ định mức cho 3 xét nghiệm hóa sinh hoặc miễn dịch, trong đó ít nhất một xét nghiệm chạy trên hai máy (một máy mua, một máy đặt); nạp sản lượng và xuất kho 12 tháng; lần tính giá chạy xong; đối soát vật chất có giải trình và lần tính được khóa; giá một kết quả khớp bảng tính tay của chuyên viên tài chính |
