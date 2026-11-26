# As-Built: FEAT-002 Trang chủ, việc chờ xử lý, thông báo, tham số vận hành
- Phiên bản app 0.0.1; Dev: NORM-52; người nghiệm thu: QA (Multica), accepted ở commit d0a4f8129cc2d48d4d19a0bc7f65993dcce796f8

## 1. Luồng nghiệp vụ đã xây
- Thông báo (FR-NOTI-001): `core/notify.py::notify` tạo Notification Log (Alert) kèm liên kết bản ghi; bỏ Administrator, Guest, user tắt; gộp trùng và không tạo lại cùng (người nhận, DocType, bản ghi, tiêu đề). `_notify` của FEAT-007 là lớp mỏng gọi `notify`, test FEAT-007 giữ nguyên và xanh.
- Email (FR-NOTI-002): `notify` gọi `send_notification_email` của Frappe khi người nhận chưa tắt email; không có Email Account gửi đi thì chỉ ghi Error Log, thông báo trong ứng dụng vẫn có (ASM-002-14: Frappe bỏ qua email cho loại "Alert").
- Việc chờ (FR-NOTI-003): suy từ trạng thái bản ghi; nguồn đăng ký ở hook `normcore_pending_sources`; R1 có nguồn "quy trình chờ duyệt" (`api/procedure_workflow.py::pending_for`) cho người qua được `_actor_error` ở hành động tiến (trưởng khoa của khoa; thư ký hội đồng; NC Director).
- Tình trạng chuỗi (FR-OUT-010): `api/home.py` đếm dịch vụ đang hoạt động theo 5 mức loại trừ nhau, lọc khoa trong phạm vi quyền; "Đã duyệt giá" luôn 0, gắn "Giả định — chờ xác nhận" (ASM-002-06). Cột "Tình trạng chuỗi" và bộ lọc ở danh sách dịch vụ (SCR-DSK-005, AMD-004).
- Tham số vận hành (FR-ADM-003): NC Settings thêm 5 trường; `core/settings.get` đọc CSDL mỗi lần gọi (không cache tiến trình).

## 2. DocType tạo mới hoặc thay đổi
- NC Settings: thêm `min_time_study_cases` (5), `price_valid_months` (24), `benchmark_window_months` (24), `min_benchmark_facilities` (3), `accounting_regime` (Hành chính sự nghiệp; tùy chọn khớp `accounting.REGIMES`); ≥ 1; section "Tham số vận hành" đặt trên cùng. Chưa đặt thì `validate` điền mặc định.
- Patch `normcore.patches.nc_settings_operating_defaults` (post_model_sync): đặt mặc định cho trường trống, không ghi đè, chạy lại không đổi. Không thêm DocType.

## 3. API, tác vụ nền, hook, fixtures
- `api/home.py`: `get_home(department)`, `get_service_stages(services)` (≤ 500), `services_in_stage(stage, department)`.
- `core/notify.py`: `notify`, `register_pending_sources`, `pending_for`. `core/settings.py`: `get`, `DEFAULTS`.
- `procedure/chain.py`: `STAGES`, `STAGE_LABELS`, `stage_of`, `count_stages` (thuần Python).
- Hooks: `normcore_pending_sources`, `app_include_js` thêm `nc_chain_dots.js`, `fixtures` thêm Custom HTML Block `NC Trang chủ` (`fixtures/custom_html_block.json`).
- Workspace `Normcore`: block `NC Trang chủ` ngay sau tiêu đề, lối tắt cũ giữ nguyên. `scripts/build_workspace.py` hỗ trợ dòng loại `CustomBlock` trong `shortcuts.txt` và `modified` Workspace được tăng (cần để migrate nạp lại Workspace; FEAT sau đổi Workspace cũng phải tăng).
- Giao diện: SCR-DSK-001 (block), SCR-DSK-005 (cột chấm + bộ lọc, đọc `nc_chain_stage`, `nc_department` trên URL), SCR-DSK-031 (`nc_settings.js`: ghi chú Cấu hình AI, thông báo sau lưu), `vi.csv`.

## 4. Quyền và luồng trạng thái
NC Settings giữ ma trận cũ: NC Admin R/W/C, NC Auditor R; NC Finance và vai trò khác lưu bị `PermissionError` (có test). `get_home`: Guest bị từ chối; người đăng nhập thấy việc của mình; NC Auditor không có việc chờ; mức "đã tính giá" ẩn với vai trò không đọc được NC Service Cost; `department` ngoài phạm vi → `PermissionError`.

## 5. Cấu hình cần thiết khi triển khai
- `bench migrate` (nạp fixture, Workspace, patch) và `bench build --app normcore`.
- Muốn có email: đặt Email Account gửi đi mặc định; người dùng tắt email ở Notification Settings.

## 6. Test case đã chạy và kết quả
TC-NOTI-01 (hai test), TC-ADM-03 **một phần** (phần tham số; phần trung vị thuộc FEAT-014), FR-NOTI-001..003, FR-OUT-010, FR-ADM-003; kết quả lệnh ở `docs/features/FEAT-002/implementation-log.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- `get_home` dùng 9 truy vấn dữ liệu (thiết kế ≤ 6), không phụ thuộc số dịch vụ (ASM-002-16). Chưa đo 300 dịch vụ.
- Giao diện chưa kiểm bằng trình duyệt (QA: nhánh chưa lên staging, không có tài khoản test theo vai trò); chỉ kiểm tĩnh và bằng test bench. Chưa đo 1366 × 768.
- `api/compliance.py`, `api/library.py`, `ai/gateway.py` chưa dùng `notify`.
- Mã cũ đọc thẳng NC Settings (`send_approval_reminders`, `api/compliance.py`) chưa chuyển sang `settings.get`.

## Hợp đồng cho FEAT sau
- Gửi thông báo: `core.notify.notify(users, subject, ref_doctype, ref_name)`.
- Thêm việc chờ: khai hàm `(user) -> list[dict]` ở hook `normcore_pending_sources`; mỗi phần tử có `doctype, name, title, task, state, department, since (ISO), overdue, route`.
- FEAT-014 (bấm giờ) đọc số ca tối thiểu qua `core.settings.get("min_time_study_cases")` và thêm `test_TC_ADM_03_ket_qua_bam_gio_3_ca` (trung vị được tính, hết cảnh báo thiếu ca khi đổi 5 → 3, không khởi động lại).

## Bổ sung NORM-57: liên kết lọc tình trạng chuỗi (SCR-DSK-005, FR-OUT-010)
- Lỗi: liên kết `/app/nc-technical-service?nc_chain_stage=...&nc_department=...` bị Frappe coi là bộ lọc DocType, `reportview.get` trả 417.
- Sửa ở `nc_technical_service_list.js`: `normcore_take_route_params()` đọc hai tham số, gỡ khỏi `frappe.route_options` và URL (`history.replaceState`) trước khi list view dựng truy vấn. Việc này làm ở mỗi lần `before_refresh` (list view được Frappe cache, `onload` chỉ chạy một lần), đặt khoa (chờ ghi xong) rồi mới đặt mức theo liên kết mới và luôn tính lại bộ lọc `name` (kể cả cùng mức, khác khoa); ô chọn mức bị loại khỏi bộ lọc chuẩn của Frappe nên không ghi vào URL. `api/home.py` không đổi.
- Test: `test_FR_OUT_010_lien_ket_tham_so_khong_loi` và `test_FR_OUT_010_lan_vao_thu_hai_khi_list_view_da_cache` (ba lần vào: (a,K01), (a,K02), (b,K03); stub Frappe: bỏ qua set_value cùng giá trị, Link ghi bất đồng bộ; `normcore/tests/test_feat_002.py`, chạy đoạn JS bằng node; kiểm cả loại `nc_chain_stage` khỏi bộ lọc chuẩn).
