# As-Built: FEAT-005 Danh mục kỹ thuật và tình trạng chuỗi
- Phiên bản app 0.0.1; Dev: NORM-17; nghiệm thu: QA (Multica), 2026-11-22

## 1. Luồng nghiệp vụ đã xây
NC Document Controller tải tệp mẫu "Dịch vụ kỹ thuật" ở danh sách, nhập tệp Excel (mã, tên, mã chuyên khoa): tạo hoặc cập nhật theo mã, dòng thiếu mã, thiếu tên, trùng mã trong tệp bị bỏ và liệt kê trong báo cáo lỗi (FR-SVC-001, 002). Gán nhiều khoa thực hiện trên form (FR-SVC-003). Mở dịch vụ thấy thẻ "Tình trạng chuỗi" có bốn mục: quy trình, định mức, giá thành, giá đã duyệt, theo quyền của người xem (FR-SVC-004).

## 2. DocType tạo mới hoặc thay đổi
Mới: NC Specialty (đặt tên theo `specialty_code`), NC Service Department (bảng con). Mở rộng NC Technical Service: `specialty`, `departments`, trường bố cục và HTML `chain_status_html`, `is_active` hiện ở danh sách. AMD-003, AMD-004 đã áp vào `data-model.md`, `ux-foundations.md`.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/service.py::get_chain_status(service)`; logic thuần `normcore/procedure/chain.py`; `core/permissions.py::readable_departments`; bộ nhập `nc_technical_service` trong `core/import_sets.py`; `hooks.py` thêm NC Specialty vào `check_not_referenced`. Workspace "Normcore" thêm hai lối tắt.

## 4. Quyền và luồng trạng thái
Theo dòng "Dịch vụ kỹ thuật, chuyên khoa": NC Document Controller, NC Admin ghi; tám vai trò còn lại đọc; NC Admin xóa (chặn khi đang được tham chiếu). Thẻ tình trạng chuỗi: mục không có quyền đọc chỉ hiện "Không có quyền xem"; bộ định mức chỉ trong phạm vi khoa của NC Clinician, NC Department Head (ASM-047).

## 5. Cấu hình cần thiết khi triển khai
`bench migrate` (DocType, Workspace), `bench build` (bản dịch). Không cần patch.

## 6. Test case đã chạy và kết quả
TC-SVC-01, TC-SVC-03, TC-SVC-04 và các test `test_FR_SVC_*`, `test_FR_ACC_005_*`, `test_SCR_DSK_005_*`; `bench run-tests --app normcore`: 180 tests OK (QA chạy lại: 182 OK trên normcore.test); pytest unit + golden 88 passed (QA: 91 passed), độ phủ costing/benchmark 98,9%; `check_conventions.py`, `build_rtm.py` (VAN DE: 0), ruff sạch. Chi tiết: `docs/features/FEAT-005/implementation-log.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- **Chưa kiểm trên trình duyệt:** preview chưa có site (`multica env start preview` thoát lỗi "chưa có site normcore.test"); bộ lọc khoa `page.add_field` ở danh sách và bố cục bốn thẻ (1366 × 768, 768 px) chưa xem thật. Test chỉ kiểm lọc `frappe.get_list` qua bảng con và quy ước JS tĩnh.
- Chưa có số tiền giá thành; Tài chính kế toán chưa xác nhận cách chọn "lần tính gần nhất" (ASM-048).
- Giá đã duyệt luôn "Chưa có giá đã duyệt" cho tới FEAT-030; cột và bộ lọc tình trạng chuỗi ở danh sách: FEAT-002; nút "Soạn quy trình": FEAT-024, "Khởi tạo bộ định mức": FEAT-012.
- FEAT-015 thêm quyền bảng giải trình cho Dept Head thì cập nhật bảng quyền; FEAT-032 trở đi `pick_norm_sets` phải nhóm thêm theo `test_system` (DI-03).
- Mã dịch vụ nhập dạng số trong Excel có thể mất số 0 (ASM-060, chờ Quản lý văn bản).
- `based_on_run` của NC Costing Run chưa có; `_cost_rows` chỉ chọn khi trường tồn tại (ASM-004).
- QA chưa tạo được site sạch (thiếu DB_ROOT_PASSWORD) và chưa kiểm giao diện bằng trình duyệt (Playwright lỗi kết nối); người duyệt bấm thử SCR-DSK-005/006 trên staging.

## 8. Quyết định và tài liệu liên quan
- ASM-047..061 và ASM-062 (`docs/decisions/assumptions.md`); CF-002; AMD-003, AMD-004 (`docs/decisions/amendments/`).
- DEF-002, DEF-003, DEF-004 (`docs/decisions/defects/`): lỗi tài liệu chỉ đọc đã ghi, không chặn FEAT.
- Hồ sơ nghiệm thu: `docs/features/FEAT-005/acceptance.md`, `verdict.json`, `DONE` (bổ sung sau merge PR #21 qua PR chỉ tài liệu).
