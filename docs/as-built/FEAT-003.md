# As-Built: FEAT-003 Sổ sự kiện và tra cứu nhật ký
- Phiên bản app 0.0.1; Dev: NORM-21; Người nghiệm thu: QA (Multica)

## 1. Luồng nghiệp vụ đã xây
Mỗi lần một bản ghi `NC *` có `workflow_state` (NC Norm Set: `status`) đổi trạng thái, hook chung `doc_events["*"]` ghi một NC Audit Event (người, thời điểm, trạng thái trước, sau; loại "Khóa" khi sang "Đã khóa"). NC Admin, NC Director, NC Auditor tra cứu ở danh sách NC Audit Event (SCR-DSK-030) hoặc `api/audit.get_events` lọc theo bản ghi, người, khoảng thời gian, thứ tự tăng dần. `core/audit.log_export` là điểm ghi xuất tệp cho FEAT-019.

## 2. DocType
Mới: NC Audit Event. NC AI Log: thêm bộ lọc chuẩn, chốt bất biến.

## 3. API, hook, fixtures
`normcore/core/audit.py`, `normcore/api/audit.py::get_events`; `hooks.py`: `doc_events["*"]`, `ignore_links_on_delete`. Workspace thêm lối tắt "Nhật ký", "Nhật ký AI".

## 4. Quyền
NC Director, NC Admin, NC Auditor chỉ đọc; không ai có ghi/xóa. Bộ điều khiển từ chối sửa, xóa kể cả Administrator; tạo chỉ qua `log_event` (ASM-064).

## 5. Cấu hình khi triển khai
`bench migrate`, `bench build`. Không cần patch (DocType mới).

## 6. Test và kết quả
TC-AUD-01, 02, 03, `test_FR_AUD_*`; `run-tests --app normcore`: 199 tests OK (normcore.test); CI site sạch pass; pytest 94 passed, độ phủ 98,9%; `check_conventions.py`, `build_rtm.py` (VAN DE: 0), ruff sạch.

## 7. Giới hạn và nợ
- Chưa kiểm UI bằng trình duyệt (SCR-DSK-030 kiểm ở smoke staging); chưa tạo site sạch cục bộ (thiếu DB_ROOT_PASSWORD), dùng CI run 45070989693.
- Tạo, sửa, xóa bản ghi không thành sự kiện riêng; dựa vào Version (ASM-063). FR-AUD-001 "xóa" chưa có dấu vết ngoài Deleted Document của Frappe.
- "Gọi AI", "Nhập tệp", "Đổi cấu hình": chỉ có loại trong danh sách; FEAT-023/019/… gọi `log_event`.
- TC-AUD-01 phần đơn giá làm trên NC Job Title; FEAT-009 thêm ca NC Item Price (ASM-066).
- DocType nào dùng trường trạng thái khác `workflow_state` phải thêm vào `audit.STATE_FIELDS`.
- `frappe.db.set_value` không đi qua bộ điều khiển (ADR-014).
