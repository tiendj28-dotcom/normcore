# FEAT-026 — Kho giá tham chiếu và chỉ số giá — Thiết kế kỹ thuật

Issue NORM-80. Bản phát hành R3. Phụ thuộc FEAT-004 (khung nhập Excel), FEAT-005 (NC Technical Service, NC Specialty), đều có `DONE` trên `develop`.

Nguồn: `srs.md` FR-BM-001, 002, 004..008, BR-ADJ-009, TBD-01, TBD-11; `use-cases.md` UC-013 (bước 1–5, 1a, 2b; 2a, 2c thuộc FEAT-027); `data-model.md` NC Benchmark Facility, NC Benchmark Price, NC CPI Index, mục 4 dòng "Giá tham chiếu, chỉ số giá"; `ux-foundations.md` SCR-DSK-025; `test-cases.md` TC-BM-01..04, TC-BM-06; As-Built FEAT-004 (cách đăng ký bộ nhập), FEAT-005, FEAT-019 (`exports/annex.py`: mẫu Phụ lục thay được). Giả định: `docs/decisions/assumptions/FEAT-026.md` (ASM-026-01..12).

`docs/golden/` không có hàm cho BR-ADJ-009 (chỉ có BR-COST/BR-CLS). Công thức lấy nguyên văn BR-ADJ-009, giá trị mong đợi lấy từ TC-BM-04; làm tròn theo cách golden làm tròn tiền (`Decimal`, 2 chữ số, `ROUND_HALF_UP`, ASM-026-08).

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-BM-001 | Đủ | NC Benchmark Facility: bốn trường bắt buộc |
| FR-BM-002 | Đủ | Nhập bằng form và bằng bộ nhập Excel `nc_benchmark_price` (khung FEAT-004). Bắt buộc: đơn vị, dịch vụ (mã **hoặc** tên gốc), giá, loại giá, ngày hiệu lực, nguồn (số văn bản **hoặc** đường dẫn **hoặc** tệp, ASM-026-05) |
| FR-BM-004 | Đủ | Đề xuất dịch vụ khớp bằng quy tắc so khớp tên (không gọi AI); dòng chuyển "Đã xác nhận" chỉ khi người dùng xác nhận |
| FR-BM-005 | Đủ (phần dữ liệu) | Hàm thuần `comparable_prices` và API `get_comparable_prices` chỉ trả dòng "Đã xác nhận". Màn hình so sánh: FEAT-028 |
| FR-BM-006 | Đủ | NC CPI Index theo tháng; giá hiệu chỉnh tính khi đọc (không lưu), theo BR-ADJ-009 |
| FR-BM-007 | Đủ | Từ chối dòng trùng ở `validate` (form, API, bộ nhập) và ở `prepare` của bộ nhập (báo lỗi theo dòng) |
| FR-BM-008 | Đủ, mẫu giả định | Phiếu khảo sát `.xlsx` theo cấu trúc giả định của Phụ lục I (TBD-01), mẫu là tệp template thay được (ASM-026-10) |

Ngoài phạm vi: FR-BM-003 (trích PDF bằng AI, UC-013 2a, 2c), gợi ý tên bằng AI, `ai_log` được ghi: FEAT-027. Màn hình và thống kê so sánh (SCR-DSK-027…): FEAT-028. TC-AI-07 phần giá tham chiếu (ASM-023-16): không sửa test FEAT-023, chỉ ghi trong As-Built rằng NC Benchmark Price đã có. `ai/guard.py`: NC Benchmark Price, NC CPI Index đã nằm trong `FORBIDDEN_DOCTYPES`, giữ nguyên; NC Benchmark Facility không thêm vào guard (không có số tiền).

## 2. DocType (module NC Benchmark, `normcore/nc_benchmark/doctype/`)

Cả ba: `track_changes = 1`, nhãn tiếng Việt, không `is_submittable`. Không đổi trường so với `data-model.md` (không cần AMD); chỉ chọn cách đặt tên (data-model không ghi hoặc ghi "tự động").

### 2.1 NC Benchmark Facility — `autoname: field:facility_name` (ASM-026-01), `title_field: facility_name`, `search_fields: province,ownership`

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `facility_name` | Tên đơn vị | Data | Có | duy nhất (đặt tên theo trường) |
| `province` | Tỉnh, thành phố | Data | Có | `in_list_view`, `in_standard_filter` |
| `ownership` | Loại hình | Select: `Công lập` / `Tư nhân` | Có | `in_list_view`, `in_standard_filter` |
| `facility_level` | Hạng hoặc cấp chuyên môn | Data | Có | `in_list_view`; chữ tự do ("Hạng I", "Cấp chuyên sâu"…) |

Thêm `normcore/core/delete_guard/nc_benchmark_facility.json` (`{"doctype": "NC Benchmark Facility"}`) để chặn xóa khi còn giá tham chiếu (cơ chế NORM-37). Ràng buộc bắt buộc bằng `reqd = 1` (Frappe ném `MandatoryError`, TC-BM-06).

### 2.2 NC Benchmark Price — `autoname: format:GTC-{#####}`, `title_field: service_name_raw`, `sort_field: effective_date`

Trường đúng bảng data-model:

| Trường | Kiểu | BB | Thuộc tính thêm |
| :-- | :-- | :-- | :-- |
| `facility` | Link NC Benchmark Facility | Có | list, filter |
| `service_name_raw` | Data | Có | list. Form/bộ nhập bỏ trống mà có `technical_service` → controller điền `service_name` của dịch vụ (ASM-026-04) |
| `technical_service` | Link NC Technical Service | | list, filter |
| `price` | Currency | Có | list; `> 0` |
| `price_category` | Link NC Price Category | Có | filter |
| `effective_date` | Date | Có | list, filter |
| `source_doc_no`, `source_url` | Data | | |
| `source_file` | Attach | | |
| `status` | Select `Đề xuất` / `Đã xác nhận` / `Loại bỏ`, mặc định `Đề xuất` | Có | list, filter |
| `verified_by` | Link User | | read_only |
| `verified_on` | Datetime | | read_only |
| `ai_log` | Link NC AI Log | | read_only (FEAT-027 ghi) |

Thêm một trường HTML `adjusted_html` (không lưu, ở khối "Giá hiệu chỉnh") để form hiện giá hiệu chỉnh (UI). Trường bố cục/HTML không phải trường dữ liệu, không cần AMD.

Controller `nc_benchmark_price.py` (chỉ gọi vào `benchmark/reference.py`):

1. `validate`:
   - Cả `technical_service` và `service_name_raw` trống → lỗi "Cần mã dịch vụ hoặc tên dịch vụ gốc". `service_name_raw` trống → điền tên dịch vụ.
   - `source_doc_no`, `source_url`, `source_file` đều trống → lỗi "Cần nguồn: số văn bản, đường dẫn hoặc tệp nguồn" (FR-BM-002, ASM-026-05).
   - `price <= 0` → lỗi "Giá phải lớn hơn 0".
   - `status = "Đã xác nhận"` mà `technical_service` trống → lỗi "Chưa gắn mã dịch vụ, chưa xác nhận được" (UC-013 hậu điều kiện).
   - Trùng (FR-BM-007): `find_duplicate(self_row, candidates)` với `candidates` = dòng cùng `facility`, `price_category`, `effective_date`, `status != "Loại bỏ"`, `name != self.name`. Có → `frappe.ValidationError` "Trùng giá tham chiếu {name}: cùng đơn vị, dịch vụ, loại giá, ngày hiệu lực" (ASM-026-06).
   - Trạng thái chuyển sang "Đã xác nhận" (mới hoặc đổi): đặt `verified_by = session.user`, `verified_on = now`. Chuyển khỏi "Đã xác nhận": xóa hai trường.
2. `before_insert` — trạng thái ban đầu và đề xuất (FR-BM-004, ASM-026-02, 03):
   - `technical_service` trống → `suggest_service(service_name_raw, services)` với `services` = NC Technical Service `is_active = 1` (`name`, `service_name`); có kết quả → đặt `technical_service`; `status = "Đề xuất"` (luôn, bất kể giá trị gửi lên).
   - `technical_service` do người dùng nhập, `ai_log` trống, `status` gửi lên là mặc định "Đề xuất" và `flags.keep_status` không đặt → `status = "Đã xác nhận"` (người có quyền ghi đã tự gắn mã; chỉ cặp khớp do hệ thống đề xuất mới chờ xác nhận). Dòng có `ai_log` (FEAT-027) giữ "Đề xuất" (TC-BM-05).
   - Hằng `CONFIRM_CODED_ROWS = True` trong `reference.py`; đặt `False` thì mọi dòng mới đều "Đề xuất" (đảo ngược được).

### 2.3 NC CPI Index — `autoname: format:CPI-{#####}`, `title_field: month`, `sort_field: month`

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `month` | Tháng | Date | Có | `unique = 1`; `validate` đưa về ngày 1 của tháng (`reference.month_start`) trước khi kiểm duy nhất; trùng → lỗi "Đã có chỉ số giá tháng MM/YYYY" |
| `index_value` | Chỉ số giá | Float | Có | `> 0`, `precision 4` |
| `source` | Nguồn | Data | | TBD-11: nguồn chỉ số chưa chốt, mô tả trường ghi "Giả định — chờ xác nhận" (ASM-026-09) |

### 2.4 Quyền (data-model mục 4, dòng "Giá tham chiếu, chỉ số giá"; cùng cho ba DocType)

| Vai trò | read | write | create | delete |
| :-- | :-: | :-: | :-: | :-: |
| NC Finance, NC Consultant | 1 | 1 | 1 | 0 |
| NC Department Head, NC Director, NC Admin, NC Auditor | 1 | 0 | 0 | 0 |
| NC Clinician, NC Council, NC Resource Manager, NC Document Controller | — | — | — | — |

Không ai có `delete` (W = tạo và sửa; "Loại bỏ" thay cho xóa, ASM-026-07). `export = 1` cho vai trò có `read`. Ma trận không phạm vi khoa (dòng này Dept Head đọc toàn bộ, không có "(khoa)").

## 3. Thành phần

### 3.1 `normcore/benchmark/reference.py` — thuần, không import `frappe`

| Hàm / hằng | Kết quả | BR/FR |
| :-- | :-- | :-- |
| `STATUS_PROPOSED = "Đề xuất"`, `STATUS_CONFIRMED = "Đã xác nhận"`, `STATUS_REJECTED = "Loại bỏ"`; `CONFIRM_CODED_ROWS = True`; `MATCH_THRESHOLD = 0.5` | Hằng | |
| `normalize_name(text) -> str` | `casefold`, "đ"→"d", NFD bỏ nhóm `Mn`, ký tự không phải chữ/số → khoảng trắng, gộp khoảng trắng, `strip`. `None` → `""` | FR-BM-004 |
| `suggest_service(raw_name, services) -> str \| None` | `services`: list `{"name", "service_name"}`. (1) tên chuẩn hóa trùng hệt → điểm 1; (2) còn lại điểm = Jaccard tập từ đã chuẩn hóa. Lấy điểm cao nhất ≥ `MATCH_THRESHOLD`; hòa điểm → `name` nhỏ nhất. Không có → `None` (dòng giữ "Chưa gắn mã") | FR-BM-004, ASM-026-03 |
| `initial_status(user_service, has_ai_log, keep_status) -> str` | Quy tắc 2.2 bước 2 | FR-BM-004, ASM-026-02 |
| `duplicate_key_matches(a, b) -> bool` | `a`, `b` cùng facility, price_category, effective_date (người gọi đã lọc) và (cả hai có `technical_service` và bằng nhau, **hoặc** `normalize_name(service_name_raw)` bằng nhau) | FR-BM-007, ASM-026-06 |
| `find_duplicate(row, candidates) -> str \| None` | `name` dòng đầu tiên trong `candidates` (bỏ `status = Loại bỏ`, bỏ `name` của chính nó) mà `duplicate_key_matches` | FR-BM-007 |
| `comparable_prices(rows) -> list` | Giữ dòng `status == "Đã xác nhận"`, giữ thứ tự | FR-BM-005 |
| `month_start(d) -> date` | `date(d.year, d.month, 1)`; nhận `date`, `datetime`, chuỗi ISO | FR-BM-006 |
| `adjusted_price(price, index_effective, index_target) -> Decimal` | `Decimal(price) × Decimal(index_target) ÷ Decimal(index_effective)`, `quantize(Decimal("0.01"), ROUND_HALF_UP)`. Chỉ số `<= 0` hoặc `None` → `ValueError` | **BR-ADJ-009**, ASM-026-08 |
| `adjust(row, cpi_by_month, target_month) -> dict` | `cpi_by_month`: `{date(đầu tháng): float}`. Có đủ hai chỉ số → `{"adjusted_price": Decimal, "index_effective", "index_target", "target_month"}`; thiếu → `{"adjusted_price": None, "missing": [tháng thiếu]}` (BR-ADJ-009 "Không áp dụng") | BR-ADJ-009 |

Độ phủ `normcore/benchmark/` ≥ 90% (cùng lệnh `--cov=normcore/benchmark`). `benchmark/rules.py` (BR-ADJ-001..007) chưa có ở FEAT này: thuộc FEAT-028/029 theo `architecture.md` (ASM-026-11).

### 3.2 `normcore/exports/price_survey.py` — thuần (FR-BM-008)

- `SURVEY_COLUMNS`: đúng nhãn cột của bộ nhập 3.3 để tệp khảo sát điền xong nhập lại được (UC-013 1a: "rồi nhập kết quả"): `Đơn vị`, `Mã dịch vụ`, `Tên dịch vụ gốc`, `Giá`, `Loại giá`, `Ngày hiệu lực`, `Số văn bản nguồn`, `Đường dẫn nguồn`. Lấy từ `import_sets.NC_BENCHMARK_PRICE.columns` để chỉ có một nguồn (Dev import hằng).
- `INFO_ROWS`: tờ thứ hai "Thông tin phiếu": Đơn vị được khảo sát, Tỉnh/thành phố, Loại hình, Hạng, Nhóm dịch vụ, Loại giá, Người lập, Ngày lập, Hạn gửi lại (trống), Ghi chú "Cấu trúc theo Phụ lục I Thông tư 21/2024/TT-BYT — Giả định, chờ xác nhận (TBD-01)".
- `build_survey(facility: dict, services: list[dict], price_category, meta: dict) -> bytes`: nạp `templates/phu_luc_i.xlsx` nếu có (thay được), không thì dựng từ hằng; tờ 1 dòng 1 là tiêu đề cột, mỗi dịch vụ một dòng (điền sẵn Đơn vị = `facility_name`, Mã, Tên, Loại giá; Giá, Ngày, Nguồn để trống). Thứ tự dịch vụ theo mã.
- `normcore/exports/templates/phu_luc_i.xlsx`: sinh từ hằng (như FEAT-019), commit vào repo.

### 3.3 Bộ nhập `nc_benchmark_price` — `normcore/core/import_sets.py` (nối thêm, không sửa khung)

```python
NC_BENCHMARK_PRICE = ImportSet(
    key="nc_benchmark_price", label="Giá tham chiếu", doctype="NC Benchmark Price",
    key_field="service_name_raw",
    key_fields=("facility", "service_name_raw", "price_category", "effective_date"),
    prepare="normcore.api.benchmark.prepare_benchmark_price",
    columns=(
        Column("facility", "Đơn vị", "Link", link_doctype="NC Benchmark Facility", required=True, example="Bệnh viện mẫu"),
        Column("technical_service", "Mã dịch vụ", "Link", link_doctype="NC Technical Service", example=<mã ví dụ>),
        Column("service_name_raw", "Tên dịch vụ gốc", "Data", example="Định lượng Glucose"),
        Column("price", "Giá", "Float", required=True, example=25000),
        Column("price_category", "Loại giá", "Link", link_doctype="NC Price Category", required=True, example=<mã loại giá mẫu>),
        Column("effective_date", "Ngày hiệu lực", "Date", required=True, example="2026-01-01"),
        Column("source_doc_no", "Số văn bản nguồn", "Data", example="123/QĐ-BV"),
        Column("source_url", "Đường dẫn nguồn", "Data"),
    ),
)
```

- Ví dụ trong mẫu phải nhập được (G2 FEAT-004): Dev dùng đơn vị/dịch vụ/loại giá có trong dữ liệu cài sẵn hoặc demo; nếu không có đơn vị cài sẵn, ghi rõ trong As-Built rằng dòng ví dụ cần tạo đơn vị "Bệnh viện mẫu" trước (theo cách các bộ nhập Link khác đã làm).
- `prepare_benchmark_price(values)` (`normcore/api/benchmark.py`, chạy ở cả "thu" và "ghi"):
  1. Không có `technical_service` và không có `service_name_raw` → `RowValueError("Tên dịch vụ gốc", "cần mã dịch vụ hoặc tên dịch vụ gốc")`.
  2. Có mã mà thiếu tên → trả `service_name_raw = service_name`.
  3. Thiếu cả `source_doc_no`, `source_url` → `RowValueError("Số văn bản nguồn", "cần số văn bản hoặc đường dẫn nguồn")`.
  4. `find_duplicate` với các dòng đã lưu (như `validate`) → `RowValueError("Tên dịch vụ gốc", "trùng giá tham chiếu {name} (cùng đơn vị, dịch vụ, loại giá, ngày hiệu lực)")`. Nhờ bước này, dòng trùng luôn bị từ chối, không rơi vào nhánh "cập nhật"/"không đổi" của khung (TC-BM-02, ASM-026-06).
  5. Không đặt `status`: `before_insert` quyết (2.2), để form, bộ nhập, FEAT-027 cùng một luật.
- Trùng trong cùng tệp: khung tự báo theo `key_fields` (khóa thô). Trùng sau chuẩn hóa tên trong cùng tệp: dòng sau bị `validate` từ chối khi ghi (lỗi dòng), chấp nhận được.

### 3.4 API — `normcore/api/benchmark.py` (mới; mọi hàm `@frappe.whitelist()`, kiểm quyền tường minh)

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `confirm_prices(names, technical_service=None)` | `names`: list hoặc JSON; `technical_service` chỉ khi một dòng (đổi cặp khớp trước khi xác nhận) | `{"confirmed": [names], "errors": [{"name", "message"}]}` | `has_permission("NC Benchmark Price", "write", doc)` từng dòng, thiếu → `PermissionError`. Dòng "Loại bỏ" hoặc chưa có mã → lỗi dòng, các dòng khác vẫn xác nhận. Mỗi dòng `doc.status = "Đã xác nhận"; doc.save()` |
| `reject_prices(names)` | list | `{"rejected": [names]}` | quyền ghi; đặt "Loại bỏ" |
| `reopen_prices(names)` | list | `{"reopened": [names]}` | quyền ghi; "Đã xác nhận"/"Loại bỏ" → "Đề xuất" (đảo ngược) |
| `get_comparable_prices(technical_service, price_category=None, target_month=None)` | mã dịch vụ; tùy chọn | `{"rows": [{"name", "facility", "facility_name", "province", "ownership", "facility_level", "price", "price_category", "effective_date", "source_doc_no", "source_url", "adjusted": <adjust()>}], "target_month"}`. Chỉ dòng "Đã xác nhận" qua `reference.comparable_prices` (FR-BM-005). `target_month` mặc định = tháng có chỉ số mới nhất | `has_permission(..., "read")`; thiếu → `PermissionError`. FEAT-028 dùng hàm này |
| `get_adjusted_price(name, target_month=None)` | một dòng | `adjust()` + `price`, `effective_date` | quyền đọc dòng đó |
| `download_price_survey(facility, price_category, specialty=None, services=None)` | đơn vị khảo sát; loại giá; nhóm dịch vụ = một chuyên khoa **hoặc** danh sách mã | tệp `phieu-khao-sat-gia-<facility>.xlsx` (`frappe.response` binary) | `has_permission("NC Benchmark Price", "create")`; không có dịch vụ nào → lỗi "Nhóm dịch vụ trống". Chỉ dịch vụ `is_active = 1` |
| `prepare_benchmark_price(values)` | — | (không whitelist) | 3.3 |

Đọc dịch vụ/đơn vị bằng `frappe.get_all` sau khi đã kiểm quyền trên NC Benchmark Price (bỏ qua quyền đọc NC Technical Service vì mọi vai trò có quyền đọc giá đều đọc được dịch vụ).

### 3.5 Khác

- `normcore/nc_core/workspace/normcore/shortcuts.d/FEAT-026.txt`: ba lối tắt "Đơn vị tham chiếu", "Giá tham chiếu", "Chỉ số giá tiêu dùng"; chạy `python3 scripts/build_workspace.py` (không sửa tay `normcore.json`).
- Bản dịch chuỗi JS: `normcore/translations/vi.d/FEAT-026.csv`.
- Không hook mới ngoài delete_guard; không tác vụ nền; không fixtures mới (mẫu Excel sinh từ `import_sets`, mẫu Phụ lục I là tệp trong `exports/templates/`). Ba DocType mới chưa lên staging → không cần patch.

## 4. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Tạo NC Benchmark Facility thiếu `province` → `frappe.MandatoryError`; tạo lại đủ tên, tỉnh, loại hình, hạng → lưu được | TC-BM-06 | FR-BM-001 | `test_TC_BM_06_don_vi_tham_chieu_bat_buoc` (`nc_benchmark_facility/test_nc_benchmark_facility.py`) |
| 2 | Nhập tệp 5 dòng (3 dòng có mã, 2 dòng chỉ tên gốc khớp được) chế độ "ghi" → `created = 5`, `errors = []`; 2 dòng tên gốc có `technical_service` = dịch vụ mong đợi và `status = "Đề xuất"`, `verified_by` trống; 3 dòng có mã `status = "Đã xác nhận"` | TC-BM-01 | FR-BM-002, FR-BM-004 | `test_TC_BM_01_nhap_tep_de_xuat_dich_vu` (`api/test_benchmark.py`) |
| 3 | Nhập lại một dòng trùng đơn vị, dịch vụ, loại giá, ngày → `created = 0`, có đúng một lỗi dòng chứa "trùng"; số dòng NC Benchmark Price không đổi. Chèn trực tiếp `frappe.get_doc(...).insert()` trùng → `frappe.ValidationError` | TC-BM-02 | FR-BM-007 | `test_TC_BM_02_tu_choi_dong_trung` |
| 4 | Dịch vụ có 3 giá "Đã xác nhận" và 1 "Đề xuất" → `get_comparable_prices(svc)["rows"]` có đúng 3 dòng, đúng 3 `name` đã xác nhận | TC-BM-03 | FR-BM-005 | `test_TC_BM_03_so_sanh_chi_dung_gia_da_xac_nhan` |
| 5 | `adjusted_price(200000, 100, 104) == Decimal("208000.00")` | TC-BM-04 | FR-BM-006, BR-ADJ-009 | `test_TC_BM_04_gia_hieu_chinh` (`tests/unit/test_benchmark_reference.py`) |
| 6 | Tích hợp: NC CPI Index tháng hiệu lực 100, tháng tính 104; `get_adjusted_price` → 208000.00; thiếu chỉ số → `adjusted_price None`, `missing` nêu tháng | TC-BM-04 | FR-BM-006 | `test_TC_BM_04_gia_hieu_chinh_tren_site` |
| 7 | `suggest_service`: trùng hệt sau chuẩn hóa (dấu, hoa thường, dấu câu); Jaccard dưới ngưỡng → `None`; hòa điểm → mã nhỏ nhất | — | FR-BM-004 | `test_FR_BM_004_so_khop_ten` (unit) |
| 8 | `confirm_prices` đặt "Đã xác nhận", `verified_by`, `verified_on`; dòng chưa có mã → lỗi dòng; `reject_prices`, `reopen_prices` đổi trạng thái | — | FR-BM-004, FR-BM-005 | `test_FR_BM_004_xac_nhan_cap_khop` |
| 9 | Form: thiếu nguồn → lỗi; thiếu cả mã và tên → lỗi; giá ≤ 0 → lỗi; xác nhận khi chưa có mã → lỗi | — | FR-BM-002 | `test_FR_BM_002_bat_buoc_khi_nhap_tay` |
| 10 | NC CPI Index: tháng đưa về ngày 1; trùng tháng → lỗi; chỉ số ≤ 0 → lỗi | — | FR-BM-006 | `test_FR_BM_006_chi_so_gia_theo_thang` |
| 11 | `download_price_survey` theo chuyên khoa → `.xlsx` có tờ 1 tiêu đề đúng `SURVEY_COLUMNS`, một dòng mỗi dịch vụ đang dùng của chuyên khoa; tệp đó điền giá, ngày, nguồn rồi nhập bằng `nc_benchmark_price` → tạo được dòng | — | FR-BM-008 | `test_FR_BM_008_phieu_khao_sat` |
| 12 | Quyền: NC Clinician (không quyền) bị `PermissionError` khi đọc/tạo ba DocType và gọi `get_comparable_prices`, `confirm_prices`, `download_price_survey`; NC Auditor đọc được, tạo/sửa/`confirm_prices`/nhập Excel bị từ chối; NC Finance, NC Consultant tạo và xác nhận được; NC Department Head, NC Director chỉ đọc | — | FR-ACC-007, data-model mục 4 | `test_quyen_feat_026_*` trong test của từng DocType và `api/test_benchmark.py` |
| 13 | Xóa NC Benchmark Facility còn giá tham chiếu → bị chặn | — | FR-BM-001 | `test_FR_BM_001_chan_xoa_don_vi_dang_dung` |

`check_conventions.py` xanh (tiền tố, nhãn, `track_changes`, Auditor không quyền ghi); `build_rtm.py` không thêm vấn đề.

## 5. Giả định và rủi ro

- ASM-026-01..12 ở `docs/decisions/assumptions/FEAT-026.md`.
- Rủi ro: so khớp tên bằng Jaccard có thể đề xuất sai khi tên ngắn; giảm thiểu bằng xác nhận bắt buộc (FR-BM-005 chặn dòng chưa xác nhận khỏi so sánh) và ngưỡng là hằng đổi được. FEAT-027 thêm gợi ý AI.
- Rủi ro: mẫu Phụ lục I chính thức (TBD-01) khác cấu trúc giả định → chỉ thay `exports/templates/phu_luc_i.xlsx` và `INFO_ROWS`; cột dữ liệu giữ khớp bộ nhập.
- Rủi ro: nguồn CPI (TBD-11) chưa chốt → nhập tay; không tự tải từ bên ngoài.
