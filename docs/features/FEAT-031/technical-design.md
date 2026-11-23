# FEAT-031 — Dịch vụ cận lâm sàng và hệ thống xét nghiệm — Thiết kế kỹ thuật

Issue NORM-25. Nguồn: `srs.md` FR-SVC-008..011, FR-CLS-001, FR-CLS-002, FR-CLS-005..008, FR-ACC-008, BR-CLS-001 (chỉ ý nghĩa hai tỷ lệ ước tính); `use-cases.md` UC-019 (bước 1, 2, 5; luồng 1a, 1b, 1c, 2a..2d, 5a); `data-model.md` 3.3 (NC Technical Service, NC Service Code Map, NC Panel Component), 3.5 (NC Test System), mục 4 dòng "Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm", DI-06, DI-07, DI-09; `ux-foundations.md` SCR-DSK-006, SCR-DSK-032; TC-CLS-20..23. Phụ thuộc đã DONE: FEAT-001 (phạm vi khoa), FEAT-005 (NC Technical Service, SCR-DSK-006), FEAT-010 (NC Equipment). Khung nhập: FEAT-004.

Không viết lại cơ chế đã có: phạm vi khoa dùng `core/permissions.py::SCOPE_RULES` (FEAT-001); bộ nhập đăng ký vào `core/import_sets.py` (FEAT-004, không sửa khung); chặn xóa bản ghi bị tham chiếu dùng `core/references.py` (đã chạy cho NC Technical Service, NC Equipment).

## 1. Phạm vi

| FR | Mức | Làm gì ở FEAT này |
| :-- | :-- | :-- |
| FR-SVC-008 | Must | NC Technical Service thêm `is_paraclinical`, `cls_group`, `result_unit`; hai trường sau bắt buộc khi `is_paraclinical` |
| FR-SVC-009 | Must | Bảng con NC Service Code Map; DI-09 kiểm ở `validate` và bằng chỉ mục duy nhất CSDL |
| FR-SVC-010 | Should | `is_panel`, `panel_costing_mode`, bảng con NC Panel Component; **chỉ lưu**. Cách tính giá theo bộ / theo thông số dùng ở FEAT tính giá cận lâm sàng (FEAT-036). TBD-17 → ASM-107 |
| FR-SVC-011 | Could | `is_send_out`, `send_out_price`; lần tính giá bỏ qua bộ định mức của dịch vụ gửi ngoài (ASM-108) |
| FR-CLS-001, FR-CLS-002 | Must | DocType mới NC Test System; nhiều hệ thống cho một (dịch vụ, khoa) |
| FR-CLS-005 | Should | `machine_minutes_per_case` bắt buộc khi thiết bị chính chia theo "Phút chiếm máy". Ngoài nghiệm thu R1 nhưng vẫn cài ràng buộc |
| FR-CLS-006 | Should | `status` Đang dùng / Ngừng dùng; hàm chọn hệ thống cho lần tính mới (DI-06 [1.1]); lần tính đã khóa không bị đụng (ASM-114) |
| FR-CLS-007 | Should | Khối tình trạng trên SCR-DSK-032: bốn mục (bộ định mức, kế hoạch chất lượng, sản lượng kịch bản mặc định, k và giá thành lần tính gần nhất). **Một phần:** dữ liệu nguồn thuộc FEAT-032, 034, 035, 036 nên ở FEAT này cả bốn mục hiện "Chưa có" (ASM-115). Cảnh báo tổng tỷ trọng ≠ 100% làm thật |
| FR-CLS-008 | Should | **Một phần:** bộ nhập `nc_test_system`. Kế hoạch chất lượng (FEAT-032) và hồ sơ tuân thủ (FEAT-033) đăng ký bộ nhập ở FEAT của chúng (ASM-116) |
| FR-ACC-008 | Must | Thêm `"NC Test System": ScopeRule()` vào `SCOPE_RULES` và hai hook trong `hooks.py`. Phần kế hoạch chất lượng làm ở FEAT-032 bằng cùng cách |

Không làm: FR-CLS-003, FR-CLS-004 (dừng tính khi tổng tỷ trọng ≠ 100%, tỷ trọng từ Qbn: FEAT-036); hệ số k và giá thành một kết quả (BR-CLS-001, FEAT-036; không tự chế công thức k); `test_system` trên NC Norm Set, DI-03 sửa, DI-15 (FEAT-034); NC QC Plan, cảnh báo "thiếu kế hoạch nội kiểm" (FEAT-032); NC Test System Volume (FEAT-035).

## 2. DocType

Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1 cho DocType cha.

### 2.1 Mở rộng NC Technical Service (mô-đun NC Procedure, đã lên staging)

Thêm sau mục "Khoa thực hiện" một Section Break `cls_section` "Cận lâm sàng" (thu gọn được). Đúng tên trường ở data-model 3.3:

| Trường | Nhãn | Kiểu | Ràng buộc |
| :-- | :-- | :-- | :-- |
| is_paraclinical | Thuộc khối cận lâm sàng | Check | Mặc định 0 |
| cls_group | Nhóm chuyên ngành | Select | `Hóa sinh`, `Miễn dịch`, `Huyết học`, `Vi sinh`, `Giải phẫu bệnh`, `Chẩn đoán hình ảnh`, `Thăm dò chức năng`, `Khác` (thứ tự FR-SVC-008); `depends_on`, `mandatory_depends_on: eval:doc.is_paraclinical` |
| result_unit | Đơn vị kết quả | Select | `Kết quả xét nghiệm`, `Ca chụp`; như trên |
| external_codes | Mã trên hệ thống ngoài | Table NC Service Code Map | Hiện mọi dịch vụ (FR-SVC-009 không giới hạn cận lâm sàng; FR-ACCT-013 dùng) |
| is_panel | Là dịch vụ bộ | Check | `depends_on: is_paraclinical` |
| panel_costing_mode | Cách tính dịch vụ bộ | Select | `Theo cả bộ`, `Theo từng thông số`; mặc định `Theo từng thông số`; mô tả trường "Giả định — chờ xác nhận (TBD-17)"; `depends_on: is_panel` (ASM-107) |
| panel_components | Thông số thành phần | Table NC Panel Component | `depends_on: is_panel` |
| is_send_out | Gửi ngoài | Check | `depends_on: is_paraclinical` |
| send_out_price | Giá hợp đồng gửi mẫu | Currency | `depends_on`, `mandatory_depends_on: is_send_out` |
| cls_systems_html | Hệ thống xét nghiệm | HTML | Danh sách hệ thống của dịch vụ (ui-design) |

Thêm `links` (Kết nối): `{"link_doctype": "NC Test System", "link_fieldname": "technical_service", "group": "Cận lâm sàng"}`.

**Bảng con mới (mô-đun NC Procedure, `istable` = 1):**
- **NC Service Code Map**: `source_system` (Select `HIS` / `LIS` / `RIS`, BB, `in_list_view`), `external_code` (Data, BB, `in_list_view`), `external_name` (Data). Hàm `on_doctype_update` trong `nc_service_code_map.py` tạo chỉ mục duy nhất `(source_system, external_code)` bằng `frappe.db.add_unique` (DI-09 khi hai người lưu đồng thời).
- **NC Panel Component**: `parameter_code` (Data, BB), `parameter_name` (Data, BB), `technical_service` (Link NC Technical Service, tùy chọn).

**`validate` của NC Technical Service** (gọi hàm thuần `procedure/service_rules.py`, mục 4):

| Điều kiện | Kết quả |
| :-- | :-- |
| `is_paraclinical` mà thiếu `cls_group` hoặc `result_unit` | từ chối, nêu trường thiếu (TC-CLS-20) |
| Bỏ `is_paraclinical` khi đang có NC Test System trỏ tới dịch vụ | từ chối, nêu mã hệ thống (ASM-109) |
| Hai dòng `external_codes` cùng (`source_system`, `external_code`) trong một dịch vụ | từ chối |
| (`source_system`, `external_code`) đã thuộc dịch vụ khác | từ chối: "Mã LIS L100 đã gắn với dịch vụ <mã> — <tên>" (DI-09, TC-CLS-21). Mã được cắt khoảng trắng hai đầu, so không phân biệt hoa thường (ASM-110) |
| `is_panel` mà `panel_components` rỗng; `parameter_code` lặp trong bộ; dòng thành phần trỏ chính dịch vụ | từ chối (ASM-107) |
| `is_send_out` mà `send_out_price` trống hoặc ≤ 0 | từ chối (ASM-108) |
| `is_paraclinical` = 0 | `cls_group`, `result_unit`, cờ bộ, gửi ngoài không bắt buộc; giá trị cũ giữ nguyên (ẩn trên form) |

Quyền không đổi (dòng "Dịch vụ kỹ thuật, chuyên khoa": Doc Controller, Admin ghi). Bảng con theo quyền của cha.

### 2.2 DocType mới NC Test System (mô-đun NC Costing, data-model 3.5)

Autoname `field:test_system_code`; `title_field` = `test_system_code`; `search_fields` = `technical_service, department`; `track_changes` = 1; sắp xếp `test_system_code asc`.

| Trường | Nhãn | Kiểu | BB | Ràng buộc |
| :-- | :-- | :-- | :-- | :-- |
| test_system_code | Mã hệ thống | Data | Có | Duy nhất (`unique`), cắt khoảng trắng |
| technical_service | Dịch vụ | Link NC Technical Service | Có | Dịch vụ phải có `is_paraclinical` = 1 |
| department | Khoa | Link NC Department | Có | Phạm vi quyền FR-ACC-008 |
| main_equipment | Thiết bị chính | Link NC Equipment | Có | |
| volume_share_pct | Tỷ trọng sản lượng (%) | Percent | Có | 0 < x ≤ 100 (ASM-111) |
| machine_minutes_per_case | Phút chiếm máy một ca | Float | Điều kiện | BB và > 0 khi `main_equipment.allocation_basis` = "Phút chiếm máy" (FR-CLS-005); ngược lại không bắt buộc, nếu có phải > 0 |
| est_rerun_rate | Tỷ lệ chạy lại ước tính (%) | Percent | | Mặc định 0; 0 ≤ x ≤ 100 |
| est_wastage_rate | Tỷ lệ hao hụt ước tính (%) | Percent | | Mặc định 0; 0 ≤ x < 100 (h < 1 vì BR-CLS-001 chia cho 1 − h) |
| status | Trạng thái | Select | Có | `Đang dùng` / `Ngừng dùng`, mặc định `Đang dùng`, `in_list_view`, `in_standard_filter` |
| status_section, status_html | Tình trạng | Section Break, HTML | | Khối tình trạng FR-CLS-007 (không lưu) |

Không thêm trường nào ngoài data-model (kể cả trường `fetch_from` hiển thị): form tự đọc `allocation_basis` của thiết bị chính bằng `frappe.db.get_value` để bật nhắc bắt buộc phút chiếm máy; máy chủ luôn đọc giá trị hiện tại của NC Equipment ở `validate`.

Tỷ lệ lưu theo phần trăm (2 nghĩa là 2%). FEAT-036 chia 100 khi đưa vào BR-CLS-001 (`golden_cls.py` dùng phân số 0,02, 0,03).

**`validate`** (hàm thuần `costing/test_systems.py::validate_test_system`): các ràng buộc ở bảng trên; lỗi tiếng Việt nêu trường. Không kiểm khoa của hệ thống có nằm trong "Khoa thực hiện" của dịch vụ, không kiểm khoa của thiết bị (ASM-111). Không kiểm tổng tỷ trọng khi lưu (mỗi lần chỉ lưu một hệ thống): chỉ cảnh báo (ASM-112).

**Quyền (data-model mục 4, dòng "Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm")**: Clinician W (khoa), Dept Head W (khoa), Council —, Finance R, Resource Manager R, Doc Controller —, Director R, Consultant R, Admin R, Auditor R. Mã ma trận `W W - R R - R R R R`. Không vai trò nào có quyền xóa (tiền lệ ASM-015, ASM-090): bỏ dùng bằng "Ngừng dùng". `scripts/check_conventions.py`: thêm dòng MATRIX `"Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm": "W W - R R - R R R R"` và `DOCTYPE_ROW["NC Test System"]`. Phạm vi khoa: `SCOPE_RULES["NC Test System"] = ScopeRule()` (đọc và ghi chỉ trong khoa được gán, giống NC Norm Set theo ASM-039; đổi `department` sang khoa khác bị chặn sẵn bởi `has_permission`) (ASM-113).

**Luồng trạng thái:** không có Workflow. `Đang dùng` ⇄ `Ngừng dùng` bằng sửa trường (nút trên form, ui-design). DI-07: hệ thống xét nghiệm là dữ liệu gốc không khóa, sửa được sau khi có lần tính khóa.

### 2.3 NC Costing Run (đổi hành vi, không đổi cấu trúc)

- Thêm phương thức `test_systems_in_scope(self)` (không whitelist): trả danh sách mã NC Test System `status` = "Đang dùng", sắp theo mã, qua hàm thuần `test_systems.in_costing_scope`. Đây là điểm DI-06 [1.1] cho FEAT-034/036 dùng.
- Trong `_run`: bỏ bộ định mức có `ns.get("test_system")` không thuộc tập trên (trường do FEAT-034 thêm; nay luôn trống nên không đổi kết quả hiện có) và bỏ bộ định mức của dịch vụ `is_send_out` = 1 (FR-SVC-011). Lọc bằng hàm thuần `test_systems.norm_sets_to_cost(norm_sets, active_systems, send_out_services)`.
- Không chạm lần tính "Đã tính"/"Đã khóa": `run_costing` đã chỉ chạy từ Nháp / Tính lỗi; đổi trạng thái hệ thống không có hook nào ghi vào NC Costing Run hay NC Service Cost (TC-CLS-23 "lần đã khóa giữ nguyên").

### 2.4 Patch

Không viết patch (ASM-117): NC Technical Service chỉ thêm trường cho phép trống (Check mặc định 0 do migrate đặt); `panel_costing_mode` trống ở bản ghi cũ không có tác dụng khi `is_panel` = 0; chỉ mục duy nhất tạo ở `on_doctype_update` khi migrate (bảng mới, chưa có dữ liệu trùng). NC Test System là DocType mới.

## 3. API whitelisted — `normcore/api/test_system.py`

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `get_status(test_system)` | mã hệ thống | `{"test_system", "status", "items": [{"key", "label", "state": "empty", "message": "Chưa có", "source": "FEAT-0xx"}], "warnings": [{"code": "share_total", "message", "total"}, {"code": "inactive", "message"}]}`; bốn `key`: `norm_set`, `qc_plan`, `volume`, `latest_cost` | `frappe.has_permission("NC Test System", "read", doc, throw=True)` (Auditor, Finance đọc được; Clinician khoa khác → `PermissionError`) |
| `get_service_systems(service)` | mã dịch vụ | `{"service", "is_paraclinical", "can_create", "departments": [{"department", "department_name", "total_share", "warning", "systems": [{"name", "main_equipment", "equipment_name", "volume_share_pct", "status"}]}]}`; chỉ hệ thống người xem đọc được (`frappe.get_list`), tổng tỷ trọng tính trên hệ thống "Đang dùng" | Quyền đọc NC Technical Service (`throw=True`); `can_create` = `frappe.has_permission("NC Test System", "create")` |

Cảnh báo `share_total`: tổng `volume_share_pct` các hệ thống "Đang dùng" cùng (dịch vụ, khoa) khác 100 → "Tổng tỷ trọng của dịch vụ <mã> tại khoa <khoa> là <x>%, khác 100%" (ASM-112). Tổng tính trên mọi hệ thống của (dịch vụ, khoa) bằng `frappe.get_all` (máy chủ, không lộ mã của hệ thống người xem không đọc được: chỉ trả con số). Cảnh báo `inactive`: "Hệ thống đã ngừng dùng: không vào các lần tính giá mới".

## 4. Logic thuần (không import `frappe`)

### `normcore/costing/test_systems.py` (độ phủ ≥ 90%)
| Hàm | Việc | Căn cứ |
| :-- | :-- | :-- |
| `validate_test_system(values, allocation_basis, service_is_paraclinical) -> list[str]` | Trả danh sách lỗi (rỗng = hợp lệ) theo bảng 2.2 | FR-CLS-001, FR-CLS-005, ASM-111 |
| `in_costing_scope(systems) -> list[str]` | Mã các hệ thống `status` = "Đang dùng", sắp theo mã | FR-CLS-006, DI-06 |
| `norm_sets_to_cost(norm_sets, active_systems, send_out_services) -> list` | Giữ bộ định mức không gắn hệ thống hoặc gắn hệ thống đang dùng, và dịch vụ không gửi ngoài | FR-CLS-006, FR-SVC-011 |
| `share_totals(systems) -> dict[(service, department), Decimal]` | Tổng tỷ trọng các hệ thống đang dùng | ASM-112 (chỉ cảnh báo; FR-CLS-003 thuộc FEAT-036) |
| `share_warning(total) -> bool` | `total != 100` | ASM-112 |
| `status_items() -> list[dict]` | Bốn mục khối tình trạng, nhãn tiếng Việt, `state` "empty" | FR-CLS-007, ASM-115 |

Tỷ trọng dùng `Decimal(str(x))`; không có phép tính tiền nào. Không có công thức k ở FEAT này.

### `normcore/procedure/service_rules.py`
| Hàm | Việc | Căn cứ |
| :-- | :-- | :-- |
| `normalize_code(code) -> str` | Cắt khoảng trắng; khóa so sánh `upper()` | ASM-110 |
| `duplicate_codes(rows) -> list[(source_system, external_code)]` | Cặp lặp trong cùng dịch vụ | DI-09 |
| `cls_errors(values) -> list[str]` | Thiếu nhóm / đơn vị khi cận lâm sàng; bộ rỗng; thông số lặp; thành phần trỏ chính mình; gửi ngoài thiếu giá | FR-SVC-008, 010, 011 |

Kiểm trùng với dịch vụ khác (cần CSDL) ở controller: `frappe.get_all("NC Service Code Map", filters={"parenttype": "NC Technical Service", "parent": ["!=", self.name]}, fields=["parent","source_system","external_code"])` rồi so bằng khóa chuẩn hóa.

## 5. Bộ nhập `nc_test_system` (FR-CLS-008, `core/import_sets.py`)

```python
NC_TEST_SYSTEM = ImportSet(
    key="nc_test_system", label="Hệ thống xét nghiệm", doctype="NC Test System", key_field="test_system_code",
    columns=(
        Column("test_system_code", "Mã hệ thống", "Data", required=True, example="GLU-A"),
        Column("technical_service", "Mã dịch vụ", "Link", link_doctype="NC Technical Service", required=True, example="GLU"),
        Column("department", "Mã khoa", "Link", link_doctype="NC Department", required=True, example="HS"),
        Column("main_equipment", "Mã thiết bị chính", "Link", link_doctype="NC Equipment", required=True, example="EQ_A"),
        Column("volume_share_pct", "Tỷ trọng sản lượng (%)", "Float", required=True, example=75),
        Column("machine_minutes_per_case", "Phút chiếm máy một ca", "Float"),
        Column("est_rerun_rate", "Tỷ lệ chạy lại ước tính (%)", "Float", example=2),
        Column("est_wastage_rate", "Tỷ lệ hao hụt ước tính (%)", "Float", example=3),
        Column("status", "Trạng thái", "Select", options=("Đang dùng", "Ngừng dùng")),
    ),
)
```

Khung FEAT-004 đã có: mã thiết bị lạ → lỗi dòng `"EQ_X" không tồn tại trong NC Equipment`, các dòng đúng vẫn ghi (TC-CLS-23). Ràng buộc nghiệp vụ ở `validate` thành lỗi dòng. Ô trống: tạo mới lấy mặc định DocType, cập nhật giữ nguyên (như ASM-084). Quyền: tạo cần quyền tạo NC Test System, nên chỉ Clinician, Dept Head (và Administrator) thấy bộ này; phạm vi khoa áp qua `has_permission` khi ghi: dòng của khoa không được gán thành lỗi dòng. Dòng ví dụ của tệp mẫu chỉ nhập được khi dữ liệu GLU, HS, EQ_A có sẵn (G2 của FEAT-004 yêu cầu dòng ví dụ đúng định dạng; test tạo sẵn dữ liệu đó). Danh sách bộ nhập của Finance, Resource Manager, Auditor ở `api/test_importer.py` **không đổi** (không có quyền tạo).

## 6. Tiêu chí nghiệm thu

Tên test mang mã TC (`test_TC_CLS_20_...`). Dữ liệu: dịch vụ GLU, khoa HS (Hóa sinh), EQ_A (Mua, Số kết quả), EQ_B (Đặt theo hóa chất, Số kết quả); GLU-A EQ_A 75%, GLU-B EQ_B 25%, chạy lại 2%, hao hụt 3% (`test-cases.md` bộ dữ liệu vàng cận lâm sàng, `golden_cls.py` `SYSTEMS`; 75/25 theo dòng "Dịch vụ GLU: tỷ trọng 75% và 25%").

| # | Điều kiện kiểm được | TC | FR | Vị trí test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Đánh dấu GLU cận lâm sàng thiếu nhóm chuyên ngành → `ValidationError` nêu "Nhóm chuyên ngành"; thiếu đơn vị kết quả → nêu "Đơn vị kết quả"; đủ (Hóa sinh, Kết quả xét nghiệm) → lưu được | TC-CLS-20 | FR-SVC-008 | `nc_technical_service/test_nc_technical_service.py` |
| 2 | Tạo GLU-A, GLU-B cho GLU tại HS → cả hai tồn tại; thiếu mã / dịch vụ / khoa / thiết bị / tỷ trọng → từ chối; hai tỷ lệ ước tính lưu 2 và 3 | TC-CLS-20 | FR-CLS-001, FR-CLS-002 | `nc_test_system/test_nc_test_system.py` |
| 3 | `get_status("GLU-A")` trả đủ bốn mục `norm_set`, `qc_plan`, `volume`, `latest_cost` (state "empty"); tổng 75 + 25 = 100 → không cảnh báo `share_total`; ngừng dùng GLU-B → `get_status("GLU-A")` có cảnh báo tổng 75%, `get_status("GLU-B")` có cảnh báo `inactive` | TC-CLS-20 | FR-CLS-007 | `api/test_test_system.py` |
| 4 | Gắn (LIS, "L100") cho GLU lưu được; gắn (LIS, "L100") (và " l100 ") cho dịch vụ khác → `ValidationError` nêu GLU; (HIS, "L100") cho dịch vụ khác lưu được; lặp trong cùng dịch vụ → từ chối | TC-CLS-21 | FR-SVC-009 | `test_nc_technical_service.py` |
| 5 | Clinician gán khoa VS sửa GLU-A (khoa HS) → `PermissionError`; tạo hệ thống cho khoa HS → `PermissionError`; Clinician khoa HS sửa được; đổi `department` GLU-A sang VS bởi Clinician khoa VS không được | TC-CLS-22 | FR-ACC-008 | `test_nc_test_system.py` |
| 6 | Ngừng dùng GLU-B; lần tính mới `test_systems_in_scope()` = ["GLU-A"]; một NC Costing Run "Đã khóa" có NC Service Cost tạo trước đó không đổi (`modified`, số dòng, số tiền) sau khi ngừng GLU-B | TC-CLS-23 | FR-CLS-006 | `nc_test_system/test_nc_test_system.py` |
| 7 | Nhập tệp mẫu 3 dòng, 1 dòng mã thiết bị "EQ_X" → `created` = 2, `error_count` = 1, lỗi nêu dòng và "Mã thiết bị chính"; nhập lại tệp → không tạo trùng | TC-CLS-23 | FR-CLS-008 | `api/test_importer_test_system.py` |
| 8 | Thiết bị chính "Phút chiếm máy" mà thiếu phút → từ chối; có 15 → lưu được | — | FR-CLS-005 | `test_FR_CLS_005_*` |
| 9 | `is_panel` không có thành phần → từ chối; mặc định `panel_costing_mode` = "Theo từng thông số" | — | FR-SVC-010 | `test_FR_SVC_010_*` |
| 10 | `is_send_out` thiếu giá → từ chối; dịch vụ gửi ngoài có bộ định mức "Đã khóa" → lần tính không sinh NC Service Cost cho dịch vụ đó | — | FR-SVC-011 | `test_FR_SVC_011_*` |
| 11 | Quyền NC Test System khớp ma trận cho 10 vai trò (Doc Controller, Council không đọc; Admin, Finance chỉ đọc; không ai xóa); NC Auditor đọc được, ghi/tạo bị từ chối; `check_conventions.py` thoát 0 | — | FR-ACC-002, FR-ACC-007 | `test_nc_test_system.py`, `tests/test_permissions.py` |
| 12 | Hàm thuần: phủ mọi nhánh của `test_systems.py`, `service_rules.py` | — | FR-CLS-001, 005, 006, FR-SVC-008..011 | `tests/unit/test_test_systems.py`, `tests/unit/test_service_rules.py` |
| 13 | Bỏ `is_paraclinical` của GLU khi có GLU-A → từ chối; xóa EQ_A (Admin) khi GLU-A trỏ tới → `LinkExistsError` nêu NC Test System GLU-A | — | FR-SVC-008, FR-ADM-005 | `test_nc_test_system.py` |

Test cũ phải đổi theo ngoại lệ CLAUDE.md mục 3.1: `tests/test_permissions.py::test_co_27_doctype_va_10_vai_tro` → số DocType thực sau gộp (27 + 3 = 30 nếu gộp trước FEAT-033; 32 nếu sau) và docstring; không đổi assertion khác. **Cần Quyết định Lead trên NORM-25** trước khi Dev sửa (ASM-113).

## 7. Giả định và rủi ro

Giả định mới (chi tiết ở `docs/decisions/assumptions.md`; bỏ qua ASM-099..106 vì nhánh FEAT-033 đang dùng):

| Mã | Tóm tắt |
| :-- | :-- |
| ASM-107 | TBD-17: `panel_costing_mode` mặc định "Theo từng thông số", chỉ lưu; bộ phải có ≥ 1 thông số, không lặp mã, không trỏ chính mình |
| ASM-108 | FR-SVC-011: gửi ngoài bắt buộc giá > 0; lần tính bỏ bộ định mức của dịch vụ gửi ngoài; thẻ tình trạng chuỗi không đổi |
| ASM-109 | Không bỏ được cờ cận lâm sàng khi còn hệ thống xét nghiệm; bỏ cờ thì giá trị cận lâm sàng cũ giữ nguyên |
| ASM-110 | DI-09: cắt khoảng trắng, so không phân biệt hoa thường; kiểm ở `validate` và chỉ mục duy nhất |
| ASM-111 | Miền giá trị tỷ trọng, hai tỷ lệ, phút chiếm máy; lưu phần trăm; không ràng khoa với khoa thực hiện hay khoa của thiết bị |
| ASM-112 | Tổng tỷ trọng ≠ 100% chỉ cảnh báo ở SCR-DSK-032, SCR-DSK-006; dừng tính là FEAT-036 |
| ASM-113 | Quyền và phạm vi khoa NC Test System; không ai xóa; đổi số đếm DocType ở test cũ (chờ Lead) |
| ASM-114 | FR-CLS-006 ở mức hàm chọn hệ thống và lọc bộ định mức; nối vào dòng chi phí theo hệ thống ở FEAT-034/036 |
| ASM-115 | FR-CLS-007: bốn mục "Chưa có" cho tới FEAT-032, 034, 035, 036 |
| ASM-116 | FR-CLS-008 một phần: chỉ bộ nhập hệ thống xét nghiệm |
| ASM-117 | Không viết patch |

Rủi ro:
- **Số ASM, số đếm DocType và `hooks.py`, `check_conventions.py`, `vi.csv` xung đột với nhánh FEAT-033** (đang mở, cùng đợt 5a): khi gộp giữ dòng của cả hai bên (CLAUDE.md mục 11); đếm lại DocType theo thực tế.
- Chỉ mục duy nhất trên bảng con: Frappe xóa dòng con cũ rồi chèn lại khi lưu; chuyển một mã từ dịch vụ A sang B phải lưu A (bỏ mã) trước, rồi B. Lưu B trước bị từ chối ở `validate` (đúng DI-09).
- Đổi tiêu chí chia của thiết bị sang "Phút chiếm máy" sau khi đã có hệ thống thiếu phút: hệ thống cũ chỉ bị bắt khai phút ở lần lưu kế tiếp; lần tính (FEAT-036) phải tự báo thiếu dữ liệu.
- FEAT-034 thêm `NC Norm Set.test_system`: lọc ở 2.3 đã sẵn; FEAT-034 thêm test lần tính bỏ bộ của hệ thống ngừng dùng.
