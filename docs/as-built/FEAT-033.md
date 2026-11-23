# As-Built FEAT-033 — Hồ sơ tuân thủ thiết bị

Issue NORM-26. FR: FR-CMP-001, FR-CMP-005, FR-CMP-006 (phần dữ liệu), FR-CMP-007, FR-ADM-006. UC-020, SCR-DSK-035, SCR-DSK-036. TC-CLS-27, TC-CLS-28.
Giới hạn: giao diện chưa xem bằng trình duyệt (chỉ kiểm tệp JS bằng test quy ước và `bench build`); chưa chạy tác vụ hằng ngày bằng scheduler thật, chỉ gọi `daily_job()` trong test.

## Đã làm
- DocType mới: NC Equipment Compliance (naming `HSTT-{YYYY}-{####}`, bảy trường bắt buộc kể cả tệp chứng từ private, `record_code` và `department` theo AMD-009, `status` hệ thống tính); NC Settings (Single, chỉ `compliance_reminder_days`, mặc định 30, ASM-099). NC Equipment có thêm nhóm Connections "Hồ sơ tuân thủ".
- Logic thuần `normcore/costing/compliance.py` (không import `frappe`, độ phủ 98%): trạng thái theo ASM-101, kiểm hồ sơ, "còn hạn tại ngày X", thiết bị bắt buộc thiếu hồ sơ, người nhận, tiêu đề thông báo, dòng báo cáo.
- `normcore/api/compliance.py`: `refresh_all_statuses`, `send_reminders` (Notification Log, chống trùng theo người nhận + hồ sơ + tiêu đề), `daily_job` (khai báo ở `hooks.py` `scheduler_events`), `run_compliance_check` (cần quyền ghi hồ sơ). Đổi số ngày nhắc ở NC Settings thì trạng thái tính lại ngay.
- Script Report "NC Compliance Expiry" (SCR-DSK-036), bộ nhập `nc_equipment_compliance` (UC-020 1a), form và danh sách SCR-DSK-035 (chỉ báo, nút "Kiểm hạn ngay", gợi ý ngày hết hạn), Workspace, `vi.csv`.

## Ghi chú
- TC-CLS-27 (`test_TC_CLS_27_thieu_chung_tu_bi_tu_choi`), TC-CLS-28 (`test_TC_CLS_28_nhac_han_thong_bao_va_doi_so_ngay`, `test_TC_CLS_28_bao_cao_liet_ke_ho_so_sap_het_han_theo_khoa`).
- Quyền NC Settings theo dòng "Cấu hình AI, mẫu lệnh" (ASM-099). FEAT-002 mở rộng NC Settings, không tạo lại.
- `get_reminder_days()` đọc thẳng bảng Singles: chưa lưu lần nào thì 30; đã lưu 0 thì 0 (hợp lệ, nhắc đúng ngày hết hạn).
- TBD-18 cài trống (ASM-104): bệnh viện tự đánh dấu `compliance_required` trên NC Equipment Type.
- FR-CMP-006 phần cảnh báo trên lần tính, FR-CMP-002..004 (quy chi phí về năm): FEAT-036.
- Không viết patch (ASM-106). ASM-099..106, AMD-009 (đã duyệt, áp vào `docs/data-model.md`). ASM-105: sửa hai test cũ theo Quyết định Lead (`test_permissions.py` 27 → 29 DocType; `api/test_importer.py` thêm `nc_equipment_compliance` cho NC Resource Manager).
- FEAT-031 chạy song song: khi gộp `develop` giữ dòng của cả hai bên ở `assumptions.md`, `vi.csv`, `check_conventions.py`, đếm DocType; đánh lại số ASM.

## Nghiệm thu
Người nghiệm thu: QA (Multica). Verify accepted ở commit `d9be0cb`. Giới hạn QA: không tạo được site sạch `normcore-verify.test` (thiếu `DB_ROOT_PASSWORD`), bộ test chạy trên site dev `normcore.test` (465 test OK); chưa kiểm giao diện bằng Playwright.
