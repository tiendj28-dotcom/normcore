# As-Built: FEAT-039 Vai trò kiểm soát nội bộ
- Phiên bản app 0.0.1; Dev: NORM-29; Người nghiệm thu: QA (Multica)

## 1. Luồng nghiệp vụ đã xây
Người dùng chỉ có NC Auditor đọc được số liệu kế toán (NC Costing Run, NC Service Cost), nhật ký (NC Audit Event, NC AI Log), bộ định mức của mọi khoa; mọi thao tác ghi, xóa, duyệt bị `PermissionError` và dữ liệu không đổi (UC-026). Vai trò, cột Auditor trong ma trận đã có từ FEAT-001/003; FEAT này bổ sung quét quyền và test nghiệm thu, không đổi quyền 9 vai trò còn lại.

## 2. DocType
Không DocType mới, không đổi trường, không patch.

## 3. Mã
- `normcore/core/readonly.py` (thuần): `READ_ONLY_ROLE`, `WRITE_PTYPES`, `perm_violations`, `workflow_violations`.
- `normcore/core/permissions.py`: `nc_doctypes()`, `read_only_violations(role)` quét quyền hiệu lực (DocPerm, Custom DocPerm) và Workflow của mọi DocType cha `NC `, tự áp cho DocType FEAT sau thêm.
- `scripts/check_conventions.py` NC-06: thêm cờ `import`, `share`, `set_user_permissions`; lỗi khi DocType cha thiếu `read` permlevel 0 cho NC Auditor.

## 4. Quyền
NC Auditor chỉ `read` ở 19 DocType cha (ASM-132). Không hook `has_permission` "*" (ASM-133).

## 5. Vận hành
Kiểm một site: `bench --site <site> execute normcore.core.permissions.read_only_violations`. Không in gì (kết quả `[]`) là sạch; có vi phạm thì in danh sách tiếng Việt.

## 6. Test và kết quả
TC-CLS-44 (`tests/test_feat_039.py`, `tests/unit/test_readonly.py`, `test_permission_matrix.py::test_TC_CLS_44_nc06_*`), TC-AUD-03 với NC Auditor, giữ TC-ACC-04. `run-tests --app normcore`: 511 tests OK; pytest unit + golden 233 passed, phủ 98,73%; `check_conventions.py` thoát 0; golden thoát 0.

## 7. Giới hạn và nợ
- ASM-131: NC Accounting Import, NC Service Volume, NC Reconciliation Line chưa có; test dùng NC Costing Run, NC Service Cost. Kiểm lại khi FEAT-016 và FEAT đối soát xong.
- Quét lúc chạy chỉ bắt quyền khai báo, không bắt API tự `ignore_permissions` (rủi ro ghi ở thiết kế); mỗi FEAT sau phải test với NC Auditor.
- T06 kiểm giao diện bằng đối chiếu mã `*.js` với bảng điều kiện nút ở `ui-design.md`, chưa mở trình duyệt (xem implementation-log).
