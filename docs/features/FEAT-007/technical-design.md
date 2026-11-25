# FEAT-007 — Phê duyệt ba cấp, ban hành, in — Thiết kế kỹ thuật

Issue NORM-34. Nguồn: `srs.md` FR-PROC-008, FR-PROC-010, FR-PROC-011, FR-PROC-012, FR-WF-001..008, FR-WF-013, FR-NOTI-001; `use-cases.md` UC-006; `data-model.md` 3.1 (NC Review Comment, NC Settings, NC Department `head_user`), 3.3 (NC Clinical Procedure và bảng con), mục 4 (dòng "Quy trình", "Ý kiến thẩm định"), mục 5.1, DI-01, DI-02, DI-07; `architecture.md` ADR-002, ADR-011, ADR-014, ADR-015; `ux-foundations.md` SCR-DSK-010; TC-PROC-05, 06, 07, TC-WF-01, 02, 03, 04, 08. Phụ thuộc FEAT-006, FEAT-001 (đều DONE; As-Built `docs/as-built/FEAT-006.md`, `docs/as-built/FEAT-001.md`).

Giả định: `docs/decisions/assumptions/FEAT-007.md` (ASM-007-01..15). Sửa thiết kế: `docs/decisions/amendments/AMD-007-01.md` (thư ký hội đồng). Q1 (mục 9) đã có Quyết định Lead: PA1 (ASM-007-16).

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-PROC-008 | Gửi duyệt bị từ chối khi có trích dẫn "Khác biệt" trống `deviation_reason`; thông báo nêu từng trích dẫn (phần/mã bước, số dòng). Lưu nháp vẫn cho phép (data-model: "BB khi Khác biệt" áp tại gửi duyệt) |
| FR-PROC-012 | Gửi duyệt kiểm đủ ba lỗi, **liệt kê tất cả** lỗi một lần, giữ "Nháp": không có bước giai đoạn "Thực hiện"; bước có `description` trống (sau strip); dòng nguồn lực `quantity` ≤ 0 hoặc trống, hoặc `uom` trống |
| FR-WF-001 | Gửi duyệt → "Chờ trưởng khoa duyệt"; thông báo trưởng khoa của khoa chủ trì |
| FR-WF-002 | Trưởng khoa (cùng khoa) "Đồng ý" → "Chờ hội đồng thẩm định"; thông báo mọi NC Council Member |
| FR-WF-003 | DocType NC Review Comment (mới); ghi ý kiến gắn phần hoặc `step_id`; hiển thị theo bước cho người soạn sau khi bị trả lại |
| FR-WF-004 | Thư ký hội đồng (AMD-007-01) "Thông qua" → "Chờ ban hành"; thông báo mọi NC Director |
| FR-WF-005 | NC Director "Ban hành" bắt buộc `decision_no`, `effective_date`; khóa nội dung; "Đã ban hành" |
| FR-WF-006 | Tác vụ ngày: phiên bản mới "Đã ban hành" có `effective_date` ≤ hôm nay → phiên bản "Đã ban hành" trước của cùng (dịch vụ, khoa) sang "Đã thay thế". Chạy thêm ngay khi ban hành nếu ngày hiệu lực ≤ hôm nay |
| FR-WF-007 | "Từ chối" ở mọi cấp chờ: bắt buộc lý do; về "Nháp"; thông báo người soạn |
| FR-WF-008 | Ở "Đã ban hành", "Đã thay thế", "Đã thu hồi": từ chối mọi chỉnh sửa nội dung qua form (Desk), qua `frappe.client`, qua API FEAT-006. Mở rộng (ASM-007-03): khóa cả ở các trạng thái chờ |
| FR-WF-013 (Could) | Tác vụ ngày nhắc người duyệt của cấp đang chờ quá `NC Settings.approval_reminder_days` (mặc định 7) |
| FR-PROC-010 | Print Format mặc định (TBD-04, ASM-007-08) + API tải PDF; bản chưa ban hành có chữ "DỰ THẢO"; bản ban hành có số quyết định, phiên bản, ngày hiệu lực, khối chữ ký |
| FR-PROC-011 (Should) | API tải DOCX cùng nội dung bản PDF (python-docx, ADR-015) |
| FR-NOTI-001 | Chỉ phần thông báo của luồng duyệt (Notification Log có liên kết bản ghi, ASM-007-01). `core/notify.py`, trang chủ, email (FR-NOTI-002) là FEAT-002 |

Không làm: "Thu hồi" (Đã ban hành → Đã thu hồi), tạo phiên bản sửa đổi, so sánh phiên bản (FEAT-008); sinh bộ định mức (FEAT-012 — chỉ để sẵn trạng thái và hàm `effective_procedure`, mục 5.2); duyệt bộ định mức, phương án giá. Không đổi trình soạn SCR-DSK-009 ngoài nút "Gửi duyệt" và chế độ thẩm định (ui-design).

Dùng lại, không làm lại: trình soạn `procedure-editor` và API `normcore/api/procedure.py` (FEAT-006); phạm vi khoa `core/permissions.py` (`get_user_departments`, `has_permission`) (FEAT-001); sổ sự kiện `core/audit.py` (FEAT-003: chuyển `workflow_state` tự ghi "Chuyển trạng thái"; `log_export` cho "Xuất tệp"); mẫu Notification Log của `api/compliance.py` (FEAT-033, ASM-100).

## 2. DocType

Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1.

### 2.1 Mới — NC Review Comment (module NC Core, data-model 3.1)
Naming: tự động (`hash`). `track_changes` = 1.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| ref_doctype | Loại bản ghi | Link DocType | Có | FEAT-007 chỉ nhận `NC Clinical Procedure` (ASM-007-05); phương án giá thêm ở FEAT của nó |
| ref_name | Bản ghi | Dynamic Link (`ref_doctype`) | Có | `in_standard_filter` |
| target_section | Phần | Select | | Cùng danh sách với `NC Procedure Citation.target_section` (8 phần FR-PROC-001) |
| target_step_id | Mã bước | Data | | Phải tồn tại trong `steps` của quy trình |
| comment | Ý kiến | Text | Có | Không rỗng sau strip |
| resolved | Đã xử lý | Check | | |
| review_state **(ASM-007-05)** | Cấp thẩm định | Data | | Chỉ đọc; trạng thái quy trình khi ghi ý kiến. Trường phụ trợ, không thêm nghĩa nghiệp vụ |

`validate`: `ref_doctype` = NC Clinical Procedure; không đồng thời có `target_section` và `target_step_id`; `target_step_id` tồn tại; chỉ tạo khi quy trình ở một trạng thái chờ (Chờ trưởng khoa duyệt / Chờ hội đồng thẩm định / Chờ ban hành); sau khi tạo, chỉ `resolved` được đổi (ASM-007-05). Không xóa (không vai trò nào có `delete`).

Quyền (ma trận mục 4, dòng "Ý kiến thẩm định"): NC Department Head, NC Council Member, NC Director: read, write, create; NC Clinician, NC Finance, NC Document Controller, NC Consultant, NC Admin, NC Auditor: read; NC Resource Manager: không có. Ngoài DocPerm, API kiểm người gọi đọc được quy trình (`frappe.has_permission("NC Clinical Procedure", "read", doc=…)`, phạm vi khoa FEAT-001). `scripts/check_conventions.py` thêm `"NC Review Comment": "Ý kiến thẩm định"` vào `DOCTYPE_ROW` (tiền lệ FEAT-033).

### 2.2 Đổi — NC Settings (Single, đã có từ FEAT-033)
| Trường | Nhãn | Kiểu | Mặc định | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| approval_section | Phê duyệt quy trình | Section Break | | |
| approval_reminder_days | Số ngày nhắc duyệt | Int | 7 | Đã có ở data-model 3.1 [FR-WF-013, FR-ADM-003]; > 0 |
| council_secretary **[AMD-007-01]** | Thư ký hội đồng | Link User | | Người có vai trò NC Council Member [FR-WF-004]; `validate` kiểm vai trò |

Chỉ thêm trường → không cần patch.

### 2.3 Đổi — NC Clinical Procedure (không thêm trường)
Controller `nc_clinical_procedure.py`:
- **Chuyển trạng thái**: chỉ qua `procedure/approval.py` + API mục 3 (đặt `flags.workflow_action`) hoặc tác vụ hệ thống (`db_set`, mục 4). Lưu thường đổi `workflow_state` → `ValidationError`. Bản mới phải "Nháp" (giữ).
- **Khóa nội dung (FR-WF-008, DI-07, ASM-007-03)**: khi `workflow_state` trước khi lưu ≠ "Nháp", so trường nội dung giữa bản trước và bản lưu: 7 phần văn bản, `doctor_request`, `technical_service`, `department`, `version_no`, `previous_version`, `copied_from`, `ai_log`, `next_step_seq`, `next_resource_seq`, mọi bảng con (`steps`, `resources`, `citations`, so theo giá trị trường, bỏ `name`, `modified`). Khác → `ValidationError` "Quy trình đã ban hành, không sửa được. Tạo phiên bản mới." (trạng thái đóng) hoặc "Quy trình đang chờ duyệt, không sửa được. Từ chối để trả về Nháp." (trạng thái chờ). Trường được đổi ngoài "Nháp": `workflow_state` (theo luồng), `decision_no`, `effective_date` (chỉ trong hành động "Ban hành"), `needs_review` (FR-LIB-009, hệ thống).
- `on_trash`: từ chối xóa ở mọi trạng thái ≠ "Nháp" (DI-07).
- `publish()` (nút tạm FEAT-006) giữ tên, thành lớp mỏng gọi `apply_action(self.name, "Ban hành", decision_no=self.decision_no, effective_date=self.effective_date)`: kiểm vai trò NC Director trước (PermissionError), rồi đòi trạng thái "Chờ ban hành". Hệ quả cho test cũ: mục 9, Q1. Bỏ hẳn `flags.allow_publish` khỏi mã sản phẩm khi không còn ai dùng (ASM-007-16); không có đường tắt chuyển trạng thái nào ngoài `apply_action` và tác vụ hệ thống `supersede_due`.
- `DI-02` giữ nguyên (các trạng thái chờ tính là "đang duyệt").

### 2.4 Frappe Workflow (fixture, ADR-011)
- Workflow State thêm: "Chờ trưởng khoa duyệt", "Chờ hội đồng thẩm định", "Chờ ban hành", "Đã thay thế", "Đã thu hồi" (cùng "Nháp", "Đã ban hành" đã có). Workflow Action Master: "Gửi duyệt", "Đồng ý", "Thông qua", "Ban hành", "Từ chối".
- Workflow `NC Clinical Procedure` (`workflow_state_field = workflow_state`, `is_active = 1`, `send_email_alert = 0`, `override_status = 1`), mọi trạng thái `doc_status = 0`:

| Trạng thái | allow_edit |
| :-- | :-- |
| Nháp | NC Clinician (thêm dòng NC Department Head) |
| Chờ trưởng khoa duyệt | NC Department Head |
| Chờ hội đồng thẩm định | NC Council Member |
| Chờ ban hành | NC Director |
| Đã ban hành / Đã thay thế / Đã thu hồi | NC Director |

| Từ | Hành động | Đến | allowed | condition |
| :-- | :-- | :-- | :-- | :-- |
| Nháp | Gửi duyệt | Chờ trưởng khoa duyệt | NC Clinician | |
| Chờ trưởng khoa duyệt | Đồng ý | Chờ hội đồng thẩm định | NC Department Head | |
| Chờ trưởng khoa duyệt | Từ chối | Nháp | NC Department Head | |
| Chờ hội đồng thẩm định | Thông qua | Chờ ban hành | NC Council Member | `frappe.session.user == frappe.db.get_value("NC Settings", "NC Settings", "council_secretary")` |
| Chờ hội đồng thẩm định | Từ chối | Nháp | NC Council Member | như trên |
| Chờ ban hành | Ban hành | Đã ban hành | NC Director | |
| Chờ ban hành | Từ chối | Nháp | NC Director | |

`allow_self_approval = 1` (ASM-007-12). NC Auditor không có trong `allowed` hay `allow_edit` (`core/readonly.py::workflow_violations` bắt). "Đã ban hành → Đã thay thế" không phải transition: hệ thống `db_set` (mục 4). "Thu hồi" để FEAT-008.
- `hooks.py` `fixtures`: mở rộng bộ lọc Workflow State theo 7 tên trên; thêm `{"dt": "Workflow Action Master", "filters": [["name", "in", [...5 tên]]]}` và `{"dt": "Workflow", "filters": [["name", "=", "NC Clinical Procedure"]]}`. Tệp `normcore/fixtures/workflow.json`, `workflow_action_master.json`.

### 2.5 Print Format (fixture chuẩn của module)
`normcore/nc_procedure/print_format/nc_clinical_procedure_standard/` — Print Format "Quy trình kỹ thuật (mặc định)", `standard = Yes`, Jinja, `doc_type = NC Clinical Procedure`, đặt làm `default_print_format` của DocType. Bố cục: mục 6.

## 3. API whitelisted — `normcore/api/procedure_workflow.py` (mới)

Mọi hàm kiểm quyền tường minh; lỗi dữ liệu → `frappe.ValidationError` (`frappe.throw`, tiếng Việt), lỗi quyền → `frappe.PermissionError`. Bản ghi lưu bằng `ignore_permissions=True` **sau** khi đã kiểm (NC Council Member, NC Director chỉ có R trên DocType, mục 4 "R, A").

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `get_review(procedure)` | tên quy trình | `{workflow_state, actions: [..], is_secretary, deviations: [...], comments_by_step: {S001: [...]}, comments_by_section: {...}, comments_general: [...], open_comments: n, last_reject: {by, at, reason} \| null, decision_no, effective_date}` | `read` trên quy trình. `actions` = hành động người gọi được làm ở trạng thái hiện tại (theo bảng 2.4 + điều kiện mục 3.1) |
| `apply_action(procedure, action, reason=None, decision_no=None, effective_date=None)` | `action` ∈ Gửi duyệt / Đồng ý / Thông qua / Ban hành / Từ chối | `{workflow_state}` | Mục 3.1. Hành động không hợp lệ ở trạng thái → ValidationError "Hành động … không áp dụng ở trạng thái …" |
| `add_review_comment(procedure, comment, target_section=None, target_step_id=None)` | | `{name}` | `create` trên NC Review Comment + `read` quy trình; kiểm `validate` 2.1 |
| `set_comment_resolved(name, resolved)` | | `{resolved}` | `write` trên NC Review Comment |
| `download_pdf(procedure)` | | tệp PDF (`frappe.local.response` `type = download`), tên `<name>.pdf` | `read` trên quy trình (ASM-007-09); ghi `audit.log_export("PDF", …)` |
| `download_docx(procedure)` | | tệp DOCX, tên `<name>.docx` | như trên; `log_export("DOCX", …)` |
| `daily_job()` | | | Scheduler (không whitelist): `supersede_due()` rồi `send_approval_reminders()` |

### 3.1 `apply_action` — kiểm và hiệu ứng

| Hành động | Trạng thái đầu | Người được làm | Kiểm trước khi chuyển | Sau khi chuyển |
| :-- | :-- | :-- | :-- | :-- |
| Gửi duyệt | Nháp | NC Clinician có `write` trên quy trình (phạm vi khoa) | `validation.submit_errors(...)` rỗng; có lỗi → `frappe.throw` liệt kê tất cả (`<br>` nối), trạng thái giữ "Nháp", không lưu gì | Thông báo trưởng khoa (ASM-007-02) |
| Đồng ý | Chờ trưởng khoa duyệt | NC Department Head, khoa chủ trì ∈ `get_user_departments(user)` | | Thông báo mọi NC Council Member đang bật |
| Thông qua | Chờ hội đồng thẩm định | NC Council Member = `NC Settings.council_secretary` | `council_secretary` trống → ValidationError "Chưa cấu hình thư ký hội đồng ở Cài đặt Normcore" | Thông báo mọi NC Director đang bật |
| Ban hành | Chờ ban hành | NC Director | `decision_no` (strip) và `effective_date` bắt buộc → ValidationError "Cần nhập số quyết định ban hành và ngày hiệu lực" | Ghi `decision_no`, `effective_date` trong cùng lần lưu; nếu `effective_date` ≤ hôm nay gọi `supersede_due(for_procedure)`; thông báo người soạn |
| Từ chối | 3 trạng thái chờ | Người được duyệt của cấp đó (dòng tương ứng ở trên) | `reason` (strip) bắt buộc → ValidationError "Cần nhập lý do từ chối"; trạng thái không đổi | Về "Nháp"; lý do ghi `NC Audit Event.detail` (sự kiện "Chuyển trạng thái" do hook ghi; hook đọc `doc.flags.audit_detail`, ASM-007-04) và Comment loại "Workflow" trên bản ghi; ý kiến thẩm định giữ nguyên; thông báo người soạn (ASM-007-02) |

Không đủ vai trò / sai khoa / không phải thư ký → PermissionError "Bạn không có quyền …". Thực hiện: `frappe.get_doc` → kiểm → đặt trường (Ban hành) → `doc.workflow_state = next`, `doc.flags.workflow_action = action`, `doc.save(ignore_permissions=True)` (Frappe `validate_workflow` vẫn kiểm transition theo vai trò người gọi) → `doc.add_comment("Workflow", …)` → thông báo. Không dùng `frappe.model.workflow.apply_workflow` (nó lưu không bỏ quyền và nạp lại bản ghi từ CSDL, làm mất `decision_no` vừa nhập).

### 3.2 Thông báo (FR-NOTI-001, ASM-007-01, ASM-007-02)
Hàm nội bộ `_notify(users, subject, doc)` tạo `Notification Log` (`type = "Alert"`, `document_type`, `document_name`, `subject`, `for_user`, `from_user = session.user`), bỏ Administrator, Guest, người dùng tắt; không trùng (cùng `for_user`, `document_name`, `subject`). Tiêu đề: `"{name}: chờ trưởng khoa duyệt"`, `"…: chờ hội đồng thẩm định"`, `"…: chờ ban hành"`, `"…: đã ban hành"`, `"…: bị từ chối ở cấp {cấp} — {lý do}"`, nhắc `"Nhắc duyệt: {name} chờ ở '{trạng thái}' từ {ngày}"`. FEAT-002 chuyển `_notify` sang `core/notify.py`.

## 4. Tác vụ ngày (`hooks.py` `scheduler_events["daily"]` thêm `normcore.api.procedure_workflow.daily_job`)

- `supersede_due(today=None, for_procedure=None)` (FR-WF-006): lấy mọi quy trình "Đã ban hành"; `approval.to_supersede(rows, today)` trả tên các bản bị thay; mỗi tên `db_set("workflow_state", "Đã thay thế")` (hook `on_change` ghi sổ sự kiện). Trả số bản đã chuyển. Test gọi trực tiếp với `today` giả lập (TC-WF-04).
- `send_approval_reminders(today=None)` (FR-WF-013): mọi quy trình ở trạng thái chờ; ngày vào trạng thái = `event_time` của NC Audit Event "Chuyển trạng thái" mới nhất có `to_state` = trạng thái hiện tại (không có thì `modified`); `approval.overdue(...)` với `approval_reminder_days`; người nhận như ở 3.1 cho cấp đó; tiêu đề có ngày vào trạng thái → mỗi lần vào trạng thái nhắc một lần (ASM-007-07). Trả số thông báo tạo.

## 5. Logic thuần (không import `frappe`; unit test ở `normcore/tests/unit/`)

### 5.1 `normcore/procedure/validation.py` (architecture.md: `procedure/validation.py`)
- `submit_errors(steps, resources, citations) -> list[str]`: đầu vào là list dict (trường như DocType). Thứ tự lỗi cố định: (1) không có bước `phase == "Thực hiện"`; (2) mỗi bước `description` rỗng: "Bước {step_id} thiếu mô tả"; (3) mỗi dòng nguồn lực thiếu số lượng (`quantity` None hoặc ≤ 0) / thiếu đơn vị: "Dòng nguồn lực {resource_row_id} thiếu số lượng" / "… thiếu đơn vị"; (4) mỗi trích dẫn "Khác biệt" có `deviation_reason` rỗng: "Trích dẫn dòng {idx} ({phần hoặc mã bước}) thuộc loại Khác biệt nhưng chưa có lý do"; (5) bước hoặc dòng nguồn lực còn `ai_suggested` (ASM-007-11). FR-PROC-008 → (4); FR-PROC-012 → (1)(2)(3). Không có BR tính giá, không có golden.

### 5.2 `normcore/procedure/approval.py`
- Hằng trạng thái, `PENDING_STATES`, `CLOSED_STATES`, `TRANSITIONS` (bảng 2.4 dạng dữ liệu, kiểm bằng test khớp fixture Workflow).
- `next_state(state, action) -> str` (ValueError nếu không hợp lệ).
- `to_supersede(published, today) -> list[str]`: `published` = list `{name, technical_service, department, version_no, effective_date}`; theo từng (dịch vụ, khoa), bản "đang hiệu lực" = bản có `effective_date` ≤ today lớn nhất (bằng nhau thì `version_no` lớn hơn); trả các bản khác có `version_no` nhỏ hơn bản đó. Bản có ngày hiệu lực tương lai không làm gì (TC-WF-04 "trước ngày").
- `effective_procedure(published, service, department, on_date) -> name | None`: cho FEAT-012 ("chỉ quy trình đã ban hành mới sinh định mức", ASM-007-15).
- `overdue(pending, today, days) -> list`: `pending` = `{name, state, entered_on}`; quá hạn khi `(today - entered_on).days >= days`.
- `reject_level(state) -> str`: nhãn cấp ("trưởng khoa", "hội đồng", "giám đốc").

### 5.3 `normcore/procedure/printing.py`
- `print_context(doc: dict, signatures: dict, today) -> dict`: `is_draft` (trạng thái ∉ Đã ban hành/Đã thay thế/Đã thu hồi), `watermark = "DỰ THẢO"` khi nháp, `status_note` ("Đã thay thế" / "Đã thu hồi" / ""), tiêu đề, số hiệu (`name`), phiên bản, khoa, dịch vụ, `decision_no`, `effective_date` (dd/mm/yyyy, NFR-LOC-001), 8 phần theo thứ tự FR-PROC-001 (phần "Các bước tiến hành" là bảng bước nhóm theo giai đoạn: mã bước, tên, mô tả, thời gian tham chiếu), bảng nguồn lực theo bước, khối chữ ký 4 ô (Người soạn / Trưởng khoa / Hội đồng chuyên môn / Giám đốc: tên, ngày; trống ở bản nháp chưa qua cấp đó).
- `signatures` lấy ở tầng Frappe từ NC Audit Event (người và thời điểm của các chuyển "→ Chờ trưởng khoa duyệt", "→ Chờ hội đồng thẩm định", "→ Chờ ban hành", "→ Đã ban hành" gần nhất).
- Print Format Jinja gọi `normcore.api.procedure_workflow.get_print_context(doc)` (tầng Frappe: lấy chữ ký rồi gọi `printing.print_context`) khai ở `hooks.py` `jinja = {"methods": [...]}`; DOCX dùng cùng `print_context` → cùng nội dung (FR-PROC-011).

### 5.4 `normcore/exports/procedure_docx.py`
`build_docx(ctx) -> bytes` bằng python-docx (dựng bằng mã, không tệp mẫu, ASM-007-10): tiêu đề, dòng "DỰ THẢO" ở đầu trang khi nháp, bảng thông tin, 8 phần, bảng bước, bảng nguồn lực, bảng chữ ký. `pyproject.toml` thêm `python-docx` vào `dependencies` (ADR-015); Dev cài trên bench dev bằng `scripts/with_bench.sh 'bench pip install python-docx'` và ghi nhật ký.

## 6. Mẫu in mặc định (TBD-04, ASM-007-08)
Khổ A4 dọc, chữ Desk mặc định. Đầu trang: Letter Head mặc định của site nếu có; dòng "QUY TRÌNH KỸ THUẬT", tên dịch vụ (mã), khoa chủ trì; bảng: Số hiệu, Phiên bản, Số quyết định, Ngày hiệu lực, Trạng thái. Bản nháp: chữ "DỰ THẢO" đậm ở đầu trang và chữ chìm chéo trang (CSS `position: fixed`, mờ). Thân: 8 phần, bảng bước, bảng nguồn lực. Cuối: khối chữ ký 4 cột. Bản "Đã thay thế"/"Đã thu hồi" in dòng trạng thái dưới tiêu đề, không có "DỰ THẢO".

## 7. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Quy trình đủ bước nhưng có trích dẫn "Khác biệt" trống lý do: `apply_action(…, "Gửi duyệt")` ném ValidationError có chuỗi chỉ ra trích dẫn đó; `workflow_state` vẫn "Nháp"; không có Notification Log | TC-PROC-05 | FR-PROC-008 | `test_TC_PROC_05_*` (tích hợp) + unit `submit_errors` |
| 2 | Không có bước "Thực hiện", 1 bước thiếu mô tả, 1 nguồn lực thiếu đơn vị: thông báo lỗi chứa đủ 3 lỗi; vẫn "Nháp" | TC-PROC-06 | FR-PROC-012 | `test_TC_PROC_06_*` (tích hợp + unit) |
| 3 | HTML in (`frappe.get_print`) và DOCX của bản "Nháp" chứa "DỰ THẢO"; của bản "Đã ban hành" không chứa "DỰ THẢO", chứa `decision_no`, "Phiên bản 1", ngày hiệu lực dd/mm/yyyy, 4 nhãn khối chữ ký; `download_pdf` trả byte bắt đầu `%PDF`. QA mở PDF kiểm bằng mắt (loại M) | TC-PROC-07 | FR-PROC-010, FR-PROC-011 | `test_TC_PROC_07_*` |
| 4 | Clinician gửi → "Chờ trưởng khoa duyệt", trưởng khoa (head_user) có Notification Log; Dept Head cùng khoa "Đồng ý" → "Chờ hội đồng thẩm định", mọi Council Member có thông báo; thư ký "Thông qua" → "Chờ ban hành", Director có thông báo; Director "Ban hành" với số QĐ và ngày → "Đã ban hành"; sổ sự kiện có đủ 4 chuyển | TC-WF-01 | FR-WF-001, 002, 004, 005 | `test_TC_WF_01_*` |
| 5 | Council Member không phải thư ký "Thông qua" → PermissionError; Dept Head khoa khác "Đồng ý" → PermissionError; Director "Ban hành" thiếu số QĐ → ValidationError, giữ "Chờ ban hành" | TC-WF-01 | FR-WF-002, 004, 005 | `test_TC_WF_01_*` (ca âm) |
| 6 | Dept Head "Từ chối" không lý do → ValidationError, giữ "Chờ trưởng khoa duyệt"; có lý do → "Nháp", người soạn có Notification Log chứa lý do, NC Audit Event `detail` = lý do | TC-WF-02 | FR-WF-007 | `test_TC_WF_02_*` (+ từ chối ở cấp hội đồng, giám đốc) |
| 7 | Quy trình "Đã ban hành": sửa `description` bước qua `doc.save()` của Clinician (đường form/`frappe.client.save`) và qua `api.procedure.update_step` đều bị từ chối, giá trị trong CSDL không đổi; tương tự ở "Đã thay thế" | TC-WF-03 | FR-WF-008 | `test_TC_WF_03_*` |
| 8 | v1 "Đã ban hành"; v2 ban hành với `effective_date` = D (tương lai): `supersede_due(today=D-1)` → v1 vẫn "Đã ban hành"; `supersede_due(today=D)` → v1 "Đã thay thế", v2 "Đã ban hành" | TC-WF-04 | FR-WF-006 | `test_TC_WF_04_*` |
| 9 | Council Member ghi ý kiến ở `S002` khi "Chờ hội đồng thẩm định": NC Review Comment có `target_step_id = S002`; sau khi thư ký từ chối, Clinician gọi `get_review` thấy ý kiến trong `comments_by_step["S002"]` | TC-WF-08 | FR-WF-003 | `test_TC_WF_08_*` |
| 10 | NC Review Comment: NC Resource Manager không đọc/tạo được; NC Auditor đọc được, tạo/sửa → PermissionError; NC Clinician tạo → PermissionError | — | FR-WF-003, FR-ACC-007 | `test_quyen_review_comment_*` |
| 11 | Quá `approval_reminder_days` ở "Chờ trưởng khoa duyệt": `send_approval_reminders(today)` tạo đúng 1 thông báo cho trưởng khoa; chạy lại không tạo thêm; chưa quá hạn thì 0 | — | FR-WF-013 | `test_FR_WF_013_*` |
| 12 | Fixture Workflow khớp `approval.TRANSITIONS`; NC Auditor không ở `allowed`/`allow_edit` | — | FR-WF-001..007, FR-ACC-007 | `test_workflow_fixture_*` |

## 8. Rủi ro
- **Test cũ** gọi `publish()` từ "Nháp" và lưu thẳng `workflow_state = "Đã ban hành"` bằng `flags.allow_publish` sẽ đỏ khi Workflow bật: Q1 (mục 9).
- `python-docx` chưa có trên bench dev, staging: phải cài khi deploy (`bench setup requirements` hoặc `bench pip install`); nếu môi trường staging không cài tự động, Lead báo người. Mã import trễ trong `download_docx` để thiếu thư viện chỉ hỏng DOCX, không hỏng app.
- `wkhtmltopdf` có trên máy dev (`/usr/bin/wkhtmltopdf`); chữ "DỰ THẢO" chìm bằng CSS phải kiểm trên PDF thật (QA, loại M).
- Nút workflow chuẩn của Desk gọi `apply_workflow` (cần quyền write): form JS chặn ở `before_workflow_action` và gọi `apply_action` (ASM-007-13).

## 9. Câu hỏi đã được Lead quyết

**Q1 — test cũ dựa vào `publish()` từ "Nháp" (luật cứng 1).** FR-WF-001..005 và data-model 5.1 chỉ cho "Ban hành" từ "Chờ ban hành"; Frappe Workflow (ADR-011) từ chối lưu `Nháp → Đã ban hành`. 13 chỗ dựng dữ liệu trong test cũ sẽ đỏ, không do lỗi mã mà do dữ liệu dựng sẵn: `tests/utils.py::make_chain_data`, `tests/test_feat_001.py` (lưu với `flags.allow_publish`); `proc.publish()` từ "Nháp" trong `nc_core/.../test_nc_audit_event.py`, `nc_costing/.../test_nc_costing_run.py`, `nc_costing/.../test_nc_norm_set.py` (2), `tests/test_form_actions.py::_published_procedure`, `tests/test_feat_039.py` (dòng 271), `nc_procedure/.../test_nc_clinical_procedure.py` (3), `api/test_procedure.py` (2). Các test kiểm quyền của `publish()` (Clinician, Auditor bị từ chối) vẫn xanh.
- **Đề xuất (PA1)**: thêm helper `publish_procedure(proc, decision_no, effective_date)` trong `normcore/tests/utils.py` đưa quy trình đến "Đã ban hành" bằng `db_set` như dữ liệu dựng sẵn (hook vẫn ghi sổ sự kiện `Nháp → Đã ban hành`, nên assertion của `test_feat_039` giữ nguyên); thay **chỉ các dòng dựng dữ liệu** bằng helper. Ba test của `test_nc_clinical_procedure.py` kiểm chính hành vi ban hành thì đưa quy trình về "Chờ ban hành" bằng helper `to_state(proc, "Chờ ban hành")` rồi mới `publish()`; mọi assertion giữ nguyên độ chặt. Ghi ASM dẫn Quyết định Lead.
- PA2: giữ đường tắt `publish()` từ "Nháp" cho NC Director — trái FR-WF-001..005 (bỏ qua hai cấp duyệt), không đề xuất.

**Quyết định Lead (bình luận `01a2119e-b0b8-7c00-afaf-3bc21c5d7ae3` trên NORM-34): chọn PA1**, kèm ba điều kiện: (1) `publish_procedure`/`to_state` chỉ ở `tests/utils.py` để dựng dữ liệu, mã sản phẩm không có đường tắt; (2) test kiểm hành vi ban hành và chuyển trạng thái (3 test ở `test_nc_clinical_procedure`, TC-WF-01/02/04) đi đường thật (`apply_action`/`publish()`), không `db_set`; (3) không skip, không đổi sang `assertIn`, không đổi giá trị mong đợi; test kiểm quyền Clinician/Auditor giữ nguyên. Ghi ở ASM-007-16. Lead cũng đồng ý ASM-007-03 và ASM-007-09.
