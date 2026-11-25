# FEAT-035 — Sản lượng cận lâm sàng và xuất kho — Thiết kế kỹ thuật

Issue NORM-36. Nguồn: `srs.md` FR-ACCT-012..015, FR-SVC-009, FR-QC-006 (cột trống), FR-CLS-007 (mục sản lượng), A-07, TBD-16, IF-07, IF-08; `use-cases.md` UC-022 (bước 1–4, luồng 1a, 2a, 2b); `data-model.md` 3.6 [1.1] (NC Test System Volume, NC Equipment Usage, NC Stock Issue Actual, NC Service Volume), mục 4 dòng "Sản lượng cận lâm sàng, phút khai thác, xuất kho thực tế", DI-14; `ux-foundations.md` SCR-DSK-021, SCR-DSK-037; `test-cases.md` mục bộ dữ liệu vàng cận lâm sàng (GLU-A, GLU-B, HC_GLU, V6), TC-CLS-34..36; `docs/golden/golden_cls.py` (`SYSTEMS`, `ITEMS`, `material_recon`). Phụ thuộc đã DONE: FEAT-004 (khung nhập), FEAT-031 (NC Test System, NC Service Code Map), FEAT-016 (NC Service Volume có `scenario`).

Không làm lại cơ chế đã có: đọc tệp, chuẩn hóa ô, lỗi theo dòng, tệp mẫu, trang `import-excel` và tham số `import_set` (FEAT-004, ASM-004-01); NC Service Volume và kịch bản (FEAT-016, đã có `scenario` BB, mặc định "Thực tế 12 tháng", khóa 4 trường); phạm vi khoa `core/permissions.py::SCOPE_RULES` (FEAT-001/031); sổ sự kiện `core/audit.py` (hook chung); hằng `SCENARIOS` ở `core/import_sets.py`, `valid_year` ở `costing/allocation_rules.py`.

## 1. Phạm vi

| FR | Mức | Làm gì ở FEAT này |
| :-- | :-- | :-- |
| FR-ACCT-012 | Must | Ba DocType sản lượng có `scenario` (Select BB, mặc định "Thực tế 12 tháng"); cột "Kịch bản sản lượng" bắt buộc trong tệp sản lượng cận lâm sàng và tệp phút khai thác. NC Service Volume đã có kịch bản từ FEAT-016: **không đổi** |
| FR-ACCT-013 | Must | DocType NC Test System Volume + bộ nhập `nc_test_system_volume`: lưu theo (năm, kịch bản, hệ thống xét nghiệm); dịch vụ, khoa lấy từ hệ thống; mã ngoài (LIS/RIS/HIS) đổi sang mã dịch vụ qua NC Service Code Map (FR-SVC-009); chỉ "Số kết quả trả" bắt buộc, các cột test phụ để trống được (giữ rỗng, không ghi 0). DocType NC Equipment Usage + bộ nhập `nc_equipment_usage` cho tổng phút khai thác của thiết bị chia theo Phút chiếm máy |
| FR-ACCT-014 | Must | Dòng có mã dịch vụ / mã khoa / mã hệ thống không tồn tại, hoặc số âm → lỗi dòng liệt kê (dòng Excel, cột, lý do) ở cả "Kiểm tra" và "Xác nhận ghi"; dòng đó không lưu, dòng khác vẫn lưu |
| FR-ACCT-015 | Must | DocType NC Stock Issue Actual + bộ nhập `nc_stock_issue_actual`: lượng xuất theo (năm, khoa, mặt hàng), theo đơn vị mua `NC Item.uom` |
| FR-CLS-007 | Should | Một phần: mục `volume` ("Sản lượng kịch bản mặc định") của khối tình trạng NC Test System hiện số kết quả trả năm gần nhất kịch bản "Thực tế 12 tháng" (ASM-035-10). Ba mục còn lại giữ nguyên (FEAT-032, 034, 036) |

Không làm: ước tính số test phụ từ kế hoạch và hệ số k (FR-QC-006, FR-COST-018 — FEAT-036; FEAT này chỉ giữ ô trống là `NULL`); Qtb và phân bổ thiết bị theo phút (FEAT-036); đối soát vật chất (FR-COST-026 — FEAT-036 đọc NC Stock Issue Actual); mã HIS ngoài cho NC Service Volume (ASM-125 hoãn tới đây, nhưng không thuộc FR/TC của FEAT-035 — ASM-035-11); `source_file` không ghi qua bộ nhập (ASM-035-06).

## 2. DocType

Mô-đun **NC Costing**. Ba DocType mới (chưa lên staging, không cần patch cấu trúc). Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1, `autoname` = `hash` (data-model: "Naming: tự động", như NC Service Volume). Tùy chọn kịch bản dùng đúng chuỗi `SCENARIOS = ("Thực tế 12 tháng", "Kế hoạch", "Công suất")`. Chỉ mục duy nhất tạo ở `on_doctype_update` (`frappe.db.add_unique`) và kiểm lại ở `validate` để thông báo tiếng Việt (mẫu `nc_service_volume.py`).

### 2.1 NC Test System Volume (DI-14)

| # | Fieldname | Nhãn | Kiểu | BB | Ghi chú |
| :-: | :-- | :-- | :-- | :-: | :-- |
| 1 | fiscal_year | Năm tài chính | Int | Có | 2000..2100; `in_list_view`, `in_standard_filter` |
| 2 | scenario | Kịch bản sản lượng | Select | Có | `SCENARIOS`, mặc định "Thực tế 12 tháng"; `in_list_view`, `in_standard_filter` |
| 3 | test_system | Hệ thống xét nghiệm | Link NC Test System | Có | `in_list_view`, `in_standard_filter` |
| 4 | technical_service | Dịch vụ | Link NC Technical Service | | `fetch_from: test_system.technical_service`, `read_only`, `in_list_view` |
| 5 | department | Khoa | Link NC Department | | `fetch_from: test_system.department`, `read_only`, `in_standard_filter`; trường phạm vi khoa |
| — | col_break | | Column Break | | |
| 6 | patient_results | Số kết quả trả | Float | Có | Qbn, ≥ 0; `in_list_view` |
| 7 | source_file | Tệp nguồn | Attach | | |
| — | aux_section | Số test phụ (để trống: ước tính từ kế hoạch) | Section Break | | |
| 8 | iqc_tests | Số test nội kiểm | Float | | Qnk, ≥ 0, trống = `NULL` |
| 9 | calibration_tests | Số test chuẩn máy | Float | | Qchuan, ≥ 0 |
| 10 | rerun_tests | Số test chạy lại | Float | | Qlai, ≥ 0 |
| 11 | eqa_tests | Số test ngoại kiểm | Float | | Qngk, ≥ 0 |
| — | aux_col | | Column Break | | |
| 12 | wastage_rate | Tỷ lệ hao hụt (%) | Percent | | 0..100 (3 nghĩa là 3%, như `est_wastage_rate` của NC Test System) |
| 13 | avg_batch_size | Cỡ mẻ bình quân | Float | | > 0 nếu có; bắt buộc hay không do FEAT-036 kiểm (FR-COST-023) |
| 14 | run_days | Số ngày chạy máy | Int | | 1..366 nếu có; trống = `NC QC Plan.run_days_per_year` (FEAT-036) |

Float/Int/Percent không đặt `default` và không `non_negative` mặc định 0: ô trống phải giữ `NULL` để FEAT-036 phân biệt "không có số thực tế" với "0" (FR-QC-006, TBD-16). Controller `validate`: (a) `cls_volume.volume_errors(doc)` (mục 4); (b) DI-14 — trùng (năm, kịch bản, hệ thống) → `ValidationError` "Đã có sản lượng năm {0}, kịch bản {1} của hệ thống {2}". Không chặn hệ thống "Ngừng dùng" (số năm cũ vẫn có thể cần) — ASM-035-03.

### 2.2 NC Equipment Usage

| # | Fieldname | Nhãn | Kiểu | BB | Ghi chú |
| :-: | :-- | :-- | :-- | :-: | :-- |
| 1 | fiscal_year | Năm tài chính | Int | Có | 2000..2100; list, filter |
| 2 | scenario | Kịch bản sản lượng | Select | Có | `SCENARIOS`, mặc định "Thực tế 12 tháng"; list, filter |
| 3 | equipment | Thiết bị | Link NC Equipment | Có | list, filter |
| 4 | department | Khoa | Link NC Department | Có | list, filter; trường phạm vi khoa |
| 5 | total_minutes | Tổng số phút khai thác | Float | Có | Mtb, ≥ 0; list |

Duy nhất theo (`fiscal_year`, `scenario`, `equipment`, `department`). `validate`: năm hợp lệ, `total_minutes` ≥ 0, thiết bị có `allocation_basis` = "Phút chiếm máy" (khác → "Thiết bị {0} chia chi phí theo {1}, không cần phút khai thác"; ASM-035-05). Không kiểm thiết bị thuộc khoa (thiết bị dùng chung qua `department_allocations`). Qtb không lưu (data-model).

### 2.3 NC Stock Issue Actual

| # | Fieldname | Nhãn | Kiểu | BB | Ghi chú |
| :-: | :-- | :-- | :-- | :-: | :-- |
| 1 | fiscal_year | Năm tài chính | Int | Có | list, filter |
| 2 | department | Khoa | Link NC Department | Có | list, filter; trường phạm vi khoa |
| 3 | item | Mặt hàng | Link NC Item | Có | list, filter |
| 4 | issued_qty | Lượng xuất | Float | Có | ≥ 0, theo đơn vị mua; list |
| 5 | source_file | Tệp nguồn | Attach | | |

Duy nhất theo (`fiscal_year`, `department`, `item`). Không có kịch bản (data-model). Không thêm trường ngoài data-model: đơn vị mua hiện trên form bằng JS (`frappe.db.get_value("NC Item", item, "uom")`, chỉ hiển thị).

### 2.4 Quyền (data-model mục 4, dòng "Sản lượng cận lâm sàng, phút khai thác, xuất kho thực tế")

| Vai trò | Quyền DocType (cả 3; cùng dạng NC Service Volume của FEAT-016) |
| :-- | :-- |
| NC Finance | read, write, create |
| NC Department Head | read (phạm vi khoa: `SCOPE_RULES` theo `department`) |
| NC Director, NC Admin, NC Auditor | read |
| NC Clinician, NC Council, NC Resource Manager, NC Doc Controller, NC Consultant | không có dòng quyền |

Không ai có `delete` (ASM-128 của FEAT-016 áp tương tự, ASM-035-07). Phạm vi khoa: thêm ba dòng `ScopeRule()` vào `core/permissions.py::SCOPE_RULES` và ba DocType vào `permission_query_conditions`, `has_permission` ở `hooks.py`. `scripts/check_conventions.py`: thêm dòng `MATRIX["Sản lượng cận lâm sàng, phút khai thác, xuất kho thực tế"] = "- R - W - - R - R R"` và ba mục `DOCTYPE_ROW`. `tests/test_permissions.py` tự đọc JSON và data-model, không cần sửa.

## 3. API và lớp Frappe

Không thêm hàm whitelisted mới cho nhập: dùng `normcore.api.importer.list_import_sets`, `download_template`, `import_file` (FEAT-004) với ba khóa bộ nhập mới. Kiểm quyền giữ nguyên (quyền `create` DocType đích để nhập, `read` để tải mẫu).

Tệp mới `normcore/api/cls_volume.py` (không whitelisted, chỉ gọi từ khung nhập qua `ImportSet.prepare`, mục 5): ba hàm chuẩn bị dòng, mỗi hàm nhận `values` (dict đã chuẩn hóa kiểu, đã qua kiểm Link) và trả dict cập nhật hoặc ném `RowValueError(nhãn_cột, thông_báo)`:

| Hàm | Việc |
| :-- | :-- |
| `prepare_test_system_volume(values)` | Đọc NC Test System (`technical_service`, `department`); đổi mã dịch vụ: `cls_volume.resolve_service(values.get("source_system"), values["service_code"], map_lookup, service_exists)` với `map_lookup(src, code)` = `frappe.db.get_value("NC Service Code Map", {"source_system": src, "external_code": code, "parenttype": "NC Technical Service"}, "parent")`; kiểm khớp dịch vụ/khoa với hệ thống (`cls_volume.system_mismatch`); kiểm số (`cls_volume.volume_errors`). Trả `{"technical_service": ..., "department": ...}` của hệ thống |
| `prepare_equipment_usage(values)` | `cls_volume.usage_errors(values, allocation_basis)` với `allocation_basis` đọc từ NC Equipment |
| `prepare_stock_issue(values)` | `cls_volume.stock_errors(values)` |

Lỗi đầu tiên của dòng được báo theo cột (một dòng có thể có nhiều lỗi: ném `RowValueError` chứa danh sách `[(cột, thông báo)]`, khung thêm từng lỗi). Kiểm ở `prepare` chạy ở cả chế độ "thu" và "ghi" nên "Kiểm tra" đã liệt kê đủ lỗi của FR-ACCT-014 (số âm không đợi tới `validate`); `validate` của DocType gọi cùng hàm thuần để form nhập tay cũng bị chặn.

`normcore/api/test_system.py::get_status(test_system)` (đã có, FEAT-031): truyền thêm bản ghi NC Test System Volume mới nhất (`scenario` = "Thực tế 12 tháng", `fiscal_year` lớn nhất, lọc theo quyền đọc của người dùng — dùng `frappe.get_list`) vào `test_systems.status_items(volume=...)`. Không đổi chữ ký whitelisted.

## 4. Logic thuần — `normcore/costing/cls_volume.py` (không import `frappe`; phủ ≥ 90%)

| Hàm | Kết quả | Căn cứ |
| :-- | :-- | :-- |
| `AUX_FIELDS = ("iqc_tests", "calibration_tests", "rerun_tests", "eqa_tests")` | | FR-ACCT-013 |
| `NON_NEGATIVE = ("patient_results", *AUX_FIELDS, "wastage_rate", "avg_batch_size", "run_days")`; `LABELS` (nhãn tiếng Việt của từng trường, dùng chung với cột nhập) | | |
| `volume_errors(get) -> list[(field, msg)]` | `get(field)` trả giá trị hoặc `None`. Năm ngoài 2000..2100 (`allocation_rules.valid_year`); `patient_results` thiếu → "bắt buộc"; số âm ở mọi trường `NON_NEGATIVE` → "{nhãn} không được âm"; `wastage_rate` > 100 → "không quá 100"; `avg_batch_size` = 0 → "phải lớn hơn 0"; `run_days` > 366 hoặc = 0 → "từ 1 đến 366" | FR-ACCT-014, ASM-035-03 |
| `resolve_service(source_system, code, map_lookup, service_exists) -> str` | `source_system` rỗng → `code` nếu `service_exists(code)`; có → `map_lookup(source_system, code)`; không thấy → `ValueError('Mã dịch vụ "{code}" không có trong ánh xạ mã {src}')` hoặc `'"{code}" không tồn tại trong NC Technical Service'` | FR-SVC-009, FR-ACCT-013, 014 |
| `system_mismatch(system, service, department) -> list[(field, msg)]` | Dịch vụ đã đổi ≠ `system.technical_service` → ("service_code", "Hệ thống {ts} thuộc dịch vụ {a}, dòng ghi {b}"); khoa ≠ `system.department` → ("department", tương tự) | ASM-035-02 |
| `blank_aux(get) -> list[str]` | Các trường `AUX_FIELDS` đang `None` (để hiển thị "Sẽ ước tính từ kế hoạch") | FR-QC-006, SCR-DSK-037 |
| `usage_errors(get, allocation_basis) -> list` | Năm; `total_minutes` thiếu/âm; `allocation_basis` ≠ "Phút chiếm máy" | FR-ACCT-013, ASM-035-05 |
| `stock_errors(get) -> list` | Năm; `issued_qty` thiếu/âm | FR-ACCT-015, ASM-035-06 |
| `volume_status(rec) -> dict` | `rec` None → `{"state": "empty", "message": "Chưa có"}`; có → `{"state": "ok"|"estimated", "message": "Năm {y}: {Qbn} kết quả trả"}` (+ " — số test phụ sẽ ước tính từ kế hoạch" khi `blank_aux` khác rỗng; `state` = "estimated") | FR-CLS-007, ASM-035-10 |

Không có công thức tiền hay hệ số k ở FEAT này; không cần đối chiếu golden ngoài dữ liệu vào (GLU-A, GLU-B, HC_GLU lấy đúng số `golden_cls.py`: Qbn 12.000/4.000, nội kiểm 600, chuẩn máy 48, chạy lại 240, ngoại kiểm 12, hao hụt 3%, 300 ngày, cỡ mẻ 40; xuất 94 hộp). `test_systems.status_items(volume=None)` (đã có, `costing/test_systems.py`): thêm tham số tùy chọn, mục `volume` lấy `cls_volume.volume_status(volume)`; gọi không tham số cho kết quả như cũ (test FEAT-031 giữ nguyên).

## 5. Khung nhập (FEAT-004) — mở rộng tương thích ngược (ASM-035-01)

`core/importer.py`:
1. `Column` thêm `virtual: bool = False`: cột được đọc, chuẩn hóa, kiểm Link và đưa vào `prepare`, nhưng **không** so với bản ghi đang có và **không** ghi vào DocType.
2. `ImportSet` thêm `prepare: str | None = None` (đường dẫn hàm lớp Frappe, ví dụ `"normcore.api.cls_volume.prepare_test_system_volume"`) và thuộc tính `stored_columns` (các cột không `virtual`).
3. `class RowValueError(ValueError)` mang `errors: list[(nhãn cột, thông báo)]`.
4. `process(..., prepare: Callable | None = None)`: sau bước kiểm Link, nếu có `prepare` thì `values = {**values, **prepare(values)}`; `RowValueError` → thêm từng lỗi dòng, bỏ dòng; sau đó bỏ khóa của cột `virtual` khỏi `values` trước khi so sánh/ghi. Không có `prepare` và không cột `virtual` → hành vi y như cũ.
`api/importer.py::run_import`: `lookup` chỉ đọc `stored_columns`; nếu `s.prepare` có giá trị → `frappe.get_attr(s.prepare)` truyền vào `process`.
Test FEAT-004/016/031 cũ giữ nguyên và phải xanh.

Bộ nhập mới (`core/import_sets.py`, đăng ký sau `nc_cost_center_driver`):

```python
SOURCE_SYSTEMS = ("HIS", "LIS", "RIS")  # đúng tùy chọn NC Service Code Map.source_system

NC_TEST_SYSTEM_VOLUME = ImportSet(
    key="nc_test_system_volume", label="Sản lượng cận lâm sàng", doctype="NC Test System Volume",
    key_field="test_system", key_fields=("fiscal_year", "scenario", "test_system"),
    prepare="normcore.api.cls_volume.prepare_test_system_volume",
    columns=(
        Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
        Column("scenario", "Kịch bản sản lượng", "Select", required=True, options=SCENARIOS, example="Thực tế 12 tháng"),
        Column("test_system", "Mã hệ thống xét nghiệm", "Link", link_doctype="NC Test System", required=True, example="GLU-A"),
        Column("source_system", "Nguồn mã dịch vụ", "Select", options=SOURCE_SYSTEMS, virtual=True, example="LIS"),
        Column("service_code", "Mã dịch vụ", "Data", required=True, virtual=True, example="LIS-GLU"),
        Column("department", "Mã khoa", "Link", link_doctype="NC Department", required=True, example="HS"),
        Column("patient_results", "Số kết quả trả", "Float", required=True, example=12000),
        Column("iqc_tests", "Số test nội kiểm", "Float", example=600),
        Column("calibration_tests", "Số test chuẩn máy", "Float", example=48),
        Column("rerun_tests", "Số test chạy lại", "Float", example=240),
        Column("eqa_tests", "Số test ngoại kiểm", "Float", example=12),
        Column("wastage_rate", "Tỷ lệ hao hụt (%)", "Float", example=3),
        Column("avg_batch_size", "Cỡ mẻ bình quân", "Float", example=40),
        Column("run_days", "Số ngày chạy máy", "Int", example=300),
    ),
)
NC_EQUIPMENT_USAGE = ImportSet(
    key="nc_equipment_usage", label="Phút khai thác thiết bị", doctype="NC Equipment Usage",
    key_field="equipment", key_fields=("fiscal_year", "scenario", "equipment", "department"),
    prepare="normcore.api.cls_volume.prepare_equipment_usage",
    columns=(
        Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
        Column("scenario", "Kịch bản sản lượng", "Select", required=True, options=SCENARIOS, example="Thực tế 12 tháng"),
        Column("equipment", "Mã thiết bị", "Link", link_doctype="NC Equipment", required=True, example="VD-TB01"),
        Column("department", "Mã khoa", "Link", link_doctype="NC Department", required=True, example="VD-K01"),
        Column("total_minutes", "Tổng số phút khai thác", "Float", required=True, example=120000),
    ),
)
NC_STOCK_ISSUE_ACTUAL = ImportSet(
    key="nc_stock_issue_actual", label="Xuất kho thực tế", doctype="NC Stock Issue Actual",
    key_field="item", key_fields=("fiscal_year", "department", "item"),
    prepare="normcore.api.cls_volume.prepare_stock_issue",
    columns=(
        Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
        Column("department", "Mã khoa", "Link", link_doctype="NC Department", required=True, example="XN"),
        Column("item", "Mã mặt hàng", "Link", link_doctype="NC Item", required=True, example="HC_GLU"),
        Column("issued_qty", "Lượng xuất (đơn vị mua)", "Float", required=True, example=94),
    ),
)
```

Dòng ví dụ của tệp mẫu phải nhập được (G2 của FEAT-004) trên site có dữ liệu tương ứng; mã ví dụ không tồn tại trên site trống chỉ sinh lỗi Link như các bộ nhập khác (như FEAT-016). Ô trống khi **cập nhật** giữ giá trị cũ (khung FEAT-004); xóa một số test phụ đã nhập phải sửa trên form (ASM-035-04). Mã hệ thống là `name` của NC Test System (`test_system_code`); khoa là `name` NC Department.

## 6. Tiêu chí nghiệm thu

Tên test mang mã TC (`test_TC_CLS_34_...`). Dữ liệu chung: `tests/utils.py::make_cls_data()` (khoa `HS-CLS`, dịch vụ GLU cận lâm sàng, EQ_A, EQ_B) + hệ thống GLU-A (EQ_A, 75%), GLU-B (EQ_B, 25%); NC Service Code Map của GLU: (LIS, `LIS-GLU`); khoa XN (`make_base`); mặt hàng HC_GLU (Hóa chất, `uom` "Hộp", 200 test danh nghĩa). Năm 2026.

| # | Điều kiện kiểm được | TC | FR | Vị trí test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Tệp sản lượng kịch bản "Thực tế 12 tháng", nguồn mã LIS, mã `LIS-GLU`: dòng GLU-A (Qbn 12.000, nội kiểm 600, chuẩn máy 48, chạy lại 240, ngoại kiểm 12, hao hụt 3, cỡ mẻ 40, 300 ngày), dòng GLU-B (Qbn 4.000, bốn cột test phụ để trống) → "thu" báo `created` 2, `error_count` 0, không ghi; "ghi" → 2 bản ghi NC Test System Volume khóa (2026, "Thực tế 12 tháng", GLU-A/GLU-B), `technical_service` = "GLU" (mã LIS đã đổi), `department` = khoa của hệ thống; GLU-B có `iqc_tests`, `calibration_tests`, `rerun_tests`, `eqa_tests` là `None` (không phải 0); nhập lại cùng tệp → `unchanged` 2, không tạo trùng; cùng tệp đổi kịch bản "Kế hoạch" → thêm 2 bản ghi riêng | TC-CLS-34 | FR-ACCT-012, FR-ACCT-013, FR-SVC-009 | `api/test_importer_cls_volume.py` |
| 2 | Tệp 4 dòng: GLU-A hợp lệ, GLU-B hợp lệ, 1 dòng mã hệ thống `GLU-X`, 1 dòng `patient_results` = -5 → "thu" và "ghi" đều `error_count` 2, lỗi nêu đúng dòng Excel và cột ("Mã hệ thống xét nghiệm", "Số kết quả trả"); "ghi" lưu 2 dòng đúng, không có bản ghi cho 2 dòng lỗi. Thêm: mã LIS lạ → lỗi cột "Mã dịch vụ"; mã khoa lạ → lỗi "Mã khoa"; mã dịch vụ đúng nhưng khác dịch vụ của hệ thống → lỗi; số test phụ âm, hao hụt 120 → lỗi | TC-CLS-35 | FR-ACCT-014 | như trên |
| 3 | Tệp xuất kho: (2026, XN, HC_GLU, 94) → 1 bản ghi NC Stock Issue Actual khóa (2026, XN, HC_GLU), `issued_qty` 94; nhập lại → không trùng; đổi 100 → `updated` 1; lượng âm → lỗi dòng | TC-CLS-36 | FR-ACCT-015 | `api/test_importer_cls_volume.py` |
| 4 | Form: trùng (năm, kịch bản, hệ thống) → `ValidationError` (DI-14); `scenario` mặc định "Thực tế 12 tháng"; `technical_service`, `department` tự lấy từ hệ thống; số âm → từ chối; thiếu `patient_results` → `MandatoryError` | — | FR-ACCT-012, 013, DI-14 | `nc_test_system_volume/test_nc_test_system_volume.py` |
| 5 | NC Equipment Usage: thiết bị "Phút chiếm máy" lưu được; thiết bị "Số kết quả" → từ chối; trùng 4 trường → từ chối; bộ nhập `nc_equipment_usage` lưu 1 dòng, dòng thiết bị lạ báo lỗi | — | FR-ACCT-013 | `nc_equipment_usage/test_nc_equipment_usage.py`, `api/test_importer_cls_volume.py` |
| 6 | NC Stock Issue Actual: trùng (năm, khoa, mặt hàng) → từ chối; `issued_qty` âm → từ chối | — | FR-ACCT-015 | `nc_stock_issue_actual/test_nc_stock_issue_actual.py` |
| 7 | Quyền 3 DocType khớp ma trận: Finance đọc/ghi/tạo; Director, Admin, Auditor chỉ đọc; Department Head đọc bản ghi khoa mình, không đọc khoa khác (`frappe.get_list` và `has_permission`); Clinician, Consultant, Resource Manager không đọc; không ai xóa; NC Auditor và NC Director gọi `run_import` ba bộ mới → `PermissionError`, không thấy ba khóa trong `list_import_sets`; `check_conventions.py` thoát 0 | — | FR-ACC-002, FR-ACC-003, FR-ACC-007 | từng `test_nc_*.py`, `tests/test_permissions.py` |
| 8 | Khối tình trạng GLU-B (`get_status`): trước khi nhập mục `volume` "Chưa có"; sau TC-CLS-34 → `state` "estimated", thông điệp chứa "4.000" (hoặc "4000" theo định dạng của API) và "ước tính từ kế hoạch"; GLU-A → `state` "ok"; ba mục khác vẫn "Chưa có" | — | FR-CLS-007 | `api/test_test_system.py` (nơi FEAT-031 đã test `get_status`), `tests/unit/test_test_systems.py` |
| 9 | Hàm thuần phủ mọi nhánh `costing/cls_volume.py`; khung nhập: cột `virtual` không bị đọc/ghi, `prepare` ném `RowValueError` thành lỗi dòng ở cả hai chế độ; bộ nhập cũ không đổi (test FEAT-004/016/031 xanh, không sửa) | — | FR-ACCT-013, 014 | `tests/unit/test_cls_volume.py`, `tests/unit/test_importer_prepare.py` |
| 10 | Danh sách bộ nhập của NC Finance trong `api/test_importer.py` thêm đúng 3 khóa mới (so đủ danh sách, không nới assertion) sau Quyết định Lead | — | — | `api/test_importer.py` (ASM-035-09) |

## 7. Giả định và rủi ro

Chi tiết ở `docs/decisions/assumptions/FEAT-035.md`. Không cần AMD: ba DocType đã có trong `data-model.md` 3.6 [1.1]; thay đổi khung nhập là mở rộng tương thích ngược như ASM-124.

| Mã | Tóm tắt |
| :-- | :-- |
| ASM-035-01 | Mở rộng khung nhập: `Column.virtual`, `ImportSet.prepare`, `RowValueError`; tương thích ngược |
| ASM-035-02 | Tệp sản lượng: năm, kịch bản bắt buộc trong tệp; khóa là mã hệ thống; mã dịch vụ + nguồn mã (trống = mã nội bộ) đổi qua NC Service Code Map; mã khoa bắt buộc; dịch vụ/khoa phải khớp hệ thống |
| ASM-035-03 | Quy tắc số: mọi số ≥ 0; hao hụt ≤ 100; cỡ mẻ > 0; ngày chạy 1..366; năm 2000..2100; không chặn hệ thống "Ngừng dùng" |
| ASM-035-04 | Ô test phụ trống lưu `NULL` (FEAT-036 ước tính); cập nhật bằng tệp không xóa số cũ, phải sửa trên form |
| ASM-035-05 | Phút khai thác chỉ cho thiết bị "Phút chiếm máy"; không ràng thiết bị với khoa; có kịch bản |
| ASM-035-06 | Xuất kho theo đơn vị mua, hiển thị `uom` lấy từ mặt hàng; bộ nhập không ghi `source_file` (lịch sử ở `track_changes`, ASM-035 cũ) |
| ASM-035-07 | Quyền theo dòng ma trận; Department Head phạm vi khoa qua `SCOPE_RULES`; không ai xóa |
| ASM-035-08 | SCR-DSK-037 = nhóm lối tắt Workspace + danh sách/form 3 DocType + trang `import-excel` (chọn sẵn bộ nhập); năm/kịch bản chọn bằng bộ lọc danh sách và cột tệp; SCR-DSK-021 thêm nút sang SCR-DSK-037 |
| ASM-035-09 | `api/test_importer.py` danh sách bộ nhập của NC Finance thêm 3 khóa — hệ quả trực tiếp, **chờ Lead duyệt** |
| ASM-035-10 | Mục `volume` của khối tình trạng: năm lớn nhất kịch bản "Thực tế 12 tháng"; "ước tính" khi có cột test phụ trống |
| ASM-035-11 | Không thêm mã HIS ngoài cho NC Service Volume (ngoài FR/TC FEAT-035); NC Service Volume không đổi |

Rủi ro:
- **Chạm khung nhập FEAT-004** (`core/importer.py`, `api/importer.py`): phải chạy lại mọi `api/test_importer*.py` và `tests/unit/test_importer*.py`. Phương án thay nếu Lead muốn giữ khung nguyên: lưu cột mã ngoài vào DocType (cần AMD).
- **TBD-16**: LIS có thể không xuất số test phụ — đã thiết kế cột trống giữ `NULL`; FEAT-036 phải đọc `NULL` là "ước tính" (ghi trong As-Built).
- Ô trống trong tệp Excel đôi khi là `0` do công thức của LIS: 0 được lưu là 0 thật, không ước tính (hướng dẫn trên form).
- Gộp với FEAT khác đang mở: `hooks.py`, `core/permissions.py`, `check_conventions.py`, `vi.csv`, `shortcuts.txt`, `api/test_importer.py` — giữ dòng cả hai bên.
