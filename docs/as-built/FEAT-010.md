# As-Built: FEAT-010 Thiết bị và phòng (gồm phần mở rộng 1.1)
- Phiên bản app 0.0.1; Dev: NORM-19; chưa qua kiểm định độc lập (QA điền ngày và người nghiệm thu)

## 1. Luồng nghiệp vụ đã xây
NC Resource Manager (hoặc NC Finance) khai báo loại thiết bị, thiết bị và phòng. Thiết bị chọn hình thức có máy (Mua, Thuê, Đặt theo hóa chất, Liên doanh, liên kết) và tiêu chí chia (Giờ kế hoạch, Số kết quả, Phút chiếm máy); trường bắt buộc đổi theo hai lựa chọn này (FR-RES-005, 019..022). Khai linh kiện lớn, tỷ lệ phân bổ theo khoa (tổng phải 100%, DI-10) và trường điện. Form hiện giá trị tạm tính theo ngày hôm nay: khấu hao/chi phí máy năm, đơn giá giờ máy, cảnh báo hết thời gian sử dụng theo lựa chọn ZERO/CONTINUE của bộ tham số mới nhất (FR-RES-006, 007). Phòng: đơn giá giờ phòng (FR-RES-008).

## 2. DocType tạo mới hoặc thay đổi
Mới: NC Equipment Type, NC Equipment, NC Room (đặt tên theo mã), bảng con NC Equipment Component, NC Equipment Allocation. Đổi: NC Costing Parameter Set thêm `expired_depreciation_mode` (ASM-078). Khấu hao và đơn giá giờ không lưu trên bản ghi (data-model 3.5).

## 3. API, tác vụ nền, hook, fixtures
`normcore/costing/resources.py` (hàm thuần: `machine_annual`, `equipment_annual`, `machine_hourly_rate`, `room_hourly_rate`, các hàm `validate_*`); `normcore/api/equipment.py` (`get_indicative_rate`, `get_room_rate`); `hooks.py` thêm ba DocType vào `check_not_referenced`; Workspace "Normcore" thêm lối tắt Thiết bị, Phòng. Không patch (ASM-081).

## 4. Quyền và luồng trạng thái
NC Equipment, NC Room: NC Finance, NC Resource Manager, NC Admin ghi; Clinician, Dept Head, Director, Consultant, Auditor đọc; Council, Document Controller không có quyền. NC Equipment Type: Resource Manager, Admin ghi; Finance cũng chỉ đọc. NC Admin xóa, chặn khi đang được tham chiếu. Không có luồng trạng thái.

## 5. Cấu hình cần thiết khi triển khai
`bench migrate` (DocType, Workspace), `bench build` (bản dịch). Bộ tham số hiện có hiểu là ZERO cho tới khi người dùng chọn.

## 6. Test case đã chạy và kết quả
TC-RES-03, TC-RES-04, TC-RES-10, TC-CLS-48, TC-CLS-49 (test cùng mã, đơn vị, golden và trên site); quyền với vai trò không có quyền và NC Auditor; xóa bị tham chiếu. Số liệu tổng và lệnh: `docs/features/FEAT-010/implementation-log.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- **Chưa kiểm trên trình duyệt:** preview không có site `normcore.test` (như FEAT-005); bố cục form, bảng con 1366 × 768 chưa xem thật.
- Chưa liên kết hồ sơ tuân thủ (FEAT-033, ASM-079); kiểm định năm là số nhập tay. Chưa tính linh kiện theo kết quả, giờ chạy, điện và chia theo số kết quả, phút (FEAT-036; TC-CLS-07/09/11/12/13). Dữ liệu cho FEAT-036 đã đủ: linh kiện, điện, tiêu chí chia, tỷ lệ khoa.
- Bộ nhập Excel thiết bị, phòng (FR-RES-012): `nc_equipment`, `nc_room` trong `core/import_sets.py` (ASM-084); chỉ trường phẳng, linh kiện và tỷ lệ khoa khai trên form.
- CF-003: diện tích phòng không bắt buộc theo TC-RES-10.
