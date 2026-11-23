# As-Built FEAT-031 — Dịch vụ cận lâm sàng và hệ thống xét nghiệm

Issue NORM-25. FR: FR-SVC-008..011, FR-CLS-001, FR-CLS-002, FR-CLS-005..008 (một phần: 007, 008), FR-ACC-008. UC-019, SCR-DSK-006 (khối "Cận lâm sàng"), SCR-DSK-032. TC: TC-CLS-20..23.
Giới hạn: giao diện chưa kiểm bằng trình duyệt; trang `import-excel` (FEAT-004) chưa đọc tham số `import_set` nên nút "Nhập từ Excel" của danh sách chỉ mở trang.

## Đã làm
- NC Technical Service thêm nhóm trường cận lâm sàng (`is_paraclinical`, `cls_group`, `result_unit`), dịch vụ bộ (`is_panel`, `panel_costing_mode`, bảng NC Panel Component), gửi ngoài (`is_send_out`, `send_out_price`), mã ngoài (bảng NC Service Code Map, DI-09 kiểm ở `validate` và bằng chỉ mục duy nhất `unique_source_code`). Quy tắc ở `normcore/procedure/service_rules.py`.
- DocType mới NC Test System (quyền theo ma trận, không ai xóa, phạm vi khoa qua `SCOPE_RULES`). Quy tắc ở `normcore/costing/test_systems.py` (phủ 100%); không có công thức k (thuộc FEAT-036).
- NC Costing Run: `test_systems_in_scope()` và lọc bộ định mức theo hệ thống ngừng dùng, dịch vụ gửi ngoài; lần tính đã có không bị đụng tới.
- API `normcore/api/test_system.py` (`get_status`, `get_service_systems`); bộ nhập `nc_test_system`; form và danh sách SCR-DSK-032, khối hệ thống ở SCR-DSK-006; Workspace; `vi.csv`.

## Ghi chú
- Khối tình trạng (FR-CLS-007): bốn mục đều "Chưa có" cho tới FEAT-032, 034, 035, 036 (ASM-115). Bộ nhập chỉ có hệ thống xét nghiệm (ASM-116).
- ASM-107..117 (`docs/decisions/assumptions.md`). ASM-113: Lead duyệt đổi số đếm `test_permissions.py` 27 → 30.
- `cls_group`, `result_unit` có dòng trống đầu danh sách để không mặc định "Hóa sinh".
- Gộp với FEAT-033: giữ dòng của cả hai bên ở `hooks.py`, `check_conventions.py`, `vi.csv`, số đếm DocType (theo số thực + 3, `assertEqual`).
