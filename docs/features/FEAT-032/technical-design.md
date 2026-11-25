# FEAT-032 — Kế hoạch chất lượng và ngoại kiểm — Thiết kế kỹ thuật

Issue NORM-35. Nguồn: `srs.md` FR-QC-001..003, FR-QC-005, FR-QC-007, FR-QC-008, BR-CLS-006..008 (chỉ để biết dữ liệu cần lưu); `use-cases.md` UC-019 (bước 3, 4; luồng 3a, 4a, 2c phần kế hoạch chất lượng); `data-model.md` 3.5 (NC QC Plan, NC QC IQC Line, NC QC Calibration Line, NC EQA Program, NC EQA Service), mục 4 dòng "Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm", DI-11, DI-12, DI-16; `ux-foundations.md` SCR-DSK-033, SCR-DSK-034; TC-CLS-24..26; `golden_cls.py` dòng 126–128 (`IQC`, `CAL`, `EQA`), 154–156 (số test ước tính), 181–193 (BR-CLS-006..008). Phụ thuộc đã DONE: FEAT-031 (NC Test System, `cls_group` trên NC Technical Service, phạm vi khoa), FEAT-009 (NC Item, loại "Vật liệu nội kiểm", "Chất chuẩn").

Không làm lại cơ chế đã có: phạm vi khoa `core/permissions.py::SCOPE_RULES` (FEAT-001, mở rộng nhỏ ở mục 2.4); bộ nhập `core/import_sets.py` (FEAT-004, không sửa khung `core/importer.py`); khối tình trạng `api/test_system.py::get_status` và `costing/test_systems.py::status_items` (FEAT-031, giữ khóa và hành vi cũ khi chưa có kế hoạch).

## 1. Phạm vi

| FR | Mức | Làm gì ở FEAT này |
| :-- | :-- | :-- |
| FR-QC-001 | Must | NC QC Plan (`run_days_per_year` = D) + bảng NC QC IQC Line; mọi trường bắt buộc, miền giá trị (ASM-032-02) |
| FR-QC-002 | Must | Bảng NC QC Calibration Line trong NC QC Plan; mọi trường bắt buộc |
| FR-QC-003 | Must | NC EQA Program + bảng NC EQA Service (ít nhất một dòng); dịch vụ phải là dịch vụ cận lâm sàng, không lặp (ASM-032-04) |
| FR-QC-005 | Must | DI-12 khi lưu NC EQA Program: `share_pct` trống ở mọi dòng hoặc có ở mọi dòng và tổng = 100 (ASM-032-03) |
| FR-QC-007 | Should | **Một phần:** hàm thuần `qc_plans.missing_iqc_warning` + hàm máy chủ `normcore.api.qc_plan.missing_iqc_warning(test_system)`; hiện trên SCR-DSK-032 (thẻ "Kế hoạch chất lượng"). Gắn cảnh báo vào bộ định mức (và kiểm "vẫn khóa được") làm ở FEAT-034 khi `NC Norm Set.test_system` có (ASM-032-05) |
| FR-QC-008 | Must | DI-16 khi lưu NC QC Plan: `qc_material.item_type` = "Vật liệu nội kiểm", `calibrator.item_type` = "Chất chuẩn" |
| FR-CLS-007 | Should | (Phần của FEAT-032 theo ASM-115) thẻ `qc_plan` của khối tình trạng NC Test System có nội dung khi đã có kế hoạch (ASM-032-08) |
| FR-CLS-008 | Should | (Phần của FEAT-032 theo ASM-116) bộ nhập `nc_qc_plan`, chỉ phần đầu kế hoạch (ASM-032-07) |

Không làm: công thức tiền BR-CLS-006..008, FR-QC-004 (chia phí), FR-QC-006 (suy số test từ kế hoạch khi tính) — FEAT-036; TBD-15 (chỉ lưu `shared_parameter_count`, mặc định 1); trường `test_system` và cảnh báo trên NC Norm Set — FEAT-034; đề xuất AI cho kế hoạch (SCR-DSK-033 "đề xuất AI chưa xử lý") — FEAT-038 (R2).

## 2. DocType

Mô-đun **NC Costing** (`normcore/nc_costing/doctype/`). Tiền tố `NC `, fieldname `snake_case` đúng data-model, nhãn tiếng Việt, `track_changes` = 1 cho hai DocType cha. Không thêm trường ngoài data-model.

### 2.1 NC QC Plan (cha)

Autoname `format:KHCL-{test_system}` (data-model ghi `KHCL-.{test_system}`, cùng kết quả `KHCL-GLU-A`, ASM-032-06); `title_field` = `test_system`; `search_fields` = `test_system`; sắp xếp `modified desc`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| test_system | Hệ thống xét nghiệm | Link NC Test System | Có | `unique` = 1 (DI-11), `set_only_once` = 1, `in_list_view`, `in_standard_filter` |
| run_days_per_year | Số ngày chạy mỗi năm | Int | Có | 1 ≤ D ≤ 366; mô tả "Ký hiệu D khi sản lượng không có số ngày thực tế" |
| iqc_lines | Nội kiểm | Table NC QC IQC Line | | |
| calibration_lines | Chuẩn máy | Table NC QC Calibration Line | | |
| estimate_html | Số test ước tính mỗi năm | HTML | | Không lưu; ui-design SCR-DSK-033 |

Bảng con (`istable` = 1, theo quyền cha), đặt `in_list_view` cho mọi trường:

**NC QC IQC Line**: `qc_material` (Link NC Item, BB), `levels` (Int, BB, ≥ 1), `runs_per_day` (Float, BB, > 0), `qty_per_run` (Float, BB, > 0; mô tả "Theo đơn vị định mức của mặt hàng"), `shared_parameter_count` (Int, BB, mặc định 1, ≥ 1; mô tả "Giả định — chờ xác nhận (TBD-15): chia đều theo số thông số").

**NC QC Calibration Line**: `calibrator` (Link NC Item, BB), `points` (Int, BB, ≥ 1), `replicates` (Int, BB, ≥ 1), `calibrations_per_year` (Float, BB, > 0), `cost_per_calibration` (Currency, BB, > 0).

Link `qc_material` / `calibrator` có `link_filters` lọc `item_type` = Vật liệu nội kiểm / Chất chuẩn trên form (chỉ tiện ích; máy chủ vẫn kiểm, TC-CLS-25).

**`validate`** (controller gọi `costing/qc_plans.py::validate_qc_plan`, mục 4). Controller đọc `item_type` của mọi mặt hàng trên dòng bằng một `frappe.get_all("NC Item", {"name": ["in", …]}, ["name", "item_type"])` rồi truyền dict vào hàm thuần.

| Điều kiện | Kết quả |
| :-- | :-- |
| Thiếu `test_system`, `run_days_per_year`, hoặc một trường bắt buộc của dòng (trống / `None`) | từ chối, nêu "Dòng nội kiểm <i>: thiếu <nhãn>" (TC-CLS-24). Frappe coi số 0 là có giá trị nên hàm thuần kiểm miền giá trị để 0 cũng bị từ chối |
| Giá trị ngoài miền ở bảng trên | từ chối, nêu trường và dòng (ASM-032-02) |
| `qc_material` có `item_type` ≠ "Vật liệu nội kiểm" | từ chối: "Dòng nội kiểm 1: mặt hàng HC_GLU thuộc loại Hóa chất, không phải Vật liệu nội kiểm" (DI-16, TC-CLS-25) |
| `calibrator` có `item_type` ≠ "Chất chuẩn" | từ chối, thông báo tương tự (DI-16) |
| Một vật liệu lặp trong bảng nội kiểm, hoặc một chất chuẩn lặp trong bảng chuẩn máy | từ chối (ASM-032-02) |
| `test_system` đã có kế hoạch khác | từ chối: "Hệ thống GLU-A đã có kế hoạch chất lượng KHCL-GLU-A" (DI-11; kiểm ở `validate` cho thông báo tiếng Việt, chỉ mục `unique` chặn khi lưu đồng thời) |

Kế hoạch được phép rỗng cả hai bảng (UC-019 cho lập dần); thiếu nội kiểm chỉ cảnh báo (FR-QC-007). Hệ thống "Ngừng dùng" vẫn có kế hoạch được (DI-07: dữ liệu gốc không khóa).

### 2.2 NC EQA Program (cha)

Autoname `field:eqa_code`; `title_field` = `program_name`; `search_fields` = `program_name, provider, department`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| eqa_code | Mã chương trình | Data | Có | `unique`, cắt khoảng trắng |
| program_name | Tên chương trình | Data | Có | `in_list_view` |
| provider | Đơn vị triển khai | Data | Có | `in_list_view` |
| department | Khoa tham gia | Link NC Department | Có | `in_list_view`, `in_standard_filter`; phạm vi khoa |
| rounds_per_year | Số đợt mỗi năm | Int | Có | ≥ 1 |
| samples_per_round | Số mẫu mỗi đợt | Int | Có | ≥ 1 |
| annual_fee | Phí chương trình năm | Currency | Có | > 0 |
| annual_shipping_fee | Phí vận chuyển năm | Currency | | ≥ 0, mặc định 0 |
| services | Dịch vụ tham gia | Table NC EQA Service | Có | ≥ 1 dòng |
| summary_html | Tóm tắt | HTML | | Không lưu: số mẫu mỗi năm, tỷ lệ hiệu lực từng dòng (ui-design SCR-DSK-034) |

**NC EQA Service** (`istable`): `technical_service` (Link NC Technical Service, BB, `in_list_view`), `share_pct` (Percent, `in_list_view`; mô tả "Để trống ở mọi dòng để chia đều").

**`validate`** (hàm thuần `qc_plans.validate_eqa_program`; controller truyền tập dịch vụ `is_paraclinical` = 1 trong số dịch vụ trên dòng):

| Điều kiện | Kết quả |
| :-- | :-- |
| Thiếu trường bắt buộc; `services` rỗng | từ chối, nêu trường (TC-CLS-24) |
| Số ngoài miền | từ chối (ASM-032-02) |
| Dịch vụ lặp; dịch vụ chưa đánh dấu cận lâm sàng | từ chối (ASM-032-04) |
| `share_pct` < 0 hoặc > 100 ở một dòng | từ chối |
| Một số dòng có `share_pct` > 0, một số trống/0 | từ chối: "Tỷ lệ riêng phải nhập ở mọi dòng hoặc để trống ở mọi dòng" (DI-12) |
| Mọi dòng có `share_pct` > 0 và tổng (Decimal, 2 chữ số) ≠ 100 | từ chối: "Tổng tỷ lệ riêng của các dịch vụ là 90%, phải bằng 100%" (FR-QC-005, TC-CLS-25) |
| Mọi dòng trống/0 | hợp lệ: chia đều (BR-CLS-008 mặc định) |

`share_pct` = 0 được coi là trống (Frappe lưu Percent trống thành 0; ASM-032-03).

### 2.3 Quyền

Dòng ma trận "Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm": `W W - R R - R R R R` (Clinician W khoa, Dept Head W khoa, Council —, Finance R, Resource Mgr R, Doc Controller —, Director R, Consultant R, Admin R, Auditor R) cho NC QC Plan và NC EQA Program. Không vai trò nào có quyền xóa (cùng ASM-113 của NC Test System; ASM-032-01): bỏ dòng trong bảng con, không xóa bản ghi. `scripts/check_conventions.py`: thêm `DOCTYPE_ROW["NC QC Plan"]`, `DOCTYPE_ROW["NC EQA Program"]` trỏ dòng ma trận đã có. `tests/test_permissions.py` so tập DocType theo thư mục (ASM-NORM32-01) nên không cần đổi số đếm.

### 2.4 Phạm vi khoa (FR-ACC-008)

- NC EQA Program: `SCOPE_RULES["NC EQA Program"] = ScopeRule()` (trường `department`).
- NC QC Plan không có trường khoa (data-model): mở rộng `ScopeRule` thêm trường tùy chọn `via: tuple | None = None` = `(link_field, link_doctype)`. Khi có `via`, khoa của bản ghi = `frappe.db.get_value(link_doctype, doc.get(link_field), department_field)`; `permission_query_conditions` sinh `` `tabNC QC Plan`.`test_system` in (select name from `tabNC Test System` where `department` in (…)) ``. Khai `SCOPE_RULES["NC QC Plan"] = ScopeRule(via=("test_system", "NC Test System"))`. Quy tắc cũ không đổi khi `via` = None. Không đổi `test_system` của kế hoạch đã lưu (`set_only_once`) nên không cần kiểm "khoa cũ".
- `hooks.py`: thêm hai DocType vào `permission_query_conditions` và `has_permission`.

### 2.5 Patch

Không viết patch (ASM-032-09): chỉ thêm DocType mới; NC Test System, NC Item không đổi cấu trúc.

## 3. API whitelisted — `normcore/api/qc_plan.py`

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `estimate_tests(plan)` | `plan`: JSON `{run_days_per_year, iqc_lines: [{levels, runs_per_day}], calibration_lines: [{points, replicates, calibrations_per_year}]}` (từ form chưa lưu) | `{"iqc_tests": float, "calibration_tests": float, "complete": bool}`; `complete` = False khi thiếu số (dòng thiếu số được bỏ qua) | `frappe.has_permission("NC QC Plan", "read", throw=True)`; không đọc CSDL |
| `missing_iqc_warning(test_system)` | mã hệ thống | `{"warning": bool, "message": str \| null}` | `frappe.has_permission("NC Test System", "read", doc, throw=True)`. Hàm này để FEAT-034 gọi khi hiện bộ định mức |
| `eqa_summary(program)` | JSON phần đầu + `services` (form chưa lưu) | `{"samples_per_year", "mode": "equal" \| "custom" \| "invalid", "shares": [{"technical_service", "share_pct"}], "total_pct", "message"}` | `frappe.has_permission("NC EQA Program", "read", throw=True)`; không đọc CSDL |

Khối tình trạng NC Test System (`api/test_system.py::get_status`): thẻ `qc_plan` lấy từ `test_systems.status_items(qc_plan=…)` (mục 4); khi chưa có kế hoạch trả đúng như cũ (`state` "empty", "Chưa có"), danh sách `warnings` không đổi (test FEAT-031 giữ nguyên).

## 4. Logic thuần (không import `frappe`)

### `normcore/costing/qc_plans.py` (mới, phủ ≥ 90%)

| Hàm | Việc | Căn cứ |
| :-- | :-- | :-- |
| `validate_qc_plan(values, item_types) -> list[str]` | Lỗi theo bảng 2.1; `item_types` = `{item_code: item_type}` | FR-QC-001, FR-QC-002, FR-QC-008, DI-16 |
| `validate_eqa_program(values, paraclinical_services) -> list[str]` | Lỗi theo bảng 2.2 | FR-QC-003, FR-QC-005, DI-12 |
| `eqa_shares(rows) -> list[Decimal]` | Tỷ lệ hiệu lực dạng phân số: mọi dòng trống → `1 / n` mỗi dòng; có tỷ lệ → `share_pct / 100`. Gọi trên chương trình hợp lệ | BR-CLS-008 ("tỷ lệ mặc định = 1 ÷ số dịch vụ"); không nhân phí (FEAT-036) |
| `estimated_tests(plan) -> (iqc, calibration)` | `iqc` = Σ `levels × runs_per_day × run_days_per_year`; `calibration` = Σ `calibrations_per_year × points × replicates` | `golden_cls.py` dòng 154–155 (`k_factor`, nhánh ước tính); FR-QC-006 dùng ở FEAT-036 |
| `eqa_samples_per_year(rounds, samples)` | `rounds × samples` | `golden_cls.py` dòng 156 |
| `LAB_GROUPS` | `("Hóa sinh", "Miễn dịch", "Huyết học", "Vi sinh", "Giải phẫu bệnh")` | ASM-032-05 |
| `missing_iqc_warning(cls_group, plan) -> str \| None` | Nhóm thuộc `LAB_GROUPS` và (không có kế hoạch hoặc kế hoạch không có dòng nội kiểm) → "Hệ thống <mã> chưa có kế hoạch nội kiểm"; ngược lại None. Không bao giờ ném lỗi (không chặn khóa) | FR-QC-007, TC-CLS-26 |
| `plan_status_item(plan) -> dict` | Thẻ `qc_plan`: có kế hoạch → `state` "ok", "Có — <n> dòng nội kiểm, <m> dòng chuẩn máy"; có kế hoạch, nhóm xét nghiệm, 0 dòng nội kiểm → `state` "warning", "Thiếu nội kiểm" | FR-CLS-007, ASM-032-08 |

Số dùng `Decimal(str(x))`. Không có phép tính tiền. Golden dùng `D`, `runs` = 1, `qty` = 0,2 (Float trong DocType, đổi Decimal qua `str`).

### `normcore/costing/test_systems.py` (đổi nhỏ)

`status_items(qc_plan=None)`: thêm tham số tùy chọn; `None` → bốn mục như cũ (test đơn vị FEAT-031 gọi không tham số vẫn đúng); có giá trị → thay mục `qc_plan` bằng `qc_plans.plan_status_item(qc_plan)`. Thứ tự và khóa không đổi.

### `normcore/core/permissions.py` (đổi nhỏ)

`ScopeRule.via` và hàm nội bộ `_doc_department(rule, doc)` như mục 2.4. Test cũ của phạm vi khoa (`tests/test_feat_001.py`, test NC Test System) phải xanh không sửa.

## 5. Bộ nhập `nc_qc_plan` (FR-CLS-008, phần kế hoạch chất lượng)

```python
NC_QC_PLAN = ImportSet(
    key="nc_qc_plan", label="Kế hoạch chất lượng", doctype="NC QC Plan", key_field="test_system",
    columns=(
        Column("test_system", "Mã hệ thống xét nghiệm", "Link", link_doctype="NC Test System", required=True, example="GLU-A"),
        Column("run_days_per_year", "Số ngày chạy mỗi năm", "Int", required=True, example=300),
    ),
)
```

Khung FEAT-004 chỉ nhập trường phẳng: bảng nội kiểm, chuẩn máy khai trên form (ASM-032-07). Dev kiểm `lookup`/`write` của `api/importer.py` tìm bản ghi theo `key_field` (không theo `name`); nếu khung chỉ tìm theo `name` thì dừng và báo Lead, không sửa khung. Mã hệ thống lạ → lỗi dòng của khung; hệ thống của khoa không được gán → lỗi dòng (quyền ghi). Chỉ Clinician, Dept Head (và Administrator) thấy bộ này.

## 6. Tiêu chí nghiệm thu

Dữ liệu (`test-cases.md` "Kế hoạch chất lượng", `golden_cls.py` `IQC`, `CAL`, `EQA`): khoa HS-CLS (Hóa sinh), GLU, GLU-A (`make_cls_data`, `make_test_system`); NC Item QC_L (Vật liệu nội kiểm), HC_GLU (Hóa chất) theo bảng mặt hàng của `test-cases.md`; CAL (Chất chuẩn) — mã của `golden_cls.py` dòng 185, `test-cases.md` không đặt mã mặt hàng cho chất chuẩn nên test tự tạo; kế hoạch GLU-A: D = 300; nội kiểm QC_L 2 mức, 1 lần/ngày, 0,2, 20 thông số; chuẩn máy CAL 2 điểm, 2 lần lặp, 12 lần/năm, 400.000; chương trình EQA-HS: phí 24.000.000, vận chuyển 1.200.000, 3 đợt × 4 mẫu.

| # | Điều kiện kiểm được | TC | FR | Vị trí test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Kế hoạch GLU-A đủ trường lưu được, tên `KHCL-GLU-A`. Bỏ lần lượt `run_days_per_year` và từng trường của dòng nội kiểm (`qc_material`, `levels`, `runs_per_day`, `qty_per_run`, `shared_parameter_count`) → mỗi lần `frappe.ValidationError` (hoặc `MandatoryError`) nêu đúng trường; điền lại → lưu được | TC-CLS-24 | FR-QC-001 | `nc_qc_plan/test_nc_qc_plan.py` |
| 2 | Như trên với từng trường dòng chuẩn máy (`calibrator`, `points`, `replicates`, `calibrations_per_year`, `cost_per_calibration`) | TC-CLS-24 | FR-QC-002 | `test_nc_qc_plan.py` |
| 3 | EQA-HS đủ trường lưu được; bỏ lần lượt `eqa_code`, `program_name`, `provider`, `department`, `rounds_per_year`, `samples_per_round`, `annual_fee`, bảng `services` → từ chối nêu trường; `annual_shipping_fee` trống lưu được (= 0) | TC-CLS-24 | FR-QC-003 | `nc_eqa_program/test_nc_eqa_program.py` |
| 4 | Dòng nội kiểm `qc_material` = HC_GLU → `ValidationError` nêu "HC_GLU" và "Vật liệu nội kiểm"; dòng chuẩn máy `calibrator` = QC_L → từ chối nêu "Chất chuẩn"; QC_L / CAL đúng loại → lưu được | TC-CLS-25 | FR-QC-008 | `test_nc_qc_plan.py` |
| 5 | EQA hai dịch vụ GLU 50%, dịch vụ thứ hai 40% → `ValidationError` nêu "90" và "100"; 60 + 40 → lưu được; cả hai trống → lưu được, `eqa_shares` = [0,5; 0,5]; 50 và trống → từ chối (DI-12) | TC-CLS-25 | FR-QC-005 | `test_nc_eqa_program.py` |
| 6 | `missing_iqc_warning("Hóa sinh", None)` và với kế hoạch 0 dòng nội kiểm → có thông báo; có dòng nội kiểm → None; nhóm "Chẩn đoán hình ảnh" không kế hoạch → None. API `missing_iqc_warning("GLU-A")` không có kế hoạch → `warning` True; tạo kế hoạch có QC_L → False. Hàm không ném lỗi (không chặn khóa; phần "khóa được bộ định mức" kiểm lại ở FEAT-034, ASM-032-05) | TC-CLS-26 | FR-QC-007 | `tests/unit/test_qc_plans.py`, `api/test_qc_plan.py` |
| 7 | Tạo kế hoạch thứ hai cho GLU-A → từ chối nêu `KHCL-GLU-A` (DI-11); đổi `test_system` của kế hoạch đã lưu → không được | — | FR-QC-001 | `test_nc_qc_plan.py` |
| 8 | Phạm vi khoa: Clinician khoa khác không đọc, không tạo, không sửa kế hoạch của GLU-A và EQA-HS (`PermissionError`; `frappe.get_list` không trả bản ghi); Clinician khoa HS-CLS tạo, sửa được | — | FR-ACC-008 | `test_nc_qc_plan.py`, `test_nc_eqa_program.py` |
| 9 | Quyền khớp ma trận cho 10 vai trò; không ai xóa; NC Auditor đọc được, tạo/sửa bị từ chối; Doc Controller (không có quyền) đọc bị từ chối; `check_conventions.py` thoát 0 | — | FR-ACC-002, FR-ACC-007 | hai tệp test DocType, `tests/test_permissions.py` |
| 10 | `estimated_tests` với dữ liệu golden = (600, 48); `eqa_samples_per_year(3, 4)` = 12 — bằng số golden tính ở nhánh ước tính của `k_factor` (GLU-B, không có số thực tế) lấy từ `golden_cls.IQC`, `CAL`, `EQA`, `SYSTEMS["GLU-B"]["run_days"]`, và trùng số thực tế 600, 48, 12 của GLU-A trong `test-cases.md` | — | FR-QC-001, FR-QC-002 | `tests/golden/test_qc_plans_golden.py` |
| 11 | `get_status("GLU-A")`: chưa có kế hoạch → thẻ `qc_plan` "empty"/"Chưa có", `warnings` như cũ; có kế hoạch 1 dòng nội kiểm, 1 dòng chuẩn máy → `state` "ok", message có "1 dòng nội kiểm" | — | FR-CLS-007 | `api/test_qc_plan.py` |
| 12 | Nhập tệp mẫu 2 dòng (GLU-A, GLU-X lạ) → `created` = 1, lỗi dòng nêu "Mã hệ thống xét nghiệm"; nhập lại đổi D → `updated` = 1, dòng nội kiểm giữ nguyên | — | FR-CLS-008 | `api/test_importer_qc_plan.py` |
| 13 | Hàm thuần phủ mọi nhánh `qc_plans.py`; `test_systems.status_items()` không tham số giữ hành vi cũ | — | FR-QC-001..008 | `tests/unit/test_qc_plans.py` |

Mọi test FEAT-031 (`api/test_test_system.py`, `tests/unit/test_test_systems.py`) và FEAT-001 (phạm vi khoa) xanh, không sửa.

## 7. Giả định và rủi ro

Giả định mới ở `docs/decisions/assumptions/FEAT-032.md` (ASM-NORM32-02):

| Mã | Tóm tắt |
| :-- | :-- |
| ASM-032-01 | Quyền NC QC Plan, NC EQA Program theo dòng ma trận chung; không ai xóa; phạm vi khoa của kế hoạch qua hệ thống xét nghiệm (`ScopeRule.via`) |
| ASM-032-02 | Miền giá trị các trường số; vật liệu / chất chuẩn / dịch vụ không lặp trong một bản ghi |
| ASM-032-03 | DI-12: `share_pct` 0 = trống; tổng so đúng 100,00; không làm tròn bù |
| ASM-032-04 | Dịch vụ tham gia ngoại kiểm phải là dịch vụ cận lâm sàng; không ràng dịch vụ với khoa của chương trình |
| ASM-032-05 | Nhóm "chuyên ngành xét nghiệm" = Hóa sinh, Miễn dịch, Huyết học, Vi sinh, Giải phẫu bệnh; "không có kế hoạch nội kiểm" = không có NC QC Plan hoặc có nhưng 0 dòng nội kiểm; gắn vào bộ định mức ở FEAT-034 |
| ASM-032-06 | Autoname `format:KHCL-{test_system}`; `test_system` duy nhất và không đổi sau khi lưu |
| ASM-032-07 | Bộ nhập `nc_qc_plan` chỉ phần đầu kế hoạch; bảng con khai trên form; không nhập chương trình ngoại kiểm; không sửa khung FEAT-004 |
| ASM-032-08 | Thẻ `qc_plan` của khối tình trạng: "ok"/"warning" khi có kế hoạch, giữ "empty" khi chưa có; không thêm mã cảnh báo vào `get_status.warnings` |
| ASM-032-09 | Không viết patch |
| ASM-032-10 | Số test ước tính trên SCR-DSK-033, SCR-DSK-034 lấy đúng nhánh ước tính của `golden_cls.k_factor` (chỉ hiển thị; FEAT-036 dùng cho FR-QC-006) |

Rủi ro:
- `ScopeRule.via` sửa tệp chung `core/permissions.py`: thay đổi chỉ thêm, mặc định giữ hành vi cũ; chạy lại toàn bộ test phạm vi khoa.
- Frappe kiểm `reqd` trước `validate`: thiếu trường có thể ra `MandatoryError` (lớp con của `ValidationError`) với thông báo chuẩn của Frappe; test bắt `frappe.ValidationError` và kiểm tên trường có trong thông báo.
- Trùng tên với nhánh khác (`check_conventions.py`, `hooks.py`, `vi.csv`, `shortcuts.txt`): giữ dòng cả hai bên (CLAUDE.md mục 11).
- FEAT-034 phải gọi `missing_iqc_warning` khi hiện bộ định mức có `test_system` và thêm test "vẫn khóa được" (TC-CLS-26 đầy đủ).
