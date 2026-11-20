# Quy tắc tính, quy tắc kiểm tra và vector kiểm thử – Normcore Phân hệ E

> Phiên bản 1.0 · 13/11/2026 · Đi kèm docs/srs.md. Mã QT = quy tắc tính, KT = quy tắc kiểm tra, TV = vector kiểm thử.
> Mọi số trong mục 5 là số giả định để kiểm thử thuật toán, không phải giá thị trường. Các giá trị kỳ vọng đã được tính bằng mã (Decimal, làm tròn HALF_UP).

## 1. Ký hiệu

| Ký hiệu | Nghĩa | Nguồn dữ liệu |
| :-- | :-- | :-- |
| Qbn | Số kết quả trả trong kỳ của hệ thống xét nghiệm | CLS Volume Period.reported_results |
| Qnk, Qchuan, Qlai, Qngk | Số test nội kiểm, chuẩn máy, chạy lại, ngoại kiểm | CLS Volume Period |
| h | Tỷ lệ hao hụt (thể tích chết, hết hạn trên máy), 0 ≤ h < 1 | CLS Volume Period.wastage_rate |
| k | Hệ số tiêu hao thực tế | QT-02 |
| D | Số ngày chạy máy trong kỳ | CLS QC Plan.run_days_per_year |
| n_me | Số mẫu bình quân một mẻ | CLS Volume Period.avg_batch_size |
| P(i) | Đơn giá mặt hàng i theo đơn vị định mức | QT-01 |
| Qtb | Tổng kết quả trả của mọi dịch vụ chạy trên một thiết bị trong kỳ | Tổng Qbn theo thiết bị |
| Mtb | Tổng phút khai thác của thiết bị trong kỳ | CLS Volume Period.machine_minutes |
| m | Phút chiếm máy của dịch vụ | CLS Test System.machine_minutes_per_result |
| Z | Giá thành 1 kết quả trả | QT-15 |

Kỳ tính chuẩn là 12 tháng. Mọi chi phí “năm” hiểu là chi phí của kỳ tính.

## 2. Danh mục khoản mục chi phí

| Mã | Khoản mục | Cấp mặc định | Cấu phần TT 21 mặc định | Quy tắc |
| :-- | :-- | :-- | :-- | :-- |
| K01 | Vật tư lấy mẫu và tiền phân tích | 1 | VT | QT-12 |
| K02 | Hóa chất chính | 1 | VT | QT-03 |
| K03 | Vật tư trên máy | 1 | VT | QT-03 |
| K04 | Hóa chất phụ trợ | 3 | VT | QT-05 |
| K05 | Vật liệu nội kiểm | 3 | VT | QT-05 |
| K06 | Chất chuẩn | 4 | VT | QT-06 |
| K07 | Ngoại kiểm | 4 | DT | QT-07 |
| K08 | Khấu hao hoặc thuê máy | 4 | KH | QT-08 |
| K09 | Bảo trì, sửa chữa, linh kiện lớn | 4 | DT | QT-09 |
| K10 | Kiểm định, hiệu chuẩn, giấy phép | 4 | DT | QT-10 |
| K11 | Nhân lực trực tiếp | 1 và 2 | NC | QT-11 |
| K12 | Điện, nước, điều hòa | 3 | DN | QT-05 |
| K13 | Chất thải, an toàn, bảo hộ | 5 | DN | QT-13 |
| K14 | CNTT, trả kết quả, lưu mẫu | 5 | QL | QT-13 |
| K15 | Quản lý chất lượng và quản lý gián tiếp | 5 | QL | QT-13 |
| K16 | Vật tư và chứng theo mẻ chạy | 2 | VT | QT-04 |
| K17 | Thuốc cản quang và vật tư đặc thù | 1 | VT | QT-03, thường mang cờ Thanh toán riêng |

Cấu phần: NC nhân công; VT thuốc, hóa chất, vật tư; DN điện, nước và hậu cần; DT duy tu, bảo dưỡng, kiểm định, hiệu chuẩn; KH khấu hao; QL quản lý. Ánh xạ khoản mục sang cấu phần là dữ liệu cấu hình (NFR-LEG-001). Xếp ngoại kiểm vào DT là mặc định đề xuất, cần kế toán xác nhận.

Khoản mục bắt buộc theo nhóm: xét nghiệm gồm K01, K02, K05, K08, K10, K11, K12; chẩn đoán hình ảnh gồm K08, K09, K10, K11, K12.

## 3. Quy tắc tính

### QT-01 Đơn giá
1. Lấy các CLS Price Source của mặt hàng có trạng thái Đã xác minh và valid_from ≤ ngày tính ≤ valid_to (valid_to trống là không hạn).
2. Chọn nguồn có loại đứng trước trong thứ tự ưu tiên của CLS Settings (mặc định: trúng thầu, hợp đồng, hóa đơn, báo giá). Cùng loại thì lấy valid_from mới nhất.
3. Giá gốc: nếu cấu hình tính VAT vào chi phí và nguồn giá chưa gồm VAT thì `gia = unit_price × (1 + vat_rate)`; nếu nguồn đã gồm VAT thì `gia = unit_price`. Nếu cấu hình không tính VAT thì lấy giá chưa VAT.
4. `P(i) = gia ÷ pack_quantity`, với pack_quantity là số đơn vị định mức trong một đơn vị mua (ví dụ hộp 200 test).

### QT-02 Hệ số tiêu hao k
```
k = (Qbn + Qnk + Qchuan + Qlai + Qngk) ÷ ((1 − h) × Qbn)
```
- Thiếu số thực tế thì ước tính từ kế hoạch: `Qnk = số mức × số lần mỗi ngày × D`; `Qchuan = số lần chuẩn × số điểm × số lần lặp`; `Qngk = số đợt × số mẫu mỗi đợt`. Kết quả gắn nhãn Ước tính từ kế hoạch.
- k làm tròn 6 chữ số thập phân trước khi dùng.
- k chỉ áp cho dòng có cờ apply_k (mặc định bật với K02, K03).
- Chẩn đoán hình ảnh dùng cùng công thức với Qnk = Qchuan = Qngk = 0 và h = 0, tức `k = 1 + Qlai ÷ Qbn` (tỷ lệ chụp lại).

### QT-03 Chi phí cấp 1
```
C1 = Σ (dinh_muc_i × P(i) × k_i),  k_i = k nếu apply_k, ngược lại = 1
```
Chỉ lấy dòng Đã xác nhận và không mang cờ Thanh toán riêng.

### QT-04 Chi phí cấp 2 (mẻ chạy)
```
C2 = Σ (dinh_muc_me_i × P(i)) ÷ n_me
```
n_me ≤ 0 hoặc trống thì dòng bị lỗi tính (FR-CST-013).

### QT-05 Chi phí cấp 3 (ngày-máy)
- Vật liệu nội kiểm: `C = lượng mỗi lần × số mức × số lần mỗi ngày × D × P ÷ số thông số dùng chung ÷ Qbn`.
- Hóa chất phụ trợ và chi phí ngày khác của thiết bị: `C = chi phí ngày × D ÷ Qtb` (chia theo kết quả) hoặc `chi phí ngày × D ÷ Mtb × m` (chia theo phút). Cho phép nhập thẳng chi phí kỳ thay cho chi phí ngày × D.
- Điện: `chi phí ngày = (kW chạy × giờ chạy + kW chờ × giờ chờ) × đơn giá điện`, D = 365 nếu thiết bị cấp điện liên tục.

### QT-06 Chất chuẩn
```
C = chi phí chất chuẩn một lần × số lần chuẩn trong kỳ ÷ Qbn
```
Hóa chất tiêu hao khi chuẩn đã nằm trong k, không cộng ở đây.

### QT-07 Ngoại kiểm
```
C = (phí chương trình + phí vận chuyển) × ty_le_dich_vu ÷ Qbn
```
ty_le_dich_vu mặc định = 1 ÷ số dịch vụ tham gia; tổng tỷ lệ của một chương trình phải bằng 100%.

### QT-08 Chi phí máy
Chi phí máy của kỳ theo hình thức có máy:

| Hình thức | Chi phí kỳ |
| :-- | :-- |
| Mua | nguyên giá ÷ số năm khấu hao; bằng 0 nếu ngày tính sau ngày hết khấu hao |
| Thuê | tiền thuê của kỳ |
| Đặt theo hóa chất | 0 |
| Liên doanh liên kết | chi phí theo hợp đồng, nhập cho kỳ |

Chia cho dịch vụ sau khi nhân tỷ lệ phân bổ khoa của thiết bị:
```
theo kết quả: C = chi_phi_ky × ty_le_khoa ÷ Qtb
theo phút:    C = chi_phi_ky × ty_le_khoa ÷ Mtb × m
```

### QT-09 Bảo trì và linh kiện lớn
- Hợp đồng bảo trì: chi phí kỳ, chia như QT-08.
- Linh kiện tuổi thọ theo tháng: `chi phí kỳ = giá thay × 12 ÷ tuổi thọ tháng`, chia như QT-08.
- Linh kiện tuổi thọ theo số ca: `C = giá thay ÷ tuổi thọ số ca` cho mỗi kết quả.
- Linh kiện tuổi thọ theo giờ: `C = giá thay ÷ tuổi thọ giờ × m ÷ 60`.
- Trong khi thiết bị là máy đặt, các dòng K09 đánh dấu nhà cung cấp chịu bằng 0.

### QT-10 Hồ sơ tuân thủ
```
chi phí kỳ của hồ sơ = chi phí mỗi lần × 12 ÷ chu kỳ tháng
```
- Cách A, gắn trực tiếp: cộng các hồ sơ của thiết bị, chia như QT-08.
- Cách B, theo giá trị tài sản: `chi phí của thiết bị = Σ chi phí hồ sơ của khoa × nguyên giá thiết bị ÷ Σ nguyên giá thiết bị của khoa`, rồi chia như QT-08.

### QT-11 Nhân lực
```
don_gia_phut = chi phí năm của chức danh ÷ (giờ chuẩn năm × 60)
C = Σ theo công đoạn (phút mỗi mẫu + phút mỗi mẻ ÷ n_me) × don_gia_phut
```
Phút lấy trung bình cộng các phiếu bấm giờ còn hiệu lực của công đoạn.

### QT-12 Tiền phân tích
```
C = Σ (dinh_muc_ong_i × P(i)) ÷ số xét nghiệm bình quân trên một ống
```

### QT-13 Chi phí cấp 5
Hai chế độ, chọn theo khoản mục trong CLS Settings hoặc nhận từ Phân hệ C:
- Tỷ lệ: `C5 = ty_le × (C1 + C2 + C3 + C4)`.
- Đơn giá: `C5 = chi phí chung của khoa trong kỳ ÷ tổng kết quả trả của khoa`.

### QT-14 Dịch vụ nhiều hệ thống
```
Z_dich_vu = Σ (ty_trong_s × Z_s),  Σ ty_trong_s = 100%
```

### QT-15 Tổng hợp và làm tròn
1. Mọi phép tính trung gian giữ 6 chữ số thập phân, làm tròn HALF_UP.
2. `Z = C1 + C2 + C3 + C4 + C5`, làm tròn đến đồng.
3. Cấu phần: cộng các dòng theo cấu phần, làm tròn đến đồng từng cấu phần; nếu tổng các cấu phần lệch Z thì điều chỉnh phần lệch vào cấu phần lớn nhất.
4. Tính lặp cho ba kịch bản sản lượng.

### QT-16 Đối soát
```
vật chất:  lech = (xuất kho thực tế − lượng tính được) ÷ xuất kho thực tế
           lượng tính được của mặt hàng = Σ theo dịch vụ (dinh_muc × k × Qbn) + lượng theo mẻ, ngày, kỳ
tài chính: lech = (chi phí thực tế của khoa − Σ Z_cau_phan × Qbn) ÷ chi phí thực tế, theo từng cấu phần
sản lượng: lech = (Qbn − số dịch vụ HIS) ÷ số dịch vụ HIS
```
So sánh trị tuyệt đối của lech với ngưỡng trong CLS Settings. Ví dụ: lượng tính được 13.298,964 test, xuất kho 14.000 test, lệch 5,0074%, vượt ngưỡng 5%, phải giải trình.

## 4. Quy tắc kiểm tra

Mức: Chặn (không cho đi tiếp), Cảnh báo (cho đi tiếp, ghi vào thuyết minh), Lọc (tự loại khỏi phép tính).

| Mã | Quy tắc | Mức | Thời điểm | FR |
| :-- | :-- | :-- | :-- | :-- |
| KT-01 | Máy đặt: khóa K08 và các dòng K09 do nhà cung cấp chịu ở giá trị 0 | Chặn | Lưu phiếu, chạy tính | FR-EQP-003 |
| KT-02 | Thiết bị Mua thiếu nguyên giá, ngày sử dụng hoặc thời gian khấu hao | Chặn | Chạy tính | FR-EQP-006 |
| KT-03 | Mặt hàng không có nguồn giá còn hiệu lực | Chặn | Trình hội đồng | FR-PRC-004 |
| KT-04 | Nguồn giá không có tệp chứng từ thì không được Đã xác minh | Chặn | Xác minh nguồn giá | FR-PRC-005 |
| KT-05 | Tổng tỷ lệ phân bổ khoa của thiết bị khác 100% | Chặn | Lưu thiết bị | FR-EQP-008 |
| KT-06 | Tổng tỷ trọng hệ thống xét nghiệm của dịch vụ khác 100% | Chặn | Chạy tính | FR-SYS-003 |
| KT-07 | Dòng K11 không có phiếu bấm giờ | Chặn | Gửi duyệt phiếu | FR-LAB-004 |
| KT-08 | Phiếu thiếu khoản mục bắt buộc của nhóm | Chặn | Gửi duyệt phiếu | FR-NRM-003 |
| KT-09 | Dòng mang cờ Thanh toán riêng | Lọc | Chạy tính | FR-NRM-004 |
| KT-10 | Có K01 mà chưa khai số xét nghiệm bình quân trên một ống | Chặn | Gửi duyệt phiếu | FR-NRM-006 |
| KT-11 | Dòng K05 chứa mặt hàng loại hóa chất chính | Chặn | Lưu dòng | FR-NRM-009 |
| KT-12 | Dòng ở trạng thái Đề xuất hoặc Từ chối | Lọc | Chạy tính | FR-AI-004 |
| KT-13 | Hệ thống xét nghiệm nhóm xét nghiệm không có kế hoạch nội kiểm | Cảnh báo | Lưu phiếu | FR-QC-006 |
| KT-14 | Thiết bị loại bắt buộc không có hồ sơ tuân thủ còn hạn | Cảnh báo | Chạy tính | FR-CMP-004 |
| KT-15 | Qbn của kịch bản chính bằng 0 hoặc trống | Lọc, có liệt kê | Chạy tính | FR-VOL-003 |
| KT-16 | Qbn ÷ 365 × hạn dùng sau mở (ngày) nhỏ hơn số test danh nghĩa một hộp | Cảnh báo | Chạy tính | FR-VOL-004 |
| KT-17 | Dòng đối soát vượt ngưỡng mà chưa có giải trình | Chặn | Trình hội đồng | FR-REC-004 |

## 5. Vector kiểm thử

Dữ liệu chung của TV-01 đến TV-13 và TV-16: một xét nghiệm miễn dịch trên máy A; máy A chạy tổng cộng 300.000 kết quả mỗi năm, chia chi phí máy theo số kết quả, tỷ lệ khoa 100%.

| Mã | Quy tắc | Đầu vào | Kỳ vọng (đồng cho 1 kết quả, trừ khi ghi khác) |
| :-- | :-- | :-- | :-- |
| TV-01 | QT-01, 02, 03 | Hộp 200 test giá 6.000.000 đã gồm VAT; định mức 1 test; Qbn 12.000; Qnk 600; Qchuan 48; Qlai 240; Qngk 12; h 3% | P = 30.000; k = 1,108247; chi phí 33.247,41 |
| TV-02 | QT-02, 03 | Như TV-01 nhưng Qbn 1.200; Qlai 24 | k = 1,618557; chi phí 48.556,71 |
| TV-03 | QT-03 | Vật tư trên máy 800 đồng mỗi test, apply_k, k của TV-01 | 886,5976 |
| TV-04 | QT-05 | Hóa chất phụ trợ của máy 90.000.000 mỗi năm; Qtb 300.000 | 300 |
| TV-05 | QT-05 | Nội kiểm 0,1 mL mỗi lần, 2 mức, 1 lần mỗi ngày, 300 ngày; lọ 5 mL giá 1.200.000; 20 thông số dùng chung; Qbn 12.000 | Chi phí năm 14.400.000; 60 |
| TV-06 | QT-06 | Chất chuẩn 400.000 mỗi lần, 12 lần mỗi năm; Qbn 12.000 | 400 |
| TV-07 | QT-07 | Phí chương trình 14.000.000, vận chuyển 1.000.000, 10 dịch vụ chia đều; Qbn 12.000 | 125 |
| TV-08 | QT-08 | Mua: nguyên giá 3.600.000.000, khấu hao 8 năm; Qtb 300.000. Biến thể: cùng máy nhưng hình thức Đặt theo hóa chất | Mua 1.500; Đặt 0 |
| TV-09 | QT-09 | Hợp đồng bảo trì 180.000.000 mỗi năm; Qtb 300.000 | 600 |
| TV-10 | QT-10 cách A | Hiệu chuẩn 6.000.000 chu kỳ 12 tháng; kiểm định 9.000.000 chu kỳ 24 tháng; Qtb 300.000 | Chi phí năm 10.500.000; 35 |
| TV-11 | QT-11 | Chức danh 211.200.000 mỗi năm, 1.760 giờ; 1,5 phút mỗi mẫu; 20 phút mỗi mẻ, 40 mẫu mỗi mẻ; 0,3 phút duyệt kết quả | Đơn giá phút 2.000; 2,3 phút; 4.600 |
| TV-12 | QT-12 | Vật tư một ống mẫu 6.000; 4 xét nghiệm mỗi ống | 1.500 |
| TV-13 | QT-05 điện | 1,2 kW chạy 10 giờ, 0,3 kW chờ 14 giờ; 365 ngày; 2.500 đồng mỗi kWh; Qtb 300.000 | 16,2 kWh mỗi ngày; 14.782.500 mỗi năm; 49,275 |
| TV-14 | QT-08, 09, 10 theo phút | Máy CT: khấu hao 1.500.000.000; bảo trì 600.000.000; bóng phát tia 1.800.000.000 tuổi thọ 36 tháng; tuân thủ 30.000.000; Mtb 135.000 phút; 9.000 ca | Chi phí năm 2.730.000.000; 20.222,222222 mỗi phút; ca 10 phút 202.222; ca 20 phút 404.444; nếu chia theo ca 303.333 |
| TV-15 | QT-14 | Hệ thống A tỷ trọng 60% giá thành 40.000; hệ thống B tỷ trọng 40% giá thành 46.000 | 42.400 |
| TV-16 | QT-13, 15 | Cộng TV-01, 03, 04, 05, 06, 07, 08 (Mua), 09, 10, 11, 12, 13 và cấp 5 theo đơn giá 3.000 | Z = 46.303 (trước làm tròn 46.303,2826). Cấu phần: NC 4.600; VT 36.394; DN 49; DT 760; KH 1.500; QL 3.000 |

Mã sinh các giá trị kỳ vọng nằm ở scripts/vectors.py; dev đưa thành kiểm thử đơn vị của bộ máy tính (NFR-MNT-001, NFR-REL-002).

## 6. Điểm cần nghiệp vụ xác nhận

- Thiết bị hết thời gian khấu hao: QT-08 đặt khấu hao bằng 0. Một số đơn vị vẫn muốn tính hao mòn để tái đầu tư; nếu có, cần thêm tham số.
- Ánh xạ K07 ngoại kiểm sang cấu phần DT.
- Cách chia chi phí vật liệu nội kiểm dùng chung: chia đều theo số thông số (mặc định) hay theo sản lượng từng thông số.
- Chế độ mặc định của chi phí cấp 5 khi Phân hệ C chưa có: tỷ lệ hay đơn giá.
