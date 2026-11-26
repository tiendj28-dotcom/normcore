# FEAT-013 — Phiên bản bộ định mức theo quy trình mới — Thiết kế kỹ thuật

Issue NORM-51. Nguồn: `srs.md` FR-NORM-015 (Must), FR-NORM-012, FR-WF-011; `use-cases.md` UC-009 luồng 1a, 9a; `data-model.md` 3.5 (NC Norm Set, NC Norm Line), mục 4 (dòng "Bộ định mức"), 5.2, DI-03, DI-04; `architecture.md` ADR-003 (logic thuần), ADR-010 (Desk Page Vue qua API whitelisted); `ux-foundations.md` SCR-DSK-014; TC-NORM-08 (sau TC-WF-06).

Phụ thuộc (đều DONE trên `origin/develop` `f71b9f4`): FEAT-008 (`create_revision` giữ `step_id`; `_flag_norm_sets` đặt `needs_update`, `step_change_note`), FEAT-012 (NC Norm Set/Line, `normcore/norm/`, `api/norm.py::new_version`, lưới `norm-grid`). **Mở rộng, không tạo lại** DocType hay API.

Giả định: `docs/decisions/assumptions/FEAT-013.md` (ASM-013-01..08). Sửa thiết kế: `docs/decisions/amendments/AMD-013-01.md` (trường `step_removed` của NC Norm Line, ngoại lệ DI-04). Không có câu hỏi mở cho Lead.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-NORM-015 | `new_version(norm_set)` khi (dịch vụ, khoa) có quy trình "Đã ban hành" **mới hơn** quy trình của bộ nguồn: tạo bộ "Nháp" tham chiếu quy trình mới; (a) **mang sang** dòng có `step_id` còn trong quy trình mới và mọi dòng "Chung cho cả dịch vụ"; (b) **đánh dấu** dòng có `step_id` không còn (`step_removed` = 1, giữ nguyên `step_id` cũ); (c) **liệt kê** bước của quy trình mới chưa có dòng (`steps_without_lines`). Kết quả trả về, ghi Comment trên bộ mới, và hiện trên lưới |
| FR-NORM-012 (giữ) | Không có quy trình mới hơn: `new_version` giữ đúng hành vi FEAT-012 (chỉ từ "Đã khóa", sao chép cùng quy trình, ASM-012-09) |
| FR-NORM-010 (mở rộng) | Dòng `step_removed` chặn "Xác nhận chuyên môn" và `confirm_line` (lý do "Thuộc bước đã bỏ") đến khi người dùng gán bước còn tồn tại, chuyển "Chung cho cả dịch vụ", hoặc xóa dòng |

**Không làm**: tự sinh dòng cho bước mới hay cho dòng nguồn lực mới của quy trình (FR chỉ yêu cầu liệt kê; người dùng thêm bằng "Thêm dòng" có sẵn, ASM-013-04); gỡ cờ `needs_update` ở bộ nguồn (bộ nguồn "Đã khóa" chuyển "Đã thay thế" khi bộ mới khóa — DI-03 đã có; ASM-013-06); cập nhật tại chỗ một bộ Nháp sang quy trình mới; trường **[1.1]** (FEAT-034); đề xuất AI (FEAT-025).

## 2. DocType (module NC Costing — mở rộng)

### 2.1 NC Norm Line (bảng con) — thêm một trường (AMD-013-01)

| Trường | Nhãn | Kiểu | BB | Thuộc tính | Ghi chú |
| :-- | :-- | :-- | :-- | :-- | :-- |
| step_removed | Thuộc bước đã bỏ | Check | | `read_only` = 1, `in_list_view` = 0, mặc định 0 | Đặt bởi `new_version` theo quy trình mới [FR-NORM-015]. Bật thì DI-04 không áp cho dòng đó |

Chỉ thêm trường (mặc định 0) → `bench migrate` thêm cột, **không cần patch**. `step_removed` **không** thuộc `LINE_INPUTS` (không phải trường người dùng nhập, không được ghi qua `save_line`).

### 2.2 NC Norm Set — không đổi cấu trúc

Dùng trường đã có: `procedure` (quy trình mới), `previous_version` (bộ nguồn), `version_no` (max + 1 của (dịch vụ, khoa)), `next_line_seq` (lấy từ bộ nguồn, giữ `line_id`), `needs_update` = 0 ở bộ mới.

### 2.3 Controller `NCNormSet.validate` (mọi đường ghi)

Trong `validate_lines`, trước khi gọi `validation.line_errors`, chuẩn hóa `step_removed` của từng dòng bằng hàm thuần `carry.removed_flag(row, before, step_ids, creating_version)` (mục 4.1):

- Giữ `step_removed` = 1 **chỉ khi**: `step_id` có giá trị, `service_level` = 0, `step_id` ∉ bước của quy trình, **và** (dòng cũ đã có `step_removed` = 1, hoặc bộ đang được tạo bởi `new_version` — `self.is_new()` và `self.flags.norm_action == "new_version"`).
- Mọi trường hợp khác: `step_removed` = 0. Hệ quả: người dùng gán `step_id` hợp lệ hoặc bật `service_level` thì cờ tự gỡ; client gửi `step_removed` = 1 qua `frappe.client`/form không có tác dụng (bị đặt lại 0 rồi DI-04 báo lỗi nếu mã bước sai).
- `line_errors` nhận thêm ctx `removed` (bộ `line_id` có cờ) — xem 4.2; DI-04 bỏ qua dòng có cờ.
- Khi `flags.norm_action == "new_version"` lúc tạo: dòng mang sang không tính là "sửa" (giữ quy tắc `changed = not procedure_resource_row` của FEAT-012); không mang xác nhận (`confirmed_by`, `confirmed_on` trống).

## 3. API whitelisted — `normcore/api/norm.py` (mở rộng)

### 3.1 `new_version(norm_set)` — đổi thân, giữ chữ ký

1. `frappe.has_permission(NS, "create", throw=True)`; `src = _load(norm_set, "write")` (phạm vi khoa như FEAT-012).
2. `target = _latest_published(src.technical_service, src.department)`: NC Clinical Procedure `workflow_state` = "Đã ban hành", cùng dịch vụ và khoa, `version_no` lớn nhất (ASM-013-01). `newer = target and version_no(target) > version_no(src.procedure)`.
3. **Không `newer`** → nhánh FEAT-012 nguyên vẹn (chỉ từ "Đã khóa", trả bộ đang soạn nếu có, sao chép dòng cùng quy trình). Không đổi hành vi, test FEAT-012 giữ xanh.
4. **`newer`**:
   - `src.status` = "Đã thay thế" → `frappe.throw("Bộ định mức đã thay thế, không tạo phiên bản được")`. Cho phép "Nháp", "Đã xác nhận chuyên môn", "Đã khóa" (ASM-013-02).
   - Bộ "Nháp"/"Đã xác nhận chuyên môn" cùng (dịch vụ, khoa) **có `procedure` = target** đã tồn tại → trả `{"name": <bộ đó>, "existing": 1, "message": "Đã có bộ định mức đang soạn theo quy trình <target>: <tên>"}` (ASM-013-03), không tạo thêm.
   - `res = carry.carry_lines([_dict(r) | {"step_removed": r.step_removed} for r in src.lines], [s.step_id for s in target.steps])`.
   - Tạo bộ mới: `technical_service`, `department` của nguồn; `procedure` = target; `version_no` = max + 1; `previous_version` = src; `status` = "Nháp"; `next_line_seq` = src; dòng = `res["lines"]`. `new.flags.norm_action = "new_version"`; `new.insert()` (quyền người dùng, như FEAT-012).
   - `new.add_comment("Info", carry.format_note(res, missing))` với `missing = carry.steps_without_lines(step_ids, res["lines"])`.
   - Trả `{"name", "procedure", "existing": 0, "carried": [line_id], "removed": [line_id], "removed_steps": [step_id], "steps_without_lines": [step_id]}`.
5. Bộ nguồn **không đổi** (kể cả `needs_update`).

Mã lỗi: `frappe.PermissionError` (không quyền tạo/ghi, ngoài khoa — 403); `frappe.ValidationError` (bộ "Đã thay thế"; nhánh FEAT-012: bộ chưa khóa và không có quy trình mới hơn — giữ thông báo cũ "Chỉ tạo phiên bản mới từ bộ Đã khóa").

### 3.2 `get_norm_set(name)` — thêm khóa, không bỏ khóa cũ

- Mỗi dòng thêm `step_removed` (bool). Dòng `step_removed` **không** rơi vào nhóm "Chung cho cả dịch vụ" nữa: `groups` thêm một nhóm `{"step_id": None, "removed": True, "title": "Bước đã bỏ", "lines": [...], "total": ...}` đặt **trước** nhóm "Chung"; chỉ có khi có dòng. Nhóm "Chung" chỉ gồm `service_level` hoặc `step_id` trống.
- `steps_without_lines`: `[{"step_id", "step_title"}]` từ `carry.steps_without_lines` theo thứ tự bước của quy trình. Chỉ tính khi `status` = "Nháp" (bộ đóng trả `[]`).
- `blockers` (Nháp): thêm lý do "Thuộc bước đã bỏ" qua `validation.confirm_blockers` (4.2).
- `actions`: thêm `"new_version"` khi người dùng có quyền tạo + ghi, bộ không "Đã thay thế", và có quy trình "Đã ban hành" mới hơn (kể cả bộ "Nháp"/"Đã xác nhận chuyên môn"); giữ điều kiện cũ ở "Đã khóa". Thêm `"delete_line"` áp cho dòng `step_removed` (xem 3.4).
- `doc` thêm `newer_procedure` (tên quy trình mới hơn hoặc `None`) để lưới ghi rõ nút.
- Chi phí tạm tính: dòng `step_removed` vẫn tính tiền như dòng thường, khóa tổng hợp theo `step_id` cũ (bước đã bỏ hiện là một hàng riêng trong bảng chéo; ASM-013-07).

### 3.3 `save_line` — giữ; `step_removed` không nằm trong `SAVE_FIELDS`

Gán `step_id` hợp lệ hoặc `service_level` = 1 cho dòng có cờ → controller gỡ cờ (2.3). Dòng có cờ lấy từ quy trình (`procedure_resource_row` có giá trị) được sửa `step_id`/`service_level` qua `save_line` (FEAT-012 chỉ hiện ô này cho dòng thêm tay; lưới FEAT-013 hiện cho dòng có cờ — ui-design). Kiểm FR-NORM-005 giữ nguyên (chỉ dòng thêm tay).

### 3.4 `delete_line` — nới cho dòng có cờ

Giữ ASM-012-07 (dòng từ quy trình không xóa được), **trừ** dòng `step_removed` = 1: xóa được (bước gốc không còn, không còn gì để "loại trừ"; ASM-013-05).

### 3.5 `confirm_line` — thêm chặn

Dòng `step_removed` = 1 → `frappe.throw("Dòng {0} thuộc bước đã bỏ ({1}): gán bước khác, chuyển Chung cho cả dịch vụ hoặc xóa trước khi xác nhận")`.

## 4. Logic thuần (không import `frappe`, pytest)

### 4.1 `normcore/norm/init_from_procedure.py` — thêm (theo khối kế hoạch "`norm/init_from_procedure.py`")

| Hàm | Vào → ra | Luật |
| :-- | :-- | :-- |
| `carry_lines(old_lines, step_ids)` | `list[dict]`, `list[str]` theo thứ tự quy trình mới → `{"lines", "carried", "removed", "removed_steps"}` | Giữ thứ tự dòng của bộ nguồn. Mỗi dòng: chép các khóa `LINE_INPUTS` (truyền vào dưới dạng dict đã lọc). `service_level` = 1 → mang sang. `step_id` ∈ `step_ids` → mang sang. Còn lại (`step_id` ∉ `step_ids`) → mang sang **kèm** `step_removed` = 1, `line_id` vào `removed`, `step_id` vào `removed_steps` (không trùng, giữ thứ tự xuất hiện). Dòng bộ nguồn đã có `step_removed` = 1 mà bước vẫn không có → vẫn `removed`. Không mang `confirmed_by`, `confirmed_on` |
| `steps_without_lines(step_ids, lines)` | → `list[str]` | Bước trong `step_ids` không có dòng nào với `step_id` đó, `service_level` = 0, `step_removed` = 0. Dòng loại trừ vẫn tính là "có dòng" |
| `removed_flag(row, before, step_ids, creating_version)` | → `0/1` | Luật 2.3 |
| `format_note(res, missing)` | → `str` | `"Theo quy trình mới: mang sang S001, S003, S004; đánh dấu bước đã bỏ S002 (L002); bước chưa có dòng S005"`; phần rỗng ghi "không có". Bước mang sang = `step_id` duy nhất của dòng mang sang không cờ, không `service_level`, theo thứ tự `step_ids` |

### 4.2 `normcore/norm/validation.py` — mở rộng, giữ chữ ký

- `line_errors(line, ctx)`: DI-04 bỏ qua khi `line.get("step_removed")`.
- `confirm_blockers(lines)`: thêm lý do `"Thuộc bước đã bỏ"` (sau "Chưa liên kết danh mục", trước "Còn đề xuất AI chưa xử lý") cho dòng có `step_removed`. Dòng có cờ luôn chưa xác nhận (không mang xác nhận, `confirm_line` chặn) nên vẫn có "Chưa xác nhận".

### 4.3 Không có phép tính tiền mới

FEAT-013 không thêm công thức; chi phí tạm tính dùng nguyên `costing/provisional.py` + `engine.applied_qty` (FEAT-012). Không chạm `docs/golden/`.

## 5. Giao diện (chi tiết ở `ui-design.md`)

SCR-DSK-014 (`NormGrid.vue`): nút "Tạo phiên bản theo quy trình mới" khi có `newer_procedure`; hộp kết quả sau khi tạo; dải "Thay đổi theo quy trình mới" ở bộ mới (mang sang / bước đã bỏ / bước chưa có dòng); nhóm "Bước đã bỏ"; nhãn dòng "Bước đã bỏ"; ô gán bước cho dòng có cờ; "Thêm dòng" điền sẵn bước từ danh sách bước chưa có dòng. Form NC Norm Set (Desk): dải "Cần cập nhật" thêm liên kết "Mở lưới định mức để tạo phiên bản theo quy trình mới".

## 6. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Dựng như TC-WF-06 (v1 4 bước S001..S004, mỗi bước một dòng nguồn lực; bộ "Đã khóa" dựa v1; v2 bỏ S002, thêm S005, đổi S003; ban hành v2). `new_version(bộ đã khóa)` → bộ "Nháp" mới, `procedure` = v2, `previous_version` = bộ nguồn, `version_no` = max + 1; dòng của S001, S003, S004 có trong bộ mới, `step_removed` = 0, giữ `line_id`; dòng của S002 có `step_removed` = 1; `steps_without_lines` = `["S005"]`; `get_norm_set` trả cùng danh sách và nhóm "Bước đã bỏ" | TC-NORM-08 | FR-NORM-015 | `normcore/api/test_norm_version.py::test_TC_NORM_08_phien_ban_theo_quy_trinh_moi` (I) |
| 2 | Hàm thuần `carry_lines` / `steps_without_lines` / `format_note` / `removed_flag` với đúng dữ liệu TC-NORM-08 và ca biên (dòng chung, dòng thêm tay, dòng loại trừ, bộ nguồn đã có cờ, quy trình không đổi bước) | TC-NORM-08 | FR-NORM-015 | `normcore/tests/unit/test_norm_carry.py::test_TC_NORM_08_carry_lines_*` (U) |
| 3 | Bộ mới có dòng S002 → `confirm_set` từ chối, liệt kê dòng S002 lý do "Thuộc bước đã bỏ"; `confirm_line` dòng đó từ chối | — | FR-NORM-015, FR-NORM-010 | `test_FR_NORM_015_dong_buoc_bo_chan_xac_nhan` |
| 4 | Gán `step_id` = S003 (hoặc `service_level` = 1) cho dòng có cờ qua `save_line` → cờ gỡ, lưu được; xóa dòng có cờ qua `delete_line` được; xóa dòng từ quy trình không cờ vẫn bị từ chối (ASM-012-07 giữ) | — | FR-NORM-015 | `test_FR_NORM_015_xu_ly_dong_buoc_bo` |
| 5 | `frappe.client.set_value`/`doc.save()` đặt `step_removed` = 1 cho dòng S001 hợp lệ → cờ bị đặt lại 0; đặt cho dòng mã bước sai → lỗi DI-04 | — | DI-04 | `test_FR_NORM_015_co_buoc_bo_khong_ghi_tu_client` |
| 6 | Bộ "Nháp" dựa v1 (`needs_update` = 1) → `new_version` được, bộ nguồn không đổi; gọi lần hai → trả bộ đã có (`existing` = 1), không tạo thêm | — | FR-NORM-015 | `test_FR_NORM_015_tu_bo_nhap_va_khong_tao_trung` |
| 7 | Không có quy trình mới hơn → hành vi FEAT-012 giữ nguyên: bộ "Nháp" gọi `new_version` bị từ chối; bộ "Đã khóa" sao chép cùng quy trình (test TC-NORM-06 cũ xanh, không sửa) | TC-NORM-06 | FR-NORM-012 | test FEAT-012 sẵn có + `test_FR_NORM_015_khong_co_quy_trinh_moi_giu_hanh_vi_cu` |
| 8 | Bộ "Đã thay thế" → từ chối | — | FR-NORM-015 | `test_FR_NORM_015_bo_da_thay_the_tu_choi` |
| 9 | Quyền: NC Auditor `get_norm_set` được, `new_version` PermissionError; NC Finance (chỉ R, A) `new_version` PermissionError; NC Clinician khoa khác PermissionError; `actions` không có `new_version` cho các vai đó | — | FR-ACC-003, FR-ACC-007 | `test_quyen_new_version_*` |
| 10 | Lưới: nút, dải thay đổi, nhóm "Bước đã bỏ", chuỗi qua `__()` có trong `vi.csv`, chỉ gọi `normcore.api.norm.*` | — | FR-NORM-015 | `normcore/tests/unit/test_norm_grid_ui.py` (thêm ca) |

Không có DocType mới → không cần bộ test quyền DocType mới; quyền NC Norm Set giữ ma trận mục 4 (dòng "Bộ định mức").

## 7. Rủi ro

- Quy trình v2 "Đã ban hành" ngày hiệu lực tương lai: v1 vẫn "Đã ban hành" đến ngày đó (TC-WF-04). Chọn v2 (version lớn nhất) — khớp FEAT-008 đặt cờ ngay lúc ban hành (ASM-013-01).
- Dòng nguồn lực mới trong bước còn tồn tại (vd đổi nguồn lực S003 thêm dòng R mới) không tự sinh dòng định mức; người dùng thấy ghi chú "đổi S003" ở bộ nguồn và tự thêm (ASM-013-04). Rủi ro bỏ sót: hạ bằng dải thay đổi hiển thị `step_change_note` của bộ nguồn.
- `NormGrid.vue` lớn; thay đổi chỉ thêm nhánh hiển thị, không đổi luồng lưu.

## 8. Tệp chạm tới

`normcore/norm/init_from_procedure.py`, `normcore/norm/validation.py`, `normcore/nc_costing/doctype/nc_norm_line/nc_norm_line.json`, `normcore/nc_costing/doctype/nc_norm_set/nc_norm_set.py`, `normcore/nc_costing/doctype/nc_norm_set/nc_norm_set.js`, `normcore/api/norm.py`, `normcore/public/js/norm_grid/NormGrid.vue`, `normcore/translations/vi.csv`, test: `normcore/tests/unit/test_norm_carry.py` (mới), `normcore/tests/unit/test_norm_validation.py` (thêm ca), `normcore/api/test_norm_version.py` (mới), `normcore/tests/unit/test_norm_grid_ui.py` (thêm ca). Tài liệu: `docs/data-model.md` 3.5 (áp AMD-013-01), `docs/as-built/FEAT-013.md`, `docs/rtm-testref.md` (mục `## FEAT-013`, hoặc `docs/rtm-testref/FEAT-013.md` nếu đã có trên develop).

## 9. Ghi chú cho Dev

- Dựng dữ liệu TC-NORM-08 dùng lại `RevisionBase`/`make_v1` (`normcore/api/test_procedure_revision.py`) và cách sửa v2 + ban hành của `normcore/api/test_procedure_norm_flag.py` (`edit_v2`, `publish_v2`); không chép số liệu khác.
- Không sửa test cũ. Nếu test FEAT-012 về nhóm "Chung" hay `new_version` đỏ do thay đổi, dừng và báo Lead.
- `step_removed` không thêm vào `LINE_INPUTS` (nếu thêm, `validate_frozen` của bộ "Đã xác nhận chuyên môn" sẽ đổi nghĩa).
