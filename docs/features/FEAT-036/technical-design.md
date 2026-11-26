# FEAT-036 — Tính giá cận lâm sàng — Thiết kế kỹ thuật

Issue NORM-42. Nguồn: `srs.md` FR-COST-017..025, 031, 032; FR-CLS-003, 004; FR-QC-004, 006; FR-CMP-002..004 (và phần cảnh báo trên lần tính của FR-CMP-006); BR-CLS-001..013, 016, BR-COST-002..004, 011, 015, 016; NFR-REL-001, NFR-REL-003, NFR-CPL-003; `use-cases.md` UC-012 bước 1, 4, 6, 8 và 4e..4k; `data-model.md` NC Costing Run, NC Service Cost, NC Test System Cost, NC Service Cost Line ([1.1]); `architecture.md` ADR-003, ADR-004, ADR-017; `ux-foundations.md` SCR-DSK-022, SCR-DSK-023 ([1.1]); golden `docs/golden/golden_cls.py` (toàn bộ, trừ `material_recon`, `volume_recon` — FEAT-037); `test-cases.md` mục 2A, TC-CLS-01..15, 37, 38, 51.

Phụ thuộc (DONE trên `origin/develop` `d4f4038`): FEAT-015 (`engine.cost_service`, `runner.run`, `loader.py`, `writer.py`, ba DocType kết quả), FEAT-033 (NC Equipment Type `compliance_required`, NC Equipment Compliance, `costing/compliance.py`), FEAT-034 (NC Norm Set `test_system`, `tests_per_tube`; NC Norm Line `cost_level`, `apply_k`, `attach_to`, `attach_equipment`), FEAT-035 (NC Test System Volume, NC Equipment Usage, NC Stock Issue Actual; ô test phụ trống = `NULL`). Dùng lại: FEAT-010 (`costing/resources.py::machine_annual`, `equipment_annual`, `machine_hourly_rate`), FEAT-031 (NC Test System, `costing/test_systems.py`), FEAT-032 (NC QC Plan, NC EQA Program, `costing/qc_plans.py::estimated_tests`, `eqa_shares`, `eqa_samples_per_year`), FEAT-011 (bộ tham số: `electricity_price`, `expired_depreciation_mode`, `eqa_cost_category`, `rental_cost_category`, `jv_cost_category`).

Giả định: `docs/decisions/assumptions/FEAT-036.md` (ASM-036-01..25). Sửa thiết kế: `docs/decisions/amendments/AMD-036-01.md` (trường `run_warnings` của NC Costing Run).

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-COST-017 | NC Costing Run thêm `volume_scenario` (mặc định "Thực tế 12 tháng") và `compliance_allocation_mode` (mặc định "Theo giá trị tài sản"), bắt buộc, khóa như các đầu vào khác. Kịch bản dùng cho **mọi** sản lượng của lần tính (NC Service Volume, NC Test System Volume, NC Equipment Usage) — thay hằng `VOLUME_SCENARIO` của `loader.py` |
| FR-COST-018 | `cls.k_factor` (BR-CLS-001) cho từng hệ thống "Đang dùng" của dịch vụ, k làm tròn 6 chữ số, lưu `NC Test System Cost.k_factor` (Float, precision 6) |
| FR-COST-019 | Chi phí một kết quả từng dòng định mức theo `cost_level`: RESULT (BR-CLS-002, nhân k khi `apply_k`), TUBE (BR-CLS-003), BATCH (BR-CLS-004), DAY/PERIOD (BR-CLS-005) |
| FR-COST-020 | Vật liệu nội kiểm (BR-CLS-006), chất chuẩn (BR-CLS-007) từ NC QC Plan; ngoại kiểm (BR-CLS-008) ở cấp dịch vụ. Mỗi khoản là dòng chi phí riêng (`line_origin` "Kế hoạch chất lượng" / "Ngoại kiểm") |
| FR-COST-021 | Dòng EQUIPMENT theo hình thức có máy và tiêu chí chia (BR-COST-004, BR-CLS-009); linh kiện theo số kết quả, giờ chạy (BR-CLS-010) và điện (BR-CLS-012) là dòng tự sinh (`line_origin` "Thiết bị") |
| FR-COST-022 | Dịch vụ nhiều hệ thống: lưu từng hệ thống vào `test_system_costs`, chi phí trực tiếp dịch vụ = bình quân gia quyền (BR-CLS-013) + ngoại kiểm |
| FR-COST-023 | Thiếu sản lượng / Qbn = 0 / có dòng BATCH mà thiếu cỡ mẻ (và các thiếu dữ liệu khác ở mục 4.6) → dịch vụ "Lỗi", `calc_message` nêu đúng dữ liệu thiếu; dịch vụ khác vẫn tính |
| FR-COST-024 | `NC Service Cost.volume` của dịch vụ cận lâm sàng = Σ `patient_results` các hệ thống (không lấy NC Service Volume); `ServiceResult.volume` mang số này cho điểm cắm `allocate` (FEAT-017) — ASM-036-20 |
| FR-COST-025 (Should) | Cảnh báo "Sản lượng thấp" (BR-CLS-016) trên `NC Test System Cost.low_volume_warning`, `calc_status` "Cảnh báo", `calc_message` |
| FR-COST-031 | NC Service Cost Line thêm `test_system`, `line_origin`, `cost_level`, `k_factor`, `divisor_label`, `divisor_value`, `divisor_source`; `get_explanation` trả khối hệ thống xét nghiệm và "k được tính thế nào" |
| FR-COST-032 | `costing/snapshot.py` dựng phần cận lâm sàng của ảnh chụp (đầu vào đã phân giải + bản ghi nguồn) và tái lập kết quả từ ảnh chụp. Lưu ảnh chụp khi khóa là FEAT-018 (ASM-036-21) |
| FR-CLS-003 | Không có Qbn của mọi hệ thống → dùng `volume_share_pct` khai tay; tổng ≠ 100 → dịch vụ "Lỗi" |
| FR-CLS-004 (Should) | Mọi hệ thống có Qbn → tỷ trọng = Qbn ÷ ΣQbn (bỏ qua tỷ trọng khai tay) |
| FR-QC-004 | Phí chương trình ngoại kiểm chia theo `qc_plans.eqa_shares` (đều nếu không khai tỷ lệ) |
| FR-QC-006 | Ô test phụ trống (`NULL`) của NC Test System Volume → suy từ kế hoạch chất lượng, tỷ lệ ước tính của NC Test System; `k_estimated` = 1, nhãn "Ước tính từ kế hoạch" |
| FR-CMP-002..004 | Kiểm định, hiệu chuẩn năm của thiết bị từ hồ sơ còn hạn tại `costing_date` (BR-CLS-011), theo `compliance_allocation_mode`; không có hồ sơ nào → `annual_calibration_cost` nhập tay |
| FR-CMP-006 (phần lần tính) | Thiết bị dùng trong lần tính thuộc loại bắt buộc mà không có hồ sơ còn hạn → cảnh báo trên lần tính (`run_warnings`, AMD-036-01), vẫn tính |
| NFR-REL-003 | k bằng Decimal, r6; chạy lại / tái lập cùng đầu vào cho cùng k |
| NFR-CPL-003 | Mọi dòng `line_origin` ≠ trống có `cost_level`, `divisor_label`, `divisor_value`, `divisor_source` |

**Không làm**: đối soát vật chất, sản lượng, thiếu dữ liệu, độ nhạy (FR-COST-026..030, BR-CLS-014, 015 — FEAT-037); phân bổ cấp 1, cấp 2, đối soát tài chính (FEAT-017; FEAT-036 chỉ bảo đảm sản lượng truyền vào đúng — TC-CLS-51 kiểm ở mức hàm và trên `ServiceResult.volume`); khóa, lưu `snapshot_file`/`snapshot_hash`, nhân bản (FEAT-018 — FEAT-036 cấp hàm dựng và tái lập); dịch vụ bộ (FR-SVC-010). Chẩn đoán hình ảnh và tiêu chí Phút chiếm máy (FR-CLS-005) được cài vì chung công thức, kiểm bằng TC-CLS-13 ở mức hàm, không thuộc nghiệm thu R1 (implementation-plan 1.1).

## 2. DocType (mở rộng, không tạo lại; chỉ thêm trường → không cần patch dữ liệu)

### 2.1 NC Costing Run
| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| volume_scenario **(mới)** | Kịch bản sản lượng | Select `Thực tế 12 tháng`/`Kế hoạch`/`Công suất` | Có | `default` "Thực tế 12 tháng". Đặt sau `price_category` |
| compliance_allocation_mode **(mới)** | Cách phân bổ kiểm định, hiệu chuẩn | Select `Theo giá trị tài sản`/`Gắn trực tiếp thiết bị` | Có | `default` "Theo giá trị tài sản" |
| run_warnings **(mới, AMD-036-01)** | Cảnh báo của lần tính | Small Text | | `read_only`; mỗi cảnh báo một dòng; ghi lại mỗi lần tính |

`INPUT_FIELDS` thêm `volume_scenario`, `compliance_allocation_mode` (khóa đầu vào ngoài Nháp/Tính lỗi như ASM-015-11). Test cũ dựng NC Costing Run không truyền hai trường → nhận `default`, không phải sửa test.

### 2.2 NC Service Cost
| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| is_paraclinical **(mới)** | Dịch vụ cận lâm sàng | Check | read_only |
| eqa_cost **(mới)** | Chi phí ngoại kiểm một kết quả | Currency | BR-CLS-008 |
| test_system_costs **(mới)** | Kết quả theo hệ thống xét nghiệm | Table NC Test System Cost | |
`norm_set` để trống với dịch vụ cận lâm sàng (data-model). `volume` theo FR-COST-024.

### 2.3 NC Test System Cost (mới, bảng con `istable` = 1, module NC Costing; quyền theo cha)
| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| test_system | Hệ thống xét nghiệm | Link NC Test System | in_list_view |
| norm_set | Bộ định mức | Link NC Norm Set | |
| patient_results | Số kết quả trả | Float | Qbn |
| share_pct | Tỷ trọng đã dùng | Float, precision 6 | phần trăm (75 = 75%) |
| q_iqc, q_calibration, q_rerun, q_eqa | Số test nội kiểm / chuẩn máy / chạy lại / ngoại kiểm đã dùng | Float | |
| wastage_rate | Hao hụt đã dùng (%) | Percent | h × 100 |
| k_factor | Hệ số k | Float, precision 6 | |
| k_estimated | Ước tính từ kế hoạch | Check | |
| direct_cost | Chi phí trực tiếp một kết quả | Currency | Σ dòng của hệ thống |
| low_volume_warning | Cảnh báo sản lượng thấp | Check | |
`track_changes` không áp cho bảng con. Dòng trùng nghĩa với data-model; không thêm trường.

### 2.4 NC Service Cost Line
| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| test_system **(mới)** | Hệ thống xét nghiệm | Link NC Test System | trống với dòng ngoại kiểm, dòng phân bổ |
| line_origin **(mới)** | Nguồn của dòng | Select `\nĐịnh mức\nKế hoạch chất lượng\nNgoại kiểm\nThiết bị\nHồ sơ tuân thủ` | trống với dịch vụ không cận lâm sàng. "Hồ sơ tuân thủ" giữ trong miền giá trị nhưng R1 không sinh dòng riêng (kiểm định nằm trong dòng EQUIPMENT — ASM-036-13) |
| cost_level **(mới)** | Cấp phát sinh | Data | `RESULT`/`TUBE`/`BATCH`/`DAY`/`PERIOD`; giao diện hiện nhãn tiếng Việt |
| k_factor **(mới)** | Hệ số k đã nhân | Float, precision 6 | trống khi không nhân |
| divisor_label **(mới)** | Tên mẫu số | Data | xem mục 4.4 |
| divisor_value **(mới)** | Giá trị mẫu số | Float | |
| divisor_source **(mới)** | Nguồn của mẫu số | Select `\nThực tế\nƯớc tính từ kế hoạch` | |

## 3. API (`normcore/api/costing.py`, mở rộng; quyền giữ như FEAT-015)

| Hàm | Đổi |
| :-- | :-- |
| `check_scope(run)` | Không đổi chữ ký. Cặp cận lâm sàng không có hệ thống nào có bộ "Đã khóa" nằm trong `ineligible` |
| `start_costing(run, confirm_ineligible)` | Không đổi |
| `get_run_results(run)` | Thêm vào `run`: `volume_scenario`, `compliance_allocation_mode`, `run_warnings` (list chuỗi). Mỗi dịch vụ thêm `is_paraclinical`, `eqa_cost`, `test_systems: [{test_system, norm_set, patient_results, share_pct, k_factor, k_estimated, direct_cost, low_volume_warning}]` |
| `get_explanation(service_cost)` | Thêm `paraclinical` (None với dịch vụ thường): `{systems: [{test_system, norm_set, equipment, patient_results, share_pct, share_source ("Từ số kết quả trả" / "Khai tay"), q_iqc, q_calibration, q_rerun, q_eqa, total_tests, wastage_rate, k_factor, k_estimated, direct_cost, low_volume_warning, groups: engine.group_explanation(dòng của hệ thống)}], service_lines: [dòng ngoại kiểm], weighted_direct, eqa_cost, direct_total}`; mỗi dòng trả thêm 7 trường mục 2.4. `notes` thêm "Khấu hao thiết bị hết thời gian sử dụng: ZERO/CONTINUE" khi có dòng mang cảnh báo đó (TC-CLS-11) |

Kiểm quyền: như FEAT-015 (`frappe.has_permission` trên NC Costing Run / NC Service Cost, scope rule khoa cho NC Department Head). Không API mới.

## 4. Logic thuần

### 4.1 `costing/engine.py` (mở rộng, ADR-017; hàm cũ giữ hành vi)
- `CostLine` thêm trường tùy chọn (mặc định trống): `test_system=""`, `line_origin=""`, `cost_level=""`, `k_factor: Decimal|None=None`, `divisor_label=""`, `divisor_value: Decimal|None=None`, `divisor_source=""`, `cost_category: str|None=None`.
- `_sum_by` theo loại chi phí: `ln.cost_category or COMPONENT_CATEGORY[ln.component]` (để phí ngoại kiểm, tiền thuê theo bộ tham số — ASM-036-15).
- `ServiceInput` thêm `paraclinical: "cls.ClsServiceInput | None" = None`.
- `ServiceResult` thêm `is_paraclinical=False`, `eqa_cost: Decimal|None=None`, `test_system_costs: tuple=()`; `finish_service` dựng lại bằng `dataclasses.replace` để giữ trường mới.
- `cost_service`: nếu `inp.paraclinical is not None` → `from normcore.costing import cls` (nhập trễ như `provisional`) và `return cls.cost_service(inp, params)`; ngược lại giữ nguyên đường FEAT-015 (kể cả `extension`).

### 4.2 `costing/cls.py` (mới, không import `frappe`; Decimal, ROUND_HALF_UP; r2/r4/r6 như golden)

Dataclass đầu vào (đóng băng, chỉ số liệu đã phân giải — dựng ở `loader.py`, cũng là nội dung ảnh chụp):
- `EquipmentInput(code, department, mode, basis, original_cost, life_years, in_service, contract_cost, maintenance, maintenance_vendor_paid, components: tuple[(cost, life_basis, life_value, vendor_paid)], dept_share, asset_value, power: (run_kw, run_h, standby_kw, standby_h, continuous)|None, manual_calibration, records: tuple[(cost_per_time, cycle_months, valid_on_costing_date)], planned_hours, utilization, qtb, mtb, compliance_required)`.
- `ClsNormLine(norm: engine.NormLine, cost_level, apply_k, attach ("SYSTEM"/"EQUIP"/""), attach_equipment)`.
- `IqcLine(item, levels, runs_per_day, qty_per_run, shared_params, rate: LineRate|None)`; `CalLine(points, replicates, per_year, cost_per_calibration)`.
- `AuxCounts(qnk, qcal, qrerun, qeqa, h)` — mỗi ô `Decimal|None` (None = không có số thực tế).
- `TestSystemInput(code, norm_set|None, equipment, qbn|None, has_volume, actual: AuxCounts, est_rerun_rate, est_h, run_days|None, plan_run_days|None, batch|None, tests_per_tube|None, manual_share_pct|None, minutes_per_case|None, lines: tuple[ClsNormLine], rates: Mapping, iqc: tuple, cal: tuple, plan_complete, eqa_tests_est, main_reagents: tuple[(item, nominal_tests, open_days)])`.
- `EqaInput(program, fee, shipping, share)` (share là phân số từ `qc_plans.eqa_shares`).
- `ClsServiceInput(scenario, fiscal_year, systems, equipment: Mapping[code, EquipmentInput], dept_peers: tuple[code], eqa: tuple[EqaInput], allocation_mode ("ASSET"/"DIRECT"), expired_mode, on, include_depr, electricity_price, imaging: bool, eqa_category, rental_category, jv_category)`.

Hàm (mỗi hàm một quy tắc, ánh xạ golden ở mục 9):

| Hàm | Làm gì |
| :-- | :-- |
| `aux_counts(sys, imaging) -> (qnk, qcal, qrerun, qeqa, h, estimated: bool)` | Từng ô: có số thực tế → dùng; `None` → ước tính: Qnk, Qchuan = `qc_plans.estimated_tests(plan)` (đã dựng sẵn ở loader thành hai số), Qngk = `eqa_tests_est` (Σ đợt × mẫu các chương trình có dịch vụ), Qlai = r0(`est_rerun_rate` × Qbn), h = `est_h`. Chẩn đoán hình ảnh: Qnk = Qchuan = Qngk = 0, h = 0 (BR-CLS-001) |
| `k_factor(qbn, qnk, qcal, qrerun, qeqa, h) -> (k, total)` | k = r6(total ÷ ((1 − h) × Qbn)) |
| `compliance_annual(eq, peers, mode) -> Decimal` | BR-CLS-011. Hồ sơ còn hạn: Σ cost × 12 ÷ cycle. Không có hồ sơ nào → `manual_calibration` (FR-CMP-002), thiết bị đó tính như Gắn trực tiếp và không vào quỹ chung (ASM-036-11). DIRECT hoặc `asset_value` trống → phần của chính thiết bị; ASSET → quỹ (Σ phần của các thiết bị cùng khoa có `asset_value` và có hồ sơ) × asset_value ÷ Σ asset_value của các thiết bị đó |
| `equipment_annual(eq, ctx) -> (annual, notes)` | BR-CLS-009: `resources.machine_annual(mode, …, on, expired_mode, include_depr)` + `resources.equipment_annual(machine, maintenance, calibration=compliance_annual, components, mode, vendor_paid, dept_share)`. `notes`: "Khấu hao bị loại (loại giá không kết cấu khấu hao)" khi `include_depr` = 0 và Mua; "Hết thời gian sử dụng: khấu hao = 0 (ZERO)" / "Hết thời gian sử dụng: tiếp tục tính khấu hao (CONTINUE)" khi `resources.is_expired` |
| `per_result(eq, annual, m=None) -> (amount, divisor_label, divisor_value)` | Số kết quả: r2(annual ÷ Qtb), "Qtb". Phút chiếm máy: r2(r4(annual ÷ Mtb) × m), "Mtb". Giờ kế hoạch: r2(m ÷ 60 × `resources.machine_hourly_rate(annual, planned_hours, utilization)`), "Giờ kế hoạch × hệ số sử dụng" (ASM-036-09) |
| `part_per_result(eq, m)`, `power_per_result(eq, run_days, m)` | BR-CLS-010 (Số kết quả, Giờ chạy; bỏ linh kiện "nhà cung cấp chịu" khi Đặt), BR-CLS-012 (D = 365 khi cấp điện liên tục; không khai công suất → 0, không sinh dòng) |
| `norm_line_cost(sys, line, k, rate, ctx) -> CostLine` | Mục 4.3 |
| `system_lines(sys, ctx) -> (lines, k, total, estimated)` | Dòng định mức theo `line_id` → dòng linh kiện `EQ-P` (nếu > 0 hoặc có linh kiện) → `EQ-E` (nếu thiết bị có công suất) → `QC-N{n}` mỗi dòng nội kiểm → `QC-C{n}` mỗi dòng chuẩn máy (BR-CLS-006, 007) |
| `shares(systems) -> (dict code→phân số, source)` | FR-CLS-004: mọi hệ thống có Qbn > 0 → Qbn ÷ ΣQbn, "Từ số kết quả trả"; ngược lại `manual_share_pct` ÷ 100, "Khai tay", tổng ≠ 100 → lỗi (FR-CLS-003) |
| `eqa_per_result(eqa, qsum) -> Decimal` | r2(Σ (fee + shipping) × share ÷ ΣQbn) (BR-CLS-008, FR-QC-004) |
| `low_volume(total, reagent) -> bool` | BR-CLS-016: total × open_days ÷ 365 < nominal_tests |
| `validate(inp) -> list[str]` | Mục 4.6 |
| `cost_service(inp, params) -> ServiceResult` | Mục 4.5 |
| `group_by_system(lines) -> list` | Gom dòng theo `test_system` rồi `engine.group_explanation`; dòng `test_system` trống đi vào nhóm "Cấp dịch vụ" |

### 4.3 Chi phí một kết quả từng dòng định mức (golden `system_lines`)
`u` = đơn giá một đơn vị định mức (`LineRate.rate` = `pricing.unit_price_per_norm`, r4 — golden `unit_price`); `q` = `engine.applied_qty` (BR-COST-007); `w` = hao hụt của dòng.
| Trường hợp | Thành tiền | Mẫu số | Ghi chú |
| :-- | :-- | :-- | :-- |
| LABOR | `engine.direct_line` (BR-COST-002) | "Kết quả", 1 | |
| EQUIPMENT | `per_result(eq, equipment_annual(eq))` với eq = `resource` của dòng nếu là thiết bị, không thì thiết bị chính; `m` = `minutes_per_case` (Phút chiếm máy) hoặc `q` (Giờ kế hoạch) | Qtb / Mtb / Giờ kế hoạch | `rate_source` "EQ_A · Mua · Theo giá trị tài sản"; `warning` = `notes`; `cost_category` = `rental_category`/`jv_category` khi Thuê / Liên doanh (ASM-036-15) |
| RESULT, `apply_k` | r2(q × u × k), không áp `w` (BR-CLS-002) | "Kết quả", 1 | `k_factor` = k; `divisor_source` theo `estimated` |
| RESULT, không `apply_k` (DRUG/SUPPLY) | `engine.direct_line` (BR-COST-003) | "Kết quả", 1 | |
| TUBE | r2(q × (1 + w) × u ÷ `tests_per_tube`) | "Số xét nghiệm mỗi ống" | ASM-036-07 |
| BATCH | r2(q × (1 + w) × u ÷ `batch`) | "Cỡ mẻ" | |
| DAY | năm = q × (1 + w) × u × D | | |
| PERIOD | năm = q × (1 + w) × u | | `q` là lượng năm |
| DAY/PERIOD gắn hệ thống (hoặc trống) | r2(năm ÷ Qbn) | "Qbn" | BR-CLS-005 |
| DAY/PERIOD gắn thiết bị | `per_result(attach_equipment or thiết bị chính, năm, m)` | Qtb / Mtb | |
| Dòng loại trừ, `billed_separately` | như `engine.direct_line` (0) | | ASM-015-07 |
Cờ `apply_k` chỉ có ở RESULT loại DRUG/SUPPLY (FEAT-034 đã chặn nhập). Phép chia trung gian không làm tròn; chỉ làm tròn thành tiền r2 (golden). `u` trùng `resource` dòng nội kiểm của kế hoạch chất lượng đã bị FEAT-034 từ chối nên không đếm trùng.

Dòng tự sinh: `EQ-P` (component EQUIPMENT, `cost_level` RESULT, mẫu số "Tuổi thọ linh kiện"), `EQ-E` (UTILITY, DAY, mẫu số Qtb/Mtb), `QC-Nn` (DRUG, PERIOD, "Qbn", `line_origin` "Kế hoạch chất lượng": r2(qty × levels × runs × D × u ÷ shared ÷ Qbn)), `QC-Cn` (DRUG, PERIOD, "Qbn": r2(cost × per_year ÷ Qbn)), `EQA` (cấp dịch vụ, component theo `eqa_category` — ASM-036-15, "Tổng Qbn của dịch vụ"). `step_id` trống ("Chung"), `norm_line_id` = mã dòng tự sinh.

### 4.4 Nguồn mẫu số (NFR-CPL-003)
`divisor_source` = "Ước tính từ kế hoạch" cho dòng nhân k khi `estimated`; còn lại "Thực tế" (Qbn, Qtb, Mtb, cỡ mẻ, số xét nghiệm mỗi ống đều là số nhập). Dòng Theo kết quả không nhân k và LABOR ghi mẫu số "Kết quả", 1 để 100% dòng có mẫu số (ASM-036-08).

### 4.5 `cls.cost_service(inp, params)`
1. `errors = validate(inp.paraclinical, inp)`; có lỗi → `ServiceResult` "Lỗi", `calc_message` = "; ".join(errors), không dòng, `is_paraclinical` = True, `volume` = ΣQbn (nếu tính được).
2. Mỗi hệ thống (thứ tự theo mã): `system_lines` → dòng gắn `test_system`; `direct_cost` = Σ thành tiền; `low_volume` theo từng hóa chất chính của bộ định mức (dòng RESULT có `is_main_reagent`, có `nominal_tests` và `open_stability_days`; thiếu → bỏ qua).
3. `share` (4.2), `weighted = r2(Σ share × direct_cost)` (golden), `eqa = eqa_per_result`, `direct_total = weighted + eqa`.
4. `direct_by_component`: r2(Σ share × tổng cấu phần của hệ thống) mỗi cấu phần, cộng `eqa` vào cấu phần của dòng EQA; chênh lệch làm tròn với `direct_total` dồn vào cấu phần lớn nhất (ASM-036-16). `direct_by_category` tương tự theo loại (có `cost_category`).
5. `status`: "Cảnh báo" khi có hệ thống sản lượng thấp hoặc có dòng mang cảnh báo đơn giá quá hạn/chưa xác minh (như FEAT-015); `calc_message` "Sản lượng thấp: GLU-B (389,59 test trong 30 ngày < 200)". Cảnh báo khấu hao, hết thời gian sử dụng, thiếu hồ sơ là thông tin, không đổi trạng thái.
6. `test_system_costs`: một `TestSystemCost` mỗi hệ thống (trường mục 2.3; `share_pct` = share × 100, r6).
7. `lines` = dòng các hệ thống (theo mã hệ thống) + dòng EQA. Lưu ý: bảng giải trình hiển thị dòng của từng hệ thống ở thành tiền **một kết quả của hệ thống đó**; tổng dịch vụ là bình quân gia quyền (giao diện ghi rõ).

### 4.6 `cls.validate` — lỗi dừng dịch vụ (FR-COST-023, FR-CLS-003, UC-012 4d, 4i, 4k)
Thu đủ lỗi (không dừng ở lỗi đầu), thứ tự: tỷ trọng → từng hệ thống theo mã → thiết bị.
| Điều kiện | Thông báo |
| :-- | :-- |
| Hệ thống "Đang dùng" không có bộ định mức "Đã khóa" | "Hệ thống {ts} chưa có bộ định mức Đã khóa" |
| Không phải mọi hệ thống có Qbn > 0 và tổng `volume_share_pct` ≠ 100 | "Tổng tỷ trọng sản lượng các hệ thống của dịch vụ {dv} tại khoa {k} là {x}%, khác 100%" |
| Không có NC Test System Volume của (năm, kịch bản, hệ thống) | "Hệ thống {ts} thiếu sản lượng năm {y}, kịch bản {s}" |
| `patient_results` = 0 | "Hệ thống {ts} có số kết quả trả bằng 0" |
| Có dòng BATCH, `avg_batch_size` trống | "Hệ thống {ts} có dòng Theo mẻ ({L04}) nhưng thiếu cỡ mẻ bình quân" |
| Có dòng TUBE, `tests_per_tube` trống/0 | "Bộ định mức {ns} có dòng Theo ống mẫu nhưng thiếu số xét nghiệm mỗi ống" |
| Cần D (dòng DAY, nội kiểm, điện không liên tục) mà cả `run_days` và `run_days_per_year` trống | "Hệ thống {ts} thiếu số ngày chạy máy" |
| Dòng không loại trừ thiếu đơn giá (trừ EQUIPMENT); vật liệu nội kiểm thiếu đơn giá | "Hệ thống {ts}: dòng thiếu đơn giá: L05 (HC_PT)" / "Hệ thống {ts}: vật liệu nội kiểm {item} thiếu đơn giá" |
| Thiết bị Số kết quả có Qtb = 0; Phút chiếm máy thiếu Mtb hoặc `machine_minutes_per_case`; Giờ kế hoạch thiếu giờ hoặc hệ số | "Thiết bị {eq} thiếu Qtb năm {y}, kịch bản {s}" / "Thiết bị {eq} thiếu phút khai thác (Mtb) …" / "Hệ thống {ts} thiếu số phút chiếm máy một ca" / "Thiết bị {eq} thiếu giờ khai thác kế hoạch hoặc hệ số sử dụng" |
| h ≥ 1 | "Hệ thống {ts} có tỷ lệ hao hụt từ 100% trở lên" |
`ValueError` khác từ `resources` (dữ liệu thiết bị hỏng) được bắt trong `cls.cost_service` và ghi thành lỗi của dịch vụ "Thiết bị {eq}: {thông báo}" — không làm cả lần "Tính lỗi" (khác ASM-015-08 cho dịch vụ thường, ASM-036-18).

### 4.7 `costing/snapshot.py` (mới, thuần; FR-COST-032, NFR-REL-001, NFR-REL-003)
| Hàm | Làm gì |
| :-- | :-- |
| `to_plain(obj)` / `from_plain(...)` | Dataclass ↔ dict; Decimal → chuỗi, date → ISO; có khóa `__type__` để dựng lại đúng lớp (`ServiceInput`, `NormLine`, `LineRate`, `ClsServiceInput`, …) |
| `build(inputs, params, sources) -> dict` | `{"version": 1, "params": …, "inputs": [ServiceInput…], "sources": {...}}`; `sources` = bản ghi nguồn phần cận lâm sàng: hệ thống xét nghiệm, sản lượng hệ thống, kế hoạch chất lượng, chương trình ngoại kiểm, hồ sơ tuân thủ, thiết bị + linh kiện + tỷ lệ khoa, phút khai thác, xuất kho thực tế của năm (chỉ lưu, FEAT-037 dùng) |
| `dumps(snap) -> bytes`, `digest(bytes) -> str` | JSON chuẩn hóa (`sort_keys`, `ensure_ascii=False`, phân cách cố định) và sha256 |
| `reproduce(snap) -> list[ServiceResult]` | Dựng lại đầu vào và gọi `runner.run(..., allocate=None)` — không đọc CSDL |
`loader.capture_snapshot(run, eligible) -> dict` (lớp CSDL) dựng `inputs` bằng chính `load_service` và `sources`. FEAT-018 gọi hàm này khi khóa và lưu `snapshot_file`, `snapshot_hash` (ASM-036-21).

### 4.8 Lớp CSDL (AMD-015-02)
- `loader.scope_info`: với cặp (dịch vụ, khoa) mà dịch vụ `is_paraclinical` = 1 và có ≥ 1 NC Test System "Đang dùng" cùng khoa → **một** mục `{"service", "department", "norm_set": "", "test_systems": [{"test_system", "norm_set"|None}]}` (mọi hệ thống "Đang dùng", theo mã; `norm_set` = bộ "Đã khóa" có `test_system` đó). Không hệ thống nào có bộ "Đã khóa" → cặp vào `ineligible`. Dịch vụ cận lâm sàng không có hệ thống "Đang dùng" → đường FEAT-015 (ASM-036-02). Bộ "Đã khóa" có `test_system` không còn "Đang dùng" vẫn bị loại như FEAT-031.
- `loader.load_context`: `VOLUME_SCENARIO` → `run.volume_scenario`; nạp theo lô cho mọi mục cận lâm sàng: NC Test System, NC Test System Volume (năm, kịch bản), NC QC Plan (+ dòng), NC EQA Program có dòng dịch vụ trong phạm vi, NC Equipment của mọi khoa liên quan (+ linh kiện, tỷ lệ khoa), NC Equipment Type, NC Equipment Compliance của các thiết bị đó, NC Equipment Usage (năm, kịch bản), Σ `patient_results` theo (thiết bị chính, khoa) cho Qtb (ASM-036-10), NC Item (`is_main_reagent`, `nominal_tests`, `open_stability_days`) và giá của mặt hàng nội kiểm.
- `loader.load_service(ctx, e)`: mục có `test_systems` → `ServiceInput(norm_set="", lines=(), rates={}, volume=ΣQbn, paraclinical=ClsServiceInput(...))`.
- `loader.run_warnings(ctx, eligible) -> list[str]`: `compliance.missing_required(thiết bị dùng trong lần tính, hồ sơ, costing_date)` → "Thiết bị {eq} ({loại}) không có hồ sơ tuân thủ còn hạn tại {dd/mm/yyyy}" (FR-CMP-006).
- `writer.write_results`: ghi `is_paraclinical`, `eqa_cost`, `test_system_costs`, 7 trường dòng mới; `execute_costing` ghi `run_warnings` cùng savepoint.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Dữ liệu vàng GLU-A: k = 1,108247, tổng 12.900; gọi lại `k_factor`/`cost_service` lần hai và `snapshot.reproduce` cho cùng k | TC-CLS-01 | FR-COST-018, NFR-REL-003 | `tests/golden/test_cls_golden.py::test_TC_CLS_01_k_GLU_A` |
| 2 | GLU-B không có số thực tế: Qnk 600, Qchuan 48, Qlai 80, Qngk 12, tổng 4.740, k = 1,221649, `estimated` = True; dòng nhân k có `divisor_source` "Ước tính từ kế hoạch" | TC-CLS-02 | FR-COST-018, FR-QC-006 | `test_TC_CLS_02_k_GLU_B_uoc_tinh` |
| 3 | L02, L03: GLU-A 33.247,41 / 1.329,90; GLU-B 36.649,47 / 1.465,98 (= `golden_cls.system_lines`); đặt `w` = 5% ở L02 không đổi kết quả | TC-CLS-03 | FR-COST-019 | `test_TC_CLS_03_dong_nhan_k_khong_hao_hut` |
| 4 | L01 = 1.500,00 (÷ 4 xét nghiệm mỗi ống), L04 = 1.250,00 (÷ cỡ mẻ 40) ở cả hai hệ thống | TC-CLS-04 | FR-COST-019 | `test_TC_CLS_04_ong_mau_va_me` |
| 5 | L05 gắn thiết bị: 120,00 (EQ_A, Qtb 300.000), 360,00 (EQ_B, Qtb 100.000) | TC-CLS-05 | FR-COST-019 | `test_TC_CLS_05_ngay_may_gan_thiet_bi` |
| 6 | QC-N 90,00 / 270,00; QC-C 400,00 / 1.200,00; là dòng riêng `line_origin` "Kế hoạch chất lượng" | TC-CLS-06 | FR-COST-020 | `test_TC_CLS_06_noi_kiem_chat_chuan` |
| 7 | ASSET: kiểm định EQ_A 10.500.000, EQ_B 3.500.000; thiết bị năm 514.500.000 / 3.500.000; L07 1.715,00 / 35,00; EQ_B máy 0, bảo trì 0 | TC-CLS-07 | FR-COST-021, FR-CMP-002, FR-CMP-003 | `test_TC_CLS_07_theo_gia_tri_tai_san` |
| 8 | V1 DIRECT: kiểm định 8.000.000 / 6.000.000; L07 1.706,67 / 60,00; dịch vụ 42.278,67. `frappe.new_doc("NC Costing Run")` có `volume_scenario` "Thực tế 12 tháng", `compliance_allocation_mode` "Theo giá trị tài sản" | TC-CLS-08 | FR-COST-017, FR-CMP-004 | golden `test_TC_CLS_08_V1_gan_truc_tiep` + site `test_TC_CLS_08_mac_dinh_lan_tinh` |
| 9 | EQ_A: EQ-P 300,00; EQ-E 87,60 | TC-CLS-09 | FR-COST-021 | `test_TC_CLS_09_linh_kien_dien` |
| 10 | GLU-A 41.531,03; GLU-B 44.221,57; tỷ trọng 75 / 25 "Từ số kết quả trả"; bình quân 42.203,67; ngoại kiểm 75,00; trực tiếp 42.278,67 (= `golden_cls.service_direct`); trên site NC Service Cost có 2 dòng `test_system_costs` đủ trường và `direct_*` cộng bằng 42.278,67 | TC-CLS-10 | FR-COST-022, FR-QC-004, FR-CLS-004 | golden + site `test_TC_CLS_10_dich_vu_GLU_tren_site` |
| 11 | V2 (ngày 01/01/2033): ZERO → L07 EQ_A 515,00; CONTINUE → 1.715,00; dòng L07 có `warning` nêu lựa chọn; `get_explanation.notes` có lựa chọn | TC-CLS-11 | FR-COST-021 (FR-RES-007) | `test_TC_CLS_11_V2_het_thoi_gian_su_dung` |
| 12 | V3 EQ_C Thuê: 1.500,00; không có cảnh báo khấu hao | TC-CLS-12 | FR-COST-021 (FR-RES-020) | `test_TC_CLS_12_V3_may_thue` |
| 13 | V4 EQ_CT Phút chiếm máy: năm 3.640.000.000; r4 20.222,2222; m 10 → 202.222,22; m 20 → 404.444,44 | TC-CLS-13 | FR-COST-021 (FR-CLS-005) | `test_TC_CLS_13_V4_phut_chiem_may` |
| 14 | V5 `include_depr` = 0: EQ_A 515,00 với cảnh báo "Khấu hao bị loại…"; EQ_C 1.500,00 | TC-CLS-14 | FR-COST-021 (FR-COST-007) | `test_TC_CLS_14_V5_khong_khau_hao` |
| 15 | Bốn ca, mỗi ca một lần tính có GLU và một dịch vụ khác: (a) xóa sản lượng GLU-B → "Hệ thống GLU-B thiếu sản lượng …"; (b) Qbn GLU-A = 0 → "… số kết quả trả bằng 0"; (c) xóa `avg_batch_size` GLU-A → "… dòng Theo mẻ (L04) … thiếu cỡ mẻ bình quân"; (d) tỷ trọng 60 / 30, không có sản lượng hệ thống → "Tổng tỷ trọng … 90%, khác 100%". GLU "Lỗi", dịch vụ khác "Thành công" | TC-CLS-15 | FR-COST-023, FR-CLS-003 | unit `test_TC_CLS_15_*` + site `test_TC_CLS_15_dung_dich_vu_GLU_tren_site` |
| 16 | V8: `low_volume` 12.900 → 1.060,27 không; 4.740 → 389,59 không; 1.900 → 156,16 có; dịch vụ có hệ thống 1.900 test → "Cảnh báo", `low_volume_warning`. EQ_A loại `compliance_required`, hồ sơ hết hạn → `run_warnings` chứa "EQ_A", lần tính "Đã tính" | TC-CLS-37 | FR-COST-025, FR-CMP-006 | unit + site `test_TC_CLS_37_canh_bao_tren_lan_tinh` |
| 17 | Tính GLU trên site; `capture_snapshot`; sửa NC QC Plan (số mức 3) và hồ sơ tuân thủ EQ_A (chi phí 16.000.000); `snapshot.reproduce` trùng từng đồng với NC Service Cost đã lưu (mọi `direct_*`, `eqa_cost`, k, từng dòng); tính lại trực tiếp từ CSDL thì khác; `get_explanation` có `test_system`, `cost_level`, `k_factor` (dòng nhân k), `divisor_label`, `divisor_value`, `divisor_source` khác trống ở **mọi** dòng cận lâm sàng và khối k đủ Qbn, Qnk, Qchuan, Qlai, Qngk, h | TC-CLS-38 | FR-COST-031, FR-COST-032, NFR-CPL-003, NFR-REL-001 | site `test_TC_CLS_38_tai_lap_tu_anh_chup` |
| 18 | Lần tính có GLU và một dịch vụ lâm sàng: `ServiceResult.volume` của GLU = 16.000 dù NC Service Volume của GLU ghi 15.800; điểm cắm `allocate` (test double) nhận 16.000; `NC Service Cost.volume` = 16.000 | TC-CLS-51 | FR-COST-024 | unit `test_TC_CLS_51_san_luong_16000` + site `test_TC_CLS_51_san_luong_tren_site` |
| 19 | Quyền: NC Test System Cost theo cha — NC Clinician không đọc NC Service Cost (có bảng con), NC Auditor đọc được, `start_costing` → PermissionError | — | FR-ACC-002, FR-ACC-007 | `test_quyen_test_system_cost_clinician_va_auditor` |
| 20 | Dịch vụ thường trong cùng lần tính cho kết quả như FEAT-015 (test FEAT-015 xanh không sửa) | — | FR-COST-003 | toàn bộ `run-tests --app normcore` |

Ngưỡng golden: tiền khớp 2 chữ số, k khớp 6 chữ số, đơn giá phút 4 chữ số. Test golden **import** `docs/golden/golden_cls.py` (không chép số) và so cả với số của `test-cases.md` mục 2A.2, 2A.3.

## 6. Test và độ phủ
- Đơn vị: `tests/unit/test_costing_cls.py` (mọi nhánh `aux_counts`, `compliance_annual`, `per_result` ba tiêu chí, `norm_line_cost` năm cấp, `shares`, `validate` từng lỗi, `low_volume`, `cost_service` "Lỗi"/"Cảnh báo"/thành công, `group_by_system`), `test_costing_snapshot.py` (khứ hồi `to_plain`/`from_plain`, `digest` ổn định, `reproduce`), `test_costing_engine.py` thêm ca `paraclinical` và `cost_category`.
- Golden: `tests/golden/test_cls_golden.py` dựng `ClsServiceInput` từ `golden_cls.ITEM`, `EQUIP`, `USAGE`, `SYSTEMS`, `NORM`, `IQC`, `CAL`, `EQA`, `PARAM`, `KTV_RATE` (hàm dựng trong `tests/golden/cls_fixture.py`), so từng dòng với `golden_cls.system_lines`, `service_direct`, `compliance_annual`, `equipment_annual`, `per_result`, `low_volume`. V2 tạm đổi `COSTING_DATE`/`expired_mode` qua tham số, không sửa golden.
- Site: `nc_costing_run/test_nc_costing_cls.py` dựng bộ dữ liệu vàng 2A trên site bằng `tests/cls_fixtures.py::make_cls_golden()` (dịch vụ GLU, khoa XN, EQ_A, EQ_B, hai hệ thống, hai bộ định mức "Đã khóa", kế hoạch chất lượng, chương trình ngoại kiểm 21 dịch vụ, hồ sơ, sản lượng; thêm hệ thống phụ trên EQ_A và EQ_B với 288.000 và 96.000 kết quả để Qtb = 300.000 và 100.000 — ASM-036-10).
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90`.

## 7. Điểm cắm cho FEAT khác
- FEAT-017: `ServiceResult.volume` (ΣQbn), `direct_by_category` (có `cost_category`); kiểm lại TC-CLS-51 khi `allocate` thật có (ASM-036-20).
- FEAT-018: `loader.capture_snapshot`, `snapshot.dumps/digest/reproduce`; chạy lại TC-CLS-38 với khóa thật (ASM-036-21).
- FEAT-037: `snapshot.sources` có xuất kho; `cls.system_lines` cho lượng tính được (BR-CLS-014).

## 8. Rủi ro
- BR-CLS chưa được chuyên gia rà (implementation-plan): cài đúng golden, không "sửa cho hợp lý".
- Dữ liệu site để Qtb = 300.000 cần hệ thống phụ; sai số liệu fixture làm lệch L05, L07, EQ-P, EQ-E.
- Bảng giải trình hiển thị dòng theo hệ thống (một kết quả của hệ thống) còn tổng dịch vụ là bình quân: dễ hiểu nhầm cộng dòng ≠ tổng → giao diện ghi rõ (ui-design).
- TC-CLS-38, TC-CLS-51 chưa kiểm được trọn vẹn đến khi có FEAT-018, FEAT-017 (ASM-036-20, 21).
- `scope_info` đổi dạng mục đủ điều kiện cho dịch vụ cận lâm sàng: test FEAT-015 dùng dịch vụ thường nên không đổi; test FEAT-031 về lọc bộ định mức phải còn xanh.

## 9. Ánh xạ BR → mã → golden

| BR | Hàm | Golden (`golden_cls.py`) |
| :-- | :-- | :-- |
| BR-CLS-001 | `cls.aux_counts`, `cls.k_factor` | `k_factor` |
| BR-CLS-002 | `cls.norm_line_cost` (RESULT), `pricing.unit_price_per_norm` | `system_lines` nhánh RESULT, `unit_price` |
| BR-CLS-003, 004, 005 | `cls.norm_line_cost` (TUBE, BATCH, DAY/PERIOD) | `system_lines` |
| BR-CLS-006, 007 | `cls.system_lines` (QC-N, QC-C) | `system_lines` vòng IQC, CAL |
| BR-CLS-008 | `cls.eqa_per_result`, `qc_plans.eqa_shares` | `service_direct` (eqa) |
| BR-CLS-009, BR-COST-004 | `cls.equipment_annual`, `cls.per_result`, `resources.machine_annual`, `resources.equipment_annual`, `resources.machine_hourly_rate` | `machine_annual`, `equipment_annual`, `per_result` |
| BR-CLS-010 | `cls.part_per_result`, `resources.equipment_annual` (tháng) | `part_per_result`, `equipment_annual` |
| BR-CLS-011 | `cls.compliance_annual` | `compliance_annual`, `_own_compliance` |
| BR-CLS-012 | `cls.power_per_result` | `power_per_result` |
| BR-CLS-013 | `cls.shares`, `cls.cost_service` | `service_direct` (weighted) |
| BR-CLS-016 | `cls.low_volume` | `low_volume` |
| BR-COST-002, 003 | `engine.direct_line` | `system_lines` (LABOR), golden_engine |
| BR-COST-011, 015 | (FEAT-017) nhận `ServiceResult.volume` = ΣQbn | — |
| BR-COST-016 | `resources.machine_annual(include_depr)` | `machine_annual(include_depr)` |
