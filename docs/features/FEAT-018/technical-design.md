# FEAT-018: Khóa, ảnh chụp đầu vào, so sánh hai lần tính (thiết kế kỹ thuật)

Issue NORM-47. Nguồn:
- `srs.md`: FR-COST-011, FR-COST-012, FR-COST-013; NFR-REL-001.
- `use-cases.md`: UC-012 bước 8, nhánh 8a (so sánh), 8c (đã khóa → từ chối tính lại, cho nhân bản).
- `architecture.md`: ADR-004 (ảnh chụp JSON nén + mã băm, tệp private gắn lần tính; chạy lại dùng ảnh chụp, không dùng dữ liệu sống; [1.1] tăng phiên bản lược đồ, lược đồ cũ vẫn đọc được). Mục 8 "Dữ liệu": bản ghi đã khóa không sửa, thay đổi tạo phiên bản mới.
- `data-model.md`: NC Costing Run (`snapshot_file`, `snapshot_hash`), mục 4 dòng "Lần tính giá, kết quả, đối soát", mục 5.4 (điều kiện khóa).
- `ux-foundations.md`: SCR-DSK-022 (trạng thái "đã khóa"). `test-cases.md`: mục 2.2, 2.3 biến thể V1; TC-COST-09, TC-COST-11, TC-COST-18.
- Golden: `docs/golden/golden_engine.py` (`run()` và `run(False)` = V1).

Phụ thuộc đã DONE trên `origin/develop` `dc1c1af`:
- FEAT-015: `runner.run`, `engine.ServiceInput/ServiceResult`, `loader.load_context/load_service`, `writer.write_results`, API `normcore/api/costing.py`, form SCR-DSK-022.
- FEAT-017: `allocation.allocate`, `reconcile.reconcile/lock_blockers`, `loader.allocation_context`, `NCCostingRun.lock_costing` (điểm cắm ảnh chụp, ASM-017-07), `writer.write_reconciliation`, API `lock_run`.

**Phụ thuộc mềm vào FEAT-036 (NORM-42, đang In Review):** FEAT-036 đã viết `normcore/costing/snapshot.py` (`to_plain`, `from_plain`, `build`, `dumps`, `digest`, `reproduce`, `VERSION = 1`) và `loader.capture_snapshot(run, eligible)`, và để lại việc lưu tệp, mã băm khi khóa cho FEAT-018 (ASM-036-21). FEAT-018 **mở rộng** các hàm đó, không viết lại (ASM-018-01). Dev chỉ bắt đầu T01 khi `git cat-file -e origin/develop:normcore/costing/snapshot.py` thành công; chưa có thì Blocked "chờ NORM-42 merge", mention Lead.

Giả định: `docs/decisions/assumptions/FEAT-018.md` (ASM-018-01..12). Không có AMD: hai trường mới đã có trong `data-model.md`, không có DocType mới.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-COST-011 | Khi khóa: dựng ảnh chụp toàn bộ đầu vào đã phân giải (định mức, đơn giá đã chọn kèm nguồn, tham số giá, số liệu kế toán, quy tắc và tiêu chí phân bổ, sản lượng, ngưỡng đối soát; phần cận lâm sàng do FEAT-036 dựng). Tính lại từ ảnh chụp và so với kết quả đã lưu; trùng hết mới lưu tệp `.json.gz` private, `snapshot_hash` (sha256) và chuyển "Đã khóa" (ASM-018-02, 03). Thao tác "Kiểm tra tái lập" tính lại từ tệp đã lưu, không đọc dữ liệu sống, so từng trường (NFR-REL-001). |
| FR-COST-012 | "Đã khóa": `run_costing` từ chối với câu riêng; mọi sửa trường của bản ghi bị từ chối. `duplicate_run` tạo lần tính mới ở "Nháp", cùng đầu vào và phạm vi, không mang kết quả, đối soát, ảnh chụp (ASM-018-06, 07). |
| FR-COST-013 (Should) | So sánh hai lần tính "Đã tính"/"Đã khóa": theo (dịch vụ, khoa), chênh lệch giá thành toàn bộ và từng cấu phần (6 cấu phần trực tiếp, 5 loại phân bổ, tích lũy, nghĩa vụ, giá tính toán, giá làm tròn). Chênh lệch = lần so sánh − lần gốc. Hàm thuần `costing/compare.py`; màn hình Script Report "So sánh hai lần tính giá" (ASM-018-08, 09). |
| NFR-REL-001 | Ảnh chụp tất định: JSON chuẩn hóa (`snapshot.dumps`), Decimal dạng chuỗi, khóa sắp xếp; tính lại bằng đúng `runner.run` + `allocation.allocate` + `reconcile.reconcile`. |

**Không làm ở FEAT này:**
- Thêm nhóm dữ liệu cận lâm sàng vào ảnh chụp (FR-COST-032): FEAT-036 đã dựng trong `capture_snapshot`; FEAT-018 chỉ lưu. Đối soát vật chất (FEAT-037) chưa có nên chưa vào ảnh chụp.
- Kịch bản điều chỉnh (`based_on_run`, `scenario_changes`, FEAT-029). Nhân bản **không** đặt `based_on_run` (ASM-018-07).
- Bàn so sánh giá với giá tham chiếu (SCR-DSK-026, FEAT-027/028) — khác với so sánh hai lần tính ở đây.
- Xuất biểu (FEAT-019).

## 2. DocType

### 2.1 NC Costing Run (mở rộng, không tạo lại; chỉ thêm trường → không cần patch)

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| snapshot_file **(mới)** | Ảnh chụp đầu vào | Attach | | `read_only`, `no_copy`. Chỉ ghi qua `lock_costing` (`db_set`). Section mới "Ảnh chụp đầu vào" sau `allocation_warnings`, `depends_on: eval:doc.snapshot_file` |
| snapshot_hash **(mới)** | Mã băm ảnh chụp | Data | | `read_only`, `no_copy`. sha256 hex (64 ký tự) của JSON chuẩn hóa **trước khi nén** (ASM-018-03) |
| progress, allocation_warnings (đã có) | | | | thêm `no_copy: 1` (để Desk "Nhân bản" chuẩn cũng không chép) |

`status` đã có `no_copy`. Nếu FEAT-036 đã merge: `run_warnings` đã `no_copy`; `volume_scenario`, `compliance_allocation_mode` là đầu vào, được chép khi nhân bản.

**Controller `validate` (bổ sung):**
- `prev.status == "Đã khóa"` và có bất kỳ trường nào khác (so `prev.as_dict()` với `self.as_dict()`, bỏ `modified`, `modified_by`) → `frappe.throw(_("Lần tính giá {0} đã khóa, không sửa được. Dùng Nhân bản để tạo lần tính mới."))` (ASM-018-06). Không chặn khi `is_new()` (test cũ chèn thẳng bản ghi "Đã khóa", `test_nc_costing_parameter_set.py:24`).
- `snapshot_file`, `snapshot_hash` khác `prev` khi lưu qua form/API → từ chối "Ảnh chụp chỉ do thao tác Khóa ghi". Mới tạo mà có giá trị → xóa về rỗng.
- `on_trash`: status "Đã khóa" → từ chối (không ai có quyền xóa theo ma trận; chặn thêm cho Administrator).

**Quyền:** không đổi DocPerm. Dòng "Lần tính giá, kết quả, đối soát": NC Finance W (tạo, sửa → khóa, nhân bản); NC Director, NC Admin, NC Auditor R (xem, so sánh, kiểm tra tái lập, tải ảnh chụp); vai trò khác không có quyền. Tệp ảnh chụp `is_private = 1`, `attached_to_doctype = "NC Costing Run"`, `attached_to_name`, `attached_to_field = "snapshot_file"`: Frappe cho tải khi có quyền đọc lần tính.

### 2.2 Bảng khác
NC Service Cost, NC Service Cost Line, NC Reconciliation Line: không đổi cấu trúc. Nhân bản không chép các bản ghi này.

## 3. Logic thuần (`normcore/costing/`, không import `frappe`)

### 3.1 `snapshot.py` (mở rộng tệp của FEAT-036)

| Hàm / hằng | Làm gì |
| :-- | :-- |
| `VERSION = 2` | Lược đồ 2 = lược đồ 1 + mục `allocation` + `meta`. `reproduce`/`recompute` đọc được cả 1 và 2 (ADR-004 [1.1]); lược đồ 1 tính không phân bổ như FEAT-036. Phiên bản khác → `ValueError("Phiên bản ảnh chụp không được hỗ trợ")` |
| `_CLASSES` | thêm `allocation.Rule`, `allocation.AllocationInput` (và lớp FEAT-036 có sẵn) |
| `to_plain` (sửa nhánh map) | khóa không phải `str` (ví dụ `(trung tâm, loại)` của `AllocationInput.accounting`) mã hóa bằng `to_plain(k)`; sắp theo `dumps` của khóa đã mã hóa. Khóa `str` giữ nguyên cách cũ (ảnh chụp lược đồ 1 vẫn đọc được). `float` vẫn bị từ chối (ASM-018-04) |
| `from_plain` (sửa nhánh map) | khóa là dict có `__tuple__` → tuple; còn lại giữ nguyên |
| `build(inputs, params, sources=None, allocation=None, meta=None)` | thêm hai mục tùy chọn: `allocation = {"input": AllocationInput, "dept_center": {khoa: trung tâm}, "tolerance": "<chuỗi>"}` và `meta = {"run", "title", "fiscal_year", "costing_date", "parameter_set", "accounting_import", "price_category", "scope_services", "scope_departments", (+ "volume_scenario", "compliance_allocation_mode" khi có)}`. Không có thời điểm trong nội dung (để băm tất định); thời điểm khóa nằm ở NC Audit Event |
| `pack(snap) -> (bytes, str)` | `data = dumps(snap)`; trả `(gzip.compress(data, mtime=0), digest(data))` |
| `unpack(blob, expected_hash=None) -> dict` | giải nén, kiểm `digest` khi có `expected_hash` (khác → `ValueError("Ảnh chụp không còn nguyên vẹn: mã băm không khớp")`), `json.loads` |
| `recompute(snap) -> Recomputed` | Tính lại không đọc CSDL, **cùng thứ tự với `NCCostingRun._run` + `execute_costing`**: (1) `inputs` theo (dịch vụ, khoa); (2) có `allocation` thì `drivers[(s, d)] = allocation.service_drivers(inp, dept_center.get(d))`; (3) `runner.run(eligible, load, params, allocate=…)` với `allocate` gọi `allocation.allocate(rs, drivers, input)` và giữ `outcome`; (4) `allocation.mark_volume` từng kết quả; (5) `reconcile.reconcile(outcome.pools, float(tolerance), input.include_depreciation, reconcile.depreciation_centers(input.accounting, outcome.pools))`. Trả `Recomputed(results, recon_rows, warnings)`. Không có `allocation` → `recon_rows = []`, như `reproduce` |
| `reproduce(snap)` | giữ chữ ký, trả `recompute(snap).results` (test FEAT-036 không sửa) |
| `diff_rows(expected, actual, places=6) -> list[str]` | So hai danh sách bản ghi phẳng (mục 4.3). Khóa bản ghi: `("cost", dịch vụ, khoa)`, `("line", dịch vụ, khoa, idx)`, `("system", dịch vụ, khoa, idx)`, `("recon", trung tâm, loại)`. Số: `Decimal(str(x)).quantize(10^-places)`; chuỗi rỗng ≡ None; 0/1 ≡ False/True. Trả câu tiếng Việt cho mỗi khác biệt, ví dụ "DV-TEST-A · K01 dòng 2 · amount: 6000.0 ≠ 10000.0", "Thiếu dòng đối soát K01 · LABOR". Rỗng = trùng ở mọi trường |

### 3.2 `reconcile.py` (thêm một hàm, không đổi hàm cũ)
`depreciation_centers(accounting, pools) -> list[str]`: trung tâm có số kế toán DEPRECIATION khác 0 và nằm trong `pools`, sắp theo tên. Đây là đúng biểu thức `depr = [...]` hiện ở `execute_costing`; `execute_costing` đổi sang gọi hàm này để lần tính sống và `recompute` dùng chung một chỗ (ASM-018-05).

### 3.3 `compare.py` (mới, FR-COST-013)

Đầu vào là bản ghi phẳng của NC Service Cost (dict, cùng tên trường với DocType), để dùng chung cho dữ liệu đã lưu và cho test golden.

| Hàm / hằng | Làm gì |
| :-- | :-- |
| `COMPONENTS` | danh sách có thứ tự `(nhóm, trường, nhãn)`: Trực tiếp: `direct_labor` Nhân công, `direct_drug` Thuốc, `direct_supply` Vật tư, `direct_equipment` Thiết bị, `direct_infra` Hạ tầng, `direct_utility` Tiện ích (+ `eqa_cost` Ngoại kiểm khi trường tồn tại — FEAT-036); Phân bổ: `alloc_labor`, `alloc_drug_supply`, `alloc_depreciation`, `alloc_utility`, `alloc_management`; Giá: `accumulation` Tích lũy, `obligation` Nghĩa vụ tài chính, `calculated_price` Giá tính toán, `rounded_price` Giá làm tròn |
| `compare(base_rows, other_rows, fields=COMPONENTS) -> list[ServiceDiff]` | Ghép theo (dịch vụ, khoa), sắp theo khóa. Mỗi `ServiceDiff(service, department, presence ("both"/"base_only"/"other_only"), base_status, other_status, full_cost: Delta, components: tuple[ComponentDelta])`. `Delta(base, other, diff, pct)`: `diff = other − base` (Decimal, r2); `pct = r2(diff ÷ base × 100)` khi base ≠ 0, còn lại None. Một bên "Lỗi" hoặc không có (`full_cost` None) → số của bên đó None, `diff` None |
| `changed(d) -> bool` | `presence` ≠ "both", hoặc `full_cost.diff` ≠ 0, hoặc một cấu phần `diff` ≠ 0, hoặc trạng thái khác nhau |
| `summary(diffs) -> dict` | `{"services", "changed", "base_only", "other_only", "total_diff"}` (`total_diff` = Σ `full_cost.diff` khác None) |
| `input_changes(base_meta, other_meta) -> list[(nhãn, gốc, so sánh)]` | Khác nhau giữa đầu vào hai lần tính: Năm tài chính, Ngày tính giá, Bộ tham số, Lần nhập kế toán, Loại giá, Phạm vi khoa, Phạm vi dịch vụ (+ hai trường [1.1] khi có) |

Kiểm tra tổng: với `presence == "both"` và hai bên thành công, `Σ diff` của cấu phần Trực tiếp + Phân bổ = `full_cost.diff` (giá thành = trực tiếp + phân bổ, BR-COST-012). Test golden kiểm đẳng thức này.

### 3.4 Ánh xạ FR, mã, golden

| FR / NFR | Mã | Golden |
| :-- | :-- | :-- |
| FR-COST-011, NFR-REL-001 | `snapshot.build/pack/unpack/recompute/diff_rows` | `golden_engine.run()`: DV-TEST-A giá thành 287.745,46 trước và sau khi đổi đơn giá GANG |
| FR-COST-012 | controller `run_costing`, `validate`, `duplicate_run` | — |
| FR-COST-013 | `compare.compare` | `run()` vs `run(False)`: DV-TEST-A giá thành 287.745,46 → 224.109,10, chênh **−63.636,36**; Thiết bị 58.712,12 → 11.363,64 (−47.348,48); Hạ tầng 12.500,00 → 0 (−12.500,00); Phân bổ khấu hao 3.787,88 → 0 (−3.787,88); cấu phần khác 0. DV-TEST-B không đổi (88.169,70) |

Test lấy số từ `golden_engine` (import), không chép số; riêng −63.636,36 so thêm với `test-cases.md` TC-COST-18.

## 4. Lớp CSDL và controller

### 4.1 `loader.py`
- `capture_snapshot(run, eligible)` (FEAT-036, mở rộng): sau khi dựng `inputs`, `sources`, gọi `allocation_context(run, ctx)` trên cùng `ctx` và thêm `allocation = {"input": actx.input, "dept_center": actx.dept_center, "tolerance": repr(actx.tolerance)}`, `meta` (mục 3.1). Gọi `snapshot.build(..., allocation=…, meta=…)`.
- `eligible_from_results(run) -> list[dict]` (mới): dựng lại danh sách `eligible` của lần tính đã chạy từ NC Service Cost đã lưu (`technical_service`, `department`, `norm_set`; với dịch vụ có `test_system_costs` thì thêm `test_systems` = [(test_system, norm_set)] theo `idx`, đúng dạng `scope_info` của FEAT-036). Không gọi lại `scope_info`, vì phạm vi sống có thể đã đổi (bộ định mức mới khóa) (ASM-018-02).
- `stored_rows(run) -> list[dict]` (mới): đọc theo lô NC Service Cost của lần tính (mọi trường `writer` ghi), dòng con `lines` (và `test_system_costs` khi có) theo `idx`, NC Reconciliation Line (trường số, `over_tolerance`; **không** gồm `explanation`), thành bản ghi phẳng có khóa như mục 3.1.

### 4.2 `writer.py`
- Tách phần dựng giá trị khỏi phần ghi, **không đổi giá trị ghi**: `service_cost_values(run_name, r) -> (header: dict, lines: list[dict], systems: list[dict])` và `recon_values(run_name, row) -> dict`. `write_results`, `write_reconciliation` gọi hai hàm này rồi `insert` như cũ.
- `expected_rows(run_name, results, recon_rows) -> list[dict]` (mới): cùng dạng `loader.stored_rows`, dựng từ kết quả `snapshot.recompute` qua hai hàm trên. Vì cùng hàm dựng giá trị nên so sánh không lệch do ánh xạ trường.

### 4.3 `nc_costing_run.py`
- `run_costing`: thêm kiểm đầu tiên sau quyền: `status == "Đã khóa"` → `frappe.throw(_("Lần tính giá {0} đã khóa, không tính lại được. Dùng Nhân bản để tạo lần tính mới.").format(self.name))` (UC-012 8c, TC-COST-11). Các trạng thái khác giữ câu cũ.
- `lock_costing()` (mở rộng, giữ thứ tự kiểm cũ):
  1. quyền `write`; `status` ≠ "Đã tính" → câu cũ; `reconcile.lock_blockers` → câu cũ (test FEAT-017 không đổi);
  2. `eligible = loader.eligible_from_results(self)`; `snap = loader.capture_snapshot(self, eligible)`;
  3. `rec = snapshot.recompute(snap)`; `diffs = snapshot.diff_rows(writer.expected_rows(self.name, rec.results, rec.recon_rows), loader.stored_rows(self))`;
  4. `diffs` khác rỗng → từ chối, giữ "Đã tính": "Đầu vào đã thay đổi sau lần tính ({n} khác biệt, ví dụ: {3 dòng đầu}). Chạy tính giá lại rồi khóa." (ASM-018-02);
  5. `blob, h = snapshot.pack(snap)`; savepoint `nc_costing_lock`: tạo `File` (`file_name = f"{name}-anh-chup-v{VERSION}.json.gz"`, `content = blob`, `is_private = 1`, gắn như mục 2.1, `insert(ignore_permissions=True)`), `self.flags.audit_detail = f"Ảnh chụp {h[:12]}"`, `self.db_set({"snapshot_file": file.file_url, "snapshot_hash": h, "status": "Đã khóa"})` (hook `core/audit.py` ghi NC Audit Event "Khóa" kèm `detail`). Lỗi bất kỳ → rollback savepoint, `frappe.throw(_("Không lưu được ảnh chụp đầu vào; lần tính chưa khóa"))`;
  6. trả "Đã khóa".
- `verify_snapshot()` (mới, `@frappe.whitelist()`): quyền `read`; `status` ≠ "Đã khóa" hoặc không có `snapshot_file` → "Lần tính giá chưa khóa, chưa có ảnh chụp". Đọc nội dung tệp (`frappe.get_doc("File", {"file_url": …}).get_content()`), `snapshot.unpack(blob, self.snapshot_hash)` (lỗi mã băm → trả `ok: False` kèm câu lỗi, không raise), `recompute`, `diff_rows` với `stored_rows`. Trả `{"ok": bool, "version", "hash", "services": n, "lines": n, "recon_lines": n, "diffs": [≤ 50 câu], "diff_count": n}`. Chỉ đọc, không ghi gì (ASM-018-10).
- `duplicate_run()` (mới, `@frappe.whitelist()`): quyền `create` NC Costing Run và `read` bản gốc; `status == "Đang tính"` → từ chối "Lần tính giá đang tính, chưa nhân bản được". `new = frappe.copy_doc(self)` (theo `no_copy`) rồi đặt rõ: `title = _("{0} (bản sao)").format(self.title)`, `status = "Nháp"`, `progress = 0`, `snapshot_file = snapshot_hash = allocation_warnings = None` (+ `run_warnings` khi có), `based_on_run = None` nếu trường tồn tại. `new.insert()` (theo quyền người dùng, `validate` kiểm lần nhập kế toán "Đã chốt" như mọi bản mới). `new.add_comment("Comment", _("Nhân bản từ {0}").format(self.name))`. Trả `new.name` (ASM-018-07).

### 4.4 Hiệu năng
Khóa chạy đồng bộ trong request: nạp lại dữ liệu + tính lại + đọc kết quả đã lưu. Với 500 dịch vụ, pha tính của FEAT-017 đo 8,1 s; dự kiến khóa < 60 s. T05 đo trên bộ dữ liệu của `tests/test_costing_perf.py` (không thêm TC) và ghi vào implementation-log; > 120 s thì báo Lead trước khi đổi sang chạy nền (ASM-018-11).

## 5. API (`normcore/api/costing.py`, `@frappe.whitelist()`, kiểm quyền tường minh)

| Hàm | Tham số | Kết quả | Quyền, lỗi |
| :-- | :-- | :-- | :-- |
| `lock_run(run)` (đã có) | | `{"status", "snapshot_hash"}` | như cũ; thêm `snapshot_hash` vào kết quả. Lỗi của `lock_costing` trả nguyên văn |
| `verify_snapshot(run)` | tên lần tính | như `NCCostingRun.verify_snapshot` | `read` trên NC Costing Run |
| `duplicate_run(run)` | tên lần tính | `{"name"}` | `read` bản gốc + `create` NC Costing Run; NC Auditor, NC Director → PermissionError |
| `compare_runs(base_run, other_run, only_changed=0)` | hai tên | `{"base": meta, "other": meta, "input_changes": [[nhãn, gốc, so sánh]], "summary": {...}, "rows": [{"service", "service_name", "department", "presence", "base_status", "other_status", "full_cost": {base, other, diff, pct}, "components": [{"group", "field", "label", base, other, diff, pct}]}]}` | `read` trên **cả hai** lần tính. `base_run == other_run` → "Chọn hai lần tính giá khác nhau". Một lần không ở "Đã tính"/"Đã khóa" → "Lần tính giá {0} chưa có kết quả". Số trả `float` (r2) |
| `get_run_results` (đã có) | | thêm `snapshot_hash`, `can_duplicate` (quyền `create`), `can_verify` (status "Đã khóa" và có tệp) | không đổi |

Script Report "NC Costing Run Comparison" (nhãn "So sánh hai lần tính giá", `nc_costing/report/nc_costing_run_comparison/`) gọi cùng hàm dựng như `compare_runs` (mục 3.3); `roles` = NC Finance, NC Director, NC Admin, NC Auditor; `ref_doctype` = NC Costing Run. `execute(filters)` kiểm `read` trên hai lần tính như API.

## 6. Tiêu chí nghiệm thu

Lớp test: `unit` = `tests/unit/test_costing_snapshot_lock.py`, `test_costing_compare.py` (tệp mới); `golden` = `tests/golden/test_snapshot_compare_golden.py`; `site` = `nc_costing/doctype/nc_costing_run/test_nc_costing_run_lock.py` (tệp mới, dùng `costing_fixtures.make_golden_allocation` của FEAT-017); `api` = `api/test_costing_lock.py`.

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Trên site, dữ liệu vàng (DV-TEST-A, DV-TEST-B, phân bổ FEAT-017): tính → giải trình dòng DRUG_SUPPLY → `lock_costing()` = "Đã khóa"; `snapshot_file` là tệp private gắn lần tính, `snapshot_hash` 64 ký tự = `snapshot.digest` của nội dung đã giải nén; có NC Audit Event "Khóa" với `detail` chứa 12 ký tự đầu mã băm. Đổi `unit_price` của đơn giá GANG 3.000 → 5.000. `verify_snapshot()` → `ok` True, `diff_count` 0, `services` 2; `snapshot.recompute(unpack(tệp))` cho DV-TEST-A `direct_total` 183.963,06 và giá thành 287.745,46 (= `golden_engine.run()`), dòng L02 6.000,00; mọi trường NC Service Cost, dòng con, dòng đối soát đã lưu không đổi. Đối chứng: nhân bản rồi tính bản sao → L02 của bản sao 10.000,00 (đơn giá mới chỉ ảnh hưởng lần mới) | TC-COST-09 | FR-COST-011, NFR-REL-001 | site `test_TC_COST_09_tinh_lai_tu_anh_chup_trung_moi_truong` |
| 2 | Tính xong, đổi đơn giá GANG **trước** khi khóa → `lock_costing()` từ chối, câu có "Đầu vào đã thay đổi" và "L02"/`amount`; trạng thái giữ "Đã tính", không có `File` mới, `snapshot_hash` rỗng. Tính lại rồi khóa thì được | — | FR-COST-011 | site `test_khoa_tu_choi_khi_dau_vao_doi_sau_lan_tinh` |
| 3 | Sửa nội dung tệp ảnh chụp (ghi đè bằng ảnh chụp khác) → `verify_snapshot()` `ok` False, câu "mã băm không khớp"; không raise | — | NFR-REL-001 | site `test_kiem_tra_tai_lap_phat_hien_tep_bi_sua` |
| 4 | Lần tính "Đã khóa": `run_costing()` và `api.start_costing` → `ValidationError`, câu chứa "đã khóa, không tính lại được" và "Nhân bản"; không có NC Service Cost mới. `duplicate_run()` → bản mới ở "Nháp", `progress` 0, cùng `fiscal_year`, `costing_date`, `parameter_set`, `accounting_import`, `price_category`, phạm vi khoa và dịch vụ; `snapshot_file`, `snapshot_hash`, `allocation_warnings` rỗng; 0 NC Service Cost, 0 NC Reconciliation Line; có comment "Nhân bản từ …". Bản gốc giữ "Đã khóa", giữ ảnh chụp. Bản mới chạy `run_costing` được | TC-COST-11 | FR-COST-012 | site `test_TC_COST_11_da_khoa_tu_choi_tinh_nhan_ban_ra_nhap` |
| 5 | Lần tính "Đã khóa": `doc.title = "x"; doc.save()` → từ chối; `frappe.client.set_value(..., "snapshot_hash", "x")` → từ chối; `frappe.delete_doc` (Administrator) → từ chối. Chèn bản mới có `status` "Đã khóa" vẫn được (test cũ) | — | FR-COST-012 | site `test_ban_ghi_da_khoa_khong_sua_khong_xoa` |
| 6 | Hai lần tính trên site cùng dữ liệu vàng: lần gốc (loại giá có khấu hao) và V1 (loại giá `include_depreciation` = 0), cả hai "Đã tính". `compare_runs(gốc, V1)`: DV-TEST-A `full_cost.diff` = −63.636,36; cấu phần `direct_equipment` −47.348,48, `direct_infra` −12.500,00, `alloc_depreciation` −3.787,88, các cấu phần trực tiếp/phân bổ khác 0; Σ chênh lệch trực tiếp + phân bổ = −63.636,36; `input_changes` có dòng "Loại giá". DV-TEST-B `full_cost.diff` 0. Report "So sánh hai lần tính giá" trả cùng số, dòng cấu phần `indent` 1 dưới dòng dịch vụ | TC-COST-18 | FR-COST-013 | site `test_TC_COST_18_so_sanh_goc_voi_V1` + golden `test_TC_COST_18_chenh_lech_V1_theo_cau_phan` |
| 7 | Golden thuần: dựng bản ghi phẳng từ `engine` + `allocation` cho `run()` và `run(False)` (helper golden của FEAT-017), `compare.compare` cho DV-TEST-A −63.636,36 = giá thành V1 − giá thành gốc lấy từ kết quả `golden_engine.run(False)` và `run()`; `snapshot.recompute` của ảnh chụp dựng từ đầu vào vàng (có `allocation`) cho giá thành 287.745,46 / 88.169,70 và 4 dòng đối soát khớp `run()[1]`; `pack` hai lần cho cùng byte và cùng mã băm | TC-COST-09, 18 | FR-COST-011, 013 | golden `test_TC_COST_09_recompute_tu_anh_chup_vang`, `test_TC_COST_18_chenh_lech_V1_theo_cau_phan` |
| 8 | Đơn vị: khứ hồi map khóa tuple; khóa `str` cho cùng JSON như lược đồ 1; đọc ảnh chụp lược đồ 1 (không `allocation`) → `recon_rows` rỗng; phiên bản 3 → `ValueError`; `unpack` sai mã băm → `ValueError`; `diff_rows`: trùng → rỗng, khác số, thiếu/thừa bản ghi, "" ≡ None, sai số dưới `places`; `compare`: base_only, other_only, một bên "Lỗi", base 0 → `pct` None, `changed`, `summary`, `input_changes`; `reconcile.depreciation_centers` | — | FR-COST-011, 013 | `tests/unit/test_costing_snapshot_lock.py`, `test_costing_compare.py` |
| 9 | Quyền: NC Clinician → `verify_snapshot`, `duplicate_run`, `compare_runs` đều PermissionError; NC Auditor: `verify_snapshot`, `compare_runs`, report đọc được, `duplicate_run` và `lock_run` → PermissionError, tải được tệp ảnh chụp (`frappe.has_permission("File", doc=file)` True); NC Director: so sánh được, nhân bản → PermissionError | — | FR-ACC-002, FR-ACC-007 | api `test_quyen_khoa_nhan_ban_so_sanh_theo_vai_tro` |
| 10 | Test cũ xanh mà không sửa: `test_nc_costing_run.py`, `test_nc_costing_run_allocation.py` (gồm `lock_costing() == "Đã khóa"`), `api/test_costing.py`, `api/test_costing_reconciliation.py`, `test_costing_snapshot.py` (FEAT-036), `test_nc_costing_parameter_set.py`, `test_nc_audit_event.py` | — | — | lệnh T08 |
| 11 | Nếu FEAT-036 đã trên develop: chạy lại kịch bản TC-CLS-38 với **khóa thật** (tính GLU, giải trình nếu cần, `lock_costing`, sửa NC QC Plan và hồ sơ tuân thủ, `verify_snapshot` `ok` True) theo ASM-036-21 | (TC-CLS-38) | FR-COST-032 | site `test_TC_CLS_38_khoa_that_tai_lap_tu_anh_chup` (ASM-018-12) |

## 7. Test và độ phủ
- Đơn vị và golden phủ mọi nhánh mục 3; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90`.
- Site: tệp mới `test_nc_costing_run_lock.py`, `api/test_costing_lock.py`, `report/nc_costing_run_comparison/test_nc_costing_run_comparison.py`. Fixture V1: thêm hàm `costing_fixtures.make_price_category_no_depr()` (chỉ thêm hàm, không sửa hàm cũ).
- Test tĩnh giao diện mới `tests/unit/test_costing_lock_ui.py` (ui-design mục Kiểm).

## 8. Rủi ro
- **Trùng tệp với FEAT-036.** Cả hai sửa `snapshot.py`, `loader.py`, `nc_costing_run.py`, `nc_costing_run.js`, `writer.py`. Giảm bằng điều kiện bắt đầu ở đầu tài liệu (FEAT-036 đã trên develop) và quy tắc tránh conflict số 4.
- **Lệch giữa `_run` và `recompute`.** Hai đường tính phải đi cùng thứ tự. Giảm bằng: `recompute` dùng cùng hàm thuần (`runner.run`, `allocation.*`, `reconcile.*`, `depreciation_centers`), và bước khóa tự so `recompute` với kết quả đã lưu — lệch thì khóa từ chối, test #1, #10 đỏ ngay.
- **Khóa chậm với lần tính lớn** (mục 4.4).
- **Tệp đính kèm bị xóa tay** (người có quyền ghi lần tính có thể xóa File gắn kèm qua giao diện đính kèm). Không thêm hook vào `hooks.py` (tệp chung). `verify_snapshot` báo "Không tìm thấy tệp ảnh chụp" và mã băm vẫn ở bản ghi; NC Audit Event "Xóa" ghi lại việc xóa (ASM-018-10).
- **Trường số Float/Currency.** So khớp ở 6 chữ số thập phân sau `Decimal(str(float))`; Currency lưu 2 số, đơn giá 4, k 6 nên không mất chính xác.

## 9. Điểm cắm cho FEAT khác
- **FEAT-019 (xuất biểu):** đọc lần tính "Đã khóa"; có thể in `snapshot_hash` lên biểu.
- **FEAT-029 (kịch bản):** dùng `compare.compare` để so kịch bản với lần gốc; tạo kịch bản bằng nhân bản + `based_on_run`.
- **FEAT-037:** thêm đối soát vật chất vào ảnh chụp (tăng `VERSION`), và vào `stored_rows`/`expected_rows`.
