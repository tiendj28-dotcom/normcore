# FEAT-011 — Thiết kế kỹ thuật: Bộ tham số, chức danh, loại giá (gồm mở rộng 1.1)

Issue NORM-20. Nhánh `feat/FEAT-011-bo-tham-so` từ `develop` @ `539ae89`. Nguồn: `srs.md` FR-RES-009..011, 012 (chức danh), 015; `use-cases.md` UC-008; `test-cases.md` TC-RES-05, 06, 11, TC-CLS-50; `data-model.md` 3.5, 4, 5; `ux-foundations.md` SCR-DSK-019.

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-RES-009 | Đủ | 15 tham số cũ + sáu trường [1.1]; mặc định ZERO / 5 / 2 |
| FR-RES-010 | Đã có (FEAT-000) | `compute_job_rates` gọi `engine.job_rate`; TC-RES-05 đã xanh ở unit/golden, thêm test mức DocType |
| FR-RES-011 | Đủ | Từ chối sửa/xóa bộ đã dùng; nút "Nhân bản" |
| FR-RES-012 | Một phần | Chỉ phần chức danh: NC Job Title đã nhập được bằng khung nhập Excel (FEAT-004); không đổi |
| FR-RES-015 | Đủ | NC Price Category mới + hai bản ghi mẫu (TBD-05) |

Ngoài phạm vi: dùng tham số ở bộ máy tính giá (FEAT-012/015), đối soát (FEAT-014), bộ nhập Excel cho tham số.
Không có BR mới; BR-COST-001 đã cài, không đổi công thức, không tự chế công thức.

## 2. DocType

### 2.1 NC Costing Parameter Set (mở rộng)
Thêm đúng các trường của `data-model.md` 3.5: `wastage_cap`, `accumulation_mode`, `accumulation_rate`, `obligation_rate`, `rounding_unit`, `reconciliation_tolerance`, `comparison_tolerance`, `electricity_price`, `water_price`, `expired_depreciation_mode`, `material_recon_tolerance`, `volume_recon_tolerance`, `eqa_cost_category`, `rental_cost_category`, `jv_cost_category`. Mặc định: ZERO, 5, 2; `rounding_unit` 100; hai ngưỡng 10; chế độ tích lũy ON_COST, tích lũy 5, nghĩa vụ 0 (khớp golden `PARAM`, ASM-063); `wastage_cap` 10 (ASM-064); ba loại chi phí tạm DRUG_SUPPLY / DEPRECIATION / DEPRECIATION. Quyền giữ nguyên (đúng dòng "Bộ tham số, chức danh, loại giá").
Bản ghi cũ: patch `backfill_parameter_set_defaults` điền mặc định (ASM-065).

`validate` (thứ tự): (1) nếu bộ đang bị khóa (xem 2.3) → `frappe.throw`; (2) kiểm khoảng giá trị bằng `costing/parameters.py`; (3) `compute_job_rates`.
`on_trash`: bộ bị khóa không xóa được. Không cho Frappe `is_locked` chỉnh tay (chỉ đọc).

### 2.2 NC Price Category (mới), module NC Costing
`autoname: field:category_code`; `category_code` (BB, duy nhất), `category_name` (BB, `title_field`), `approval_authority` (Select Bệnh viện / Cơ quan có thẩm quyền, BB, không mặc định), `include_depreciation`, `include_accumulation` (Check). `track_changes` 1. Quyền như dòng "Bộ tham số, chức danh, loại giá"; NC Admin thêm `delete` (ASM-066); chặn xóa khi đang được tham chiếu (hooks `check_not_referenced`). Khai `DOCTYPE_ROW`, `DELETE_ALLOWED` ở `check_conventions.py`; test đếm DocType 18 → 19.
Hai bản ghi mẫu (TBD-05, ASM-067) nạp bằng patch `normcore.patches.add_sample_price_categories` và `install.after_install`: `GIA-BV` "Giá do bệnh viện quyết định (Giả định — chờ xác nhận)" / Bệnh viện / không khấu hao / có tích lũy; `GIA-NN` "Giá theo cơ quan có thẩm quyền (Giả định — chờ xác nhận)" / Cơ quan có thẩm quyền / có khấu hao / không tích lũy.

### 2.3 Khóa bộ tham số (FR-RES-011, DI-xx "đã dùng")
Bộ "đang được dùng" khi `is_locked` = 1 trong CSDL **hoặc** có NC Costing Run `status = "Đã khóa"` trỏ tới bộ (ASM-068: skeleton chưa có ai bật `is_locked`; FEAT-015 sẽ bật khi khóa lần tính). Hàm `is_in_use(name)`. Thông báo tiếng Việt nêu mã lần tính. Nhân bản: whitelisted method `duplicate()` trên doc (cần quyền `create`): sao chép mọi trường và dòng chức danh, `is_locked` = 0, `title` thêm " (bản sao)", trả tên bộ mới.

## 3. Logic thuần — `normcore/costing/parameters.py` (không import `frappe`)
- `DEFAULTS`: các mặc định mục 2.1.
- `check_ranges(values) -> list[str]`: các tỷ lệ % ∈ [0, 100]; `accumulation_rate` < 100 và `obligation_rate` < 100 (engine yêu cầu [0,1), BR-COST-013); số ngày, giờ > 0; `rounding_unit` ≥ 1; mode ∈ tập hợp lệ. Trả danh sách lỗi tiếng Việt.
- `accumulation_engine_mode(mode)`: `NONE` → `None`, còn lại giữ nguyên (cầu nối tới `engine.apply_accumulation`).
Phép tính tiền: không thêm; chức danh dùng `engine.job_rate` ↔ `golden_engine.job_rate`.

## 4. Giao diện (SCR-DSK-019): xem `ui-design.md`.

## 5. Bảng tiêu chí nghiệm thu

| # | Điều kiện | TC | FR |
| :-- | :-- | :-- | :-- |
| 1 | BS: 185.250.000 / 87.713,0682; DD: 125.970.000 / 59.644,8864 qua doc bộ tham số | TC-RES-05 | FR-RES-010 |
| 2 | Sửa bộ có lần tính "Đã khóa" bị từ chối; bộ nhân bản sửa được | TC-RES-06 | FR-RES-011 |
| 3 | Loại giá thiếu cấp phê duyệt bị từ chối; "Bệnh viện", không khấu hao, có tích lũy lưu được đúng ba lựa chọn | TC-RES-11 | FR-RES-015 |
| 4 | Bộ mới: ZERO, 5, 2 | TC-CLS-50 | FR-RES-009 |
| 5 | NC Auditor và vai trò ngoài ma trận không ghi được NC Price Category và bộ tham số | (quy ước) | FR-ACC-007 |
| 6 | Tham số ngoài khoảng bị từ chối | (unit) | FR-RES-009 |
| 7 | FEAT-004 không đỏ | — | — |

## 6. Giả định và rủi ro
ASM-063..068 như trên (chốt trong `docs/decisions/assumptions.md`). Rủi ro: nhánh khác (NORM-19: FEAT-009/010) cùng thêm ASM — gộp khi merge, giữ cả hai bên.
