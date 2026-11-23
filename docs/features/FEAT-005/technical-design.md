# FEAT-005 — Thiết kế kỹ thuật: Danh mục kỹ thuật và tình trạng chuỗi

Issue NORM-17. Nhánh `feat/FEAT-005-danh-muc-ky-thuat` từ `develop` @ `7aafc10`. Nguồn: `srs.md` FR-SVC-001..004; `use-cases.md` UC-003; `test-cases.md` TC-SVC-01, 03, 04; `data-model.md` 3.3, 4, 6; ADR-012; "Quyết định Lead" trên NORM-17 (2026-11-22).

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-SVC-001 | Đủ | Bộ nhập `nc_technical_service` trên khung FEAT-004 |
| FR-SVC-002 | Đủ | Giữ dòng đầu, báo lỗi dòng trùng sau (ASM-050) |
| FR-SVC-003 | Đủ | Bảng con NC Service Department |
| FR-SVC-004 | Một phần | Đủ bốn mục. Mục giá thành chưa có số tiền (ASM-048, chờ FEAT có `full_cost`); mục giá đã duyệt luôn là "Chưa có giá đã duyệt" cho tới FEAT-030 (ASM-049) |

Ngoài phạm vi: UC-003 bước 3–5 (FEAT-022); trường và khối cận lâm sàng [1.1] (FEAT-031); NC Service Price History (FEAT-030); cột và bộ lọc tình trạng chuỗi ở danh sách (FEAT-002, AMD-004); nút "Soạn quy trình" (FEAT-024), "Khởi tạo bộ định mức" (FEAT-012); bộ nhập Excel cho chuyên khoa.

Không có BR-COST/ADJ/CLS nào liên quan; không có phép tính tiền, không đối chiếu golden.

## 2. DocType

### 2.1 NC Specialty (mới) — module NC Procedure

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| specialty_code | Mã chuyên khoa | Data | Có | `unique`; `autoname: field:specialty_code` |
| specialty_name | Tên chuyên khoa | Data | Có | `title_field`; hiện ở danh sách |

`track_changes` = 1. Quyền theo dòng "Dịch vụ kỹ thuật, chuyên khoa": NC Document Controller và NC Admin đọc, sửa, tạo; tám vai trò còn lại chỉ đọc; NC Admin thêm `delete` (ASM-053). Khai `DOCTYPE_ROW["NC Specialty"]` và thêm vào `DELETE_ALLOWED["NC Admin"]` trong `scripts/check_conventions.py`; thêm vào `doc_events` của `core/references.py::check_not_referenced` trong `hooks.py` (FR-ADM-005).

### 2.2 NC Service Department (mới) — bảng con, module NC Procedure

`department`: Khoa, Link NC Department, BB, hiện trong lưới. `istable` = 1. Quyền theo DocType cha.

### 2.3 NC Technical Service (mở rộng)

- Thêm `specialty` (Link NC Specialty, "Chuyên khoa", không BB, `in_list_view`, `in_standard_filter`), `departments` (Table NC Service Department, "Khoa thực hiện"), các trường bố cục và HTML của thẻ tình trạng chuỗi (ui-design).
- `is_active`: thêm `in_list_view`, `in_standard_filter`. `search_fields`: `service_name,specialty`. Giữ nguyên quyền, `autoname`, `track_changes`.
- `validate`: cùng một khoa xuất hiện hai lần → `frappe.throw` tiếng Việt nêu mã khoa (ASM-056). Không ràng buộc khoa với quy trình đã có (ASM-055).
- Không thêm `approved_prices` và các trường [1.1].

Không cần patch: chỉ thêm trường cho phép trống và DocType mới, `bench migrate` đồng bộ đủ, không có dữ liệu cũ phải chuyển.

## 3. Bộ nhập Excel

Thêm vào `normcore/core/import_sets.py`, **không sửa** `core/importer.py`, `api/importer.py` và test của khung:

`ImportSet(key="nc_technical_service", label="Dịch vụ kỹ thuật", doctype="NC Technical Service", key_field="service_code")` với ba cột:

| Cột | Kiểu | BB | Ví dụ |
| :-- | :-- | :-- | :-- |
| Mã dịch vụ (`service_code`) | Data | Có | `VD-DV01` |
| Tên dịch vụ (`service_name`) | Data | Có | `Dịch vụ kỹ thuật (ví dụ)` |
| Chuyên khoa (`specialty`) | Link NC Specialty | | trống |

- Chuyên khoa ghi **mã**; mã chưa có → dòng lỗi "không tồn tại", không tự tạo (ASM-051). Ví dụ để trống để nhập lại nguyên tệp mẫu không lỗi (ASM-028, TC-ADM-02).
- Mẫu sinh bằng `build_template`, không thêm tệp `.xlsx` tĩnh (ASM-058). Mã nên để ô dạng văn bản (ASM-060).
- Quyền, chế độ `thu`/`ghi`, thông báo dòng: nguyên theo khung (ASM-029, 031, 032, 033).

## 4. Logic thuần — `normcore/procedure/chain.py` (không import `frappe`)

| Hàm | Vào | Ra |
| :-- | :-- | :-- |
| `pick_procedures(rows, today)` | dòng quy trình "Đã ban hành" (`name, department, version_no, effective_date`) | `{khoa: dòng}`. Trong mỗi khoa lấy `version_no` lớn nhất có `effective_date` ≤ `today` (trống coi như đã hiệu lực); không có thì lấy `version_no` lớn nhất, kèm `not_effective=True` (ASM-054) |
| `pick_norm_sets(rows)` | dòng bộ định mức "Đã khóa" | `{khoa: dòng}`, `version_no` lớn nhất (ASM-054) |
| `pick_costs(rows)` | dòng giá thành đã ghép `run_status, costing_date, run_creation, based_on_run` | `{khoa: dòng}`. Bỏ dòng có `based_on_run`; chỉ lấy `run_status` thuộc ("Đã tính", "Đã khóa"); lớn nhất theo (`costing_date`, `run_creation`). Dòng `calc_status` = "Lỗi" vẫn được chọn (ASM-048) |
| `build_item(key, departments, picked, allowed)` | `allowed`: `None` = mọi khoa, hoặc tập mã khoa | một mục theo mục 5.2 |

Không có hàm nào nhận hay trả trường tiền.

## 5. API — `normcore/api/service.py`

### 5.1 `get_chain_status(service)` (`@frappe.whitelist()`)

| Tình huống | Kết quả |
| :-- | :-- |
| Guest | Frappe từ chối (không `allow_guest`) |
| Dịch vụ không tồn tại | `frappe.DoesNotExistError` |
| Không đọc được dịch vụ | `frappe.PermissionError`, không trả dữ liệu |
| Bình thường | `{"service": ..., "items": [4 mục]}` |

Chỉ đọc, không ghi CSDL. Truy vấn bằng `frappe.get_list` (không dùng `get_all`, không `ignore_permissions`), chỉ chọn các trường cần; không chọn trường tiền. `based_on_run` chỉ chọn khi `frappe.get_meta("NC Costing Run").has_field("based_on_run")`, vì trường này chưa có (ASM-004); FEAT thêm trường không phải sửa lại hàm chọn.

### 5.2 Cấu trúc trả về

Bốn mục theo thứ tự cố định `procedure`, `norm_set`, `cost`, `price`:

```
{"key", "label", "state": "ok"|"empty"|"no_permission", "message", "badges": [{"label","indicator"}],
 "rows": [{"department", "department_name", "state", "status", "indicator", "date",
           "doctype", "name", "route", "badges"}],
 "links": ["/app/nc-norm-set/DM-…", …]}
```

- `links` = `route` của mọi dòng `ok`. Mục `price`: `state="empty"`, `message="Chưa có giá đã duyệt"`, `rows=[]`, `links=["#nc-chain-price"]` (thẻ giá đã duyệt trên form; FEAT-030 thay bằng bảng giá thật).
- Mục `cost`: liên kết tới **NC Service Cost**; `status` = trạng thái lần tính; `date` = `costing_date`; nhãn mục `badges=[{"label": "Giả định — chờ xác nhận", "indicator": "yellow"}]` khi `state` = `ok`; dòng "Lỗi" thêm nhãn đỏ, "Cảnh báo" thêm nhãn vàng. Không có số tiền.
- Màu: "Đã ban hành", "Đã khóa" `green`; "Đã tính" `blue`; "Chưa hiệu lực" `yellow`; "Chưa có", "Không có quyền xem" `gray` (`design.md` mục 3).

### 5.3 Quyền và không lộ thông tin (FR-SVC-004, FR-ACC-005, ASM-047, CF-002)

1. Không có quyền đọc ở mức vai trò (`frappe.has_permission(doctype, "read")` sai; mục `cost` cần cả NC Service Cost và NC Costing Run): mục `state="no_permission"`, `message="Không có quyền xem"`, `rows=[]`, `links=[]`, `badges=[]`. Không truy vấn bản ghi của mục.
2. Phạm vi khoa: thêm `readable_departments(doctype, user=None)` vào `core/permissions.py`, trả `None` nếu không bị hẹp, ngược lại tập khoa được gán (dùng lại `_is_scoped`, `get_user_departments`). Chỉ áp cho mục `norm_set`; quy trình "Đã ban hành" đọc toàn viện (FR-ACC-003).
3. Tập khoa của các dòng = `departments` của dịch vụ ∪ khoa của những bản ghi **người xem đọc được** ở cả ba mục (ASM-055). Không dùng bản ghi không đọc được để suy ra khoa.
4. Dòng: khoa ngoài `allowed` → `no_permission` dù có hay không có bản ghi, và không có `name`, `route`, `status`, `date`; có bản ghi → `ok`; còn lại → `empty` ("Chưa có").
5. Mục: có dòng `ok` → `ok`; mọi dòng `no_permission`, hoặc người bị hẹp mà chưa được gán khoa nào → `no_permission`; còn lại → `empty`. Người bị hẹp có khoa, mục `empty`: message "Chưa có trong phạm vi khoa của bạn".
6. Mục `price` theo quyền đọc dịch vụ, nên mọi vai trò đọc được dịch vụ đều thấy.

Bảng kỳ vọng khi dịch vụ X có đủ dữ liệu ở khoa K (Clinician, Dept Head được gán K):

| Vai trò | procedure | norm_set | cost | price |
| :-- | :-- | :-- | :-- | :-- |
| NC Finance, NC Director, NC Admin, NC Auditor | ok | ok | ok | empty |
| NC Clinician, NC Department Head | ok | ok | no_permission | empty |
| NC Resource Manager, NC Consultant | ok | ok | no_permission | empty |
| NC Document Controller, NC Council Member | ok | no_permission | no_permission | empty |

Clinician, Dept Head chỉ được gán khoa khác K: `norm_set` → `no_permission` ở dòng K. Dept Head xem giá thành của khoa mình: FEAT-015.

## 6. Tiêu chí nghiệm thu

Tệp test: **S** = `nc_procedure/doctype/nc_technical_service/test_nc_technical_service.py`, **C** = `tests/unit/test_chain.py`, **A** = `api/test_service.py`, **P** = `nc_procedure/doctype/nc_specialty/test_nc_specialty.py`, **U** = `tests/unit/test_service_ui_conventions.py`.

| # | Điều kiện kiểm được | TC | FR | Test |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Tệp 10 dòng: Excel 2–8 `SVC01`…`SVC07` hợp lệ; 9 `SVC08` thiếu tên; 10 lặp `SVC01`; 11 lặp `SVC02`. Chế độ `thu`: `created`=7, CSDL không đổi. Chế độ `ghi`: `created`=7, `updated`=0, đúng 7 dịch vụ mới, tên `SVC01`/`SVC02` lấy từ dòng 2/3; `errors` đúng ba dòng với `text`: `Dòng 9, cột "Tên dịch vụ": ô bắt buộc đang để trống`; `Dòng 10, cột "Mã dịch vụ": trùng khóa "SVC01" với dòng 2 trong cùng tệp`; `Dòng 11, cột "Mã dịch vụ": trùng khóa "SVC02" với dòng 3 trong cùng tệp`. Người nhập: NC Document Controller | TC-SVC-01 | FR-SVC-001, 002 | S `test_TC_SVC_01_nhap_danh_muc` |
| 2 | Tải mẫu → nhập: tạo 1, không lỗi; nhập lại: `unchanged`=1 | — | FR-SVC-001 | S `test_FR_SVC_001_tai_mau_nhap_lai` |
| 3 | Mã đã có → cập nhật tên, chuyên khoa; `departments`, `is_active` giữ nguyên | — | FR-SVC-001 | S `test_FR_SVC_001_cap_nhat_theo_ma` |
| 4 | Mã chuyên khoa lạ → dòng lỗi `"X" không tồn tại trong NC Specialty`; không tạo NC Specialty; dòng khác vẫn ghi | — | FR-SVC-001 | S `test_FR_SVC_001_chuyen_khoa_la` |
| 5 | Dòng thiếu mã bị bỏ, có trong báo cáo lỗi | — | FR-SVC-002 | S `test_FR_SVC_002_thieu_ma` |
| 6 | NC Finance và NC Auditor nhập → `PermissionError` | — | FR-ACC-002, 007 | S `test_FR_SVC_001_vai_tro_chi_doc_bi_tu_choi` |
| 7 | Gán K01, lưu; gán thêm K02, lưu; đọc lại CSDL: `["K01","K02"]`, 2 dòng con `parent`=X | TC-SVC-04 | FR-SVC-003 | S `test_TC_SVC_04_nhieu_khoa` |
| 8 | Gán trùng khoa → `ValidationError` nêu mã khoa; NC Finance, NC Auditor sửa → `PermissionError` | — | FR-SVC-003 | S `test_FR_SVC_003_*` |
| 9 | X, khoa K: quy trình ban hành, bộ định mức khóa, lần tính "Đã tính". NC Finance gọi `get_chain_status`: bốn mục đúng thứ tự; **mỗi mục có `links` không rỗng**; ba mục đầu chứa đúng tên NC Clinical Procedure, NC Norm Set, NC Service Cost vừa dựng; mục 4 là `#nc-chain-price` | TC-SVC-03 | FR-SVC-004 | S `test_TC_SVC_03_tinh_trang_chuoi` |
| 10 | Dịch vụ chưa có gì vẫn đủ bốn mục, đều `empty` | — | FR-SVC-004 | A `test_FR_SVC_004_chua_co_gi` |
| 11 | Hai khoa → hai dòng; bộ định mức "Nháp", "Đã thay thế" và quy trình "Nháp" không được chọn; có khoa dữ liệu ngoài `departments` | — | FR-SVC-004 | A `test_FR_SVC_004_theo_khoa` |
| 12 | 10 vai trò cho kết quả đúng bảng mục 5.3 | — | FR-SVC-004, FR-ACC-002, 007 | A `test_FR_SVC_004_quyen_theo_vai_tro` |
| 13 | Clinician khoa khác: JSON trả về không chứa tên bộ định mức, lần tính; kết quả mục `norm_set` **giống hệt** khi khoa K có và không có bộ định mức | — | FR-ACC-003, 005 | A `test_FR_ACC_005_khong_lo_thong_tin` |
| 14 | JSON trả về không có khóa tiền nào (`direct_labor`, `full_cost`, `calculated_price`, `rounded_price`, `amount`) với mọi vai trò; mục `cost` có nhãn "Giả định — chờ xác nhận" | — | FR-SVC-004 | A `test_FR_SVC_004_khong_hien_tien` |
| 15 | Dịch vụ lạ → `DoesNotExistError`; người không có vai trò NC → `PermissionError` | — | FR-ACC-005 | A `test_FR_ACC_005_tu_choi` |
| 16 | Các hàm `pick_*`, `build_item`: hiệu lực tương lai, nhiều phiên bản, cùng `costing_date`, kịch bản, lần tính "Nháp"/"Tính lỗi", kết quả "Lỗi" | — | FR-SVC-004 | C `test_FR_SVC_004_*` (≥ 8) |
| 17 | `frappe.get_list` lọc theo khoa K01 qua bảng con trả đúng dịch vụ, không lặp dòng; lọc theo chuyên khoa | — | SCR-DSK-005 | S `test_SCR_DSK_005_loc_danh_sach` |
| 18 | NC Specialty: thiếu tên → `MandatoryError`; trùng mã → từ chối; NC Finance và NC Auditor không ghi; NC Admin xóa khi được dịch vụ tham chiếu → `LinkExistsError` nêu dịch vụ, khi không tham chiếu thì xóa được; NC Document Controller không xóa được | — | FR-ACC-002, 007, FR-ADM-005 | P |
| 19 | JS của hai màn hình: không mã màu cứng; mọi chuỗi `__()` có bản dịch | — | NFR-USE-001 | U |

Test cũ: chỉ đổi `test_co_16_doctype_va_10_vai_tro` → `test_co_18_doctype_va_10_vai_tro` và `16` → `18` (ASM-053). Không đổi test nào khác.

## 7. Giả định, mâu thuẫn, sửa tài liệu

ASM-047..ASM-061 (`docs/decisions/assumptions.md`); CF-002; AMD-003, AMD-004; DEF-002, DEF-003, DEF-004 (không chặn FEAT).

## 8. Rủi ro và nợ (Dev ghi vào As-Built)

- Chưa có số tiền giá thành; Tài chính kế toán **chưa** xác nhận cách chọn "lần tính gần nhất" (ASM-048).
- Giá đã duyệt: FEAT-030 thêm `approved_prices` và thay mục `price`.
- Cột, bộ lọc tình trạng chuỗi: FEAT-002. Nút hành động: FEAT-012, FEAT-024.
- FEAT-015 thêm quyền bảng giải trình cho Dept Head thì cập nhật bảng mục 5.3; FEAT-032 trở đi có nhiều bộ định mức cho một (dịch vụ, khoa) theo hệ thống xét nghiệm thì `pick_norm_sets` phải nhóm thêm theo `test_system` (DI-03).
- Mã dịch vụ nhập dạng số trong Excel có thể mất số 0 (ASM-060, chờ Quản lý văn bản).
