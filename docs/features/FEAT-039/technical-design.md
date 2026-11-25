# FEAT-039 — Vai trò kiểm soát nội bộ — Thiết kế kỹ thuật

Issue NORM-29. Nguồn: `srs.md` FR-ACC-007, phần sửa ở bản 1.1 của FR-ACC-002, FR-ACC-004, FR-AUD-003; `use-cases.md` UC-026; `data-model.md` mục 4 (cột Auditor); `test-cases.md` TC-CLS-44, TC-ACC-04, TC-AUD-03; `ux-foundations.md` SCR-DSK-030. Phụ thuộc FEAT-001, FEAT-003: đều có `DONE` trên `develop`.

**Đã có, không làm lại** (As-Built FEAT-001, FEAT-003, FEAT-031 và mã trên `develop` 73029ce):

| Thành phần | Chỗ | Tình trạng |
| :-- | :-- | :-- |
| Vai trò NC Auditor (`desk_access` = 1) | `install.py::ROLES`, `fixtures/role.json` | Có. Không đổi |
| Cột Auditor = R trong ma trận | `scripts/check_conventions.py::MATRIX`, 19 DocType cha đều chỉ có `read` | Có. Không đổi |
| Luật NC-06 (Auditor không có write, create, delete, submit, cancel, amend) | `check_conventions.py::AUDITOR_FORBIDDEN` | Có; FEAT này mở rộng (mục 3) |
| Quét quyền 10 vai trò, Auditor đọc mọi DocType cha, không ghi | `tests/test_permissions.py` (glob `nc_*/doctype/*/*.json`, tự áp DocType mới) | Có. Không sửa |
| Auditor đọc mọi khoa (không thuộc `SCOPED_ROLES`) | `core/permissions.py` | Có. Không đổi |
| NC Audit Event, NC AI Log: Auditor đọc; `get_events` cho Auditor | FEAT-003, `test_FR_AUD_003_loc_nguoi_thoi_gian_va_quyen` | Có |
| Trang `import-excel`, `procedure-editor` cho Auditor vào; bộ nhập và sửa quy trình từ chối | `api/test_importer*.py`, `api/test_procedure.py`, `tests/test_form_actions.py` | Có |

FEAT này **bổ sung**: (1) test nghiệm thu TC-CLS-44 theo đúng kịch bản UC-026; (2) quét quyền lúc chạy trên CSDL (DocPerm, Custom DocPerm, Workflow) tự áp cho mọi DocType `NC ` kể cả DocType FEAT sau thêm hoặc quyền thêm qua giao diện Role Permission Manager; (3) mở rộng NC-06 cho các cờ ghi còn thiếu; (4) TC-AUD-03 chạy với NC Auditor. Không đổi quyền của 9 vai trò còn lại; không thêm DocType, trường, patch.

## 1. Phạm vi

| FR | Mức | Làm gì ở FEAT này |
| :-- | :-- | :-- |
| FR-ACC-007 | Should | Hàm quét `core/permissions.py::read_only_violations` + test TC-CLS-44: Auditor đọc được mọi DocType cha `NC `; mọi thao tác tạo, sửa, xóa, duyệt (nút máy chủ, API whitelisted, `frappe.client`) bị `PermissionError`; không bản ghi nào đổi |
| FR-ACC-002 (sửa 1.1) | Must | Giữ TC-ACC-04 (10 vai trò, không `All`); NC-06 thêm `import`, `share`, `set_user_permissions` và luật thiếu `read` (mục 3). Không đổi ma trận 9 vai trò kia |
| FR-ACC-004 (sửa 1.1) | Must | **Một phần:** Auditor đọc dòng "Số liệu kế toán, sản lượng, phân bổ" và "Lần tính giá, kết quả, đối soát" đang có trên `develop` (NC Costing Run, NC Service Cost). NC Accounting Import, NC Service Volume, NC Allocation…, NC Reconciliation Line chưa có (FEAT-016 và FEAT đối soát): quét lúc chạy tự áp khi các DocType đó lên; TC-CLS-44 kiểm lại khi các FEAT đó xong (ASM-131) |
| FR-AUD-003 (sửa 1.1) | Must | Thêm `test_TC_AUD_03_auditor_loc_theo_quy_trinh`: NC Auditor lọc nhật ký theo một quy trình qua `api/audit.get_events`, kết quả theo thời gian tăng dần |

Không làm: quyền NC Consultant xem số liệu kế toán khi "cấp riêng" (FEAT-016); xuất tệp, in cho Auditor (ASM-132); hook `has_permission` "*" chặn mọi ghi của Auditor (ASM-133).

## 2. DocType

Không DocType mới, không đổi trường, không patch. Quyền NC Auditor trên mọi DocType cha giữ đúng một dòng `{"role": "NC Auditor", "read": 1}` (permlevel 0). Bảng con theo quyền cha (data-model mục 4).

Không có Workflow trên `develop` (FEAT-007 thêm cho NC Clinical Procedure, FEAT phương án giá cho NC Price Proposal). Quét ở mục 4 đã bao Workflow để FEAT đó không được gán NC Auditor vào `allowed` của chuyển trạng thái hay `allow_edit` của trạng thái.

## 3. Quét tĩnh `scripts/check_conventions.py` (NC-06)

- `AUDITOR_FORBIDDEN` thêm `import`, `share`, `set_user_permissions`: ba cờ này cho người dùng thay đổi dữ liệu hoặc cấp quyền cho người khác. Thành `("write", "create", "delete", "submit", "cancel", "amend", "import", "share", "set_user_permissions")`.
- Không cấm `report`, `export`, `print`, `email`, `select` ở luật tĩnh (là quyền đọc), nhưng hiện cũng không cấp (ASM-132).
- NC-06 áp cho **mọi** dòng quyền của NC Auditor ở mọi `permlevel` (hiện đã vậy: vòng lặp trên mọi `perm`). Thêm vào luật: DocType cha `NC ` mà NC Auditor **không có** `read` ở permlevel 0 → lỗi `NC-06 NC Auditor thiếu quyền đọc` (FR-ACC-007 "chỉ đọc đối với mọi bản ghi"). Hiện NC-08 đã bắt qua ma trận; luật NC-06 riêng để bắt cả DocType chưa có dòng ma trận.
- Hiện app sạch: thay đổi không làm `check_conventions.py` báo lỗi mới (đã kiểm 19 DocType cha: Auditor chỉ `read`).

## 4. Quét lúc chạy — `normcore/core/permissions.py`

Thêm hằng và hai hàm. Hàm thuần đặt ở mô-đun mới `normcore/core/readonly.py` (không import `frappe`, test bằng pytest); `core/permissions.py` chỉ đọc CSDL rồi gọi.

### 4.1 `normcore/core/readonly.py` (thuần)

| Hàm / hằng | Việc | Căn cứ |
| :-- | :-- | :-- |
| `READ_ONLY_ROLE = "NC Auditor"` | | FR-ACC-007 |
| `WRITE_PTYPES = ("write", "create", "delete", "submit", "cancel", "amend", "import", "share", "set_user_permissions")` | Cùng tập với NC-06 (một nguồn: `check_conventions.py` giữ bản riêng vì là script độc lập, test đơn vị so hai tập bằng nhau) | |
| `perm_violations(doctype, perms, role) -> list[str]` | `perms`: list dict (role, permlevel, cờ). Trả: thiếu `read` permlevel 0; mỗi dòng của `role` có cờ thuộc `WRITE_PTYPES` (nêu permlevel, cờ) | FR-ACC-007 |
| `workflow_violations(workflows, role) -> list[str]` | `workflows`: list dict `{name, document_type, transitions: [{state, action, allowed}], states: [{state, allow_edit}]}`. Trả mỗi chuyển trạng thái có `allowed == role` (thao tác duyệt) và mỗi trạng thái có `allow_edit == role` | FR-ACC-007 "không duyệt"; UC-026 1a |

Thông báo tiếng Việt, ví dụ: `NC Norm Set: NC Auditor có quyền write (permlevel 0)`, `Workflow Quy trình: NC Auditor được chuyển "Gửi duyệt" từ "Nháp"`.

### 4.2 `normcore/core/permissions.py`

| Hàm | Việc |
| :-- | :-- |
| `nc_doctypes() -> list[str]` | `frappe.get_all("DocType", {"name": ["like", "NC %"], "istable": 0}, pluck="name", order_by="name")`. Đọc CSDL (không liệt kê cứng, không glob tệp): tự gồm DocType FEAT sau thêm và DocType tùy biến đặt tên `NC ` |
| `read_only_violations(role=READ_ONLY_ROLE) -> list[str]` | Với mỗi DocType ở `nc_doctypes()`: quyền hiệu lực = `frappe.get_meta(dt).permissions` (meta đã thay bằng Custom DocPerm nếu DocType có Custom DocPerm), gọi `perm_violations`. Workflow: mọi `Workflow` có `document_type` thuộc `nc_doctypes()` (kể cả không active), gọi `workflow_violations`. Trả danh sách rỗng = sạch |

Không whitelist (không có màn hình cho nó). Vận hành kiểm trên site: `bench --site <site> execute normcore.core.permissions.read_only_violations` (ghi vào As-Built).

Không đổi `has_permission`, `permission_query_conditions`, `SCOPE_RULES`.

## 5. API whitelisted

Không thêm API. Danh sách thao tác ghi / duyệt đang có mà TC-CLS-44 thử với NC Auditor (mỗi dòng phải ném `frappe.PermissionError` và không đổi CSDL):

| Thao tác | Cách gọi trong test |
| :-- | :-- |
| Sửa bộ định mức (kịch bản TC) | `frappe.get_doc("NC Norm Set", x)`, đổi một dòng định mức, `.save()` |
| Xóa bộ định mức | `frappe.delete_doc("NC Norm Set", x)` |
| Tạo bộ định mức từ quy trình | `nc_norm_set.make_norm_set(procedure)` |
| Khóa bộ định mức (duyệt) | `doc.lock()` |
| Ban hành quy trình (duyệt) | `NC Clinical Procedure.publish()` |
| Sửa quy trình qua trình soạn | `api.procedure.save_sections`, `add_step` |
| Tạo quy trình | `api.procedure.create_procedure` |
| Chạy lần tính giá | `NC Costing Run.run_costing()` |
| Nhân bản bộ tham số | `NC Costing Parameter Set.duplicate()` |
| Xác minh đơn giá | `api.item.verify_price` |
| Nhập Excel | `api.importer.import_file` |
| Gán khoa | `api.access.assign_department` |
| Ghi chung của Frappe | `frappe.client.set_value`, `frappe.client.insert`, `frappe.client.delete` trên NC Norm Set, NC Costing Run, NC Audit Event |

Lỗi nào trong số này hiện trả thông báo khác `PermissionError` (ví dụ `ValidationError` vì kiểm trạng thái trước quyền) là lỗi phải sửa ở mã đó trong phạm vi FEAT này: kiểm quyền trước kiểm dữ liệu. Dev ghi vào implementation-log mọi chỗ sửa.

## 6. Logic thuần và golden

Không có phép tính tiền; không đối chiếu golden. `normcore/core/readonly.py` test bằng pytest (`tests/unit/test_readonly.py`).

## 7. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | Người dùng chỉ có NC Auditor: `frappe.has_permission(dt, "read")` đúng, mở được (`frappe.get_doc` + `get_list` không rỗng khi có dữ liệu) với NC Costing Run, NC Service Cost (số liệu, kết quả), NC Audit Event, NC AI Log (nhật ký), NC Norm Set của hai khoa khác nhau | TC-CLS-44 | FR-ACC-007, FR-ACC-004 |
| 2 | Auditor sửa một bộ định mức → `PermissionError`; giá trị trong CSDL không đổi | TC-CLS-44 | FR-ACC-007 |
| 3 | Mọi thao tác ở bảng mục 5 → `PermissionError`; đếm bản ghi và `modified` không đổi | TC-CLS-44 | FR-ACC-007 |
| 4 | `read_only_violations()` trên site test trả `[]` | TC-CLS-44 | FR-ACC-007 |
| 5 | Thêm Custom DocPerm cho NC Auditor `write` trên một DocType `NC ` (trong test, rollback) → `read_only_violations()` báo đúng DocType và cờ; Workflow giả có chuyển trạng thái `allowed = NC Auditor` → báo | TC-CLS-44 | FR-ACC-007 |
| 6 | `perm_violations`, `workflow_violations` (pytest): bắt thiếu `read`, từng cờ `WRITE_PTYPES`, permlevel > 0, chuyển trạng thái, `allow_edit`; đầu vào sạch → `[]`; `WRITE_PTYPES` bằng `AUDITOR_FORBIDDEN` | TC-CLS-44 | FR-ACC-007 |
| 7 | `check_conventions.py`: DocType mẫu cho Auditor `import` / `share` / `set_user_permissions`, hoặc thiếu `read` → lỗi `NC-06`; app hiện tại thoát 0 | TC-ACC-04, TC-CLS-44 | FR-ACC-002, FR-ACC-007 |
| 8 | TC-ACC-04 giữ đạt: `tests/unit/test_permission_matrix.py`, `tests/test_permissions.py` xanh, không sửa | TC-ACC-04 | FR-ACC-002 |
| 9 | NC Auditor gọi `get_events(ref_doctype="NC Clinical Procedure", ref_name=x)` → các sự kiện của quy trình đó, `timestamp` tăng dần | TC-AUD-03 | FR-AUD-003 |
| 10 | Người dùng có NC Auditor **và** NC Finance vẫn sửa được bộ tham số (quyền vai trò khác không bị hẹp) | TC-CLS-44 | FR-ACC-002 |

Tên test: `test_TC_CLS_44_<mo_ta>`, `test_TC_AUD_03_auditor_<mo_ta>`. Test tích hợp đặt ở `normcore/tests/test_feat_039.py`; test đơn vị ở `normcore/tests/unit/test_readonly.py` và thêm hàm mới vào `normcore/tests/unit/test_permission_matrix.py` (chỉ thêm, không sửa hàm cũ).

## 8. Giả định và rủi ro

| Mã | Nội dung |
| :-- | :-- |
| ASM-131 | FR-ACC-004, TC-CLS-44 "số liệu kế toán, đối soát": DocType NC Accounting Import, NC Service Volume, NC Reconciliation Line chưa có trên `develop` (FEAT-016 đang thiết kế; đối soát ở FEAT sau). Test dùng NC Costing Run và NC Service Cost (dòng "Lần tính giá, kết quả, đối soát") làm số liệu tài chính. `read_only_violations` và `tests/test_permissions.py` tự áp cho DocType mới. Kiểm lại TC-CLS-44 với DocType kế toán, đối soát khi FEAT-016 và FEAT đối soát DONE (mỗi FEAT đó đã phải có test với NC Auditor theo luật chung) |
| ASM-132 | NC Auditor chỉ có cờ `read` (ma trận "R = đọc"), không `report`, `export`, `print`, `email`: giữ như 9 vai trò R khác, không đổi quyền hiện có. Cần xuất tệp cho kiểm soát thì Lead quyết ở FEAT xuất biểu |
| ASM-133 | Không thêm hook `has_permission` "*" chặn Auditor: người dùng giữ NC Auditor cùng vai trò khác vẫn có quyền của vai trò kia (tiền lệ G4 của FEAT-001). Kiểm soát bằng quét tĩnh NC-06 (CI) và quét lúc chạy `read_only_violations` (test + lệnh vận hành) |
| ASM-134 | "Duyệt" ở FR-ACC-007 = chuyển trạng thái theo luồng (data-model mục 5) và nút máy chủ tương đương (`lock`, `publish`). Khi chưa có Frappe Workflow, kiểm qua nút máy chủ; khi có, kiểm qua `workflow_violations` |

Số ASM: cuối trên `develop` là ASM-117; ASM-118..130 đã được nhánh FEAT-016 dùng, nên FEAT này lấy từ ASM-131. Gộp xung đột `assumptions.md`: giữ dòng cả hai bên.

Rủi ro:
- Thao tác ghi về sau (FEAT-007, 012, 016…) có thể kiểm trạng thái trước quyền, trả `ValidationError` thay vì `PermissionError`. Luật chung buộc mỗi FEAT test với NC Auditor; quét lúc chạy chỉ bắt quyền khai báo, không bắt API tự `ignore_permissions`.
- `tests/test_permissions.py` đếm cứng số DocType (30): FEAT này không thêm DocType nên không đụng.
