# FEAT-001 Technical design: vai trò, khoa, trung tâm chi phí, phạm vi theo khoa

Phạm vi: FR-ACC-001..006, FR-ADM-004, FR-ADM-005, UC-017, SCR-DSK-031. Quyết định: ASM-026..ASM-034.

## Dữ liệu
- **NC Cost Center** (mới): `cost_center_code` (tên bản ghi), `cost_center_name`, `center_type` (Lâm sàng / Hỗ trợ), `track_changes`. Quyền G1.
- **NC Department**: thêm `cost_center` (Link, bắt buộc). Patch `add_cost_center_to_departments` (post_model_sync) điền cho khoa có sẵn; chạy lại không tạo trùng.
- Quyền xóa: NC Admin trên NC Department, NC Cost Center, NC Job Title, NC Technical Service.

## Phạm vi theo khoa (`normcore/core/permissions.py`)
- Khoa gán = User Permission (`allow` = NC Department, `applicable_for` = NC Cost Center, xem ASM-031). Hàm `get_user_departments` đọc thẳng CSDL nên hiệu lực ngay ở yêu cầu kế tiếp.
- `SCOPE_RULES[doctype] = ScopeRule(department_field, public_read)`; hook `has_permission` và `permission_query_conditions` dùng chung, đăng ký trong `hooks.py` cho NC Clinical Procedure và NC Norm Set. DocType mới thêm một dòng ở `SCOPE_RULES` và hai dòng ở `hooks.py`.
- Ghi: chỉ khoa được gán. Đọc: khoa được gán hoặc `public_read` (quy trình "Đã ban hành"). Hook chỉ từ chối; không áp khi người dùng có quyền cùng loại từ vai trò khác (G4).
- `make_norm_set` kiểm thêm `has_permission(..., doc=ns)`; `add_step` đã kiểm `write` trên bản ghi.

## Gán khoa (`normcore/api/access.py`)
`assign_department`, `unassign_department`, `list_department_users`: chỉ NC Admin / Administrator, nếu không thì `PermissionError`.

## Xóa danh mục (`normcore/core/references.py`)
`doc_events.on_trash` của bốn DocType danh mục: liệt kê mọi bản ghi tham chiếu (liên kết thường và Dynamic Link, dòng con quy về bản ghi cha), ném `LinkExistsError` tiếng Việt.

## Quét quyền (`scripts/check_conventions.py`)
NC-07: không cấp quyền cho `All`. NC-08: quyền từng vai trò khớp `MATRIX` qua `DOCTYPE_ROW`; `delete` chỉ hợp lệ theo `DELETE_ALLOWED`.

## Tiêu chí nghiệm thu
TC-ACC-01..05, TC-ADM-04, TC-ADM-05, FR-ACC-006 (xem `tests/test_feat_001.py`, `tests/unit/test_permission_matrix.py`).

## Giới hạn
Người dùng có hai vai trò mà một vai trò cấp quyền đọc (ví dụ Finance) thấy mọi khoa; ô "A (khoa)" thuộc FEAT-007, FEAT-012; "NC Consultant được cấp riêng" thuộc FEAT-016.
