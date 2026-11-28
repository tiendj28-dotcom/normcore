# FEAT-016 — Số liệu kế toán, sản lượng, quy tắc phân bổ — Thiết kế kỹ thuật

Issue NORM-28. Nguồn: `srs.md` FR-ACCT-001..011, BR-COST-008, BR-COST-009; `use-cases.md` UC-011 (bước 1–7, luồng 1a, 1b, 2a, 4a, 4b, 7a); `data-model.md` 3.1 (NC Cost Center, NC Cost Center Driver), 3.6 (NC Account Mapping, NC Accounting Import, NC Accounting Import Line, NC Service Volume, NC Allocation Rule), mục 4 dòng "Số liệu kế toán, sản lượng, phân bổ", DI-06, DI-07; `architecture.md` ADR-013; `ux-foundations.md` SCR-DSK-020, SCR-DSK-021; `test-cases.md` mục 2.1 (bộ dữ liệu vàng), TC-ACCT-01..09; `docs/golden/golden_engine.py` (`ACCOUNTING`, `HEADCOUNT`, `L1_DRIVER`, `L2_DRIVER`). Phụ thuộc đã DONE: FEAT-001 (NC Cost Center, NC Department), FEAT-004 (khung nhập Excel).

Không viết lại cơ chế đã có: đọc tệp, chuẩn hóa ô, lỗi theo dòng, tệp mẫu dùng `core/importer.py` (FEAT-004); bộ nhập danh mục đăng ký ở `core/import_sets.py`; sổ sự kiện dùng `core/audit.py` (hook chung `doc_events["*"]`); chặn xóa bản ghi bị tham chiếu dùng `core/references.py`.

## 1. Phạm vi

| FR | Mức | Làm gì ở FEAT này |
| :-- | :-- | :-- |
| FR-ACCT-001 | Must | NC Accounting Import: lưu bản ghi mới có tệp đính kèm → đọc tệp, tạo dòng, trạng thái "Nháp", `line_count`, `total_amount` |
| FR-ACCT-002 | Must | Thiếu mã tài khoản, số tiền không phải số, mã trung tâm chi phí không tồn tại → lỗi dòng lưu ở `import_errors` (AMD-010), `error_count` > 0 chặn chốt |
| FR-ACCT-003 | Must | Gán `cost_category` theo NC Account Mapping của `accounting_regime`, khớp tiền tố dài nhất (ADR-013) |
| FR-ACCT-004 | Must | Đổi loại chi phí hoặc đánh dấu loại trừ của một dòng phải có lý do; lưu `changed_by` |
| FR-ACCT-005 | Must | Chốt bị từ chối khi còn dòng (không loại trừ) chưa có loại chi phí; thông báo nêu dòng |
| FR-ACCT-006 | Must | Chốt: khóa dòng (DI-07), ghi bảng tổng theo (trung tâm, loại) `totals` (AMD-010), sự kiện "Khóa" |
| FR-ACCT-007 | Must | DocType NC Service Volume + bộ nhập `nc_service_volume`: lỗi dòng cho mã dịch vụ/khoa lạ, dòng đúng vẫn lưu |
| FR-ACCT-008 | Must | DocType NC Allocation Rule: bắt buộc cấp, loại chi phí, tiêu chí; HEADCOUNT / AREA / REVENUE chỉ ở cấp 1 (BR-COST-009) |
| FR-ACCT-009 | Must | Cài bảng ánh xạ mặc định chế độ "Hành chính sự nghiệp" (TBD-03 → ASM-118) khi cài app và bằng patch cho site đã có; NC Finance sửa được; bộ nhập `nc_account_mapping` |
| FR-ACCT-010 | Must | DocType NC Cost Center Driver + bộ nhập `nc_cost_center_driver`; hàm đọc tiêu chí và hàm tỷ lệ cấp 1 (khớp golden: 20 ÷ 50 = 40%) |
| FR-ACCT-011 | Should | Lần nhập thứ hai cùng năm là bản ghi mới (`KT-2026-02`), lần cũ không đổi |

Không làm: tính phân bổ cấp 1, cấp 2 và đối soát (FEAT-015, FEAT-017 — chỉ cung cấp dữ liệu và hàm tỷ lệ tiêu chí); nối `NC Costing Run.accounting_import` (ASM-004, FEAT-015); sản lượng cận lâm sàng, xuất kho, mã HIS ngoài (UC-022, FEAT-035; trang SCR-DSK-037); NC Consultant xem số liệu kế toán khi "cấp riêng" (FR-ACC-004, không thuộc FR của FEAT này — ASM-128); NC Settings (`accounting_regime` mặc định lấy ở trường, ASM-119).

## 2. DocType

Mô-đun **NC Costing**. Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1 cho DocType cha. Tất cả là DocType mới (chưa lên staging), không cần patch cấu trúc (ASM-130).

Hằng dùng chung (định nghĩa một lần ở `normcore/costing/accounting.py`, JSON dùng đúng chuỗi):
- `COST_CATEGORIES = ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT", "EXCLUDED")` (BR-COST-008). `ALLOCATABLE = COST_CATEGORIES[:-1]`.
- `DRIVERS = ("LABOR_MIN", "MACHINE_MIN", "VOLUME", "DIRECT_COST", "REVENUE", "HEADCOUNT", "AREA")`; `LEVEL1_ONLY = ("REVENUE", "HEADCOUNT", "AREA")` (BR-COST-009).
- `REGIMES = ("Hành chính sự nghiệp", "Doanh nghiệp")`, mặc định "Hành chính sự nghiệp" (ASM-119).
- Mã loại chi phí và tiêu chí giữ nguyên chữ in (là mã của BR); Select hiển thị mã, mô tả trường liệt kê nghĩa tiếng Việt.

### 2.1 NC Account Mapping (data-model 3.6, ADR-013)

Autoname `hash`; `title_field` = `account_prefix`; sắp xếp `account_prefix asc`; `search_fields` = `accounting_regime, cost_category`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| accounting_regime | Chế độ kế toán | Select `REGIMES` | Có | Mặc định "Hành chính sự nghiệp"; `in_list_view`, `in_standard_filter` |
| account_prefix | Tiền tố tài khoản | Data | Có | Chuẩn hóa `normalize_account` (ASM-120); `in_list_view` |
| cost_category | Loại chi phí | Select `COST_CATEGORIES` | Có | `in_list_view`, `in_standard_filter` |
| note | Ghi chú | Small Text | | Bản mặc định ghi "Giả định — chờ xác nhận (TBD-03)" |

`validate`: chuẩn hóa tiền tố; rỗng sau chuẩn hóa → từ chối; (`accounting_regime`, `account_prefix`) trùng bản ghi khác → "Tiền tố 61111 của chế độ Hành chính sự nghiệp đã có". Chỉ mục duy nhất CSDL `(accounting_regime, account_prefix)` ở `on_doctype_update` (`frappe.db.add_unique`). Sửa ánh xạ **không** đổi lần nhập đã có; lần nhập "Nháp" chỉ đổi khi bấm "Gán lại theo bảng ánh xạ" (mục 3). Lần nhập "Đã chốt" không bao giờ đổi.

### 2.2 NC Accounting Import và bảng con (data-model 3.6, sửa theo AMD-010)

Autoname `KT-.{fiscal_year}.-.##` (ví dụ `KT-2026-01`, `KT-2026-02` — FR-ACCT-011); không đặt `title_field` (tên bản ghi là tiêu đề; đặt `title_field` = `name` làm ListView lỗi, NORM-87, ASM-NORM86-02); sắp xếp `creation desc`; `track_changes` = 1.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| fiscal_year | Năm tài chính | Int | Có | 2000 ≤ năm ≤ 2100 (ASM-121); `in_list_view`, `in_standard_filter`; không đổi sau khi tạo (`set_only_once`) |
| accounting_regime | Chế độ kế toán | Select `REGIMES` | Có | Mặc định "Hành chính sự nghiệp"; `set_only_once` |
| source_file | Tệp nguồn | Attach | Có | `.xlsx` (khung FEAT-004) |
| status | Trạng thái | Select `Nháp` / `Đã chốt` | Có | Mặc định "Nháp", `read_only`, `in_list_view`, `in_standard_filter`; chỉ đổi bằng API chốt |
| line_count | Số dòng | Int | | **[AMD-010]** `read_only`; `in_list_view` |
| total_amount | Tổng tiền | Currency | | `read_only`; tổng `amount` mọi dòng hợp lệ (kể cả dòng loại trừ, ASM-123); `in_list_view` |
| error_count | Số dòng lỗi | Int | | **[AMD-010]** `read_only`; số lỗi dòng của lần đọc tệp gần nhất |
| import_errors | Lỗi khi đọc tệp | Long Text | | **[AMD-010]** `read_only`, ẩn trên form (form hiển thị qua HTML); JSON `[{"row", "column", "message", "text"}]` từ `RowError.as_dict()` |
| lines | Dòng | Table NC Accounting Import Line | | Chỉ sinh từ tệp (ASM-122) |
| totals | Tổng theo trung tâm và loại chi phí | Table NC Accounting Import Total | | **[AMD-010]** `read_only`; chỉ ghi lúc chốt |

**NC Accounting Import Line** (bảng con, `istable` = 1), đúng data-model:

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| account_code | Mã tài khoản | Data | Có | `read_only`, `in_list_view` |
| account_name | Tên tài khoản | Data | | `read_only`, `in_list_view` |
| cost_center | Trung tâm chi phí | Link NC Cost Center | Có | `read_only`, `in_list_view` |
| amount | Số tiền | Currency | Có | `read_only`, `in_list_view` |
| cost_category | Loại chi phí | Select `""` + `COST_CATEGORIES` | | Trống = chưa gán; `in_list_view`; sửa qua hộp thoại (ui-design) |
| is_excluded | Loại trừ | Check | | `in_list_view` |
| change_reason | Lý do sửa | Small Text | | |
| changed_by | Người sửa | Link User | | `read_only` |

**NC Accounting Import Total** **[AMD-010]** (bảng con, `istable` = 1): `cost_center` (Link NC Cost Center, BB, `in_list_view`), `cost_category` (Select `ALLOCATABLE`, BB, `in_list_view`), `amount` (Currency, BB, `in_list_view`). Một dòng cho mỗi cặp có số tiền, sắp theo (trung tâm, thứ tự `ALLOCATABLE`).

**Luồng trạng thái** (không dùng Workflow; `STATE_FIELDS["NC Accounting Import"] = "status"` và thêm `"Đã chốt"` vào `LOCKED_STATES` trong `core/audit.py` → sự kiện "Khóa" khi chốt):

```
(mới, có tệp) --lưu: đọc tệp--> Nháp --chốt [error_count = 0, có dòng, mọi dòng không loại trừ có loại]--> Đã chốt
Nháp --"Đọc lại tệp"/"Gán lại theo bảng ánh xạ"/sửa loại dòng--> Nháp
Đã chốt: không sửa, không xóa, không mở lại (DI-07)
```

**Controller `nc_accounting_import.py`** (logic ở `costing/accounting.py`, mục 4):

| Sự kiện | Việc |
| :-- | :-- |
| `before_insert` | Đọc `source_file` (`frappe.get_doc("File", {"file_url": ...}).get_content()`), gọi `accounting.parse_lines` rồi `accounting.assign_categories` với ánh xạ của `accounting_regime`; ghi `lines`, `import_errors`, `error_count`, `line_count`, `total_amount`. Lỗi mức tệp (không phải .xlsx, thiếu cột bắt buộc, tệp rỗng, quá 5.000 dòng) → `frappe.throw`, không tạo bản ghi (ASM-121) |
| `validate` (bản ghi đã có) | Trạng thái trong CSDL "Đã chốt" và không có `flags.nc_finalizing` → từ chối mọi thay đổi: "Lần nhập KT-2026-01 đã chốt, không sửa được" (DI-07, TC-ACCT-06). "Nháp": so dòng với bản trong CSDL (`get_doc_before_save`) bằng `accounting.check_line_changes` — thêm/bớt dòng hoặc đổi `account_code`, `account_name`, `cost_center`, `amount` → từ chối ("Dòng chỉ thay đổi bằng cách đọc lại tệp"); đổi `cost_category` hoặc `is_excluded` mà `change_reason` trống hoặc không đổi so với trước → từ chối "Dòng 3: nhập lý do khi đổi loại chi phí hoặc loại trừ" (TC-ACCT-04); hợp lệ thì đặt `changed_by` = người dùng hiện tại. Chọn `cost_category` = EXCLUDED → `is_excluded` = 1; bỏ `is_excluded` khi loại vẫn là EXCLUDED → từ chối "chọn loại chi phí khác". Tính lại `line_count`, `total_amount` |
| `on_trash` | "Đã chốt" → từ chối (DI-07). (Không vai trò nào có quyền xóa; chặn cả Administrator) |

### 2.3 NC Service Volume (data-model 3.6 [1.1])

Autoname `hash`; `title_field` = `technical_service`; `search_fields` = `fiscal_year, department, scenario`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| fiscal_year | Năm tài chính | Int | Có | 2000..2100; `in_list_view`, `in_standard_filter` |
| technical_service | Dịch vụ | Link NC Technical Service | Có | `in_list_view`, `in_standard_filter` |
| department | Khoa | Link NC Department | Có | `in_list_view`, `in_standard_filter` |
| scenario | Kịch bản sản lượng | Select `Thực tế 12 tháng` / `Kế hoạch` / `Công suất` | Có | Mặc định "Thực tế 12 tháng"; `in_list_view`, `in_standard_filter` |
| volume | Sản lượng | Float | Có | ≥ 0 (ASM-125); `in_list_view` |

`validate`: `volume` < 0 → từ chối; trùng (`fiscal_year`, `technical_service`, `department`, `scenario`) với bản ghi khác → "Đã có sản lượng năm 2026 của DV-TEST-A tại khoa K01, kịch bản Thực tế 12 tháng". Chỉ mục duy nhất 4 trường ở `on_doctype_update`. Không kiểm khoa có thuộc "Khoa thực hiện" của dịch vụ (ASM-125). Dữ liệu gốc không khóa (DI-07 [1.1]).

### 2.4 NC Cost Center Driver (data-model 3.1)

Autoname `hash` (data-model: tự động); `title_field` = `cost_center`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| fiscal_year | Năm tài chính | Int | Có | 2000..2100; `in_list_view`, `in_standard_filter` |
| cost_center | Trung tâm chi phí | Link NC Cost Center | Có | `in_list_view`, `in_standard_filter` |
| headcount | Số nhân lực | Float | | ≥ 0; `in_list_view` |
| area_m2 | Diện tích (m²) | Float | | ≥ 0; `in_list_view` |
| revenue | Doanh thu | Currency | | ≥ 0; `in_list_view` |

`validate`: số âm → từ chối; trùng (`fiscal_year`, `cost_center`) → "Đã có tiêu chí năm 2026 của trung tâm K01". Chỉ mục duy nhất 2 trường. Hàm module (không whitelist) `get_driver_values(fiscal_year, driver) -> dict[str, Decimal]` trong `nc_cost_center_driver.py`: `driver` ∈ `LEVEL1_ONLY` → trường `headcount` / `area_m2` / `revenue`; trả `{cost_center: Decimal(str(giá trị))}` của các bản ghi năm đó có giá trị khác trống; driver khác → `ValueError`. FEAT-017 dùng cùng `allocation_rules.driver_shares` (mục 4).

### 2.5 NC Allocation Rule (data-model 3.6)

Autoname `hash`; `title_field` = `rule_name`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| rule_name | Tên quy tắc | Data | Có | `in_list_view` |
| level | Cấp phân bổ | Select `Cấp 1` / `Cấp 2` | Có | Mô tả: "Cấp 1: Hỗ trợ sang Lâm sàng; Cấp 2: Lâm sàng sang Dịch vụ"; `in_list_view`, `in_standard_filter` |
| cost_category | Loại chi phí | Select `ALLOCATABLE` | Có | Không có EXCLUDED (ASM-127); `in_list_view`, `in_standard_filter` |
| driver | Tiêu chí phân bổ | Select `DRIVERS` | Có | `in_list_view` |
| cost_center | Trung tâm chi phí | Link NC Cost Center | | Trống = mọi trung tâm; `in_list_view` |

`validate` (hàm thuần `allocation_rules.rule_errors`): thiếu trường bắt buộc → `MandatoryError` chuẩn Frappe (nhãn tiếng Việt; TC-ACCT-07 lần 1); `level` = Cấp 2 và `driver` ∈ `LEVEL1_ONLY` → "Tiêu chí HEADCOUNT chỉ dùng ở cấp 1 (BR-COST-009)" (TC-ACCT-07 lần 2); `cost_center` có giá trị: cấp 1 phải là trung tâm "Hỗ trợ", cấp 2 phải là "Lâm sàng" (ASM-127); trùng (`level`, `cost_category`, `cost_center` hoặc trống) với quy tắc khác → "Đã có quy tắc Cấp 2 cho LABOR áp cho mọi trung tâm". Cấp 1 dùng được mọi tiêu chí (BR-COST-009 chỉ giới hạn chiều ngược lại). Không có năm tài chính (data-model không có).

### 2.6 Quyền (data-model mục 4, dòng "Số liệu kế toán, sản lượng, phân bổ")

Năm DocType cha NC Accounting Import, NC Account Mapping, NC Service Volume, NC Cost Center Driver, NC Allocation Rule: Clinician —, Dept Head —, Council —, **Finance W** (read, write, create), Resource Mgr —, Doc Controller —, Director R, Consultant —, Admin R, Auditor R. Mã ma trận `- - - W - - R - R R`. Không vai trò nào có quyền xóa (ASM-015, ASM-128): lần nhập sai giữ ở "Nháp", không vào lần tính. Bảng con theo quyền cha.

`scripts/check_conventions.py`: thêm `MATRIX["Số liệu kế toán, sản lượng, phân bổ"] = "- - - W - - R - R R"` và năm dòng `DOCTYPE_ROW`. Không thêm `DELETE_ALLOWED`.

Không dùng phạm vi khoa (`SCOPE_RULES`): Finance thấy mọi trung tâm.

**Test cũ đổi theo ngoại lệ CLAUDE.md mục 3.1 — cần Quyết định Lead trên NORM-28 trước khi Dev sửa:**
- `tests/test_permissions.py::test_co_30_doctype_va_10_vai_tro`: 30 → 37 (thêm 5 cha + 2 bảng con; cộng thêm số DocType của FEAT-033 nếu gộp trước) và docstring; không đổi assertion khác.
- `api/test_importer.py`: danh sách bộ nhập của NC Finance thêm `nc_account_mapping`, `nc_service_volume`, `nc_cost_center_driver` (theo thứ tự đăng ký); Resource Manager, Auditor không đổi.

### 2.7 Dữ liệu cài sẵn và patch

- `install.py`: `ensure_default_account_mapping()` gọi trong `after_install`; dữ liệu ở hằng `DEFAULT_ACCOUNT_MAPPING` trong `normcore/costing/accounting.py` (một nơi, ASM-118). Chỉ chèn dòng (chế độ, tiền tố) chưa có → không ghi đè giá trị NC Finance đã sửa.
- Patch `normcore.patches.add_default_account_mapping` ([post_model_sync], gọi cùng hàm) cho staging đã cài.
- Không patch cấu trúc: toàn DocType mới (ASM-130).

Bảng mặc định (chế độ "Hành chính sự nghiệp", mọi dòng `note` = "Giả định — chờ xác nhận (TBD-03)"):

| Tiền tố | Loại | Ý nghĩa giả định |
| :-- | :-- | :-- |
| 61111 | LABOR | Chi phí tiền lương, tiền công và chi phí khác cho nhân viên (thường xuyên) |
| 61112 | DRUG_SUPPLY | Chi phí vật tư, công cụ, dịch vụ đã sử dụng (thường xuyên) |
| 611122 | UTILITY | Chi tiết điện, nước, nhiên liệu, xử lý chất thải, vệ sinh (thường xuyên) |
| 61113 | DEPRECIATION | Chi phí khấu hao, hao mòn tài sản cố định (thường xuyên) |
| 61118 | MANAGEMENT | Chi phí hoạt động khác (thường xuyên) |
| 61121 | LABOR | Như 61111, không thường xuyên |
| 61122 | DRUG_SUPPLY | Như 61112, không thường xuyên |
| 611222 | UTILITY | Như 611122, không thường xuyên |
| 61123 | DEPRECIATION | Như 61113, không thường xuyên |
| 61128 | MANAGEMENT | Như 61118, không thường xuyên |
| 642 | MANAGEMENT | Chi phí quản lý |
| 811 | EXCLUDED | Chi phí khác, không tính vào giá |
| 821 | EXCLUDED | Chi phí thuế thu nhập doanh nghiệp, không tính vào giá |

## 3. API whitelisted — `normcore/api/accounting.py`

Mỗi hàm kiểm quyền tường minh trên bản ghi (`frappe.has_permission(..., doc=name, throw=True)`); lỗi tiếng Việt qua `frappe.throw`.

| Hàm | Tham số | Kết quả | Quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `get_import_summary(name)` | mã lần nhập | `{"name", "status", "line_count", "total_amount", "error_count", "errors": [...], "unassigned": [{"idx", "account_code", "cost_center", "amount"}], "excluded_count", "can_finalize": bool, "blockers": [str], "totals": [{"cost_center", "cost_category", "amount"}]}`; khi "Nháp", `totals` là bản xem trước tính từ dòng hiện tại | `read` |
| `update_line(name, row, cost_category, is_excluded, change_reason)` | `row` = `name` của dòng con | Bản tóm tắt như trên | `write`; "Nháp"; lý do trống → `ValidationError` "Nhập lý do…" (TC-ACCT-04); ghi `changed_by` |
| `reapply_mapping(name)` | | `{"changed": n}` + tóm tắt | `write`; "Nháp"; gán lại dòng chưa có `changed_by` theo ánh xạ hiện tại; dòng đã sửa tay giữ nguyên (ASM-122) |
| `reload_file(name)` | | Tóm tắt | `write`; "Nháp"; đọc lại `source_file` hiện tại (người dùng đã thay tệp đính kèm), thay toàn bộ `lines`, `import_errors`; mất các sửa tay (hộp thoại xác nhận ở giao diện) |
| `finalize(name)` | | Tóm tắt (status "Đã chốt") | `write`; điều kiện ở `accounting.finalize_blockers`; vi phạm → `ValidationError` liệt kê: "Không chốt được lần nhập KT-2026-01: còn 2 dòng lỗi khi đọc tệp", "…: 1 dòng chưa có loại chi phí: dòng 3 (tài khoản 99999, trung tâm K01)" (TC-ACCT-02, 03); hợp lệ → ghi `totals`, `status` = "Đã chốt", lưu với `flags.nc_finalizing` (sự kiện "Khóa" qua `core/audit.py`) |
| `download_template()` | | Tệp `mau-nhap-so-lieu-ke-toan.xlsx` (tiêu đề + 1 dòng ví dụ) | `read` NC Accounting Import |

Bộ nhập danh mục (sản lượng, tiêu chí, ánh xạ) dùng API sẵn có `normcore.api.importer.*` (FEAT-004).

## 4. Logic thuần (không import `frappe`; độ phủ ≥ 90%)

### `normcore/costing/accounting.py`

| Hàm | Việc | Căn cứ |
| :-- | :-- | :-- |
| `ACCOUNTING_LINES` | `ImportSet` **không đăng ký** (key `nc_accounting_import_line`): cột `account_code` "Mã tài khoản" Data BB (ví dụ 61111), `account_name` "Tên tài khoản" Data, `cost_center` "Mã trung tâm chi phí" Link NC Cost Center BB (K01), `amount` "Số tiền" Float BB (700000000) | FR-ACCT-001 (mẫu: mã TK, tên TK, mã TTCP, số tiền) |
| `normalize_account(code) -> str` | Chuỗi; số `61111.0` → `"61111"`; bỏ mọi khoảng trắng và dấu chấm; chữ in hoa | ASM-120 |
| `match_category(account_code, mappings) -> str \| None` | Tiền tố dài nhất của `normalize_account(code)` trong `mappings` (`{prefix: category}`); không khớp → `None` | FR-ACCT-003, ADR-013 |
| `parse_lines(content, filename, cost_center_exists) -> (lines, errors)` | Gọi `core.importer.parse(ACCOUNTING_LINES, ..., unique=False)`; thêm lỗi dòng `"K99" không tồn tại trong NC Cost Center` theo `cost_center_exists`; lỗi mức tệp → `ImportFileError(text)`. `lines`: list dict có `source_row` (dòng Excel, chỉ để báo lỗi, không lưu) | FR-ACCT-001, 002 |
| `assign_categories(lines, mappings, keep_manual=False) -> int` | Đặt `cost_category` (`None` → trống); EXCLUDED → `is_excluded` = 1; `keep_manual` bỏ qua dòng có `changed_by`; trả số dòng đổi | FR-ACCT-003, UC-011 2a |
| `check_line_changes(before, after) -> list[str]` | Lỗi theo 2.2 (dòng thêm/bớt, trường nguồn đổi, thiếu lý do, EXCLUDED/loại trừ không khớp) | FR-ACCT-004, ASM-122 |
| `unassigned(lines) -> list` | Dòng `is_excluded` = 0 và `cost_category` trống | FR-ACCT-005 |
| `finalize_blockers(status, error_count, lines) -> list[str]` | Không phải "Nháp"; `error_count` > 0; không có dòng; còn dòng chưa gán (nêu `idx`, tài khoản, trung tâm) | FR-ACCT-002, 005 |
| `totals(lines) -> list[(cost_center, category, Decimal)]` | Cộng `Decimal(str(amount))` theo (trung tâm, loại), bỏ dòng `is_excluded` / EXCLUDED; không làm tròn (golden cộng số nguyên đồng) | FR-ACCT-006; đối chiếu `golden_engine.ACCOUNTING` |
| `total_amount(lines) -> Decimal` | Tổng mọi dòng | FR-ACCT-001, ASM-123 |
| `DEFAULT_ACCOUNT_MAPPING` | Bảng 2.7 | FR-ACCT-009, ASM-118 |

### `normcore/costing/allocation_rules.py`

| Hàm | Việc | Căn cứ |
| :-- | :-- | :-- |
| `rule_errors(level, cost_category, driver, center_type) -> list[str]` | Cấp 2 + `LEVEL1_ONLY`; loại không thuộc `ALLOCATABLE`; loại trung tâm sai cấp | BR-COST-009, FR-ACCT-008, ASM-127 |
| `driver_errors(values) -> list[str]` | Số âm ở `headcount`, `area_m2`, `revenue` | FR-ACCT-010, ASM-126 |
| `volume_errors(volume) -> list[str]` | Sản lượng âm | FR-ACCT-007, ASM-125 |
| `valid_year(year) -> bool` | 2000..2100 | ASM-121 |
| `driver_shares(values: dict[str, Decimal]) -> dict[str, Decimal]` | `v / tổng`, đúng như golden `HEADCOUNT["K01"] / sum(HEADCOUNT.values())` (không làm tròn); tổng = 0 hoặc rỗng → `ValueError("Tổng tiêu chí bằng 0")` | FR-ACCT-010, TC-ACCT-09; golden `run()` dòng `share = ...` |

Không có phép tính tiền phân bổ ở FEAT này (FEAT-017 nhân tỷ lệ với số kế toán và làm tròn theo golden `r2`).

## 5. Khung nhập (FEAT-004) — mở rộng tương thích ngược (ASM-124)

`core/importer.py`:
1. `ImportSet` thêm `key_fields: tuple = ()`; thuộc tính `keys` = `key_fields or (key_field,)`. Khóa ghép: `parse` kiểm trùng trong tệp theo bộ giá trị của `keys` (thông báo `trùng khóa "2026 / DV-TEST-A / K01 / Thực tế 12 tháng" với dòng 2`); `process` truyền `key` là tuple khi `key_fields` có giá trị, giữ nguyên chuỗi khi một khóa.
2. `parse(..., unique=True)`: `unique=False` bỏ kiểm trùng khóa (dòng kế toán trùng tài khoản là hợp lệ).
3. `api/importer.py::run_import`: `lookup`/`can_update`/`write` lọc bằng `dict(zip(s.keys, key))` khi khóa ghép.
Bộ nhập cũ không đổi hành vi; test FEAT-004 giữ nguyên và phải xanh.

Bộ nhập mới (`core/import_sets.py`, đăng ký sau `nc_test_system`):

```python
NC_ACCOUNT_MAPPING = ImportSet(
    key="nc_account_mapping", label="Bảng ánh xạ tài khoản", doctype="NC Account Mapping",
    key_field="accounting_regime", key_fields=("accounting_regime", "account_prefix"),
    columns=(
        Column("accounting_regime", "Chế độ kế toán", "Select", required=True, options=REGIMES, example="Hành chính sự nghiệp"),
        Column("account_prefix", "Tiền tố tài khoản", "Data", required=True, example="61111"),
        Column("cost_category", "Loại chi phí", "Select", required=True, options=COST_CATEGORIES, example="LABOR"),
        Column("note", "Ghi chú", "Data"),
    ),
)
NC_SERVICE_VOLUME = ImportSet(
    key="nc_service_volume", label="Sản lượng dịch vụ", doctype="NC Service Volume",
    key_field="fiscal_year", key_fields=("fiscal_year", "technical_service", "department", "scenario"),
    columns=(
        Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
        Column("technical_service", "Mã dịch vụ", "Link", link_doctype="NC Technical Service", required=True, example="DV-TEST-A"),
        Column("department", "Mã khoa", "Link", link_doctype="NC Department", required=True, example="K01"),
        Column("scenario", "Kịch bản sản lượng", "Select", required=True, options=SCENARIOS, example="Thực tế 12 tháng"),
        Column("volume", "Sản lượng", "Float", required=True, example=4000),
    ),
)
NC_COST_CENTER_DRIVER = ImportSet(
    key="nc_cost_center_driver", label="Tiêu chí trung tâm chi phí", doctype="NC Cost Center Driver",
    key_field="fiscal_year", key_fields=("fiscal_year", "cost_center"),
    columns=(
        Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
        Column("cost_center", "Mã trung tâm chi phí", "Link", link_doctype="NC Cost Center", required=True, example="K01"),
        Column("headcount", "Số nhân lực", "Float", example=20),
        Column("area_m2", "Diện tích (m²)", "Float"),
        Column("revenue", "Doanh thu", "Float"),
    ),
)
```

Mã dịch vụ là `name` của NC Technical Service (`service_code`); mã HIS ngoài (NC Service Code Map) để FEAT-035 (ASM-125). Cột kịch bản bắt buộc trong tệp, ví dụ là giá trị mặc định (ASM-125). Lỗi Link của khung: `"DV-X" không tồn tại trong NC Technical Service`, dòng khác vẫn ghi (TC-ACCT-05). Quyền: chỉ NC Finance (và Administrator) có quyền tạo nên chỉ Finance thấy ba bộ này.

Tệp chi phí kế toán **không** đăng ký vào trang `import-excel` (tạo một bản ghi cha nhiều dòng, không phải upsert danh mục): tải mẫu qua `api.accounting.download_template`, nạp qua form NC Accounting Import.

## 6. Tiêu chí nghiệm thu

Tên test mang mã TC (`test_TC_ACCT_01_...`). Dữ liệu chung (fixture test, `normcore/tests/accounting_fixtures.py`): trung tâm K01, K02 (Lâm sàng), HC (Hỗ trợ); khoa K01 (trung tâm K01); dịch vụ DV-TEST-A, DV-TEST-B; bảng ánh xạ mặc định 2.7. **Tệp vàng dạng tài khoản** (năm 2026, chế độ Hành chính sự nghiệp; 10 dòng, tổng 2.105.000.000):

| Dòng Excel | Mã TK | Tên TK | TTCP | Số tiền | Loại gán |
| :-: | :-- | :-- | :-- | --: | :-- |
| 2 | 61111 | Tiền lương | K01 | 500.000.000 | LABOR |
| 3 | 61111 | Phụ cấp, đóng góp theo lương | K01 | 200.000.000 | LABOR |
| 4 | 61112 | Thuốc, hóa chất, vật tư | K01 | 260.000.000 | DRUG_SUPPLY |
| 5 | 61113 | Khấu hao tài sản cố định | K01 | 300.000.000 | DEPRECIATION |
| 6 | 611122 | Điện, nước | K01 | 40.000.000 | UTILITY |
| 7 | 61118 | Chi khác | K01 | 100.000.000 | MANAGEMENT |
| 8 | 811 | Chi phí khác | K01 | 5.000.000 | EXCLUDED |
| 9 | 61111 | Tiền lương | HC | 300.000.000 | LABOR |
| 10 | 61118 | Chi khác | HC | 150.000.000 | MANAGEMENT |
| 11 | 642 | Chi phí quản lý | HC | 250.000.000 | MANAGEMENT |

Tổng theo (trung tâm, loại) sau khi bỏ dòng loại trừ đúng bảng "Số liệu kế toán đã gán loại chi phí" mục 2.1 test-cases (= `golden_engine.ACCOUNTING`): K01 LABOR 700.000.000, DRUG_SUPPLY 260.000.000, DEPRECIATION 300.000.000, UTILITY 40.000.000, MANAGEMENT 100.000.000; HC LABOR 300.000.000, MANAGEMENT 400.000.000.

| # | Điều kiện kiểm được | TC | FR | Vị trí test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | NC Finance tạo lần nhập 2026 với tệp vàng → `status` "Nháp", `line_count` 10, `total_amount` 2.105.000.000, `error_count` 0; loại từng dòng đúng cột "Loại gán" (611122 khớp tiền tố dài nhất, không phải 61112); dòng 811 `is_excluded` = 1 | TC-ACCT-01 | FR-ACCT-001, 003 | `nc_accounting_import/test_nc_accounting_import.py` |
| 2 | Tệp 4 dòng: 1 dòng số tiền "abc", 1 dòng TTCP "K99" → tạo "Nháp", `error_count` 2, `get_import_summary` có 2 lỗi nêu dòng Excel và cột ("Số tiền", "Mã trung tâm chi phí"), `line_count` 2; `finalize` → `ValidationError` nêu "2 dòng lỗi", trạng thái vẫn "Nháp". Thêm: dòng thiếu mã tài khoản → lỗi "ô bắt buộc"; tệp không phải .xlsx → không tạo bản ghi | TC-ACCT-02 | FR-ACCT-002 | như trên |
| 3 | Tệp vàng + 1 dòng tài khoản 99999 → dòng đó `cost_category` trống; `finalize` → `ValidationError` nêu idx, "99999", "K01"; NC Finance gán loại kèm lý do → chốt được | TC-ACCT-03 | FR-ACCT-005 | như trên |
| 4 | `update_line` đổi LABOR → MANAGEMENT không lý do → `ValidationError` "lý do"; sửa trực tiếp trong bảng (save) không lý do → cũng từ chối; có lý do → lưu, `changed_by` = người dùng Finance, `change_reason` lưu; đánh dấu loại trừ cũng cần lý do | TC-ACCT-04 | FR-ACCT-004 | như trên |
| 5 | Tệp sản lượng 3 dòng (DV-TEST-A 4000, DV-TEST-B 6000, DV-X 10) → `created` 2, `error_count` 1, lỗi nêu dòng 4 và "Mã dịch vụ"; nhập lại → không tạo trùng; mã khoa lạ cũng lỗi dòng; trùng 4 trường trên form → từ chối; mặc định `scenario` = "Thực tế 12 tháng"; cùng (năm, dịch vụ, khoa) khác kịch bản lưu được | TC-ACCT-05 | FR-ACCT-007 | `nc_service_volume/test_nc_service_volume.py`, `api/test_importer_accounting.py` |
| 6 | Chốt lần nhập tệp vàng → "Đã chốt", `totals` 7 dòng đúng bảng tổng trên (so với `golden_engine.ACCOUNTING` bằng `Decimal`); có NC Audit Event "Khóa"; sau đó sửa `amount` một dòng (save) → `ValidationError`; `update_line`, `reapply_mapping`, `reload_file`, `finalize` lần hai → từ chối; Administrator xóa → từ chối | TC-ACCT-06 | FR-ACCT-006, DI-07 | `test_nc_accounting_import.py`; `tests/golden/test_accounting_golden.py` (thuần) |
| 7 | Quy tắc thiếu `driver` → `MandatoryError`; Cấp 2 LABOR HEADCOUNT → `ValidationError` nêu "HEADCOUNT" và "cấp 1"; Cấp 2 LABOR LABOR_MIN → lưu được; Cấp 1 MANAGEMENT HEADCOUNT → lưu được; trùng (cấp, loại, trung tâm) → từ chối; cấp 2 gắn trung tâm HC (Hỗ trợ) → từ chối; AREA, REVENUE ở cấp 2 → từ chối | TC-ACCT-07 | FR-ACCT-008 | `nc_allocation_rule/test_nc_allocation_rule.py` |
| 8 | Trên site test (đã chạy `after_install`): có đủ 13 dòng bảng 2.7 chế độ "Hành chính sự nghiệp", `note` chứa "Giả định — chờ xác nhận"; gọi lại `ensure_default_account_mapping()` không tạo trùng và không ghi đè; NC Finance đổi 61113 → MANAGEMENT; lần nhập mới tệp vàng gán dòng 61113 = MANAGEMENT; lần nhập cũ không đổi; `reapply_mapping` trên "Nháp" cũ đổi theo giá trị mới (trừ dòng sửa tay) | TC-ACCT-08 | FR-ACCT-009 | `nc_account_mapping/test_nc_account_mapping.py` |
| 9 | Nhập tiêu chí 2026: K01 headcount 20, K02 30 (bộ nhập `nc_cost_center_driver`) → 2 bản ghi; trùng (2026, K01) → từ chối; `get_driver_values(2026, "HEADCOUNT")` = {K01: 20, K02: 30}; `driver_shares(...)["K01"]` = `Decimal("0.4")` = golden `HEADCOUNT["K01"] / sum(HEADCOUNT.values())` | TC-ACCT-09 | FR-ACCT-010 | `nc_cost_center_driver/test_nc_cost_center_driver.py`; `tests/golden/test_accounting_golden.py` |
| 10 | Tạo lần nhập thứ hai năm 2026 → tên `KT-2026-02`, `KT-2026-01` không đổi (`modified`, dòng) | — | FR-ACCT-011 | `test_FR_ACCT_011_*` |
| 11 | Quyền 5 DocType khớp ma trận (Finance ghi; Director, Admin, Auditor chỉ đọc; Clinician, Consultant, Resource Manager không đọc; không ai xóa); NC Auditor `update_line`/`finalize`/nhập Excel → `PermissionError`; NC Clinician `get_import_summary` → `PermissionError`; `check_conventions.py` thoát 0 | — | FR-ACC-002, FR-ACC-007 | từng `test_nc_*.py`, `tests/test_permissions.py` |
| 12 | Hàm thuần phủ mọi nhánh `costing/accounting.py`, `costing/allocation_rules.py`; khung nhập: khóa ghép, `unique=False`, test FEAT-004 cũ vẫn xanh | — | FR-ACCT-001..010 | `tests/unit/test_accounting.py`, `tests/unit/test_allocation_rules.py`, `tests/unit/test_importer_composite_key.py` |

## 7. Giả định và rủi ro

Chi tiết ở `docs/decisions/assumptions.md`; sửa thiết kế ở `docs/decisions/amendments/AMD-010.md` (AMD-009 do nhánh FEAT-033 dùng).

| Mã | Tóm tắt |
| :-- | :-- |
| ASM-118 | TBD-03: bảng ánh xạ mặc định 13 dòng (2.7), ghi "Giả định — chờ xác nhận"; cài khi install + patch; chỉ chèn dòng thiếu; chưa có bảng cho "Doanh nghiệp" |
| ASM-119 | `accounting_regime` = Hành chính sự nghiệp / Doanh nghiệp, mặc định Hành chính sự nghiệp ở trường (NC Settings chưa có) |
| ASM-120 | Chuẩn hóa mã tài khoản, khớp tiền tố dài nhất, duy nhất (chế độ, tiền tố); EXCLUDED ⇒ loại trừ |
| ASM-121 | Lỗi mức tệp không tạo bản ghi; lỗi dòng tạo "Nháp" có danh sách lỗi; sửa bằng "Đọc lại tệp" hoặc lần nhập mới; số tiền âm, bằng 0 chấp nhận; năm 2000..2100 |
| ASM-122 | Dòng chỉ sinh từ tệp; chỉ đổi loại/loại trừ (kèm lý do); "Gán lại" bỏ qua dòng sửa tay; "Đọc lại tệp" xóa sửa tay |
| ASM-123 | Chốt: điều kiện, tổng bỏ dòng loại trừ, `total_amount` gồm mọi dòng; sự kiện "Khóa"; không mở lại |
| ASM-124 | Mở rộng khung nhập FEAT-004: khóa ghép `key_fields`, `parse(unique=False)`; tương thích ngược |
| ASM-125 | Sản lượng ≥ 0; cột kịch bản bắt buộc trong tệp; không ràng khoa với khoa thực hiện; mã dịch vụ = `service_code` |
| ASM-126 | Tiêu chí ≥ 0; `get_driver_values`, `driver_shares` (khớp golden, không làm tròn) |
| ASM-127 | Quy tắc: không EXCLUDED; ràng loại trung tâm theo cấp; duy nhất (cấp, loại, trung tâm); cấp 1 dùng mọi tiêu chí; không có năm |
| ASM-128 | Quyền dòng "Số liệu kế toán, sản lượng, phân bổ"; không ai xóa; NC Consultant "cấp riêng" (FR-ACC-004) ngoài phạm vi; đổi số đếm test cũ chờ Lead |
| ASM-129 | SCR-DSK-021 là danh sách + form chuẩn Desk và lối tắt Workspace; liên kết SCR-DSK-037 để FEAT-035 |
| ASM-130 | Không patch cấu trúc; chỉ patch dữ liệu ánh xạ mặc định |

Rủi ro:
- **Bảng ánh xạ mặc định là giả định** (TBD-03): tài khoản thật của bệnh viện có thể khác; dòng không khớp chỉ bị chặn chốt (không gán sai lặng lẽ). Chuyên gia kế toán thay bảng bằng bộ nhập `nc_account_mapping`.
- **Mở rộng khung nhập** (ASM-124) chạm `core/importer.py`, `api/importer.py` của FEAT-004: phải chạy lại toàn bộ test nhập (`api/test_importer*.py`). Nếu Lead muốn giữ khung nguyên vẹn, phương án thay là thêm trường mã ghép (như AMD-008) — cần AMD mới.
- Xung đột khi gộp với nhánh FEAT-033 (số ASM/AMD, `check_conventions.py`, `hooks.py`, `vi.csv`, số đếm DocType): giữ dòng cả hai bên (CLAUDE.md mục 11), đếm lại DocType theo thực tế.
- `before_insert` đọc tệp đồng bộ (tối đa 5.000 dòng như khung FEAT-004); tệp lớn hơn phải tách.
- FEAT-015 nối `NC Costing Run.accounting_import` (Link, phải "Đã chốt" — DI-06) và đọc `totals`; FEAT-017 đọc NC Allocation Rule, NC Cost Center Driver, NC Service Volume (kịch bản "Thực tế 12 tháng").
