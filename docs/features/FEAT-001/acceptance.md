# Acceptance FEAT-001 — Kiểm định độc lập (NORM-14)

Kết luận: **chưa nghiệm thu (ghi `rework` trong verdict.json vì không có giá trị "chờ")**. Mã, test, quyền đều đạt; không có lỗi mã. Chưa được `accepted` vì giao diện màn hình quản trị khoa (SCR-DSK-031, nút Gán/Bỏ gán) chưa kiểm bằng trình duyệt.

## Môi trường kiểm
Nhánh `ai/NORM-14-verify-006-001-004` từ `develop` 98d21fe; site sạch `normcore-verify.test` (đã xóa sau khi kiểm).

| Lệnh | Kết quả |
| :-- | :-- |
| `bench --site normcore-verify.test run-tests --app normcore` | 148 test, OK (147 trước khi QA thêm 1 test) |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 69 passed, độ phủ 98,9% |
| `python3 docs/golden/golden_engine.py` / `--no-depr` / `golden_cls.py` | thoát 0, số khớp |
| `python3 scripts/check_conventions.py` | thoát 0 |
| `python3 docs/tools/build_rtm.py docs` | thoát 0, `VAN DE: 0`; 12 ghi chú có sẵn (DEF-001) |
## Độ phủ tiêu chí

| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| TC-ACC-01 (Clinician K01 không sửa nháp K02; đã ban hành K02 vẫn đọc) | 5 test `test_TC_ACC_01_*`: sửa/tạo/add_step/make_norm_set bị `PermissionError`; không kéo bản ghi khác khoa về khoa mình; đọc bản đã ban hành; cả NC Clinician lẫn NC Department Head. Chạy tay trên site verify cùng kết quả | Đạt |
| TC-ACC-02 (Clinician: danh sách trống / API lỗi quyền cho số liệu kế toán) | `test_TC_ACC_02_*`: `get_list` và `client.get_list` ném `PermissionError` trên NC Costing Run, NC Service Cost. NC Accounting Import / NC Reconciliation Line chưa có (FEAT sau) nên dùng DocType số liệu hiện có; TC nói "danh sách trống hoặc lỗi quyền", test kiểm lỗi quyền | Đạt (thay thế DocType) |
| TC-ACC-03 (RM mở link trực tiếp: không đủ quyền, không lộ trường) | `test_TC_ACC_03_*`: `client.get` và `getdoc` ném `PermissionError`, thông báo không chứa tiêu đề/năm, `response.docs` rỗng. Chạy tay K01→bản nháp K02: `PermissionError ('read', 'NC Clinical Procedure', ...)`, docs = None | Đạt |
| TC-ACC-04 (quét quyền, không "All", khớp ma trận) | `unit/test_permission_matrix.py` (7 test, gồm ma trận sai, thiếu cột, "All") + `test_permissions` quét 16 DocType × 10 vai trò × 4 quyền | Đạt |
| TC-ACC-05 (chưa đăng nhập: API lỗi, Desk về /login) | `test_TC_ACC_05_guest_bi_tu_choi`, `..._desk_chuyen_ve_trang_dang_nhap` (3xx về `/login`) | Đạt |
| TC-ADM-04 (khoa thiếu loại bị từ chối; K03 CLS gắn trung tâm chi phí) | 3 test; thiếu từng trường bắt buộc, K03 lưu và `cost_center` đúng; trung tâm chi phí thiếu trường bị `MandatoryError` | Đạt |
| TC-ADM-05 (xóa mục đang tham chiếu bị từ chối, nêu bản ghi) | 3 test; chạy tay: "Không xóa được NC Job Title DDV vì đang được tham chiếu bởi: NC Clinical Procedure QT-DVV1-KV1-v1, ..." | Đạt |
| DocType mới NC Cost Center: vai trò không quyền + NC Auditor chỉ đọc | `test_permissions` (Auditor chỉ đọc 15 DocType cha, vai trò ngoài ma trận bị từ chối); `test_TC_ACC_01_auditor_*` đọc mọi khoa không ghi, không gán khoa | Đạt |
| Giao diện SCR-DSK-031 ở 1366×768, `vi` | Không có trình duyệt | **Chưa kiểm** |

## Kiểm trực tiếp (site verify)
Tạo KV1, KV2; NC Admin gán Clinician vào KV1 (trả True). Clinician: sửa nháp KV2 = False; đọc quy trình đã ban hành KV2 = True; danh sách có 3 bản (không có nháp KV2); mở thẳng nháp KV2 → `PermissionError`, không lộ nội dung; xóa NC Job Title đang tham chiếu → `LinkExistsError`.

## Soát diff test và tài liệu
- Commit `40c3c05` "sửa setUp test cũ theo ASM-026": chỉ thêm `access.assign_department(self.clin, self.dept)` và dòng import vào `setUp` của `api/test_procedure.py`. Là dữ liệu dựng; không đổi assertion. Hợp lệ (nhưng ASM trong tên commit là 026, nay là ASM-043 G5).
- `test_co_14_doctype` → `test_co_16_doctype` (ASM-037, người duyệt đã đồng ý): chỉ đổi số.
- Không sửa tài liệu chỉ đọc. Sửa `.github/workflows/ci.yml` (cài openpyxl, theo người duyệt NORM-13): lệnh hạ tầng, chấp nhận.

## ASM-042: kết luận rõ
- Phạm vi khoa dùng User Permission `applicable_for="NC Cost Center"`; bộ lọc mặc định của Frappe không kích hoạt vì NC Cost Center chưa có Link tới NC Department. Phạm vi thật do hook `core/permissions.py` quyết định, không phụ thuộc chỗ đó.
- Kiểm: người có NC Resource Manager + NC Clinician gán KV1 đọc được nháp KV2 (đúng ASM-043/G4 và FR-ACC-003, vì FR chỉ giới hạn người *chỉ có* Clinician/Dept Head và chỉ giới hạn *sửa*). Người chỉ có NC Clinician: không đọc được NC Costing Run (`PermissionError`), NC Job Title; đọc toàn bộ NC Department/Cost Center/Technical Service (FR không giới hạn đọc các danh mục này).
- **Không phải lỗi hiện tại.** Là rủi ro của FEAT sau: mỗi DocType mới thuộc FR-ACC-003/008 (phiếu bấm giờ, hệ thống xét nghiệm, kế hoạch chất lượng) phải thêm một dòng vào `SCOPE_RULES` và `hooks.py`; quên thì Clinician sửa được toàn viện. Nên có test quét bắt buộc (mỗi DocType có trường khoa phải nằm trong SCOPE_RULES).

## ASM-037..045
Không dòng nào trái FR/TC. Lưu ý: ASM-039 chặn đọc bản nháp/bộ định mức của khoa khác, hẹp hơn FR-ACC-003 (chỉ nói quyền sửa) nhưng người duyệt đã chốt và TC-ACC-01 không mâu thuẫn. ASM-040 (ma trận NC Cost Center) chưa có dòng tương ứng trong `data-model.md` mục 4; chờ xác nhận, không sai test.

## Việc còn lại (người duyệt tự bấm, 1366×768, `vi`)
SCR-DSK-031 → tạo 2 khoa; mở người dùng → "Gán khoa" K01; đăng nhập người đó: sửa được quy trình K01, không sửa được nháp K02, mở được bản đã ban hành K02; dán link nháp K02 → thông báo không đủ quyền; xóa mục đang tham chiếu → thông báo nêu bản ghi; nút "Bỏ gán" hoạt động (sửa ở fe8314f); không vỡ bố cục, không cuộn ngang.
