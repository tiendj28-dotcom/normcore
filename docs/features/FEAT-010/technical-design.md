# FEAT-010 — Thiết bị và phòng (gồm phần mở rộng 1.1) — Thiết kế kỹ thuật

Nguồn: `srs.md` FR-RES-005..008, FR-RES-019..026 (FR-RES-012 chỉ phần dữ liệu); BR-COST-004, BR-COST-005, BR-CLS-009..010 (phần dữ liệu và khấu hao), BR-CLS-012 (chỉ lưu trường điện); `data-model.md` 3.5, mục 4, DI-10; `golden_engine.py` `equip_rate`, `room_rate`; `golden_cls.py` `machine_annual`, `equipment_annual`; TC-RES-03, TC-RES-04, TC-RES-10, TC-CLS-48, TC-CLS-49.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-RES-005, 019, 020, 021, 022 | Form NC Equipment, trường bắt buộc theo hình thức có máy và tiêu chí chia |
| FR-RES-006, 007 | Hàm thuần khấu hao năm và đơn giá giờ máy tại một ngày tính giá; form hiển thị giá trị tạm tính theo ngày hiện tại (không lưu) |
| FR-RES-008 | NC Room, đơn giá giờ phòng |
| FR-RES-012 | **Một phần**: chỉ cấu trúc dữ liệu thiết bị, phòng có khóa duy nhất theo mã (để bộ nhập của FEAT-009 dùng). Bộ nhập Excel là FEAT-009 |
| FR-RES-023 | Bảng con NC Equipment Component |
| FR-RES-024, 025 | Bảng con NC Equipment Allocation, DI-10 |
| FR-RES-026 | Chỉ lưu các trường điện, cờ cấp điện liên tục. Tính điện (BR-CLS-012) là FEAT-036 |

Không làm: TC-CLS-07/09/11/12/13 (FEAT-036); liên kết NC Equipment Compliance (DocType của FEAT-031; xem ASM); bộ nhập Excel (FEAT-009); các trường còn lại của NC Costing Parameter Set (FEAT-011).

## 2. DocType

Mô-đun `NC Costing` (data-model 3.5). Tiền tố `NC `, fieldname `snake_case`, nhãn tiếng Việt, `track_changes` = 1.

### 2.1 Mới
- **NC Equipment Type** (autoname `field:type_code`): `type_code` (duy nhất, BB), `type_name` (BB), `compliance_required` (Check).
- **NC Equipment** (autoname `field:equipment_code`): đúng bảng ở data-model 3.5 (`equipment_code`, `equipment_name`, `department`, `equipment_type`, `acquisition_mode`, `allocation_basis`, `original_cost`, `in_service_date`, `useful_life_years`, `funding_source`, `annual_contract_cost`, `contract_asset_value`, `annual_maintenance_cost`, `maintenance_vendor_paid`, `annual_calibration_cost`, `planned_hours_per_year`, `utilization_rate`, `power_kw`, `power_standby_kw`, `run_hours_per_day`, `standby_hours_per_day`, `continuous_power`, `components`, `department_allocations`). Thêm mục chỉ đọc "Giá trị tạm tính" (HTML) do JS dựng.
- **NC Equipment Component** (bảng con): `component_name`, `replacement_cost`, `life_basis` (Tháng / Số kết quả / Giờ chạy), `life_value` (BB cả bốn), `vendor_paid`.
- **NC Equipment Allocation** (bảng con): `department` (BB), `share_pct` (Percent, BB).
- **NC Room** (autoname `field:room_code`): `room_code`, `room_name`, `department`, `annual_infrastructure_cost`, `available_hours_per_year` (BB), `area_m2` (không BB, CF-003).

### 2.2 Đổi
- **NC Costing Parameter Set**: thêm đúng một trường `expired_depreciation_mode` (Select ZERO / CONTINUE, mặc định ZERO, BB) theo data-model 3.5; ghi ASM. Không thêm trường nào khác của FEAT-011.

### 2.3 Quyền (data-model mục 4)
- NC Equipment, NC Room — dòng "Mặt hàng, đơn giá, thiết bị, phòng": Clinician R, Dept Head R, Council —, **Finance W**, **Resource Manager W**, Doc Controller —, Director R, Consultant R, Admin W, Auditor R. Mã ma trận `R R - W W - R R W R`.
- NC Equipment Type — dòng "Loại thiết bị, hồ sơ tuân thủ": `R R - R W - R R W R`.
- NC Admin xóa được trên ba DocType (tiền lệ Q2 của NORM-12). Bảng con theo quyền của DocType cha.
- Xóa bản ghi đang được tham chiếu: thêm ba DocType vào `doc_events.on_trash` của `core/references.py` (FR-ADM-005, UC-008 luồng 6a).

### 2.4 Ràng buộc kiểm ở `validate` (gọi hàm thuần `costing/resources.py`)
| Điều kiện | Lỗi |
| :-- | :-- |
| `acquisition_mode` = Mua mà thiếu `original_cost` hoặc `useful_life_years` (> 0) | từ chối |
| `acquisition_mode` = Thuê / Liên doanh, liên kết mà thiếu `annual_contract_cost` | từ chối |
| `allocation_basis` = Giờ kế hoạch mà thiếu `planned_hours_per_year` (> 0) hoặc `utilization_rate` (0 < u ≤ 1) | từ chối |
| `department_allocations` có dòng mà tổng `share_pct` ≠ 100 (DI-10); một khoa lặp hai dòng | từ chối |
| Giá trị âm ở tiền, giờ, công suất | từ chối |
| NC Room thiếu giờ khai thác năm hoặc ≤ 0 | từ chối |

Thiết bị Thuê/Liên doanh không cần nguyên giá; Đặt theo hóa chất không cần nguyên giá, hợp đồng (FR-RES-021, UC-008 3c). Giờ kế hoạch + hệ số sử dụng không bắt buộc khi tiêu chí là Số kết quả hoặc Phút chiếm máy (TC-CLS-48 ca ba).

## 3. Logic thuần — `normcore/costing/resources.py` (không import `frappe`)

| Hàm | BR | Golden |
| :-- | :-- | :-- |
| `is_expired(in_service, life_years, on)` | BR-COST-004 | `equip_rate`: `on >= date(năm + int(life), tháng, ngày)`; `golden_cls.machine_annual` cùng quy tắc |
| `machine_annual(mode, cost, life, in_service, contract, on, expired_mode, include_depr=True)` | BR-CLS-009, BR-COST-004, BR-COST-016 | `golden_cls.machine_annual`: Đặt = 0; Thuê, LDLK = hợp đồng; Mua = cost/life, hết hạn và ZERO → 0, CONTINUE → cost/life |
| `equipment_annual(...)` | BR-CLS-009, BR-CLS-010 | `golden_cls.equipment_annual`: (máy + bảo trì + linh kiện tính theo tháng + kiểm định nhập tay) × tỷ lệ khoa; bảo trì và linh kiện "nhà cung cấp chịu" = 0 khi Đặt |
| `machine_hourly_rate(annual, hours, util)` | BR-COST-004 | `golden_engine.equip_rate`: `r4((khấu hao + bảo trì + kiểm định) / (giờ × hệ số))`, HALF_UP 4 số lẻ |
| `room_hourly_rate(annual, hours)` | BR-COST-005 | `golden_engine.room_rate` |
| `validate_equipment(...)`, `validate_allocations(...)`, `validate_room(...)` | FR-RES-005/019..025, DI-10 | — |

Làm tròn đúng golden: chỉ đơn giá giờ làm tròn 4 số lẻ HALF_UP; khấu hao và tổng năm giữ nguyên `Decimal`. Kiểm định, hiệu chuẩn năm lấy từ `annual_calibration_cost` (hồ sơ tuân thủ là FEAT-031, BR-CLS-011 phần quy về năm thuộc FEAT-031/036).

## 4. API
Không thêm API ghi. Một hàm đọc cho form: `normcore.api.equipment.get_indicative_rate(equipment: str, on: date = hôm nay)` → `{annual_depreciation, annual_machine_cost, hourly_rate, expired}`; kiểm `frappe.has_permission("NC Equipment", "read", doc)`; lấy `expired_depreciation_mode` từ bộ tham số mới nhất có `effective_from` ≤ `on` (không có thì ZERO). Lỗi: `PermissionError`, `DoesNotExistError`.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | EQ1: khấu hao 150.000.000; giờ máy 176.136,3636 | TC-RES-03 | FR-RES-006 |
| 2 | V2 (đưa vào sử dụng 01/01/2015), ZERO: khấu hao 0; giờ máy 34.090,9091. CONTINUE: khấu hao 150.000.000 | TC-RES-04 | FR-RES-007 |
| 3 | Phòng thiếu giờ khai thác bị từ chối; R1 (52.800.000; 2.112 giờ) lưu được, 25.000 | TC-RES-10 | FR-RES-008 |
| 4 | Thuê thiếu hợp đồng, Mua thiếu nguyên giá bị từ chối; chia theo Số kết quả không cần giờ kế hoạch thì lưu được | TC-CLS-48 | FR-RES-005, 019, 020, 022 |
| 5 | Khoa 60% + 30% từ chối; 60% + 40% lưu được | TC-CLS-49 | FR-RES-024, 025 |
| 6 | Thuê: khấu hao thay bằng hợp đồng; Đặt: máy, bảo trì và linh kiện nhà cung cấp chịu = 0; số khớp `golden_cls` EQ_A, EQ_B, EQ_C | (đơn vị, tham chiếu TC-CLS-12) | FR-RES-020, 021, 023 |
| 7 | Quyền: Finance, Resource Manager ghi; vai trò không có quyền và NC Auditor bị từ chối ghi, kể cả sửa; Clinician chỉ đọc | — | FR-ACC-002, 007 |
| 8 | Xóa thiết bị đang được tham chiếu bị chặn, nêu bản ghi | — | FR-ADM-005 |

## 6. Giả định và rủi ro
- **CF-003**: FR-RES-008 "yêu cầu diện tích" mâu thuẫn TC-RES-10 và data-model (R1 lưu được không có diện tích; `area_m2` không BB). Theo bậc 2 (TC) thắng: diện tích không bắt buộc.
- **ASM-063**: `expired_depreciation_mode` thêm vào NC Costing Parameter Set ở FEAT này; FEAT-011 làm phần còn lại.
- **ASM-064**: Liên kết hồ sơ tuân thủ (SCR-DSK-018) chưa làm vì NC Equipment Compliance thuộc FEAT-031; `annual_calibration_cost` dùng như số nhập tay.
- **ASM-065**: Giờ máy tạm tính dùng `machine_annual` + bảo trì + linh kiện theo tháng + kiểm định nhập tay, nhân tỷ lệ khoa, chia (giờ × hệ số); với EQ1 trùng BR-COST-004. Linh kiện tính theo số kết quả, giờ chạy và điện thuộc FEAT-036.
- **ASM-066**: Không viết patch (trường mới cho phép trống hoặc có mặc định, DocType mới; cùng tiền lệ ASM-062). Bản ghi bộ tham số cũ không có `expired_depreciation_mode` được hiểu là ZERO.
- Rủi ro: FEAT-009, FEAT-011 chạy song song cũng sửa `assumptions.md`, `vi.csv`; khi gộp giữ dòng cả hai bên.
