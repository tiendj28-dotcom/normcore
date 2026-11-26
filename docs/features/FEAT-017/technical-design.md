# FEAT-017: Phân bổ hai cấp và đối soát (thiết kế kỹ thuật)

Issue NORM-43. Nguồn:
- `srs.md`: FR-COST-004, 005, 008, 009, 014; BR-COST-009, 010, 011, 015, 016; NFR-PERF-002.
- `use-cases.md`: UC-012 bước 4, 5, 7, 8 và các nhánh 4b, 8b.
- `data-model.md`: NC Service Cost Line, NC Reconciliation Line (trường bản 1.0), NC Costing Run, mục 4 (dòng "Lần tính giá, kết quả, đối soát"), mục 5.4 (điều kiện khóa).
- `ux-foundations.md`: SCR-DSK-024. `test-cases.md`: mục 2.1, 2.2, biến thể V1 và V5; TC-COST-02, 03, 05, 08, 10, 14, 16.
- Golden: `docs/golden/golden_engine.py:115-145` (`run`: tiêu chí cấp 2, cấp 1, cấp 2, đối soát).

Phụ thuộc đã DONE trên `origin/develop` `7663a38`:
- FEAT-015: `engine.ServiceResult`, `CostLine`, `finish_service`; `runner.run(allocate=…)`; điểm cắm `nc_costing_run.allocate_pools`; `loader.py`, `writer.py`; API `normcore/api/costing.py`.
- FEAT-016: NC Accounting Import "Đã chốt" và bảng `totals` theo (trung tâm, loại); NC Cost Center Driver và `get_driver_values`; NC Allocation Rule; NC Service Volume; `allocation_rules.driver_shares`.

Giả định ghi ở `docs/decisions/assumptions/FEAT-017.md` (ASM-017-01..11). Sửa thiết kế ghi ở `docs/decisions/amendments/AMD-017-01.md` (trường `allocation_warnings`). **Câu hỏi cho Lead ở mục 10 (Q1).** Chỉ T03 phải chờ Q1; T01 và T02 làm trước được.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-COST-004 | Phân bổ cấp 1 (BR-COST-010). Mỗi trung tâm hỗ trợ và mỗi loại chi phí có số kế toán khác 0 được chia một lần cho **mọi trung tâm lâm sàng**, theo quy tắc cấp 1 và tiêu chí của từng trung tâm. Không phân bổ vòng giữa các trung tâm hỗ trợ. |
| FR-COST-005 | Phân bổ cấp 2 (BR-COST-011). Tính trên mỗi (trung tâm lâm sàng, loại):<br>phần còn lại = max(số kế toán + phần nhận từ cấp 1 − Σ chi phí trực tiếp cùng loại × sản lượng, 0).<br>Phần của một ca dịch vụ = phần còn lại × tiêu chí của dịch vụ ÷ tổng tiêu chí ÷ sản lượng.<br>Mỗi phần tạo một dòng "Phân bổ" trên NC Service Cost Line. Giá thành tính lại qua `engine.finish_service` (đã có). |
| FR-COST-008 | Sau phân bổ, lập NC Reconciliation Line theo (trung tâm lâm sàng, loại), không có MANAGEMENT. Mỗi dòng có số đã tính, số kế toán, chênh lệch tuyệt đối, chênh lệch phần trăm (BR-COST-015). Màn hình: SCR-DSK-024. |
| FR-COST-009 | Đánh dấu `over_tolerance` theo BR-COST-015 (a), (b), với ngưỡng `reconciliation_tolerance` của bộ tham số. NC Finance ghi `explanation`. Thao tác **Khóa** từ chối khi còn dòng vượt ngưỡng chưa có giải trình (data-model 5.4, nhánh 8b). |
| FR-COST-014 | Dịch vụ có sản lượng 0 hoặc thiếu sản lượng: không nhận phân bổ cấp 2 và không góp vào tổng tiêu chí. Thêm cảnh báo vào `calc_message`; chi phí trực tiếp và giá vẫn tính (ASM-017-02). |
| NFR-PERF-002 (TC-COST-14) | 500 dịch vụ, 50.000 dòng định mức tính xong trong 5 phút, chạy nền, có tiến độ. Đo thời gian thật và ghi vào implementation-log. |

**Không làm ở FEAT này:**
- Ảnh chụp đầu vào, nhân bản, so sánh hai lần tính (FR-COST-011..013, FEAT-018). Ở FEAT này **Khóa** chỉ kiểm điều kiện đối soát rồi đặt trạng thái "Đã khóa". FEAT-018 cắm ảnh chụp vào cùng hàm này (ASM-017-07).
- Đối soát vật chất và sản lượng, cùng các trường **[1.1]** của NC Reconciliation Line (`recon_type`, `department`, `item`, `technical_service`, `calculated_qty`, `actual_qty`, `recon_status`). Phần này thuộc FEAT-037, và FEAT-037 sẽ mở rộng `reconcile.py`.
- Dịch vụ cận lâm sàng dùng tổng số kết quả trả làm sản lượng (UC-012 bước 4 [1.1], nhánh 4i). Phần này thuộc FEAT-036. FEAT-017 lấy sản lượng từ `ServiceResult.volume`, vì vậy FEAT-036 chỉ cần đặt đúng `volume`.
- TBD-14 (loại chi phí của ngoại kiểm, thuê máy): FEAT-036 và FEAT-037.

## 2. DocType

### 2.1 NC Reconciliation Line (mới, DocType độc lập, module NC Costing)

Đã khai trong `data-model.md` mục 3 và ER `NC_Costing_Run ||--o{ NC_Reconciliation_Line`. Cài đặt:
- `istable` = 0, `autoname` = `hash`, `track_changes` = 1.
- `title_field` = `cost_category`; `sort_field` = `cost_center`.
- Chỉ trường bản 1.0. Các trường [1.1] để FEAT-037.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| costing_run | Lần tính giá | Link NC Costing Run | Có | `in_list_view`, `in_standard_filter`, chỉ đọc |
| cost_center | Trung tâm chi phí | Link NC Cost Center | Có | `in_list_view`, `in_standard_filter`, chỉ đọc |
| cost_category | Loại chi phí | Select LABOR / DRUG_SUPPLY / DEPRECIATION / UTILITY | Có | `in_list_view`, chỉ đọc. Không có MANAGEMENT (BR-COST-015) |
| costed_amount | Số đã tính | Currency | | Chỉ đọc |
| accounting_amount | Số kế toán | Currency | | Chỉ đọc. Gồm phần nhận từ cấp 1 |
| variance | Chênh lệch | Currency | | Chỉ đọc. = số đã tính − số kế toán |
| variance_pct | Chênh lệch (%) | Float, `precision` 2 | | Chỉ đọc. Trống khi số kế toán = 0 (ASM-017-06) |
| over_tolerance | Vượt ngưỡng | Check | | Chỉ đọc, `in_list_view` |
| explanation | Giải trình | Small Text | | Trường duy nhất sửa được, chỉ khi lần tính "Đã tính" |

**Quyền.** Theo dòng "Lần tính giá, kết quả, đối soát": NC Finance đọc, sửa, tạo; NC Director, NC Admin, NC Auditor chỉ đọc; vai trò khác không có quyền; không ai xóa. Quy ước `check_conventions.py` hiểu W là read + write + create.

**Controller `NCReconciliationLine`:**
- `before_insert`: nếu không có `self.flags.from_costing` thì từ chối với "Dòng đối soát do hệ thống tạo khi tính giá". Nhờ vậy NC Finance có quyền create nhưng không tạo tay được dòng.
- `validate` với bản ghi đã có:
  - đổi bất kỳ trường nào ngoài `explanation` → "Chỉ sửa được giải trình của dòng đối soát";
  - đổi `explanation` khi lần tính khác "Đã tính" → "Lần tính giá ở trạng thái {0}, không sửa được giải trình";
  - `explanation` được `strip()` trước khi lưu.
- `on_trash`: chỉ cho xóa khi có `flags.from_costing`. Bảo đảm DI-07 cho lần tính đã khóa.

Lý do kiểm ở controller: mọi đường ghi đều đi qua đây, kể cả `frappe.client.set_value`.

### 2.2 NC Costing Run (mở rộng, AMD-017-01)

| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| allocation_warnings **(mới)** | Cảnh báo phân bổ | Small Text | Chỉ đọc, sau `progress`. Do `execute_costing` ghi, mỗi cảnh báo một dòng (ASM-017-01). Trống khi không có cảnh báo |

Chỉ thêm trường nên không cần patch dữ liệu. Không đổi trạng thái hay luồng của FEAT-015. "Đã khóa" đã nằm ngoài `RUNNABLE` và `EDITABLE_INPUTS`, nên lần tính đã khóa tự bị từ chối khi tính lại hay sửa đầu vào.

### 2.3 NC Service Cost, NC Service Cost Line

Không đổi cấu trúc. FEAT-017 ghi dòng `line_type` = "Phân bổ" với:
- `component` = loại chi phí;
- `allocation_rule`;
- `driver_value`: tiêu chí năm của dịch vụ;
- `driver_total`: tổng tiêu chí của trung tâm;
- `pool_amount`: phần còn lại của (trung tâm, loại);
- `amount`: số tiền một ca;
- `rate_source` = "Cấp 2 · {tiêu chí}".

`alloc_*` và giá do `writer` ghi như FEAT-015. `calc_message` thêm câu cảnh báo FR-COST-014 khi cần.

## 3. Logic thuần (`normcore/costing/`, không import `frappe`, dùng Decimal và ROUND_HALF_UP)

### 3.1 `allocation.py` (mới)

```python
CATEGORIES = ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT")   # = accounting.ALLOCATABLE
VOLUME_WARNING = "Sản lượng bằng 0 hoặc chưa có: không phân bổ chi phí chung (FR-COST-014)"

@dataclass(frozen=True) class Rule:
    name: str; level: str; cost_category: str; driver: str; cost_center: str | None   # level: allocation_rules.LEVEL1/LEVEL2

@dataclass(frozen=True) class ServiceDrivers:
    service: str; department: str; cost_center: str | None
    labor_min_per_case: Decimal   # Σ applied_qty × headcount, dòng LABOR không loại trừ
    machine_min_per_case: Decimal # Σ applied_qty, dòng EQUIPMENT không loại trừ

@dataclass(frozen=True) class AllocationInput:
    accounting: Mapping[tuple[str, str], Decimal]  # (trung tâm, loại) → số tiền: NC Accounting Import Total
    center_types: Mapping[str, str]                # trung tâm → "Lâm sàng" / "Hỗ trợ"
    center_drivers: Mapping[str, Mapping[str, Decimal]]  # trung tâm → {"HEADCOUNT","AREA","REVENUE"}
    rules: tuple[Rule, ...]
    include_depreciation: bool

@dataclass(frozen=True) class Pool:              # một (trung tâm lâm sàng, loại) sau cấp 1
    cost_center: str; cost_category: str
    own_amount: Decimal; received: Decimal; pool_in: Decimal   # pool_in = own + received
    costed: Decimal; remainder: Decimal
    rule: str | None; driver: str | None; driver_total: Decimal | None

@dataclass(frozen=True) class AllocationOutcome:
    lines: dict           # (dịch vụ, khoa) → list[CostLine "Phân bổ"]
    received: dict        # (trung tâm lâm sàng, loại) → Decimal
    pools: list[Pool]
    warnings: list[str]
```

| Hàm | Quy tắc | Golden |
| :-- | :-- | :-- |
| `service_drivers(inp: ServiceInput, cost_center) -> ServiceDrivers` | Đếm phút trên một ca từ `NormLine`: LABOR tính `applied_qty × headcount`, EQUIPMENT tính `applied_qty`; bỏ dòng `excluded`. `applied_qty` dùng `engine.applied_qty` (BR-COST-007) | `labor_min`, `mach_min` (dòng 120–121, trước khi nhân sản lượng) |
| `service_driver_value(drivers, result, driver) -> Decimal` | Gọi `v` = `result.volume`; `None` coi là 0.<br>LABOR_MIN = `labor_min_per_case × v`<br>MACHINE_MIN = `machine_min_per_case × v`<br>VOLUME = `v`<br>DIRECT_COST = `result.direct_total × v` (BR-COST-009) | `drv` (dòng 122) |
| `find_rule(rules, level, category, center) -> Rule \| None` | Quy tắc có `cost_center` = trung tâm thắng quy tắc chung (`cost_center` trống), theo data-model NC Allocation Rule. Nhiều quy tắc cùng mức ưu tiên thì lấy tên nhỏ nhất và cảnh báo (ASM-017-09) | |
| `level1(inp, members) -> (received, warnings)` | `members`: {trung tâm lâm sàng: [(ServiceDrivers, ServiceResult)]}. Với mỗi trung tâm hỗ trợ `S`, mỗi loại `c` có `A = accounting[S, c] ≠ 0`:<br>• lấy quy tắc cấp 1;<br>• nếu không có quy tắc hoặc tổng tiêu chí = 0 thì cảnh báo và không chia;<br>• có thì tỷ lệ = `allocation_rules.driver_shares(giá trị theo trung tâm lâm sàng)` và `received[k, c] += r2(A × tỷ lệ_k)`.<br>Giá trị tiêu chí: HEADCOUNT, AREA, REVENUE lấy từ `center_drivers` (thiếu = 0); LABOR_MIN, MACHINE_MIN, VOLUME, DIRECT_COST là tổng `service_driver_value` của các dịch vụ thuộc trung tâm trong lần tính (ASM-017-05). Trung tâm lâm sàng = mọi trung tâm có `center_types` "Lâm sàng" | `share`, `recv` (dòng 124–126): nhân tỷ lệ rồi `r2`, đúng thứ tự golden |
| `level2(inp, members, received) -> (lines, pools, warnings)` | Với mỗi trung tâm lâm sàng có ít nhất một dịch vụ trong `members`, mỗi loại `c` thuộc hợp của {loại có số kế toán, loại nhận từ cấp 1, loại có chi phí trực tiếp}. Bỏ DEPRECIATION khi `include_depreciation` sai (BR-COST-016).<br>• `pool_in = own + received`<br>• `costed = Σ direct_by_category[c] × v`<br>• `remainder = max(pool_in − costed, 0)`<br>Nếu `remainder > 0` mà không có quy tắc cấp 2 thì cảnh báo và không chia. Có quy tắc thì `d_s = service_driver_value`, `total = Σ d_s`.<br>Với dịch vụ có `v > 0` và `total ≠ 0`: `amount = r2(remainder × d_s / total / v)`, ghi một `CostLine("Phân bổ", c, amount, allocation_rule, driver_value=d_s, driver_total=total, pool_amount=remainder, rate_source="Cấp 2 · {driver}")`. Dòng vẫn ghi khi `amount` = 0, để thấy phần còn lại bằng 0 (TC-COST-16).<br>Dịch vụ `v = 0` hoặc thiếu: không có dòng (FR-COST-014).<br>`total = 0` (ví dụ không dịch vụ nào có phút máy): không chia, cảnh báo | `pool_in`, `costed`, `remainder`, `alloc` (dòng 132–137) |
| `allocate(results, drivers, inp) -> AllocationOutcome` | Gom `results` (bỏ dịch vụ "Lỗi", ASM-017-04) theo `drivers[(s, d)].cost_center`; dịch vụ không có trung tâm thì cảnh báo và bỏ. Gọi `level1` rồi `level2`. Thứ tự tất định: trung tâm, loại theo `CATEGORIES`, dịch vụ, khoa (NFR-REL-002) | `run` |
| `mark_volume(result) -> ServiceResult` | Dịch vụ không "Lỗi" có `volume` None hoặc ≤ 0 thì nối `VOLUME_WARNING` vào `message` (ngăn bằng "; "); `status` giữ nguyên (ASM-017-02). Dịch vụ khác trả nguyên | |

### 3.2 `reconcile.py` (mới)

```python
@dataclass(frozen=True) class ReconRow:
    cost_center: str; cost_category: str
    costed: Decimal | None; accounting: Decimal | None; remainder: Decimal | None
    variance: Decimal | None; variance_pct: Decimal | None; over_tolerance: bool | None
    skipped: bool = False     # BR-COST-016: DEPRECIATION khi loại giá không kết cấu khấu hao
```

| Hàm | Quy tắc | Golden |
| :-- | :-- | :-- |
| `reconcile(pools, tolerance, include_depreciation, depr_centers=()) -> list[ReconRow]` | Bỏ MANAGEMENT.<br>`variance = costed − accounting`.<br>`variance_pct = r2(variance / accounting × 100)` khi `accounting ≠ 0`; ngược lại `None`.<br>`over = pct > tol` hoặc (`cat == DRUG_SUPPLY` và `pct < −tol`). Khi `pct` là `None` thì `over = costed > 0` (ASM-017-06).<br>`costed` và `accounting` đều 0 thì không lập dòng.<br>Khi `include_depreciation` sai, trung tâm có số kế toán DEPRECIATION cho một hàng `skipped=True`, các số `None`, giống tuple `None` của golden. Hàng này không ghi CSDL.<br>`tolerance`: Percent, ví dụ 10 nghĩa là 10% | dòng 129–145 (`pct`, `over`, MANAGEMENT `continue`, nhánh `--no-depr`) |
| `lock_blockers(lines) -> list[str]` | `lines`: dict `cost_center`, `cost_category`, `over_tolerance`, `explanation`. Trả nhãn "K01 · DRUG_SUPPLY" cho mọi dòng `over_tolerance` có `explanation` trống sau `strip()` (FR-COST-009, data-model 5.4). FEAT-037 thêm dòng Vật chất vào cùng hàm | |

### 3.3 Ánh xạ BR, mã, golden

| BR | Hàm | Golden |
| :-- | :-- | :-- |
| BR-COST-009 | `allocation.service_driver_value`, `level1` (tiêu chí theo trung tâm) | `drv`, `HEADCOUNT` |
| BR-COST-010 | `allocation.level1` + `allocation_rules.driver_shares` | dòng 124–126 |
| BR-COST-011 | `allocation.level2` | dòng 129–137 |
| BR-COST-015 | `reconcile.reconcile`, `lock_blockers` | dòng 138–145 |
| BR-COST-016 (phân bổ, đối soát) | `level2` bỏ DEPRECIATION; `reconcile` cho hàng `skipped` | dòng 131–132 |
| BR-COST-012 | `engine.finish_service` (FEAT-015, không đổi) | dòng 147 |

## 4. Lớp CSDL và controller

### 4.1 `loader.py` (mở rộng)

`allocation_context(run, ctx) -> AllocCtx` đọc một lần cho cả lần tính:
- `accounting`: NC Accounting Import Total của `run.accounting_import`.
- `center_types`: mọi NC Cost Center.
- `dept_center`: NC Department → `cost_center`.
- `center_drivers`: NC Cost Center Driver của `fiscal_year`, qua `get_driver_values` cho HEADCOUNT, AREA, REVENUE.
- `rules`: mọi NC Allocation Rule.
- `include_depreciation` = `ctx.pricing.include_depreciation`.
- `tolerance` = `reconciliation_tolerance` của bộ tham số.
- `drivers` = {} (điền dần khi nạp từng dịch vụ).
- `outcome` = None.

### 4.2 `nc_costing_run.py`

- `allocate_pools(results, actx=None)`: **giữ tên và đường dẫn**, vì `test_TC_COST_15_dong_giai_trinh_du_nguon` vá hàm này bằng `mock.patch(return_value=…)`.
  - `actx` là None thì trả {}.
  - Ngược lại `actx.outcome = allocation.allocate(results, actx.drivers, actx.input)` và trả `actx.outcome.lines`.
  - Khi bị vá, `outcome` vẫn None, nên không lập đối soát.
- `_run(eligible, progress)`:
  - tạo `actx = loader.allocation_context(self, ctx)`;
  - hàm `load` bọc `loader.load_service` và ghi `actx.drivers[(s, d)] = allocation.service_drivers(inp, actx.dept_center.get(d))`;
  - `allocate=lambda rs: allocate_pools(rs, actx)`;
  - sau `runner.run`, áp `allocation.mark_volume` cho từng kết quả;
  - lưu `self._allocation = actx` rồi trả danh sách như cũ.
- `execute_costing` (pha ghi, trong cùng savepoint):
  - xóa NC Reconciliation Line cũ của lần tính (cùng lúc xóa NC Service Cost cũ, `flags.from_costing`). Giải trình cũ mất theo (ASM-017-08);
  - `writer.write_results` như cũ;
  - khi `doc._allocation.outcome` có thì `writer.write_reconciliation(doc, reconcile.reconcile(...))` (bỏ hàng `skipped`);
  - `db_set("allocation_warnings", "\n".join(warnings) or None)`.
  - Tiến độ: pha tính 0–90%, xong pha ghi thì 100% (`progress(i, n)` đổi tỷ lệ thành `int(i × 90 / n)`).
- `lock_costing()` (`@frappe.whitelist()`, doc method):
  - kiểm quyền `write`;
  - `status` ≠ "Đã tính" → "Chỉ khóa được lần tính giá ở trạng thái Đã tính";
  - `blockers = reconcile.lock_blockers(…NC Reconciliation Line của lần tính…)`; khác rỗng thì từ chối với "Còn {n} dòng đối soát vượt ngưỡng chưa có giải trình: {danh sách}";
  - qua được thì `db_set("status", "Đã khóa")` (`core/audit.py` ghi sự kiện "Khóa" như các trạng thái khác) và trả "Đã khóa".
  - FEAT-018 thêm ảnh chụp trước `db_set` (ASM-017-07).

### 4.3 `writer.py` (mở rộng)

`write_reconciliation(run, rows) -> list[str]`: mỗi `ReconRow` không `skipped` thành một NC Reconciliation Line, với `flags.from_costing = True` và `insert(ignore_permissions=True)`. Quyền đã kiểm ở `run_costing`. Ghi số bằng `float`.

**Hiệu năng (TC-COST-14).** Nếu số đo vượt 5 phút, được đổi cách ghi dòng con của NC Service Cost sang `frappe.db.bulk_insert`. Kết quả ghi phải giữ nguyên, và test site của FEAT-015 phải vẫn xanh. Ghi số đo trước và sau vào implementation-log.

## 5. API (`normcore/api/costing.py`, `@frappe.whitelist()`, kiểm quyền tường minh)

| Hàm | Tham số | Kết quả | Quyền, lỗi |
| :-- | :-- | :-- | :-- |
| `get_reconciliation(run)` | tên lần tính | `{"run", "status", "tolerance", "include_depreciation", "partial_scope": bool, "warnings": [..], "lines": [{name, cost_center, cost_center_name, cost_category, category_label, costed_amount, accounting_amount, variance, variance_pct, remainder, over_tolerance, explanation, needs_explanation}], "blocked": n, "can_explain": bool, "can_lock": bool}` | `read` trên NC Costing Run.<br>`partial_scope` = có phạm vi khoa hoặc dịch vụ.<br>`remainder = max(accounting − costed, 0)`.<br>`needs_explanation` = vượt ngưỡng mà chưa có giải trình.<br>`can_explain` = có quyền `write` NC Reconciliation Line và status "Đã tính".<br>`can_lock` = có quyền `write` NC Costing Run, status "Đã tính" và `blocked` = 0.<br>Thứ tự: trung tâm, loại theo `CATEGORIES` |
| `save_explanation(line, explanation)` | tên dòng, chuỗi | `{"name", "explanation", "needs_explanation", "blocked"}`. `blocked` là số dòng còn chặn của lần tính | `has_permission("NC Reconciliation Line", "write", doc)`. Lưu bằng `doc.save()` để controller mục 2.1 kiểm trạng thái |
| `lock_run(run)` | | `{"status"}` | Gọi `NCCostingRun.lock_costing()`. Lỗi trả nguyên văn |
| `get_run_results` (đã có) | | thêm `has_volume_warning` mỗi dòng (`VOLUME_WARNING` có trong `calc_message`) và `recon_blocked` (số dòng chặn) | không đổi |
| `get_explanation` (đã có) | | `allocation_lines` lấy dòng thật. `notes` giữ nguyên chuỗi `NOTE_NO_ALLOCATION` khi không có dòng phân bổ, vì `api/test_costing.py:86` so khớp nguyên văn (ASM-017-10); thêm `VOLUME_WARNING` khi có | không đổi |

## 6. Tiêu chí nghiệm thu

Lớp test: `golden` = `tests/golden/test_allocation_golden.py` (dựng đầu vào từ `golden_engine`, không chép số); `site` = `nc_costing/doctype/nc_costing_run/test_nc_costing_run_allocation.py` (tệp mới, không sửa tệp test cũ).

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Dữ liệu vàng: K01 nhận LABOR 120.000.000, MANAGEMENT 160.000.000 (= `golden_engine.run()[2]`); HC không nhận. Phần của K02 (30/50) kiểm ở test đơn vị #9, không phải số golden | TC-COST-02 | FR-COST-004 | golden `test_TC_COST_02_cap1_K01_nhan_LABOR_MANAGEMENT` |
| 2 | Năm pool của K01: `remainder` khớp bảng mục 2.2 (365.061.600; 73.000.000; 15.151.520; 34.000.000; 260.000.000). `alloc` từng loại của DV-TEST-A, DV-TEST-B khớp `golden_engine.run()[0][s]["alloc"]`. Giá thành sau `finish_service` 287.745,46 và 88.169,70 | TC-COST-03 | FR-COST-005 | golden `test_TC_COST_03_phan_con_lai_va_phan_bo_theo_ca` |
| 3 | `reconcile` cho đúng 4 dòng LABOR, DRUG_SUPPLY, DEPRECIATION, UTILITY, khớp `golden_engine.run()[1]` (số đã tính, số kế toán, %, vượt ngưỡng). Chỉ DRUG_SUPPLY vượt ngưỡng (−28,08). Không có MANAGEMENT | TC-COST-05 | FR-COST-008, 009 | golden `test_TC_COST_05_bon_dong_doi_soat` |
| 4 | V5 (sản lượng DV-TEST-B = 0, so với golden chạy với `VOLUME` đã vá):<br>• DV-TEST-B: chi phí trực tiếp 32.822,44, mọi `alloc` = 0, không có dòng phân bổ, `message` chứa `VOLUME_WARNING`;<br>• DV-TEST-A: `alloc` khớp golden V5 | TC-COST-08 | FR-COST-014 | golden `test_TC_COST_08_V5_san_luong_bang_0` |
| 5 | Trên site, đủ dữ liệu vàng (trung tâm K01, HC, K02, tiêu chí, quy tắc, lần nhập theo golden), tính xong:<br>• có 4 NC Reconciliation Line, dòng DRUG_SUPPLY `over_tolerance` = 1;<br>• `lock_costing()` từ chối, lỗi nêu "DRUG_SUPPLY", trạng thái giữ "Đã tính";<br>• `save_explanation` rồi `lock_costing()` cho "Đã khóa";<br>• sau khóa: `save_explanation` bị từ chối, `run_costing` bị từ chối | TC-COST-10 | FR-COST-009 | site `test_TC_COST_10_khoa_khi_DRUG_SUPPLY_chua_giai_trinh` |
| 6 | 500 dịch vụ, 50.000 dòng định mức sinh tự động (`bulk_insert`):<br>• `run_costing()` gọi `frappe.enqueue(queue="long")` và đặt "Đang tính";<br>• `execute_costing(..., background=True)` chạy trong test xong dưới 300 giây (đo `time.monotonic`), `progress` tăng dần tới 100, trạng thái "Đã tính", có 500 NC Service Cost | TC-COST-14 | NFR-PERF-002, FR-COST-015 | site `test_TC_COST_14_500_dich_vu_50000_dong_duoi_5_phut` (tệp riêng `tests/test_costing_perf.py`) |
| 7 | Số kế toán DEPRECIATION của K01 = 200.000.000:<br>• `remainder` = 0;<br>• `alloc` DEPRECIATION của cả hai dịch vụ = 0, vẫn có dòng phân bổ với `amount` 0;<br>• `variance_pct` = 42,42, `over_tolerance` đúng; khớp golden đã vá | TC-COST-16 | FR-COST-005 | golden `test_TC_COST_16_phan_con_lai_am_lay_0` |
| 8 | V1 (`include_depreciation` = 0): không có `alloc` DEPRECIATION; `reconcile` cho hàng DEPRECIATION `skipped` (golden `run(False)` cho tuple `None`); giá thành DV-TEST-A 224.109,10 | (TC-COST-06 phần phân bổ) | FR-COST-007 | golden `test_V1_khong_phan_bo_khong_doi_soat_khau_hao` |
| 9 | Đơn vị cho `find_rule` (cụ thể thắng chung; trùng thì lấy tên nhỏ và cảnh báo); thiếu quy tắc cấp 1 hoặc cấp 2 thì có cảnh báo và không chia; `total` = 0; dịch vụ "Lỗi" bị bỏ; dịch vụ không có trung tâm; `accounting` = 0 mà `costed` > 0 thì `pct` None, vượt ngưỡng; tiêu chí cấp 1 DIRECT_COST/VOLUME; `lock_blockers` với giải trình rỗng hoặc chỉ có khoảng trắng | — | FR-COST-004, 005, 009 | `tests/unit/test_allocation.py`, `test_reconcile.py` |
| 10 | Quyền NC Reconciliation Line:<br>• NC Clinician không đọc được, `get_reconciliation` → PermissionError;<br>• NC Auditor đọc được, `save_explanation` và `lock_run` → PermissionError;<br>• NC Finance tạo tay một dòng → bị từ chối (`from_costing`);<br>• sửa `costed_amount` qua `frappe.client.set_value` → bị từ chối;<br>• DocPerm khớp ma trận | — | FR-ACC-002, FR-ACC-007 | site `test_quyen_doi_soat_*` |
| 11 | Test cũ của FEAT-015 xanh mà không sửa: `test_nc_costing_run.py`, `api/test_costing.py`, `test_feat_039.py`, `test_nc_audit_event.py`, `test_nc_costing_parameter_set.py`. Không thêm dòng phân bổ khi không có quy tắc | — | — | lệnh T04, T05, T10 |

## 7. Test và độ phủ

- Đơn vị: `tests/unit/test_allocation.py`, `test_reconcile.py`. Phủ mọi nhánh mục 3.
- Golden: `tests/golden/test_allocation_golden.py`.
  - Dựng `ServiceResult` qua `engine.cost_service` từ đầu vào vàng như `test_costing_golden.py`; dùng lại helper của tệp đó nếu có, không chép số.
  - `AllocationInput` lấy từ `golden_engine.ACCOUNTING`, `HEADCOUNT`, `L1_DRIVER`, `L2_DRIVER`.
  - Biến thể V5 và TC-COST-16 vá `golden_engine.VOLUME`, `ACCOUNTING` bằng `mock.patch.dict` rồi trả lại.
- Site: `test_nc_costing_run_allocation.py` (TC-COST-10, quyền, `allocation_warnings`, xóa dòng cũ khi tính lại), `api/test_costing_reconciliation.py` (`get_reconciliation`, `save_explanation`, `lock_run`), `tests/test_costing_perf.py` (TC-COST-14).
- Fixture site mới: `tests/costing_fixtures.py::make_golden_allocation(dept)`. Hàm này gắn `cost_center` của khoa vàng vào trung tâm có số K01 và tạo HC, K02, NC Cost Center Driver năm 2026 (20, 30), quy tắc theo `L1_DRIVER`/`L2_DRIVER`, lần nhập riêng "Đã chốt" có `totals` bằng `golden_engine.ACCOUNTING`. Chỉ thêm hàm, không sửa hàm cũ.
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90`.

## 8. Rủi ro

- **Phạm vi một phần.** Phần còn lại chỉ chia cho dịch vụ trong lần tính, nên giá cao hơn so với tính toàn viện (ASM-017-03). Bảng đối soát và bảng giải trình có dải ghi chú khi `partial_scope`.
- **Thiếu quy tắc hoặc tiêu chí** chỉ cảnh báo, không chặn (ASM-017-01), nên người dùng có thể bỏ qua. Cảnh báo hiện ở dải vàng trên SCR-DSK-022 và SCR-DSK-024.
- **TC-COST-14.** Ghi 50.000 dòng con qua ORM có thể vượt 5 phút. Cách xử lý ở mục 4.3; đo thật ở T06.
- **Đối soát khi bỏ qua dịch vụ "Lỗi".** Số đã tính thiếu phần của dịch vụ lỗi, nên chênh lệch phóng đại. Trạng thái "Lỗi" đã hiện trên SCR-DSK-022.

## 9. Điểm cắm cho FEAT khác

- **FEAT-018:** `lock_costing` thêm ảnh chụp trước `db_set`; nhân bản bỏ qua NC Reconciliation Line.
- **FEAT-036:** đặt `ServiceResult.volume` = tổng số kết quả trả cho dịch vụ cận lâm sàng. `mark_volume` không áp cho dịch vụ có hệ thống xét nghiệm (nhánh 4i dừng tính), nên FEAT-036 thêm điều kiện này.
- **FEAT-037:** thêm trường [1.1] cho NC Reconciliation Line (`recon_type` mặc định Tài chính cho dòng FEAT-017); mở rộng `reconcile.lock_blockers`; thêm liên kết SCR-DSK-038 trên SCR-DSK-024.

## 10. Câu hỏi cho Lead

**Q1: Sửa tệp chung `scripts/check_conventions.py` cho DocType mới.** `check_permissions` báo lỗi `[NC-08]` với mọi DocType chưa có trong `DOCTYPE_ROW` (`scripts/check_conventions.py:65`). NC Reconciliation Line là DocType mới nên cần thêm một dòng. Quy tắc tránh conflict số 5 trong mô tả issue yêu cầu báo Lead trước khi sửa tệp chung.
- **PA1 (đề xuất):** thêm đúng một dòng `"NC Reconciliation Line": "Lần tính giá, kết quả, đối soát",` vào `DOCTYPE_ROW`. Không đổi `MATRIX`, không đổi dòng nào khác. Tiền lệ: FEAT-015 T08.
- PA2: không thêm dòng. `check_conventions.py` sẽ đỏ và trái DoD.
