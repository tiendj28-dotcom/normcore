# FEAT-029 — Kịch bản điều chỉnh và yêu cầu sửa quy trình — Thiết kế kỹ thuật

Issue NORM-83. Bản phát hành R3. Phụ thuộc FEAT-028, FEAT-008, FEAT-013 (đều có `DONE` trên `develop`, đã kiểm `git cat-file -e origin/develop:docs/features/FEAT-xxx/DONE`). Dùng lại FEAT-037 (`costing/sensitivity.py`, `api/costing._snapshot_for`), FEAT-018 (`compare_runs`).

Nguồn: `srs.md` FR-ADJ-006, 007, 009, FR-NORM-009..011, FR-WF-009, BR-ADJ-001..004 (mục 3.4.2, "Không quy tắc nào được đề xuất bỏ bước hay giảm số lượng nguồn lực chuyên môn; thay đổi loại đó chỉ đến từ người dùng và đi theo FR-ADJ-007"); `use-cases.md` UC-014 bước 4–6, 4b, UC-007 1c; `data-model.md` NC Costing Run (`based_on_run`, `scenario_changes`), NC Scenario Change, NC Procedure Change Request, mục 4 dòng "Gợi ý, kịch bản, phương án giá"; `ux-foundations.md` SCR-DSK-026 (trạng thái "gợi ý cần sửa quy trình; kịch bản đang mở"); As-Built FEAT-028, FEAT-008, FEAT-013, FEAT-037.

**Golden.** `docs/golden/` không có hàm kịch bản hay BR-ADJ-002..004 (`grep -n ADJ docs/golden/*.py`). Kịch bản **không có công thức mới**: đổi đầu vào trong ảnh chụp (`dataclasses.replace`) rồi tính lại bằng `costing.snapshot.recompute`, đúng đường tính của lần tính (như `costing/sensitivity.py`). Đơn giá giờ máy mới dùng `resources.machine_hourly_rate` (BR-COST-004). Kiểm chặt nhất có được: DV-TEST-A gốc tính với EQ1 hệ số 0,4; kịch bản đưa EQ1 về 0,5 (giá trị golden) → giá tính toán kịch bản phải bằng **302.132,73** (`golden_engine.py`, test-cases mục 2.3).

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-ADJ-006 | Đủ | Chấp nhận gợi ý không cần sửa quy trình (BR-ADJ-001, 002, 004, 005) → ghi NC Scenario Change vào kịch bản đang mở (tạo nếu chưa có), tính lại toàn bộ kịch bản (gồm phân bổ), ghi NC Service Cost của kịch bản. Lần tính gốc không đổi. BR-ADJ-006, 007 không có giá trị để áp: chỉ ghi quyết định (ASM-029-03) |
| FR-ADJ-007 | Đủ | Gợi ý cần sửa quy trình (BR-ADJ-003) hoặc đề xuất của người dùng đổi bước/nguồn lực → không áp vào kịch bản, không sửa bộ định mức; tạo NC Procedure Change Request gửi khoa chủ trì, thông báo trưởng khoa; trưởng khoa tiếp nhận → bản nháp phiên bản kế tiếp theo FR-WF-009, ghi kèm đề xuất và lý do (UC-007 1c) |
| FR-ADJ-009 | Đủ | Thay đổi loại "Dòng định mức" (BR-ADJ-002 số phút, BR-ADJ-004 hao hụt) → tạo (hoặc dùng) bộ định mức "Nháp" phiên bản kế tiếp mang giá trị mới, dòng đó bỏ xác nhận, chờ xác nhận lại theo FR-NORM-009..011 |

UC-014: bước 4, 5, 6 (lặp, phần lập phương án giá là FEAT-030), 4b. UC-007: 1c. SCR-DSK-026: thêm trạng thái "kịch bản đang mở", chấp nhận gợi ý ghi vào kịch bản, chuyển yêu cầu sửa quy trình.

Ngoài phạm vi: phương án giá (FEAT-030); khóa kịch bản (ASM-029-07); thay đổi số do người dùng tự nhập vào kịch bản ngoài gợi ý (ASM-029-14); quy tắc riêng cho dòng hệ thống xét nghiệm (giữ giới hạn của FEAT-028).

## 2. DocType

Mọi DocType và trường dưới đây đã có trong `data-model.md`; không thêm trường ngoài data-model nên **không có AMD**.

### 2.1 NC Costing Run (mở rộng)

Thêm hai trường (data-model đã khai), đặt trong section mới "Kịch bản điều chỉnh" sau `scope_services`, `depends_on: eval:doc.based_on_run`:

| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| `based_on_run` | Kịch bản của lần tính | Link NC Costing Run | `read_only = 1`, `in_standard_filter = 1`, `search_index = 1` |
| `scenario_changes` | Thay đổi của kịch bản | Table NC Scenario Change | `read_only = 1` |

Chỉ thêm trường, bản ghi cũ có `based_on_run` trống: không cần patch (giống FEAT-008 thêm trường NC Norm Set). `duplicate_run` đã xóa `based_on_run` khi nhân bản (mã FEAT-018), giữ nguyên.

Controller `nc_costing_run.py` thêm (ASM-029-01, 07):
- `is_scenario` = `bool(self.based_on_run)`.
- `validate`: `based_on_run` chỉ đặt được khi tạo và chỉ khi `self.flags.scenario_write` (do API đặt); lần gốc phải không phải kịch bản (không lồng) và `status ∈ {Đã tính, Đã khóa}`; đổi `based_on_run` hoặc bảng `scenario_changes` mà không có `flags.scenario_write` → `frappe.throw("Kịch bản chỉ sửa qua Bàn so sánh giá")`.
- `run_costing`, `lock_costing`, `duplicate_run` trên kịch bản → `frappe.throw("Kịch bản điều chỉnh tính lại qua Bàn so sánh giá, không chạy, khóa hay nhân bản trực tiếp")`.
- Không đụng hành vi của lần tính thường (test FEAT-015..018, 036, 037 giữ xanh).

Quyền: DocPerm NC Costing Run không đổi (Finance W; Director, Admin, Auditor R). Trưởng khoa (cột "R, A (khoa)" của dòng "Gợi ý, kịch bản") xem kịch bản qua API của trang (đọc NC Service Cost của kịch bản theo phạm vi khoa, dòng "Bảng giải trình") và chấp nhận gợi ý qua API; máy chủ ghi kịch bản bằng `ignore_permissions` sau khi đã kiểm quyền quyết định (ASM-029-17).

### 2.2 NC Scenario Change (mới, bảng con, module NC Benchmark)

`istable = 1`, `track_changes` theo cha. Quyền theo DocType cha (data-model mục 4 [1.1]). Mọi trường `read_only = 1`, ghi bằng máy chủ.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `technical_service` | Dịch vụ | Link NC Technical Service | | Trống với thay đổi áp cho cả lần tính (Tham số, Thiết bị) |
| `change_type` | Loại thay đổi | Select `Tham số\nThiết bị\nDòng định mức` | Có | `in_list_view` |
| `target_ref` | Đối tượng | Data | Có | Mã bộ tham số / mã thiết bị / mã dòng định mức (`L04`) |
| `field` | Trường | Data | Có | `accumulation_rate` / `utilization_rate` / `hospital_qty`, `wastage_rate` (bảng 3.1) |
| `old_value` | Giá trị cũ | Data | | Số chuẩn dấu chấm, đơn vị của trường nguồn (ASM-029-04) |
| `new_value` | Giá trị mới | Data | Có | như trên |
| `source_suggestion` | Gợi ý nguồn | Link NC Adjustment Suggestion | | Khoa của thay đổi "Dòng định mức" lấy qua gợi ý → `service_cost.department` (ASM-029-06) |

### 2.3 NC Procedure Change Request (mới, module NC Benchmark)

Naming `YCSQT-.YYYY.-.#####`. `track_changes = 1`. Mọi trường `read_only = 1` trên form; tạo và đổi trạng thái chỉ qua API (mục 3.3), `validate` chặn khi thiếu `self.flags.pcr_write`. Không ai có quyền xóa.

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `procedure` | Quy trình | Link NC Clinical Procedure | Có | `in_list_view`, `in_standard_filter`; quy trình đích theo ASM-029-13 |
| `requested_by` | Người yêu cầu | Link User | Có | Máy chủ đặt `session.user` |
| `source_suggestion` | Gợi ý nguồn | Link NC Adjustment Suggestion | | Trống với đề xuất người dùng tự nêu (FR-ADJ-007 vế 2) |
| `proposed_change` | Đề xuất thay đổi | Text | Có | Máy chủ dựng bằng `scenario.proposal_text` (gợi ý) hoặc người dùng nhập; luôn kèm lý do |
| `status` | Trạng thái | Select `Mới\nĐã tiếp nhận\nTừ chối\nĐã thực hiện` | Có | Mặc định `Mới`; `in_list_view`, `in_standard_filter` |

Luồng trạng thái (ASM-029-11), kiểm ở controller (`TRANSITIONS`) và API:

| Từ | Hành động | Sang | Ai | Tác dụng |
| :-- | :-- | :-- | :-- | :-- |
| Mới | Tiếp nhận | Đã tiếp nhận | Trưởng khoa của khoa quy trình (Administrator được, dùng cho test) | Gọi `api.procedure.create_revision(procedure)` bằng quyền người gọi (Trưởng khoa có W quy trình theo khoa); thêm Comment "Info" vào bản nháp: "Yêu cầu sửa đổi từ Bàn so sánh giá {pcr}: {proposed_change}" (UC-007 1c). Đã có bản đang soạn (1d) → Comment vào bản đó. Trả `revision` |
| Mới, Đã tiếp nhận | Từ chối | Từ chối | Trưởng khoa của khoa quy trình | Lý do bắt buộc ("Từ chối yêu cầu phải nêu lý do"), lưu Comment trên yêu cầu; thông báo người yêu cầu |
| Đã tiếp nhận | Đã thực hiện | Đã thực hiện | Trưởng khoa của khoa quy trình | Chỉ khi có quy trình "Đã ban hành" của cùng (dịch vụ, khoa) có `version_no` lớn hơn `procedure`; ngược lại "Phiên bản sửa đổi chưa ban hành" |

### 2.4 Quyền NC Procedure Change Request (ASM-029-10)

Không có dòng riêng trong ma trận; theo dòng "Gợi ý, kịch bản, phương án giá" (cùng nguồn gốc phân hệ D):

| Vai trò | DocPerm | Phạm vi |
| :-- | :-- | :-- |
| NC Finance | read, write, create, report, export | mọi khoa |
| NC Department Head | read, report | theo khoa: `normcore/core/scope_rules/nc_procedure_change_request.json` `{"doctype": "NC Procedure Change Request", "department_field": "department", "public_read": {}, "via": ["procedure", "NC Clinical Procedure"]}` |
| NC Director | read, report | mọi khoa |
| NC Consultant, NC Admin, NC Auditor | read | NC Auditor chỉ đọc |
| NC Clinician và vai khác | không | |

`scripts/conventions/perm_matrix/nc_procedure_change_request.json`: `{"doctype": "NC Procedure Change Request", "row": "Gợi ý, kịch bản, phương án giá", "codes": "- R - W - - R R R R", "delete": []}`. NC Scenario Change là bảng con: không có tệp perm_matrix, không có scope rule (`check_scope_rules` bỏ qua `istable`).

Thao tác "A" của Trưởng khoa (tiếp nhận, từ chối, đã thực hiện) là quyền qua API, không phải DocPerm write. Người tạo yêu cầu: những vai được quyết định gợi ý (ASM-028-11: NC Finance, NC Director, Trưởng khoa của khoa dịch vụ); máy chủ ghi `ignore_permissions` sau khi kiểm.

`normcore/tests/unit/test_scope_registry.py`: tập `SCOPED` thêm đúng một phần tử `"NC Procedure Change Request"` (ASM-029-15, Quyết định BA trong thiết kế này; đủ ba điều kiện: DocType mới đúng FR-ADJ-007 và dòng ma trận; assertion vẫn so khớp tập đầy đủ; có ASM). Danh sách/số đếm sinh tự động (số DocType, workspace) chạy lại script sinh, không sửa tay.

### 2.5 NC Adjustment Suggestion (không đổi cấu trúc)

Controller: trạng thái "Đã chuyển yêu cầu sửa quy trình" là trạng thái đã quyết (bất biến như "Chấp nhận", "Từ chối"); chỉ đặt được khi `flags.adj_decision`.

## 3. Thành phần

### 3.1 `normcore/benchmark/scenario.py` (thuần, không import frappe; độ phủ ≥ 90%)

```
CHANGE_TYPES = ("Tham số", "Thiết bị", "Dòng định mức")
PARAM, EQUIPMENT, NORM_LINE = CHANGE_TYPES
FIELDS = {PARAM: ("accumulation_rate",), EQUIPMENT: ("utilization_rate",), NORM_LINE: ("hospital_qty", "wastage_rate")}
SCENARIO_SOURCE = " · kịch bản"          # hậu tố nguồn đơn giá của dòng bị đổi
class InvalidChange(ValueError)            # thông báo tiếng Việt, API chuyển thành frappe.throw
@dataclass(frozen=True) class Change: change_type, target_ref, field, new_value (Decimal), old_value (Decimal|None),
                                       service (str|None), department (str|None)
```

| Hàm | Vào → Ra | Ghi chú |
| :-- | :-- | :-- |
| `parse_value(text)` | `"0,5"`, `"15 phút"`, `"5%"`, `"0.5"` → Decimal | Bỏ hậu tố đơn vị (` phút`, `%`), `,` → `.`; rỗng/sai → `InvalidChange("Giá trị gợi ý không đọc được")` |
| `change_for(rule_code, target_ref, current, suggested, service, department)` | → `Change` \| `PROCEDURE` \| `None` | Bảng ánh xạ dưới; `PROCEDURE` = sentinel "cần yêu cầu sửa quy trình"; `None` = không có giá trị để áp |
| `merge(changes, new)` | list Change, Change → list | Cùng khóa `(change_type, target_ref, field, service, department)`: thay `new_value`, giữ `old_value` của dòng đầu (ASM-029-04); khác khóa: nối cuối |
| `apply(snap, changes, equipment)` | dict ảnh chụp, list Change, `{code: {annual_cost, planned_hours}}` → dict ảnh chụp mới | Không sửa `snap`. Bảng áp dưới |
| `recompute(snap, changes, equipment)` | → `snapshot.Recomputed` | `snapshot.recompute(apply(...))` |
| `proposal_text(rule_code, target_ref, current, suggested, text, note=None)` | → str | "Quy tắc {rule}: {text}\nHiện tại: {current} → Đề xuất: {suggested}\nLý do: giá tính toán vượt ngưỡng lệch so với đơn vị tham chiếu" (+ "\nGhi chú: {note}") |

Ánh xạ gợi ý → thay đổi (ASM-029-03):

| Quy tắc | Kết quả `change_for` | `change_type` · `field` · `new_value` |
| :-- | :-- | :-- |
| BR-ADJ-001 | Change | Thiết bị · `utilization_rate` · `parse(suggested)` (0,5); service, department = None |
| BR-ADJ-002 | Change | Dòng định mức · `hospital_qty` · `parse("15 phút")` = 15 |
| BR-ADJ-003 | PROCEDURE | — |
| BR-ADJ-004 | Change | Dòng định mức · `wastage_rate` · `parse("5%")` = 5 (Percent như NC Norm Line) |
| BR-ADJ-005 | Change | Tham số · `accumulation_rate` · `parse("4%")` = 4 (Percent như bộ tham số) |
| BR-ADJ-006, 007 | None | — |

Áp vào ảnh chụp (`snapshot.from_plain`/`to_plain`, `dataclasses.replace`):
- **Tham số** `accumulation_rate`: `params = replace(params, accumulation_rate=new/100)` (đúng quy ước ASM-015-09 của `PricingParams.from_values`). Áp cho cả kịch bản.
- **Thiết bị** `utilization_rate`: `rate = resources.machine_hourly_rate(eq.annual_cost, eq.planned_hours, new)` (BR-COST-004); mọi `ServiceInput` thường có dòng `component == "EQUIPMENT"`, `resource == target_ref`, không loại trừ → `rates[line_id] = replace(rate_cũ, rate=rate, source=rate_cũ.source + SCENARIO_SOURCE)`. Thiết bị không có trong `equipment` → `InvalidChange("Thiếu chi phí năm hoặc giờ kế hoạch của thiết bị {0}")`. Dòng cận lâm sàng (`paraclinical`) không đổi (ASM-029-05).
- **Dòng định mức**: đúng `ServiceInput` `(service, department)`; dòng `line_id == target_ref`; `hospital_qty = new` hoặc `wastage_rate = new/100` (NormLine dùng phân số). Không thấy dịch vụ/dòng → `InvalidChange("{0} không có trong lần tính này")`.

Tính lại toàn bộ ảnh chụp (không chỉ một dịch vụ) vì phân bổ cấp 2 phụ thuộc mọi dịch vụ; đây là "tính lại đầy đủ" mà ASM-028-06 hoãn tới FEAT-029.

### 3.2 `normcore/api/norm.py` (mở rộng FEAT-012/013, không đổi API cũ)

- Tách thân hai nhánh của `new_version` thành `_build_new_version(src) -> (doc_chưa_insert, info)`; `new_version` giữ chữ ký, kiểm quyền, thông báo và kết quả như cũ (test FEAT-012, 013 không sửa).
- Thêm (không whitelisted) `version_for_adjustment(service, department, test_system, line_id, field, value, note) -> {"name", "created": 0|1}` (FR-ADJ-009, ASM-029-08):
  1. Có bộ "Nháp" của (dịch vụ, khoa, hệ thống) (`_open_set`, trạng thái Nháp) → dùng bộ đó.
  2. Có bộ "Đã xác nhận chuyên môn" → `frappe.throw("Bộ định mức {0} đang chờ khóa; khóa hoặc trả về trước khi áp thay đổi")` (cả thao tác chấp nhận rollback).
  3. Không có: nguồn = bộ "Đã khóa" mới nhất của (dịch vụ, khoa, hệ thống); không có → throw "Chưa có bộ định mức Đã khóa của {0}"; `_build_new_version(src)` rồi `insert(ignore_permissions=True)` (NC Finance chỉ có R, A trên bộ định mức; bộ do hệ thống tạo theo FR-ADJ-009).
  4. Dòng `line_id`: đặt `hospital_qty = value` hoặc `wastage_rate = value`; `confirmed_by = confirmed_on = None` (FR-NORM-009: chờ xác nhận lại); dòng không có (bước đã bỏ ở quy trình mới) → throw "Dòng {0} không còn trong bộ định mức mới". `flags.norm_action = "adjustment"`, `flags.from_procedure = True`, `save(ignore_permissions=True)`.
  5. `add_comment("Info", note)` (note: "Thay đổi từ kịch bản {scenario}, gợi ý {adj}: {line_id} {field} {old} → {new}"); `core.notify.notify([head_user của khoa], "Bộ định mức {0} cần xác nhận lại sau điều chỉnh giá", "NC Norm Set", name)`.

### 3.3 API `normcore/api/scenario.py` (mới, whitelisted)

Kiểm quyền tường minh trong từng hàm; lỗi `frappe.throw` tiếng Việt; `frappe.PermissionError` khi không có quyền. Dùng lại `price_compare._can_decide`, `price_compare._run_info`, `costing._snapshot_for`, `price_compare._equipment_facts`, `writer.write_results`.

| Hàm | Tham số | Kết quả | Kiểm |
| :-- | :-- | :-- | :-- |
| `get_open_scenario(run)` | lần tính gốc | `None` hoặc `{name, title, status, created_on, change_count, changes: [{change_type, technical_service, target_ref, field, old_value, new_value, source_suggestion}], rows: [{technical_service, department, service_name, base_price, scenario_price, diff, diff_pct}], warnings, can_create}` | Như `_run_info` (đọc NC Service Cost); `rows` chỉ dịch vụ người gọi đọc được (`frappe.get_list` NC Service Cost của kịch bản, phạm vi khoa tự áp) |
| `create_scenario(run)` | | `{name}` kịch bản mới (rỗng) | `has_permission("NC Costing Run", "create")` (NC Finance); lần gốc không phải kịch bản, `status ∈ {Đã tính, Đã khóa}` |
| `accept_suggestion(name, note=None)` | NC Adjustment Suggestion | `{suggestion, outcome: "scenario" \| "procedure_request" \| "decision_only", scenario?, scenario_price?, norm_set?, norm_set_created?, change_request?, notified?: [user], warnings}` | `_can_decide(sc)`; gợi ý `Mới`; lần tính của gợi ý không phải kịch bản |
| `request_procedure_change(service_cost, proposed_change, reason)` | đề xuất người dùng (FR-ADJ-007 vế 2) | `{change_request, notified}` | `_can_decide(sc)`; `proposed_change`, `reason` không rỗng |
| `change_request_actions(name)` | | `["Tiếp nhận", "Từ chối", "Đã thực hiện"]` hợp lệ cho người gọi | đọc được bản ghi |
| `act_on_change_request(name, action, reason=None)` | | bản ghi + `revision?` | Bảng 2.3; `_is_head_of(department của quy trình)` (vai NC Department Head và khoa trong `scope.get_user_departments(user)`), Administrator được |

`accept_suggestion` (FR-ADJ-006, 007, 009), một giao dịch (lỗi nào cũng rollback toàn bộ, gợi ý giữ "Mới"):
1. `kind = scenario.change_for(...)` với `service, department` của `service_cost`.
2. `PROCEDURE` → `_create_request(sc, proposal_text(...), suggestion)`: quy trình đích (ASM-029-13), insert PCR `Mới` (`flags.pcr_write`, `ignore_permissions`), `notify` head_user của khoa quy trình ("Yêu cầu sửa đổi quy trình {0} từ Bàn so sánh giá"); thiếu head_user → `warnings` "Khoa {0} chưa có trưởng khoa để nhận thông báo". Gợi ý → `Đã chuyển yêu cầu sửa quy trình`. **Không** ghi kịch bản, **không** đụng NC Norm Set (TC-ADJ-06).
3. `None` (BR-ADJ-006, 007) → gợi ý `Chấp nhận`, `outcome = "decision_only"`, `warnings` "Gợi ý không có giá trị để áp vào kịch bản; cập nhật dữ liệu nguồn rồi tính lần mới".
4. `Change` → `_open_or_create(run)` (kịch bản mới nhất có `based_on_run = run`, ngược lại tạo mới như `create_scenario` nhưng bằng máy chủ, ASM-029-01); `merge` vào `scenario_changes` (ghi `source_suggestion`, `old_value` = `parse(current)`); `_recompute(scenario)`; nếu `change_type == Dòng định mức` → `norm.version_for_adjustment(...)` (TC-ADJ-07). Gợi ý `Chấp nhận`.
5. Đặt `decided_by`, `decided_on`, `flags.adj_decision`, `save(ignore_permissions=True)`.

`_recompute(scenario)`: `base = costing._snapshot_for(origin)`; `equipment = price_compare._equipment_facts({mã thiết bị trong thay đổi}, origin)`; `rec = scenario.recompute(base, changes, equipment)` (`InvalidChange` → `frappe.throw`); xóa NC Service Cost cũ của kịch bản; `writer.write_results(scenario_doc, rec.results)`; `allocation_warnings = rec.warnings`; `run_warnings` = cảnh báo đầu vào: lần gốc "Đã tính" và `snapshot.recompute(base)` khác `full_cost` đã lưu của lần gốc ở dịch vụ nào → "Dữ liệu đầu vào đã đổi sau lần tính gốc; kịch bản tính trên dữ liệu hiện tại" (cùng cách FEAT-037); `status = Đã tính`, `progress = 100` (`db_set`). Không ghi NC Reconciliation Line (ASM-029-02). Không đụng bản ghi nào của lần gốc.

Sửa `price_compare.py` (FEAT-028):
- `decide_suggestion(name, "Chấp nhận")` với gợi ý không cần sửa quy trình → gọi cùng `scenario._accept` (FR-ADJ-006 không có đường chấp nhận nào bỏ qua kịch bản); với gợi ý cần sửa quy trình giữ thông báo chặn hiện có (chứa "sửa quy trình", test FEAT-028 giữ nguyên) nhưng đổi câu thành "Gợi ý cần sửa quy trình, không áp trực tiếp được: dùng Chuyển yêu cầu sửa quy trình" (ASM-029-09). "Từ chối" không đổi.
- `generate_suggestions` trên NC Service Cost của kịch bản → throw "Kịch bản không sinh gợi ý; mở lần tính gốc"; `get_service_detail` trả thêm `is_scenario`, `change_request` (PCR của gợi ý nếu có), `can_request_change = _can_decide(sc)`; `can_generate`, `can_decide` = False trên kịch bản.
- `_suggestions`/`get_comparison.suggestion_counts`: thêm khóa `"Đã chuyển yêu cầu sửa quy trình"`.

### 3.4 Giao diện

Chi tiết ở `ui-design.md`: SCR-DSK-026 (`PriceCompare.vue`) thêm dải và khung "Kịch bản đang mở", nút Chấp nhận gọi `accept_suggestion`, nút "Chuyển yêu cầu sửa quy trình", "Đề xuất sửa quy trình"; form NC Costing Run (kịch bản), form/list NC Procedure Change Request, dải trên form NC Clinical Procedure. Bản dịch `normcore/translations/vi.d/FEAT-029.csv`.

## 4. Tiêu chí nghiệm thu

Dữ liệu: thế giới vàng `cf.make_golden_world()` + `make_golden_allocation` như `normcore/api/test_price_compare.py`; trưởng khoa K01 = `NC Department.head_user`.

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | EQ1 hệ số 0,4 **trước** khi tính lần gốc; chấp nhận gợi ý BR-ADJ-001 (EQ1 0,4 → 0,5): có kịch bản `based_on_run` = gốc, một NC Scenario Change (Thiết bị, EQ1, `utilization_rate`, 0.4 → 0.5, `source_suggestion`); NC Service Cost DV-TEST-A của kịch bản có `calculated_price` = 302.132,73 (golden) ≠ giá gốc; mọi NC Service Cost của lần gốc giữ nguyên `calculated_price`, `full_cost`, `modified`; lần gốc giữ `status`, `modified`; gợi ý "Chấp nhận" | TC-ADJ-05 | FR-ADJ-006 | `normcore/api/test_scenario.py::test_TC_ADJ_05_kich_ban_tinh_lai_goc_khong_doi` |
| 2 | Chấp nhận gợi ý BR-ADJ-003 (L05 → mặt hàng tương đương): số NC Norm Set và mọi dòng bộ định mức DV-TEST-A không đổi; kịch bản không có thay đổi mới; có NC Procedure Change Request `Mới`, `procedure` = quy trình của DV-TEST-A/K01, `source_suggestion`, `requested_by` = người chấp nhận, `proposed_change` có mã quy tắc và giá trị đề xuất; Notification Log cho head_user K01 trỏ tới yêu cầu; gợi ý "Đã chuyển yêu cầu sửa quy trình" | TC-ADJ-06 | FR-ADJ-007 | `test_scenario.py::test_TC_ADJ_06_yeu_cau_sua_quy_trinh` |
| 3 | Chấp nhận gợi ý BR-ADJ-002 (L04 20 → 15 phút): có NC Norm Set mới `status = Nháp`, `previous_version` = bộ đã khóa, `version_no` kế tiếp, dòng L04 `hospital_qty = 15`, `confirmed_by` trống; bộ đã khóa không đổi; kịch bản có thay đổi Dòng định mức L04 và giá DV-TEST-A trong kịch bản giảm | TC-ADJ-07 | FR-ADJ-009 | `test_scenario.py::test_TC_ADJ_07_bo_dinh_muc_nhap_so_phut_moi` |
| 4 | Chấp nhận lần hai vào cùng kịch bản: thay đổi cộng dồn; cùng khóa ghi đè `new_value`, giữ `old_value`; `get_open_scenario` trả đúng số thay đổi và chênh lệch | — | FR-ADJ-006 | `test_scenario.py::test_FR_ADJ_006_cong_don_va_ghi_de` |
| 5 | `decide_suggestion(…, "Chấp nhận")` gợi ý thường cũng ghi kịch bản; gợi ý cần sửa quy trình vẫn bị chặn (test FEAT-028 xanh, không sửa) | — | FR-ADJ-006, 007 | `test_scenario.py::test_FR_ADJ_006_decide_cung_ghi_kich_ban`; `test_price_compare.py` (cũ) |
| 6 | Đã có bộ "Nháp" → áp vào bộ đó, không tạo thêm; bộ "Đã xác nhận chuyên môn" → chặn, rollback (gợi ý vẫn "Mới", không có NC Scenario Change) | — | FR-ADJ-009 | `test_scenario.py::test_FR_ADJ_009_dung_bo_nhap_dang_co`, `test_FR_ADJ_009_bo_cho_khoa_chan` |
| 7 | Đề xuất người dùng: lý do trống bị chặn; có lý do → PCR không có `source_suggestion`, trưởng khoa nhận thông báo | — | FR-ADJ-007 | `test_scenario.py::test_FR_ADJ_007_de_xuat_nguoi_dung` |
| 8 | Trưởng khoa khoa đó "Tiếp nhận" → có bản nháp phiên bản kế tiếp (FR-WF-009) với Comment chứa `proposed_change`; khoa khác, Finance, Auditor bị PermissionError; "Từ chối" cần lý do; "Đã thực hiện" chỉ khi đã ban hành phiên bản mới hơn | — | FR-ADJ-007, FR-WF-009 (UC-007 1c) | `test_scenario.py::test_UC_007_1c_tiep_nhan_tao_ban_nhap`, `test_FR_ADJ_007_luong_trang_thai` |
| 9 | Kịch bản: `run_costing`, `lock_costing`, `duplicate_run`, sửa `scenario_changes` ngoài API bị chặn; `generate_suggestions` trên kịch bản bị chặn | — | FR-ADJ-006 | `normcore/nc_costing/doctype/nc_costing_run/test_nc_costing_scenario.py::test_kich_ban_chi_sua_qua_api` |
| 10 | Quyền chấp nhận: Finance, Director, Trưởng khoa khoa mình được; khoa khác, Consultant, Admin, Auditor bị PermissionError; Trưởng khoa thấy `rows` kịch bản chỉ của khoa mình | — | FR-ACC-003, 007 | `test_scenario.py::test_quyen_chap_nhan_va_xem_kich_ban` |
| 11 | Quyền NC Procedure Change Request: Clinician không đọc; Auditor đọc, không tạo/sửa/xóa; Trưởng khoa chỉ đọc yêu cầu của khoa mình; Finance tạo được; sửa ngoài API bị chặn | — | FR-ACC-003, 007 | `normcore/nc_benchmark/doctype/nc_procedure_change_request/test_nc_procedure_change_request.py::test_quyen_*`, `test_sua_ngoai_api_bi_chan` |
| 12 | `scenario.py` thuần: `parse_value`, `change_for` mọi quy tắc, `merge`, `apply` từng loại (không sửa ảnh chụp vào), lỗi `InvalidChange`; DV-TEST-A ảnh chụp vàng với EQ1 0,4 → `recompute` sau đổi 0,5 cho 302.132,73 | TC-ADJ-05 (đơn vị) | FR-ADJ-006 | `normcore/tests/unit/test_benchmark_scenario.py::test_TC_ADJ_05_apply_thiet_bi_ve_golden`, `test_FR_ADJ_006_*` (độ phủ `scenario.py` ≥ 90%) |
| 13 | Trang có chuỗi qua `__()`, có bản dịch, nút gọi đúng API | — | FR-ADJ-006 | `normcore/tests/unit/test_feat_029_ui.py` |

## 5. Giả định và rủi ro

Giả định ASM-029-01..17 ở `docs/decisions/assumptions/FEAT-029.md`. Không có CF, AMD, DEF.

Rủi ro:
- Lần gốc "Đã tính" (chưa khóa) dựng ảnh chụp từ dữ liệu sống: dữ liệu đổi sau lần tính thì giá kịch bản phản ánh cả thay đổi đó; có cảnh báo trên kịch bản. Lần gốc "Đã khóa" dùng ảnh chụp đã lưu nên ổn định.
- Tính lại toàn bộ kịch bản chạy đồng bộ trong yêu cầu chấp nhận (ASM-029-16): lần tính rất lớn có thể chậm; đo trên bộ vàng và ghi vào implementation-log. Nếu vượt 10 s ở bộ hiệu năng thì báo Lead (không tự đổi sang tác vụ nền).
- Đổi hệ số sử dụng thiết bị trong kịch bản ảnh hưởng mọi dịch vụ dùng thiết bị đó, kể cả khoa khác của người chấp nhận (đúng bản chất BR-ADJ-001; ghi vào As-Built).
