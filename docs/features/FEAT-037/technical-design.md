# FEAT-037 — Đối soát vật chất và sản lượng; thiếu dữ liệu; độ nhạy — Thiết kế kỹ thuật

Issue NORM-46. Nguồn: `srs.md` FR-COST-026..030, FR-OUT-012; BR-CLS-014, BR-CLS-015 (và BR-CLS-001..008, BR-COST-007 cho lượng); A-08; TBD-14; `use-cases.md` UC-023, UC-024; `data-model.md` NC Reconciliation Line **[1.1]**, ma trận mục 4 dòng "Lần tính giá, kết quả, đối soát"; `architecture.md` mục cây thư mục (`public/js/sensitivity/`) và ADR-010 **[1.1]** (trang `sensitivity` chỉ đọc); `ux-foundations.md` SCR-DSK-024 **[1.1]**, SCR-DSK-038, 039, 040; `design.md` "Kết quả thử [1.1]"; golden `docs/golden/golden_cls.py:196` `material_recon`, `:207` `volume_recon`; `test-cases.md` mục 2A.3 (V6, V7), TC-CLS-16..19, 39, 40.

Phụ thuộc (DONE trên `origin/develop` `b22ab47`): FEAT-017 (NC Reconciliation Line, `costing/reconcile.py`, `lock_costing`, report "NC Reconciliation", `save_explanation`), FEAT-036 (`costing/cls.py`, `ClsServiceInput`, `k_factor`, `aux_counts`, `snapshot.recompute`, fixture `tests/cls_fixtures.py::make_cls_golden`), FEAT-018 (khóa có ảnh chụp, `loader.capture_snapshot`, `snapshot.diff_rows`), FEAT-035 (NC Stock Issue Actual, NC Test System Volume), FEAT-011 (`material_recon_tolerance`, `volume_recon_tolerance` của NC Costing Parameter Set — trường đã có).

Giả định: `docs/decisions/assumptions/FEAT-037.md` (ASM-037-01..18). Không có AMD: các trường thêm đã có trong `data-model.md` [1.1]; bản 1.0 không ghi `cost_center`, `cost_category` là bắt buộc.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-COST-026 | Khi lần tính hoàn tất (pha ghi của `execute_costing`), lập dòng đối soát vật chất `recon_type` = "Vật chất" cho mỗi (khoa, mặt hàng) của dịch vụ cận lâm sàng: `calculated_qty`, `actual_qty` (đơn vị định mức), `variance_pct`. Lượng tính được theo BR-CLS-014, khớp `golden_cls.material_recon` |
| FR-COST-027 | `over_tolerance` = \|%\| > `material_recon_tolerance` (mặc định 5). Dòng "Vượt ngưỡng" chưa có `explanation` chặn `lock_costing` |
| FR-COST-028 (Should) | Dòng `recon_type` = "Sản lượng" cho mỗi (dịch vụ, khoa) cận lâm sàng: số kết quả trả với sản lượng HIS, `over_tolerance` = cảnh báo khi \|%\| > `volume_recon_tolerance` (mặc định 2). **Không chặn khóa** |
| FR-COST-029 | Khoa trong phạm vi không có NC Stock Issue Actual nào của năm → một dòng "Vật chất" `recon_status` = "Chưa đối soát" (không mặt hàng). Chỉ khóa được khi dòng có `explanation` (NC Finance xác nhận kèm lý do — ASM-037-06) |
| FR-COST-030 (Should) | API và trang `sensitivity` (SCR-DSK-040): tính lại giá thành của một dịch vụ từ ảnh chụp đầu vào của lần tính với giả định sản lượng, đơn giá hoặc hình thức có máy; **không ghi** gì vào CSDL |
| FR-OUT-012 | Script Report "NC Missing Data" (SCR-DSK-039): theo phạm vi (năm, kịch bản, ngày tính, bộ tham số, loại giá, khoa, dịch vụ), liệt kê dịch vụ thiếu đơn giá, thiếu sản lượng, thiếu bấm giờ, thiếu kế hoạch chất lượng, thiếu hồ sơ tuân thủ; chạy được khi chưa có lần tính |
| SCR-DSK-024 [1.1] | Report "NC Reconciliation" chỉ hiện dòng Tài chính; dải liên kết sang SCR-DSK-038; điều kiện khóa gồm cả vật chất |

**Không làm:** sửa công thức tính giá, phân bổ hay đối soát tài chính (FEAT-017 giữ nguyên); chốt TBD-14 (ASM-037-01); đối soát vật chất cho dịch vụ không có hệ thống xét nghiệm (BR-CLS-014 định nghĩa theo hệ thống — ASM-037-03); lưu kết quả thử độ nhạy.

## 2. DocType

### 2.1 NC Reconciliation Line (mở rộng, không tạo lại)

| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| recon_type **(mới)** | Loại đối soát | Select `Tài chính`/`Vật chất`/`Sản lượng` | `default` "Tài chính", `in_list_view`, `in_standard_filter`, `read_only`. Đặt sau `costing_run` |
| department **(mới)** | Khoa | Link NC Department | `depends_on: eval:doc.recon_type!='Tài chính'` |
| item **(mới)** | Mặt hàng | Link NC Item | `depends_on` Vật chất |
| technical_service **(mới)** | Dịch vụ | Link NC Technical Service | `depends_on` Sản lượng |
| calculated_qty **(mới)** | Lượng tính được | Float, precision 6 | Vật chất: đơn vị định mức; Sản lượng: số kết quả trả |
| actual_qty **(mới)** | Lượng thực tế | Float, precision 6 | Vật chất: xuất kho đã đổi về đơn vị định mức; Sản lượng: sản lượng HIS |
| recon_status **(mới)** | Tình trạng | Select `Đã đối soát`/`Chưa đối soát` | `default` "Đã đối soát" |
| cost_center | (đã có) | | `reqd` 1 → 0, thêm `mandatory_depends_on: eval:doc.recon_type=='Tài chính'` |
| cost_category | (đã có) | | như trên |

Mọi trường mới `read_only` (chỉ `explanation` sửa được — controller FEAT-017 đã chặn). Section "Đối soát vật chất, sản lượng" (`depends_on` ≠ Tài chính) chứa các trường mới.

Ánh xạ trường cho dòng vật chất / sản lượng (ASM-037-08):

| Trường | Vật chất | Vật chất, Chưa đối soát (cả khoa) | Sản lượng |
| :-- | :-- | :-- | :-- |
| cost_center | trung tâm của khoa (`NC Department.cost_center`, có thể trống) | như trên | như trên |
| cost_category | `DRUG_SUPPLY` | `DRUG_SUPPLY` | trống |
| item | mặt hàng | trống | trống |
| technical_service | trống | trống | dịch vụ |
| calculated_qty / actual_qty | lượng tính / xuất kho đổi đơn vị | trống / trống | số kết quả trả / HIS |
| variance_pct | `r2((actual − calc) ÷ actual × 100)` | trống | `r2((results − his) ÷ his × 100)` |
| variance, costed_amount, accounting_amount | trống (là tiền) | trống | trống |
| over_tolerance | \|%\| > ngưỡng vật chất | 0 | \|%\| > ngưỡng sản lượng |
| recon_status | Đã đối soát (hoặc Chưa đối soát theo mặt hàng — ASM-037-05) | Chưa đối soát | Đã đối soát |

Controller `nc_reconciliation_line.py`: thêm `validate` (bản mới tạo từ máy chủ) — `recon_type` = "Tài chính" thì `cost_center`, `cost_category` bắt buộc (giữ hành vi cũ). Không đổi luật "chỉ sửa `explanation`, chỉ khi lần tính Đã tính".

**Patch** `normcore/patches/backfill_reconciliation_type.py` (khai `patches.txt` mục `[post_model_sync]`): `UPDATE` dòng có `recon_type` trống → "Tài chính", `recon_status` trống → "Đã đối soát". Idempotent. Lý do: Select `default` không áp vào dòng đã có trên staging (issue: "dòng cũ mặc định recon_type = Tài chính").

Quyền: không đổi (ma trận dòng "Lần tính giá, kết quả, đối soát"; `perm_matrix/nc_reconciliation_line.json` của FEAT-017 giữ nguyên). Test quyền: NC Clinician không đọc được dòng Vật chất; NC Auditor đọc được, không sửa `explanation`.

### 2.2 Không thêm DocType. Report và Page mới (không phải DocType)

| Tên | Loại | Module | ref_doctype | roles |
| :-- | :-- | :-- | :-- | :-- |
| NC Physical Reconciliation (SCR-DSK-038, nhãn "Đối soát vật chất và sản lượng") | Script Report | NC Costing | NC Reconciliation Line | NC Finance, NC Director, NC Admin, NC Auditor |
| NC Missing Data (SCR-DSK-039, nhãn "Báo cáo thiếu dữ liệu") | Script Report | NC Costing | NC Costing Run | NC Finance, NC Director, NC Admin, NC Auditor, NC Department Head (ASM-037-13) |
| `sensitivity` (SCR-DSK-040, tiêu đề "Phân tích độ nhạy") | Page, bundle `public/js/sensitivity/` | NC Costing | — | NC Finance, NC Director, NC Admin, NC Auditor, NC Department Head (ASM-037-16) |

## 3. API (`normcore/api/costing.py`, `@frappe.whitelist()`, kiểm quyền tường minh)

| Hàm | Tham số | Kết quả | Kiểm quyền, lỗi |
| :-- | :-- | :-- | :-- |
| `get_reconciliation(run)` **(sửa)** | | như FEAT-017, chỉ dòng `recon_type` = "Tài chính"; thêm `physical: {material_blocked, unreconciled, volume_warnings, available}` để dải liên kết SCR-DSK-038; `blocked` = số dòng chặn **mọi loại**; `can_lock` theo `blocked` mới | như cũ |
| `get_physical_reconciliation(run)` **(mới)** | | `{run, status, scenario, available, material_tolerance, volume_tolerance, material: [...], volume: [...], blocked, can_explain, can_lock}`. Dòng material: `name, department, department_name, item, item_name, norm_uom, calculated_qty, actual_qty, diff_qty (= actual − calc), variance_pct, over_tolerance, recon_status, explanation, needs_explanation`. Dòng volume: `name, technical_service, service_name, department, department_name, calculated_qty (kết quả trả), actual_qty (HIS), diff_qty, variance_pct, over_tolerance (cảnh báo), explanation`. `available` = 0 khi kịch bản ≠ "Thực tế 12 tháng" (ASM-037-02) | `_run(run, "read")` + `has_permission(RECON, "read", throw)` |
| `save_explanation(line, explanation)` **(giữ)** | | thêm `needs_explanation` tính theo luật chặn mới (`reconcile.needs_explanation`) | như cũ |
| `lock_run(run)` | | không đổi chữ ký | lỗi nguyên văn của `lock_costing` |
| `get_run_results(run)` **(sửa nhỏ)** | | `recon_blocked` đếm theo luật chặn mới; thêm `physical_unreconciled` (số khoa "Chưa đối soát") cho dải SCR-DSK-022 | như cũ |
| `get_sensitivity_base(service_cost)` **(mới)** | | `{service_cost, run, run_status, service, service_name, department, is_paraclinical, origin: {full_cost, calculated_price, rounded_price, direct_total, alloc_total, by_component}, inputs: {volume, systems: [{test_system, qbn, equipment, mode, contract_cost}], items: [{item, item_name, purchase_price, norm_units, uom}], equipments: [{equipment, mode, contract_cost}]}, modes: ACQUISITION_MODES}` | `has_permission(COST, "read", doc=sc, throw)`; lần tính phải "Đã tính" hoặc "Đã khóa", không thì `ValidationError` "Lần tính chưa có kết quả" |
| `run_sensitivity(service_cost, overrides)` **(mới)** | `overrides` JSON: `{"volume": số?, "system_volumes": {ts: số}, "prices": {item: giá một đơn vị mua}, "equipment_modes": {eq: {"mode": "...", "contract_cost": số?}}}` | `{trial: {...như origin}, origin, diff: {full_cost, rounded_price, pct}, systems: [{test_system, k_origin, k_trial, direct_origin, direct_trial}], warnings, note: "Kết quả thử, không lưu"}` | như `get_sensitivity_base`; giả định sai → `frappe.throw` (`ValidationError`) với thông báo mục 4.4; **không** gọi `insert/save/db_set/db.set_value`, không commit |

Report "NC Missing Data" không cần API riêng: `execute(filters)` của report gọi loader + `costing/missing_data.py` (mục 4.5).

## 4. Logic

### 4.1 `costing/reconcile.py` (thuần, mở rộng; giữ nguyên `reconcile`, `depreciation_centers`)

```python
FINANCIAL, MATERIAL, VOLUME = "Tài chính", "Vật chất", "Sản lượng"
RECONCILED, UNRECONCILED = "Đã đối soát", "Chưa đối soát"

@dataclass(frozen=True)
class PhysRow:  # một dòng Vật chất hoặc Sản lượng
    recon_type: str; department: str; item: str | None; service: str | None
    calculated: Decimal | None; actual: Decimal | None; variance_pct: Decimal | None
    over_tolerance: bool; status: str = RECONCILED; note: str = ""

def material_quantities(inputs) -> dict[tuple[str, str], Decimal]
def material_rows(calc, issued, units, item_meta, departments_with_data, tolerance) -> list[PhysRow]
def volume_rows(results, his, tolerance) -> list[PhysRow]
def needs_explanation(line: Mapping) -> bool
def lock_blockers(lines) -> list[str]          # mở rộng
```

**`material_quantities(inputs)`** — BR-CLS-014, golden `material_recon`. `inputs`: các `engine.ServiceInput` có `paraclinical` của lần tính. Với mỗi hệ thống `s` của mỗi dịch vụ, khoa `d` = `inp.department`:
- `qnk, qcal, qrerun, qeqa, h, _ = cls.aux_counts(s, c.imaging)`; `k, _ = cls.k_factor(s.qbn, …)` (r6, đúng hàm của lần tính — không công thức mới);
- mỗi `ln` trong `s.lines` có `ln.norm.component` ∈ {DRUG, SUPPLY}, `not ln.norm.excluded`, `ln.norm.resource` là NC Item; `q = engine.applied_qty(hospital_qty, authority_qty)`, `w = wastage_rate` (ASM-037-03):

| `cost_level` | Lượng một năm |
| :-- | :-- |
| RESULT, `apply_k` | `q × k × Qbn` |
| RESULT, không k | `q × Qbn` |
| TUBE | `q × (1 + w) × Qbn ÷ tests_per_tube` |
| BATCH | `q × (1 + w) × Qbn ÷ batch` |
| DAY | `q × (1 + w) × D` (D = `cls._days(s)`) |
| PERIOD | `q × (1 + w)` |

- mỗi `IqcLine` (BR-CLS-006): `qty_per_run × levels × runs_per_day × D ÷ shared_params` vào mặt hàng `iqc.item`. Chất chuẩn (`CalLine`) không có mặt hàng → không đối soát (ASM-037-03).
- Cộng dồn `Decimal` theo (d, item), **không làm tròn** (golden trả `18185.560000`).

Kiểm golden: dựng `ClsServiceInput` từ `tests/golden/cls_fixture.py` → `material_quantities(...)[("XN","HC_GLU")] == golden_cls.material_recon("HC_GLU", 94)[0]` (= 18.185,56). Mặt hàng chỉ có dòng RESULT nên khớp đúng hàm golden; các cấp khác theo chữ BR-CLS-014.

**`material_rows(calc, issued, units, item_meta, departments_with_data, tolerance)`**
- `issued`: `{(khoa, mặt hàng): Σ issued_qty}` (đơn vị mua) từ NC Stock Issue Actual của `fiscal_year`; `units`: `{mặt hàng: norm_units_per_purchase_unit}`; `item_meta[item].norm_required` = `item_type ∈ pricing.NORM_ITEM_TYPES`.
- Khoa trong `{d for d, _ in calc}` không thuộc `departments_with_data` → **một** `PhysRow(MATERIAL, d, None, …, status=UNRECONCILED, note="Khoa chưa có số liệu xuất kho năm {y}")` (FR-COST-029, A-08); bỏ các mặt hàng của khoa đó.
- Khoa có số liệu, mỗi (d, item) có `calc > 0`:
  - không có dòng xuất kho của mặt hàng, hoặc thiếu số đơn vị định mức mà `norm_required` → `status=UNRECONCILED`, `actual=None`, `pct=None`, `note` nêu lý do (ASM-037-04, 05);
  - còn lại `actual = issued × (units or 1)`; `actual == 0` → như "không có dòng xuất kho"; `pct = r2((actual − calc) ÷ actual × 100)` (ROUND_HALF_UP); `over = abs(pct) > tol` (golden: `>` , không `≥`).
- Mặt hàng có xuất kho nhưng không có lượng tính → không lập dòng (ASM-037-05).
- Sắp theo (khoa, dòng khoa-chưa-đối-soát trước, mặt hàng).

**`volume_rows(results, his, tolerance)`** — BR-CLS-015, golden `volume_recon`. `results`: `{(dịch vụ, khoa): Σ qbn}` của các hệ thống dịch vụ cận lâm sàng (chính là `ServiceResult.volume`, FR-COST-024); `his`: `{(dịch vụ, khoa): NC Service Volume.volume}` kịch bản "Thực tế 12 tháng". `pct = r2((results − his) ÷ his × 100)`, `over = abs(pct) > tol`. HIS thiếu hoặc 0 → `pct=None`, `over=True`, `note="Thiếu sản lượng HIS"` (ASM-037-07).

**`needs_explanation(line)`** (dict có `recon_type`, `over_tolerance`, `recon_status`, `explanation`):
- trống `explanation` **và** một trong: (`recon_type` ∈ {Tài chính, trống} và `over_tolerance`) hoặc (`recon_type` = Vật chất và (`over_tolerance` hoặc `recon_status` = Chưa đối soát)).
- `recon_type` = Sản lượng → luôn `False` (FR-COST-028: không chặn).

**`lock_blockers(lines)`**: lọc theo `needs_explanation`; nhãn dòng Tài chính giữ nguyên `"{cost_center} · {cost_category}"` (test FEAT-017 không đổi); dòng Vật chất `"Vật chất · {department} · {item}"` hoặc `"Vật chất · {department} · Chưa đối soát"`. Dòng thiếu `recon_type` coi là Tài chính.

### 4.2 Lớp CSDL (`nc_costing_run/`)

- `NCCostingRun._run`: trong closure `load(e)` giữ `self._inputs[(service, dept)] = inp` (không đổi kết quả).
- `loader.physical_context(run, inputs) -> PhysCtx` (**mới**, chỉ đọc, nạp theo lô): `available` = `run.volume_scenario == "Thực tế 12 tháng"`; khoa = khoa của các input cận lâm sàng; `issued` (NC Stock Issue Actual, `fiscal_year`, các khoa đó), `departments_with_data`; `units`, `item_meta` (NC Item); `his` (NC Service Volume, năm, kịch bản "Thực tế 12 tháng", cặp cận lâm sàng); `dept_center` (`NC Department.cost_center`); hai ngưỡng từ bộ tham số (`material_recon_tolerance`, `volume_recon_tolerance`; trống → 5 và 2 theo golden `PARAM`, ASM-037-17).
- `execute_costing`: sau `write_reconciliation` tài chính, nếu `available`: `writer.write_physical_reconciliation(doc, rows, dept_center)` với `rows = reconcile.material_rows(reconcile.material_quantities(cls_inputs), …) + reconcile.volume_rows(…)`. Cùng savepoint `nc_costing_run`: lỗi → "Tính lỗi" như cũ. Tính lại xóa mọi dòng của lần tính (đã có), giải trình mất theo (ASM-017-08).
- `writer.recon_values` thêm `recon_type` = "Tài chính" (và `recon_status` "Đã đối soát"); `writer.physical_values(run, row, center)` theo bảng ánh xạ mục 2.1; `flags.from_costing = True`.
- `lock_costing`: đọc thêm `recon_type`, `recon_status`, `department`, `item`; `reconcile.lock_blockers` mới; thông báo: `"Còn {n} dòng đối soát vượt ngưỡng hoặc chưa đối soát chưa có giải trình: {nhãn}"`.
- **Ảnh chụp (FEAT-018):** `loader.stored_rows` chỉ lấy dòng `recon_type` ∈ {"Tài chính", NULL}; `writer.expected_rows` không đổi (chỉ có dòng tài chính). Dòng vật chất, sản lượng không vào so khớp tái lập (ASM-037-09). Không đổi `snapshot.VERSION`.
- `api._blockers`, `get_reconciliation`: lọc/đếm theo luật mới; report "NC Reconciliation" `execute` lọc `recon_type` = "Tài chính".

### 4.3 Độ nhạy — `costing/sensitivity.py` (thuần, mới)

```python
class InvalidAssumption(ValueError): ...
def apply(inp: engine.ServiceInput, overrides: Mapping, units: Mapping) -> engine.ServiceInput
def trial(snap: dict, service: str, department: str, overrides: Mapping, units: Mapping) -> engine.ServiceResult
```
- `apply` dùng `dataclasses.replace`, không sửa đối tượng gốc:
  - `system_volumes[ts]` → `TestSystemInput.qbn` (và `has_volume=True`); `ServiceInput.volume` = Σ qbn mới (FR-COST-024). `volume` (dịch vụ thường) → `ServiceInput.volume`.
  - `prices[item]` (giá một đơn vị mua) → `rate = pricing.unit_price_per_norm(price, units[item] or 1)` (BR-CLS-002) thay `LineRate.rate` của mọi dòng có `resource == item` trong `inp.rates` / `s.rates` và `IqcLine.rate` có `item == item`; giữ `source` + " · giả định".
  - `equipment_modes[eq]` → `EquipmentInput.mode` (∈ `resources.ACQUISITION_MODES`), `contract_cost` khi Thuê / Liên doanh, liên kết.
- `trial`: `snap2` = bản sao của `snap` với input của (service, department) thay bằng `to_plain(apply(...))`; `snapshot.recompute(snap2)` (tính lại cả phân bổ cấp 1, cấp 2 như lần tính — không công thức mới); trả `ServiceResult` của cặp. Không đọc CSDL.
- Kiểm hợp lệ (UC-024 2a), ném `InvalidAssumption`:
  - sản lượng ≤ 0 hoặc không phải số → "Sản lượng giả định phải lớn hơn 0";
  - giá < 0 → "Đơn giá giả định không được âm";
  - hình thức ngoài danh sách → "Hình thức có máy không hợp lệ";
  - Thuê/Liên doanh thiếu `contract_cost` > 0 → "Nhập chi phí năm theo hợp đồng";
  - Mua mà thiết bị không có nguyên giá, số năm sử dụng → "Thiết bị chưa có nguyên giá hoặc số năm sử dụng";
  - hệ thống, mặt hàng, thiết bị không thuộc dịch vụ → "{mã} không thuộc dịch vụ này";
  - không có giả định nào → "Nhập ít nhất một giả định".
- Kết quả dịch vụ "Lỗi" (ví dụ thiếu dữ liệu sau giả định) → API trả `trial.status = "Lỗi"` và `calc_message`, không ném lỗi.

API (`get_sensitivity_base`, `run_sensitivity`): lấy ảnh chụp — "Đã khóa": `snapshot.unpack(file, snapshot_hash)`; "Đã tính": `loader.capture_snapshot(run, loader.eligible_from_results(run))` (chỉ đọc). Có thể giữ ảnh chụp trong `frappe.cache` 10 phút theo khóa `(run, modified)` (không ghi CSDL). `origin` = số đã lưu của NC Service Cost; `trial` = `run_sensitivity`. Nếu tính lại không giả định khác số đã lưu (dữ liệu đổi sau lần tính, chỉ có ở "Đã tính") → `warnings` "Dữ liệu đầu vào đã đổi sau lần tính; so sánh có thể lệch" (ASM-037-14).

### 4.4 Thông báo lỗi (tiếng Việt, qua `_()`) — như mục 4.3 và: "Lần tính chưa có kết quả", "Chỉ khóa được lần tính giá ở trạng thái Đã tính" (giữ), "Còn {n} dòng đối soát vượt ngưỡng hoặc chưa đối soát chưa có giải trình: …".

### 4.5 Báo cáo thiếu dữ liệu — `costing/missing_data.py` (thuần, mới)

```python
PRICE, VOLUME, TIME_STUDY, QC_PLAN, COMPLIANCE = "Thiếu đơn giá", "Thiếu sản lượng", "Thiếu bấm giờ", "Thiếu kế hoạch chất lượng", "Thiếu hồ sơ tuân thủ"
@dataclass(frozen=True)
class Gap: service: str; department: str; kind: str; detail: str
def collect(pairs: Sequence[PairData]) -> list[Gap]
```
`PairData` (dataclass): `service, department, input: engine.ServiceInput | None, norm_lines_basis: {line_id: basis}, has_time_study: bool, systems_without_plan: tuple, systems_without_volume: tuple, missing_compliance: tuple[(equipment, type)], imaging: bool`.

Luật (ASM-037-11):
- **Thiếu đơn giá:** dòng không loại trừ có `rates[line_id] is None` (dịch vụ thường) hoặc `s.rates[...] is None` (từng hệ thống), hoặc thiết bị chính của hệ thống không dựng được đơn giá. `detail` = "L02 · Hóa chất GLU" (mỗi dòng một `Gap`, gộp hiển thị ở report).
- **Thiếu sản lượng:** dịch vụ thường `input.volume` None hoặc ≤ 0; cận lâm sàng: mỗi hệ thống "Đang dùng" không có NC Test System Volume của năm, kịch bản, hoặc `patient_results` ≤ 0. `detail` = "Hệ thống GLU-B" hoặc "Kịch bản Thực tế 12 tháng".
- **Thiếu bấm giờ:** bộ định mức có dòng LABOR `basis` = "Bấm giờ" mà không có NC Time Study của (dịch vụ, khoa).
- **Thiếu kế hoạch chất lượng:** hệ thống "Đang dùng" không có NC QC Plan; bỏ qua dịch vụ chẩn đoán hình ảnh (`imaging`, Qnk = Qchuan = 0 — ASM-036-06).
- **Thiếu hồ sơ tuân thủ:** thiết bị chính, thiết bị gắn dòng định mức, thuộc loại `compliance_required` mà không có hồ sơ còn hạn tại ngày tính (`compliance.missing_required`).
- Sắp theo dịch vụ, khoa, loại (thứ tự năm loại trên).

Lớp CSDL (`report/nc_missing_data/nc_missing_data.py::execute`): dựng NC Costing Run **tạm, không insert** (`frappe.new_doc`) từ bộ lọc → `loader.scope_info(run)` (cặp đủ điều kiện và chưa đủ) → `loader.load_context(run, eligible)` → `loader.load_service` từng cặp → `PairData` (thêm `basis` dòng LABOR, NC Time Study, `ctx.plans`, `ctx.ts_vol`, hồ sơ) → `missing_data.collect`. Cặp "chưa có bộ định mức Đã khóa" không vào bảng, đếm trong dải đầu (ASM-037-12). Chỉ đọc, không tạo bản ghi. NC Department Head: bộ lọc khoa ép về khoa được phân (`frappe.get_roles` + User Permission NC Department như `SCOPE_RULES`).

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test (tên gợi ý) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Golden V6 xuất 94 hộp: lượng tính 18.185,56 (khớp `golden_cls.material_recon` đến 6 số lẻ); xuất kho 18.800; 3,27%; `over_tolerance` sai | TC-CLS-16 | FR-COST-026 | `tests/golden/test_reconcile_cls_golden.py::test_TC_CLS_16_V6_xuat_94_hop` |
| 2 | V6 xuất 100 hộp trên site: dòng Vật chất XN · HC_GLU 9,07%, "Vượt ngưỡng"; `lock_run` từ chối (thông báo có "Vật chất · XN · HC_GLU"); sau `save_explanation` thì khóa được, status "Đã khóa" | TC-CLS-17 | FR-COST-027 | `nc_costing_run/test_nc_costing_physical.py::test_TC_CLS_17_vuot_nguong_chan_khoa` (+ `tests/unit` phần thuần `test_TC_CLS_17_V6_xuat_100_hop`) |
| 3 | V7: HIS 15.800 → 1,27%, không cảnh báo; HIS 15.500 → 3,23%, cảnh báo; dòng Sản lượng cảnh báo không có trong `lock_blockers` | TC-CLS-18 | FR-COST-028 | `tests/golden/test_reconcile_cls_golden.py::test_TC_CLS_18_V7_san_luong` |
| 4 | Khoa XN không có NC Stock Issue Actual: đúng một dòng Vật chất "Chưa đối soát", không mặt hàng; khóa bị từ chối; sau giải trình thì khóa được | TC-CLS-19 | FR-COST-029 | `test_nc_costing_physical.py::test_TC_CLS_19_chua_doi_soat_vat_chat` |
| 5 | Phạm vi có dịch vụ A thiếu đơn giá, B thiếu sản lượng, C có hệ thống thiếu NC QC Plan: report trả đúng ba dịch vụ với đúng loại; dịch vụ đủ dữ liệu không xuất hiện; chạy được khi chưa có lần tính | TC-CLS-39 | FR-OUT-012 | `report/nc_missing_data/test_nc_missing_data.py::test_TC_CLS_39_ba_dich_vu_thieu` (+ unit `test_missing_data.py`) |
| 6 | `run_sensitivity` GLU, `system_volumes={"GLU-A": 6000}`: `trial.full_cost` ≠ `origin.full_cost`; NC Costing Run (`modified`, `status`, `snapshot_hash`), mọi NC Service Cost và dòng của lần tính không đổi (so trước/sau), không có bản ghi mới | TC-CLS-40 | FR-COST-030 | `api/test_costing_sensitivity.py::test_TC_CLS_40_do_nhay_khong_ghi` |
| 7 | Giả định sản lượng 0 → `ValidationError` "Sản lượng giả định phải lớn hơn 0" | — (UC-024 2a) | FR-COST-030 | `test_sensitivity.py::test_san_luong_0_bao_loi` |
| 8 | Kịch bản ≠ "Thực tế 12 tháng": không có dòng Vật chất/Sản lượng; khóa không bị chặn vì vật chất | — | FR-COST-026 | `test_nc_costing_physical.py::test_khong_doi_soat_vat_chat_khi_ke_hoach` |
| 9 | Dòng FEAT-017 đã có sau patch có `recon_type` "Tài chính"; test FEAT-017, FEAT-018 xanh không sửa (khóa với ảnh chụp vẫn so khớp) | — | FR-COST-008, 011 | `test_patch_backfill_reconciliation_type`, cả bộ hiện có |
| 10 | Quyền: NC Clinician không đọc dòng Vật chất, không mở report, `get_physical_reconciliation` → PermissionError; NC Auditor đọc được, `save_explanation` → PermissionError; NC Department Head ngoài khoa → PermissionError ở `run_sensitivity` | — | FR-ACC-007 | `test_nc_costing_physical.py::test_quyen_clinician_auditor`, `test_costing_sensitivity.py::test_quyen_truong_khoa_ngoai_khoa` |

Golden bất biến: `python3 docs/golden/golden_cls.py` thoát 0; độ phủ `normcore/costing` ≥ 90% (ba module thuần phủ ≥ 95%).

## 6. Rủi ro

- **TBD-14** chưa có người chốt (README: "Nghiệm thu FEAT-037"). FEAT-037 không dùng ba loại chi phí tạm (đối soát vật chất, sản lượng tính theo lượng); giữ mặc định ASM-074 / ASM-036-15. Lead cần xác nhận có cần người chốt trước QA hay không (ASM-037-01).
- `capture_snapshot` cho lần tính "Đã tính" lớn có thể chậm (đọc toàn bộ đầu vào); mỗi lần thử còn chạy lại phân bổ cả lần tính (FEAT-017 đo 8,1 s / 500 dịch vụ cho pha tính). Chấp nhận ở R1; ghi số đo vào As-Built.
- Đổi `reqd` của `cost_center`, `cost_category` sang điều kiện: dòng cũ đều có giá trị, patch chỉ điền `recon_type`.
- Dòng Vật chất không vào so khớp ảnh chụp: khóa không phát hiện xuất kho đổi sau lần tính (ASM-037-09).
