# FEAT-014 — Khảo sát bấm giờ — Thiết kế kỹ thuật

Issue NORM-49. Nguồn: `srs.md` FR-TS-001..005, NFR-USE-003, FR-ADM-003, FR-NORM-008, FR-ACC-003, FR-ACC-007; `use-cases.md` UC-010; `data-model.md` 3.5 (NC Time Study, NC Time Study Line, NC Norm Set, NC Norm Line), NC Settings (`min_time_study_cases`), mục 4 dòng "Phiếu bấm giờ"; `architecture.md` cây thư mục `norm/time_study.py`, ADR-003 (logic thuần); `ux-foundations.md` SCR-DSK-015, SCR-DSK-016; `design.md` mục 4 (vùng chạm 44 px); TC-TS-01..05, TC-NFR-05, TC-ADM-03 (phần kết quả bấm giờ, theo Quyết định Lead).

Phụ thuộc: FEAT-012 DONE trên `origin/develop` (`7ed1b85`): NC Norm Set/Line, `api/norm.py`, trang `norm-grid`. Dùng lại phạm vi khoa FEAT-001 (`core/permissions.py`, `core/scope_rules/`).
**Phụ thuộc mềm FEAT-002 (NORM-52, chưa merge):** `normcore/core/settings.py::get` và trường `NC Settings.min_time_study_cases` do FEAT-002 làm (Quyết định Lead). FEAT-014 **không** tự tạo hai thứ này (xem mục 7, task T05).

Giả định: `docs/decisions/assumptions/FEAT-014.md` (ASM-014-01..10). Không có AMD (NC Time Study, NC Time Study Line đã có trong `data-model.md`; thêm một trường bố cục HTML là ASM-014-08). Không có câu hỏi mở cho Lead.

Golden: không có phép tính tiền ở FEAT này (trung vị số phút không thuộc BR-COST/BR-CLS). Áp kết quả chỉ ghi `hospital_qty` của NC Norm Line; chi phí tạm tính của lưới vẫn do `costing/provisional.py` (FEAT-012) tính.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-TS-001 | Tạo NC Time Study cho (dịch vụ, khoa): controller tự chọn quy trình "Đã ban hành" của (dịch vụ, khoa) nếu `procedure` trống, từ chối nếu không có/không khớp, và nạp `lines` theo thứ tự bước của quy trình (ASM-014-02) |
| FR-TS-002 | Mỗi dòng lưu `step_id`, `job_title`, `headcount`, `labor_minutes` hoặc `equipment`, `machine_minutes` (ASM-014-07). Không có trường định danh người bệnh ở cả hai DocType |
| FR-TS-003 | `norm/time_study.py::summarize`: trung vị theo (bước, chức danh) và (bước, thiết bị) trên các ca cùng (dịch vụ, khoa, quy trình); số ca; `sufficient` so với `min_time_study_cases` (ASM-014-01, 04, 05) |
| FR-TS-004 | `api/time_study.py::apply_to_norm_set`: bộ "Nháp" → `hospital_qty` của dòng LABOR/EQUIPMENT tương ứng = trung vị, `basis` = "Bấm giờ", `basis_ref` (ASM-014-06) |
| FR-TS-005 | Số ca < tối thiểu và chưa `confirm` → không ghi, trả `needs_confirm`; giao diện cảnh báo, hỏi xác nhận, gọi lại với `confirm=1` |
| NFR-USE-003 | SCR-DSK-015 bố cục máy tính bảng ≥ 768 px, mỗi bước ≤ 3 lần chạm, vùng chạm ≥ 44 px (ui-design) |
| FR-ADM-003 (phần FEAT-014) | `test_TC_ADM_03_ket_qua_bam_gio_3_ca`: đổi tối thiểu 5 → 3 ở NC Settings, dịch vụ có 3 ca → `sufficient`, không cảnh báo, không khởi động lại |

Ngoài phạm vi: lưu ngoại tuyến (ux-foundations: không yêu cầu ở v1); xóa phiếu (ASM-014-09); cập nhật `headcount` của dòng định mức.

## 2. DocType (module NC Costing, mới)

### 2.1 NC Time Study

Naming `format:BG-{technical_service}-{department}-{####}` (ASM-014-10). `track_changes` = 1. Không submittable, không workflow.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| technical_service | Dịch vụ | Link NC Technical Service | Có | `in_list_view`, `in_standard_filter` |
| department | Khoa | Link NC Department | Có | `in_list_view`, `in_standard_filter`; trường phạm vi khoa |
| procedure | Phiên bản quy trình | Link NC Clinical Procedure | Có | Tự điền khi trống (2.3); chỉ đọc sau khi lưu lần đầu (`set_only_once`) |
| observed_on | Ngày bấm giờ | Date | Có | Mặc định `Today`; `in_list_view` |
| observer | Người khảo sát | Link User | | Mặc định người tạo |
| entry_panel | Ghi theo bước | HTML | | Trường bố cục, không lưu (ASM-014-08) |
| lines | Dòng bấm giờ | Table NC Time Study Line | | |

Quyền (DocPerm, mục 4 dòng "Phiếu bấm giờ"; ASM-014-09):

| Vai trò | read | write | create | delete |
| :-- | :-: | :-: | :-: | :-: |
| NC Clinician (khoa) | 1 | 1 | 1 | 0 |
| NC Department Head (khoa) | 1 | 1 | 1 | 0 |
| NC Finance | 1 | 0 | 0 | 0 |
| NC Director | 1 | 0 | 0 | 0 |
| NC Consultant | 1 | 1 | 1 | 0 |
| NC Admin | 1 | 0 | 0 | 0 |
| NC Auditor | 1 | 0 | 0 | 0 |
| NC Council Member, NC Resource Manager, NC Document Controller | — | — | — | — |

Phạm vi khoa: tệp mới `normcore/core/scope_rules/nc_time_study.json` `{"doctype": "NC Time Study", "department_field": "department", "public_read": {}}` (hook tự sinh, không sửa `hooks.py`).

### 2.2 NC Time Study Line (bảng con, `istable`)

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| step_id | Mã bước | Data | Có | Phải có trong `steps` của `procedure`; `in_list_view` |
| job_title | Chức danh | Link NC Job Title | | Dòng nhân lực; `in_list_view` |
| headcount | Số người | Int | | Mặc định 1 với dòng nhân lực; `in_list_view` |
| labor_minutes | Số phút nhân lực | Float | | ≥ 0; `in_list_view` |
| equipment | Thiết bị | Link NC Equipment | | Dòng thiết bị; `in_list_view` |
| machine_minutes | Số phút máy | Float | | ≥ 0; `in_list_view` |

Không có trường nào tên/nhãn chứa người bệnh, mã bệnh án, họ tên, ngày sinh, mã BHYT; không Link tới DocType người bệnh (TC-TS-05).

### 2.3 Controller `NCTimeStudy` (`nc_time_study.py`, lớp mỏng gọi `norm/time_study.py`)

- `before_validate`, chỉ khi `is_new()`:
  - `procedure` trống → lấy NC Clinical Procedure `workflow_state` = "Đã ban hành" cùng (`technical_service`, `department`), `version_no` lớn nhất. Không có → `frappe.throw(_("Dịch vụ chưa có quy trình đã ban hành tại khoa này."))`.
  - `procedure` có → phải "Đã ban hành" và khớp `technical_service`, `department`, nếu không → ValidationError.
  - `lines` trống → `lines = lines_from_procedure(steps, resources)`.
- `validate` (mọi đường ghi): `line_errors(lines, step_ids_of_procedure)`; có lỗi → `frappe.throw` liệt kê từng lỗi, mỗi lỗi một dòng (design.md mục 5). Mặc định `observer` = `frappe.session.user` khi trống.
- Không chặn sửa phiếu sau khi đã áp kết quả (áp là bản chụp tại thời điểm áp; `basis_ref` ghi số ca và khoảng ngày).

## 3. API whitelisted — `normcore/api/time_study.py` (mới)

Mọi hàm kiểm quyền tường minh; lỗi quyền `frappe.PermissionError`, lỗi dữ liệu `frappe.ValidationError` với thông báo tiếng Việt qua `_()`.

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `get_entry(name)` | tên NC Time Study | `{doc: {name, technical_service, department, procedure, observed_on, observer}, steps: [{step_id, step_title, phase, idx}], lines: [{name, idx, step_id, job_title, job_title_label, headcount, labor_minutes, equipment, equipment_label, machine_minutes}], can_write}` | `frappe.has_permission("NC Time Study", "read", doc)`; không có → PermissionError |
| `get_result(technical_service, department, procedure=None)` | `procedure` trống = quy trình "Đã ban hành" mới nhất của (dịch vụ, khoa) | `{procedure, n_cases, min_cases, sufficient, first_date, last_date, rows: [{step_id, step_title, kind: "labor"\|"equipment", resource, resource_label, median_minutes, n}]}`; `rows` sắp theo thứ tự bước rồi `kind` (labor trước) rồi `resource` | Ca lấy bằng `frappe.get_list` (áp phạm vi khoa); `frappe.has_permission("NC Time Study", "read")` không có → PermissionError. `min_cases` = `core.settings.get("min_time_study_cases")` mỗi lần gọi (ASM-014-01) |
| `apply_to_norm_set(norm_set, confirm=0)` | tên NC Norm Set | Chưa đủ ca và `confirm` ≠ 1: `{applied: false, needs_confirm: true, n_cases, min_cases, message}` (không ghi gì). Ngược lại: `{applied: true, updated: [line_id], unmatched: [{step_id, kind, resource}], n_cases}` | `frappe.has_permission("NC Norm Set", "write", ns)` (phạm vi khoa) và `has_permission("NC Time Study", "read")`; thiếu → PermissionError. `ns.status` ≠ "Nháp" → ValidationError "Chỉ áp được vào bộ định mức Nháp". `n_cases` = 0 → ValidationError "Chưa có ca bấm giờ nào". Ghi qua `ns.save()` để `NCNormSet.validate` (FEAT-012) kiểm dòng và xóa xác nhận của dòng bị đổi |

`apply_to_norm_set` lấy ca theo (`ns.technical_service`, `ns.department`, `ns.procedure`), gọi `summarize` rồi `plan_apply`, gán từng cập nhật vào dòng của `ns`, `ns.save()`. Không ghi NC Audit Event mới: `track_changes` của NC Norm Set đã lưu phiên bản trước/sau.

Bộ định mức (FEAT-012) mở rộng:
- `api/norm.py::_actions`: thêm `"apply_time_study"` khi `ns.status` = "Nháp" và `can_write` (chung nhánh với `save_line`). Không đổi hàm nào khác.

## 4. Logic thuần — `normcore/norm/time_study.py` (mới, không import `frappe`)

| Hàm | Vào | Ra | Căn cứ |
| :-- | :-- | :-- | :-- |
| `lines_from_procedure(steps, resources)` | `steps`: list dict `{step_id, idx}`; `resources`: list dict `{step_id, resource_type, linked_doctype, linked_name, headcount}` | list dict dòng phiếu, theo thứ tự `idx` của bước, trong bước giữ thứ tự nguồn lực: "Nhân lực" → `{step_id, job_title: linked_name, headcount: headcount or 1}`; "Thiết bị" → `{step_id, equipment: linked_name}`; bước không có hai loại → `{step_id}` | FR-TS-001, ASM-014-02 |
| `line_errors(lines, step_ids)` | dòng phiếu, tập mã bước của quy trình | list chuỗi lỗi (rỗng = hợp lệ): mã bước lạ; vừa `job_title` vừa `equipment`; `labor_minutes` > 0 không `job_title`; `machine_minutes` > 0 không `equipment`; số phút âm; `labor_minutes` > 0 mà `headcount` < 1; trùng (bước, chức danh) hoặc (bước, thiết bị) | FR-TS-002, ASM-014-07 |
| `median(values)` | list số | trung vị (`statistics.median`), số chẵn phần tử = trung bình hai giữa | FR-TS-003, TC-TS-01 |
| `collect(cases)` | list ca, mỗi ca `{observed_on, lines}` | `{(step_id, "labor", job_title): [phút...], (step_id, "equipment", equipment): [phút...]}`; bỏ giá trị ≤ 0 (ASM-014-03) | UC-010 2a |
| `summarize(cases, min_cases, step_order)` | ca, mức tối thiểu, `{step_id: idx}` | `{n_cases, min_cases, sufficient: n_cases >= min_cases, first_date, last_date, rows: [{step_id, kind, resource, median_minutes, n}]}` | FR-TS-003, FR-TS-005, ASM-014-04, 05 |
| `plan_apply(norm_lines, rows, basis_ref)` | dòng NC Norm Line (dict), `rows` của `summarize` | `(updates, unmatched)`: `updates` = list `{line_id, hospital_qty, basis: "Bấm giờ", basis_ref}` cho mọi dòng LABOR (`resource_doctype` NC Job Title) / EQUIPMENT (`resource_doctype` NC Equipment) có cùng `step_id` và `resource`, không `service_level`; `unmatched` = các `rows` không khớp dòng nào | FR-TS-004, ASM-014-06 |
| `basis_ref(n_cases, first_date, last_date)` | | `"6 ca bấm giờ, 01/11/2026–20/11/2026"` (ngày `dd/mm/yyyy`, NFR-LOC-001) | FR-NORM-008 |

Hằng `BASIS = "Bấm giờ"` (khớp lựa chọn `NC Norm Line.basis`). Độ phủ: `pytest --cov=normcore/norm/time_study.py` ≥ 90% (không bắt buộc bởi NFR-MNT-001 nhưng làm như `norm/` của FEAT-012).

## 5. Giao diện (chi tiết ở `ui-design.md`)

- SCR-DSK-015: form NC Time Study (Desk Form chuẩn) + bảng ghi theo bước vẽ vào `entry_panel` (`nc_time_study.js`), lưu vào `lines`.
- SCR-DSK-016: Script Report `NC Time Study Result` ("Kết quả bấm giờ", `nc_costing/report/nc_time_study_result/`) gọi `api/time_study.get_result`; nút "Áp vào bộ định mức".
- SCR-DSK-014 (FEAT-012) mở rộng: nút "Áp kết quả bấm giờ" trong `NormGrid.vue` khi `actions` có `apply_time_study`; nút cùng tên trên form NC Norm Set.

## 6. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test (tên gợi ý) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | 5 ca, bước S002 chức danh BS, số phút 18, 22, 20, 25, 19 → `summarize` trung vị 20, n = 5; thêm ca 21 → 20,5, n = 6 | TC-TS-01 | FR-TS-003 | `tests/unit/test_time_study.py::test_TC_TS_01_trung_vi_5_ca_va_6_ca` |
| 2 | Bộ "Nháp" có dòng LABOR S002/BS (20) và EQUIPMENT S002/EQ1; ≥ 5 ca → `apply_to_norm_set` đặt `hospital_qty` = trung vị, `basis` = "Bấm giờ", `basis_ref` chứa số ca; dòng khác không đổi; `unmatched` liệt kê khóa không có dòng | TC-TS-02 | FR-TS-004 | `api/test_time_study.py::test_TC_TS_02_ap_ket_qua_vao_bo_nhap` |
| 3 | Chỉ 3 ca (tối thiểu 5) → `apply_to_norm_set` trả `needs_confirm`, CSDL không đổi; `confirm=1` → áp | TC-TS-03 | FR-TS-005 | `test_TC_TS_03_thieu_ca_canh_bao_xac_nhan` |
| 4 | Quy trình "Đã ban hành" 4 bước, khoa K01 → tạo phiếu chỉ với dịch vụ + khoa → `procedure` tự điền, `lines` phủ đủ 4 mã bước, đúng thứ tự `idx` của quy trình; quy trình chưa ban hành → từ chối | TC-TS-04 | FR-TS-001 | `nc_time_study/test_nc_time_study.py::test_TC_TS_04_nap_4_buoc_theo_quy_trinh` |
| 5 | Ghi ca S002: BS 1 người 20 phút, DD 1 người 20 phút, EQ1 20 phút máy → đọc lại đúng từng trường theo bước; meta của NC Time Study và NC Time Study Line không có trường định danh người bệnh (danh sách từ khóa ở 2.2) | TC-TS-05 | FR-TS-002 | `test_TC_TS_05_luu_theo_buoc_khong_dinh_danh_nguoi_benh` |
| 6 | Đổi `NC Settings.min_time_study_cases` 5 → 3, 3 ca → `get_result` `sufficient` = true, `min_cases` = 3, trung vị có; `apply_to_norm_set` không cần `confirm`; không khởi động lại, không xóa cache | TC-ADM-03 (phần FEAT-014) | FR-ADM-003, FR-TS-003 | `api/test_time_study.py::test_TC_ADM_03_ket_qua_bam_gio_3_ca` |
| 7 | Ghi một ca 6 bước trên 768 px: mỗi bước ≤ 3 lần chạm, không cuộn ngang | TC-NFR-05 (M) | NFR-USE-003 | Kiểm tay theo ui-design mục 1.5, ghi vào implementation-log; test tĩnh `tests/unit/test_time_study_ui.py` (vùng chạm ≥ 44 px, `inputmode="decimal"`, không `min-width` cố định > 768 px) |
| 8 | `line_errors`: mỗi nhánh lỗi ở mục 4 có ca; bước không làm (0 phút) không vào trung vị | — | FR-TS-002, UC-010 2a | `tests/unit/test_time_study.py` |
| 9 | Quyền: NC Council Member (không quyền) đọc/tạo phiếu, `get_result`, `get_entry` → PermissionError; NC Auditor đọc phiếu, `get_result` được, tạo/sửa phiếu và `apply_to_norm_set` → PermissionError; Clinician khoa K02 không đọc/sửa phiếu K01; Consultant tạo được phiếu, `apply_to_norm_set` → PermissionError; DocPerm khớp bảng 2.1 | — | FR-ACC-003, FR-ACC-007 | `test_quyen_time_study_*` |
| 10 | `apply_to_norm_set` vào bộ "Đã khóa" → ValidationError; dòng đã xác nhận bị đổi số phút thì mất xác nhận (theo FEAT-012) | — | FR-TS-004 | `test_ap_chi_vao_bo_nhap` |
| 11 | Toàn bộ test cũ xanh; `check_conventions.py` thoát 0 | — | NFR-MNT-001 | T10 |

## 7. Rủi ro

- **FEAT-002 chưa merge**: `core.settings.get` và trường `min_time_study_cases` chưa có trên develop. T01–T04 không cần chúng (logic thuần nhận `min_cases` làm tham số). T05 bắt đầu bằng `git fetch && git cat-file -e origin/develop:normcore/core/settings.py`; chưa có → Dev chuyển Blocked, hỏi Lead (không tự viết `core/settings.py`, không viết cứng 5).
- **Test cũ đếm DocType / quyền** (ví dụ quét NC Auditor chỉ đọc, danh sách DocType có phạm vi khoa): DocType mới có thể làm đổi số đếm. Chỉ cập nhật theo CLAUDE.md mục 3.1 (cần Quyết định Lead + ASM).
- **Frappe lưu Float trống thành 0**: không phân biệt "chưa ghi" với 0 phút (ASM-014-03).
- **Bàn phím ảo che bảng** trên máy tính bảng: ui-design dùng `scrollIntoView` khi focus.
- Áp kết quả khi bộ đã có dòng trùng (FR-NORM-014 cho phép lưu trùng): mọi dòng khớp đều được cập nhật cùng trung vị.

## 8. Tệp chạm tới

Mới: `normcore/norm/time_study.py`, `normcore/tests/unit/test_time_study.py`, `normcore/tests/unit/test_time_study_ui.py`, `normcore/nc_costing/doctype/nc_time_study/{__init__,nc_time_study.json,nc_time_study.py,nc_time_study.js,nc_time_study_list.js,test_nc_time_study.py}`, `normcore/nc_costing/doctype/nc_time_study_line/{__init__,nc_time_study_line.json,nc_time_study_line.py}`, `normcore/core/scope_rules/nc_time_study.json`, `normcore/api/time_study.py`, `normcore/api/test_time_study.py`, `normcore/nc_costing/report/nc_time_study_result/*`, `docs/as-built/FEAT-014.md`.
Sửa: `normcore/api/norm.py` (`_actions` thêm `apply_time_study`), `normcore/public/js/norm_grid/NormGrid.vue` (nút), `normcore/nc_costing/doctype/nc_norm_set/nc_norm_set.js` (nút), `normcore/translations/vi.csv`, `docs/rtm-testref.md` (mục `## FEAT-014`, hoặc `docs/rtm-testref/FEAT-014.md` nếu đã có trên develop).

## 9. Ghi chú cho Dev

- Mọi lệnh `bench` qua `scripts/with_bench.sh`, migrate và test trong cùng một lần gọi.
- Dữ liệu test: dựng quy trình "Đã ban hành" bằng helper có sẵn của FEAT-012 trong `normcore/tests/utils.py` nếu có; chức danh BS, DD và thiết bị EQ1 như bộ dữ liệu vàng.
- Không đọc `min_time_study_cases` bằng `frappe.get_single`/`get_cached_doc` (cache): chỉ qua `core.settings.get`.
- Chuỗi giao diện qua `_()`/`__()`; khóa `vi.csv` sắp thứ tự.
