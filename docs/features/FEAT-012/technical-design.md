# FEAT-012 — Bộ định mức theo bước: khởi tạo, sửa, xác nhận, khóa — Thiết kế kỹ thuật

Issue NORM-39. Nguồn: `srs.md` FR-NORM-001..014, FR-NORM-016, BR-COST-002..007, FR-ACC-003, FR-AI-008; `use-cases.md` UC-009; `data-model.md` 3.5 (NC Norm Set, NC Norm Line), mục 4 (dòng "Bộ định mức"), 5.2, DI-03, DI-04, DI-05, DI-06; `architecture.md` ADR-003 (logic thuần), ADR-010 (Desk Page Vue qua API whitelisted), cây thư mục `norm/`, `api/norm.py`, `public/js/norm_grid/`; `ux-foundations.md` SCR-DSK-013, SCR-DSK-014; `design.md` mục 3 (Lưới định mức, Dòng đề xuất của AI, Bản ghi chỉ đọc); golden `docs/golden/golden_engine.py:93` (`applied_qty`, BR-COST-007) và `direct_lines` (BR-COST-002..006); TC-NORM-01..07, 09..12.

Phụ thuộc (đều DONE trên `origin/develop`): FEAT-007 (quy trình "Đã ban hành"), FEAT-009 (NC Item, NC Item Price, `costing/pricing.py`), FEAT-010 (NC Equipment, NC Room, `costing/resources.py`), FEAT-011 (NC Costing Parameter Set `wastage_cap`, NC Job Title Rate). Dùng lại khung FEAT-000 (NC Norm Set, NC Norm Line, `make_norm_set`, `lock`) và phạm vi khoa FEAT-001 (`core/permissions.py`, `core/scope_rules/nc_norm_set.json` đã có).

Giả định: `docs/decisions/assumptions/FEAT-012.md` (ASM-012-01..16). Sửa thiết kế: `docs/decisions/amendments/AMD-012-01.md` (nguồn lực chưa liên kết, gồm CF-012-01). **Câu hỏi cho Lead: mục 10 (Q1, Q2)** — Dev chỉ bắt đầu T03 sau khi có Quyết định Lead.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-NORM-001 | `create_norm_set(procedure)`: quy trình "Đã ban hành" → bộ "Nháp", `version_no` = max + 1 của (dịch vụ, khoa), **một dòng cho mỗi dòng nguồn lực** (mọi loại, không chỉ Nhân lực), mang `step_id` và `procedure_resource_row`; cấu phần theo bảng ánh xạ 4.1 |
| FR-NORM-002 | Từ chối khởi tạo khi quy trình chưa "Đã ban hành" (đã có ở `validate` và `make_norm_set`, giữ) |
| FR-NORM-003 | Dòng **mới hoặc bị sửa** phải có cấu phần, nguồn lực trong danh mục, định mức (> 0), đơn vị; LABOR thêm số người (≥ 1) và số phút (> 0). Thông báo nêu mã dòng và tên trường thiếu. Kiểm ở controller (mọi đường ghi) |
| FR-NORM-004 | DRUG/SUPPLY: `wastage_rate` > `wastage_cap` của bộ tham số hiệu lực mà `wastage_reason` trống → từ chối lưu |
| FR-NORM-005 | Dòng thêm (không có `procedure_resource_row`) phải có đúng một trong hai: `step_id` tồn tại trong quy trình, hoặc `service_level` = 1 (khi đó `step_id` trống) |
| FR-NORM-006, 007 | Lượng áp dụng = `engine.applied_qty` (đã có, BR-COST-007); hiển thị ở lưới và dùng cho chi phí tạm tính. `authority_qty` = 0 hoặc trống là "không có" (ASM-013 của FEAT-000) |
| FR-NORM-008 | `basis` là Select 5 giá trị (Frappe tự từ chối giá trị ngoài danh sách; API kiểm lại); `basis_ref` lưu kèm |
| FR-NORM-009 | `confirm_line`: NC Clinician hoặc NC Department Head có quyền ghi bộ (phạm vi khoa) → ghi `confirmed_by`, `confirmed_on` của đúng dòng đó |
| FR-NORM-010 | `confirm_set` (NC Department Head cùng khoa): từ chối nếu còn dòng chưa xác nhận, chưa liên kết danh mục, hoặc `ai_suggested`; thông báo liệt kê từng dòng một lần, giữ "Nháp" |
| FR-NORM-011 | `lock_set` (NC Finance): chỉ từ "Đã xác nhận chuyên môn" → "Đã khóa"; ghi `locked_by`, `locked_on`; DI-03 (bộ khóa cũ cùng dịch vụ, khoa → "Đã thay thế", đã có) |
| FR-NORM-012 | "Đã khóa"/"Đã thay thế": từ chối mọi sửa (form, `frappe.client`, API); `new_version` tạo bộ "Nháp" mới từ bộ đã khóa |
| FR-NORM-013 | `is_excluded` = 1 mà `exclude_reason` trống hoặc ngoài danh sách → từ chối lưu |
| FR-NORM-014 (Should) | Cùng nguồn lực ở hai dòng của cùng một bước (hoặc cùng là dòng chung) → `save_line` trả cảnh báo, chưa lưu; người dùng xác nhận thì lưu (`allow_duplicate`). Lưới luôn đánh dấu dòng trùng |
| FR-NORM-016 (Should) | `get_norm_set` trả chi phí trực tiếp tạm tính theo dòng, theo bước × cấu phần, với bộ tham số hiệu lực; dòng thiếu đơn giá ghi "Chưa có đơn giá", không bịa số |
| Trạng thái 5.2 | Thêm "Trả lại" (Đã xác nhận chuyên môn → Nháp, NC Finance, bắt buộc lý do) |

**Không làm** (FEAT khác): FR-NORM-015 phiên bản theo quy trình mới, mang dòng theo bước còn tồn tại (FEAT-013 — FEAT-012 chỉ sao chép bộ đã khóa với cùng quy trình); FR-AI-007 đề xuất liên kết và nút "Chấp nhận/Bỏ" đề xuất (FEAT-025 — FEAT-012 chỉ hiện nhãn "Đề xuất" và chặn ở FR-NORM-010); FR-WF-011 đặt cờ `needs_update` (FEAT-008 — FEAT-012 chỉ thêm trường và bộ lọc); FR-NORM-017..025 và mọi trường **[1.1]** (`test_system`, `tests_per_tube`, `cost_level`, `apply_k`, `attach_to`, `attach_equipment`, `template_item`, `norm_template`, `copied_from`) là FEAT-034; áp trung vị bấm giờ (FEAT-014); lần tính giá đọc các cấu phần ngoài LABOR (FEAT-015); xuất bộ định mức (`exports/norm_set.py`).

**Thiết kế để FEAT-034 mở rộng**: ánh xạ cấu phần, kiểm dòng, cổng xác nhận và chi phí tạm tính là hàm thuần nhận `dict` dòng; FEAT-034 thêm luật (DI-15, DI-17, FR-NORM-020, 023) bằng cách nối thêm vào danh sách lỗi của cùng hàm (`line_errors`, `confirm_blockers`), không đổi chữ ký. `get_norm_set` trả `meta.has_test_system` = `frappe.get_meta("NC Norm Set").has_field("test_system")` (cùng mẹo `nc_costing_run.py:43`) để lưới thêm cột sau.

## 2. DocType (module NC Costing, đã có từ FEAT-000 — mở rộng, không tạo lại)

Chỉ thêm trường, đổi `reqd` của một trường, bật `track_changes` → không cần patch dữ liệu (`bench migrate` thêm cột; bản ghi cũ để trống là hợp lệ).

### 2.1 NC Norm Set
`track_changes` = 1 (hiện chưa bật). Naming giữ `format:DM-{technical_service}-{department}-v{version_no}`. Thứ tự trường:

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| technical_service, department, procedure, version_no | (đã có) | | Có | `procedure` phải "Đã ban hành" khi tạo (đã có) |
| previous_version **(mới)** | Phiên bản trước | Link NC Norm Set | | Chỉ đọc; `new_version` ghi |
| status | Trạng thái | Select | Có | Đã có; 4 giá trị; `in_standard_filter`, `in_list_view`; chỉ đổi qua API mục 3 (`flags.norm_action`) |
| needs_update **(mới)** | Cần cập nhật | Check | | Chỉ đọc; `in_standard_filter`; FEAT-008 đặt (FR-WF-011) |
| step_change_note **(mới)** | Bước thêm, bỏ, đổi | Small Text | | Chỉ đọc; FEAT-008/013 ghi |
| lines | Dòng định mức | Table NC Norm Line | | Đã có |
| next_line_seq | Số cấp mã dòng kế tiếp | Int | | Đã có, ẩn, chỉ đọc (mã dòng bất biến, không tái dùng) |
| locked_by, locked_on | Người khóa, Thời điểm khóa | Link User, Datetime | | Đã có, chỉ đọc |

### 2.2 NC Norm Line (bảng con)

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| line_id | Mã dòng | Data | Có | Đã có; `L###` cấp từ `next_line_seq`, bất biến (đã có) |
| step_id | Mã bước | Data | | Đã có; DI-04 |
| service_level | Chung cho cả dịch vụ | Check | | Đã có; FR-NORM-005 |
| procedure_resource_row | Dòng nguồn lực gốc | Data | | Đã có; chỉ đọc |
| component | Cấu phần | Select | Có | Đã có, LABOR / DRUG / SUPPLY / EQUIPMENT / INFRA / UTILITY |
| resource_doctype | Loại nguồn lực | Link DocType | Có | Đã có; DI-05; khởi tạo điền theo cấu phần kể cả khi chưa liên kết |
| resource | Nguồn lực | Dynamic Link | **Không** (AMD-012-01) | Trống = "chưa liên kết danh mục"; bắt buộc khi sửa dòng (FR-NORM-003) và trước "Xác nhận chuyên môn" (FR-NORM-010) |
| headcount | Số người | Int | | Đã có; LABOR |
| hospital_qty | Định mức của bệnh viện | Float | Có | Đã có; phút với LABOR, EQUIPMENT, INFRA |
| authority_qty | Định mức ban hành | Float | | Đã có |
| authority_ref **(mới)** | Văn bản ban hành định mức | Data | | |
| uom | Đơn vị | Data | Có | Đã có |
| wastage_rate **(mới)** | Hao hụt (%) | Percent | | DRUG, SUPPLY; 0..100 |
| wastage_reason **(mới)** | Lý do vượt trần | Small Text | | FR-NORM-004 |
| basis | Căn cứ | Select | Có | Đã có; Quy trình / Bấm giờ / Tiêu hao thực tế / Định mức ban hành / Ước tính |
| basis_ref **(mới)** | Tham chiếu căn cứ | Data | | FR-NORM-008 |
| is_excluded **(mới)** | Loại trừ | Check | | FR-NORM-013 |
| exclude_reason **(mới)** | Lý do loại trừ | Select | | Thanh toán riêng / Ngân sách nhà nước bảo đảm / Đã tính trong dịch vụ khác / Không áp dụng / Khác (đủ 5 giá trị data-model, gồm "Không áp dụng" [1.1]) |
| ai_suggested **(mới)** | Đề xuất của AI chưa xử lý | Check | | Chỉ đọc ở FEAT-012 (FEAT-025 đặt và xử lý) |
| confirmed_by **(mới)** | Người xác nhận | Link User | | Chỉ đọc; FR-NORM-009 |
| confirmed_on **(mới)** | Thời điểm xác nhận | Datetime | | Chỉ đọc |

Quyền DocType giữ như hiện có (khớp ma trận mục 4, dòng "Bộ định mức"): NC Clinician, NC Department Head: read, write, create (phạm vi khoa qua `core/permissions.py`); NC Finance, NC Resource Manager, NC Director, NC Consultant, NC Admin, NC Auditor: read; NC Council Member, NC Document Controller: không có; không ai có `delete`. Cột "A" (Dept Head xác nhận chuyên môn; Finance khóa, trả lại) kiểm trong API bằng vai trò, không qua DocPerm. NC Auditor không qua được API ghi nào (`PermissionError`).

### 2.3 Controller `NCNormSet.validate` (mọi đường ghi: form, `frappe.client`, API)
Thứ tự:
1. **Khóa nội dung** (FR-NORM-012, ASM-012-05): bản trước lưu ở "Đã khóa"/"Đã thay thế" → từ chối mọi thay đổi (trừ `flags.allow_replace` của DI-03, đã có). Ở "Đã xác nhận chuyên môn": từ chối đổi `lines` và trường đầu bộ (so `as_dict` các dòng với bản trước), trừ hành động `flags.norm_action` hợp lệ.
2. **Chuyển trạng thái** chỉ khi `flags.norm_action` khớp `norm/workflow.py::TRANSITIONS` (mục 4.4); đổi `status` qua form/`frappe.client` → từ chối "Chỉ đổi trạng thái bằng nút trên lưới định mức". Giữ `flags.allow_lock` (dùng ở `tests/utils.py::make_chain_data`) như một bí danh của hành động "Khóa" do hệ thống/test dựng dữ liệu.
3. Tạo mới: quy trình phải "Đã ban hành" (đã có).
4. `assign_line_ids()` (đã có).
5. **Kiểm dòng**: với mỗi dòng gọi `norm.validation.line_errors(line, ctx)` (mục 4.2), `ctx` gồm `step_ids` của quy trình, `wastage_cap` của bộ tham số hiệu lực (mục 4.5), `changed` = dòng mới hoặc khác bản trước ở bất kỳ trường nhập nào. Gom mọi lỗi, `frappe.throw` một lần, mỗi lỗi một dòng `<br>`, tiêu đề "Dòng định mức chưa hợp lệ". DI-04, DI-05 chuyển vào `line_errors` (giữ thông báo cũ).
6. **Xóa xác nhận khi sửa** (ASM-012-06): dòng `changed` đã có `confirmed_by` → xóa `confirmed_by`, `confirmed_on` (trừ khi chính hành động là `confirm_line`).
7. `on_trash` (đã có): chặn xóa bộ "Đã khóa"; thêm chặn "Đã thay thế".

## 3. API whitelisted — `normcore/api/norm.py` (mới)

Quy ước chung: mọi hàm `@frappe.whitelist()`; tải bộ bằng `frappe.get_doc`; kiểm quyền tường minh trước khi đổi; lỗi nghiệp vụ `frappe.ValidationError` (thông báo tiếng Việt qua `_()`), lỗi quyền `frappe.PermissionError`; `line_id` là mã nghiệp vụ `L###`, không dùng `name` của hàng con. Hàm ghi trả về `get_norm_set(name)` mới để lưới vẽ lại. Kiểm "ghi" = `frappe.has_permission("NC Norm Set", "write", doc=ns, throw=True)` (phạm vi khoa FR-ACC-003). Thao tác của NC Finance (chỉ có R) lưu bằng `ignore_permissions=True` **sau** khi đã kiểm vai trò.

| Hàm | Tham số | Kết quả | Kiểm quyền | Lỗi |
| :-- | :-- | :-- | :-- | :-- |
| `create_norm_set(procedure)` | tên NC Clinical Procedure | `{"name"}` | `has_permission("NC Norm Set","create")` + phạm vi khoa trên bản mới (như `make_norm_set`) | Quy trình chưa ban hành (TC-NORM-02); dòng Nhân lực chưa gắn chức danh (giữ hành vi cũ, Q2) |
| `get_norm_set(name)` | | dict mục 3.1 | `has_permission(read, doc)` | PermissionError |
| `save_line(norm_set, values, line_id=None, allow_duplicate=0)` | `values`: JSON các trường nhập của dòng (2.2, trừ trường chỉ đọc) | `{"saved": true, "norm_set": …}` hoặc `{"saved": false, "duplicates": [{"line_id","step_id","resource"}]}` | ghi; trạng thái "Nháp" | Lỗi `line_errors`; `line_id` không có; bộ không ở "Nháp" ("Bộ định mức đã <trạng thái>, không sửa được.") |
| `delete_line(norm_set, line_id)` | | `norm_set` | ghi; "Nháp" | Dòng có `procedure_resource_row` → "Dòng lấy từ quy trình không xóa được; đánh dấu Loại trừ nếu không tính" (ASM-012-07) |
| `confirm_line(norm_set, line_id)` | | `norm_set` | vai trò NC Clinician hoặc NC Department Head **và** ghi (phạm vi khoa); "Nháp" | Dòng chưa liên kết hoặc còn đề xuất AI → "Dòng Lxxx chưa liên kết danh mục/còn đề xuất AI, chưa xác nhận được" (ASM-012-08) |
| `confirm_set(norm_set)` | | `norm_set` | vai trò NC Department Head **và** ghi (khoa); "Nháp" | `confirm_blockers` khác rỗng → ValidationError liệt kê (TC-NORM-05) |
| `return_set(norm_set, reason)` | | `norm_set` | vai trò NC Finance; "Đã xác nhận chuyên môn" | `reason` trống sau strip → "Cần nhập lý do trả lại" |
| `lock_set(norm_set)` | | `norm_set` | vai trò NC Finance; "Đã xác nhận chuyên môn" | Trạng thái khác → "Chỉ khóa được bộ định mức Đã xác nhận chuyên môn" |
| `new_version(norm_set)` | | `{"name"}` | `has_permission("NC Norm Set","create")` + ghi theo khoa của bộ nguồn; nguồn "Đã khóa" | Nguồn không "Đã khóa" → "Chỉ tạo phiên bản mới từ bộ Đã khóa"; đã có bộ "Nháp"/"Đã xác nhận chuyên môn" của cùng (dịch vụ, khoa) → trả tên bộ đó kèm thông báo (ASM-012-09) |

Chi tiết:
- `confirm_line`: chỉ ghi `confirmed_by` = `frappe.session.user`, `confirmed_on` = `now_datetime()` cho đúng dòng; lưu qua `save()` với `flags.norm_action = "confirm_line"` (không xóa xác nhận của dòng khác, TC-NORM-12).
- `return_set`: về "Nháp"; giữ xác nhận các dòng; lý do ghi vào `NC Audit Event.detail` qua `flags.audit_detail` (cơ chế FEAT-007 `core/audit.py::_log_state`) và một Comment "Info" trên bộ.
- `lock_set`: thân hàm chuyển từ `NCNormSet.lock()`; `NCNormSet.lock()` giữ là lớp mỏng gọi cùng hàm nội bộ (nút cũ, test cũ), **cùng điều kiện** "Đã xác nhận chuyên môn" (Q1). Kiểm vai trò trước kiểm trạng thái (giữ `PermissionError` cho người không phải Finance).
- `new_version`: bộ mới cùng `technical_service`, `department`, `procedure`; `version_no` = max + 1; `previous_version` = nguồn; sao chép mọi dòng **giữ `line_id`**, `next_line_seq` lấy từ nguồn; xóa `confirmed_by`, `confirmed_on`; `status` "Nháp". Bộ nguồn giữ "Đã khóa" đến khi bộ mới khóa (DI-03 đã có).
- `make_norm_set(procedure)` (FEAT-000, nút form quy trình, test cũ): giữ tên và đường dẫn, gọi `create_norm_set`, trả `name` (chuỗi) như cũ.

### 3.1 Kết quả `get_norm_set`
```
{
  "doc": {name, technical_service, technical_service_name, department, procedure, version_no, status,
          previous_version, needs_update, step_change_note, locked_by, locked_on, modified},
  "steps": [{"step_id", "step_title", "phase"}...],          # theo thứ tự quy trình
  "groups": [{"step_id"|null, "title", "lines": [line...], "total": số|null}],  # cuối: nhóm "Chung cho cả dịch vụ"
  line = {các trường 2.2, "applied_qty", "resource_label", "unlinked": bool, "duplicate_of": [line_id],
          "cost": {"rate", "amount"} | {"missing": "<lý do>"}, "excluded": bool},
  "summary": {"by_step_component": {step_key: {component: amount}}, "by_component": {...}, "total", "incomplete": bool,
              "parameter_set": name|null},
  "wastage_cap": số, "wastage_cap_source": name|"mặc định",
  "blockers": [{"line_id", "reasons": [...]}],              # confirm_blockers, để lưới tô dòng
  "actions": ["save_line","delete_line","confirm_line","confirm_set","return_set","lock_set","new_version"],  # theo người dùng
  "options": {"component", "basis", "exclude_reason", "resource_doctype_by_component"},
  "meta": {"has_test_system": bool}
}
```
`actions` chỉ là gợi ý giao diện; mọi hàm ghi tự kiểm lại.

## 4. Logic thuần (không import `frappe`, test bằng pytest)

### 4.1 `normcore/norm/init_from_procedure.py` (mới; FEAT-013 mở rộng)
- `COMPONENT_BY_RESOURCE_TYPE`: Nhân lực → LABOR; Thuốc, Hóa chất, Dịch truyền → DRUG; Vật tư → SUPPLY; Thiết bị → EQUIPMENT; Phòng → INFRA; Khác → SUPPLY (ASM-012-02).
- `RESOURCE_DOCTYPE_BY_COMPONENT` (DI-05, chuyển từ `nc_norm_set.COMPONENT_DOCTYPE`): LABOR → NC Job Title; DRUG, SUPPLY, UTILITY → NC Item; EQUIPMENT → NC Equipment; INFRA → NC Room.
- `lines_from_resources(resources) -> list[dict]`: mỗi dòng nguồn lực một dòng: `step_id`, `procedure_resource_row` = `resource_row_id`, `component`, `resource_doctype` theo cấu phần, `resource` = `linked_name` nếu `linked_doctype` khớp DI-05, ngược lại trống; `headcount` = `headcount or 1` với LABOR, trống với loại khác; `hospital_qty` = `quantity`; `uom`; `basis` = "Quy trình"; `ai_suggested` = 0. Thứ tự = thứ tự dòng nguồn lực. Trả kèm danh sách lỗi: dòng Nhân lực chưa gắn chức danh (giữ FEAT-000, Q2).

### 4.2 `normcore/norm/validation.py` (mới)
- `REQUIRED_LABELS`, `EXCLUDE_REASONS` (5), `BASIS_VALUES` (5), `COMPONENTS` (6).
- `line_errors(line: dict, ctx: dict) -> list[str]`: FR-NORM-003 (khi `ctx.changed`: thiếu `resource`; luôn: thiếu `component`, `uom`, `hospital_qty` ≤ 0 khi không loại trừ; LABOR: `headcount` < 1 → "Số người", `hospital_qty` ≤ 0 → "Số phút"), thông báo dạng "Dòng L003 thiếu: Đơn vị, Số phút"; FR-NORM-004; FR-NORM-005 (dòng không có `procedure_resource_row`: không có cả `step_id` lẫn `service_level`, hoặc có cả hai → lỗi); DI-04; DI-05; FR-NORM-008 (`basis` ngoài danh sách); FR-NORM-013 (`is_excluded` mà `exclude_reason` trống/ngoài danh sách); số âm (`authority_qty`, `wastage_rate` ngoài 0..100). Không đổi dữ liệu.
- `duplicates(lines) -> dict[line_id, list[line_id]]`: FR-NORM-014; khóa = (`step_id` hoặc "service", `resource_doctype`, `resource`), bỏ dòng chưa liên kết và dòng loại trừ.
- `confirm_blockers(lines) -> list[{"line_id","reasons"}]`: FR-NORM-010; lý do theo thứ tự "Chưa xác nhận", "Chưa liên kết danh mục", "Còn đề xuất AI chưa xử lý"; mỗi dòng một mục (TC-NORM-05: 2 dòng).

### 4.3 `normcore/costing/provisional.py` (mới; FR-NORM-016; đo độ phủ 90%)
- `line_amount(component, applied_qty, rate, headcount=1, wastage_rate=0, reuse_count=1) -> Decimal`, làm tròn 2 số lẻ HALF_UP như golden `r2`:
  - LABOR: `engine.labor_line` (BR-COST-002, đã có).
  - DRUG, SUPPLY: `q × (1 + wastage) × rate ÷ reuse` (BR-COST-003; `rate` là đơn giá một đơn vị định mức từ `pricing.unit_price_per_norm`, cùng công thức `pricing.material_line`; dùng lại hàm đó nếu có giá gốc).
  - EQUIPMENT: `q ÷ 60 × rate` (BR-COST-004, `rate` = `resources.machine_hourly_rate` qua `NC Equipment.indicative()`).
  - INFRA: `q ÷ 60 × rate` (BR-COST-005, `rate` = `resources.room_hourly_rate`).
  - UTILITY: `q × rate` (BR-COST-006).
- `wastage_rate` vào hàm là phân số (Percent ÷ 100; controller đổi).
- `summarize(rows) -> {"by_step_component", "by_component", "total", "incomplete"}`: `rows` = (step_key, component, amount|None, excluded); dòng loại trừ = 0 (như golden); dòng `None` (thiếu đơn giá/chưa liên kết) không cộng và bật `incomplete`.
- Lượng áp dụng luôn qua `engine.applied_qty` (BR-COST-007). Không chế công thức mới: mỗi nhánh dẫn chiếu dòng golden `direct_lines`.
- Đơn giá do lớp API nạp (không thuộc hàm thuần): LABOR `rate_per_hour` của dòng NC Job Title Rate trong bộ tham số hiệu lực; NC Item: `pricing.select_price` của NC Item Price tại hôm nay + `norm_units_per_purchase_unit`, `reuse_count`, `billed_separately` (thanh toán riêng → 0); NC Equipment `indicative(today, expired_mode của bộ tham số)["hourly_rate"]`; NC Room `room_hourly_rate(annual_infrastructure_cost, available_hours_per_year)`; UTILITY: đơn giá hiệu lực của NC Item tiện ích (ASM-012-11). Thiếu bất kỳ → `{"missing": "Chưa có đơn giá"}`.

### 4.4 `normcore/norm/workflow.py` (mới)
`TRANSITIONS = {("Nháp","confirm_set"): "Đã xác nhận chuyên môn", ("Đã xác nhận chuyên môn","lock_set"): "Đã khóa", ("Đã xác nhận chuyên môn","return_set"): "Nháp", ("Đã khóa","replace"): "Đã thay thế"}`; `next_status(status, action)` (None nếu không hợp lệ); `EDITABLE = {"Nháp"}`; `ROLE_OF_ACTION` = confirm_set: NC Department Head; lock_set, return_set: NC Finance; confirm_line: NC Clinician, NC Department Head. Khớp `data-model.md` 5.2 (có test so bảng).

### 4.5 Bộ tham số hiệu lực
`norm/validation.py::effective_parameter_set(rows, today)`: trong các NC Costing Parameter Set có `effective_from` ≤ hôm nay, lấy `effective_from` lớn nhất, hòa thì `name` lớn nhất (ASM-012-10). Không có → `wastage_cap` = `parameters.DEFAULTS["wastage_cap"]` (10), lưới ghi "Trần hao hụt mặc định — chưa có bộ tham số hiệu lực"; chi phí tạm tính LABOR "Chưa có đơn giá".

## 5. Giao diện (chi tiết ở `ui-design.md`)
- SCR-DSK-013: List view chuẩn NC Norm Set (`nc_norm_set_list.js`): chỉ báo 4 trạng thái theo `design.md` mục 3, bộ lọc trạng thái, khoa, "Cần cập nhật".
- SCR-DSK-014: Desk Page `norm-grid` (Vue 3), `normcore/nc_costing/page/norm_grid/` + `normcore/public/js/norm_grid/` (`norm_grid.bundle.js`, `NormGrid.vue`); chỉ gọi `api/norm.py`.
- Form NC Norm Set: bảng `lines` chỉ đọc trên form, nút "Mở lưới định mức"; bỏ nút tạm "Khóa" của FEAT-000. Form NC Clinical Procedure: nút "Khởi tạo bộ định mức" gọi `create_norm_set` rồi mở `norm-grid`.

## 6. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test (tên gợi ý) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Quy trình ban hành có 6 dòng nguồn lực (2 Nhân lực, Thuốc, Vật tư, Thiết bị, Phòng) → bộ "Nháp" 6 dòng; mỗi dòng có `step_id` và `procedure_resource_row` đúng dòng gốc, cấu phần theo 4.1 | TC-NORM-01 | FR-NORM-001 | `api/test_norm.py::test_TC_NORM_01_khoi_tao_6_dong_mang_ma_buoc_va_dong_goc` |
| 2 | Quy trình còn "Nháp" → `create_norm_set` ValidationError, không tạo bản ghi | TC-NORM-02 | FR-NORM-002 | `test_TC_NORM_02_*` (đã có ở `test_nc_norm_set.py`, thêm ca qua API) |
| 3 | L03 (20, ban hành 25) → 20; L09 (15, ban hành 10) → 10; L01 (10, không có) → 10, số lấy từ `golden_engine.NORMS` | TC-NORM-03 | FR-NORM-006, 007 | `tests/golden/test_norm_golden.py::test_TC_NORM_03_luong_ap_dung_L03_L09_L01` |
| 4 | Bộ tham số hiệu lực trần 5%; dòng SUPPLY hao hụt 8% không lý do → từ chối lưu, thông báo "Lý do vượt trần"; có lý do → lưu | TC-NORM-04 | FR-NORM-004 | `test_TC_NORM_04_vuot_tran_hao_hut_can_ly_do` |
| 5 | Bộ có 1 dòng chưa xác nhận và 1 dòng chưa liên kết (các dòng khác đã xác nhận) → `confirm_set` từ chối, thông báo nêu đúng 2 mã dòng, trạng thái giữ "Nháp"; gỡ hết → chuyển "Đã xác nhận chuyên môn" | TC-NORM-05 | FR-NORM-010 | `test_TC_NORM_05_con_dong_chua_xac_nhan_chua_lien_ket_tu_choi` |
| 6 | Finance `lock_set` bộ "Đã xác nhận chuyên môn" → "Đã khóa", `locked_by`; sau đó `save_line`, `doc.save()`, `frappe.client.set_value` đều bị từ chối, CSDL không đổi; `new_version` tạo bộ "Nháp" v+1, `previous_version`, giữ `line_id`, xác nhận trống | TC-NORM-06 | FR-NORM-011, 012 | `test_TC_NORM_06_khoa_tu_choi_sua_tao_phien_ban_moi` |
| 7 | `is_excluded` = 1 không `exclude_reason` → từ chối; lý do ngoài danh sách → từ chối; "Thanh toán riêng" → lưu | TC-NORM-07 | FR-NORM-013 | `test_TC_NORM_07_loai_tru_can_ly_do_trong_danh_sach` |
| 8 | Thêm dòng UTILITY điện không có `step_id`, không `service_level` → từ chối; có `service_level` → lưu với `step_id` trống; có `step_id` hợp lệ → lưu | TC-NORM-09 | FR-NORM-005 | `test_TC_NORM_09_dong_them_phai_gan_buoc_hoac_chung` |
| 9 | Sửa dòng SUPPLY xóa `uom` → từ chối, thông báo có "Đơn vị"; sửa dòng LABOR xóa số phút → từ chối, thông báo có "Số phút"; CSDL không đổi | TC-NORM-10 | FR-NORM-003 | `test_TC_NORM_10_thieu_don_vi_thieu_so_phut_tu_choi` |
| 10 | `save_line` L03 `basis` "Định mức ban hành", `basis_ref` "QĐ 123/QĐ-BYT" → lưu cả hai; `basis` "Theo cảm tính" qua API → ValidationError | TC-NORM-11 | FR-NORM-008 | `test_TC_NORM_11_can_cu_va_tham_chieu` |
| 11 | NC Clinician gán khoa K01 `confirm_line` L01 → L01 có `confirmed_by` = người đó, `confirmed_on`; các dòng khác trống; Clinician khoa khác → PermissionError | TC-NORM-12 | FR-NORM-009 | `test_TC_NORM_12_xac_nhan_mot_dong` |
| 12 | Hai dòng cùng bước cùng nguồn lực → `save_line` trả `saved: false` + `duplicates`; `allow_duplicate=1` → lưu | — | FR-NORM-014 | `test_FR_NORM_014_canh_bao_trung` |
| 13 | Chi phí tạm tính của 11 dòng DV01 golden bằng thành tiền `golden_engine.direct_lines("DV01")` từng dòng; tổng theo bước × cấu phần khớp; dòng loại trừ 0; dòng thiếu đơn giá → `incomplete` | — | FR-NORM-016 | `tests/golden/test_norm_golden.py::test_FR_NORM_016_*`, `tests/unit/test_norm_provisional.py`; `api/test_norm.py::test_FR_NORM_016_get_norm_set_co_chi_phi_tam_tinh` |
| 14 | Quyền: NC Council Member (không có quyền) đọc/ghi → PermissionError; NC Auditor đọc được `get_norm_set`, mọi hàm ghi → PermissionError; Finance không `save_line`, không `confirm_set`; Clinician không `confirm_set`, không `lock_set` | — | FR-ACC-003, FR-ACC-007 | `test_quyen_norm_set_*` |
| 15 | Trả lại: Finance `return_set` không lý do → từ chối; có lý do → "Nháp", lý do trong `NC Audit Event.detail` | — | data-model 5.2 | `test_tra_lai_can_ly_do` |
| 16 | `TRANSITIONS` khớp data-model 5.2; `line_errors`, `confirm_blockers`, `duplicates`, `lines_from_resources` phủ mọi nhánh | — | FR-NORM-003..014 | `tests/unit/test_norm_validation.py`, `test_norm_init.py`, `test_norm_workflow.py` |
| 17 | Toàn bộ test cũ xanh (sau Quyết định Lead Q1); độ phủ `normcore/costing` ≥ 90% | — | NFR-MNT-001 | T14 |

## 7. Rủi ro
- **Test cũ gọi `lock()` từ "Nháp"** (12 chỗ, mục 10 Q1): đổi điều kiện khóa làm đỏ test cũ nếu không có Quyết định Lead.
- **Frappe lưu Float trống thành 0**: không phân biệt "chưa nhập" với 0 ở controller; FR-NORM-003 coi `hospital_qty` ≤ 0 là thiếu (trừ dòng loại trừ). `authority_qty` 0 = không có (ASM-013, khác golden khi ban hành bằng 0 — chưa có TC nào dùng 0).
- Chi phí tạm tính cần đơn giá của FEAT-009/010/011; dữ liệu thiếu thì lưới ghi "Chưa có đơn giá" — không chặn lưu.
- Lưới > 100 dòng (UXQ-05): `get_norm_set` một lần gọi, không phân trang; Vue vẽ theo nhóm bước, thu gọn được.
- FEAT-034 thêm cột/luật vào cùng hàm: giữ chữ ký `line_errors(line, ctx)`, `ctx` là dict mở.

## 8. Tệp chạm tới
Mới: `normcore/api/norm.py`, `normcore/api/test_norm.py`, `normcore/norm/__init__.py`, `init_from_procedure.py`, `validation.py`, `workflow.py`, `normcore/costing/provisional.py`, `normcore/tests/unit/test_norm_*.py`, `normcore/tests/golden/test_norm_golden.py`, `normcore/nc_costing/page/norm_grid/*`, `normcore/public/js/norm_grid/*`, `normcore/nc_costing/doctype/nc_norm_set/nc_norm_set_list.js`, `docs/decisions/assumptions/FEAT-012.md` (đã có từ BA), `docs/as-built/FEAT-012.md`.
Sửa: `nc_norm_set.json`, `nc_norm_set.py`, `nc_norm_set.js`, `nc_norm_line.json`, `nc_clinical_procedure.js` (nút khởi tạo), `normcore/translations/vi.csv`, `docs/data-model.md` (áp AMD-012-01), test cũ theo Q1 (chỉ dòng dựng dữ liệu), `normcore/tests/utils.py` (helper Q1), `docs/rtm-testref.md` (mục `## FEAT-012`, theo quy tắc 4).

## 9. Ghi chú cho Dev
- Mọi lệnh `bench` qua `scripts/with_bench.sh`, migrate và test trong cùng một lần gọi.
- Chuỗi giao diện tiếng Việt qua `_()`/`__()`; khóa `vi.csv` sắp thứ tự (`test_vi_csv_order.py`).
- Không đổi `costing/engine.py` (FEAT-015); `provisional.py` chỉ dùng `engine.applied_qty`, `engine.labor_line`, `pricing.*`, `resources.*`.

## 10. Câu hỏi cho Lead

**Q1 — Điều kiện "Khóa" và test cũ.** FR-NORM-011 + data-model 5.2: "Khóa" chỉ từ "Đã xác nhận chuyên môn". Khung FEAT-000 (ASM-010, "nút tạm… luồng xác nhận chuyên môn là FEAT-012") cho khóa từ "Nháp", và 12 chỗ test cũ gọi `ns.lock()` trên bộ "Nháp": `nc_norm_set/test_nc_norm_set.py` (2 test: `test_khoa_chi_nc_finance_va_khong_sua_khong_xoa`, `test_DI03_bo_khoa_moi_thay_the_bo_cu`, 3 lần gọi), `nc_costing_run/test_nc_costing_run.py` (4), `nc_test_system/test_nc_test_system.py` (3), `nc_core/doctype/nc_audit_event/test_nc_audit_event.py` (1), `api/test_ai.py::test_TC_AI_07_*` (1). Hai test `tests/test_form_actions.py::test_lock_clinician_bi_tu_choi`, `test_lock_auditor_bi_tu_choi` không cần đổi (kiểm vai trò đứng trước kiểm trạng thái nên vẫn PermissionError). CLAUDE.md mục 3.1 không cho sửa test nếu chưa có Quyết định Lead.
- **PA1 (đề xuất)**, theo tiền lệ FEAT-007 Q1/ASM-007-16: thêm helper `tests/utils.py::confirm_norm_set(ns)` (dựng dữ liệu bằng `db_set("status","Đã xác nhận chuyên môn")`), chèn **một dòng dựng dữ liệu** trước mỗi `lock()` ở 12 chỗ trên; không đổi/xóa dòng `assert*` nào. `lock()` chỉ từ "Đã xác nhận chuyên môn".
- PA2: giữ `NCNormSet.lock()` khóa được từ "Nháp" (không sửa test), chỉ `api/norm.py::lock_set` kiểm "Đã xác nhận chuyên môn". Nhược: NC Finance vẫn gọi được `lock` qua `run_doc_method`, bỏ qua FR-NORM-010 → FR-NORM-011 chỉ đạt hình thức.

**Q2 — Dòng Nhân lực chưa gắn chức danh khi khởi tạo.** FR-NORM-001 "sinh một dòng cho mỗi dòng nguồn lực"; test cũ `test_nguon_luc_nhan_luc_chua_gan_chuc_danh_bi_tu_choi` khẳng định khởi tạo bị từ chối khi dòng Nhân lực chưa gắn NC Job Title.
- **PA1 (đề xuất)**: giữ hành vi cũ (không sửa test): Nhân lực phải gắn chức danh mới khởi tạo được; các loại khác được để chưa liên kết (trình soạn FEAT-006 chỉ gắn được chức danh, nên dòng Nhân lực chưa gắn là lỗi dữ liệu quy trình, sửa ở quy trình). Ghi ASM-012-03.
- PA2: cho mọi loại kể cả Nhân lực để chưa liên kết (đúng chữ FR-NORM-001 hơn), đổi test cũ thành kiểm dòng được sinh và bị chặn ở FR-NORM-010.
