# FEAT-021 — Thay thế văn bản và hàng đợi rà soát — Thiết kế kỹ thuật

Issue NORM-64. Nguồn: `srs.md` FR-LIB-007, FR-LIB-008, FR-LIB-009 (và FR-WF-009, FR-NOTI-001 mà UC-002 dẫn tới); `use-cases.md` UC-002 (bước 1–7, 2a, 5a); `data-model.md` mục 3.2 (NC Legal Document `supersessions`, `expiry_date`; NC Legal Supersession), mục 3.3 (NC Clinical Procedure `needs_review`, NC Procedure Citation) và mục 4 dòng "Văn bản, mục, ánh xạ", "Quy trình"; `ux-foundations.md` SCR-DSK-012; TC-LIB-05, TC-LIB-06, TC-LIB-07. Phụ thuộc FEAT-020, FEAT-007 (DONE trên `develop`); dùng thêm FEAT-002 (`core/notify.py`), FEAT-008 (`create_revision`), FEAT-022 (đều DONE). Giả định: `docs/decisions/assumptions/FEAT-021.md` (ASM-021-01..).

> **Cập nhật sau NORM-65 (ASM-021-13):** trích dẫn của quy trình nay là Link; khớp theo `legal_section`/`legal_document`. Các đoạn dưới đây nói về khớp theo số hiệu và mã mục gõ tay (ASM-021-01, mục 3.2, tiêu chí 4, mục 6, 7) đã hết hiệu lực. Xem `docs/as-built/FEAT-021.md`.

Dùng lại, **không tạo lại**: NC Legal Document, NC Legal Section, `api/library.py` (`refresh_validity`, `daily_job`, `get_sections`), `library/validity.py`, `library/search.py` (`normalize_doc_number`, `natural_key`) của FEAT-020; NC Clinical Procedure (trường `needs_review` đã có từ FEAT-006), NC Procedure Citation, `api/procedure_workflow.py`, `procedure/approval.py` của FEAT-006/007; `api/procedure.create_revision` của FEAT-008; `core/notify.notify` của FEAT-002; phạm vi khoa `core/scope_rules/nc_clinical_procedure.json`.

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-LIB-007 (Must) | Trên văn bản A khai báo dòng thay thế "Toàn bộ" văn bản B từ ngày D: ghi dòng NC Legal Supersession, đặt `B.expiry_date` = D − 1 ngày. Khi đến ngày D, tác vụ hằng ngày (đã có, `refresh_validity`) chuyển B và mọi mục của B sang "Hết hiệu lực". D ≤ hôm nay: tính lại hiệu lực ngay khi lưu. |
| FR-LIB-008 (Must) | Dòng thay thế "Một phần" kèm danh sách mã mục (`section_no`) của B: chỉ đặt `expiry_date` cho đúng các NC Legal Section đó; mục khác và `B.expiry_date` giữ nguyên. |
| FR-LIB-009 (Must) | Mỗi lần `refresh_validity` chuyển văn bản hoặc mục sang "Hết hiệu lực": tìm quy trình "Đã ban hành" có trích dẫn văn bản/mục đó, đặt `needs_review` = 1, thông báo trưởng khoa của khoa chủ trì (`NC Department.head_user`) bằng `core.notify.notify`. Không có quy trình nào → chỉ có liên kết thay thế (UC-002 5a). Hàng đợi rà soát SCR-DSK-012 liệt kê quy trình có cờ kèm trích dẫn bị ảnh hưởng và văn bản thay thế; trưởng khoa chọn "Sửa đổi" (tạo phiên bản sửa đổi, UC-007) hoặc "Không cần sửa" kèm lý do (gỡ cờ). |

Không làm: đổi `legal_document`/`legal_section` của NC Procedure Citation sang Link (nợ ASM-046, ghi ở mục 7); rà soát ánh xạ dịch vụ hoặc bộ định mức khi văn bản bị thay thế (FEAT-025); tự hoàn tác ngày hết hiệu lực khi xóa dòng thay thế (ASM-021-02); kênh thông báo mới (dùng Notification Log + email của FEAT-002).

## 2. DocType

### 2.1 Mới — NC Legal Supersession (bảng con, module NC Library)
Tệp `normcore/nc_library/doctype/nc_legal_supersession/`. `istable` = 1, `editable_grid` = 0 (sửa bằng hộp thoại "Khai báo thay thế" hoặc form dòng), `permissions` = [] (bảng con theo quyền DocType cha — data-model mục 4 ghi chú [1.1]). Thay đổi hiện trong Version của văn bản A (NC Legal Document có `track_changes` = 1).

| Trường | Nhãn | Kiểu | BB | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| superseded_document | Văn bản bị thay thế | Link NC Legal Document | Có | `in_list_view` |
| scope | Phạm vi | Select `Toàn bộ` / `Một phần` | Có | mặc định `Toàn bộ`, `in_list_view` |
| superseded_sections | Các mục bị thay thế | Small Text | | Danh sách `section_no` của B, lưu dạng chuẩn `"2, 5"` (ASM-021-04); `depends_on`/`mandatory_depends_on: eval:doc.scope=='Một phần'` |
| from_date | Từ ngày | Date | Có | `in_list_view` |

Không có trường nào ngoài data-model.

### 2.2 Mở rộng — NC Legal Document
- Thêm Section Break `supersession_section` (nhãn "Thay thế") + `supersessions` (Table NC Legal Supersession, nhãn "Thay thế") — đúng data-model. Đặt sau section "Các mục" (`sections_html`), trước "Ánh xạ hướng dẫn".
- Thêm HTML `superseded_by_html` (trong cùng section) hiện "Bị thay thế bởi" (tra ngược). Trường bố cục không có cột CSDL, tiền lệ ASM-020-02, ASM-022-09 — không AMD (ASM-021-10).
- Không đổi trường cũ. Quyền giữ nguyên (`R R R R R W R R W R`).

### 2.3 NC Clinical Procedure
Không thêm trường. `needs_review` (Check, "Cần rà soát") đã có. Thay đổi hành vi:
- `api/procedure_workflow.apply_action`, nhánh "Ban hành": đặt `doc.needs_review = 0` trước `doc.save` (phiên bản sửa đổi kế thừa cờ theo ASM-008-05; ban hành xong là đã rà soát — ASM-021-06).
- Đặt/gỡ cờ ở quy trình "Đã ban hành" (nội dung bị khóa) bằng `frappe.db.set_value(DT, name, "needs_review", v, update_modified=False)` từ mã máy chủ đã kiểm quyền (mục 4), kèm Comment "Info" trên quy trình để có dấu vết.

### 2.4 Kiểm tra khi lưu NC Legal Document (`validate` → `library/supersession.row_errors`)
Cho mỗi dòng `supersessions` (gom hết lỗi, `frappe.throw` một lần, mỗi lỗi một dòng có số thứ tự dòng):
1. `superseded_document` = chính văn bản → "Văn bản không thể thay thế chính nó".
2. Hai dòng cùng `superseded_document` → "Văn bản {0} đã được khai báo thay thế ở dòng {1}".
3. `from_date` ≤ `effective_date` của B → "Ngày bắt đầu thay thế phải sau ngày hiệu lực của {0} ({1})" (để `expiry_date` = D − 1 ≥ ngày hiệu lực, giữ đúng `check_dates` của FEAT-020).
4. `scope` = "Một phần": `superseded_sections` rỗng → "Chọn ít nhất một mục bị thay thế"; có mã không thuộc mục của B → "Văn bản {0} không có mục: {1}" (B chưa lập chỉ mục coi như không có mục).
5. `scope` = "Toàn bộ": xóa `superseded_sections` (không báo lỗi).
6. Chuẩn hóa `superseded_sections` về dạng `"2, 5"` (giữ thứ tự `natural_key`, bỏ trùng).

### 2.5 Áp dụng khi lưu (`on_update` → `api/library.apply_supersessions(doc)`)
Với mỗi dòng (idempotent, chạy lại không đổi gì):
1. Kiểm quyền ghi B: `frappe.has_permission("NC Legal Document", "write", doc=B)`; không có → `frappe.PermissionError` "Bạn không có quyền sửa văn bản {0}".
2. "Toàn bộ": `new = supersession.plan_expiry(B.expiry_date, from_date)`; có giá trị → `frappe.db.set_value("NC Legal Document", B, "expiry_date", new)`.
3. "Một phần": `supersession.plan_section_expiry(mục của B, các mã, from_date)` → `set_value` `expiry_date` cho từng mục.
4. Có thay đổi ở 2 hoặc 3 → Comment "Info" trên B: "Bị thay thế toàn bộ bởi {A} từ dd/mm/yyyy" / "Các mục {2, 5} bị thay thế bởi {A} từ dd/mm/yyyy".
5. Sau cùng, nếu có dòng đổi và `from_date` ≤ hôm nay: gọi `refresh_validity()` (cùng giao dịch) để chuyển trạng thái và gắn cờ ngay.

Ngày hết hiệu lực chỉ được kéo **sớm hơn**: nếu B/mục đã có `expiry_date` ≤ giá trị mới thì giữ (hai văn bản cùng thay B → lấy ngày sớm nhất). Xóa dòng thay thế không hoàn tác `expiry_date`; người quản lý văn bản sửa tay ở form B (ASM-021-02).

### 2.6 Migration
Bảng mới, trường mới tạo bởi `bench migrate`. Không đổi cấu trúc cột đã có → không cần patch.

## 3. Logic thuần (không import `frappe`)

### 3.1 `normcore/library/supersession.py`
Hằng: `ALL = "Toàn bộ"`, `PART = "Một phần"`.

| Hàm | Vào → Ra | Quy tắc |
| :-- | :-- | :-- |
| `parse_sections(text)` | str → list[str] | Tách theo `,`, `;`, xuống dòng; `strip`; bỏ rỗng; bỏ trùng (so sánh `strip().casefold()`); sắp `search.natural_key` |
| `format_sections(nos)` | list → str | `", ".join(nos)` |
| `expiry_for(from_date)` | date → date | `from_date − 1 ngày` (FR-LIB-007, BR không có công thức tiền) |
| `plan_expiry(current, from_date)` | → date \| None | `new = expiry_for(from_date)`; `current` có và `current ≤ new` → None; ngược lại `new` |
| `plan_section_expiry(sections, wanted, from_date)` | `sections`: list `(name, section_no, expiry_date)`; `wanted`: list mã → list `(name, new_expiry)` | Chỉ mục có `section_no` (so `casefold`) thuộc `wanted`; áp `plan_expiry` từng mục |
| `row_errors(rows, own_name, targets)` | `rows`: list dict dòng (`idx`, `superseded_document`, `scope`, `superseded_sections`, `from_date`); `targets`: dict tên B → `{"effective_date", "doc_number", "section_nos"}` → list[str] | Quy tắc 2.4.1–2.4.4 |
| `normalize_rows(rows)` | → None (sửa `rows`) | 2.4.5, 2.4.6 |
| `covers(row, section_no)` | → bool | "Toàn bộ" → True; "Một phần" → `section_no` thuộc `parse_sections` |

### 3.2 `normcore/procedure/review.py`
Hằng: `REASON_DOC = "Văn bản hết hiệu lực"`, `REASON_SECTION = "Mục hết hiệu lực"`.

NC Procedure Citation đang lưu `legal_document`, `legal_section` dạng **Data** (ASM-046, chưa đổi sang Link). Hàm khớp chấp nhận cả tên bản ghi và giá trị người dùng gõ (ASM-021-01):

| Hàm | Vào → Ra | Quy tắc |
| :-- | :-- | :-- |
| `normalize_section_no(s)` | → str | NFC, `casefold`, bỏ tiền tố "mục"/"điều" đầu chuỗi, bỏ khoảng trắng, bỏ dấu `.` cuối |
| `build_index(documents, sections)` | `documents`: list `(name, doc_number)`; `sections`: list `(name, legal_document, section_no)` → `Index` | Bảng tra: tên văn bản; `normalize_doc_number(doc_number)` → tên; tên mục → (văn bản, mục); (văn bản, `normalize_section_no`) → mục |
| `resolve(citation, index)` | `citation`: dict `legal_document`, `legal_section` → `(doc, section)` \| None | (a) `legal_section` là tên NC Legal Section → (văn bản của mục, mục). (b) `legal_document` khớp tên hoặc số hiệu chuẩn hóa → doc; `legal_section` rỗng → (doc, None); khớp `section_no` trong doc → (doc, mục); không khớp mục → (doc, None). (c) Còn lại → None |
| `affected(citations, index, expired_docs, expired_sections)` | → list dict (citation + `legal_document_name`, `legal_section_name`, `reason`) | Trích dẫn ảnh hưởng khi doc ∈ `expired_docs` (`REASON_DOC`) hoặc mục ∈ `expired_sections` (`REASON_SECTION`). Quan hệ "Chưa có căn cứ" không có văn bản → không ảnh hưởng |
| `to_flag(procedures, index, expired_docs, expired_sections)` | `procedures`: list dict `name`, `workflow_state`, `citations` → list `(name, [affected])` | Chỉ `workflow_state` = `approval.PUBLISHED` |
| `notify_subject(procedure, refs, on)` | → str | "Cần rà soát quy trình {procedure}: {số hiệu} [mục {a, b}] hết hiệu lực từ dd/mm/yyyy" (tiêu đề có ngày để `notify` chống trùng theo đợt) |
| `dismiss_errors(state, needs_review, reason)` | → list[str] | Không "Đã ban hành" → "Chỉ rà soát quy trình đã ban hành"; không có cờ → "Quy trình không có cờ Cần rà soát"; lý do rỗng sau `strip` → "Cần nhập lý do không cần sửa" |

Ánh xạ BR/golden: không có phép tính tiền; không dùng `docs/golden/`. Độ phủ hai module ≥ 90% (pytest `tests/unit`).

## 4. API và tác vụ

Mọi hàm whitelisted kiểm quyền tường minh; thiếu quyền → `frappe.PermissionError` với thông báo tiếng Việt.

### 4.1 `normcore/api/library.py` (mở rộng)

| Hàm | Tham số | Kết quả | Lỗi / quyền |
| :-- | :-- | :-- | :-- |
| `declare_supersession(legal_document, superseded_document, scope, from_date, sections=None)` | `sections`: JSON list hoặc chuỗi mã | `{"row", "expiry_date", "sections": [{"name","section_no","expiry_date"}]}` | Quyền ghi A (`frappe.has_permission("NC Legal Document","write",A)`). Thêm dòng vào `A.supersessions`, `A.save()` (không `ignore_permissions`) → `validate` 2.4, `on_update` 2.5. Dòng cùng B đã có → cập nhật dòng đó thay vì thêm |
| `get_supersessions(legal_document)` | tên văn bản | `{"supersedes": [{"row","superseded_document","doc_number","title","scope","sections","from_date"}], "superseded_by": [{"document","doc_number","title","scope","sections","from_date"}]}` | Quyền đọc. `superseded_by` tra ngược `tabNC Legal Supersession` `parenttype='NC Legal Document'`, `superseded_document = %s` |
| `apply_supersessions(doc)` (không whitelisted) | NC Legal Document | số bản ghi đổi | mục 2.5 |
| `refresh_validity(today=None)` (đã có) | | thêm khóa `"flagged"` | Thu các văn bản và mục **vừa đổi sang** "Hết hiệu lực" (`status == validity.HET` trong `changed_docs`, `changed_secs`) → `api.review.flag_affected(docs, sections, on)`. Không có thay đổi sang Hết → không gọi |

`daily_job` giữ nguyên (gọi `refresh_validity`). Test gọi thẳng `refresh_validity(today=...)` (UC-002 bước 4).

### 4.2 `normcore/api/review.py` (mới)

| Hàm | Tham số | Kết quả | Lỗi / quyền |
| :-- | :-- | :-- | :-- |
| `flag_affected(expired_docs, expired_sections, on=None)` (không whitelisted) | tập tên | số quy trình được gắn cờ | Đọc trích dẫn của quy trình "Đã ban hành" bằng một truy vấn JOIN `tabNC Procedure Citation` (parenttype `NC Clinical Procedure`, parentfield `citations`); dựng `Index` chỉ từ văn bản/mục có liên quan; `review.to_flag`. Mỗi quy trình: `needs_review` = 1 (nếu chưa), Comment "Info" nêu trích dẫn bị ảnh hưởng, `notify.notify([head_user], notify_subject(...), DT, name)` (khoa không có `head_user` → chỉ gắn cờ, `frappe.log_error` mức thông tin không cần). Chạy dưới quyền hệ thống (từ tác vụ nền) |
| `get_review_queue(department=None, start=0, page_length=50)` | | `{"total", "rows": [ {"name","technical_service","service_name","department","version_no","effective_date","decision_no","pending_revision","can_act","citations":[{"row","target_section","target_step_id","relation","quote","legal_document","legal_section","doc_number","section_no","heading","validity_status","expiry_date","reason","replacements":[{"document","doc_number","title","scope","sections","from_date"}]}]} ]}` | Quyền đọc NC Clinical Procedure (`frappe.has_permission(DT,"read")`), không có → PermissionError. Danh sách bằng `frappe.get_list` (áp phạm vi khoa cho NC Clinician/NC Department Head) lọc `needs_review = 1`, `workflow_state = "Đã ban hành"` (+ `department`), sắp `modified desc`, `page_length` ≤ 200. `citations` = trích dẫn đang trỏ tới văn bản/mục "Hết hiệu lực" (tính lúc đọc, `review.affected` với tập Hết hiện tại); `replacements` = dòng NC Legal Supersession có `superseded_document` = văn bản đó và `covers(row, section_no)`. `pending_revision` = tên bản Nháp/Chờ… cùng (dịch vụ, khoa) nếu có. `can_act` = người gọi là NC Department Head của khoa (hoặc Administrator) |
| `dismiss_review(procedure, reason)` | | `{"needs_review": 0}` | Quyền: vai NC Department Head và `department ∈ scope.get_user_departments(user)` (hoặc Administrator); khác → PermissionError "Chỉ trưởng khoa của khoa chủ trì được kết luận rà soát". `review.dismiss_errors` → `frappe.throw`. Gỡ cờ (`set_value`), Comment "Info": "Không cần sửa: {lý do}" |

"Sửa đổi" (UC-002 bước 7 → UC-007) **không có API mới**: giao diện gọi `normcore.api.procedure.create_revision(procedure)` (FEAT-008; đã kiểm quyền ghi theo khoa, trả bản đang soạn nếu có) rồi mở trình soạn. Cờ ở bản gốc giữ tới khi bản sửa đổi được ban hành; bản gốc thành "Đã thay thế" thì rời hàng đợi; bản mới được gỡ cờ ở "Ban hành" (2.3).

### 4.3 Hook, fixtures
- Không thêm scheduler: dùng `normcore.api.library.daily_job` đã có.
- Desk Page `review-queue` (module NC Procedure) — xem `ui-design.md`; lối tắt Workspace thêm một dòng cuối `normcore/nc_core/workspace/normcore/shortcuts.d/00-base.txt` rồi chạy `python3 scripts/build_workspace.py` (không sửa tay Workspace JSON).
- `vi.csv`: chuỗi giao diện mới.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test (đề xuất tên) |
| :-: | :-- | :-- | :-- | :-- |
| 1 | B hiệu lực 01/01/2026 có mục 1..5. `declare_supersession(A, B, "Toàn bộ", 2026-07-01)`: `B.expiry_date` = 2026-06-30; `refresh_validity(today=2026-06-30)`: B và mục "Còn hiệu lực"; `refresh_validity(today=2026-07-01)`: B "Hết hiệu lực" và **mọi** mục của B "Hết hiệu lực"; A có dòng NC Legal Supersession đúng 4 trường | TC-LIB-05 | FR-LIB-007 | `api/test_library_supersession.py::test_TC_LIB_05_thay_toan_bo` |
| 2 | `declare_supersession(A, B, "Một phần", 2026-07-01, ["2","5"])`: mục 2 và 5 có `expiry_date` 2026-06-30; mục 1, 3, 4 và B không có; sau `refresh_validity(today=2026-07-01)` chỉ mục 2, 5 "Hết hiệu lực", B và mục khác "Còn hiệu lực"; `superseded_sections` lưu "2, 5" | TC-LIB-06 | FR-LIB-008 | `test_TC_LIB_06_thay_mot_phan` |
| 3 | Quy trình P "Đã ban hành" (khoa K có `head_user` = H) trích dẫn mục 2 của B; khai báo thay mục 2; `refresh_validity(today=from_date)`: `P.needs_review` = 1; có Notification Log cho H, `document_name` = P; `get_review_queue()` gọi bằng H trả P với trích dẫn mục 2, `reason` "Mục hết hiệu lực", `replacements` chứa A. Quy trình "Nháp" cùng trích dẫn không bị gắn cờ; quy trình trích dẫn mục 3 không bị gắn cờ | TC-LIB-07 | FR-LIB-009 | `api/test_review_queue.py::test_TC_LIB_07_gan_co_thong_bao_hang_doi` |
| 4 | Trích dẫn ghi dạng gõ tay (số hiệu "123/qđ-byt", mục "Mục 2") và dạng tên bản ghi (`LS-…`) đều được khớp; B hết hiệu lực toàn bộ gắn cờ cả trích dẫn chỉ ghi văn bản | — | FR-LIB-009 | `test_FR_LIB_009_khop_trich_dan_tu_do` |
| 5 | UC-002 5a: thay thế văn bản không có trích dẫn → không quy trình nào đổi `needs_review`, không Notification Log mới, `flagged` = 0; liên kết thay thế vẫn ghi | — | FR-LIB-009 | `test_FR_LIB_009_khong_co_quy_trinh_trich_dan` |
| 6 | Kiểm khi lưu (2.4): tự thay chính nó, trùng B, `from_date` ≤ ngày hiệu lực B, "Một phần" không mục, mục không có trong B → `ValidationError` liệt kê lỗi; "Toàn bộ" xóa `superseded_sections`. Hai văn bản cùng thay B: `expiry_date` lấy ngày sớm hơn; lưu lại A không đổi gì | — | FR-LIB-007, FR-LIB-008 | `test_FR_LIB_007_kiem_khi_luu` |
| 7 | `from_date` ≤ hôm nay: ngay sau `declare_supersession` B (hoặc mục) đã "Hết hiệu lực" và quy trình trích dẫn đã có cờ | — | FR-LIB-007, FR-LIB-009 | `test_FR_LIB_007_ngay_qua_khu_ap_dung_ngay` |
| 8 | `dismiss_review(P, "Nội dung mục mới giống mục cũ")` bởi H: `needs_review` = 0, có Comment "Không cần sửa: …", P rời hàng đợi. Lý do rỗng → lỗi. NC Clinician, NC Department Head khoa khác, NC Auditor → `PermissionError` | — | FR-LIB-009 (UC-002 bước 7) | `test_FR_LIB_009_khong_can_sua_go_co` |
| 9 | "Sửa đổi": H gọi `create_revision(P)` → bản Nháp v+1 có `needs_review` = 1; `get_review_queue` trả `pending_revision` = bản đó; ban hành bản mới (`apply_action` "Ban hành") → bản mới `needs_review` = 0; khi bản cũ thành "Đã thay thế" thì rời hàng đợi | — | FR-LIB-009, FR-WF-009 | `test_FR_WF_009_sua_doi_tu_hang_doi` |
| 10 | Quyền: NC Clinician, NC Auditor gọi `declare_supersession` → `PermissionError`; NC Auditor gọi `get_supersessions`, `get_review_queue` được (`can_act` = false); người không có vai NC gọi `get_review_queue` → `PermissionError`; NC Department Head chỉ thấy quy trình khoa mình; NC Document Controller khai báo được | — | FR-ACC-007, FR-ACC-003 | `test_FR_LIB_007_quyen_thay_the`, `test_SCR_DSK_012_quyen_hang_doi` |
| 11 | Hàm thuần mục 3: đủ nhánh `parse_sections`, `plan_expiry`, `plan_section_expiry`, `row_errors`, `resolve`, `affected`, `to_flag`, `dismiss_errors`; độ phủ hai module ≥ 90% | — | FR-LIB-007..009 | `tests/unit/test_library_supersession.py`, `tests/unit/test_procedure_review.py` |
| 12 | `check_conventions.py` thoát 0 với DocType và Page mới; nhãn tiếng Việt; chuỗi JS có trong `vi.csv` | — | NFR-MNT-003 | `tests/unit/test_library_ui_conventions.py` (mở rộng nếu cần) |

## 6. Giả định và rủi ro

Giả định ASM-021-01..11 ở `docs/decisions/assumptions/FEAT-021.md`.

Rủi ro:
- Trích dẫn là văn bản tự do (ASM-046): trích dẫn gõ sai số hiệu/mục sẽ không được khớp → quy trình không bị gắn cờ. Giảm thiểu: khớp theo tên bản ghi và số hiệu chuẩn hóa; As-Built ghi giới hạn; đổi sang Link là việc riêng (cần patch chuyển dữ liệu).
- Văn bản B lập lại chỉ mục sau khi khai báo "Một phần": mục giữ tên và `expiry_date` theo `section_no` (ASM-020-12) nên không mất; mục bị xóa khi lập lại thì dòng thay thế trỏ tới mã không còn — chỉ ảnh hưởng hiển thị.
- `refresh_validity` duyệt mọi văn bản/mục (≤ 2.000 văn bản, NFR-SCAL-002); `flag_affected` chỉ chạy khi có chuyển sang Hết và đọc trích dẫn bằng một truy vấn.
- Không gỡ cờ tự động khi người dùng xóa dòng thay thế hoặc sửa `expiry_date`; trưởng khoa kết luận "Không cần sửa".

## 7. Nợ để lại

- NC Procedure Citation `legal_document`, `legal_section` vẫn là Data (ASM-046 hẹn FEAT-020 đổi sang Link nhưng FEAT-020 không đổi). FEAT-021 không đổi cấu trúc DocType của FEAT-006 để giữ phạm vi; Lead quyết có tạo issue riêng không.
