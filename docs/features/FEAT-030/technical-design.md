# FEAT-030 — Phương án giá, phê duyệt, lịch sử giá — Thiết kế kỹ thuật

Issue NORM-84. Bản phát hành R3. Phụ thuộc FEAT-028 (có `DONE` trên `develop`); dùng lại FEAT-019 (khung xuất, DONE), FEAT-011 (NC Price Category, hai loại mẫu `install.SAMPLE_PRICE_CATEGORIES`), FEAT-018 (khóa lần tính).

Nguồn: `srs.md` FR-PRICE-001..010, FR-OUT-007, FR-NOTI-001, 003, FR-ACC-003, 007, TBD-05; `use-cases.md` UC-015, UC-016 (bảng so sánh giá); `data-model.md` 3 (NC Price Proposal, NC Price Proposal Item, NC Proposal Dept Confirmation, NC Service Price History, NC Technical Service `approved_prices`, NC Price Category `approval_authority`), mục 4 dòng "Gợi ý, kịch bản, phương án giá", 5.3, DI-07; `architecture.md` ADR-011; `ux-foundations.md` SCR-DSK-027; `design.md` mục 3; As-Built FEAT-019, FEAT-028.

**Golden.** Giá đề xuất mặc định = `rounded_price` của NC Service Cost do bộ máy tính (golden DV-TEST-A 302.100, DV-TEST-B 92.600; giá thành toàn bộ DV-TEST-A 287.745,46). FEAT này không có công thức tiền mới: chỉ chép, so sánh (`<`) và ghi giá. Trung vị tham chiếu tính bằng `benchmark/stats.py` của FEAT-028.

Giả định: `docs/decisions/assumptions/FEAT-030.md` (ASM-030-01..16). Không có CF, AMD: mọi trường dùng đúng `data-model.md`.

## 1. Phạm vi

| FR | Làm | Ghi chú |
| :-- | :-- | :-- |
| FR-PRICE-001 | Đủ với nguồn lần tính "Đã khóa" | Mỗi NC Service Cost `calc_status ≠ Lỗi` một dòng: `full_cost`, `calculated_price`, `rounded_price`, `benchmark_median`, `benchmark_count`, `proposed_price = rounded_price`. Kịch bản điều chỉnh (FEAT-029, chưa DONE): chưa làm, xem ASM-030-01 |
| FR-PRICE-002 | Đủ | `proposed_price ≠ rounded_price` mà `adjustment_basis` rỗng → chặn "Gửi duyệt", nêu mã dịch vụ |
| FR-PRICE-003 | Đủ | `below_cost = proposed_price < full_cost` (máy chủ đặt); Giám đốc phê duyệt phải tích `director_ack` từng dòng `below_cost` |
| FR-PRICE-004 | Đủ | Gửi duyệt → "Chờ khoa xác nhận", sinh một dòng NC Proposal Dept Confirmation cho mỗi khoa có dòng; thông báo `head_user` của từng khoa |
| FR-PRICE-005 | Đủ | Mọi dòng xác nhận có `confirmed_by` → "Chờ phê duyệt", thông báo người có vai NC Director |
| FR-PRICE-006 | Đủ | Loại giá "Bệnh viện": "Đã duyệt", ghi NC Service Price History (`proposed_price`, `apply_from`) vào từng dịch vụ |
| FR-PRICE-007 | Đủ | Loại giá "Cơ quan có thẩm quyền": "Đã duyệt nội bộ, chờ trình", chưa ghi lịch sử giá |
| FR-PRICE-008 | Đủ | "Ghi kết quả phê duyệt": số, ngày văn bản, `authority_price` từng dòng → "Đã được cấp thẩm quyền duyệt", ghi lịch sử giá bằng `authority_price` kèm `authority_doc_no` |
| FR-PRICE-009 | Đủ | Từ chối ở "Chờ khoa xác nhận" (trưởng khoa của khoa có dòng) hoặc "Chờ phê duyệt" (Giám đốc): bắt buộc lý do, về "Nháp", thông báo người lập |
| FR-PRICE-010 | Đủ | Lịch sử chỉ thêm dòng, không sửa, không xóa; giá cũ giữ nguyên |
| FR-OUT-007 | Đủ | Bảng so sánh giá Excel (đơn vị, giá, ngày hiệu lực, nguồn, thống kê) qua khung FEAT-019; từ lần tính đã khóa (hộp thoại SCR-DSK-028) và từ phương án giá |

Ngoài phạm vi: lập phương án từ kịch bản điều chỉnh (FEAT-029); đưa bảng so sánh giá vào hồ sơ nén (ASM-030-14); trích bảng giá cho HIS (FEAT-027 phần R3 khác).

## 2. DocType

Ba DocType cha/con mới ở module **NC Benchmark** (`normcore/nc_benchmark/doctype/`), một bảng con mới ở module **NC Procedure** (cùng chỗ NC Technical Service và NC Service Department). Trường đúng `data-model.md`; chỉ thêm thuộc tính hiển thị (`read_only`, `in_list_view`, `depends_on`) và một Section/HTML hiển thị (không phải trường dữ liệu).

### 2.1 NC Price Proposal (mới)

Naming `PAG-.YYYY.-.###`. `track_changes = 1`. Có Frappe Workflow "NC Price Proposal" (mục 2.6).

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| `title` | Tên phương án | Data | Có | Mặc định `"Phương án giá " + run.title` |
| `costing_run` | Lần tính giá hoặc kịch bản | Link NC Costing Run | Có | Chỉ đặt khi tạo; `set_only_once = 1`; validate `status = "Đã khóa"` |
| `price_category` | Loại giá | Link NC Price Category | Có | Lấy từ `costing_run.price_category`, `read_only = 1` (ASM-030-02) |
| `approval_authority` | Cấp phê duyệt | Data, `fetch_from: price_category.approval_authority`, `read_only` | | Chỉ hiển thị (trường fetch, không phải dữ liệu mới); máy chủ luôn đọc lại từ NC Price Category |
| `apply_from` | Ngày áp dụng | Date | | BB khi "Gửi duyệt" nếu loại giá "Bệnh viện" (ASM-030-05) |
| `workflow_state` | Trạng thái | Link Workflow State | | `read_only`, `in_list_view`, `in_standard_filter` |
| `items` | Dòng | Table NC Price Proposal Item | | |
| `department_confirmations` | Xác nhận của khoa | Table NC Proposal Dept Confirmation | | `read_only`; máy chủ ghi |
| `authority_doc_no` | Số văn bản phê duyệt | Data | | `depends_on` trạng thái "Đã duyệt nội bộ, chờ trình" hoặc sau; `read_only` (ghi qua API) |
| `authority_doc_date` | Ngày văn bản phê duyệt | Date | | như trên |

### 2.2 NC Price Proposal Item (bảng con, mới)

| Trường | Nhãn | Kiểu | Ghi chú |
| :-- | :-- | :-- | :-- |
| `technical_service` | Dịch vụ | Link NC Technical Service, BB | `read_only`, `in_list_view` |
| `department` | Khoa | Link NC Department | `read_only`, `in_list_view`; từ NC Service Cost |
| `full_cost` | Giá thành toàn bộ | Currency | `read_only` |
| `calculated_price` | Giá tính toán | Currency | `read_only` |
| `rounded_price` | Giá làm tròn | Currency | `read_only`, `in_list_view` |
| `benchmark_median` | Trung vị tham chiếu | Currency | `read_only`; trống khi chưa đủ dữ liệu |
| `benchmark_count` | Số đơn vị tham chiếu | Int | `read_only` |
| `proposed_price` | Giá đề xuất | Currency, BB | `in_list_view`; sửa được ở "Nháp" (NC Finance) |
| `adjustment_basis` | Căn cứ điều chỉnh | Small Text | `in_list_view`; BB khi `proposed_price ≠ rounded_price` (kiểm ở Gửi duyệt, ASM-030-04) |
| `below_cost` | Dưới giá thành | Check | `read_only`; máy chủ đặt |
| `director_ack` | Giám đốc xác nhận dòng dưới giá thành | Check | `read_only` trên form; đặt qua API Phê duyệt |
| `authority_price` | Giá cấp thẩm quyền duyệt | Currency | `read_only`; ghi qua API "Ghi kết quả phê duyệt" |

### 2.3 NC Proposal Dept Confirmation (bảng con, mới)

`department` (Link NC Department), `confirmed_by` (Link User), `confirmed_on` (Datetime), `note` (Small Text). Mọi trường `read_only`; máy chủ ghi.

### 2.4 NC Service Price History (bảng con, mới, module NC Procedure) và NC Technical Service (mở rộng)

NC Service Price History: `price_category` (Link NC Price Category, BB), `price` (Currency, BB), `effective_date` (Date, BB), `price_proposal` (Link NC Price Proposal, BB), `authority_doc_no` (Data). Mọi trường `read_only`.

NC Technical Service: thêm `approved_prices` (Table NC Service Price History, `read_only = 1`, nhãn "Giá đã duyệt") trong section mới "Giá đã duyệt" cuối form. Trường mới, không đổi dữ liệu cũ: không cần patch (ASM-030-15). Dòng chỉ thêm bằng `price_proposal.write_price_history` (mục 3.2) với `ignore_permissions` và cờ `doc.flags.price_history_write = True`; controller NC Technical Service chặn thêm/sửa/xóa dòng `approved_prices` khi không có cờ (so sánh với bản đã lưu) — DI-07, FR-PRICE-010.

### 2.5 Controller `nc_price_proposal.py`

- `before_insert`/`validate`: `costing_run.status = "Đã khóa"` (ngược lại "Chỉ lập phương án từ lần tính giá đã khóa"); `price_category = costing_run.price_category`; mỗi dòng `below_cost = proposal.is_below_cost(proposed_price, full_cost)`; `proposed_price` > 0.
- Trạng thái ≠ "Nháp": mọi thay đổi trường dữ liệu (dòng, ngày áp dụng, loại giá, tên) bị chặn "Phương án đang duyệt hoặc đã duyệt, không sửa được" trừ khi `self.flags.proposal_action` (do API đặt) — DI-07.
- Đổi `workflow_state` chỉ khi `self.flags.proposal_action` (ngăn chuyển trạng thái bằng Desk), như mẫu FEAT-007 (`apply_action`).
- `on_trash`: chỉ xóa được ở "Nháp" (DocPerm delete chỉ NC Finance).
- Ghi NC Audit Event "Chuyển trạng thái" qua cơ chế sẵn có (`flags.workflow_action`, `audit_detail`) như quy trình.

### 2.6 Frappe Workflow "NC Price Proposal" (ADR-011, data-model 5.3)

Trạng thái (Workflow State): `Nháp` (đã có), `Chờ khoa xác nhận`, `Chờ phê duyệt`, `Đã duyệt`, `Đã duyệt nội bộ, chờ trình`, `Đã được cấp thẩm quyền duyệt`. Hành động (Workflow Action Master): `Gửi duyệt`, `Từ chối` (đã có), `Xác nhận`, `Phê duyệt`, `Ghi kết quả phê duyệt`.

| Từ | Hành động | Đến | Vai trò (`allowed`) | Điều kiện (kiểm ở API, mục 3.3) |
| :-- | :-- | :-- | :-- | :-- |
| Nháp | Gửi duyệt | Chờ khoa xác nhận | NC Finance | `submit_errors` rỗng |
| Chờ khoa xác nhận | Xác nhận | Chờ khoa xác nhận | NC Department Head | còn khoa chưa xác nhận |
| Chờ khoa xác nhận | Xác nhận | Chờ phê duyệt | NC Department Head | mọi khoa đã xác nhận |
| Chờ khoa xác nhận | Từ chối | Nháp | NC Department Head | có lý do |
| Chờ phê duyệt | Phê duyệt | Đã duyệt | NC Director | "Bệnh viện"; mọi dòng `below_cost` có `director_ack` |
| Chờ phê duyệt | Phê duyệt | Đã duyệt nội bộ, chờ trình | NC Director | "Cơ quan có thẩm quyền"; mọi dòng `below_cost` có `director_ack` (ASM-030-07) |
| Chờ phê duyệt | Từ chối | Nháp | NC Director | có lý do |
| Đã duyệt nội bộ, chờ trình | Ghi kết quả phê duyệt | Đã được cấp thẩm quyền duyệt | NC Finance | có số, ngày văn bản, giá được duyệt mọi dòng |

`allow_edit` của Workflow Document State: `Nháp` → NC Finance; các trạng thái khác → NC Finance (doc_status 0) nhưng controller chặn sửa (2.5). Không trạng thái nào cho NC Auditor (kiểm `read_only_violations`).

Cài đặt (ASM-030-03): dữ liệu luồng ở `normcore/benchmark/proposal.py` (`STATES`, `TRANSITIONS`); hàm `normcore.benchmark.proposal_setup.ensure_workflow()` tạo/cập nhật idempotent Workflow State, Workflow Action Master, Workflow "NC Price Proposal" từ dữ liệu đó; đăng ký `after_install` và `after_migrate` ở `normcore/hook_registry/FEAT-030.json`. Không sửa `hooks.py`, `fixtures/workflow*.json`. Test so khớp Workflow trên site với `TRANSITIONS`.

### 2.7 Quyền (data-model mục 4, dòng "Gợi ý, kịch bản, phương án giá")

| Vai trò | DocPerm NC Price Proposal | Phạm vi / thao tác A |
| :-- | :-- | :-- |
| NC Finance | read, write, create, delete, report, export, print | mọi phương án; Gửi duyệt, Ghi kết quả phê duyệt |
| NC Department Head | read, report, print | chỉ phương án có ít nhất một dòng thuộc khoa được gán; A = Xác nhận/Từ chối phần khoa mình |
| NC Director | read, report, print | mọi phương án; A = Phê duyệt/Từ chối |
| NC Consultant, NC Admin, NC Auditor | read | NC Auditor chỉ đọc |
| Các vai khác | không | |

Bảng con theo DocType cha. NC Service Price History theo NC Technical Service (mọi vai đọc; ghi chỉ máy chủ).

- `scripts/conventions/perm_matrix/nc_price_proposal.json`: `{"doctype": "NC Price Proposal", "row": "Gợi ý, kịch bản, phương án giá", "codes": "- R - W - - R R R R", "delete": ["NC Finance"]}`.
- Phạm vi khoa (ASM-030-06): `normcore/core/scope_rules/nc_price_proposal.json` `{"doctype": "NC Price Proposal", "department_field": "department", "public_read": {}, "child": ["NC Price Proposal Item", "department"]}`. Mở rộng tương thích ngược ở `core/scope_registry.py` (đọc khóa `child`) và `core/permissions.py` (`ScopeRule.child`; `_doc_departments` trả tập khoa của các dòng con; đọc được khi giao với khoa được gán; điều kiện SQL `` `tabNC Price Proposal`.name in (select parent from `tabNC Price Proposal Item` where parenttype='NC Price Proposal' and department in (…)) ``). Rule không có `child` chạy y như cũ. Thêm `"NC Price Proposal"` vào `SCOPED` của `tests/unit/test_scope_registry.py` theo tiền lệ ASM-028-12 (assertion vẫn so tập đầy đủ).
- `normcore/core/delete_guard/`: không thêm (phương án chỉ xóa ở Nháp do controller).

## 3. Thành phần

### 3.1 `normcore/benchmark/proposal.py` (thuần, không import frappe)

| Hàm / hằng | Vào → Ra | FR |
| :-- | :-- | :-- |
| `DRAFT, WAIT_DEPT, WAIT_DIRECTOR, APPROVED, WAIT_AUTHORITY, AUTHORITY_APPROVED`; `STATES`; `TRANSITIONS` (bảng 2.6, mỗi dòng `(từ, hành động, đến, vai)`); `LOCKED_STATES = (APPROVED, WAIT_AUTHORITY, AUTHORITY_APPROVED)`; `PENDING_STATES = (WAIT_DEPT, WAIT_DIRECTOR)` | | 5.3 |
| `HOSPITAL = "Bệnh viện"`, `AUTHORITY = "Cơ quan có thẩm quyền"` | | TBD-05 |
| `is_below_cost(proposed, full_cost)` | Decimal → bool (`proposed < full_cost`; thiếu `full_cost` → False) | FR-PRICE-003 |
| `build_items(costs, bench)` | `costs`: list dict NC Service Cost (`technical_service`, `department`, `full_cost`, `calculated_price`, `rounded_price`, `calc_status`); `bench`: `{service: (median, count)}` → list dict dòng, bỏ `calc_status = "Lỗi"`, `proposed_price = rounded_price`, `below_cost`, thứ tự theo `technical_service` | FR-PRICE-001 |
| `needs_basis(item)` | `proposed_price != rounded_price` (so `Decimal`) | FR-PRICE-002 |
| `submit_errors(items, approval_authority, apply_from)` | list chuỗi lỗi: không có dòng; dòng `needs_basis` mà `adjustment_basis.strip()` rỗng ("Dòng {mã}: giá đề xuất khác giá làm tròn, cần ghi căn cứ điều chỉnh"); `proposed_price` ≤ 0; "Bệnh viện" mà thiếu `apply_from` | FR-PRICE-002, ASM-030-05 |
| `departments(items)` | tập khoa khác rỗng, sắp tên | FR-PRICE-004 |
| `confirm(confirmations, depts, user, now)` | đặt `confirmed_by/on` cho dòng có `department ∈ depts` chưa xác nhận → `(số dòng đã đặt, all_confirmed)`; không đặt được dòng nào → `ValueError` | FR-PRICE-004, 005 |
| `approve_errors(items, acknowledged)` | đặt `director_ack` cho dòng có `name ∈ acknowledged`; trả lỗi "Dòng {mã}: giá đề xuất {p} thấp hơn giá thành toàn bộ {c}, Giám đốc cần xác nhận riêng dòng này" cho mỗi dòng `below_cost` chưa `director_ack` | FR-PRICE-003 |
| `approved_state(approval_authority)` | HOSPITAL → APPROVED; AUTHORITY → WAIT_AUTHORITY; khác → `ValueError` | FR-PRICE-006, 007 |
| `history_rows(items, price_category, effective_date, proposal, authority_doc_no=None, use_authority=False)` | list dict NC Service Price History, giá = `authority_price` nếu `use_authority` ngược lại `proposed_price` | FR-PRICE-006, 008, 010 |
| `history_conflicts(existing, new)` | các cặp trùng (`technical_service`, `price_category`, `effective_date`) giữa lịch sử đã có và dòng mới (ASM-030-09) | FR-PRICE-010 |
| `authority_errors(items, prices, doc_no, doc_date)` | thiếu số/ngày văn bản; dòng không có giá được duyệt hoặc giá ≤ 0 | FR-PRICE-008 |
| `reset_for_draft(items, confirmations)` | bỏ `director_ack` mọi dòng, xóa bảng xác nhận (trả danh sách rỗng) | FR-PRICE-009, ASM-030-08 |

### 3.2 API `normcore/api/price_proposal.py` (mới)

Kiểm quyền tường minh trong từng hàm; lỗi `frappe.throw` tiếng Việt; không quyền → `frappe.PermissionError`. Ghi bằng `ignore_permissions` sau khi đã kiểm, đặt `doc.flags.proposal_action = action`.

| Hàm (whitelisted) | Tham số | Kết quả | Kiểm |
| :-- | :-- | :-- | :-- |
| `create_proposal(costing_run, title=None, apply_from=None)` | | `{name}` | quyền `create` NC Price Proposal (NC Finance); lần tính "Đã khóa"; có ít nhất một dịch vụ không lỗi |
| `get_proposal(proposal)` | | `{doc, items (kèm service_name, needs_basis), confirmations (kèm tên khoa, tên người), approval_authority, actions: [hành động người gọi làm được], my_departments: [khoa chưa xác nhận người gọi xác nhận được], summary: {count, adjusted, below_cost, unacked}}` | `has_permission(read)` |
| `apply_action(proposal, action, reason=None, acknowledged=None, department=None, note=None)` | `acknowledged`: JSON list tên dòng; `department`, `note` (ghi vào dòng xác nhận): tùy chọn | `{workflow_state}` | xem bảng dưới |
| `record_authority_result(proposal, authority_doc_no, authority_doc_date, prices, apply_from=None)` | `prices`: JSON `{tên dòng: giá}` | `{workflow_state}` | NC Finance có quyền write; trạng thái "Đã duyệt nội bộ, chờ trình" |
| `export_price_comparison(proposal)` | | tệp xlsx | xem 3.4 |
| `pending_for(user)` (không whitelisted) | | việc chờ theo hợp đồng `core/notify.py` | FR-NOTI-003; đăng ký `normcore_pending_sources` ở `hook_registry/FEAT-030.json` |

`create_proposal` (FR-PRICE-001): đọc NC Service Cost của lần tính (`frappe.get_all`, đã kiểm quyền create của người gọi; NC Finance đọc được kết quả); `bench` lấy bằng hàm mới `price_compare.benchmark_summary(run_doc, costs)` (không whitelisted) = `comparable_prices_bulk` + `_stats_for` với bộ lọc rỗng, `use_adjusted=False`, trả `{service: (median nếu sufficient, count)}` — mở rộng FEAT-028, không viết lại (`get_comparison` không đổi). `proposal.build_items` → insert.

`apply_action` theo hành động (`_actor_error` như mẫu `procedure_workflow`):

| Hành động | Trạng thái nguồn | Người làm | Việc |
| :-- | :-- | :-- | :-- |
| Gửi duyệt | Nháp | NC Finance có write | `submit_errors` khác rỗng → `frappe.throw("<br>".join(errors), title="Chưa gửi duyệt được")`; tạo bảng xác nhận theo `departments(items)`; → "Chờ khoa xác nhận"; thông báo `NC Department.head_user` của từng khoa (FR-PRICE-004) |
| Xác nhận | Chờ khoa xác nhận | NC Department Head, khoa (hoặc `department`) thuộc khoa được gán và có dòng chưa xác nhận | `proposal.confirm`; còn khoa chưa xác nhận → giữ trạng thái, ghi comment "Xác nhận: {khoa}"; đủ → "Chờ phê duyệt", thông báo mọi người có vai NC Director (FR-PRICE-005) |
| Phê duyệt | Chờ phê duyệt | NC Director | `approve_errors(items, acknowledged)` khác rỗng → throw (không lưu `director_ack` lẻ, ASM-030-07); `approved_state(price_category.approval_authority)`; "Bệnh viện": `write_price_history(doc, use_authority=False)` (FR-PRICE-006, 010); thông báo người lập |
| Từ chối | Chờ khoa xác nhận (trưởng khoa của khoa có dòng) / Chờ phê duyệt (NC Director) | | lý do rỗng → "Cần nhập lý do từ chối"; `reset_for_draft`; → "Nháp"; comment "Từ chối ở cấp {khoa/giám đốc}: lý do"; thông báo `doc.owner` (người lập, NC Finance) với tiêu đề "{name}: bị từ chối ở cấp {cấp} — {lý do}" (FR-PRICE-009) |

`record_authority_result` (FR-PRICE-008): `authority_errors` → throw; đặt `authority_doc_no`, `authority_doc_date`, `authority_price` từng dòng; `apply_from = apply_from or doc.apply_from or authority_doc_date`; → "Đã được cấp thẩm quyền duyệt"; `write_price_history(doc, use_authority=True)`; `proposed_price` giữ nguyên (giá đã trình nằm cạnh giá được duyệt).

`write_price_history(doc, use_authority)` (không whitelisted): `history_rows`; `history_conflicts` với `approved_prices` hiện có của các dịch vụ → throw nêu dịch vụ, loại giá, ngày, phương án cũ (ASM-030-09) **trước** khi đổi trạng thái (một giao dịch); thêm dòng vào từng NC Technical Service (`flags.price_history_write`, `ignore_permissions`). Không xóa, không sửa dòng cũ (TC-PRICE-05).

Mọi chuyển trạng thái: `doc.workflow_state = new`, `flags.proposal_action`, `flags.workflow_action`, `flags.audit_detail = reason`, `save(ignore_permissions=True)`, `add_comment("Workflow", …)`; thông báo qua `core.notify.notify`.

### 3.3 Thông báo (FR-NOTI-001, 003)

| Sự kiện | Người nhận | Tiêu đề |
| :-- | :-- | :-- |
| Gửi duyệt | `head_user` mỗi khoa trong phương án | "{name}: chờ khoa xác nhận" |
| Đủ khoa | người dùng bật có vai NC Director | "{name}: chờ phê duyệt" |
| Phê duyệt | người lập | "{name}: đã duyệt" / "{name}: đã duyệt nội bộ, chờ trình" |
| Từ chối | người lập | "{name}: bị từ chối ở cấp {trưởng khoa|giám đốc} — {lý do}" |

`pending_for(user)`: trưởng khoa — phương án "Chờ khoa xác nhận" còn khoa của họ chưa xác nhận; Giám đốc — "Chờ phê duyệt"; NC Finance — "Đã duyệt nội bộ, chờ trình".

### 3.4 Bảng so sánh giá (FR-OUT-007)

`normcore/exports/price_comparison.py` (thuần, openpyxl, cùng kiểu `annex.py`): `build_workbook(data, meta) -> bytes`.

- Trang "Tổng hợp": Mã DV · Tên DV · Khoa · Giá tính toán · Giá làm tròn · [Giá đề xuất — chỉ khi nguồn là phương án] · Số đơn vị · Thấp nhất · Trung vị · Cao nhất · Độ lệch % · Ghi chú ("Chưa đủ dữ liệu so sánh").
- Trang "Giá tham chiếu": Mã DV · Tên DV · Đơn vị tham chiếu · Tỉnh/thành phố · Hạng · Loại hình · Loại giá · Giá · Ngày hiệu lực · Nguồn (`source_doc_no`; trống thì `source_url`).
- Trang thông tin + chân trang theo `exports/meta.py` (mã lần tính, bộ tham số, thời điểm, người xuất; nguồn phương án khi có).
- Dữ liệu = đúng tập giá FEAT-028 chọn (`_stats_for`, bộ lọc rỗng, giá gốc); tiền định dạng như `annex.py`.

Điểm vào:
1. Hộp thoại SCR-DSK-028 (lần tính "Đã khóa"): thêm `"price_comparison": ("Bảng so sánh giá", "so-sanh-gia-{run}.xlsx", None)` vào `api/export.py::FILE_TYPES` và một nhánh trong `export_file` gọi `price_proposal.comparison_data(run_doc)` + `price_comparison.build_workbook`; `export_dialog.js` thêm dòng vào khối Phụ lục. Quyền: quyền đọc lần tính (ASM-019-04).
2. Form phương án giá: `export_price_comparison(proposal)` — quyền đọc phương án; Trưởng khoa chỉ thấy dòng khoa mình (ASM-030-13).

Cả hai ghi `audit.log_export` ("Xuất tệp") như FEAT-019. Không đưa vào hồ sơ nén (ASM-030-14).

### 3.5 Giao diện

Form NC Price Proposal (SCR-DSK-027), nút "Tạo phương án giá" trên form NC Costing Run "Đã khóa", section "Giá đã duyệt" trên NC Technical Service. Chi tiết: `ui-design.md`.

## 4. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Từ lần tính vàng "Đã khóa": 2 dòng; `proposed_price` 302.100 (DV-TEST-A) và 92.600 (DV-TEST-B) = `rounded_price`; `full_cost` DV-TEST-A 287.745,46; `benchmark_count` khớp `get_comparison`; lần tính chưa khóa bị từ chối | TC-PRICE-01 | FR-PRICE-001 | `normcore/api/test_price_proposal.py::test_TC_PRICE_01_lap_tu_lan_tinh_khoa`; `tests/unit/test_price_proposal_logic.py::test_FR_PRICE_001_build_items` |
| 2 | Sửa DV-TEST-A thành 295.000, căn cứ trống, Gửi duyệt → lỗi chứa "DV-TEST-A" và "căn cứ", trạng thái vẫn "Nháp"; ghi căn cứ → gửi được | TC-PRICE-02 | FR-PRICE-002 | `test_price_proposal.py::test_TC_PRICE_02_thieu_can_cu_tu_choi_gui` |
| 3 | DV-TEST-A 280.000 (< 287.745,46): `below_cost = 1`; Giám đốc Phê duyệt không `acknowledged` → lỗi, trạng thái "Chờ phê duyệt"; `acknowledged=[dòng A]` → duyệt | TC-PRICE-03 | FR-PRICE-003 | `test_price_proposal.py::test_TC_PRICE_03_duoi_gia_thanh_can_xac_nhan_dong` |
| 4 | Dòng của KHOA-TEST và KHOA-TEST-2: sau trưởng khoa thứ nhất xác nhận vẫn "Chờ khoa xác nhận" (một dòng xác nhận có `confirmed_by`); sau khoa thứ hai "Chờ phê duyệt"; Giám đốc nhận thông báo; trưởng khoa khác khoa bị PermissionError | TC-PRICE-04 | FR-PRICE-004, 005 | `test_price_proposal.py::test_TC_PRICE_04_hai_khoa_xac_nhan_lan_luot` |
| 5 | Loại giá "Bệnh viện", `apply_from` 01/01/2027: "Đã duyệt"; sửa dòng bị chặn; NC Technical Service DV-TEST-A có dòng lịch sử mới (302.100, 2027-01-01, phương án) và dòng lịch sử cũ (dựng trước, ngày cũ) còn nguyên | TC-PRICE-05 | FR-PRICE-006, 010 | `test_price_proposal.py::test_TC_PRICE_05_duyet_ghi_lich_su_gia` |
| 6 | Loại giá "Cơ quan có thẩm quyền": Phê duyệt → "Đã duyệt nội bộ, chờ trình", chưa có lịch sử; Ghi kết quả (số, ngày, giá) → "Đã được cấp thẩm quyền duyệt", `authority_price` cạnh `proposed_price`, lịch sử dùng `authority_price` và `authority_doc_no` | TC-PRICE-06 | FR-PRICE-007, 008 | `test_price_proposal.py::test_TC_PRICE_06_cap_tham_quyen_ghi_ket_qua` |
| 7 | Trưởng khoa Từ chối không lý do → lỗi; có lý do → "Nháp", bảng xác nhận rỗng, người lập (NC Finance) có Notification Log chứa lý do | TC-PRICE-07 | FR-PRICE-009 | `test_price_proposal.py::test_TC_PRICE_07_tu_choi_ve_nhap_bao_tai_chinh` |
| 8 | Xuất bảng so sánh giá: xlsx có trang "Tổng hợp" (thống kê count/min/median/max/độ lệch) và "Giá tham chiếu" (đơn vị, giá, ngày hiệu lực, nguồn); có trang thông tin; ghi NC Audit Event "Xuất tệp" | TC-OUT-05 | FR-OUT-007 | `normcore/api/test_price_proposal.py::test_TC_OUT_05_xuat_bang_so_sanh_gia`; `tests/unit/test_exports_price_comparison.py` |
| 9 | Hàm thuần 3.1: mỗi hàm có test nhánh đúng/sai; `proposal.py` phủ ≥ 90% | — | FR-PRICE-001..010 | `tests/unit/test_price_proposal_logic.py` |
| 10 | Quyền: NC Clinician không đọc; NC Auditor đọc, không tạo/sửa/hành động; Trưởng khoa chỉ thấy phương án có khoa mình; NC Consultant chỉ đọc; Gửi duyệt bởi Director bị từ chối; sửa `workflow_state` qua `save()` bị chặn | — | FR-ACC-003, 007 | `normcore/nc_benchmark/doctype/nc_price_proposal/test_nc_price_proposal.py::test_quyen_*`, `test_sua_ngoai_api_bi_chan` |
| 11 | Lịch sử giá: thêm/sửa/xóa dòng `approved_prices` bằng `save()` của NC Technical Service bị chặn; trùng (dịch vụ, loại giá, ngày) bị chặn | — | FR-PRICE-010 | `test_price_proposal.py::test_FR_PRICE_010_lich_su_chi_them` |
| 12 | Workflow trên site khớp `proposal.TRANSITIONS`; `read_only_violations()` rỗng | — | ADR-011, FR-ACC-007 | `test_nc_price_proposal.py::test_workflow_khop_transitions` |
| 13 | Phạm vi `child` không đổi hành vi rule cũ (test scope cũ xanh) | — | FR-ACC-003 | `tests/unit/test_scope_registry.py`, `normcore/tests/test_scope_child.py` |
| 14 | Giao diện: form JS dùng `__()`, có bản dịch | — | SCR-DSK-027 | `tests/unit/test_feat_030_ui.py` |

## 5. Giả định và rủi ro

Giả định ASM-030-01..16 ở `docs/decisions/assumptions/FEAT-030.md`.

Rủi ro:
- Mở rộng `core/permissions.py` (khóa `child`) là tệp dùng chung: thay đổi phải tương thích ngược, chạy lại toàn bộ test phạm vi.
- `export.py`, `export_dialog.js` (FEAT-019) bị chạm thêm một loại tệp: test FEAT-019 không được sửa; nếu có test đếm số loại tệp thì báo BA trước khi đổi.
- Workflow cài bằng mã (ASM-030-03) thay vì fixture: bệnh viện đổi tên trạng thái trên Desk sẽ bị `after_migrate` ghi đè các transition gốc; ghi vào As-Built.
- Trung vị tham chiếu chụp lúc lập phương án; giá tham chiếu xác nhận sau đó không tự cập nhật (ASM-030-10).
