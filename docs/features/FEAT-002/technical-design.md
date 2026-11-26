# FEAT-002 — Trang chủ, việc chờ xử lý, thông báo, tham số vận hành — Thiết kế kỹ thuật

Issue NORM-52. Nguồn: `srs.md` FR-NOTI-001, FR-NOTI-002, FR-NOTI-003, FR-OUT-010, FR-ADM-003; `use-cases.md` UC-018 (bước 1–3; bước 4 tra cứu nhật ký đã có ở FEAT-003); `data-model.md` 3.1 NC Settings, mục 4; `architecture.md` khối NC Core, `core/notify.py`; `ux-foundations.md` SCR-DSK-001, SCR-DSK-031, SCR-DSK-005 (cột và bộ lọc tình trạng chuỗi theo AMD-004), thành phần "Thẻ tình trạng chuỗi"; TC-NOTI-01, TC-ADM-03. Phụ thuộc FEAT-007 (DONE, `docs/as-built/FEAT-007.md`).

Giả định: `docs/decisions/assumptions/FEAT-002.md` (ASM-002-01..12). Không có AMD mới: không thêm DocType, chỉ thêm trường đã có trong `data-model.md` 3.1 vào NC Settings. Câu hỏi chờ Lead: Q1 (mục 9, TC-ADM-03).

## 1. Phạm vi

| FR | Làm gì ở FEAT này |
| :-- | :-- |
| FR-NOTI-001 | `core/notify.py::notify` là điểm tạo thông báo chung (Notification Log, liên kết bản ghi). Luồng duyệt FEAT-007 chuyển sang gọi `notify` (giữ `_notify` là lớp mỏng, cùng người nhận, cùng tiêu đề, cùng chống trùng) |
| FR-NOTI-002 (Should) | Email cho mỗi thông báo qua cơ chế sẵn có của Frappe (Notification Log `after_insert` → `send_notification_email`, có đường dẫn tới bản ghi) khi site có Email Account gửi đi mặc định; không có thì chỉ có thông báo trong ứng dụng, không lỗi (ASM-002-02) |
| FR-NOTI-003 | Danh sách "Việc chờ xử lý" của người đang đăng nhập trên trang chủ, suy từ trạng thái hiện tại của bản ghi (không từ thông báo chưa đọc). Nguồn việc đăng ký qua hook `normcore_pending_sources`; R1 có nguồn "quy trình chờ duyệt" (ba cấp FEAT-007) |
| FR-OUT-010 (Should) | Đếm dịch vụ đang hoạt động theo năm mức tình trạng chuỗi, loại trừ nhau theo mức cao nhất đã đạt; lọc theo khoa trong phạm vi quyền. Thêm cột "Tình trạng chuỗi" và bộ lọc ở SCR-DSK-005 (AMD-004) |
| FR-ADM-003 | NC Settings thêm các trường còn lại của `data-model.md` 3.1; `core/settings.py::get` đọc giá trị mỗi lần gọi, không cache ở tiến trình. Ba tham số FR nêu: `min_time_study_cases` (NC Settings, mới), `approval_reminder_days` (NC Settings, FEAT-007), thời hạn gọi AI `NC AI Settings.timeout_seconds` (FEAT-023, ASM-002-09). Có test "đổi rồi áp ngay, không khởi động lại" cho cả ba |

Không làm: logic bấm giờ, trung vị, cảnh báo thiếu ca (FEAT-014; xem Q1); duyệt bộ định mức, duyệt giá (FEAT sau đăng ký nguồn việc và mức "đã duyệt giá" khi có DocType); tra cứu nhật ký (FEAT-003 đã làm); quản lý khoa, trung tâm chi phí, phạm vi khoa ở SCR-DSK-031 (FEAT-001 đã làm); trang nhập Excel (FEAT-004). Không chuyển các thông báo của `api/compliance.py`, `api/library.py`, `ai/gateway.py` sang `notify` (không refactor ngoài phạm vi, ghi nợ ở As-Built).

Dùng lại, không làm lại: `api/procedure_workflow.py` (`_recipients`, `_actor_error`, `apply_action`, `send_approval_reminders`), `procedure/approval.py` (`PENDING_STATES`, `TRANSITIONS`), `procedure/chain.py` (`pick_procedures`, `pick_norm_sets`, `pick_costs`), `api/service.py` (`_procedure_rows`, `_norm_rows`, `_cost_rows`), `core/permissions.py::readable_departments`, Workspace `Normcore` (module NC Core).

## 2. DocType

### 2.1 Đổi — NC Settings (Single, module NC Core; đã có từ FEAT-033, FEAT-007)

Thêm đúng các trường của `data-model.md` 3.1 còn thiếu. Không đổi trường cũ. Nhóm thành Section mới "Tham số vận hành" đặt trên cùng.

| Fieldname | Nhãn | Kiểu | Mặc định | Ràng buộc (validate) |
| :-- | :-- | :-- | :-- | :-- |
| min_time_study_cases | Số ca bấm giờ tối thiểu | Int | 5 | ≥ 1 — "Số ca bấm giờ tối thiểu phải lớn hơn 0" |
| price_valid_months | Hạn tham chiếu đơn giá (tháng) | Int | 24 | ≥ 1 |
| benchmark_window_months | Cửa sổ giá tham chiếu (tháng) | Int | 24 | ≥ 1 |
| min_benchmark_facilities | Số đơn vị tham chiếu tối thiểu | Int | 3 | ≥ 1 |
| accounting_regime | Chế độ kế toán | Select | Hành chính sự nghiệp | Tùy chọn lấy từ `costing/accounting.py::REGIMES` ("Hành chính sự nghiệp", "Doanh nghiệp"); viết cứng trong JSON, có test so khớp với `REGIMES` |

- Mỗi trường mới có `description` tiếng Việt nêu FR dùng nó. `min_time_study_cases`: "Áp dụng cho lần mở kết quả bấm giờ kế tiếp (FR-ADM-003, FR-TS-*)".
- Quyền: giữ như hiện tại (NC Admin R/W/C, NC Auditor R; ASM-099). Vai trò khác không đọc form; đọc giá trị qua `core/settings.get` ở máy chủ.
- `track_changes` đã bật (giữ). Đổi giá trị ghi vào sổ sự kiện qua `core/audit.py` như hiện tại.
- Patch `normcore/patches/v0_0/nc_settings_operating_defaults.py` (khai trong `patches.txt` mục `[post_model_sync]`): với mỗi trường mới đang trống trên site, đặt mặc định ở bảng trên (`frappe.db.set_single_value`). Không ghi đè giá trị đã có. Chạy lại không đổi gì (idempotent).

### 2.2 Notification Log (Frappe, không đổi cấu trúc)

Dùng `type = "Alert"`, `document_type`, `document_name` (Frappe dựng liên kết `/app/<doctype>/<name>` trong chuông và email), `subject`, `for_user`, `from_user`.

### 2.3 Workspace `Normcore` (đã có)

Thêm một Custom HTML Block `NC Trang chủ` (fixture, module NC Core) ở đầu `content`, trước các lối tắt hiện có. Không xóa lối tắt cũ. Chi tiết trong `ui-design.md`.

## 3. Thành phần

### 3.1 `normcore/core/notify.py` (mới)

```python
SKIP_USERS = ("Administrator", "Guest")

def notify(users, subject, ref_doctype, ref_name, from_user=None) -> int:
    """Notification Log (Alert) cho từng người; trả số thông báo đã tạo."""

def register_pending_sources() -> list[callable]:
    """Đọc frappe.get_hooks("normcore_pending_sources"), trả hàm đã import; bỏ đường dẫn lỗi (log_error)."""

def pending_for(user=None) -> list[dict]:
    """Gộp việc chờ từ mọi nguồn; sắp theo `since` tăng dần (việc chờ lâu nhất lên đầu)."""
```

- `notify`: bỏ người trống, `SKIP_USERS`, user `enabled = 0`; gộp trùng trong danh sách (giữ thứ tự); không tạo nếu đã có Notification Log cùng `(for_user, document_type, document_name, subject)` (cùng quy tắc ASM-007-01, thêm `document_type` để không trùng nhầm giữa DocType). `insert(ignore_permissions=True)`. `from_user` mặc định `frappe.session.user`.
- Email (FR-NOTI-002) không có mã riêng trong `notify`: Frappe gửi trong `after_insert` của Notification Log khi Notification Settings của người nhận bật email (mặc định bật). ASM-002-02.
- Mỗi phần tử việc chờ (hợp đồng chung cho mọi nguồn, FEAT sau theo đúng khóa này):

| Khóa | Kiểu | Ý nghĩa |
| :-- | :-- | :-- |
| `doctype`, `name` | str | Bản ghi |
| `title` | str | Tên hiển thị (ví dụ tên dịch vụ + khoa) |
| `task` | str | Việc cần làm, tiếng Việt ("Duyệt cấp trưởng khoa", "Thẩm định cấp hội đồng", "Ban hành") |
| `state` | str | Trạng thái hiện tại |
| `department` | str \| None | Mã khoa của bản ghi (để lọc theo khoa) |
| `since` | str ISO date | Ngày vào trạng thái chờ |
| `overdue` | bool | Quá `approval_reminder_days` (chỉ với nguồn có ngưỡng; nguồn khác `False`) |
| `route` | str | `/app/...` hoặc route Desk Page mở thẳng bản ghi (FEAT-007: chế độ thẩm định `procedure-editor/<name>`) |

### 3.2 Nguồn việc "quy trình chờ duyệt" — `api/procedure_workflow.py::pending_for(user)` (thêm)

- Lấy `NC Clinical Procedure` có `workflow_state` trong `approval.PENDING_STATES` bằng `frappe.get_all` (không qua quyền danh sách, vì Council và Director chỉ có R; quyết định ai được làm bằng `_actor_error`).
- Giữ bản ghi khi người đó làm được hành động tiến của trạng thái: `_actor_error(doc, <hành động tiến>, user) is None` (Đồng ý / Thông qua / Ban hành; bảng `approval.TRANSITIONS`). Như vậy trưởng khoa chỉ thấy quy trình của khoa mình; ở cấp hội đồng chỉ thư ký hội đồng (`NC Settings.council_secretary`, AMD-007-01) có việc; ở cấp ban hành mọi NC Director — đúng người làm được hành động, không lệch với nút duyệt. (Thông báo "Đồng ý" vẫn gửi mọi Council Member như FEAT-007; danh sách việc chỉ của thư ký: ASM-002-04.)
- Tối ưu: lọc trước theo vai trò (không có vai trò của cấp nào thì không đọc bản ghi cấp đó); với trưởng khoa lọc `department in get_user_departments(user)`. Đọc `doc` nhẹ bằng `frappe.get_doc` chỉ cho bản ghi qua bộ lọc.
- `since` = ngày vào trạng thái theo `_entered_on` (FEAT-007, đọc sổ sự kiện); `overdue` = `approval.overdue(...)` với `core/settings.get("approval_reminder_days")`.
- `route` = `/app/procedure-editor/<name>` (mở chế độ thẩm định FEAT-007, cùng route nút ở form quy trình).
- `hooks.py`: `normcore_pending_sources = ["normcore.api.procedure_workflow.pending_for"]`.
- `_notify` của FEAT-007 thành lớp mỏng: `return notify.notify(users, subject, DT, doc.name)`. Không đổi người nhận, tiêu đề; test FEAT-007 giữ nguyên và phải xanh.

### 3.3 `normcore/core/settings.py` (mới)

```python
DEFAULTS = {"min_time_study_cases": 5, "approval_reminder_days": 7, "price_valid_months": 24,
            "benchmark_window_months": 24, "min_benchmark_facilities": 3,
            "accounting_regime": "Hành chính sự nghiệp", "compliance_reminder_days": 30}

def get(fieldname):
    """Giá trị NC Settings hiện hành; trống thì DEFAULTS. Đọc `frappe.db.get_single_value` mỗi lần gọi."""
```

- Không lưu vào biến mô-đun, không `lru_cache`. Cache single của Frappe tự xóa khi lưu NC Settings → lần gọi kế tiếp (cùng hay khác tiến trình worker) thấy giá trị mới.
- Trường không có trong `DEFAULTS` → `KeyError` (lỗi lập trình, có test).
- Mã cũ đang đọc thẳng (`send_approval_reminders`, `api/compliance.py`) không bắt buộc đổi; `pending_for` mới dùng `settings.get`. FEAT-014 (bấm giờ) đọc `settings.get("min_time_study_cases")` (ghi vào As-Built mục "Hợp đồng cho FEAT sau").

### 3.4 Logic thuần — `normcore/procedure/chain.py` (mở rộng, không import `frappe`)

```python
STAGES = ("no_procedure", "procedure", "norm_locked", "costed", "price_approved")
STAGE_LABELS = {"no_procedure": "Chưa có quy trình", "procedure": "Có quy trình",
                "norm_locked": "Có định mức đã khóa", "costed": "Đã tính giá",
                "price_approved": "Đã duyệt giá"}

def stage_of(has_procedure, has_norm, has_cost, has_price=False) -> str
def count_stages(service_flags, readable=STAGES) -> list[dict]
```

- `stage_of`: mức cao nhất đạt được theo thứ tự `STAGES` (ASM-002-05). Ví dụ có định mức khóa mà không có quy trình hiện hành (dữ liệu cũ) → `norm_locked`.
- `count_stages`: vào là list `(service, has_procedure, has_norm, has_cost, has_price)`; `readable` là các mức người xem có quyền thấy. Mức không đọc được: cờ tương ứng coi như `False` trước khi tính `stage_of` (dịch vụ rơi về mức cao nhất người đó thấy được) và mục trả `{"stage", "label", "count": None, "no_permission": True}`. Ra đủ 5 mục theo thứ tự `STAGES`, mỗi mục `{stage, label, count, no_permission}`, `count` là số nguyên (0 nếu không có).
- `price_approved`: R1 chưa có DocType phương án giá đã duyệt → cờ luôn `False`, mục mang `assumption: True` để giao diện gắn "Giả định — chờ xác nhận" như `chain.price_item()` (ASM-002-06).

### 3.5 API whitelisted — `normcore/api/home.py` (mới)

| Hàm | Tham số | Kết quả | Kiểm quyền / lỗi |
| :-- | :-- | :-- | :-- |
| `get_home(department=None)` | `department`: mã NC Department hoặc trống | `{"pending": [...], "stages": [...], "departments": [{"name","department_name"}], "department": <đang lọc>}` | Đăng nhập (không Guest → `PermissionError`). `pending` luôn của chính người gọi. `stages`: nếu không có quyền đọc `NC Technical Service` → `stages = []`. `department` ngoài phạm vi khoa của người bị hẹp → `PermissionError` "Khoa này ngoài phạm vi của bạn". `department` không tồn tại → `DoesNotExistError` |
| `get_service_stages(services)` | JSON list mã dịch vụ (≤ 500) | `{<service>: {"stage", "dots": [{key, state, indicator}]×4}}` | Bỏ dịch vụ không đọc được; > 500 → `ValidationError`. Dùng cho cột SCR-DSK-005 |
| `services_in_stage(stage, department=None)` | `stage` ∈ `STAGES` | list mã dịch vụ | `stage` sai → `ValidationError`; `stage` người gọi không có quyền thấy → `[]`. Dùng cho bộ lọc SCR-DSK-005 |

Cách tính tập dịch vụ và cờ (một hàm nội bộ `_service_flags(department)` dùng chung cho ba API, truy vấn gộp, không lặp theo dịch vụ):

1. Dịch vụ: `frappe.get_list("NC Technical Service", {"is_active": 1}, ...)` (quyền chuẩn). Khoa của dịch vụ: bảng con `NC Service Department`.
2. Phạm vi khoa (ASM-002-07): `readable_departments(<DocType nguồn>)` cho từng nguồn (quy trình, định mức, giá thành). Người bị hẹp theo khoa (Clinician, Dept Head): chỉ đếm dịch vụ có ít nhất một khoa thực hiện trong phạm vi; cờ chỉ xét bản ghi thuộc khoa trong phạm vi. Có `department`: chỉ dịch vụ có khoa đó trong `NC Service Department` và cờ chỉ xét bản ghi của khoa đó.
3. Cờ: `has_procedure` = có bản "Đã ban hành" (`chain.pick_procedures`, kể cả chưa tới ngày hiệu lực? **không**: chỉ bản đã hiệu lực, `not_effective = False`); `has_norm` = có NC Norm Set "Đã khóa"; `has_cost` = `chain.pick_costs` không rỗng. Truy vấn mỗi DocType nguồn một lần cho mọi dịch vụ (`technical_service in [...]`), dùng `frappe.get_list` để giữ quyền; nhóm theo dịch vụ ở Python.
4. Mức đọc được: `procedure` cần đọc NC Clinical Procedure; `norm_locked` cần NC Norm Set; `costed` cần NC Service Cost và NC Costing Run; `price_approved` R1 luôn đọc được (đều 0). `no_procedure` luôn đọc được khi đọc được dịch vụ. Theo ASM-047: mục không đọc được hiện "Không có quyền xem", không số.

Hiệu năng (NFR-PERF-001): ≤ 6 truy vấn cho `get_home` bất kể số dịch vụ; test với 300 dịch vụ hoàn tất < 2 giây trên bench dev (ghi số đo vào implementation-log, không assert thời gian trong CI).

### 3.6 Bản dịch

Mọi chuỗi mới qua `_()`/`__()`; thêm vào `normcore/translations/vi.csv` theo thứ tự quy ước hiện có (`test_vi_csv_order`).

## 4. Quyền

| Đối tượng | Ai | Ghi chú |
| :-- | :-- | :-- |
| NC Settings | NC Admin R/W/C; NC Auditor R; vai trò khác không có | Giữ nguyên (ASM-099). Test: NC Finance (không quyền) lưu → `PermissionError`; NC Auditor đọc được, lưu → `PermissionError` |
| `get_home` | Mọi người dùng đã đăng nhập có một vai trò NC | Guest → `PermissionError`. NC Auditor: `pending = []` (không có hành động duyệt), `stages` theo quyền đọc |
| `get_service_stages`, `services_in_stage` | Người đọc được NC Technical Service | Từng mức theo quyền đọc DocType nguồn và phạm vi khoa |
| Notification Log | Frappe (người nhận đọc thông báo của mình) | Không đổi |

Không có DocType mới nên không thêm dòng ma trận.

## 5. Tiêu chí nghiệm thu

| # | Điều kiện kiểm được | TC | FR | Test |
| :-: | :-- | :-- | :-- | :-- |
| 1 | Clinician gửi duyệt quy trình của khoa K; `head_user` của K có đúng 1 Notification Log `document_type = NC Clinical Procedure`, `document_name` = quy trình; gọi `get_home()` bằng trưởng khoa → `pending` có phần tử của quy trình đó, `task = "Duyệt cấp trưởng khoa"`, `route` mở bản ghi | TC-NOTI-01 | FR-NOTI-001, FR-NOTI-003 | `test_TC_NOTI_01_gui_duyet_thong_bao_va_trang_chu_truong_khoa` (`normcore/api/test_home.py`) |
| 2 | Cùng dữ liệu: trưởng khoa của khoa khác và NC Finance có `pending` không chứa quy trình; sau "Đồng ý", trưởng khoa không còn việc đó, thư ký hội đồng thấy việc, Council Member khác không thấy | TC-NOTI-01 (ca âm) | FR-NOTI-003 | `test_TC_NOTI_01_viec_cho_dung_nguoi` |
| 3 | `notify` bỏ Administrator, Guest, user tắt, gộp trùng; gọi lại cùng tiêu đề không tạo thêm | — | FR-NOTI-001 | `test_FR_NOTI_001_notify_*` (`normcore/core/test_notify.py`) |
| 4 | Có Email Account gửi đi mặc định (tạo trong test, `frappe.sendmail` được patch): `notify` cho một người → `sendmail` được gọi với `recipients` = email người đó, nội dung chứa đường dẫn `/app/nc-clinical-procedure/<name>`; không có Email Account → Notification Log vẫn tạo, không ném lỗi | — | FR-NOTI-002 | `test_FR_NOTI_002_email_khi_co_may_chu`, `test_FR_NOTI_002_khong_may_chu_van_thong_bao` |
| 5 | `stage_of`, `count_stages`: đủ 5 mức, loại trừ nhau, mức không đọc được → `count None`, dịch vụ rơi về mức thấp hơn | — | FR-OUT-010 | `test_FR_OUT_010_*` (`normcore/tests/unit/test_chain_stages.py`) |
| 6 | Dữ liệu 5 dịch vụ ở 4 mức (không, có QT, ĐM khóa, đã tính): `get_home()` của NC Finance trả số 1/1/1/1(+…)/0 đúng từng mức; `get_home(department=K)` chỉ đếm dịch vụ của K; Clinician khoa K: chỉ dịch vụ của K, mục "Đã tính giá" `no_permission`; `department` ngoài phạm vi → `PermissionError` | — | FR-OUT-010 | `test_FR_OUT_010_dem_theo_tinh_trang_chuoi`, `test_FR_OUT_010_loc_khoa_va_pham_vi` |
| 7 | `services_in_stage("norm_locked")` trả đúng tập; `get_service_stages` > 500 mã → `ValidationError` | — | FR-OUT-010 (SCR-DSK-005, AMD-004) | `test_FR_OUT_010_bo_loc_danh_sach_dich_vu` |
| 8 | NC Admin đổi `min_time_study_cases` 5 → 3 và lưu; `settings.get("min_time_study_cases")` trả 3 ngay ở lời gọi kế tiếp, không `clear_cache`, không khởi động lại. **Phần "trung vị, cảnh báo thiếu ca" chờ Q1** | TC-ADM-03 (xem Q1) | FR-ADM-003 | `test_TC_ADM_03_doi_so_ca_toi_thieu_ap_ngay` (`normcore/nc_core/doctype/nc_settings/test_nc_settings.py`) |
| 9 | Đổi `approval_reminder_days` 7 → 2: quy trình chờ 3 ngày được nhắc ở lần `send_approval_reminders` kế tiếp và `pending_for` có `overdue = True`; đổi `NC AI Settings.timeout_seconds` 180 → 30: lần gọi gateway kế tiếp (provider giả lập) nhận `timeout = 30` | — | FR-ADM-003 | `test_FR_ADM_003_so_ngay_nhac_ap_ngay`, `test_FR_ADM_003_thoi_han_ai_ap_ngay` |
| 10 | NC Settings: mặc định đúng bảng 2.1; giá trị ≤ 0 bị từ chối với thông báo tiếng Việt; tùy chọn `accounting_regime` = `accounting.REGIMES`; patch đặt mặc định khi trống, không ghi đè, chạy lại không đổi | — | FR-ADM-003 | `test_nc_settings_*` |
| 11 | Quyền: NC Finance lưu NC Settings → `PermissionError`; NC Auditor đọc được, lưu → `PermissionError`; Guest gọi `get_home` → `PermissionError` | — | FR-ADM-003, FR-ACC-007 | `test_quyen_nc_settings_*`, `test_quyen_get_home_guest` |
| 12 | Test FEAT-007 (`api/test_procedure_workflow.py`, `test_procedure_workflow_jobs.py`) giữ nguyên, xanh sau khi `_notify` gọi `core/notify` | — | FR-NOTI-001 | chạy lại module cũ |

## 6. Giả định

`docs/decisions/assumptions/FEAT-002.md`:

- ASM-002-01 `core/notify.notify` là điểm chung; chỉ luồng duyệt FEAT-007 chuyển sang dùng ở FEAT này.
- ASM-002-02 Email dùng cơ chế Notification Log của Frappe; "máy chủ email được cấu hình" = có Email Account gửi đi mặc định.
- ASM-002-03 Việc chờ suy từ trạng thái bản ghi, nguồn đăng ký qua hook `normcore_pending_sources`; R1 chỉ nguồn quy trình chờ duyệt.
- ASM-002-04 Người có việc = người qua được `_actor_error` cho hành động tiến của trạng thái.
- ASM-002-05 Năm mức tình trạng chuỗi loại trừ nhau theo mức cao nhất.
- ASM-002-06 "Đã duyệt giá" R1 luôn 0, gắn "Giả định — chờ xác nhận".
- ASM-002-07 Phạm vi khoa và quyền mức theo ASM-047; dịch vụ rơi về mức cao nhất đọc được.
- ASM-002-08 "Có quy trình" = có bản "Đã ban hành" đã tới ngày hiệu lực.
- ASM-002-09 Thời hạn gọi AI giữ ở NC AI Settings (FEAT-023), không nhân đôi vào NC Settings.
- ASM-002-10 Trang chủ = Workspace `Normcore` + Custom HTML Block; lối tắt theo vai trò dùng cơ chế lọc theo quyền sẵn có của Workspace.
- ASM-002-11 Ràng buộc ≥ 1 cho các tham số Int mới; tùy chọn `accounting_regime` theo `accounting.REGIMES`.
- ASM-002-12 Cột/bộ lọc tình trạng chuỗi ở SCR-DSK-005 tính khi hiển thị, không lưu trường (AMD-004, ASM-047).

## 7. Tệp dự kiến đổi

Mới: `normcore/core/notify.py`, `normcore/core/settings.py`, `normcore/api/home.py`, `normcore/api/test_home.py`, `normcore/core/test_notify.py`, `normcore/tests/unit/test_chain_stages.py`, `normcore/nc_core/doctype/nc_settings/test_nc_settings.py` (nếu chưa có; có thì thêm test), `normcore/nc_core/custom_html_block/nc_trang_chu/*` (fixture), `normcore/public/js/nc_chain_dots.js` (thành phần dùng chung SCR-DSK-001/005), `normcore/patches/v0_0/nc_settings_operating_defaults.py`.
Đổi: `normcore/procedure/chain.py`, `normcore/api/procedure_workflow.py` (`_notify`, `pending_for`), `nc_settings.json`/`.py`/`.js`, `nc_technical_service_list.js`, Workspace `normcore.json`, `hooks.py` (`normcore_pending_sources`, `app_include_js` nếu cần, `fixtures` Custom HTML Block), `patches.txt`, `translations/vi.csv`, `docs/decisions/assumptions/FEAT-002.md`, As-Built, Test ref.

## 8. Rủi ro

- Frappe tự gửi email khi không có Email Account → `OutgoingEmailError` được Frappe bắt và ghi Error Log mỗi thông báo. Chấp nhận (không lỗi người dùng); As-Built ghi cách tắt email trong Notification Settings.
- Custom HTML Block chạy script trong shadow DOM: không dùng được CSS Desk ngoài biến CSS; dùng `frappe.call` và biến `--*` của Desk (design.md). Nếu Workspace không nạp block ở bản Frappe trên bench, phương án lùi: Desk Page `nc-home` và đặt `desktop:home_page` — báo Lead trước khi đổi (là sửa UX).
- Đổi `_notify` có thể làm lệch test FEAT-007 nếu khóa chống trùng thêm `document_type` — cùng DocType nên không đổi kết quả; test cũ là chuẩn.
- Số dịch vụ lớn: bộ lọc `name in [...]` của SCR-DSK-005 dài; giới hạn 2.000 mã, quá thì báo "Lọc theo khoa trước" (ui-design).

## 9. Câu hỏi chờ Lead

**Q1 — TC-ADM-03 khi FEAT-014 chưa DONE.** TC-ADM-03 (test-cases.md): "Đổi số ca bấm giờ tối thiểu từ 5 thành 3; mở kết quả bấm giờ của một dịch vụ có 3 ca → Trung vị được tính và không còn cảnh báo thiếu ca; không cần khởi động lại dịch vụ". Kết quả bấm giờ, trung vị, cảnh báo thiếu ca là của FEAT-014 (NORM-49, đang Blocked, không phải phụ thuộc trong build-order). Mô tả NORM-52 cấm BA tự dựng logic bấm giờ.

- **PA1 (đề xuất):** FEAT-002 làm trường `min_time_study_cases`, `core/settings.get` và `test_TC_ADM_03_doi_so_ca_toi_thieu_ap_ngay` ở mức tham số (dòng 8 mục 5). Phần "mở kết quả bấm giờ 3 ca → có trung vị, hết cảnh báo" chuyển cho FEAT-014: FEAT-014 đọc qua `settings.get` và thêm test cùng mã `test_TC_ADM_03_ket_qua_bam_gio_3_ca`. QA FEAT-002 nghiệm thu TC-ADM-03 "một phần", ghi rõ trong acceptance; RTM ghi Test ref ở cả hai FEAT. Không chặn FEAT-002.
- PA2: giữ task TC-ADM-03 của FEAT-002 mở, chỉ làm sau khi FEAT-014 DONE (FEAT-002 không vào QA được tới lúc đó).
- PA3: tách TC-ADM-03 thành issue riêng phụ thuộc FEAT-014; FEAT-002 làm như PA1 phần tham số.

tasks.md viết theo PA1 (T09); nếu Lead chọn khác, BA sửa T09 và dòng 8 mục 5.
