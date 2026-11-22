# FEAT-009 — Thiết kế kỹ thuật: Mặt hàng và đơn giá có chứng từ (gồm phần mở rộng 1.1)

Issue NORM-18. Nhánh `ai/NORM-18-feat-009` từ `develop` @ `539ae89` (theo đề bài issue; cùng tiền lệ ASM-024). Nguồn: `srs.md` FR-RES-001..004, 012, 013, 014, 016..018; `use-cases.md` UC-008; `test-cases.md` TC-RES-01, 02, 07, 08, 09, TC-CLS-45..47; `data-model.md` 3.x (NC Item, NC Item Price), 4; golden `golden_engine.py::direct_lines`, `golden_cls.py::unit_price`.

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-RES-001 | Đủ | NC Item: mã, tên, loại, đơn vị tính bắt buộc; số lần dùng mặc định 1 |
| FR-RES-002 | Đủ | NC Item Price: nguồn giá gồm "Hợp đồng", `valid_to` tùy chọn |
| FR-RES-003 | Đủ (hàm thuần) | `price_warnings`; gắn lên dòng chi phí do FEAT-015 gọi (ASM-065) |
| FR-RES-004 | Đủ (hàm thuần + API) | `select_price`, `get_effective_price` |
| FR-RES-012 | Đủ phần mặt hàng, đơn giá | Bộ nhập `nc_item` và `nc_item_price` (khóa `price_code`, AMD-005, ASM-071); thiết bị, phòng, chức danh thuộc FEAT khác |
| FR-RES-013 | Tối thiểu | Trường `equivalent_group` và API `get_equivalent_items`; chưa gợi ý thay thế (ASM-067) |
| FR-RES-014 | Đủ (hàm thuần) | `material_line(billed_separately=True)` → thành tiền 0 kèm lý do |
| FR-RES-016 | Đủ | `verify_price`, `validate` của NC Item Price |
| FR-RES-017 | Đủ (hàm thuần) | cảnh báo "Đơn giá chưa xác minh", không chặn |
| FR-RES-018 | Đủ | trường định mức của NC Item, `unit_price_per_norm` |

Ngoài phạm vi: dòng chi phí thật trong NC Service Cost Line và bảng giải trình (FEAT-015 gọi `material_line`); gợi ý thay thế BR-ADJ-003; nhân k của BR-CLS-002 (FEAT-032+).

## 2. DocType (module NC Costing)

Theo `data-model.md` đã áp AMD-005 (thêm `price_code`, bỏ mặc định 1 của `norm_units_per_purchase_unit`). NC Item (`autoname: field:item_code`, `title_field: item_name`), NC Item Price (`autoname: format:DG-{#####}`). Quyền đúng dòng "Mặt hàng, đơn giá, thiết bị, phòng": Finance, Resource Manager, Admin đọc/sửa/tạo; Clinician, Dept Head, Director, Consultant, Auditor đọc; Council, Document Controller không có quyền. Không ai xóa (ASM-068). `track_changes` = 1. Hai Select `item_type`, `price_source` có dòng đầu rỗng để bắt buộc chọn (Frappe tự chọn tùy chọn đầu nếu không).

`NC Item.validate`: `reuse_count` ≥ 1; loại Hóa chất / Chất chuẩn / Vật liệu nội kiểm bắt buộc `norm_units_per_purchase_unit` > 0 (ASM-072, không có mặc định; loại khác để trống thì đặt 1); số test danh nghĩa, hạn dùng sau mở không âm.

`NC Item Price.validate`: `unit_price` > 0; `valid_to` ≥ `valid_from`; trạng thái "Đã xác minh" cần `attachment`; người xác minh và thời điểm do hệ thống ghi (người dùng không tự khai, không sửa lại sau khi đã xác minh); bỏ xác minh thì xóa hai trường. Đang "Đã xác minh" thì khóa mặt hàng, giá, nguồn, số và ngày chứng từ, hiệu lực, tệp (phải bỏ xác minh trước). `attachment`, `verification_status`, `verified_by`, `verified_on`, `price_code` đặt `no_copy`. `price_code` trống → lấy bằng `name`; trùng hoặc dạng `DG-<số>` khác `name` bị từ chối (ASM-069, ASM-071).

Không cần patch: DocType mới, chưa có dữ liệu cũ (ASM-073).

## 3. Logic thuần — `normcore/costing/pricing.py` (không import `frappe`)

| Hàm | BR / FR | Golden |
| :-- | :-- | :-- |
| `select_price(prices, as_of)` | FR-RES-004: còn hiệu lực = `valid_from ≤ as_of ≤ valid_to` (nếu có); nguồn ưu tiên cao nhất; rồi `valid_from` gần nhất; rồi ngày chứng từ, tên (ASM-063) | — (TC-RES-01, TC-CLS-45) |
| `price_warnings(price, as_of)` | FR-RES-003 (ngày chứng từ < ngày tính − 24 tháng, ASM-064), FR-RES-017 | — |
| `unit_price_per_norm(price, units)` | BR-CLS-002, 4 số lẻ HALF_UP | `golden_cls.py::unit_price` |
| `material_line(qty, wastage, reuse, norm_units, prices, as_of, billed_separately)` | BR-COST-003 trên đơn giá một đơn vị định mức (BR-CLS-002): `qty*(1+hao hụt)*unit_price_per_norm/số lần dùng`, 2 số lẻ HALF_UP; `norm_units` bắt buộc > 0 (ASM-075); FR-RES-014 | `golden_engine.py::direct_lines` (L02, L05, L06, L11, số đơn vị = 1), `golden_cls.py::unit_price` (mọi mặt hàng, dòng không bật k) |

Không có đơn giá hiệu lực → `NoEffectivePrice`, không bịa số (ASM-066).

## 4. API — `normcore/api/item.py`

| Hàm | Kết quả | Quyền |
| :-- | :-- | :-- |
| `get_effective_price(item, as_of=None)` | `{price, warnings, norm_unit_price, norm_uom}`; `price=None` khi không có giá hiệu lực | đọc NC Item; truy vấn bằng `frappe.get_list` |
| `verify_price(name)` | đặt "Đã xác minh", trả người và thời điểm; thiếu tệp → `ValidationError` | quyền ghi NC Item Price (Auditor bị từ chối) |
| `get_equivalent_items(item)` | mặt hàng cùng `equivalent_group` | đọc NC Item |

Bộ nhập `nc_item` (11 cột, bốn bắt buộc) và `nc_item_price` (8 cột, bảy bắt buộc, khóa `price_code`, không có cột xác minh hay tệp) trong `core/import_sets.py`; khung FEAT-004 không sửa. `get_effective_price`: hóa chất, chất chuẩn, vật liệu nội kiểm thiếu số đơn vị trả `norm_unit_price=None` (ASM-076).

## 5. Tiêu chí nghiệm thu

| # | Điều kiện | TC | FR | Test |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Ba giá cùng nguồn (01/01, 01/06, 01/01 năm sau), ngày 31/12 → 01/06 | TC-RES-01 | FR-RES-004 | `test_pricing.py::test_TC_RES_01_*`, `api/test_item.py::test_TC_RES_01_*` |
| 2 | Chứng từ cũ hơn 24 tháng → cảnh báo, vẫn tính | TC-RES-02 | FR-RES-003 | `test_TC_RES_02_*` (unit và API) |
| 3 | THUOCY thanh toán riêng → 0 + lý do; khớp golden L11 | TC-RES-07 | FR-RES-014 | `test_TC_RES_07_*` (unit, golden) |
| 4 | Nhập 5 dòng, 2 thiếu đơn vị tính → tạo 3, báo 2 lỗi | TC-RES-08 | FR-RES-012 | `api/test_item.py::test_TC_RES_08_*` |
| 5 | Thiếu đơn vị tính bị từ chối; đủ trường lưu với số lần dùng 1 | TC-RES-09 | FR-RES-001 | `test_nc_item.py::test_TC_RES_09_*` |
| 6 | Trúng thầu 01/2025 và Báo giá 06/2026 → Trúng thầu; Trúng thầu hết hạn 30/06/2026 → Báo giá | TC-CLS-45 | FR-RES-004 | unit và API `test_TC_CLS_45_*` |
| 7 | Nguồn Hợp đồng có `valid_to` lưu được; xác minh thiếu tệp bị từ chối; chưa xác minh → cảnh báo | TC-CLS-46 | FR-RES-002, 016, 017 | `test_nc_item_price.py::test_TC_CLS_46_*`, API, unit |
| 8 | HC_GLU 6.000.000 / 200 → 30.000,0000; khớp golden_cls | TC-CLS-47 | FR-RES-018 | unit, golden, API `test_TC_CLS_47_*` |
| 9 | Tải mẫu mặt hàng, nhập lại nguyên tệp: tạo 1, nhập lại không đổi | TC-ADM-02 (ASM-026) | FR-ADM-002 | `test_TC_ADM_02_mat_hang_*` |
| 9a | Nhập đơn giá: tạo, cập nhật theo mã, nhập lại không đổi, mặt hàng lạ và thiếu trường báo lỗi dòng, hai mặt hàng cùng số chứng từ không đè nhau, đã xác minh thì không ghi đè, Auditor bị từ chối | — | FR-RES-012 | `api/test_item.py::test_FR_RES_012_don_gia_*` |
| 9b | Khóa đơn giá đã xác minh; Nhân bản không chép xác minh; `valid_to` kiểu chuỗi; `price_code` | — | FR-RES-016 | `test_nc_item_price.py` |
| 9c | HC_GLU 1 đơn vị qua `material_line` ra 30.000,00; thiếu số đơn vị báo lỗi; khớp golden_cls | TC-CLS-47 | FR-RES-018 | `test_pricing.py`, `test_material_golden.py` |
| 10 | Quyền theo ma trận; Auditor chỉ đọc; vai trò ngoài ma trận không đọc | — | FR-ACC-002, 007 | `test_FR_ACC_*` ở hai DocType và API |
| 11 | JS: không mã màu cứng, chuỗi có bản dịch, escape | — | NFR-USE-001 | `test_item_ui_conventions.py` |

## 6. ASM áp dụng

ASM-063..ASM-076, AMD-005 (`docs/decisions/assumptions.md`). Test cũ: đổi `test_co_18_doctype_va_10_vai_tro` → `test_co_20_…`, và hai kỳ vọng ở `api/test_importer.py` (ASM-074, **chờ tiendj28 duyệt**; hiện các kỳ vọng này chưa khớp sau khi thêm bộ `nc_item_price`, xem nhật ký).

## 7. Rủi ro và nợ

- Chưa có dòng chi phí thật dùng `material_line`; FEAT-015 gọi hàm này và đưa cảnh báo, lý do loại lên bảng giải trình (ASM-065). Hệ số k, cấp ống, mẻ, ngày, UTILITY chưa có.
- `equivalent_group` là Data (đúng data-model), chưa có DocType nhóm.
