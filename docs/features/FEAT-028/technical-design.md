# FEAT-028 — So sánh giá và gợi ý điều chỉnh — Thiết kế kỹ thuật

Issue NORM-81. Bản phát hành R3. Phụ thuộc FEAT-026, FEAT-018 (đều có `DONE` trên `develop`).

Nguồn: `srs.md` FR-ADJ-001..005, 008, 010; BR-ADJ-001..008 (mục 3.4.2), BR-COST-004, 007, 013; `use-cases.md` UC-014 bước 1–3, 2a, 2b, 4a; `data-model.md` NC Adjustment Suggestion, NC Costing Parameter Set (`comparison_tolerance`, `wastage_cap`), NC Settings (`benchmark_window_months`, `min_benchmark_facilities`, `price_valid_months`), mục 4 dòng "Gợi ý, kịch bản, phương án giá"; ADR-008; `ux-foundations.md` SCR-DSK-026, "Thanh so sánh giá", "Thanh cơ cấu giá"; As-Built FEAT-014 (bấm giờ), FEAT-018, FEAT-026, FEAT-037 (độ nhạy).

**Golden.** `docs/golden/` không có hàm cho BR-ADJ-* (đã `grep -n ADJ docs/golden/*.py`: rỗng). Số mong đợi lấy từ `test-cases.md` (bậc 2): TC-ADJ-02 dùng giá tính toán golden của DV-TEST-A 302.132,73. Tác động ước tính của gợi ý không có công thức trong tài liệu; thiết kế chỉ gọi lại hàm đã có của bộ máy tính giá (BR-COST-004, 007, 013), không thêm công thức tiền mới (ASM-028-06).

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-ADJ-001 | Đủ | Chọn giá "Đã xác nhận", cùng loại giá với lần tính, `effective_date` trong cửa sổ `benchmark_window_months` (24) tháng trước ngày tính giá, mỗi đơn vị lấy giá mới nhất |
| FR-ADJ-002 | Đủ | Thấp nhất, trung vị, cao nhất, độ lệch % so với trung vị (BR-ADJ-008) khi số đơn vị ≥ `min_benchmark_facilities` (3) |
| FR-ADJ-003 | Đủ | Dưới ngưỡng: nhãn "Chưa đủ dữ liệu so sánh", không sinh gợi ý |
| FR-ADJ-004 | Đủ | Lọc theo tỉnh/thành phố, hạng, loại hình; tính lại thống kê trên tập đã lọc |
| FR-ADJ-005 | Đủ | Độ lệch vượt `comparison_tolerance` → sinh gợi ý theo BR-ADJ-001..007 (quy tắc, không AI), lưu NC Adjustment Suggestion, xếp theo |tác động| giảm dần |
| FR-ADJ-008 | Đủ | Chấp nhận / Từ chối gợi ý; Từ chối bắt buộc lý do; lưu người và thời điểm quyết định |
| FR-ADJ-010 | Đủ | Giá trị và tỷ trọng từng cấu phần trong giá thành toàn bộ; tổng giá trị = `full_cost` |

Ngoài phạm vi (FEAT-029): ghi gợi ý vào kịch bản, tính lại giá, tạo phiên bản bộ định mức nháp (UC-014 bước 4–5), yêu cầu sửa quy trình (4b, FR-ADJ-006, 007, 009); trạng thái "Đã chuyển yêu cầu sửa quy trình" chỉ khai trong Select, FEAT-028 không đặt. Phương án giá: FEAT-030. "Kịch bản đang mở" của SCR-DSK-026: FEAT-029.

## 2. DocType

### 2.1 NC Adjustment Suggestion (mới, module NC Benchmark)

Trường đúng `data-model.md`, không thêm trường dữ liệu (không cần AMD). Naming: `ADJ-.YYYY.-.#####`. `track_changes = 1`. Mọi trường `read_only = 1` trên form: gợi ý chỉ do máy chủ sinh, quyết định chỉ qua API `decide_suggestion` (mục 3.3). Không ai có quyền xóa.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `service_cost` | Kết quả dịch vụ | Link NC Service Cost | Có | `in_list_view`, `in_standard_filter` |
| `rule_code` | Quy tắc | Data | Có | `BR-ADJ-001` … `BR-ADJ-007`; validate thuộc tập này |
| `direction` | Hướng | Select `Giảm\nTăng` | Có | |
| `component` | Cấu phần | Data | Có | Mã cấu phần `LABOR`/`DRUG`/`SUPPLY`/`EQUIPMENT`/`INFRA`/`UTILITY` hoặc `PARAMETER` (BR-ADJ-005, 007 phần bộ tham số) |
| `target_ref` | Đối tượng | Data | Có | Khóa ổn định của đối tượng: mã dòng định mức (`L04`), mã thiết bị (`EQ1`), mã mặt hàng, mã bộ tham số; xem bảng 3.2 |
| `current_value` | Giá trị hiện tại | Data | | Chuỗi đã định dạng vi-VN (ví dụ `0,4`, `20 phút`, `5%`) |
| `suggested_value` | Giá trị đề xuất | Data | | |
| `estimated_impact` | Tác động ước tính đến giá | Currency | | Âm = giảm giá tính toán. Để trống khi không ước tính được (BR-ADJ-006, 007; ASM-028-07) |
| `requires_procedure_change` | Cần sửa quy trình | Check | | 1 chỉ với BR-ADJ-003 |
| `status` | Trạng thái | Select `Mới\nChấp nhận\nTừ chối\nĐã chuyển yêu cầu sửa quy trình` | Có | Mặc định `Mới`; `in_list_view` |
| `decision_reason` | Lý do | Small Text | | BB khi `Từ chối` (FR-ADJ-008) |
| `decided_by`, `decided_on` | Người quyết định, thời điểm | Link User, Datetime | | Máy chủ đặt |

Controller `nc_adjustment_suggestion.py`:
- `validate`: `rule_code` thuộc `rules.RULE_CODES`; `status = "Từ chối"` mà `decision_reason.strip()` rỗng → `frappe.throw("Từ chối gợi ý phải nêu lý do")`; đổi `status` khỏi `Mới` (hoặc đổi trường quyết định) chỉ khi `self.flags.adj_decision` (do API đặt), ngược lại throw "Quyết định gợi ý qua Bàn so sánh giá". Bản đã quyết (`Chấp nhận`/`Từ chối`) không sửa được trường nào (ASM-028-09).
- Không có DI riêng trong data-model cho DocType này.

### 2.2 Quyền (data-model mục 4, dòng "Gợi ý, kịch bản, phương án giá")

| Vai trò | DocPerm | Phạm vi |
| :-- | :-- | :-- |
| NC Finance | read, write, create, report, export | mọi khoa |
| NC Department Head | read, report | theo khoa: `scope_rules/nc_adjustment_suggestion.json` với `"via": ["service_cost", "NC Service Cost"]` |
| NC Director | read, report | mọi khoa |
| NC Consultant, NC Admin, NC Auditor | read | NC Auditor chỉ đọc |
| Các vai khác | không có | |

`scripts/conventions/perm_matrix/nc_adjustment_suggestion.json`: `{"doctype": "NC Adjustment Suggestion", "row": "Gợi ý, kịch bản, phương án giá", "codes": "- R - W - - R R R R", "delete": []}`.

Thao tác "A" (Trưởng khoa theo khoa, Giám đốc) = quyền quyết định Chấp nhận/Từ chối qua API (mục 3.3), không phải DocPerm write.

### 2.3 Không đổi DocType cũ

NC Costing Parameter Set đã có `comparison_tolerance`, `wastage_cap`; NC Settings đã có `benchmark_window_months`, `min_benchmark_facilities`, `price_valid_months` (đọc qua `core.settings`). NC Benchmark Price, NC Benchmark Facility không đổi. Không cần patch.

## 3. Thành phần

### 3.1 `normcore/benchmark/stats.py` (thuần, không import frappe)

| Hàm | Vào | Ra | BR/FR |
| :-- | :-- | :-- | :-- |
| `window_start(costing_date, months)` | date, int | date = cùng ngày của `months` tháng trước (cuối tháng thì kẹp về ngày cuối tháng) | FR-ADJ-001, ASM-028-01 |
| `select_prices(rows, costing_date, months)` | dòng đã xác nhận (dict `facility`, `price`, `effective_date`, …) | mỗi `facility` một dòng có `effective_date` lớn nhất trong `[window_start, costing_date]`; hòa ngày lấy `name` nhỏ nhất; thứ tự theo giá tăng | FR-ADJ-001 |
| `filter_rows(rows, provinces=None, levels=None, ownerships=None)` | | dòng khớp mọi bộ lọc khác rỗng (OR trong một bộ lọc, AND giữa các bộ lọc) | FR-ADJ-004 |
| `median(values)` | list Decimal | Decimal, n lẻ giá trị giữa, n chẵn `(a+b)/2` (không làm tròn) | BR-ADJ-008 |
| `deviation_pct(calc, median)` | Decimal | `((calc − median) / median × 100)` làm tròn 2 số lẻ `ROUND_HALF_UP` | BR-ADJ-008, ASM-028-03 |
| `summarize(calc_price, rows, min_facilities, use_adjusted=False)` | | `{count, min, median, max, deviation_pct, sufficient, label}`; `sufficient = count ≥ min_facilities`; không đủ: `min/median/max/deviation_pct = None`, `label = "Chưa đủ dữ liệu so sánh"` | FR-ADJ-002, 003 |
| `exceeds(deviation_pct, tolerance)` | | `abs(deviation_pct) > tolerance`; `None` → False | FR-ADJ-005, ASM-028-04 |
| `breakdown(service_cost)` | dict trường NC Service Cost | danh sách `{group, field, label, value, share_pct}` cho các cấu phần `DIRECT`/`ALLOC` của `costing.compare.COMPONENTS` (bỏ `eqa_cost` khi trống), `share_pct = value / full_cost × 100` 2 số lẻ; kèm `total = Σ value` và `full_cost` | FR-ADJ-010, ASM-028-10 |

Giá dùng cho thống kê: `price` (giá gốc). `use_adjusted=True`: dùng `adjusted.adjusted_price` (BR-ADJ-009 của FEAT-026) khi có, dòng thiếu chỉ số giữ giá gốc và mang cờ `adjusted_missing` (ASM-028-02).

Kiểm TC-ADJ-02: `summarize(302132.73, [250000, 280000, 300000])` → median 280000, deviation +7,90; thêm 320000 → median 290000, +4,18.

### 3.2 `normcore/benchmark/rules.py` (thuần; được import `normcore.costing.engine`, `normcore.costing.resources`)

ADR-008: mỗi quy tắc một hàm thuần, nhận `ServiceFacts`, trả list `Suggestion`. Câu chữ từ mẫu cố định `TEMPLATES[rule_code]`.

```
RULE_CODES = ("BR-ADJ-001", …, "BR-ADJ-007")
UTILIZATION_TARGET = Decimal("0.5")      # BR-ADJ-001
TIME_STUDY_MARGIN = Decimal("0.15")      # BR-ADJ-002
@dataclass(frozen=True) class Suggestion: rule_code, direction, component, target_ref, current_value, suggested_value,
                                          estimated_impact (Decimal|None), requires_procedure_change (bool), text
@dataclass(frozen=True) class ServiceFacts:
  direct_total, alloc_by_category (dict), pricing (engine.PricingParams), norm_lines (tuple engine.NormLine),
  line_rates (dict line_id -> engine.LineRate),            # đơn giá đã dùng trong lần tính (NC Service Cost Line)
  equipment (dict code -> {annual_cost, planned_hours, utilization, maintenance}),
  time_study (dict (step_id, job_title) -> median_minutes; chỉ khi đủ số ca),
  wastage_cap (Decimal, phân số), equivalents (dict item -> [(item, LineRate)] rẻ hơn, đã lọc đang dùng),
  stale_prices (dict line_id -> {item, valid_from}), latest_parameter_set (str|None), parameter_set (str),
  accumulation_rate_pct (Decimal)
```

Tác động ước tính (ASM-028-06): `impact(facts, delta_direct)` = `engine.price_service(direct_total + delta_direct, alloc_by_category, pricing).calculated_price − engine.price_service(direct_total, alloc_by_category, pricing).calculated_price`. Phân bổ cấp 2 giữ nguyên (tính lại đầy đủ là việc của kịch bản FEAT-029). `delta_direct` = `engine.direct_line(dòng mới, rate mới).amount − engine.direct_line(dòng hiện tại, rate hiện tại).amount` (BR-COST-002..007), không tự viết công thức dòng.

| Quy tắc | Hàm | Kích hoạt | `target_ref` · hiện tại → đề xuất | Tác động |
| :-- | :-- | :-- | :-- | :-- |
| BR-ADJ-001 Giảm | `rule_001_utilization` | dòng `EQUIPMENT` không loại trừ, thiết bị có `utilization < 0,5` | mã thiết bị · `0,4` → `0,5` | rate hiện tại/mới = `LineRate(resources.machine_hourly_rate(annual_cost, planned_hours, u))` với u hiện tại / 0,5; cộng mọi dòng dùng thiết bị đó trong dịch vụ |
| BR-ADJ-002 Giảm | `rule_002_time_study` | dòng `LABOR` có trung vị bấm giờ (khóa `(step_id, resource)`) và `hospital_qty > median × 1,15` | mã dòng · `20 phút` → `15 phút` | dòng với `hospital_qty = median`, rate = rate đã dùng |
| BR-ADJ-003 Giảm, cần sửa QT | `rule_003_equivalent` | dòng `DRUG`/`SUPPLY` có mặt hàng cùng `equivalent_group` đang dùng với đơn giá (theo đơn vị định mức) thấp hơn | mã dòng · mã mặt hàng hiện tại → mặt hàng rẻ nhất | dòng với rate của mặt hàng thay |
| BR-ADJ-004 Giảm | `rule_004_wastage` | `wastage_rate > wastage_cap` | mã dòng · `8%` → trần | dòng với `wastage_rate = wastage_cap` |
| BR-ADJ-005 Giảm/Tăng | `rule_005_accumulation` | `pricing.accumulation_mode` khác None và tỷ lệ ≠ 0 | mã bộ tham số · `5%` → `4%` (Giảm) hoặc `6%` (Tăng) | `price_service` với tỷ lệ ± 1 điểm % (không âm) − giá hiện tại; `component = "PARAMETER"` |
| BR-ADJ-006 Tăng | `rule_006_missing` | (a) dòng thiết bị mà thiết bị `maintenance` = 0; (b) không có dòng `INFRA`; (c) không có dòng `UTILITY` | mã thiết bị / `INFRA` / `UTILITY` · "Chưa có" → "Bổ sung …" | None (ASM-028-07) |
| BR-ADJ-007 Tăng | `rule_007_stale` | (a) đơn giá mặt hàng dùng trong dịch vụ có `valid_from` cũ hơn `price_valid_months` tháng trước ngày tính giá; (b) có bộ tham số `effective_from` mới hơn bộ đang dùng và ≤ ngày tính giá | mã mặt hàng / mã bộ tham số · ngày hiệu lực → "Cập nhật" | None (ASM-028-07) |

`generate(facts, deviation_pct, tolerance)`:
1. `not stats.exceeds(deviation_pct, tolerance)` (gồm `deviation_pct is None` khi chưa đủ dữ liệu) → `[]` (FR-ADJ-003, 005).
2. `deviation_pct > 0` → chạy quy tắc hướng Giảm (001–004) và 005 hướng Giảm; `< 0` → quy tắc Tăng (006, 007) và 005 hướng Tăng (ASM-028-05).
3. Bỏ gợi ý có `estimated_impact == 0`. Sắp: có tác động trước, theo `abs(estimated_impact)` giảm dần; không có tác động sau, theo `rule_code`, `target_ref`.
4. Không quy tắc nào đề xuất bỏ bước, giảm `headcount` (SRS 3.4.2).

Kiểm TC-ADJ-04 (dữ liệu DV-TEST-A golden, EQ1 `utilization = 0,4`, chi phí năm 186.000.000, 2.112 giờ; trung vị bấm giờ (S002, DD) = 15; bộ tham số ON_COST 5%, nghĩa vụ 0; trực tiếp 183.963,06, phân bổ 103.782,40; deviation +20,85, tolerance 10): ra gợi ý BR-ADJ-001 `EQ1` tác động −15.411,93 (dòng L07 73.390,15 → 58.712,12), BR-ADJ-002 `L04` −5.218,93 (19.881,63 → 14.911,22); BR-ADJ-005 −2.877,45 nếu có; thứ tự 001, 002, 005. Các số này là kết quả của hàm bộ máy đã có, Dev kiểm lại khi viết test và ghi vào implementation-log; test khẳng định có mặt, giá trị hiện tại/đề xuất, dấu và thứ tự tác động (không đặt thêm giá trị tiền mới vào test-cases).

### 3.3 API `normcore/api/price_compare.py` (mới, whitelisted)

Kiểm quyền tường minh trong từng hàm. Lỗi ném `frappe.throw` (tiếng Việt), `frappe.PermissionError` khi không có quyền.

| Hàm | Tham số | Kết quả | Kiểm |
| :-- | :-- | :-- | :-- |
| `get_comparison(run, provinces=None, levels=None, ownerships=None, use_adjusted=0)` | lọc là list JSON | `{run: {name, title, status, costing_date, price_category, parameter_set, tolerance, window_months, min_facilities}, filter_options: {provinces, levels, ownerships}, rows: [{service_cost, technical_service, service_name, department, calculated_price, count, min, median, max, deviation_pct, sufficient, label, exceeds, suggestion_counts: {Mới, Chấp nhận, Từ chối}}]}` | `run.status ∈ {Đã tính, Đã khóa}` ngược lại "Lần tính chưa có kết quả"; chỉ dịch vụ `calc_status ≠ Lỗi` mà người gọi đọc được (`frappe.get_list("NC Service Cost")`, phạm vi khoa tự áp); không đọc được dòng nào → PermissionError |
| `get_service_detail(service_cost, provinces…, use_adjusted=0)` | | `{stats, prices: [dòng đã chọn + đơn vị, tỉnh, hạng, loại hình, adjusted], excluded: [{facility, effective_date, reason: "Ngoài cửa sổ 24 tháng" / "Cũ hơn giá khác của đơn vị" / "Sau ngày tính giá"}], breakdown, suggestions: [bản ghi NC Adjustment Suggestion + text], can_generate, can_decide}` | `frappe.has_permission("NC Service Cost", "read", doc, throw=True)` |
| `generate_suggestions(service_cost, provinces…, use_adjusted=0)` | | như `suggestions` ở trên | quyền `create` NC Adjustment Suggestion (NC Finance); không vượt ngưỡng/chưa đủ dữ liệu → trả `[]` và không ghi (FR-ADJ-003) |
| `decide_suggestion(name, decision, reason=None)` | `decision ∈ {"Chấp nhận", "Từ chối"}` | bản ghi đã cập nhật | xem dưới |

`generate_suggestions` (FR-ADJ-005): dựng `ServiceFacts` bằng `_facts(service_cost)` rồi `rules.generate`. Ghi đè có kiểm soát: mỗi khóa `(rule_code, target_ref)` — bản `Mới` cũ được cập nhật giá trị; bản đã quyết giữ nguyên, không tạo thêm; bản `Mới` cũ không còn kích hoạt bị xóa (máy chủ, `ignore_permissions`). Ghi bằng `ignore_permissions` sau khi đã kiểm quyền create. Ghi NC Audit Event không bắt buộc (không có loại sự kiện tương ứng).

`_facts(service_cost)` (đọc CSDL, không ghi): `direct_total` = Σ dòng `Trực tiếp` của NC Service Cost; `alloc_by_category` từ `alloc_*`; `pricing = engine.PricingParams.from_values(parameter_set, price_category)` của lần tính; `norm_lines` từ NC Norm Set `norm_set` của kết quả (đúng kiểu `engine.NormLine` như loader dựng); `line_rates` từ `unit_rate` của dòng NC Service Cost Line theo `norm_line_id`; `equipment` từ `NCEquipment.indicative(costing_date, expired_mode, include_depr)["annual_equipment_cost"]`, `planned_hours_per_year`, `utilization_rate`, `annual_maintenance_cost` (chỉ thiết bị `allocation_basis = Giờ kế hoạch`); `time_study` từ `api.time_study._summary(service, department, procedure)` khi `sufficient` (ASM-028-08); `equivalents` qua cùng đường đơn giá mặt hàng của loader (`rates.material_rate`); `stale_prices` từ `NC Item Price` đang dùng; `latest_parameter_set` = bộ có `effective_from` lớn nhất ≤ `costing_date`.

`decide_suggestion` (FR-ADJ-008, UC-014 4a): chỉ bản `Mới`. Quyền quyết định: NC Finance (write), NC Director, NC Department Head có quyền đọc `service_cost` (phạm vi khoa). Ngược lại PermissionError (NC Auditor, NC Consultant, NC Admin luôn bị từ chối). `Từ chối` mà lý do rỗng → "Từ chối gợi ý phải nêu lý do". `Chấp nhận` khi `requires_procedure_change = 1` → "Gợi ý cần sửa quy trình, chưa áp trực tiếp được (FEAT-029)" (UC-014 4b; ASM-028-11). Đặt `status`, `decision_reason`, `decided_by = session.user`, `decided_on = now`, `flags.adj_decision = True`, `save(ignore_permissions=True)`.

### 3.4 Mở rộng `normcore/api/benchmark.py` (FEAT-026)

Thêm `comparable_prices_bulk(technical_services, price_category, target_month)` (không whitelisted): một truy vấn NC Benchmark Price `technical_service in …`, `ref.comparable_prices`, gắn thông tin đơn vị và `_adjust` như `get_comparable_prices`; trả `{service: [rows]}`. `get_comparable_prices` giữ nguyên chữ ký và hành vi (test FEAT-026 không sửa). `target_month` = tháng của `costing_date`.

### 3.5 Trang `price-compare` và lối vào

- Desk Page `normcore/nc_benchmark/page/price_compare/` (`price_compare.json`, `.js`), Vue ở `normcore/public/js/price_compare/` (`PriceCompare.vue`, `price_compare.bundle.js`) theo mẫu trang `sensitivity`. Vai trò của Page: NC Finance, NC Department Head, NC Director, NC Admin, NC Auditor (NC Consultant không có quyền đọc kết quả tính giá; xem gợi ý qua danh sách DocType).
- Form NC Costing Run (`nc_costing_run.js`): nút "So sánh giá" khi `status ∈ {Đã tính, Đã khóa}` → `/app/price-compare?run=<name>`.
- Chi tiết bố cục: `ui-design.md`.

## 4. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | P (01/01/2025, 01/06/2026), Q (01/10/2024), ngày tính 31/12/2026, cửa sổ 24: chọn dòng 01/06/2026 của P, Q bị loại "Ngoài cửa sổ" | TC-ADJ-01 | FR-ADJ-001 | `normcore/tests/unit/test_benchmark_stats.py::test_TC_ADJ_01_chon_gia_trong_24_thang` |
| 2 | Chỉ dòng "Đã xác nhận", cùng loại giá lần tính | — | FR-ADJ-001 | `normcore/api/test_price_compare.py::test_FR_ADJ_001_chi_gia_xac_nhan_cung_loai_gia` |
| 3 | 302.132,73 với 3 giá → trung vị 280.000, +7,90; 4 giá → 290.000, +4,18; min/max đúng | TC-ADJ-02 | FR-ADJ-002 | `test_benchmark_stats.py::test_TC_ADJ_02_trung_vi_va_do_lech` |
| 4 | Dịch vụ có 2 đơn vị: `label = "Chưa đủ dữ liệu so sánh"`, `generate_suggestions` trả `[]`, không có bản ghi NC Adjustment Suggestion | TC-ADJ-03 | FR-ADJ-003 | `test_price_compare.py::test_TC_ADJ_03_chua_du_du_lieu` |
| 5 | Lọc tỉnh/hạng/loại hình làm đổi count, median, deviation | — | FR-ADJ-004 | `test_benchmark_stats.py::test_FR_ADJ_004_loc_don_vi`, `test_price_compare.py::test_FR_ADJ_004_loc_tinh_lai` |
| 6 | DV-TEST-A (mục 3.2): gợi ý BR-ADJ-001 cho EQ1 và BR-ADJ-002 cho L04, mỗi gợi ý có giá trị hiện tại, đề xuất, tác động; xếp theo tác động giảm dần | TC-ADJ-04 | FR-ADJ-005 | `normcore/tests/unit/test_benchmark_rules.py::test_TC_ADJ_04_goi_y_dv_test_a` |
| 7 | Trong ngưỡng → không gợi ý; độ lệch âm → chỉ quy tắc Tăng; mỗi quy tắc 001–007 có test kích hoạt và không kích hoạt | — | FR-ADJ-005 | `test_benchmark_rules.py::test_FR_ADJ_005_*` (độ phủ `rules.py` ≥ 90%) |
| 8 | Sinh lại không nhân đôi; bản đã quyết giữ nguyên | — | FR-ADJ-005 | `test_price_compare.py::test_FR_ADJ_005_sinh_lai_khong_trung` |
| 9 | Từ chối không lý do bị chặn; có lý do → lưu lý do, người, thời điểm; Chấp nhận gợi ý cần sửa QT bị chặn | — | FR-ADJ-008 | `test_price_compare.py::test_FR_ADJ_008_tu_choi_can_ly_do` |
| 10 | DV-TEST-A: 12 cấu phần có giá trị và tỷ trọng, Σ giá trị = `full_cost` 287.745,46 | TC-ADJ-08 | FR-ADJ-010 | `test_price_compare.py::test_TC_ADJ_08_co_cau_gia` |
| 11 | Quyền NC Adjustment Suggestion: NC Clinician không đọc; NC Auditor đọc, không tạo/sửa/quyết định; Trưởng khoa chỉ thấy và quyết định gợi ý của khoa mình; NC Finance tạo được | — | FR-ACC-003, 007 | `normcore/nc_benchmark/doctype/nc_adjustment_suggestion/test_nc_adjustment_suggestion.py::test_quyen_*` |
| 12 | Trang `price-compare` có trong Page, dùng `__()`, có bản dịch | — | FR-ADJ-002 | `normcore/tests/unit/test_feat_028_ui.py` |

## 5. Giả định và rủi ro

Giả định ASM-028-01..11 ở `docs/decisions/assumptions/FEAT-028.md`. Không có CF, AMD.

Rủi ro:
- Tác động ước tính không tính lại phân bổ cấp 2 nên có thể lớn hơn tác động thật sau khi tính lại (phần trực tiếp giảm làm phần còn lại để phân bổ tăng). Giao diện ghi "Ước tính, chưa tính lại phân bổ"; số chính xác do kịch bản FEAT-029.
- Thiết bị và đơn giá đọc từ dữ liệu sống tại lúc so sánh, không từ ảnh chụp: với lần tính "Đã khóa" lâu, giá trị hiện tại của gợi ý có thể khác lúc tính (ASM-028-08).
- Dịch vụ cận lâm sàng (`is_paraclinical`): quy tắc chỉ xét dòng định mức thường; dòng theo hệ thống xét nghiệm chưa có quy tắc riêng (ghi vào As-Built).
