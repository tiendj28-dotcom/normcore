# FEAT-019: Xuất biểu Thông tư 21, bảng giải trình, bộ định mức (thiết kế kỹ thuật)

Issue NORM-48. Nguồn:
- `srs.md`: FR-OUT-001, 002, 003 (Should), 004, 005, 006, 008, 009 (Could); FR-AUD-004 (Should); NFR-CPL-002. Liên quan: FR-OUT-011 (đã làm ở FEAT-034), FR-COST-010 (dòng giải trình).
- `use-cases.md`: UC-016 (bước 1–4, nhánh 2a "xuất toàn bộ hồ sơ chạy nền", ngoại lệ 3a "lỗi sinh tệp").
- `architecture.md`: ADR-015 (Excel bằng openpyxl điền vào tệp mẫu `.xlsx` trong app; PDF bằng Jinja + bộ sinh PDF của Frappe), ADR-014 (sổ sự kiện, loại "Xuất tệp").
- `data-model.md` mục 4: dòng "Lần tính giá, kết quả, đối soát", "Bảng giải trình của dịch vụ thuộc khoa", "Bộ định mức".
- `ux-foundations.md`: SCR-DSK-028 Xuất hồ sơ (hộp thoại từ phương án hoặc lần tính giá; trạng thái "Đang đóng gói", "lỗi xuất").
- `test-cases.md`: mục 2.1, 2.2 (dữ liệu vàng); TC-OUT-01, 02, 03, 04. Golden: `docs/golden/golden_engine.py` (`run()`).

Phụ thuộc đã DONE trên `origin/develop` `b22ab47`:
- FEAT-003: `normcore/core/audit.py::log_export(file_type, ref_doctype, ref_name, file_name)` → NC Audit Event loại "Xuất tệp".
- FEAT-015/017/018: NC Costing Run (trạng thái "Đã khóa"), NC Service Cost (+ `lines`), `api/costing.py::get_explanation` (đã nhóm theo cấu phần và bước bằng `engine.group_explanation`), `engine.COMPONENT_CATEGORY`, `engine.COMPONENT_LABEL`.
- FEAT-034: `normcore/exports/norm_set.py::build_workbook` và `api/norm.py::export_norm_set`, `_export_data` (Excel bộ định mức gồm cột FR-OUT-006 và FR-OUT-011; ASM-034-15 để PDF và SCR-DSK-028 cho FEAT-019).
- FEAT-008: mẫu sinh PDF tự chứa `api/procedure_workflow.py::_html`, `_pdf_bytes` (`frappe.utils.pdf.get_pdf`).
- Fixture: `normcore/tests/costing_fixtures.py` (`make_golden_world`, `make_golden_run`, `make_locked_norm_set`, `make_golden_allocation`).

Giả định: `docs/decisions/assumptions/FEAT-019.md` (ASM-019-01..17). Sửa thiết kế: AMD-019-01 (không sửa `api/norm.py`, `norm_grid/`). Không thêm DocType, không thêm trường, không đổi quyền.

**TBD-01 (mẫu biểu chính thức Phụ lục I–V):** trong repo không có tệp mẫu nào (đã tìm `*.xlsx`, "Phụ lục", "REF-03", "TBD-01" trong `docs/` và mã). Áp dụng mặc định `CLAUDE.md` mục 6: "Xuất theo cấu trúc trong `srs.md`, `design.md`; mẫu là tệp template thay được". Cấu trúc cột dưới đây dựng từ mô tả FR-OUT-001..004 và các chỉ tiêu của `test-cases.md` mục 2.2; mọi tệp có dòng **"Mẫu biểu: Giả định — chờ xác nhận (TBD-01)"** (ASM-019-01). Khi có mẫu chính thức: thay tệp `.xlsx` trong `normcore/exports/templates/` và bảng cột trong `exports/annex.py` ở **một chỗ**; test NFR-CPL-002 đối chiếu hai thứ đó với nhau.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-OUT-001 | Phụ lục II "Phương án giá" từ một lần tính giá "Đã khóa": mỗi dịch vụ một trang tính (cơ cấu giá I–VII, mục 3.2). |
| FR-OUT-002 | Phụ lục III "Bảng tính giá thành theo yếu tố chi phí": mỗi dịch vụ một dòng, 5 yếu tố (trực tiếp + phân bổ) và giá thành toàn bộ. |
| FR-OUT-003 (Should) | Phụ lục IV "Bảng tính giá thành theo phương pháp phân bổ": mỗi dịch vụ một khối, chi phí trực tiếp, từng dòng phân bổ (quy tắc, tiêu chí, quỹ, số phân bổ), giá thành. Không có TC riêng; có test đơn vị. |
| FR-OUT-004 | Phụ lục V "Danh mục dịch vụ đề nghị định giá": mỗi dịch vụ một dòng, giá thành, giá tính toán, giá đề nghị (= giá làm tròn). |
| FR-OUT-005 | PDF bảng giải trình của một NC Service Cost: dòng chi phí FR-COST-010 nhóm theo cấu phần rồi theo bước, phần phân bổ, cơ cấu, tổng. Dùng đúng dữ liệu của `get_explanation`. |
| FR-OUT-006 | Bộ định mức: Excel (có sẵn, FEAT-034) **thêm** PDF cùng nội dung dòng (bước, căn cứ, người xác nhận). Xuất từ form bộ định mức hoặc từ hộp thoại của lần tính giá (bộ đã dùng cho dịch vụ). |
| FR-OUT-008 | Mọi tệp (Excel, PDF, tệp nén) có **trang thông tin** và **chân trang**: mã lần tính giá, bộ tham số, thời điểm xuất, người xuất (mục 3.1). |
| FR-OUT-009 (Could) | "Xuất toàn bộ hồ sơ": tác vụ nền đóng gói Phụ lục II, III, IV, V, mọi bảng giải trình PDF và mọi bộ định mức (Excel + PDF) thành một `.zip` private gắn lần tính; thông báo khi xong hoặc lỗi. Không có TC riêng. |
| FR-AUD-004 | Mỗi lần xuất thành công gọi `audit.log_export` một lần (tệp nén: một sự kiện cho tệp nén). |
| NFR-CPL-002 | Cấu trúc cột Phụ lục II–V do một bảng hằng trong `exports/annex.py` quyết định; tệp mẫu trong app có tiêu đề cột trùng bảng hằng (test). Đối chiếu với mẫu chính thức chờ TBD-01. |

**Không làm ở FEAT này:**
- Phụ lục I (FR-BM-008, FEAT-026) và bảng so sánh giá (FR-OUT-007, FEAT-027/028). Hộp thoại SCR-DSK-028 không hiện hai loại này.
- Phương án giá (NC Price Proposal, FEAT-028, R3) **chưa có** ở R1: "phương án vàng" của TC-OUT-01 = lần tính giá vàng đã khóa (ASM-019-02). Khi FEAT-028 có, mở rộng điểm vào, không đổi bộ sinh.
- Không đổi số liệu nào: bộ xuất chỉ đọc giá trị đã lưu ở NC Service Cost (đã khớp golden ở FEAT-015/017). Không tính lại, không làm tròn lại.

## 2. DocType

Không có DocType mới, không thêm trường, không đổi DocPerm. Đọc: NC Costing Run, NC Service Cost, NC Service Cost Line, NC Costing Parameter Set, NC Technical Service, NC Department, NC Norm Set, NC Norm Line, NC Clinical Procedure. Ghi: NC Audit Event (qua `log_export`), File (tệp nén, private).

**Quyền xuất (ASM-019-04):** xuất được khi có quyền **đọc** bản ghi nguồn; không đòi `export`/`print` của DocPerm.

| Loại tệp | Bản ghi nguồn | Kiểm | Vai trò được (ma trận mục 4) |
| :-- | :-- | :-- | :-- |
| Phụ lục II, III, IV, V; tệp nén | NC Costing Run | `has_permission("NC Costing Run", "read", doc)`; `status == "Đã khóa"` | NC Finance, NC Director, NC Admin, NC Auditor |
| Bảng giải trình PDF | NC Service Cost | `has_permission("NC Service Cost", "read", doc)` (phạm vi khoa của NC Department Head do quyền sẵn có); lần tính cha "Đã khóa" | NC Finance, NC Director, NC Admin, NC Auditor, NC Department Head (khoa mình) |
| Bộ định mức Excel, PDF | NC Norm Set | `has_permission("NC Norm Set", "read", doc)`; nếu kèm `run`: thêm quyền đọc lần tính và bộ phải là `norm_set` của một NC Service Cost thuộc lần tính | như ma trận "Bộ định mức" (Clinician, Dept Head theo khoa; Finance, Resource Mgr, Director, Consultant, Admin, Auditor) |

Vai trò không có quyền đọc → `frappe.PermissionError` với câu "Bạn không có quyền xuất tệp này". NC Auditor xuất được (đọc), không ghi được gì ngoài sự kiện nhật ký do máy chủ ghi.

## 3. Logic thuần (`normcore/exports/`, không import `frappe`)

Chỉ dùng `openpyxl`, `zipfile`, `decimal`. Mọi số đầu vào là `Decimal` (hoặc chuỗi số) do tầng API chuyển từ trường Currency; bộ xuất **không làm tròn lại**, chỉ ghi giá trị và đặt `number_format`.

### 3.1 `exports/meta.py` (mới) — FR-OUT-008

| Hàm / hằng | Làm gì |
| :-- | :-- |
| `INFO_SHEET = "Thông tin xuất"` | Tên trang tính thông tin (luôn là trang **cuối**, để không làm lệch trang đầu của `norm_set.build_workbook` mà test FEAT-034 đọc). |
| `TEMPLATE_NOTE = "Mẫu biểu: Giả định — chờ xác nhận (TBD-01)"` | Dòng ghi chú ở trang thông tin của Phụ lục II–V (ASM-019-01). |
| `NO_RUN = "Không gắn lần tính giá"` | Giá trị "Mã lần tính giá" khi xuất bộ định mức từ form bộ, không qua lần tính (ASM-019-05). |
| `info_rows(meta) -> list[tuple[str, str]]` | `meta = {run, parameter_set, parameter_set_title, exported_at (datetime), exported_by, exported_by_name, file_type, source, template_note?}` → các cặp: "Loại tệp", "Bản ghi nguồn", "Mã lần tính giá", "Bộ tham số" (`"<mã> — <tên>"`, không có thì "—"), "Thời điểm xuất" (`dd/mm/yyyy HH:MM:SS`, NFR-LOC-001), "Người xuất" (`"<họ tên> (<user>)"`), và `template_note` nếu có. |
| `footer_text(meta) -> str` | Một dòng: `"Lần tính {run} · Bộ tham số {ps} · Xuất {dd/mm/yyyy HH:MM} · {họ tên}"`. |
| `add_info_sheet(wb, meta)` | Thêm trang `INFO_SHEET` (cột A in đậm), và đặt `ws.oddFooter.center.text = footer_text(meta)` cho **mọi** trang tính của `wb`. |

### 3.2 `exports/annex.py` (mới) — FR-OUT-001..004, NFR-CPL-002

Hằng cấu trúc (một chỗ duy nhất, ASM-019-01):

```
ANNEX = {
  "II":  {"title": "PHƯƠNG ÁN GIÁ DỊCH VỤ KHÁM BỆNH, CHỮA BỆNH", "template": "phu_luc_ii.xlsx",  "header_row": 6, ...},
  "III": {"title": "BẢNG TÍNH GIÁ THÀNH THEO YẾU TỐ CHI PHÍ",     "template": "phu_luc_iii.xlsx", "header_row": 5, ...},
  "IV":  {"title": "BẢNG TÍNH GIÁ THÀNH THEO PHƯƠNG PHÁP PHÂN BỔ", "template": "phu_luc_iv.xlsx",  "header_row": 5, ...},
  "V":   {"title": "DANH MỤC DỊCH VỤ ĐỀ NGHỊ ĐỊNH GIÁ",           "template": "phu_luc_v.xlsx",   "header_row": 5, ...},
}
```

Dòng 1–4 của mỗi mẫu: tên đơn vị (để trống, bệnh viện điền), tên biểu ("Phụ lục <số> — Thông tư 21/2024/TT-BYT"), tiêu đề, dòng "Lần tính giá … · Ngày tính giá … · Loại giá …". `header_row` là dòng tiêu đề cột; dữ liệu bắt đầu ở `header_row + 1`.

**Phụ lục II** (`ANNEX_II_COLUMNS = ("STT", "Nội dung chi phí", "Thành tiền (đồng)", "Tỷ trọng (%)", "Ghi chú")`), mỗi dịch vụ một trang tính tên `service_code` (cắt 31 ký tự, trùng thì thêm `-2`…). Trên bảng: "Mã dịch vụ", "Tên dịch vụ", "Khoa", "Sản lượng". Dòng (`ANNEX_II_ROWS`, khóa → trường NC Service Cost):

| STT | Nội dung | Giá trị |
| :-- | :-- | :-- |
| I | Chi phí trực tiếp | Σ 6 dòng con |
| 1 | Nhân công | `direct_labor` |
| 2 | Thuốc | `direct_drug` |
| 3 | Vật tư | `direct_supply` |
| 4 | Thiết bị | `direct_equipment` |
| 5 | Hạ tầng | `direct_infra` |
| 6 | Tiện ích | `direct_utility` |
| II | Chi phí phân bổ | Σ 5 dòng con |
| 1–5 | Nhân công; Thuốc và vật tư; Khấu hao; Tiện ích; Quản lý | `alloc_labor`, `alloc_drug_supply`, `alloc_depreciation`, `alloc_utility`, `alloc_management` |
| III | Giá thành toàn bộ (I + II) | `full_cost` |
| IV | Tích lũy | `accumulation` |
| V | Nghĩa vụ tài chính | `obligation` |
| VI | Giá tính toán | `calculated_price` |
| VII | Giá đề nghị (đã làm tròn) | `rounded_price` |

Tỷ trọng (%) = giá trị ÷ `full_cost` × 100, làm tròn 2 chữ số **chỉ để hiển thị** (không phải công thức giá; ASM-019-06) — chỉ cho dòng I, II và con của chúng; `full_cost` = 0 thì trống. Dịch vụ cận lâm sàng: dòng I lấy theo cùng trường (bình quân gia quyền BR-CLS-013 ở FEAT-036, đã cộng ngoại kiểm vào dòng Thuốc/Vật tư), ghi chú dòng I "Bình quân gia quyền theo hệ thống xét nghiệm"; `eqa_cost` ≠ 0 thì thêm một dòng diễn giải "Trong đó: ngoại kiểm" = `eqa_cost`, không STT, không tỷ trọng, không tính vào tổng (ASM-019-07).

Kiểm tự nhất quán: |Σ I + Σ II − `full_cost`| > 0,01 → thêm ghi chú dòng III "Lệch {x} so với tổng cấu phần" (không sửa số).

**Phụ lục III** (`ANNEX_III_COLUMNS = ("STT", "Mã dịch vụ", "Tên dịch vụ", "Khoa", "Sản lượng", "Nhân công", "Thuốc và vật tư", "Khấu hao", "Tiện ích", "Quản lý", "Giá thành toàn bộ", "Ghi chú")`), một trang tính, một dòng/dịch vụ, không có dòng "Cộng" (giá thành đơn vị của các dịch vụ khác nhau không cộng có nghĩa). Yếu tố:

| Yếu tố | = trực tiếp (theo `engine.COMPONENT_CATEGORY` = golden `CATEGORY`) | + phân bổ |
| :-- | :-- | :-- |
| Nhân công (LABOR) | `direct_labor` | `alloc_labor` |
| Thuốc và vật tư (DRUG_SUPPLY) | `direct_drug + direct_supply` | `alloc_drug_supply` |
| Khấu hao (DEPRECIATION) | `direct_equipment + direct_infra` | `alloc_depreciation` |
| Tiện ích (UTILITY) | `direct_utility` | `alloc_utility` |
| Quản lý (MANAGEMENT) | 0 | `alloc_management` |

Hàm `elements(sc: dict) -> dict[str, Decimal]` (ánh xạ lấy từ `engine.COMPONENT_CATEGORY`, không gõ lại; `exports` được import `normcore.costing.engine` vì nó là module thuần). Σ yếu tố ≠ `full_cost` (ví dụ cận lâm sàng có ngoại kiểm hạch toán loại khác) → ghi chú "Chênh {x} với giá thành toàn bộ" và giữ `full_cost` đúng giá trị đã lưu (ASM-019-07). DV-TEST-A: 121.152,60; 49.550,00; 75.000,00; 4.900,00; 37.142,86; tổng 287.745,46.

**Phụ lục IV** (`ANNEX_IV_COLUMNS = ("STT", "Nội dung", "Loại chi phí", "Quy tắc phân bổ", "Tiêu chí của dịch vụ", "Tổng tiêu chí", "Quỹ chi phí", "Thành tiền")`): mỗi dịch vụ một khối: dòng tiêu đề khối "<mã> — <tên> (khoa, sản lượng)", dòng "Chi phí trực tiếp" (= Σ I của Phụ lục II), mỗi dòng NC Service Cost Line `line_type = "Phân bổ"` một dòng (`component`, `allocation_rule`, `driver_value`, `driver_total`, `pool_amount`, `amount`), dòng "Giá thành toàn bộ" = `full_cost`. Không có dòng phân bổ → một dòng "Không có chi phí phân bổ".

**Phụ lục V** (`ANNEX_V_COLUMNS = ("STT", "Mã dịch vụ", "Tên dịch vụ", "Mã trên HIS", "Khoa", "Loại giá", "Giá thành toàn bộ", "Giá tính toán", "Giá đề nghị", "Ghi chú")`): một dòng/dịch vụ; "Mã trên HIS" = `external_code` đầu tiên có `source_system = "HIS"` của NC Technical Service, không có thì trống; "Giá đề nghị" = `rounded_price`. Dịch vụ `calc_status = "Lỗi"`: ba cột giá trống, ghi chú "Tính lỗi: {calc_message}"; "Cảnh báo": ghi chú `calc_message`.

Thứ tự dịch vụ ở mọi phụ lục: `(service_code, department)` tăng dần. Phụ lục II, III, IV bỏ dịch vụ "Lỗi" (không có số), liệt kê chúng ở trang thông tin dòng "Dịch vụ tính lỗi, không xuất" (ASM-019-08).

| Hàm | Làm gì |
| :-- | :-- |
| `template_path(code) -> Path` | `normcore/exports/templates/<template>`. |
| `make_template(code) -> Workbook` | Dựng mẫu từ hằng (dòng 1–4, tiêu đề cột in đậm ở `header_row`, độ rộng cột). Dùng **một lần** để sinh tệp mẫu trong repo (script `python3 -m normcore.exports.annex --write-templates`), và làm dự phòng khi thiếu tệp. |
| `load_template(code) -> Workbook` | Mở tệp mẫu bằng `openpyxl.load_workbook`; thiếu tệp → `make_template(code)`. |
| `header_of(ws, code) -> tuple[str, ...]` | Đọc tiêu đề cột ở `header_row` (dùng cho test NFR-CPL-002). |
| `build_annex_ii(data) -> bytes`, `build_annex_iii(data)`, `build_annex_iv(data)`, `build_annex_v(data)` | `data = {run: {name, costing_date, price_category, parameter_set, …}, services: [ {service_code, service_name, department, volume, his_code, calc_status, calc_message, is_paraclinical, eqa_cost, <các trường tiền>, alloc_lines: [...]}, … ], meta: {...}}` → điền mẫu (giữ định dạng của mẫu), `number_format = '#,##0.00'` cho tiền, `'#,##0'` cho "Giá đề nghị", rồi `meta.add_info_sheet` → bytes. |
| `annex_rows_ii(svc) / annex_rows_iii(svc) / annex_rows_iv(svc) / annex_row_v(svc)` | Trả list dòng (giá trị thô) — dùng chung cho build và test golden. |

### 3.3 `exports/explanation.py` (mới) — FR-OUT-005

| Hàm | Làm gì |
| :-- | :-- |
| `pdf_context(expl: dict, meta: dict) -> dict` | Nhận đúng kết quả của `api.costing.get_explanation` và `meta` → ngữ cảnh Jinja: `header`, `direct_groups` (cấu phần → bước → dòng, giữ thứ tự của `engine.group_explanation`), `allocation_lines`, `structure`, `notes`, `paraclinical`, `totals` {direct, alloc, full_cost, accumulation, obligation, calculated_price, rounded_price}, `info` = `meta.info_rows(meta)`, `footer` = `meta.footer_text(meta)`. Chuỗi số định dạng `money(x)` → `"287.745,46"` (dấu chấm nghìn, phẩy thập phân, số âm "−"), `money0(x)` → `"302.100"`. |
| `money(x)`, `money0(x)`, `qty(x)` | Định dạng NFR-LOC-001 (thuần, test được). Không làm tròn khác 2 chữ số đã lưu. |

Mẫu Jinja: `normcore/exports/templates/service_explanation.html` (ASM-019-09): bảng tiêu đề (dịch vụ, khoa, lần tính, loại giá, sản lượng); với mỗi cấu phần: dòng nhóm "<nhãn cấu phần> — {tổng}", mỗi bước: dòng nhóm "<mã bước — tên bước> — {tổng}", rồi dòng chi phí (mã dòng, nguồn lực, lượng áp dụng, đơn giá, thành tiền, nguồn đơn giá, cảnh báo); phần "Chi phí phân bổ" (loại, quy tắc, tiêu chí, quỹ, thành tiền); khối cận lâm sàng nếu `paraclinical`; bảng tổng (chi phí trực tiếp, phân bổ, **giá thành toàn bộ**, tích lũy, nghĩa vụ, giá tính toán, giá làm tròn); ghi chú; **trang thông tin** (bảng `info`) ở cuối; chân trang `footer` mỗi trang qua `<div id="footer-html">` của bộ sinh PDF Frappe.

### 3.4 `exports/norm_set.py` (mở rộng tệp của FEAT-034) — FR-OUT-006, 008

- `build_workbook(data, meta=None)`: thêm tham số tùy chọn; `meta` có thì gọi `meta.add_info_sheet(wb, meta)` **sau** mọi trang hiện có. Không đổi trang, cột, thứ tự hiện có (test FEAT-034 giữ nguyên).
- `pdf_context(data, meta) -> dict` (mới): cùng `HEAD_ROWS`, `LINE_COLUMNS` (lọc cột cận lâm sàng như Excel), nhóm dòng theo bước (`step_id`, `step_title`), `info`, `footer`. Phần nội kiểm, chuẩn máy, ngoại kiểm, k (FR-OUT-011) đưa vào PDF như các bảng phụ khi `has_test_system`.
- Mẫu Jinja `normcore/exports/templates/norm_set.html`.

### 3.5 `exports/bundle.py` (mới) — FR-OUT-009

| Hàm | Làm gì |
| :-- | :-- |
| `zip_files(files: list[tuple[str, bytes]], meta) -> bytes` | `zipfile.ZIP_DEFLATED`, tên tệp trong gói giữ nguyên thứ tự, thêm `thong-tin-xuat.txt` (= `info_rows`). Tên trùng → thêm `-2`. Thời điểm mục zip cố định `(1980, 1, 1, 0, 0, 0)` để nội dung tất định. |

## 4. Tầng máy chủ (`normcore/api/export.py`, mới)

Hằng `FILE_TYPES` (mã → nhãn sự kiện, đuôi):

| Mã | Nhãn (ghi vào `log_export` và hộp thoại) | Tệp |
| :-- | :-- | :-- |
| `annex_ii` | Phụ lục II — Phương án giá | `PL-II-<run>.xlsx` |
| `annex_iii` | Phụ lục III — Giá thành theo yếu tố chi phí | `PL-III-<run>.xlsx` |
| `annex_iv` | Phụ lục IV — Giá thành theo phương pháp phân bổ | `PL-IV-<run>.xlsx` |
| `annex_v` | Phụ lục V — Danh mục dịch vụ đề nghị định giá | `PL-V-<run>.xlsx` |
| `explanation_pdf` | Bảng giải trình (PDF) | `giai-trinh-<service_code>-<run>.pdf` |
| `norm_set_xlsx` | Bộ định mức (Excel) | `<norm_set>.xlsx` |
| `norm_set_pdf` | Bộ định mức (PDF) | `<norm_set>.pdf` |
| `bundle` | Hồ sơ nén | `ho-so-<run>.zip` |

Hàm nội bộ:
- `_meta(file_type, source, run=None)`: `run` có → `parameter_set` và `title` của bộ tham số từ lần tính; `exported_at = now_datetime()`; `exported_by = frappe.session.user`, họ tên từ User.
- `_locked_run(run)`: `get_doc`, kiểm đọc, `status != "Đã khóa"` → `frappe.ValidationError` "Chỉ xuất hồ sơ từ lần tính giá đã khóa. Lần tính {0} đang ở trạng thái {1}." (ASM-019-03).
- `_annex_data(run)`: đọc mọi NC Service Cost của lần tính (`as_dict`, chuyển tiền sang `Decimal(str(x))`), tên dịch vụ, mã HIS, dòng phân bổ → `data` của mục 3.2.
- `_explanation_pdf(service_cost)`: `costing.get_explanation` (đã kiểm quyền) → `explanation.pdf_context` → `jinja2.Environment(autoescape=True)` dựng mẫu → `get_pdf` (HTML tự chứa như `procedure_workflow._html`).
- `_norm_set_files(norm_set, run=None)`: `norm._load(name)` (kiểm quyền có sẵn) → `norm._export_data(ns)` → Excel (`build_workbook(data, meta)`) / PDF.
- `_send(filename, content, file_type, ref_doctype, ref_name)`: `audit.log_export(FILE_TYPES[file_type].label, ref_doctype, ref_name, filename)` **rồi** đặt `frappe.response` (`filename`, `filecontent`, `type = "binary"`). Sinh tệp lỗi → không ghi sự kiện, ném lỗi "Không sinh được tệp {0}: {1}" (UC-016 3a).

API whitelisted:

| Hàm | Tham số | Kết quả | Lỗi / quyền |
| :-- | :-- | :-- | :-- |
| `get_export_options(run=None, service_cost=None, norm_set=None)` | một trong ba | `{"source": {...}, "options": [{"file_type", "label", "enabled", "reason", "needs": "service_cost"/"norm_set"/null}], "service_costs": [{name, service_code, service_name, department, calc_status}], "norm_sets": [{name, service_code, department}], "bundle": {"file_url", "creation"} hoặc null}` cho hộp thoại SCR-DSK-028. `run` chưa "Đã khóa" → mọi lựa chọn `enabled: false`, `reason` = câu của `_locked_run` | Không quyền đọc nguồn → `PermissionError` |
| `export_file(file_type, run=None, service_cost=None, norm_set=None)` | `file_type` thuộc `FILE_TYPES` trừ `bundle` | tệp nhị phân tải về | `file_type` lạ → `ValidationError` "Loại tệp không hợp lệ"; thiếu tham số bắt buộc → "Chọn {dịch vụ / bộ định mức} để xuất"; quyền theo mục 2 |
| `export_bundle(run)` | `run` "Đã khóa" | `{"queued": true, "job_id": "..."}`; `frappe.enqueue("normcore.api.export.build_bundle", queue="long", timeout=1500, run=run, user=session.user, job_id=f"nc-export-bundle-{run}", deduplicate=True)` | quyền đọc lần tính; job cùng lần tính đang chạy → trả `{"queued": false, "running": true}` |
| `build_bundle(run, user)` (không whitelist; chạy nền) | | sinh tệp theo thứ tự: PL-II, III, IV, V; giải trình PDF mỗi dịch vụ không "Lỗi"; mỗi `norm_set` khác nhau (xlsx + pdf) → `bundle.zip_files` → File private `ho-so-<run>.zip` gắn `NC Costing Run`/`run` (tệp cũ cùng tên bị thay) → `log_export("Hồ sơ nén", …, user=user)` → `core.notify.notify([user], "Đã đóng gói hồ sơ {run}", "NC Costing Run", run)` + `frappe.publish_realtime("nc_export_bundle", {"run", "status": "done", "file_url"}, user=user)` | Lỗi → `frappe.log_error(title="Xuất hồ sơ nén {run}")`, `publish_realtime(... "status": "error", "message")`, `notify([user], "Lỗi đóng gói hồ sơ {run}")`; không tạo File, không ghi "Xuất tệp" |

`audit.log_export` cần nhận `user` cho tác vụ nền: thêm tham số tùy chọn `user=None` chuyển tiếp sang `log_event` (thay đổi tương thích ngược, một dòng; ASM-019-10).

**`api/norm.py::export_norm_set(name)` không sửa (AMD-019-01).** Tệp `api/norm.py` giữ nguyên như `origin/develop`; `api/export.py` chỉ import `_load`, `_export_data`. Đường "Xuất Excel" ở lưới (FEAT-034) giữ hành vi cũ, không có trang thông tin và không ghi nhật ký (giới hạn đã biết, DEF-019-01). Đường xuất bộ định mức có truy vết là `export_file("norm_set_xlsx" | "norm_set_pdf")` từ hộp thoại.

## 5. Giao diện (chi tiết ở `ui-design.md`)
- SCR-DSK-028 hộp thoại "Xuất hồ sơ" dùng chung (`normcore/public/js/export_dialog.js`, `normcore.export.open({run|service_cost|norm_set})`), mở từ: form NC Costing Run (nút "Xuất hồ sơ"), form NC Service Cost / SCR-DSK-023 (nút "Xuất PDF giải trình"), form NC Norm Set và lưới định mức (nút "Xuất PDF" cạnh "Xuất Excel" có sẵn).
- Nạp hộp thoại **[AMD-019-02]**: `hook_registry/FEAT-019.json` khai báo bundle `"normcore_export.bundle.js"` (import `./export_dialog.js`), Frappe trả URL có hash qua `assets.json`; không dùng URL cố định `/assets/normcore/js/export_dialog.js` (bị nginx cache 1 năm, NORM-77).
- Tải tệp bằng `open_url_post("/api/method/normcore.api.export.export_file", args)` (không đặt tham số lên URL GET).
- Chuỗi qua `__()`/`_()`, bản dịch `normcore/translations/vi.d/FEAT-019.csv`.

## 6. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR |
| :-: | :-- | :-- | :-- |
| 1 | Golden (thuần): từ `golden_engine.run()` dựng `services` → `annex_rows_ii` DV-TEST-A có I = 183.963,06; II = 103.782,40 (52.151,66 + 7.300,00 + 3.787,88 + 3.400,00 + 37.142,86); III = 287.745,46; IV = 14.387,27; VI = 302.132,73; VII = 302.100; DV-TEST-B III = 88.169,70, VII = 92.600. `annex_rows_iii` DV-TEST-A: 121.152,60 / 49.550,00 / 75.000,00 / 4.900,00 / 37.142,86 / 287.745,46. `annex_row_v` A: 287.745,46 / 302.132,73 / 302.100. Số lấy từ golden, không chép tay | TC-OUT-01 | FR-OUT-001, 002, 004 |
| 2 | Site: lần tính vàng đã khóa (`make_golden_world` + `make_golden_allocation` + chạy + khóa) → `export_file("annex_ii"/"annex_iii"/"annex_v")` trả `.xlsx` mở được; tiêu đề cột ở `header_row` **bằng đúng** `ANNEX_*_COLUMNS` và bằng tiêu đề của tệp mẫu trong app (`header_of(load_template(code))`); ô số khớp #1; Phụ lục II có 2 trang tính dịch vụ + trang "Thông tin xuất" | TC-OUT-01 | FR-OUT-001, 002, 004, NFR-CPL-002 |
| 3 | Site: `export_file("explanation_pdf", service_cost=<DV-TEST-A>)` trả PDF (`%PDF`); HTML sinh ra (gọi hàm dựng HTML, kiểm chuỗi) có nhóm cấu phần theo thứ tự `group_explanation`, mỗi cấu phần có tiêu đề nhóm và tổng, trong cấu phần Nhân công có đủ nhóm của 3 bước quy trình (thứ tự bước), mọi dòng trực tiếp của `get_explanation` xuất hiện đúng một lần (theo mã dòng), có phần phân bổ 5 dòng, và "287.745,46" ở dòng giá thành toàn bộ | TC-OUT-02 | FR-OUT-005 |
| 4 | Site: với **mỗi** loại tệp (`annex_ii`…`norm_set_pdf`): tệp có trang/khối thông tin chứa mã lần tính, `"<bộ tham số> — <tên>"`, thời điểm xuất định dạng `dd/mm/yyyy`, họ tên và user người xuất; Excel có `oddFooter.center.text` chứa mã lần tính ở mọi trang; mỗi lần xuất thêm đúng **một** NC Audit Event `event_type = "Xuất tệp"`, `user` = người xuất, `ref_doctype`/`ref_name` = bản ghi nguồn, `detail` chứa nhãn loại tệp và tên tệp | TC-OUT-03 | FR-OUT-008, FR-AUD-004 |
| 5 | Site: `export_file("norm_set_xlsx"/"norm_set_pdf", norm_set=<bộ DV-TEST-A>, run=<lần vàng>)`: Excel có 11 dòng định mức (L01–L11) theo thứ tự bước, cột "Căn cứ" = "Quy trình", "Người xác nhận" = người đã xác nhận dòng; PDF (HTML) có 11 dòng nhóm theo 3 bước của quy trình và nhóm "Chung cho cả dịch vụ" (L10), cột căn cứ, người xác nhận. Fixture `make_locked_norm_set` không đặt `confirmed_by`: test đặt `confirmed_by`, `confirmed_on` cho các dòng bằng `frappe.db.set_value` ở bước dựng dữ liệu (không sửa tệp fixture cũ). Xuất từ form bộ (không kèm `run`) qua `export_file`: trang "Thông tin xuất" ghi "Không gắn lần tính giá" và có sự kiện. `api/norm.py`, `norm_grid/` không đổi so với `origin/develop` (AMD-019-01) | TC-OUT-04 | FR-OUT-006, 008 |
| 6 | Thuần: `annex_rows_iv` DV-TEST-A có 5 dòng phân bổ (LABOR 52.151,66; DRUG_SUPPLY 7.300,00; DEPRECIATION 3.787,88; UTILITY 3.400,00; MANAGEMENT 37.142,86), dòng trực tiếp 183.963,06, giá thành 287.745,46; dịch vụ không có phân bổ → "Không có chi phí phân bổ" | — | FR-OUT-003 |
| 7 | Site: `build_bundle(run, user)` (gọi trực tiếp, không qua hàng đợi) tạo File private `ho-so-<run>.zip` gắn lần tính, gói có PL-II, III, IV, V, 2 PDF giải trình, xlsx + pdf của mỗi bộ định mức, `thong-tin-xuat.txt`; một sự kiện "Xuất tệp" detail "Hồ sơ nén"; `export_bundle` gọi `frappe.enqueue` (mock) với `queue="long"`; lỗi giả lập trong một bộ sinh → không có File, có Error Log, không có sự kiện "Xuất tệp" | — | FR-OUT-009 |
| 8 | Site, quyền: NC Auditor xuất được Phụ lục V và bảng giải trình (đọc), không ghi được gì khác; NC Clinician gọi `export_file("annex_v", run)` → `PermissionError`; NC Department Head xuất giải trình dịch vụ khoa mình được, khoa khác bị từ chối; lần tính "Đã tính" (chưa khóa) → `ValidationError` "Chỉ xuất hồ sơ từ lần tính giá đã khóa"; `file_type` lạ → `ValidationError` | — | FR-OUT-001, 005, FR-ACC-007 |
| 9 | Thuần: `meta.info_rows`, `footer_text`, `explanation.money` (`287745.46 → "287.745,46"`, `-63636.36 → "−63.636,36"`, `302100 → "302.100"`), `bundle.zip_files` tất định (hai lần cùng đầu vào → cùng bytes), tên trang tính trùng/dài; độ phủ `normcore/exports/` (mới) ≥ 90% | — | FR-OUT-008, 009 |

Tên test (bắt buộc có): `test_TC_OUT_01_phu_luc_ii_iii_v_khop_golden` (thuần, golden), `test_TC_OUT_01_xuat_phu_luc_cot_khop_mau` (site), `test_TC_OUT_02_giai_trinh_pdf_nhom_cau_phan_buoc`, `test_TC_OUT_03_thong_tin_truy_vet_va_nhat_ky`, `test_TC_OUT_04_bo_dinh_muc_excel_pdf_11_dong`.

## 7. Bố trí test (tệp mới, không sửa tệp cũ)
- Thuần: `normcore/tests/unit/test_exports_annex.py`, `test_exports_meta.py`, `test_exports_explanation.py`, `test_exports_bundle.py`.
- Golden: `normcore/tests/golden/test_exports_golden.py` (#1, #6; import `docs/golden/golden_engine.py` như các test golden hiện có).
- Site: `normcore/api/test_export.py` (#2–#5, #7, #8; dùng `costing_fixtures`, không thêm fixture vào tệp cũ ngoài hàm mới nếu cần, như FEAT-018).
- UI tĩnh: `normcore/tests/unit/test_export_ui.py` (nút, đường gọi API đầy đủ, chuỗi có bản dịch).

## 8. Rủi ro
- **TBD-01**: cột chưa đối chiếu mẫu chính thức. Giảm nhẹ: một chỗ cấu trúc + tệp mẫu thay được + nhãn "Giả định — chờ xác nhận" (ASM-019-01). Lead có thể đổi khi có mẫu mà không đổi API.
- **wkhtmltopdf** trên CI/bench: test kiểm HTML (chuỗi) là chính, PDF chỉ kiểm chữ ký `%PDF` (như test in quy trình FEAT-008).
- Test FEAT-034 đọc trang đầu `norm_set.build_workbook`: trang thông tin thêm ở **cuối** để không đổi kết quả cũ.
- Tệp nén của bộ dữ liệu lớn (500 dịch vụ) chạy nền `long`; đo một lần ở implementation-log, không thêm TC.
