# FEAT-003 — Thiết kế kỹ thuật: Sổ sự kiện và tra cứu nhật ký

Issue NORM-21. Nhánh `ai/NORM-21-feat-003` từ `develop` @ `539ae89`. Nguồn: `srs.md` FR-AUD-001..004, FR-ACC-007; `use-cases.md` UC-018; `test-cases.md` TC-AUD-01..03; `data-model.md` 3.4, 4; ADR-014 (và ghi chú [1.1]).

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-AUD-001 | Một phần có chủ đích | Lịch sử theo trường: `track_changes` (đã bật ở mọi DocType). Sổ sự kiện: chuyển trạng thái, khóa (ASM-063) qua hook `doc_events["*"]`. Tạo, sửa, xóa không thành sự kiện riêng vì danh sách `event_type` ở data-model không có (ASM-063) |
| FR-AUD-002 | Đủ | NC Audit Event, NC AI Log: không vai trò nào có quyền sửa, xóa, và bộ điều khiển từ chối cả Administrator (ASM-064) |
| FR-AUD-003 | Đủ | `api/audit.py::get_events` và danh sách chuẩn SCR-DSK-030; NC Admin, NC Director, NC Auditor |
| FR-AUD-004 | Chỉ điểm ghi | `core/audit.py::log_export`; luồng xuất tệp thuộc FEAT-019 |

Không có phép tính tiền, không đối chiếu golden, không có BR-COST/ADJ/CLS.

## 2. DocType

### 2.1 NC Audit Event (mới) — module NC Core

Trường đúng `data-model.md` 3.4: `event_time` (Datetime, BB), `user` (Link User), `event_type` (Select: Chuyển trạng thái / Khóa / Xuất tệp / Đổi cấu hình / Gọi AI / Nhập tệp; BB), `ref_doctype` (Link DocType), `ref_name` (Dynamic Link), `from_state`, `to_state` (Data), `detail` (Small Text). Tên tự động `AUD-.#####`. `track_changes` = 1, `in_create` = 1, `sort_field` = `event_time`, `sort_order` = ASC; `ref_doctype`, `ref_name`, `user`, `event_time`, `event_type` là bộ lọc chuẩn. Trường chỉ đọc.

Quyền (dòng "Nhật ký AI, sổ sự kiện"): NC Director, NC Admin, NC Auditor chỉ `read`; không `write`, `create`, `delete`. Khai `DOCTYPE_ROW["NC Audit Event"]` trong `scripts/check_conventions.py`. Test đếm DocType 18 → 19 (như ASM-053 của FEAT-005).

### 2.2 NC AI Log (đã có) — thêm bộ lọc chuẩn `user`, `ref_doctype`, `purpose`, `sort_field` giữ nguyên. Bộ điều khiển thêm chống sửa, xóa.

## 3. Logic — `normcore/core/audit.py`

| Hàm | Việc |
| :-- | :-- |
| `log_event(event_type, ref_doctype, ref_name, from_state, to_state, detail, user)` | Tạo NC Audit Event (đặt `flags.from_audit` để vượt chốt `before_insert`, `ignore_permissions`); `event_time = now_datetime()` |
| `log_export(file_type, ref_doctype, ref_name, file_name)` | FR-AUD-004: `event_type` = "Xuất tệp", `detail` = `"{file_type}: {file_name}"` |
| `on_doc_update(doc, method)`, `on_doc_insert(doc, method)` | Hook `doc_events["*"]`. Chỉ DocType tên bắt đầu `NC `, không phải NC Audit Event, NC AI Log, và có trường `workflow_state`. `on_update` ghi khi `workflow_state` khác bản trước (`get_doc_before_save`); `after_insert` ghi từ rỗng → trạng thái đầu |
| `guard_immutable(doc)` | `frappe.throw` PermissionError; gắn vào `validate` (khi không mới) và `on_trash` của hai DocType |
| `STATE_EVENTS` | Trạng thái đích `Đã khóa` → loại "Khóa", còn lại "Chuyển trạng thái" |

`hooks.py`: `doc_events["*"] = {"after_insert": ..., "on_update": ...}` gộp cùng khóa `on_trash` hiện có của các DocType danh mục; `ignore_links_on_delete = ["NC Audit Event"]` để Dynamic Link `ref_name` không chặn xóa bản ghi nguồn (FR-ADM-005 vẫn do `check_not_referenced`).

## 4. API — `normcore/api/audit.py`

`get_events(ref_doctype=None, ref_name=None, user=None, from_time=None, to_time=None, limit=200)` (`@frappe.whitelist()`): người không có quyền đọc NC Audit Event → `frappe.PermissionError`. Dùng `frappe.get_list` (không `ignore_permissions`), sắp `event_time asc, creation asc`; trả `[{name, event_time, user, event_type, ref_doctype, ref_name, from_state, to_state, detail}]`. `limit` tối đa 1000.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện | TC | FR | Test |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Sửa tên NC Job Title (`save(ignore_version=False)`) → có Version chứa trường `job_title_name` giá trị cũ/mới; ban hành quy trình → NC Audit Event "Chuyển trạng thái" `Nháp → Đã ban hành`, người ban hành | TC-AUD-01 | FR-AUD-001 | `nc_audit_event/test_nc_audit_event.py::test_TC_AUD_01_*` |
| 2 | NC Admin: sửa/xóa NC Audit Event và NC AI Log qua `frappe.client.set_value`/`delete`, `frappe.get_doc().save()/.delete()` → `PermissionError`; `has_permission` write/delete sai; Administrator cũng bị chặn bởi bộ điều khiển | TC-AUD-02 | FR-AUD-002 | `test_TC_AUD_02_*` |
| 3 | Director gọi `get_events(ref_doctype=quy trình, ref_name=…)` → các sự kiện của đúng quy trình theo thời gian tăng dần | TC-AUD-03 | FR-AUD-003 | `test_TC_AUD_03_*` |
| 4 | Lọc theo người, khoảng thời gian; NC Auditor đọc được, NC Clinician (không quyền) bị từ chối | — | FR-AUD-003, FR-ACC-007 | `test_FR_AUD_003_*` |
| 5 | NC Auditor và vai trò không quyền: không tạo, sửa, xóa được; tạo thẳng không qua `log_event` bị từ chối | — | FR-AUD-002, FR-ACC-007 | `test_FR_AUD_002_*` |
| 6 | `log_export` ghi người xuất, loại tệp, bản ghi nguồn | — | FR-AUD-004 | `test_FR_AUD_004_*` |
| 7 | Xóa bản ghi nguồn (NC Specialty) không bị Dynamic Link của sổ sự kiện chặn | — | FR-ADM-005 | `test_FR_AUD_001_xoa_ban_ghi_nguon_khong_bi_chan` |
| 8 | Chuỗi JS của danh sách có bản dịch, không mã màu cứng | — | NFR-USE-001 | `tests/unit/test_audit_ui_conventions.py` |

## 6. Giả định và rủi ro

ASM-063..ASM-066 (`docs/decisions/assumptions.md`). Rủi ro: quản trị CSDL vẫn sửa được ở mức thấp (ADR-014, ngoài phạm vi v1); `frappe.db.set_value` không đi qua bộ điều khiển, nên mã của FEAT sau không được dùng nó trên hai DocType này.
