# Normcore – Tóm tắt ý tưởng sản phẩm (13/11/2026)

Bản đầy đủ: doc "Normcore – Ý tưởng sản phẩm: Quy trình kỹ thuật, định mức KTKT và giá dịch vụ KCB có AI hỗ trợ" (https://claude.ai/artifact/TpmjuREF4XzkjGbu7UuV8y). Phân hệ E có doc riêng: "Normcore – Phân hệ E: Định mức KTKT và giá thành 1 test khối cận lâm sàng" (https://claude.ai/artifact/EqMcskhFMUiRkMrVLRihBu). Danh mục văn bản pháp lý đầy đủ (rà soát hiệu lực đến 13/11/2026): doc "Normcore – Danh mục văn bản pháp lý liên quan" (https://claude.ai/artifact/RfxKdqusHBLT3j3fN8LaSw). Tệp này chỉ ghi khung ý tưởng để các phiên làm việc sau bám theo.

Bộ tài liệu phân tích nghiệp vụ bàn giao cho dev (bản 1.0, 13/11/2026) nằm ở `claude/docs/`, bắt đầu từ `claude/docs/README.md`. Bản 1.0 đặc tả phân hệ A đến D; phân hệ E chưa được đặc tả (TBD-13 trong `claude/docs/srs.md`).

## Định vị
Phần mềm trên Frappe v15 đưa bệnh viện đi từ quy trình kỹ thuật (QTKT) được phê duyệt đến giá dịch vụ có đủ định mức KTKT và hồ sơ giải trình, trên một chuỗi dữ liệu liền mạch. Mỗi con số trong giá truy ngược được về một bước quy trình, một dòng định mức, một đơn giá có chứng từ hoặc một tiêu chí phân bổ từ sổ kế toán.

## Năm phân hệ
- A. Soạn QTKT với AI: AI rà soát hướng dẫn của Bộ Y tế + yêu cầu của bác sĩ, soạn dự thảo có dẫn nguồn; bác sĩ chỉnh; trưởng khoa, hội đồng chuyên môn, giám đốc duyệt. Quy trình lưu dạng có cấu trúc (bước, hoạt động, nguồn lực).
- B. Bóc tách định mức theo bước: nhân lực, thuốc/hóa chất/dịch truyền, vật tư, thiết bị, hạ tầng, điện nước và tiện ích, quản lý gián tiếp. AI đề xuất, người xác nhận từng dòng; thời gian phải bấm giờ thực tế.
- C. Tính giá thành: Giá = giá thành toàn bộ + tích lũy/lợi nhuận dự kiến + nghĩa vụ tài chính (TT 21/2024/TT-BYT, Điều 6). Tính từ dưới lên (định mức × đơn giá) và từ trên xuống (phân bổ từ số liệu kế toán), rồi đối soát ngược với tổng chi phí thực tế của khoa. Phép tính do bộ máy cố định thực hiện, không phải AI.
- D. So sánh và điều chỉnh: đối chiếu ít nhất 3 đơn vị tương đương, dữ liệu trong 24 tháng; gợi ý tăng/giảm theo cấu phần; thay đổi chạm bước chuyên môn phải quay lại phân hệ A.
- E. Định mức KTKT khối cận lâm sàng (bổ sung 13/11/2026): tính giá thành 1 kết quả xét nghiệm hoặc 1 ca chẩn đoán hình ảnh, nạp kết quả vào phân hệ C. Xem mục riêng bên dưới.

## Phân hệ E – khung ý tưởng
- Đơn vị tính: 1 kết quả trả cho người bệnh, không phải 1 test danh nghĩa trên hộp hóa chất. Đơn vị dữ liệu: "hệ thống xét nghiệm" = dịch vụ + máy + hóa chất + kế hoạch chất lượng.
- Năm cấp phát sinh chi phí: (1) theo test; (2) theo mẻ chạy; (3) theo ngày-máy; (4) theo kỳ, gắn thiết bị hoặc thông số; (5) theo khoa và toàn viện. Bộ máy quy mọi cấp về đồng/kết quả.
- Hệ số tiêu hao thực tế k = (test người bệnh + nội kiểm + chuẩn máy + chạy lại + ngoại kiểm) ÷ ((1 − hao hụt) × test người bệnh), lấy từ LIS và sổ nội kiểm.
- Danh mục gốc bắt buộc: dịch vụ CLS (mã TT 23), thiết bị (kèm hình thức có máy: mua, thuê, máy đặt theo hóa chất, liên kết), hệ thống xét nghiệm, hóa chất/chất chuẩn/vật liệu nội kiểm, vật tư, kế hoạch nội kiểm và chuẩn máy, chương trình ngoại kiểm, hồ sơ tuân thủ thiết bị (kiểm định, hiệu chuẩn, kiểm xạ, giấy phép, bảo trì), nhân lực, sản lượng kỳ. Mỗi đơn giá có chứng từ và ngày hiệu lực.
- Chẩn đoán hình ảnh: chia chi phí máy theo phút chiếm máy; bóng phát tia, heli, đầu dò tính theo tuổi thọ; thuốc cản quang có cờ "tính trong giá / thanh toán riêng".
- Ba đối soát trước khi duyệt: vật chất (định mức × sản lượng với xuất kho), tài chính (với sổ kế toán khoa), sản lượng (LIS/RIS với HIS).
- Quy tắc chống trùng/thiếu chính: máy đặt thì không tính khấu hao; hóa chất chạy nội kiểm chỉ nằm trong k; ống mẫu chia theo số xét nghiệm trên 1 ống; cảnh báo dịch vụ sản lượng thấp.
- Luôn hiển thị giá thành ở ba mức sản lượng: thực tế 12 tháng, kế hoạch, công suất.
- DocType dự kiến: Dịch vụ CLS, Thiết bị CLS, Hệ thống xét nghiệm, Nguồn giá, Kế hoạch nội kiểm và chuẩn máy, Chương trình ngoại kiểm, Hồ sơ tuân thủ thiết bị, Phiếu định mức CLS, Sản lượng kỳ, Lần tính giá thành.
- Thứ tự làm: hóa sinh và miễn dịch (30–50 dịch vụ, đi cùng MVP B + C) → các nhóm xét nghiệm còn lại, nối LIS → chẩn đoán hình ảnh, nối RIS/PACS → tính lại tự động khi có thầu mới.

## Căn cứ chính
Luật KCB 2023, NĐ 96/2023/NĐ-CP; TT 23/2024/TT-BYT (danh mục kỹ thuật); các QĐ hướng dẫn QTKT của Bộ Y tế theo chuyên khoa; TT 21/2024/TT-BYT (phương pháp định giá); TT 24/2024/TT-BTC (kế toán HCSN, bệnh viện công) và TT 99/2025/TT-BTC (kế toán doanh nghiệp, bệnh viện tư); NĐ 60/2021/NĐ-CP sửa bởi NĐ 111/2025/NĐ-CP.

Bổ sung cho phân hệ E: TT 21/2024 Phụ lục III có khoản "duy tu, bảo dưỡng, kiểm định, hiệu chuẩn tài sản" (phân bổ theo tổng giá trị tài sản), Phụ lục IV phân bổ theo thời gian nhân công và thời gian dùng máy; TT 10/2026/TT-BYT (tiêu chuẩn, định mức sử dụng máy móc, thiết bị chuyên dùng y tế, hiệu lực 01/07/2026, đơn vị công lập thuộc Bộ Y tế) làm tham chiếu công suất; TT 01/2013/TT-BYT và QĐ 2429/QĐ-BYT (nội kiểm, ngoại kiểm, chất lượng phòng xét nghiệm).

Cập nhật pháp lý ảnh hưởng tham số (rà soát 13/11/2026, chi tiết ở doc danh mục pháp lý): lương cơ sở 2.530.000 đ từ 01/7/2026 (NĐ 161/2026/NĐ-CP); phụ cấp PTTT, trực theo NĐ 192/2026/NĐ-CP (từ 15/7/2026, thay QĐ 73/2011/QĐ-TTg) và phụ cấp ưu đãi nghề theo NĐ 350/2026/NĐ-CP; TT 25/2026/TT-BYT cho Phụ lục 01 TT 23/2024 dùng đến 31/12/2027, Phụ lục 02 từ 01/01/2028; các tập Hướng dẫn QTKT mới áp dụng từ 01/01/2028; hao mòn, khấu hao khu vực công theo TT 141/2025/TT-BTC (thay TT 23/2023/TT-BTC từ năm tài chính 2026); kiểm định TBYT mua trước 01/7/2027 hoàn thành trước 01/01/2028; Luật Trí tuệ nhân tạo 134/2025/QH15 (01/3/2026), Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 + NĐ 356/2025/NĐ-CP (01/01/2026).

## Quyết định đã chốt (13/11/2026)
- Khách hàng đầu tiên: bệnh viện công (kế toán hành chính, sự nghiệp theo TT 24/2024/TT-BTC làm trước).
- Triển khai: ứng dụng Frappe v15 độc lập, không cần ERPNext.
- AI: để mở, đổi nhà cung cấp bằng cấu hình (lớp trung gian với bộ chuyển đổi theo giao thức).
- Bộ tài liệu bàn giao cho dev: bộ đầy đủ theo SDLC (SRS, use case, RTM, kiến trúc + ADR, mô hình dữ liệu, UX, kế hoạch build, test case).

## Lộ trình đề xuất
0. Chuẩn bị (bệnh viện và chuyên khoa thí điểm, nạp văn bản, mẫu số liệu kế toán) → 1. MVP phân hệ B + C, kèm phân hệ E cho hóa sinh và miễn dịch, xuất biểu TT 21 → 2. Phân hệ A và luồng duyệt; mở rộng E sang các nhóm xét nghiệm khác → 3. Phân hệ D; E cho chẩn đoán hình ảnh → 4. Kết nối HIS, LIS, RIS/PACS, kế toán, mở rộng toàn viện.

Kế hoạch build chi tiết của bộ tài liệu 1.0 (30 tính năng, 3 bản phát hành, chỉ gồm A đến D): `claude/docs/implementation-plan.md`. Trong kế hoạch đó, soạn quy trình thủ công và luồng duyệt nằm ở R1 vì định mức phải bóc từ quy trình đã ban hành.

## Câu hỏi chưa chốt
1. Loại giá ưu tiên: KCB theo yêu cầu, phương án giá trình cấp thẩm quyền, hay cả hai? (TBD-05)
2. Chuyên khoa thí điểm và số dịch vụ mẫu? (TBD-06)
3. Bán phần mềm hay công cụ nội bộ cho dịch vụ tư vấn định giá?
4. Đưa phân hệ E vào SRS bằng bản sửa đổi; E cho hóa sinh, miễn dịch có làm cùng R1 không? (TBD-13)
5. (E) Sản lượng dùng để tính giá: thực tế 12 tháng, kế hoạch được duyệt hay công suất máy?
6. (E) Bệnh viện thí điểm dùng máy mua hay máy đặt theo hóa chất là chính?
7. (E) LIS có xuất được số test nội kiểm, chuẩn máy, chạy lại không?
8. (E) Dịch vụ dạng bộ (tổng phân tích máu, điện giải đồ) tính theo cả bộ hay từng thông số? Xét nghiệm gửi ngoài có đưa vào E không?
9. (E) Khoản kiểm định, hiệu chuẩn: gắn trực tiếp vào thiết bị hay phân bổ theo tổng giá trị tài sản như Phụ lục III TT 21?

## Chưa đối chiếu toàn văn
Phụ lục IV, V của TT 21; TT 23/2024/TT-BYT; TT 99/2025/TT-BTC; TT 24/2024/TT-BTC (hệ thống tài khoản); các điều của Luật KCB về thẩm quyền định giá. Cho phân hệ E: phụ lục TT 10/2026/TT-BYT; quy định kiểm định, hiệu chuẩn thiết bị y tế và phương tiện đo; an toàn bức xạ (phí theo TT 74/2026/TT-BTC, các QCVN kiểm định X-quang, CT); quy định đấu thầu hóa chất kèm máy đặt. Danh sách việc cần đối chiếu tiếp (gồm số hiệu các văn bản tháng 6–7/2026 chưa xác định) nằm ở cuối doc danh mục pháp lý.
