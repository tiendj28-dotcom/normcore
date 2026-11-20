# Design: Normcore (quy ước giao diện)

> Status: Draft · Version: 1.1 · Last updated: 2026-11-13
> Nguồn gốc: hệ thiết kế có sẵn của Frappe Desk v15 (khung thành phần bắt buộc theo ràng buộc C-01 và ADR-010). Tệp này không định nghĩa bộ token riêng và không có `tokens.json`: giá trị màu, chữ, khoảng cách lấy từ biến CSS của Desk tại thời điểm chạy.
> Khoảng trống đã biết: chưa có nhận diện thương hiệu riêng (UXQ-01); chưa có mẫu bản in quy trình (TBD-04).
> Bản 1.1 thêm nhãn trạng thái và thành phần của phân hệ E (cận lâm sàng). Phần thêm mang nhãn **[1.1]**.

## 1. Hướng thị giác

Giao diện làm việc trung tính của Desk. Normcore không thêm màu, phông hay bo góc riêng. Mục tiêu là người dùng Frappe không thấy khác biệt giữa form chuẩn và các trang tùy biến (ba trang ở bản 1.0; **[1.1]** thêm trang nhẹ phân tích độ nhạy).

## 2. Giá trị thiết kế

Chỉ dùng biến CSS của Desk trong mã giao diện tùy biến; không viết mã màu cứng.

| Vai trò | Biến của Desk |
| :-- | :-- |
| Chữ chính, chữ phụ | `--text-color`, `--text-muted` |
| Nền trang, nền thẻ | `--bg-color`, `--card-bg` |
| Đường viền | `--border-color` |
| Nền nhấn nhẹ (dòng đề xuất) | `--bg-light-gray` hoặc biến tương đương của bản Desk đang dùng |
| Màu chính của nút | `--primary` |
| Bo góc, khoảng cách | `--border-radius`, `--padding-sm`, `--padding-md`, `--padding-lg` |

Tên biến cần được đối chiếu với bản Frappe v15 thực tế khi dựng trang đầu tiên; nếu một biến không tồn tại, dùng lớp tiện ích tương ứng của Desk.

## 3. Thành phần và trạng thái

**Nhãn trạng thái (indicator pill của Desk).**

| Trạng thái | Màu indicator |
| :-- | :-- |
| Nháp, Đề xuất, Chưa lập | `gray` |
| Chờ trưởng khoa duyệt, Chờ hội đồng thẩm định, Chờ ban hành, Chờ khoa xác nhận, Chờ phê duyệt, Đang lập, Đang tính | `orange` |
| Đã xác nhận chuyên môn, Đã tính, Đã duyệt nội bộ chờ trình | `blue` |
| Đã ban hành, Đã khóa, Đã chốt, Đã duyệt, Đã xác nhận, Còn hiệu lực; **[1.1]** Đang dùng, Còn hạn, Đã xác minh, Đã đối soát | `green` |
| Đã thay thế, Hết hiệu lực, Loại bỏ; **[1.1]** Ngừng dùng | `darkgrey` |
| Lỗi, Tính lỗi, Đã thu hồi, Vượt ngưỡng; **[1.1]** Hết hạn | `red` |
| Cần rà soát, Cần cập nhật, Cảnh báo, Chưa hiệu lực; **[1.1]** Sắp hết hạn, Chưa xác minh, Chưa đối soát, Ước tính từ kế hoạch, Sản lượng thấp | `yellow` |

**[1.1]** "Hết hạn" (hồ sơ tuân thủ của thiết bị, màu đỏ) khác "Hết hiệu lực" (văn bản, màu xám đậm): hồ sơ hết hạn là việc phải xử lý, văn bản hết hiệu lực là trạng thái lưu trữ.

**Nhãn quan hệ trích dẫn.** "Theo hướng dẫn": `green`. "Khác biệt": `orange`. "Chưa có căn cứ": `red`.

**Dòng đề xuất của AI.** Nền nhấn nhẹ, nhãn "Đề xuất" màu `purple`, hai nút nhỏ "Chấp nhận" và "Bỏ". Sau khi chấp nhận, dòng trở về dạng thường. **[1.1]** Dùng cùng kiểu này cho đề xuất định mức và kế hoạch chất lượng lấy từ tài liệu của hãng.

**Bản ghi chỉ đọc.** Dải thông báo ở đầu form: "Bản ghi đã <trạng thái>, không sửa được. <Hành động tạo phiên bản mới>."

**Lưới định mức.** Hàng nhóm theo bước có nền nhấn nhẹ và tổng chi phí của bước ở cuối hàng. Cột số căn phải, phông số đơn cách của Desk. Ô sửa được có viền khi đưa chuột tới; ô chỉ đọc không có viền. **[1.1]** Cột cấp phát sinh là ô chọn; ô "nhân k" là ô đánh dấu, vô hiệu ở dòng không phải Theo kết quả loại thuốc, vật tư. Hàng khoản mục bắt buộc chưa có lượng có nền nhấn nhẹ và nhãn `yellow` "Chưa có lượng".

**Khối "k được tính thế nào" [1.1].** Một hàng năm ô số (kết quả trả, nội kiểm, chuẩn máy, chạy lại, ngoại kiểm), tiếp theo là tỷ lệ hao hụt và giá trị k với 6 chữ số thập phân. Ô nào lấy từ kế hoạch thay cho số thực tế thì mang nhãn `yellow` "Ước tính từ kế hoạch". Khối chỉ đọc; không có nút sửa.

**Nhãn cấp phát sinh [1.1].** Chữ thường, không màu: Theo kết quả, Theo ống mẫu, Theo mẻ, Theo ngày-máy, Theo kỳ. Ở bảng giải trình, mẫu số đứng ngay sau nhãn, ví dụ "Theo mẻ · chia 40".

**Kết quả thử [1.1].** Trang phân tích độ nhạy có dải thông báo cố định "Kết quả thử, không lưu" ở đầu trang; cột giá thành thử dùng nền nhấn nhẹ để khác cột giá thành gốc.

**Trạng thái của mọi thành phần tương tác:** thường, đưa chuột tới, đang chọn bằng bàn phím (có viền focus nhìn thấy), vô hiệu, đang tải.

## 4. Quy tắc tiếp cận

- Mọi thao tác trên các trang tùy biến làm được bằng bàn phím: Tab để di chuyển, Enter để mở sửa, Esc để hủy.
- Tương phản chữ trên nền tối thiểu 4,5:1 [NFR-USE-004].
- Màu không phải kênh duy nhất: mọi nhãn màu đều có chữ.
- Vùng chạm trên phiếu bấm giờ tối thiểu 44 px [NFR-USE-003].

## 5. Câu chữ

- Số: `1.234.567`; tiền: thêm ` đ`; ngày: `dd/mm/yyyy` [NFR-LOC-001].
- **[1.1]** Hệ số k hiển thị 6 chữ số thập phân (`1,108247`); đơn giá một đơn vị định mức hiển thị 4 chữ số thập phân khi có phần lẻ.
- Nút: động từ ngắn. Hộp xác nhận: nêu hệ quả ("Sau khi ban hành, nội dung phiên bản này không sửa được.").
- Lỗi kiểm tra: liệt kê từng lỗi, mỗi lỗi một dòng, có liên kết tới bước hoặc dòng sai.
- Trạng thái trống: một câu nói màn hình này dùng để làm gì và một nút hành động đầu tiên.

## 6. Nên và không nên

| Nên | Không nên |
| :-- | :-- |
| Dùng form, list, report chuẩn khi đủ dùng | Viết trang tùy biến cho việc form chuẩn làm được |
| Dùng indicator và hộp thoại của Desk | Tự tạo kiểu nhãn, kiểu hộp thoại mới |
| Hiển thị nguồn của mọi con số | Hiển thị tổng mà không có đường xuống chi tiết |
| Phân biệt rõ đề xuất của AI | Trộn nội dung AI chưa duyệt với nội dung đã duyệt |
| **[1.1]** Ghi rõ số nào là ước tính từ kế hoạch | Hiển thị số ước tính giống số thực tế |

## 7. Tham chiếu nhanh cho người viết mã giao diện

1. Trang tùy biến: Desk Page, Vue 3, gọi `frappe.call` tới API whitelisted; không ghi thẳng DocType từ trình duyệt.
2. Màu và khoảng cách: chỉ biến CSS của Desk.
3. Nhãn trạng thái: bảng ở mục 3.
4. Mọi chuỗi hiển thị bọc bằng hàm dịch `__()` và có bản tiếng Việt.
5. Kiểm tra trên màn hình 1366 × 768 và máy tính bảng 768 px bề ngang.
