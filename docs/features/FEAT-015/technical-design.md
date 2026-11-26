# FEAT-015 — Tính chi phí trực tiếp, giá và bảng giải trình — Thiết kế kỹ thuật

Issue NORM-41. Nguồn: `srs.md` FR-COST-001..003, 006, 007, 010, 015, 016; BR-COST-001..007, 012..014, 016; NFR-CPL-001, NFR-REL-002; `use-cases.md` UC-012 (bước 1–4, 6; 2a, 4a, 4c, 4d); `data-model.md` 3.x (NC Costing Run, NC Service Cost, NC Service Cost Line), mục 4 (dòng "Lần tính giá, kết quả, đối soát" và "Bảng giải trình của dịch vụ thuộc khoa"), 5.4; `architecture.md` ADR-003, ADR-017, mục 6.2; `ux-foundations.md` SCR-DSK-022, SCR-DSK-023; golden `docs/golden/golden_engine.py` (`job_rate`, `equip_rate`, `room_rate`, `applied_qty`, `direct_lines`, `run`); `test-cases.md` mục 2.1–2.3, TC-COST-01, 04, 06, 07, 12, 13, 15, 17, 19.

Phụ thuộc (DONE trên `origin/develop`): FEAT-012 (NC Norm Set "Đã khóa", `engine.applied_qty`, `costing/provisional.py::line_amount`). Dùng lại: FEAT-000 (khung NC Costing Run, NC Service Cost, `engine.py`), FEAT-009 (`costing/pricing.py`), FEAT-010 (`costing/resources.py`, `NCEquipment.indicative`), FEAT-011 (NC Costing Parameter Set, NC Job Title Rate, NC Price Category), FEAT-016 (NC Accounting Import "Đã chốt", NC Service Volume, NC Allocation Rule), FEAT-031 (`costing/test_systems.py`).

Giả định: `docs/decisions/assumptions/FEAT-015.md` (ASM-015-01..20). Sửa thiết kế: `docs/decisions/amendments/AMD-015-01.md` (hai bảng con phạm vi), `AMD-015-02.md` (loader/writer cạnh controller, CF-015-01). **Câu hỏi cho Lead: mục 10 (Q1, Q2)** — T02 chờ Q1, T08 chờ Q2; các task khác làm được trước.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-COST-001 | NC Costing Run bắt buộc năm tài chính, ngày tính giá, bộ tham số, **lần nhập kế toán "Đã chốt"**, **loại giá**; phạm vi khoa, dịch vụ (Table MultiSelect, trống = toàn viện). Kiểm ở `validate` (mọi đường ghi). Tạo mới ở "Nháp" |
| FR-COST-002 | `check_scope` liệt kê cặp (dịch vụ, khoa) trong phạm vi chưa có bộ định mức "Đã khóa"; `run_costing` từ chối khi chưa xác nhận, sau xác nhận chỉ tính cặp đủ điều kiện (ASM-015-03, 04) |
| FR-COST-003 | Chi phí trực tiếp từng dòng không loại trừ, đủ 6 cấu phần: LABOR (BR-COST-001, 002), DRUG/SUPPLY (003), EQUIPMENT (004), INFRA (005), UTILITY (006), lượng áp dụng BR-COST-007 |
| FR-COST-006 | Mỗi dịch vụ: giá thành toàn bộ (BR-COST-012 = trực tiếp + phân bổ cấp 2 do điểm cắm `allocate` trả), tích lũy, nghĩa vụ tài chính (BR-COST-013, `apply_accumulation` có sẵn), giá tính toán, giá làm tròn (BR-COST-014) |
| FR-COST-007 | Loại giá `include_depreciation` = 0: khấu hao thiết bị = 0 (đơn giá giờ máy chỉ còn bảo trì, kiểm định), đơn giá giờ phòng = 0; dòng EQUIPMENT, INFRA ghi `warning` "Khấu hao bị loại (loại giá không kết cấu khấu hao)"; bảng giải trình có dải ghi rõ. Phần "DEPRECIATION không phân bổ cấp 2, không đối soát" của BR-COST-016 là FEAT-017 |
| FR-COST-010 | NC Service Cost Line đủ trường data-model (gồm `allocation_rule`, `driver_value`, `driver_total`, `pool_amount`, `warning`); `get_explanation` và form NC Service Cost (SCR-DSK-023) hiện dòng nhóm theo cấu phần và bước kèm nguồn |
| FR-COST-015 (Should) | > 50 cặp đủ điều kiện → tác vụ nền hàng đợi `long`, `progress` và realtime (ASM-015-12) |
| FR-COST-016 | Dòng thiếu đơn giá hiệu lực tại `costing_date` → dịch vụ đó "Lỗi", `calc_message` nêu mọi dòng thiếu, các dịch vụ khác vẫn tính (ASM-015-08) |

**Không làm** (FEAT khác): phân bổ cấp 1, cấp 2, đối soát, cảnh báo sản lượng 0 (FR-COST-004, 005, 008, 009, 014 — FEAT-017; FEAT-015 dựng điểm cắm `allocate` và chỗ chứa dòng "Phân bổ"); khóa, ảnh chụp, tính lại từ ảnh chụp, nhân bản, so sánh hai lần tính (FR-COST-011..013 — FEAT-018); kịch bản sản lượng, cách phân bổ kiểm định và mọi trường **[1.1]** của ba DocType (`volume_scenario`, `compliance_allocation_mode`, `is_paraclinical`, `eqa_cost`, `test_system_costs`, `test_system`, `line_origin`, `cost_level`, `k_factor`, `divisor_*` — FEAT-036 qua `cls.py`); `based_on_run`, `scenario_changes`, `snapshot_*` (FEAT-018, FEAT-029); hiệu năng 500 dịch vụ (TC-COST-14, NFR-PERF-002 — FEAT-017, nhưng thiết kế nạp theo lô ở mục 4.4 để không cản).

## 2. DocType (module NC Costing — mở rộng, không tạo lại; chỉ thêm trường → không cần patch dữ liệu)

### 2.1 NC Costing Run (đã có từ FEAT-000)
`track_changes` = 1 (giữ). Naming giữ `TG-.YYYY.-.###`. Thứ tự trường:

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| title, fiscal_year, costing_date, parameter_set | (đã có) | | Có | |
| accounting_import **(mới)** | Lần nhập kế toán | Link NC Accounting Import | Có | `validate`: status phải "Đã chốt", nếu không → "Lần nhập kế toán {0} chưa chốt" (ASM-015-10). Form lọc `status = Đã chốt` |
| price_category **(mới)** | Loại giá | Link NC Price Category | Có | Có liên kết thật tới NC Price Category → móc chặn xóa của FEAT-011 kiểm được |
| scope_departments **(mới)** | Phạm vi khoa | Table MultiSelect NC Costing Run Department | | Trống = toàn viện (AMD-015-01) |
| scope_services **(mới)** | Phạm vi dịch vụ | Table MultiSelect NC Costing Run Service | | (AMD-015-01) |
| status | Trạng thái | Select | Có | Đã có; Nháp / Đang tính / Đã tính / Tính lỗi / Đã khóa; chỉ đọc trên form, chỉ đổi bằng mã máy chủ |
| progress **(mới)** | Tiến độ (%) | Percent | | Chỉ đọc |

`validate` (mọi đường ghi, kể cả `frappe.client`): (a) bắt buộc như trên (JSON `reqd` + thông báo tiếng Việt); (b) lần nhập "Đã chốt"; (c) bản ghi đã có mà status không thuộc {Nháp, Tính lỗi} thì không được đổi các trường đầu vào (`fiscal_year`, `costing_date`, `parameter_set`, `accounting_import`, `price_category`, hai bảng phạm vi) — "Lần tính giá ở trạng thái {0}, không sửa được đầu vào" (ASM-015-11); (d) bản ghi mới luôn bắt đầu "Nháp" khi người dùng tạo (giữ hành vi test cũ dựng sẵn trạng thái bằng `insert(ignore_permissions)` — chỉ đặt "Nháp" khi `status` trống).

### 2.2 NC Costing Run Department, NC Costing Run Service (mới, bảng con — AMD-015-01)
Mỗi bảng một trường Link (`department` → NC Department; `technical_service` → NC Technical Service), BB, `in_list_view`. Quyền theo cha.

### 2.3 NC Service Cost (đã có)
`track_changes` = 1. Thêm trường (Currency trừ khi ghi khác), mọi trường chỉ đọc trên form (do `writer` ghi):

| Trường | Nhãn | Ghi chú |
| :-- | :-- | :-- |
| costing_run, technical_service, department, norm_set, calc_status, calc_message, direct_labor, lines | (đã có) | |
| volume | Sản lượng | Float (ASM-015-13) |
| direct_drug, direct_supply, direct_equipment, direct_infra, direct_utility | Chi phí trực tiếp: thuốc, vật tư, thiết bị, hạ tầng, tiện ích | Tổng `amount` dòng trực tiếp theo cấu phần |
| alloc_labor, alloc_drug_supply, alloc_depreciation, alloc_utility, alloc_management | Phân bổ: nhân công, thuốc và vật tư, khấu hao, tiện ích, quản lý | Tổng dòng "Phân bổ" theo loại; FEAT-015 = 0 (ASM-015-02) |
| direct_total **— không thêm** | | Không có trong data-model; tính khi hiển thị = tổng sáu `direct_*` |
| full_cost | Giá thành toàn bộ | BR-COST-012 |
| accumulation | Tích lũy | BR-COST-013 |
| obligation | Nghĩa vụ tài chính | BR-COST-013 |
| calculated_price | Giá tính toán | BR-COST-013 |
| rounded_price | Giá làm tròn | BR-COST-014 |

Dịch vụ "Lỗi": mọi trường số để trống (0), không có dòng (giữ test G5). Quyền: **chờ Q2** (mục 10).

### 2.4 NC Service Cost Line (đã có, bảng con)
Thêm: `allocation_rule` (Link NC Allocation Rule), `driver_value` (Float), `driver_total` (Float), `pool_amount` (Currency), `warning` (Data). Giữ `unit_rate` Float `precision` 4. `line_type` giữ "Trực tiếp" / "Phân bổ".

| Loại dòng | Trường phải có (NFR-CPL-001, TC-COST-15) |
| :-- | :-- |
| Trực tiếp | `component`, `step_id` (trống = dòng chung, ASM-015-06), `norm_line_id`, `resource_label`, `applied_qty`, `unit_rate`, `amount`, `rate_source`; `warning` khi có |
| Phân bổ (FEAT-017 tạo; FEAT-015 ghi được) | `component` = loại chi phí, `allocation_rule`, `driver_value`, `driver_total`, `pool_amount`, `amount` |

## 3. API (`normcore/api/costing.py`, `@frappe.whitelist()`, kiểm quyền tường minh)

| Hàm | Tham số | Kết quả | Quyền, lỗi |
| :-- | :-- | :-- | :-- |
| `check_scope(run)` | tên lần tính | `{"eligible": [{service, service_name, department, department_name, norm_set}], "ineligible": [{service, service_name, department, department_name}], "background": bool}` | `has_permission("NC Costing Run", "write", doc)`; thứ tự sắp theo (dịch vụ, khoa) |
| `start_costing(run, confirm_ineligible=0)` | | `{"status", "enqueued": bool, "skipped": n}` | Như trên. Gọi `NCCostingRun.run_costing(confirm_ineligible)` |
| `get_progress(run)` | | `{"status", "progress"}` | `read` |
| `get_run_results(run)` | | danh sách `{name, service, service_name, department, calc_status, calc_message, full_cost, calculated_price, rounded_price, has_allocation}` + đếm theo `calc_status` | `read` trên NC Costing Run; chỉ trả NC Service Cost người dùng đọc được (`frappe.get_list`) |
| `get_explanation(service_cost)` | | mục 4.5 | `read` trên NC Service Cost (gồm phạm vi khoa nếu Q2 = PA1) |

Doc method `NCCostingRun.run_costing(confirm_ineligible=0)` (giữ tên, nút cũ và test cũ dùng): kiểm `write`; status ∉ {Nháp, Tính lỗi, Đã tính} → "Chỉ chạy được lần tính giá ở trạng thái Nháp, Tính lỗi hoặc Đã tính"; tính phạm vi; có cặp chưa đủ điều kiện mà `confirm_ineligible` falsy → `frappe.throw` nêu danh sách (không đổi gì); số cặp đủ điều kiện > 50 → đặt "Đang tính", `progress` 0, `frappe.enqueue("normcore.nc_costing.doctype.nc_costing_run.nc_costing_run.execute_costing", queue="long", timeout=1500, run=name, eligible=…, enqueue_after_commit=True)`, trả "Đang tính"; ngược lại chạy `execute_costing` ngay. `execute_costing`: pha tính (loader → `runner.run`), pha ghi (savepoint, xóa NC Service Cost cũ của lần tính, `writer`), đặt "Đã tính", `progress` 100; ngoại lệ → rollback savepoint, `frappe.log_error`, "Tính lỗi" (giữ cách FEAT-000). Trạng thái đổi bằng `db_set` → `core/audit.py` ghi sự kiện như cũ.

## 4. Logic thuần (`normcore/costing/`, không import `frappe`, Decimal, ROUND_HALF_UP)

### 4.1 `engine.py` (mở rộng; giữ nguyên `apply_accumulation`, `job_rate`, `applied_qty`, `labor_line`, `LaborLine`, `compute_direct_lines`, `DirectLineExtension`)

```python
COMPONENT_CATEGORY = {"LABOR": "LABOR", "DRUG": "DRUG_SUPPLY", "SUPPLY": "DRUG_SUPPLY",
                      "EQUIPMENT": "DEPRECIATION", "INFRA": "DEPRECIATION", "UTILITY": "UTILITY"}  # = golden CATEGORY
DEPR_EXCLUDED_WARNING = "Khấu hao bị loại (loại giá không kết cấu khấu hao)"

@dataclass(frozen=True) class NormLine:   # một dòng của bộ định mức đã khóa
    line_id: str; step_id: str; component: str; resource: str; resource_label: str
    hospital_qty: Decimal; authority_qty: Decimal | None = None; headcount: int = 1
    wastage_rate: Decimal = 0  # phân số (Percent ÷ 100)
    excluded: bool = False; exclude_reason: str | None = None

@dataclass(frozen=True) class LineRate:   # do rates.py dựng từ dữ liệu đã nạp
    rate: Decimal; source: str; reuse_count: int = 1; warnings: tuple = ()
    billed_separately: bool = False

@dataclass(frozen=True) class CostLine:   # một dòng bảng giải trình
    line_type: str; component: str; amount: Decimal
    step_id: str = ""; norm_line_id: str = ""; resource_label: str = ""
    applied_qty: Decimal | None = None; unit_rate: Decimal | None = None
    rate_source: str = ""; warning: str = ""
    allocation_rule: str | None = None; driver_value: Decimal | None = None
    driver_total: Decimal | None = None; pool_amount: Decimal | None = None

@dataclass(frozen=True) class ServiceInput: service: str; department: str; norm_set: str
    lines: tuple[NormLine, ...]; rates: Mapping[str, LineRate | None]  # khóa line_id; None = thiếu đơn giá
    volume: Decimal | None = None

@dataclass(frozen=True) class PricingParams:
    accumulation_mode: str | None; accumulation_rate: Decimal; obligation_rate: Decimal
    rounding_unit: Decimal; include_depreciation: bool
    @classmethod from_values(param_set: dict, price_category: dict)  # ASM-015-09: Percent ÷ 100; NONE / include_accumulation 0 → None

@dataclass(frozen=True) class PriceResult: full_cost; accumulation; obligation; calculated_price; rounded_price
@dataclass(frozen=True) class ServiceResult: service; department; norm_set; status; message
    lines: tuple[CostLine, ...]; direct_by_component: dict; direct_by_category: dict; direct_total: Decimal
    alloc_by_category: dict; price: PriceResult | None; volume
```

| Hàm | Quy tắc | Golden |
| :-- | :-- | :-- |
| `direct_line(line, rate) -> CostLine` | Loại trừ → qty 0, rate 0, amount 0, `rate_source` "Loại trừ: <lý do>" (ASM-015-07). Còn lại: `q = applied_qty(hospital, authority)`; `amount = provisional.line_amount(component, q, rate.rate, headcount, wastage_rate, reuse_count)` (BR-COST-002..006, đã khớp golden ở FEAT-012); `billed_separately` → amount 0, warning `pricing.EXCLUDED_REASON`; `warning` = "; ".join(rate.warnings) | `direct_lines` |
| `round_price(calc, unit) -> Decimal` | `(calc / unit).quantize(1, ROUND_HALF_UP) * unit`; `unit` ≤ 0 → ValueError | dòng 152 |
| `price_service(direct_total, alloc_by_category, params) -> PriceResult` | `full = direct_total + Σ alloc` (BR-COST-012); `apply_accumulation(full, mode, rate, obl)`; `rounded = round_price(calc, unit)` | dòng 147–152 |
| `cost_service(inp, params, extension=None) -> ServiceResult` (chưa giá) | `extension(inp)` (điểm cắm ADR-017 cho `cls.py`, kiểu `DirectServiceExtension = Callable[[ServiceInput], list[CostLine] \| None]`) trả None → tính mặc định từng dòng theo thứ tự `line_id`; có dòng `rates[line_id] is None` (không loại trừ) → `status` "Lỗi", `message` "Dòng thiếu đơn giá: L05 (THUOCX), …", `lines` = () (FR-COST-016); có cảnh báo `pricing.STALE_WARNING`/`UNVERIFIED_WARNING` → "Cảnh báo"; tổng theo cấu phần và theo loại (`COMPONENT_CATEGORY`) | `run` (by_cat) |
| `finish_service(result, alloc_lines, params) -> ServiceResult` | Gộp dòng "Phân bổ" (tổng theo `component`), gọi `price_service`; dịch vụ "Lỗi" không có giá | |

### 4.2 `rates.py` (mới) — dựng `LineRate` từ dữ liệu đã nạp, không import `frappe`

| Hàm | Quy tắc |
| :-- | :-- |
| `labor_rate(hourly_rate, source)` | `hourly_rate` = `NC Job Title Rate.rate_per_hour` của bộ tham số (đã là `job_rate().hourly_rate`, BR-COST-001); None → None |
| `material_rate(prices, as_of, norm_units, item_type, reuse_count, billed_separately, labels)` | `billed_separately` → `LineRate(0, EXCLUDED_REASON, billed_separately=True)`; `pricing.select_price(prices, as_of)` None → None; `norm_units` trống và `item_type` ∉ `pricing.NORM_ITEM_TYPES` → 1 (như FEAT-012), trống ở loại định mức → None; `rate = unit_price_per_norm(...)`; `warnings = price_warnings(price, as_of)`; `source = labels[price.name]` |
| `utility_rate(uom, electricity_price, water_price, param_name, material)` | ASM-015-05 |
| `room_rate(annual_cost, hours, include_depr, source)` | `include_depr` False → `LineRate(0, source, warnings=(DEPR_EXCLUDED_WARNING,))`; còn lại `resources.room_hourly_rate` |
| `equipment_rate(hourly_rate, include_depr, is_buy, source)` | `hourly_rate` None → None; `include_depr` False và hình thức Mua → thêm `DEPR_EXCLUDED_WARNING` |

### 4.3 `runner.py` (mới) — điều phối thuần, nhận hàm qua tham số

```python
BACKGROUND_THRESHOLD = 50
def scope_pairs(services, scope_services, scope_departments) -> list[tuple[str, str]]   # ASM-015-03
def eligibility(pairs, locked_norm_sets, scope_services, scope_departments) -> (eligible: list[dict], ineligible: list[tuple])
def needs_background(n_eligible) -> bool        # n > 50
def run(eligible, load: Callable[[dict], ServiceInput], params: PricingParams,
        progress: Callable[[int, int], None] = None,
        extension: DirectServiceExtension | None = None,
        allocate: Callable[[list[ServiceResult]], Mapping[tuple, list[CostLine]]] | None = None) -> list[ServiceResult]
```
`run`: sắp `eligible` theo (dịch vụ, khoa); với mỗi cặp `load` → `cost_service`, gọi `progress(i, n)`; sau cùng `allocate(results)` (None → {}) → `finish_service` từng dịch vụ. Tất định (NFR-REL-002).

### 4.4 Lớp chạm CSDL (cạnh controller, AMD-015-02)
- `loader.py`: `load_context(run)` đọc một lần: bộ tham số (+ `job_title_rates`), loại giá, `NC Item`, `NC Item Price` của mọi mặt hàng xuất hiện trong các bộ đủ điều kiện (một truy vấn theo danh sách), `NC Equipment` (gọi `indicative(costing_date, expired_mode, include_depr)`, ASM-015-15), `NC Room`, `NC Service Volume` của năm; `load_service(ctx, norm_set_row) -> ServiceInput` dựng `NormLine` (Float → `Decimal(str())`, `authority_qty` 0 = không có — ASM-013, `wastage_rate` ÷ 100) và `rates` qua `rates.py`; nhãn nguồn theo ASM-015-16; `resource_label` = tên hiển thị của nguồn lực.
- `writer.py`: `write_results(run, results)` tạo NC Service Cost (`insert(ignore_permissions=True)` — kết quả do máy chủ ghi, quyền đã kiểm ở `run_costing`), các trường mục 2.3, dòng mục 2.4.
- `NCEquipment.indicative(on, expired_mode, include_depr=True)`: thêm tham số cuối, truyền xuống `resources.machine_annual(..., include_depr=include_depr)`; mặc định giữ kết quả cũ.

### 4.5 `get_explanation` (SCR-DSK-023)
Trả `{"header": {service, service_name, department, costing_run, run_status, calc_status, calc_message, volume, price_category, include_depreciation, direct_total, alloc_total, full_cost, accumulation, obligation, calculated_price, rounded_price, has_allocation}, "structure": [{component, label, amount, share_pct}], "direct_groups": [{component, label, total, steps: [{step_id | "", step_label, total, lines: [...]}]}], "allocation_lines": [...], "notes": [...]}`. `notes` gồm "Khấu hao bị loại…" khi loại giá `include_depreciation` = 0 (FR-COST-007), "Chưa gồm chi phí phân bổ chung…" khi không có dòng phân bổ (ASM-015-02). Tên bước lấy từ quy trình của bộ định mức (`NC Procedure Step.step_title` theo `step_id`). Logic gom nhóm là hàm thuần `engine.group_explanation(lines)`.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Dữ liệu vàng → 11 dòng DV-TEST-A từ `cost_service` khớp `golden_engine.direct_lines("DV-TEST-A")` (lượng, đơn giá, thành tiền từng dòng) và tổng 183.963,06; DV-TEST-B 32.822,44 | TC-COST-01 | FR-COST-003 | `tests/golden/test_costing_golden.py::test_TC_COST_01_*` |
| 2 | `price_service` với trực tiếp từ bộ máy + phân bổ `golden_engine.run()` → giá thành 287.745,46 / 88.169,70; tích lũy; giá tính toán; làm tròn 302.100 / 92.600 | TC-COST-04 | FR-COST-006 | `test_TC_COST_04_*` |
| 3 | V1 (`include_depreciation` = 0): đơn giá giờ máy 34.090,9091; L07 11.363,64; L08 0; trực tiếp 124.114,58; với phân bổ `run(False)` giá thành 224.109,10, làm tròn 235.300; L07, L08 có `DEPR_EXCLUDED_WARNING`; `get_explanation` có ghi chú khấu hao bị loại | TC-COST-06 | FR-COST-007 | golden + `test_nc_costing_run.py::test_TC_COST_06_bang_giai_trinh_ghi_khau_hao_bi_loai` |
| 4 | V4 (THUOCX không có đơn giá): DV-TEST-A "Lỗi", `calc_message` chứa "L05", không dòng; DV-TEST-B "Thành công", trực tiếp 32.822,44 | TC-COST-07 | FR-COST-016 | `test_TC_COST_07_*` (golden) + mức site |
| 5 | V3 ON_PRICE: tích lũy 15.144,50; giá tính toán 302.889,96; làm tròn 302.900 | TC-COST-12 | FR-COST-006 | `test_TC_COST_12_*` |
| 6 | `round_price(302150.00, 100)` = 302.200; `round_price(302149.99, 100)` = 302.100 | TC-COST-13 | FR-COST-006 | `tests/unit/test_costing_engine.py::test_TC_COST_13_*` |
| 7 | Lần tính trên site với bộ định mức DV-TEST-A dựng từ dữ liệu vàng: mọi dòng "Trực tiếp" có `step_id` (hoặc dòng gốc `service_level`), `resource_label`, `applied_qty`, `unit_rate`, `rate_source` khác trống; một dòng "Phân bổ" do `allocate` giả (test double) trả được ghi đủ `allocation_rule`, `driver_value`, `driver_total`, `amount`; `get_explanation` trả đủ các trường này | TC-COST-15 | FR-COST-010, NFR-CPL-001 | `test_nc_costing_run.py::test_TC_COST_15_*` |
| 8 | Phạm vi 2 dịch vụ (cùng khoa), 1 chưa có bộ "Đã khóa": `check_scope` liệt kê đúng dịch vụ đó; `run_costing()` không xác nhận → từ chối, không có NC Service Cost; `run_costing(confirm_ineligible=1)` → chỉ 1 NC Service Cost của dịch vụ còn lại | TC-COST-17 | FR-COST-002 | `test_TC_COST_17_*` |
| 9 | Tạo thiếu bộ tham số → từ chối; tạo với lần nhập "Nháp" → từ chối; tạo đủ 6 đầu vào với lần nhập "Đã chốt" → tạo được, "Nháp" | TC-COST-19 | FR-COST-001 | `test_TC_COST_19_*` |
| 10 | 51 cặp đủ điều kiện (`BACKGROUND_THRESHOLD` vá nhỏ trong test hoặc 51 bộ tối giản) → `frappe.enqueue` được gọi với `queue="long"`, trạng thái "Đang tính"; `execute_costing` cập nhật `progress` tới 100 | — | FR-COST-015 | `test_FR_COST_015_*` |
| 11 | Quyền: vai trò không có quyền (NC Clinician) không đọc NC Costing Run, NC Service Cost, không gọi được `start_costing`, `check_scope`; NC Auditor đọc được, `start_costing`/`run_costing` → PermissionError; DocPerm khớp ma trận | — | FR-ACC-002, FR-ACC-007 | `test_quyen_*` |
| 12 | Đầu vào không sửa được ở "Đã tính" (qua `doc.save()` và `frappe.client.set_value`) | — | FR-COST-001 | `test_khoa_dau_vao_khi_da_tinh` |

## 6. Test và độ phủ
- Đơn vị: `tests/unit/test_costing_engine.py` (mọi nhánh `direct_line`, `cost_service`, `price_service`, `round_price`, `PricingParams.from_values`, `group_explanation`), `test_costing_rates.py`, `test_costing_runner.py` (phạm vi, đủ điều kiện, ngưỡng, thứ tự, tiến độ, `allocate`, `extension`).
- Golden: `tests/golden/test_costing_golden.py` dựng `ServiceInput` từ `golden_engine.NORMS`, `JOB`, `ITEM`, `EQUIP`, `ROOM`, `PARAM` (qua `rates.py` và `resources.py`), so với `golden_engine.direct_lines`/`run`; V3 tạm đổi `golden_engine.PARAM["accumulation_mode"]` trong test rồi trả lại.
- Site: `nc_costing_run/test_nc_costing_run.py` (TC-COST-06 phần giải trình, 07, 15, 17, 19, FR-COST-015, quyền), `api/test_costing.py`.
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90`.

## 7. Điểm cắm cho FEAT khác
- FEAT-036: `extension` của `cost_service`/`runner.run` (ADR-017); `loader.py` thêm dữ liệu cận lâm sàng; trường [1.1] thêm vào ba DocType.
- FEAT-017: tham số `allocate` của `runner.run` trả dòng "Phân bổ" theo (dịch vụ, khoa); `reconcile.py` dùng `ServiceResult.direct_by_category` và `volume`.
- FEAT-018: ảnh chụp đọc `loader.load_context`; khóa đặt "Đã khóa" (đã bị `run_costing` từ chối).

## 8. Rủi ro
- Tạm tính trên lưới định mức (FEAT-012) và lần tính có thể lệch ở dòng tiện ích và ngày chọn đơn giá (hôm nay vs `costing_date`) — ASM-015-05, 19; ghi vào As-Built.
- Giá thành ở FEAT-015 chưa gồm phân bổ: người dùng có thể hiểu nhầm là giá cuối — dải cảnh báo ASM-015-02 trên cả hai màn hình.
- Test cũ phải bổ sung đầu vào bắt buộc (Q1).

## 9. Ánh xạ BR → mã → golden

| BR | Hàm | Golden |
| :-- | :-- | :-- |
| BR-COST-001 | `engine.job_rate` (FEAT-000, giá trị ở NC Job Title Rate) → `rates.labor_rate` | `job_rate` |
| BR-COST-002..006 | `engine.direct_line` → `provisional.line_amount` | `direct_lines` |
| BR-COST-004 | `resources.machine_annual`, `equipment_annual`, `machine_hourly_rate` qua `indicative` | `equip_rate` |
| BR-COST-005, 016 | `rates.room_rate`, `resources.room_hourly_rate` | `room_rate` |
| BR-COST-007 | `engine.applied_qty` | `applied_qty` |
| BR-COST-012 | `engine.price_service` | `run` dòng 147 |
| BR-COST-013 | `engine.apply_accumulation` (FEAT-000) | `run` dòng 148–150 |
| BR-COST-014 | `engine.round_price` | `run` dòng 151–152 |

## 10. Câu hỏi cho Lead

**Q1 — Test cũ dựng NC Costing Run thiếu hai trường nay bắt buộc (FR-COST-001, TC-COST-19).** `accounting_import` và `price_category` thành `reqd` và `validate` đòi lần nhập "Đã chốt". Chín chỗ dựng NC Costing Run bằng `insert` chỉ với `title`, `fiscal_year`, `costing_date`, `parameter_set` sẽ lỗi `MandatoryError`: `nc_core/doctype/nc_audit_event/test_nc_audit_event.py:164`, `nc_costing/doctype/nc_costing_parameter_set/test_nc_costing_parameter_set.py:27`, `nc_costing/doctype/nc_costing_run/test_nc_costing_run.py:27`, `nc_costing/doctype/nc_test_system/test_nc_test_system.py:228`, `tests/test_feat_039.py:183`, `:223`, `tests/test_feat_001.py:132`, `tests/test_form_actions.py:117`, `tests/utils.py:124` (`make_chain_data`).
- **PA1 (đề xuất)**: thêm helper `tests/utils.py::costing_run_inputs()` trả `{"accounting_import": <lần nhập "Đã chốt" dựng sẵn>, "price_category": "GIA-BV"}`; mỗi chỗ trên thêm `**costing_run_inputs()` vào dict dựng bản ghi. Không đổi, không xóa dòng `assert*` nào (kiểm bằng `git diff origin/develop -- '*test*.py' | grep -E '^-.*assert'` rỗng). Giống tiền lệ ASM-012-04.
- PA2: không đặt `reqd` ở DocType, chỉ kiểm khi tạo qua API — trái "mọi đường ghi" và TC-COST-19 dùng đường tạo chuẩn. Không đề xuất.

**Q2 — Quyền NC Service Cost.** `scripts/check_conventions.py:92` (tệp chung) xếp NC Service Cost vào dòng "Lần tính giá, kết quả, đối soát" (Finance W, Dept Head —). Nhưng NC Service Cost chính là bảng giải trình (ux SCR-DSK-023 "chế độ xem của NC Service Cost"; data-model NC Service Cost Line "là nội dung bảng giải trình"), và ma trận có dòng riêng "Bảng giải trình của dịch vụ thuộc khoa": Dept Head R (khoa), Finance R, Director/Admin/Auditor R.
- **PA1 (đề xuất)**: NC Service Cost theo dòng "Bảng giải trình…": DocPerm Finance R, Dept Head R, Director R, Admin R, Auditor R (kết quả do `writer` ghi bằng `ignore_permissions`, Finance không cần W); thêm `core/scope_rules/nc_service_cost.json` (`department_field` = `department`); sửa `check_conventions.py`: thêm dòng MATRIX "Bảng giải trình của dịch vụ thuộc khoa": "- R - R - - R - R R" và đổi `DOCTYPE_ROW["NC Service Cost"]`. NC Costing Run giữ dòng cũ. Test cũ chỉ cần Clinician bị từ chối (`test_feat_001.py:151`) — vẫn đúng.
- PA2: giữ như hiện tại; trưởng khoa chưa xem được bảng giải trình (để FEAT sau). Thiếu một dòng ma trận mức Must (FR-ACC-003).
