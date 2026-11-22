# FEAT-010 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-018; `design.md`; technical-design mục 2–4. Form và danh sách chuẩn của Desk, không trang tùy biến. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `vi.csv`; nhãn DocType và thông báo máy chủ tiếng Việt. Chỉ dùng biến CSS và lớp `indicator-pill` của Desk, không mã màu cứng.

## SCR-DSK-018 Thiết bị và phòng
Hiện thực: List + Form chuẩn cho NC Equipment, NC Room, NC Equipment Type (tệp `nc_equipment.js`, `nc_equipment_list.js`; Room, Type dùng form chuẩn không JS).

**Danh sách NC Equipment**: cột Mã (ID), Tên, Khoa quản lý, Hình thức có máy, Tiêu chí chia. Bộ lọc chuẩn: khoa, hình thức, tiêu chí.

**Form NC Equipment** (bố cục): 1) Nhận diện: mã, tên, khoa, loại thiết bị. 2) Hình thức và tiêu chí chia: `acquisition_mode`, `allocation_basis`. 3) Giá trị: ngày đưa vào sử dụng, nguồn hình thành, nguyên giá, thời gian sử dụng, chi phí năm theo hợp đồng, giá trị ghi trên hợp đồng. 4) Bảo trì, kiểm định: bảo trì năm, "nhà cung cấp chịu bảo trì", kiểm định năm. 5) Giờ kế hoạch: giờ khai thác, hệ số sử dụng. 6) Điện (thu gọn): công suất chạy, chờ, giờ chạy, giờ chờ, cấp điện liên tục. 7) Linh kiện lớn (bảng). 8) Tỷ lệ theo khoa (bảng; trống = 100% cho khoa quản lý). 9) Giá trị tạm tính (HTML, chỉ đọc).

Trường đổi theo lựa chọn (`depends_on` và `mandatory_depends_on` để người dùng thấy sớm; máy chủ vẫn là nơi quyết):
- Mua: hiện và bắt buộc nguyên giá, thời gian sử dụng. Thuê, Liên doanh, liên kết: hiện và bắt buộc chi phí hợp đồng; hiện giá trị ghi trên hợp đồng. Đặt theo hóa chất: ẩn nguyên giá, hợp đồng; hiện "nhà cung cấp chịu bảo trì".
- Giờ kế hoạch: hiện và bắt buộc giờ khai thác, hệ số sử dụng; hai tiêu chí còn lại ẩn.

**Giá trị tạm tính**: khi mở form đã lưu, gọi `normcore.api.equipment.get_indicative_rate`; hiện khấu hao năm, đơn giá giờ máy, nhãn "tính theo ngày hôm nay"; thiết bị hết thời gian sử dụng có chỉ báo `orange` "Hết thời gian sử dụng" kèm lựa chọn bộ tham số đang dùng. Thiết bị mới: "Lưu để xem giá trị tạm tính". Tiêu chí khác Giờ kế hoạch: "Tính theo số kết quả/phút ở lần tính giá".

**Form NC Room**: mã, tên, khoa, diện tích, chi phí hạ tầng năm, giờ khai thác năm; dòng tạm tính đơn giá giờ phòng bằng JS thuần phép chia hiển thị (số do máy chủ là chuẩn: gọi `get_room_rate`).

| Trạng thái | Hiển thị |
| :-- | :-- |
| Rỗng | Trạng thái trống chuẩn của Desk |
| Đang tải, lỗi | Chuẩn của Desk; khung tạm tính hiện thông báo lỗi tiếng Việt |
| Không có quyền | Trang không đủ quyền của Desk |
| Chỉ đọc (NC Auditor, Clinician, Dept Head, Director, Consultant) | Form chỉ đọc, không nút lưu; khung tạm tính vẫn hiện |

Bàn phím: dùng chuẩn Desk (Ctrl+S lưu, Tab theo thứ tự trường). Kiểm 1366 × 768: bảng con cuộn trong form, mục điện thu gọn mặc định. Tương phản: chỉ lớp Desk.

API: `get_indicative_rate`, `get_room_rate` (thêm vào `api/equipment.py`).
