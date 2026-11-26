# FEAT-034 — Định mức theo hệ thống xét nghiệm — Thiết kế kỹ thuật

Issue NORM-40. Nguồn: `srs.md` FR-NORM-017..025, FR-OUT-011 (kèm FR-OUT-006), BR-CLS-001..005 (chỉ để biết dữ liệu cần lưu), FR-QC-007, FR-ACC-002, FR-ACC-007; `use-cases.md` UC-021; `data-model.md` 3.5 (NC Norm Set, NC Norm Line, NC Norm Template, NC Norm Template Item), mục 4 (dòng "Bộ định mức", "Mẫu định mức"), DI-03 (bản 1.1), DI-15, DI-17; `ux-foundations.md` SCR-DSK-014, SCR-DSK-041; golden `docs/golden/golden_cls.py` (`NORM`, `SYSTEMS`, `ITEM["QC_L"]`, `IQC`); TC-CLS-29..33, TC-CLS-26 (phần còn lại của FEAT-032).

Phụ thuộc (đều có `DONE` trên `origin/develop` 7ed1b85): FEAT-012 (NC Norm Set/Line, `normcore/norm/*`, `api/norm.py`, trang `norm-grid`), FEAT-031 (NC Test System, `costing/test_systems.py`, `NC Technical Service.is_paraclinical`, `cls_group`), FEAT-032 (NC QC Plan, NC EQA Program, `costing/qc_plans.py::missing_iqc_warning`). Dùng thêm FEAT-009 (NC Item), FEAT-010 (NC Equipment).

Giả định: `docs/decisions/assumptions/FEAT-034.md` (ASM-034-01..23). Sửa thiết kế: `docs/decisions/amendments/AMD-034-01.md` (`uom` của dòng giữ chỗ). Không có câu hỏi chặn cho Lead; các điểm Lead nên xem trước ở mục 10.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-NORM-017 (Must) | `test_system` trên NC Norm Set: bắt buộc khi (dịch vụ, khoa) có hệ thống "Đang dùng" (ASM-034-01); DI-15; tên bộ có mã hệ thống (ASM-034-02); DI-03 theo (dịch vụ, khoa, hệ thống): hai hệ thống của một dịch vụ khóa được hai bộ cùng hiệu lực |
| FR-NORM-018 (Must) | `cost_level` trên NC Norm Line (5 giá trị, mặc định RESULT); dịch vụ không cận lâm sàng luôn RESULT (ASM-034-08); `attach_to`, `attach_equipment` cho DAY/PERIOD (ASM-034-09) |
| FR-NORM-019 (Must) | `apply_k`: chỉ RESULT + DRUG/SUPPLY + bộ có hệ thống (DI-17, ASM-034-07); bật thì `wastage_rate` về 0; mặc định bật khi khởi tạo (ASM-034-06) |
| FR-NORM-020 (Must) | `tests_per_tube` trên NC Norm Set; thiếu khi có dòng TUBE → từ chối "Xác nhận chuyên môn" (ASM-034-12) |
| FR-NORM-021 (Should) | DocType mới NC Norm Template, NC Norm Template Item (SCR-DSK-041); quyền NC Finance, NC Admin ghi (ASM-034-20); mẫu Hóa sinh, Miễn dịch cài sẵn, chưa bật (ASM-034-18) |
| FR-NORM-022 (Should) | Khởi tạo: áp mẫu đang dùng của nhóm chuyên ngành; khoản mục bắt buộc chưa khớp dòng quy trình → dòng chung, chưa có lượng (ASM-034-03, 04, 05) |
| FR-NORM-023 (Should) | Thiếu khoản mục bắt buộc, chưa loại trừ có lý do → từ chối "Xác nhận chuyên môn", liệt kê khoản mục (ASM-034-11) |
| FR-NORM-024 (Must) | Dòng dùng mặt hàng của kế hoạch nội kiểm/chuẩn máy cùng hệ thống → từ chối lưu dòng (ASM-034-10) |
| FR-NORM-025 (Could) | `copy_norm_set(source, test_system)`: bộ Nháp mới cho hệ thống khác của cùng dịch vụ, mang dòng có mã bước còn tồn tại, ghi `copied_from` (ASM-034-13, 14) |
| FR-OUT-011 (Must) | `export_norm_set(name)` → tệp Excel: phần FR-OUT-006 (dòng theo bước, căn cứ, người xác nhận) + cấp phát sinh, nhân k, kế hoạch nội kiểm, chuẩn máy, ngoại kiểm, hệ số k của lần tính giá gần nhất (ASM-034-15, 16) |
| FR-QC-007 (TC-CLS-26, phần còn lại) | Cảnh báo thiếu kế hoạch nội kiểm trên bộ định mức; vẫn khóa được (ASM-034-17) |

**Không làm**: tính tiền theo cấp phát sinh và k (BR-CLS-001..005, 009..013, FEAT-036) — FEAT này chỉ lưu dữ liệu và kiểm ràng buộc nhập, không có công thức mới; NC Test System Cost (FEAT-036); PDF của FR-OUT-006 và màn hình SCR-DSK-028 (FEAT-019); FR-NORM-015 (FEAT-013); đề xuất AI (FEAT-025, FEAT-038). Chi phí tạm tính của lưới không tính dòng cận lâm sàng không phải RESULT, hoặc có nhân k (ASM-034-22).

## 2. DocType (module NC Costing)

NC Norm Set và NC Norm Line đã có (FEAT-000, FEAT-012) và đã lên staging: **mở rộng, không tạo lại**. Thêm trường, bỏ `reqd` của `uom` (AMD-034-01) → `bench migrate` thêm cột. Patch duy nhất: đặt `cost_level` = RESULT cho dòng cũ (ASM-034-19).

### 2.1 NC Norm Set — trường thêm

`autoname` JSON giữ `format:DM-{technical_service}-{department}-v{version_no}`; thêm `NCNormSet.autoname()`: có `test_system` → `DM-{technical_service}-{department}-{test_system}-v{version_no}` (ASM-034-02).

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| test_system | Hệ thống xét nghiệm | Link NC Test System | Có điều kiện | Sau `department`; `set_only_once`; `in_list_view`, `in_standard_filter`; ASM-034-01, DI-15 |
| tests_per_tube | Số xét nghiệm bình quân trên một ống mẫu | Float | Có điều kiện | `depends_on` có `test_system` hoặc dịch vụ cận lâm sàng; FR-NORM-020; > 0 khi có dòng TUBE |
| norm_template | Mẫu định mức | Link NC Norm Template | | Chỉ đọc; ghi khi khởi tạo (ASM-034-03) |
| copied_from | Sao chép từ | Link NC Norm Set | | Chỉ đọc; ghi khi sao chép (FR-NORM-025) |

`HEAD_FIELDS` của controller thêm `test_system`, `tests_per_tube` (khóa nội dung ở "Đã xác nhận chuyên môn" so cả hai).

### 2.2 NC Norm Line — trường thêm, đổi

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| cost_level | Cấp phát sinh | Select `RESULT`/`TUBE`/`BATCH`/`DAY`/`PERIOD` | Có | Mặc định `RESULT`; sau `component`; nhãn hiển thị qua `options.cost_level` (Theo kết quả, Theo ống mẫu, Theo mẻ, Theo ngày-máy, Theo kỳ) |
| apply_k | Nhân hệ số tiêu hao k | Check | | DI-17 |
| attach_to | Gắn với | Select (trống)/`Hệ thống xét nghiệm`/`Thiết bị` | Có điều kiện | BB khi DAY, PERIOD (ASM-034-09) |
| attach_equipment | Thiết bị được gắn | Link NC Equipment | Có điều kiện | BB khi `attach_to` = Thiết bị |
| template_item | Khoản mục của mẫu | Data | | Tên khoản mục của `norm_set.norm_template` (ASM-034-23) |
| uom **(đổi)** | Đơn vị | Data | **Bỏ `reqd`** | AMD-034-01; vẫn kiểm ở controller |

`LINE_INPUTS` (controller) thêm `cost_level`, `apply_k`, `attach_to`, `attach_equipment`, `template_item` → đổi các trường này là "sửa dòng" (xóa xác nhận, ASM-012-06). `SAVE_FIELDS` của API tự có theo.

### 2.3 NC Norm Template (mới) — SCR-DSK-041

Naming `field:template_code`. `track_changes` = 1. Module NC Costing. Chỉ các trường của data-model (không thêm trường).

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| template_code | Mã mẫu | Data | Có | `unique`, `set_only_once` |
| cls_group | Nhóm chuyên ngành | Select như `NC Technical Service.cls_group` (dòng trống đầu, ASM FEAT-031) | Có | `in_list_view`, `in_standard_filter` |
| is_active | Đang dùng | Check | | Tối đa một mẫu đang dùng mỗi `cls_group` (ASM-034-03) |
| items | Khoản mục | Table NC Norm Template Item | | ≥ 1 khi `is_active` (ASM-034-21) |

**NC Norm Template Item** (bảng con, `istable`): `item_name` (Data, BB), `component` (Select 6 như NC Norm Line, BB), `default_cost_level` (Select 5 như `cost_level`, BB, mặc định RESULT), `is_mandatory` (Check). Cả bốn `in_list_view`.

Quyền (ASM-034-20, ma trận mục 4 dòng "Mẫu định mức" `R R — W R — R R W R`): NC Finance, NC Admin: read, write, create; NC Clinician, NC Department Head, NC Resource Manager, NC Director, NC Consultant, NC Auditor: read; không ai `delete`. Thêm `"NC Norm Template": "Mẫu định mức"` vào bảng ánh xạ quyền của `scripts/check_conventions.py` (tệp chung — cùng tiền lệ FEAT-032).

Controller `NCNormTemplate.validate`: gọi `norm.templates.template_errors(values, other_active)` (mục 4.2), `other_active` = mẫu khác `is_active` cùng `cls_group`; có lỗi thì `frappe.throw` một lần.

### 2.4 Controller `NCNormSet` — thay đổi

Thứ tự `validate` của FEAT-012 giữ nguyên; chèn:
1. Sau `validate_status_change`: **DI-15** khi `test_system` có giá trị: NC Test System phải tồn tại, `technical_service` và `department` bằng của bộ (thông báo "Hệ thống xét nghiệm GLU-A không thuộc dịch vụ/khoa của bộ định mức"); khi tạo mới thêm điều kiện "Đang dùng". **Không** bắt buộc `test_system` ở `validate` (ASM-034-01: yêu cầu nằm ở `api/norm.py::create_norm_set` và `set_blockers`, để test cũ FEAT-031 dựng bộ qua `make_norm_set` vẫn xanh).
2. Trước `validate_lines`, ở trạng thái "Nháp": `validation.normalize_line(line, set_ctx)` cho mỗi dòng (ASM-034-07, 08, 09) — đặt lại trường phụ thuộc, không báo lỗi.
3. `validate_lines`: `ctx` thêm `paraclinical` (`NC Technical Service.is_paraclinical`), `has_test_system`, `qc_items` (ASM-034-10; tập rỗng khi không có hệ thống/kế hoạch), `template_items` (tên khoản mục của `norm_template`, tập rỗng khi không có). Tính `changed` như FEAT-012; riêng lúc tạo mới, dòng giữ chỗ của mẫu (`template_item` có, không `procedure_resource_row`) coi là chưa sửa (`changed` = False) khi bộ được tạo bởi `create_from_procedure` (`flags.from_procedure`).
4. `lock_norm_set`: bộ lọc DI-03 thêm `"test_system": ns.test_system or ["is", "not set"]` (ASM-034-14).
5. `create_from_procedure(procedure, test_system=None)`: xem mục 3 `create_norm_set`.

Nạp dữ liệu cho `ctx` đặt ở hàm riêng `_cls_ctx(ns)` trong controller (dùng chung cho API).

## 3. API whitelisted — `normcore/api/norm.py` (mở rộng)

Quy ước FEAT-012 giữ nguyên (kiểm quyền tường minh, lỗi nghiệp vụ `ValidationError` tiếng Việt, hàm ghi trả `get_norm_set`).

| Hàm | Tham số | Kết quả | Kiểm quyền | Lỗi |
| :-- | :-- | :-- | :-- | :-- |
| `create_options(procedure)` **mới** | NC Clinical Procedure | `{"test_systems": [{"name","main_equipment","open_set"}], "required": bool, "template": name\|null}` | `has_permission("NC Norm Set","create")`; đọc NC Test System ở máy chủ | — |
| `create_norm_set(procedure, test_system=None)` **đổi** | | `{"name"}` | như FEAT-012 + phạm vi khoa | (dịch vụ, khoa) có hệ thống "Đang dùng" mà `test_system` trống → "Dịch vụ có hệ thống xét nghiệm: chọn hệ thống cho bộ định mức (GLU-A, GLU-B)"; dịch vụ không có hệ thống mà truyền `test_system` → từ chối (ASM-034-01); DI-15; hệ thống đã có bộ Nháp/Đã xác nhận chuyên môn → trả tên bộ đó + `message` (ASM-034-14) |
| `get_norm_set(name)` **đổi** | | dict 3.1 | như FEAT-012 | |
| `save_line(...)` **giữ chữ ký** | `values` nhận thêm `cost_level`, `apply_k`, `attach_to`, `attach_equipment`, `template_item` | như FEAT-012 | như FEAT-012 | DI-17, FR-NORM-024 (TC-CLS-31), ASM-034-09, 23 |
| `save_head(norm_set, values)` **mới** | `values` chỉ nhận `tests_per_tube` | `norm_set` | ghi; "Nháp" | Trường khác → "Trường không được nhập"; số < 0 → từ chối |
| `confirm_set(norm_set)` **đổi** | | | như FEAT-012 | Lỗi bộ (`set_blockers`) **đứng trước** lỗi dòng (`confirm_blockers`), cùng một thông báo (TC-CLS-32) |
| `copy_norm_set(source, test_system)` **mới** | | `{"name", "skipped": [{"line_id","reason"}]}` hoặc `{"name","message"}` khi đã có bộ đang soạn | đọc nguồn; `has_permission("NC Norm Set","create")` + phạm vi khoa trên bộ mới | ASM-034-13 |
| `new_version(norm_set)` **đổi** | | | | Mang `test_system`, `tests_per_tube`, `norm_template`; kiểm bộ đang soạn theo hệ thống (ASM-034-14) |
| `export_norm_set(name)` **mới** | | tệp `.xlsx` (`frappe.response.filename`, `filecontent`, `type = "binary"`) | `has_permission(read, doc)` | — |
| `lock_set` | | | giữ | Không kiểm cảnh báo nội kiểm (ASM-034-17) |

Chi tiết:
- `create_norm_set`: `create_from_procedure(procedure, test_system)` → (1) sinh dòng `lines_from_resources` như FEAT-012; (2) dịch vụ cận lâm sàng và có mẫu đang dùng (`templates.pick_template`) → `templates.apply_template(lines, items, paraclinical)` (ASM-034-04); (3) có `test_system` → `templates.default_apply_k(lines)` (ASM-034-06); (4) `version_no` theo (dịch vụ, khoa, hệ thống); `ns.flags.from_procedure = True`; `insert`.
- `save_line`: sau `row.update(values)` controller chạy `normalize_line` rồi `line_errors`; `apply_k` = 1 với `wastage_rate` 5 → lưu được, `wastage_rate` = 0 (TC-CLS-30).
- `copy_norm_set`: nạp nguồn, hệ thống đích, quy trình "Đã ban hành" của (dịch vụ, khoa đích), `qc_items` của hệ thống đích; gọi `norm.copy.copy_lines(src_lines, target_step_ids, target_resource_rows, equipment_map, qc_items)` → (dòng, bỏ); tạo bộ Nháp; `copied_from` = nguồn.
- `export_norm_set`: gom dữ liệu (mục 4.4) rồi `exports.norm_set.build_workbook(data) -> bytes`; tên tệp `<tên bộ>.xlsx`.
- `_latest_k(test_system)`: ASM-034-16; `frappe.db.exists("DocType", "NC Test System Cost")` sai → `None`.

### 3.1 `get_norm_set` — phần thêm (khóa FEAT-012 giữ nguyên)
```
doc += {test_system, test_system_label ("GLU-A · EQ_A"), tests_per_tube, norm_template, copied_from}
line += {cost_level, apply_k, attach_to, attach_equipment, template_item, "placeholder": bool, "qc_conflict": bool}
"set_blockers": ["<lý do>", ...],                 # FR-NORM-020, 023, 024, ASM-034-01 (chỉ ở Nháp)
"warnings": [{"code": "missing_iqc", "message"}],  # TC-CLS-26 (ASM-034-17)
"template_items": [{"item_name","component","default_cost_level","is_mandatory","satisfied"}],
"options" += {"cost_level": [{"value","label"}], "attach_to": [...]},
"meta" += {"is_paraclinical": bool, "has_test_system": true, "other_test_systems": [{"name","main_equipment"}]},
"actions" += "save_head" (cùng điều kiện save_line), "copy_norm_set" (bộ có test_system, có quyền create, còn hệ thống khác), "export_norm_set" (mọi người đọc được)
```
`summary.incomplete` bật khi có dòng `cost.missing` = "Tính ở lần tính giá" (ASM-034-22).

## 4. Logic thuần (không import `frappe`, pytest)

### 4.1 `normcore/norm/validation.py` (nối thêm, giữ chữ ký)
- Hằng `COST_LEVELS = ("RESULT","TUBE","BATCH","DAY","PERIOD")`, `COST_LEVEL_LABELS`, `ATTACH_TO = ("Hệ thống xét nghiệm","Thiết bị")`.
- `is_placeholder(line) -> bool` (ASM-034-05).
- `normalize_line(line: dict, ctx: dict) -> dict` (trả bản sao đã chuẩn hóa; controller ghi lại vào dòng): không cận lâm sàng → RESULT, `apply_k` 0, xóa `attach_*`; cấp khác DAY/PERIOD → xóa `attach_*`; `attach_to` ≠ Thiết bị → xóa `attach_equipment`; `apply_k` hợp lệ (RESULT, DRUG/SUPPLY, có hệ thống) → `wastage_rate` 0, `wastage_reason` trống.
- `line_errors(line, ctx)` thêm:
  - dòng giữ chỗ chưa sửa: bỏ ba mục thiếu "Nguồn lực", "Đơn vị", "Định mức của bệnh viện" (ASM-034-05);
  - `cost_level` ngoài `COST_LEVELS` → lỗi;
  - DI-17: `apply_k` mà cấp ≠ RESULT → "Dòng L004: chỉ bật Nhân k ở dòng Theo kết quả"; cấu phần ∉ DRUG/SUPPLY → "...chỉ dòng thuốc, hóa chất, vật tư"; không có hệ thống → "...chỉ ở bộ có hệ thống xét nghiệm";
  - ASM-034-09: DAY/PERIOD thiếu `attach_to` → "Dòng Lxxx thiếu: Gắn với"; "Hệ thống xét nghiệm" khi bộ không có hệ thống → lỗi; "Thiết bị" thiếu `attach_equipment` → "thiếu: Thiết bị được gắn";
  - FR-NORM-024: `ctx.changed` và `resource` ∈ `ctx.qc_items` → "Dòng Lxxx: QC_L đã có trong kế hoạch nội kiểm/chuẩn máy của hệ thống GLU-A, không làm dòng định mức (tính từ kế hoạch chất lượng)";
  - ASM-034-23: `template_item` có mà ∉ `ctx.template_items` → lỗi.
- `set_blockers(head: dict, lines: list, ctx: dict) -> list[str]` (mới; `head` có `test_system`, `tests_per_tube`; `ctx` có `ts_required`, `qc_items`, `mandatory_items`): theo thứ tự (1) "Chưa gắn hệ thống xét nghiệm" khi `ts_required` mà trống; (2) FR-NORM-020 "Chưa nhập Số xét nghiệm bình quân trên một ống mẫu (dòng Theo ống mẫu: L001)"; (3) FR-NORM-023 "Thiếu khoản mục bắt buộc của mẫu: Vật tư lấy mẫu, Thiết bị" (ASM-034-11); (4) FR-NORM-024 mọi dòng không loại trừ dùng `qc_items` → "Dòng L00x dùng mặt hàng của kế hoạch chất lượng: QC_L".
- `mandatory_status(items, lines) -> list[{"item_name", "satisfied"}]` dùng cho (3) và cho `template_items` của 3.1.

### 4.2 `normcore/norm/templates.py` (mới)
- `template_errors(values, other_active: list[str]) -> list[str]` (ASM-034-21, ASM-034-03: "Nhóm Hóa sinh đã có mẫu đang dùng: MDM-HOA-SINH").
- `pick_template(rows, cls_group) -> name | None`: mẫu `is_active` cùng nhóm (đã bảo đảm ≤ 1).
- `apply_template(lines, items, paraclinical) -> list[dict]` (ASM-034-04): trả danh sách dòng mới (dòng cũ đã gán `template_item`, `cost_level`, cộng dòng giữ chỗ cuối danh sách theo thứ tự khoản mục). Không đổi đầu vào.
- `default_apply_k(lines) -> list[dict]` (ASM-034-06).
- `DEFAULT_TEMPLATES` (ASM-034-18): dữ liệu hai mẫu cài sẵn; `install.py` chỉ đọc hằng này.

### 4.3 `normcore/norm/copy.py` (mới; FR-NORM-025)
`copy_lines(lines, step_ids, resource_rows, equipment_map, qc_items) -> (list[dict], list[{"line_id","reason"}])`: theo ASM-034-13; lý do bỏ: "Mã bước S00x không còn trong quy trình", "Mặt hàng thuộc kế hoạch chất lượng của hệ thống đích". Chỉ sao chép trường trong `LINE_INPUTS` (truyền vào), bỏ `confirmed_*`, `ai_suggested` giữ nguyên giá trị.

### 4.4 `normcore/exports/norm_set.py` (mới; FR-OUT-006 phần Excel + FR-OUT-011)
`build_workbook(data: dict) -> bytes` — chỉ dùng `openpyxl`, không `frappe`; `data` do API gom:
- Trang "Bộ định mức": đầu trang (dịch vụ, khoa, phiên bản, trạng thái, quy trình, hệ thống xét nghiệm, số xét nghiệm mỗi ống, người khóa, thời điểm khóa); bảng dòng theo thứ tự bước (cột: Bước, Tên bước, Mã dòng, Cấu phần, Nguồn lực, Cấp phát sinh, Nhân k, Gắn với, Số người, Định mức BV, Định mức ban hành, Lượng áp dụng, Đơn vị, Hao hụt %, Căn cứ, Tham chiếu căn cứ, Loại trừ, Lý do loại trừ, Người xác nhận, Thời điểm xác nhận). Bộ không có hệ thống: bỏ ba cột Cấp phát sinh, Nhân k, Gắn với.
- Bộ có hệ thống, thêm: trang "Nội kiểm" (vật liệu, số mức, lần/ngày, lượng/lần, số thông số dùng chung, ngày chạy/năm); "Chuẩn máy" (chất chuẩn, số điểm, lần lặp, lần/năm, chi phí/lần); "Ngoại kiểm" (mã, tên chương trình, nhà cung cấp, đợt/năm, mẫu/đợt, phí năm, phí vận chuyển, tỷ lệ của dịch vụ) — từ NC EQA Program có `services.technical_service` = dịch vụ; "Hệ số k" (hệ thống, lần tính giá, ngày tính, k 6 chữ số thập phân, nhãn "Ước tính từ kế hoạch" khi `k_estimated`; không có → "Chưa có lần tính giá", ASM-034-16). Không có kế hoạch chất lượng → trang ghi "Chưa có kế hoạch chất lượng".
- Nhãn tiếng Việt; số giữ kiểu số (không chuỗi) để Excel tính được; k định dạng `0.000000`.

## 5. Giao diện (chi tiết ở `ui-design.md`)
- SCR-DSK-041: Form/List chuẩn NC Norm Template (`nc_norm_template.js`, `nc_norm_template_list.js`), lối tắt Workspace "Mẫu định mức".
- SCR-DSK-014: mở rộng `NormGrid.vue` (đầu trang có hệ thống, ô số xét nghiệm mỗi ống, dải cảnh báo, cột Cấp phát sinh, Nhân k, bộ lọc cấp, tô dòng giữ chỗ, nút Sao chép, Xuất Excel).
- SCR-DSK-013 và form quy trình: nút "Khởi tạo bộ định mức" gọi `create_options` → hộp chọn hệ thống khi `required`.

## 6. Tiêu chí nghiệm thu

Dữ liệu: dịch vụ GLU (`is_paraclinical`, `cls_group` Hóa sinh), khoa XN, quy trình "Đã ban hành"; hệ thống GLU-A (EQ_A), GLU-B (EQ_B) theo `test-cases.md` 2A.1; NC Item HC_GLU, ONG, CUVET, DD_RUA, HC_PT, QC_L; NC QC Plan của GLU-A có nội kiểm QC_L (golden `IQC`). Số liệu đọc từ `docs/golden/golden_cls.py` khi cần, không chép.

| # | Điều kiện kiểm được | TC | FR | Test |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Mẫu Hóa sinh đang dùng (Vật tư lấy mẫu · SUPPLY · TUBE · bắt buộc; Hóa chất chính · DRUG · bắt buộc; Thiết bị · EQUIPMENT · bắt buộc); quy trình có dòng nguồn lực Hóa chất và Nhân lực, không có Vật tư/Thiết bị. `create_norm_set(proc, "GLU-A")` → `test_system` = GLU-A, tên `DM-GLU-XN-GLU-A-v1`, `norm_template` = mẫu; dòng Hóa chất có `template_item` "Hóa chất chính"; thêm đúng 2 dòng `service_level` = 1 (Vật tư lấy mẫu cấp TUBE, Thiết bị), `hospital_qty` trống/0, `resource` trống. `create_norm_set` không truyền hệ thống → từ chối, thông báo nêu GLU-A, GLU-B; truyền hệ thống của dịch vụ khác → từ chối (DI-15); bộ thiếu hệ thống (dựng qua `make_norm_set`) → `confirm_set` từ chối "Chưa gắn hệ thống xét nghiệm" | TC-CLS-29 | FR-NORM-017, 021, 022 | `api/test_norm_cls.py::test_TC_CLS_29_khoi_tao_gan_he_thong_va_them_khoan_muc_bat_buoc` |
| 2 | Đặt cấp cho từng dòng (5 giá trị) → lưu; `apply_k` = 1 ở dòng BATCH → từ chối, CSDL không đổi; `apply_k` ở LABOR RESULT → từ chối; dòng SUPPLY RESULT hao hụt 5% bật `apply_k` → lưu, `wastage_rate` = 0; dịch vụ không cận lâm sàng gửi `cost_level` TUBE → lưu thành RESULT | TC-CLS-30 | FR-NORM-018, 019 | `test_TC_CLS_30_cap_phat_sinh_va_co_k` |
| 3 | `save_line` thêm dòng DRUG dùng QC_L ở bộ GLU-A → ValidationError, thông báo có "QC_L" và "kế hoạch"; CSDL không thêm dòng. Cùng dòng ở bộ của dịch vụ không có kế hoạch → lưu được | TC-CLS-31 | FR-NORM-024 | `test_TC_CLS_31_tu_choi_dong_trung_ke_hoach_chat_luong` |
| 4 | Bộ có dòng TUBE, mọi dòng đã xác nhận, `tests_per_tube` trống → `confirm_set` từ chối, thông báo "Số xét nghiệm bình quân trên một ống mẫu", giữ Nháp; `save_head(tests_per_tube=4)` → qua bước này. Thiếu khoản mục bắt buộc "Thiết bị" → từ chối, thông báo nêu "Thiết bị"; loại trừ dòng giữ chỗ với lý do "Không áp dụng" → `confirm_set` chuyển "Đã xác nhận chuyên môn" | TC-CLS-32 | FR-NORM-020, 023 | `test_TC_CLS_32_xac_nhan_can_so_xn_moi_ong_va_khoan_muc_bat_buoc` |
| 5 | Bộ GLU-A khóa; `copy_norm_set(GLU-A bộ, "GLU-B")` → bộ Nháp `DM-GLU-XN-GLU-B-v1`, `copied_from`, dòng giữ `line_id`, không có xác nhận, dòng L05 `attach_equipment` EQ_A → EQ_B; xác nhận và khóa bộ GLU-B → cả hai bộ "Đã khóa" (DI-03 theo hệ thống, bộ GLU-A **không** thành "Đã thay thế"); `export_norm_set` mỗi bộ → tệp mở được bằng openpyxl, trang dòng có cột "Cấp phát sinh" đúng giá trị, có trang "Nội kiểm" (QC_L), "Chuẩn máy", "Ngoại kiểm", "Hệ số k" (ô k = "Chưa có lần tính giá") | TC-CLS-33 | FR-NORM-017, 025, FR-OUT-011 | `test_TC_CLS_33_sao_chep_khoa_hai_bo_va_xuat` |
| 6 | `build_workbook` với k = 1,108247 (lấy `golden_cls.k_factor("GLU-A")[0]`), `k_estimated` sai → ô k số 1.108247, định dạng 6 chữ số; GLU-B (`k_factor("GLU-B")`, ước tính) → nhãn "Ước tính từ kế hoạch"; bộ không có hệ thống → không có ba cột cận lâm sàng, không có trang kế hoạch | TC-CLS-33 | FR-OUT-011, FR-OUT-006 | `exports/test_norm_set_export.py::test_TC_CLS_33_tep_xuat_co_k_6_chu_so` |
| 7 | Hệ thống GLU-A nhóm Hóa sinh không có kế hoạch nội kiểm → `get_norm_set` có `warnings[0].code` = `missing_iqc`; Finance `lock_set` vẫn chuyển "Đã khóa" | TC-CLS-26 | FR-QC-007 | `test_TC_CLS_26_canh_bao_tren_bo_dinh_muc_van_khoa_duoc` |
| 8 | Mẫu: hai mẫu đang dùng cùng nhóm → từ chối; trùng tên khoản mục → từ chối; mẫu đang dùng không có khoản mục → từ chối. Quyền: NC Council Member đọc/ghi NC Norm Template → PermissionError; NC Auditor đọc được, tạo/sửa → PermissionError; NC Clinician tạo → PermissionError; NC Finance tạo được; DocPerm khớp ma trận | — | FR-NORM-021, FR-ACC-002, FR-ACC-007 | `nc_norm_template/test_nc_norm_template.py::test_FR_NORM_021_*`, `test_quyen_norm_template_*` |
| 9 | `new_version` bộ GLU-A đã khóa → bộ mới có `test_system` GLU-A, `tests_per_tube`, `norm_template`; tạo bộ khi GLU-A đã có bộ Nháp → trả tên bộ đó | — | FR-NORM-017, DI-03 | `test_FR_NORM_017_phien_ban_moi_giu_he_thong` |
| 10 | Lần tính giá (FEAT-031 `nc_costing_run`) với bộ có `test_system` "Ngừng dùng" bỏ bộ đó (trường `test_system` nay có thật) — test cũ FEAT-031 xanh | — | FR-NORM-017 | test cũ `nc_costing_run/test_nc_costing_run.py` |
| 11 | Hàm thuần phủ mọi nhánh: `normalize_line`, `line_errors` (luật mới), `set_blockers`, `mandatory_status`, `template_errors`, `apply_template` (khớp theo cấu phần, giữ chỗ, không bắt buộc không thêm), `default_apply_k`, `copy_lines` | — | FR-NORM-017..025 | `tests/unit/test_norm_cls.py`, `test_norm_templates.py`, `test_norm_copy.py` |
| 12 | Toàn bộ test cũ (FEAT-012 TC-NORM-*, golden `test_norm_golden.py`) xanh không sửa; patch đặt RESULT cho dòng cũ; độ phủ `normcore/costing` ≥ 90% | — | NFR-MNT-001 | T13 |

## 7. Rủi ro
- **Bật `test_system` có thật** làm nhánh `has_field("test_system")` của `nc_costing_run.py:43` chạy: test FEAT-031 dựng bộ định mức không có hệ thống vẫn qua (`norm_sets_to_cost` giữ bộ không gắn hệ thống). Dev chạy `test_nc_costing_run` sớm (T03).
- **Test cũ tạo bộ cho dịch vụ có hệ thống xét nghiệm**: `nc_test_system/test_nc_test_system.py` (`_locked_run`, hai test `test_FR_SVC_011_*`) dựng bộ qua `make_norm_set` không có `test_system` rồi `confirm_norm_set` + `lock()`. ASM-034-01 giữ chúng xanh (yêu cầu hệ thống chỉ ở `create_norm_set` API và `confirm_set`). Dev vẫn chạy `grep -rln "NC Norm Set\|make_norm_set" normcore --include=test_*.py` ở T03 và chạy các module đó; test cũ nào đỏ thì **dừng, báo Lead** (CLAUDE.md 3.1), không tự sửa test.
- **Mẫu cài sẵn đang dùng** sẽ thêm dòng giữ chỗ vào mọi bộ Hóa sinh/Miễn dịch mới → cài ở trạng thái chưa bật (ASM-034-18).
- **Frappe lưu Float trống thành 0**: `hospital_qty`, `tests_per_tube` trống = 0 = "chưa nhập" (như FEAT-012).
- Tệp chung phải chạm: `scripts/check_conventions.py` (ánh xạ quyền), `hooks.py` (`after_migrate`), `install.py`, `patches.txt`, `vi.csv`, Workspace NC Costing, `docs/data-model.md` (áp AMD-034-01). Theo quy tắc tránh conflict 5: Dev nêu danh sách này trong PR để Lead duyệt.

## 8. Tệp chạm tới
Mới: `normcore/norm/templates.py`, `normcore/norm/copy.py`, `normcore/exports/norm_set.py`, `normcore/exports/test_norm_set_export.py`, `normcore/api/test_norm_cls.py`, `normcore/nc_costing/doctype/nc_norm_template/*` (json, py, js, `_list.js`, `test_nc_norm_template.py`), `normcore/nc_costing/doctype/nc_norm_template_item/*`, `normcore/patches/set_norm_line_cost_level.py`, `normcore/tests/unit/test_norm_cls.py`, `test_norm_templates.py`, `test_norm_copy.py`, `docs/as-built/FEAT-034.md`.
Sửa: `nc_norm_set.json`, `nc_norm_set.py`, `nc_norm_set_list.js`, `nc_norm_line.json`, `normcore/norm/validation.py`, `normcore/api/norm.py`, `normcore/public/js/norm_grid/NormGrid.vue`, `nc_clinical_procedure.js` (hộp chọn hệ thống), `normcore/install.py`, `hooks.py`, `patches.txt`, `scripts/check_conventions.py`, Workspace NC Costing, `normcore/translations/vi.csv`, `docs/data-model.md` (AMD-034-01), `docs/rtm-testref.md` (mục `## FEAT-034`, quy tắc 4; hoặc `docs/rtm-testref/FEAT-034.md` nếu thư mục đã có trên develop), `docs/decisions/assumptions/FEAT-034.md` (trạng thái).

## 9. Ghi chú cho Dev
- Mọi lệnh `bench` qua `scripts/with_bench.sh`, migrate và test trong cùng một lần gọi.
- Không đổi `costing/engine.py`, `costing/provisional.py` (chỉ `api/norm.py::_cost` đổi nhánh theo ASM-034-22). Không có công thức tiền mới trong FEAT này.
- `golden_cls.py` chỉ dùng để lấy số k cho test xuất (mục 6 #6) và dữ liệu dựng bộ (mục `NORM`); import, không chép số.
- Tên test mang mã TC; mọi TC-CLS-29..33 và TC-CLS-26 có test cùng mã.

## 10. Điểm Lead nên xem (không chặn)
1. ASM-034-15/16: FR-OUT-011 làm trước FR-OUT-006 (FEAT-019 đứng sau); k trong tệp là "Chưa có lần tính giá" cho tới FEAT-036. Nếu Lead muốn k thật ở TC-CLS-33 thì cần đưa hàm k (BR-CLS-001) vào FEAT này — BA đề xuất **không**, để FEAT-036 làm.
2. ASM-034-18: mẫu cài sẵn ở trạng thái chưa bật.
3. ASM-034-04: ghép khoản mục với dòng quy trình theo cấu phần, dòng đầu tiên.
