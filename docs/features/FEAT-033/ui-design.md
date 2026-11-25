# FEAT-033 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-035, SCR-DSK-036, SCR-DSK-018 (liên kết hồ sơ), SCR-DSK-031 (số ngày nhắc); `design.md`; technical-design mục 2–4. Chỉ dùng List, Form, Script Report chuẩn của Desk, không trang Vue. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `vi.csv`; nhãn DocType, thông báo máy chủ tiếng Việt. Màu trạng thái dùng lớp `indicator-pill` của Desk (`green`, `orange`, `red`), không mã màu cứng.

## SCR-DSK-035 Hồ sơ tuân thủ thiết bị (List + Form NC Equipment Compliance)
Tệp: `nc_equipment_compliance.js`, `nc_equipment_compliance_list.js`.

**Danh sách**: cột ID, Thiết bị, Loại hồ sơ, Ngày hết hạn, Trạng thái. Bộ lọc chuẩn (`in_standard_filter`): Khoa quản lý, Trạng thái, Loại hồ sơ, Thiết bị. `get_indicator`: Còn hạn → `green`, Sắp hết hạn → `orange`, Hết hạn → `red`. Nút "Check expiry now" ("Kiểm hạn ngay") chỉ hiện khi `frappe.model.can_write("NC Equipment Compliance")`; gọi `normcore.api.compliance.run_compliance_check`, xong thì báo "Updated {0} records, sent {1} notifications" và làm mới danh sách. Nút "Import from Excel" mở trang `import-excel` (AMD-002) với bộ `nc_equipment_compliance`, theo cách các danh sách FEAT-010 đang làm.

**Form** (bố cục):
1. Nhận diện: `record_code`, `equipment`, `department` (chỉ đọc) | `record_type`, `status` (chỉ đọc).
2. Thực hiện: `provider`, `cost_per_time` | `performed_on`, `cycle_months`, `expiry_date`.
3. Chứng từ: `attachment`, `note`.

Tương tác JS:
- Khi đổi `performed_on` hoặc `cycle_months` mà `expiry_date` đang trống: điền gợi ý `performed_on + cycle_months tháng` (`frappe.datetime.add_months`); người dùng sửa được (ASM-102).
- Tiêu đề form có chỉ báo trạng thái (cùng màu danh sách) và dòng phụ "Expires in {0} days" / "Expired {0} days ago" tính phía client chỉ để hiển thị.
- Tệp chứng từ: trường Attach chuẩn; hộp tải lên mặc định Private. Máy chủ từ chối tệp public (thông báo tiếng Việt).

## SCR-DSK-036 Báo cáo hạn hồ sơ tuân thủ (Script Report "NC Compliance Expiry")
Tệp: `nc_compliance_expiry.py`, `.js`, `.json` trong `normcore/nc_costing/report/nc_compliance_expiry/`.
- Bộ lọc: Ngày xem (`as_of`, mặc định hôm nay, BB), Khoa, Trạng thái (Hết hạn / Sắp hết hạn / Thiếu hồ sơ còn hạn).
- Cột: Khoa, Thiết bị, Loại thiết bị, Hồ sơ (Link), Loại hồ sơ, Đơn vị thực hiện, Ngày thực hiện, Ngày hết hạn, Còn (ngày), Trạng thái. `formatter` tô ô Trạng thái theo chỉ báo trên; dòng "Thiếu hồ sơ còn hạn" để trống các cột hồ sơ.
- Dòng tóm tắt (`report_summary`): số Hết hạn, số Sắp hết hạn, số thiết bị thiếu hồ sơ, và "Reminder days: {0}".
- Xuất Excel/in dùng chức năng chuẩn của Report.

## SCR-DSK-018 (bổ sung) — Form NC Equipment
Mục Connections (`links` của DocType) có nhóm "Hồ sơ tuân thủ", đếm và mở danh sách hồ sơ lọc theo thiết bị, nút "+" tạo hồ sơ điền sẵn thiết bị. Không đổi bố cục khác.

## SCR-DSK-031 (phần FEAT này) — NC Settings
Form Single chuẩn, một mục "Hồ sơ tuân thủ" có `compliance_reminder_days` với mô tả "Số ngày trước ngày hết hạn bắt đầu nhắc. Đổi giá trị thì trạng thái hồ sơ được tính lại ngay." Cờ "Bắt buộc có hồ sơ tuân thủ" vẫn sửa trên form NC Equipment Type (đã có). Lối vào: Workspace normcore, thêm liên kết "Hồ sơ tuân thủ", "Báo cáo hạn hồ sơ tuân thủ", "Tham số vận hành".

## Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Rỗng | Danh sách: trạng thái trống chuẩn, nút tạo mới. Báo cáo: "Không có hồ sơ hết hạn hoặc sắp hết hạn" (thông báo trống chuẩn của Report) |
| Đang tải, lỗi | Chuẩn của Desk; lỗi máy chủ hiện bằng `frappe.msgprint` tiếng Việt |
| Không có quyền | Trang không đủ quyền của Desk (Council, Doc Controller với hồ sơ; mọi vai trò trừ Admin, Auditor với NC Settings) |
| Chỉ đọc (NC Auditor, Clinician, Dept Head, Finance, Director, Consultant) | Form chỉ đọc, không nút lưu, không nút "Kiểm hạn ngay", không nút nhập; báo cáo xem được |
| Còn hạn / Sắp hết hạn / Hết hạn | Chỉ báo `green` / `orange` / `red` ở danh sách, form, báo cáo |
| Thiết bị bắt buộc chưa có hồ sơ | Dòng "Thiếu hồ sơ còn hạn" (`red`) trong báo cáo |

Bàn phím: chuẩn Desk (Ctrl+S lưu, Ctrl+B tạo mới, Tab theo thứ tự trường). 1366 × 768: form hai cột, báo cáo 10 cột cuộn ngang trong khung Report. Tương phản (NFR-USE-004): chỉ lớp Desk. Ngày dd/mm/yyyy, tiền theo NFR-LOC-001 (định dạng hệ thống).

API: `normcore.api.compliance.run_compliance_check`; báo cáo `execute`; bộ nhập qua `normcore.api.importer` sẵn có.
