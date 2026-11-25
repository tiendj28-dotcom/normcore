# FEAT-033 — Hồ sơ tuân thủ thiết bị — Thiết kế kỹ thuật

Issue NORM-26. Nguồn: `srs.md` FR-CMP-001, FR-CMP-005, FR-CMP-006 (phần dữ liệu), FR-CMP-007, FR-ADM-006, FR-NOTI-001; `use-cases.md` UC-020; `data-model.md` NC Equipment Type, NC Equipment Compliance, NC Settings, NC Department (`head_user`), mục 4; `ux-foundations.md` SCR-DSK-035, SCR-DSK-036, SCR-DSK-018 (liên kết hồ sơ), SCR-DSK-031 (số ngày nhắc); TC-CLS-27, TC-CLS-28. Phụ thuộc FEAT-010 (DONE, `docs/as-built/FEAT-010.md`).

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-CMP-001 | DocType NC Equipment Compliance, bắt buộc đủ bảy trường và tệp chứng từ; bộ nhập Excel `nc_equipment_compliance` (UC-020 luồng 1a) |
| FR-CMP-005 | Tác vụ hằng ngày: tính lại trạng thái, gửi thông báo trong ứng dụng cho NC Resource Manager và trưởng khoa của khoa quản lý thiết bị |
| FR-CMP-006 | **Chỉ phần dữ liệu**: hàm thuần "thiết bị có hồ sơ còn hạn tại ngày X" và "thiết bị bắt buộc thiếu hồ sơ còn hạn". Cảnh báo trên lần tính giá là FEAT-036 |
| FR-CMP-007 | Script Report SCR-DSK-036: hồ sơ hết hạn và sắp hết hạn theo khoa, cộng thiết bị bắt buộc chưa có hồ sơ còn hạn |
| FR-ADM-006 | NC Settings `compliance_reminder_days` (mặc định 30); đổi giá trị thì trạng thái mọi hồ sơ tính lại ngay. Cờ `compliance_required` của NC Equipment Type đã có từ FEAT-010, chỉ dùng, không đổi |

Không làm: FR-CMP-002..004 (quy chi phí hồ sơ về năm theo BR-CLS-011, phân bổ Theo giá trị tài sản / Gắn trực tiếp; golden `golden_cls.compliance_annual`) và cảnh báo FR-CMP-006 trên lần tính: FEAT-036. Không viết `core/notify.py` (FEAT-002); không thêm trường khác của NC Settings (FEAT-002).

## 2. DocType

Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1.

### 2.1 Mới — NC Equipment Compliance (mô-đun NC Costing)
Naming `HSTT-.YYYY.-.####` (naming series, data-model). Thứ tự trường:

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| record_code **[AMD-009]** | Mã hồ sơ | Data | | Duy nhất. Để trống thì lấy bằng `name`. Khóa của bộ nhập |
| equipment | Thiết bị | Link NC Equipment | Có | `in_list_view`, `in_standard_filter` |
| department **[AMD-009]** | Khoa quản lý | Link NC Department | | Chỉ đọc, `fetch_from: equipment.department`; `in_standard_filter`. Dùng cho lọc theo khoa và báo cáo |
| record_type | Loại hồ sơ | Select | Có | `Kiểm định` / `Hiệu chuẩn` / `Kiểm xạ` / `Giấy phép an toàn bức xạ` / `Khác` |
| cycle_months | Chu kỳ (tháng) | Int | Có | > 0 |
| provider | Đơn vị thực hiện | Data | Có | |
| cost_per_time | Chi phí mỗi lần | Currency | Có | Đã gồm thuế GTGT; ≥ 0 |
| performed_on | Ngày thực hiện | Date | Có | |
| expiry_date | Ngày hết hạn | Date | Có | > `performed_on`; `in_list_view` |
| attachment | Tệp chứng từ | Attach | Có | Tệp private (`/private/files/…`) |
| status | Trạng thái | Select, `read_only` | | `Còn hạn` / `Sắp hết hạn` / `Hết hạn`; `in_list_view`, `in_standard_filter`; không nhân bản (`no_copy`) |
| note | Ghi chú | Small Text | | |

Không có workflow. Trạng thái do hệ thống tính (mục 3), người dùng không sửa được.

`validate` (controller gọi `costing/compliance.validate_record` và `compute_status`):

| Điều kiện | Kết quả |
| :-- | :-- |
| Thiếu một trường BB, kể cả `attachment` | từ chối, nêu trường (TC-CLS-27 lần 1) |
| `cycle_months` ≤ 0 | từ chối "Chu kỳ (tháng) phải lớn hơn 0" (UC-020 1b) |
| `cost_per_time` < 0 | từ chối |
| `expiry_date` ≤ `performed_on` | từ chối |
| `attachment` không phải tệp private | từ chối "Tệp chứng từ phải là tệp riêng tư" |
| `record_code` trống | gán bằng `name` ở `before_insert`/`validate`; mã tự đặt trùng mẫu `HSTT-…` khác `name` bị từ chối (cùng cách `price_code`, ASM-093) |
| luôn | `status` = `compute_status(expiry_date, hôm nay, reminder_days)` |

### 2.2 Mới — NC Settings (Single, mô-đun NC Core) — ASM-099
Chỉ một trường của FEAT này: `compliance_reminder_days` (Int, nhãn "Số ngày nhắc hạn hồ sơ tuân thủ", `default` 30, ≥ 0). FEAT-002 thêm các trường còn lại của data-model sau. `on_update`: nếu `compliance_reminder_days` đổi thì gọi `refresh_all_statuses()` (mục 4) để trạng thái về đúng ngay (TC-CLS-28 bước cuối). Đọc giá trị qua một hàm `normcore.api.compliance.get_reminder_days()`: trống → 30.

### 2.3 Đổi
- **NC Equipment Type**: không đổi cấu trúc (`compliance_required` đã có từ FEAT-010). TBD-18: không fixture nào đánh dấu sẵn, cài trống (ASM-104).
- **NC Equipment**: thêm `links` (Connections) tới NC Equipment Compliance theo `equipment`, nhãn nhóm "Hồ sơ tuân thủ" — phần "liên kết đến hồ sơ tuân thủ" của SCR-DSK-018 mà ASM-079 để lại. Không thêm trường.
- **hooks.py**: `scheduler_events = {"daily": ["normcore.api.compliance.daily_job"]}`.

### 2.4 Quyền (data-model mục 4)
- NC Equipment Compliance — dòng "Loại thiết bị, hồ sơ tuân thủ": `R R - R W - R R W R` (Clinician R, Dept Head R, Council —, Finance R, Resource Manager W, Doc Controller —, Director R, Consultant R, Admin W + xóa, Auditor R). Không phạm vi khoa (dòng ma trận không ghi "(khoa)").
- NC Settings — không có dòng riêng; dùng dòng "Cấu hình AI, mẫu lệnh": Admin W, Auditor R, còn lại — (ASM-099). Máy chủ đọc giá trị không qua quyền người dùng.
- Script Report SCR-DSK-036: `roles` = mọi vai trò có R ở dòng trên (Clinician, Dept Head, Finance, Resource Manager, Director, Consultant, Admin, Auditor); `ref_doctype` NC Equipment Compliance.
- `scripts/check_conventions.py`: thêm `DOCTYPE_ROW` cho hai DocType mới; `DELETE_ALLOWED` NC Admin cho NC Equipment Compliance.

### 2.5 Migration
DocType mới, không có dữ liệu cũ: không cần patch (ASM-106). NC Equipment chỉ thêm `links`, không đổi cột.

## 3. Logic thuần — `normcore/costing/compliance.py` (không import `frappe`)

| Hàm | FR/BR | Mô tả |
| :-- | :-- | :-- |
| `reminder_days(value)` | FR-ADM-006 | `None`/trống → 30; < 0 → `ValueError` |
| `compute_status(expiry_date, today, reminder_days)` | FR-CMP-005, data-model `status` | `d = (expiry − today).days`; `d < 0` → `Hết hạn`; `0 ≤ d ≤ N` → `Sắp hết hạn`; `d > N` → `Còn hạn` (ASM-101) |
| `validate_record(values)` | FR-CMP-001, UC-020 1b | Trả danh sách lỗi tiếng Việt (bảng 2.1) |
| `is_valid_on(record, on)` | FR-CMP-006 | `performed_on ≤ on ≤ expiry_date` |
| `has_valid_record(records, on)` | FR-CMP-006 | Có ít nhất một hồ sơ `is_valid_on` |
| `missing_required(equipments, records_by_equipment, on)` | FR-CMP-006, FR-CMP-007, SCR-DSK-036 | Thiết bị có `compliance_required` của loại mà không có hồ sơ còn hạn tại `on` |
| `due_for_reminder(records, today, N)` | FR-CMP-005 | Hồ sơ có `compute_status` = `Sắp hết hạn` |
| `recipients(resource_managers, head_user)` | FR-CMP-005 | Hợp (không trùng, sắp xếp) người có vai trò NC Resource Manager và trưởng khoa; bỏ giá trị trống |
| `reminder_subject(record)` | FR-CMP-005 | Tiêu đề thông báo; chứa mã hồ sơ, thiết bị, ngày hết hạn (dd/mm/yyyy) — cũng là khóa chống gửi trùng (ASM-100) |
| `build_expiry_report(records, missing, on, N, department=None)` | FR-CMP-007 | Dòng báo cáo: chỉ `Hết hạn` và `Sắp hết hạn` tại `on`, cộng dòng `Thiếu hồ sơ còn hạn` cho thiết bị bắt buộc; sắp theo khoa, rồi Hết hạn → Sắp hết hạn → Thiếu, rồi `expiry_date` |

Không có phép tính tiền ở FEAT này; không đối chiếu golden. Độ phủ `costing/compliance.py` ≥ 90% (`normcore/tests/unit/test_compliance.py`).

## 4. API và tác vụ — `normcore/api/compliance.py`

| Hàm | Loại | Kết quả | Quyền |
| :-- | :-- | :-- | :-- |
| `get_reminder_days()` | nội bộ | Int | — |
| `refresh_all_statuses(today=None)` | nội bộ | số hồ sơ đổi trạng thái | — (chạy quyền hệ thống); cập nhật `status` bằng `frappe.db.set_value(..., update_modified=False)` |
| `send_reminders(today=None)` | nội bộ | số thông báo đã tạo | Tạo `Notification Log` (type `Alert`, `document_type`, `document_name`, `subject`, `from_user` Administrator) cho từng người nhận; bỏ qua nếu đã có Notification Log cùng `for_user`, `document_name`, `subject` (ASM-100) |
| `daily_job()` | scheduler daily | — | `refresh_all_statuses()` rồi `send_reminders()` |
| `run_compliance_check()` | `@frappe.whitelist()` | `{"updated": n, "notified": m}` | `frappe.has_permission("NC Equipment Compliance", "write")` bắt buộc, không thì `frappe.PermissionError` (NC Auditor, Finance bị từ chối). Nút "Kiểm hạn ngay" trên danh sách |

Người nhận: user `enabled` có vai trò NC Resource Manager (`Has Role`, bỏ Administrator, Guest) và `NC Department.head_user` của `NC Equipment.department` (nếu có, `enabled`).

**Report** `normcore/nc_costing/report/nc_compliance_expiry/` (Script Report, tên "NC Compliance Expiry", hiển thị qua `_()` "Báo cáo hạn hồ sơ tuân thủ"): `execute(filters)` đọc hồ sơ bằng `frappe.get_list` (theo quyền người xem), thiết bị bắt buộc, `get_reminder_days()`, rồi gọi `build_expiry_report`. Bộ lọc: `as_of` (Date, mặc định hôm nay, BB), `department` (Link NC Department), `status` (Select: trống / Hết hạn / Sắp hết hạn / Thiếu hồ sơ còn hạn). Cột: Khoa, Thiết bị, Loại thiết bị, Hồ sơ (Link), Loại hồ sơ, Đơn vị thực hiện, Ngày thực hiện, Ngày hết hạn, Còn (ngày), Trạng thái.

**Bộ nhập** `nc_equipment_compliance` trong `core/import_sets.py` (khung FEAT-004, không sửa khung), khóa `record_code` (ASM-103). Cột: `record_code` (BB), `equipment` (Link, BB), `record_type` (Select, BB), `cycle_months` (Int, BB), `provider` (BB), `cost_per_time` (Float, BB), `performed_on` (Date, BB), `expiry_date` (Date, BB), `attachment` (Data, BB — đường dẫn tệp private đã tải lên, ví dụ `/private/files/kd-tb01.pdf`), `note`. Không có cột `status`, `department`. Controller vẫn là nơi kiểm (tệp không tồn tại hoặc không private → lỗi dòng).

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | Tạo hồ sơ đủ trường nhưng không có tệp chứng từ: bị từ chối (`MandatoryError`/`ValidationError`); thêm tệp private: lưu được, `status` = `Còn hạn` (hết hạn sau hôm nay > 30 ngày) | TC-CLS-27 | FR-CMP-001 |
| 2 | Hồ sơ `expiry_date` = hôm nay + 20, N = 30; chạy `daily_job()`: `status` = `Sắp hết hạn`; có Notification Log cho người dùng NC Resource Manager và `head_user` của khoa quản lý thiết bị, liên kết tới hồ sơ; chạy lần hai không tạo thêm | TC-CLS-28 | FR-CMP-005, FR-NOTI-001 |
| 3 | Cùng dữ liệu: `execute({"as_of": hôm nay})` của báo cáo có dòng hồ sơ đó dưới khoa của thiết bị, trạng thái Sắp hết hạn; hồ sơ hết hạn cũng có; hồ sơ Còn hạn không có | TC-CLS-28 | FR-CMP-007 |
| 4 | Đổi `compliance_reminder_days` thành 10 và lưu NC Settings: hồ sơ trên về `Còn hạn` ngay, không cần chạy tác vụ | TC-CLS-28 | FR-ADM-006 |
| 5 | Chu kỳ 0, ngày hết hạn ≤ ngày thực hiện, chi phí âm, tệp public: từ chối | (đơn vị + tích hợp) | FR-CMP-001, UC-020 1b |
| 6 | `compute_status`, `is_valid_on`, `missing_required` đúng ở biên (d = N, d = 0, d = −1; ngày = ngày thực hiện, = ngày hết hạn) | (đơn vị) | FR-CMP-005, FR-CMP-006 |
| 7 | Thiết bị thuộc loại `compliance_required` không có hồ sơ còn hạn xuất hiện ở báo cáo với "Thiếu hồ sơ còn hạn"; loại không bắt buộc thì không | (tích hợp) | FR-CMP-006, FR-CMP-007 |
| 8 | Quyền: Resource Manager, Admin tạo/sửa được; Finance, Clinician chỉ đọc; NC Auditor và một vai trò không có quyền (NC Council) bị từ chối ghi, kể cả `run_compliance_check`; NC Settings chỉ Admin ghi, Auditor đọc | — | FR-ACC-002, FR-ACC-007 |
| 9 | Bộ nhập: tệp mẫu đúng cột; dòng thiếu tệp hoặc chu kỳ 0 thành lỗi dòng; dòng đủ tạo hồ sơ có trạng thái; chạy lại cùng tệp không tạo trùng | — | FR-CMP-001 (UC-020 1a) |

Tên test: `test_TC_CLS_27_thieu_chung_tu_bi_tu_choi`, `test_TC_CLS_28_nhac_han_bao_cao_va_doi_so_ngay` (một hoặc tách nhiều hàm cùng tiền tố `test_TC_CLS_28_`).

## 6. Giả định, sửa thiết kế và rủi ro
- **AMD-009**: thêm `record_code` (khóa bộ nhập) và `department` (fetch, lọc theo khoa) vào NC Equipment Compliance. Dev áp vào `data-model.md` ở FEAT này (tiền lệ AMD-008).
- **ASM-099**: tạo NC Settings sớm, chỉ trường `compliance_reminder_days`; quyền theo dòng "Cấu hình AI, mẫu lệnh".
- **ASM-100**: thông báo bằng Notification Log của Frappe (chưa có `core/notify.py`), người nhận, chống trùng; hồ sơ Hết hạn không gửi.
- **ASM-101**: quy tắc biên trạng thái và "còn hạn tại ngày X"; trạng thái tính lại khi lưu, hằng ngày và khi đổi số ngày nhắc; báo cáo tính tại ngày xem.
- **ASM-102**: ràng buộc thêm: ngày hết hạn sau ngày thực hiện, chi phí ≥ 0, tệp private; không ép ngày hết hạn = ngày thực hiện + chu kỳ.
- **ASM-103**: bộ nhập khóa `record_code`; tệp chứng từ nhập bằng đường dẫn tệp đã tải lên.
- **ASM-104**: TBD-18 cài trống.
- **ASM-105**: test cũ đếm DocType (`tests/test_permissions.py`, 27 → 29) và danh sách bộ nhập của Resource Manager (`api/test_importer.py`, thêm `nc_equipment_compliance`) phải cập nhật — **cần Quyết định Lead** trên NORM-26 theo luật cứng 1 trước khi Dev sửa.
- **ASM-106**: không viết patch.
- Rủi ro: FEAT-031 chạy song song (cùng nhóm 5a) cũng ghi `assumptions.md`, `vi.csv`, `check_conventions.py`, bảng đếm DocType; khi gộp giữ dòng cả hai bên và đánh lại số ASM/đếm. FEAT-002 sau này mở rộng NC Settings, có thể chuyển thông báo sang `core/notify.py`.
