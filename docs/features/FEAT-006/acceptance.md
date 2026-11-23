# Acceptance FEAT-006 — Kiểm định lại sau NORM-15 và NORM-22 (NORM-16)

Kết luận: **rework — lỗi mã nguồn ở giao diện trình soạn ().** Phần A đạt. Phần B (Playwright trên staging, bản có NORM-22 và NORM-23): L1, E15 (do NORM-23), G1, C1–C5 và các thao tác đơn lẻ đạt; nhưng  và  gọi `.finally` trên promise của `frappe.call` (jQuery Deferred, không có `.finally`) nên ném `TypeError`: (1) cờ `busy` không bao giờ về false, mọi nút ghi (Lên, Xuống, Xóa, Lưu, Lưu phần) bị khóa sau thao tác ghi đầu tiên cho tới khi tải lại trang; (2) dòng "Đang tải…" không tắt; (3) sau khi **tạo/sao chép thành công** vẫn hiện dải lỗi đỏ "Dịch vụ đã có quy trình cho khoa này". K3 không đạt vì nguyên nhân này. Không ghi Test ref, As-Built, `DONE`.

Bằng chứng Phần B: kịch bản Playwright (Chromium headless, 1366×768, locale `vi`) chạy qua `~/pw-venv/run.sh` trên http://112.213.88.40:8100 (staging chứa `d0b4fe1`, gồm `c70a15c`), ảnh theo mã đính kèm ở bình luận NORM-16. Theo ASM-099 (Quyết định Lead), kết quả này thay cho câu trả lời của người duyệt.

## Môi trường kiểm
Nhánh `ai/NORM-16-reverify-006` = `origin/develop` (đã chứa PR #27, merge 927d54f) gộp vào; HEAD kiểm `107384af82e3945dd59c9937cc644f24725ef3f2`. Site sạch `normcore-verify.test` qua `scripts/with_bench.sh` (đã xóa sau khi kiểm). Không sửa mã sản phẩm, không thêm test.

## Phần A

| # | Lệnh | Kết quả | Đạt |
| :-- | :-- | :-- | :-: |
| A0 | `git merge origin/develop` | gộp sạch; 927d54f là tổ tiên của HEAD | Đạt |
| A1 | `PYTHONPATH=$PWD python -c "import normcore;print(normcore.__file__)"` | nằm trong checkout NORM-16 | Đạt |
| A2 | `bench --site normcore-verify.test run-tests --app normcore` | Ran 247 tests, OK | Đạt |
| A3 | `run-tests --module normcore.api.test_procedure` | Ran 21 tests, OK | Đạt |
| A4 | `run-tests --module ...nc_clinical_procedure.test_nc_clinical_procedure` | Ran 13 tests, OK | Đạt |
| A5 | `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` | 110 passed, độ phủ 99,19% | Đạt |
| A6 | `golden_engine.py`, `--no-depr`, `golden_cls.py` | cả ba thoát 0 | Đạt |
| A7 | `python3 scripts/check_conventions.py` | thoát 0 | Đạt |
| A8 | `build_rtm.py` trên bản sao `docs` | thoát 0, Must chưa có TC: 0 | Đạt |
| A9 | grep 8 test TC-PROC-01, 02, 03, 04, 08, 09, FR-PROC-005, 013 | 8/8 "co" | Đạt |
| A10 | 4 đột biến trên mã (hoàn nguyên bằng `git checkout`, cây sạch): bỏ lưu `legal_document` → 2 test đỏ; bỏ lưu `legal_section` → 2 đỏ (TC-PROC-09, FR-PROC-013); trích dẫn của **phần** mất văn bản/mục → `test_TC_PROC_09_trich_dan` đỏ; sao chép bỏ hai trường → `test_FR_PROC_013_sao_chep` đỏ. (Lần trước thêm: bỏ `legal_section` khỏi `CITATION_FIELDS` → 2 lỗi) | mọi đột biến làm đỏ test | Đạt |
| A11 | Gọi API như NC Clinician (đã gán khoa) trên site verify: tạo → 3 bước → đổi 1↔3 → xóa S002 → thêm | thứ tự S003,S002,S001 rồi S003,S001,S004; nhân lực R001 headcount 2; hai trích dẫn đủ văn bản/mục/đoạn trích/quan hệ (bước S001 và phần Chỉ định); tạo lần hai bị từ chối nêu `QT-DV-A11-A-KHOA-A11-v1`; sao chép sang dịch vụ khác: S001..S003, `copied_from` đúng, trích dẫn của bước S001 → S002 kèm văn bản, mục; 8 bản ghi Version. NC Auditor và NC Finance: `add_step`, `add_citation`, `create`, `copy`, `reorder`, `add_resource` đều `PermissionError` | Đạt |
| A12 | `git diff 85c4313..927d54f -- normcore` | xem mục dưới | Đạt |
| A13 | Đọc `ProcedureEditor.vue` | xem mục dưới | Đạt (tĩnh) |
| A14 | `bench drop-site normcore-verify.test --force`, `ls sites` | không còn site verify | Đạt |

## Soát diff PR #27 và diff `85c4313..927d54f -- normcore`
- Không test nào bị skip hay nới (không có `skip`/`expectedFailure`/`xfail` mới). Dòng test bị xóa duy nhất: `test_co_16_doctype_va_10_vai_tro` đổi tên `test_co_18_...` và 16 → 18 DocType (FEAT-005 thêm NC Specialty, NC Service Department; cùng kiểu thay đổi đã chấp nhận ở ASM-037/ASM-076), thêm test mới.
- Phần của FEAT-006 (`ProcedureEditor.vue`, `vi.csv`, `tests/unit/test_ui_conventions.py::TestEditorFeat006Fixes`) đúng phạm vi NORM-22. Phần còn lại của diff thuộc FEAT-005 (đã nghiệm thu riêng).
- `git diff --name-only 85c4313..HEAD` trên `docs/golden`, `srs.md`, `test-cases.md`, `use-cases.md`, `implementation-plan.md`, `CLAUDE.md`, `.claude`, `.github`, `.autopilot`: rỗng.
- AMD-005 (`ux-foundations.md` dòng "Thẻ bước": nút Lên/Xuống, kéo chuột tùy chọn), ASM-063 (placeholder dùng `var(--text-muted)`, `opacity: 1`) và ASM-064 (tiêu điểm sang nút còn lại ở biên) đều có người duyệt/Lead dẫn bình luận, không trái FR/NFR.


## Dữ liệu thử đã tạo trên staging (STG_ADMIN, theo Quyết định Lead)
- NC Technical Service: `THU-NORM16-X`, `THU-NORM16-Y`, `THU-NORM16-Z` (Z thêm để tách thử nghiệm tạo mới khỏi sao chép). NC Job Title "Điều dưỡng" (`DD`) đã có sẵn nên không tạo.
- Do tài khoản NC Clinician tạo qua giao diện: NC Clinical Procedure `QT-THU-NORM16-X-K01-v1`, `QT-THU-NORM16-Y-K01-v1`, `QT-THU-NORM16-Z-K01-v1` (đều "Nháp"), cùng các bước, nguồn lực, trích dẫn. Không sửa, không xóa bản ghi có sẵn. Hai tài khoản thử được đặt `language = vi` (ASM-099).

## Phần B — kết quả từng mã (Playwright, staging `d0b4fe1`)
| Mã | Kết quả | Điều thấy được |
| :-- | :-: | :-- |
| L1 | Đạt | Danh sách có cột Mã số, Trạng thái, Dịch vụ kỹ thuật, Khoa chủ trì, Phiên bản; tiêu đề "Quy trình kỹ thuật"; không cuộn ngang (NORM-23 sửa) |
| L2, L4 | Đạt (giữ từ lượt trước) | |
| L3 | Đạt | "Nháp" chấm xám, "Đã ban hành" xanh, đều có chữ |
| L5 | Đạt | NC Auditor: xem được, không có nút thêm |
| E1 | **Không đạt** | Tạo X/K01: bản "Nháp" đủ 8 phần được tạo, nhưng **đồng thời hiện dải lỗi đỏ "Dịch vụ đã có quy trình cho khoa này: QT-THU-NORM16-X-K01-v1"** và "Đang tải…" không tắt (console: `TypeError: …finally is not a function` ở `load`) |
| E2 | Đạt | Tạo lần hai X/K01 (bản Nháp): dải đỏ "Dịch vụ đã có quy trình cho khoa này:" + liên kết tới `QT-THU-NORM16-X-K01-v1`, bấm mở đúng bản |
| E3 | Đạt | Nhập Đại cương, Lưu phần, tải lại: còn nguyên |
| E4 | **Không đạt** | Bỏ trống tên bị chặn (đạt), ba bước S001, S002, S003 tạo được, **nhưng sau lần Lưu đầu nút "Lưu" của biểu mẫu bước và mọi nút ghi bị khóa (`busy` kẹt true)**; phải tải lại trang giữa các lần thêm |
| E5 | **Không đạt** | Thứ tự cuối đúng S003, S002, S001 và mã giữ nguyên, **nhưng sau một lần Xuống, 16 nút ghi bị khóa** (kể cả Xuống S001); mỗi lần bấm phải tải lại trang |
| E6 | **Không đạt** | Xóa S002 có hộp xác nhận, thêm bước → S004, thứ tự S003, S001, S004 (đúng), nhưng cùng lỗi khóa nút: phải tải lại giữa xóa và thêm |
| E7 | Đạt từng thao tác (cần tải lại) | Gợi ý chức danh ("Điều Dưỡng|HR1", "Điều dưỡng|DD"); nhân lực: đơn vị "phút" chỉ đọc, R001; sửa 15 → 20 phút vẫn R001 |
| E8 | Đạt từng thao tác | Vật tư không có trong danh mục lưu được (R002), không có liên kết |
| E9 | Đạt | Chọn S001, trích dẫn "Theo hướng dẫn", cột phải hiện quan hệ, "Thông tư 43/2013/TT-BYT — Điều 5", đoạn trích |
| E10 | Đạt | Chỉ định: "Khác biệt", "Luật Khám bệnh, chữa bệnh 15/2023/QH15 — Điều 7", đoạn trích, lý do; chọn qua lại S001 / Chỉ định chỉ hiện trích dẫn của mục đang chọn |
| E11 | Đạt | Mặc định "Chưa có căn cứ"; sửa Mục (Điều 5 → Điều 6) vẫn giữ Văn bản; xóa có hộp xác nhận |
| E12 | **Không đạt** | Sao chép X → Y: dữ liệu đúng (bước S001..S003 cấp lại, nguồn lực R001, R002 và trích dẫn kèm văn bản, mục đi theo bước; "Sao chép từ" = X), **nhưng hiện dải lỗi đỏ "Dịch vụ đã có quy trình cho khoa này: QT-THU-NORM16-Y-K01-v1"** sau khi sao chép thành công |
| E13 | Đạt | Dòng thời gian bản ghi: "Bạn đã thay đổi giá trị cho Số lượng từ 20 đến 25 ở hàng #1 · vừa rồi", "… Mô tả từ Mô tả 1 đến THU-NORM16 mô tả đã sửa ở hàng #2 · vừa rồi" (trước/sau, người, thời điểm) |
| E14 | Đạt | Xóa S001 khi còn nguồn lực: hộp xác nhận, rồi dải lỗi tiếng Việt "Bước S001 còn 2 nguồn lực và 1 trích dẫn; xóa chúng trước"; S001 còn nguyên |
| E15 | Đạt | Dịch vụ không tồn tại: dải đỏ trong trang (`role="alert"`) "Không thể tìm thấy Dịch vụ kỹ thuật: THU-NORM16-KHONG-TON-TAI", không còn hộp thoại Desk, không nói "đã có quy trình" (NORM-23 sửa) |
| G1 | Đạt | NC Auditor mở bản **Nháp**: "Bạn chỉ có quyền xem quy trình này."; không còn "Tạo quy trình", "Sao chép…", Sửa, Xóa, Lên, Xuống, Thêm…; ô văn bản readonly |
| G2 | Đạt (giữ) | |
| U1 | Đạt | Biểu mẫu bước, nguồn lực, trích dẫn ở 1366×768: không cuộn ngang, không ô chồng lấn, nằm trong khung |
| U2 | Đạt | Trình soạn Nháp, biểu mẫu, dải lỗi: không còn chữ tiếng Anh |
| K1, K2 | Đạt (giữ) | |
| K3 | **Không đạt** | Quy trình 2 bước (S003, S001) và 3 bước: Enter trên "Xuống" ở bước đầu → thứ tự đổi đúng nhưng **tiêu điểm rơi về `BODY`**, 15–16 nút bị khóa; tương tự "Lên" ở bước cuối/giữa. Không đạt cả khi ở biên. PR #27 chỉ có test tĩnh đọc chuỗi mã nên không thấy lỗi này |
| K4 | Đạt | Enter trên "Thêm bước" mở biểu mẫu, gõ, Enter lưu được (3 → 4 bước); biểu mẫu ở cuối trang, tới được bằng Tab nhưng tiêu điểm không tự chuyển vào biểu mẫu |
| K5 | Đạt | Esc đóng biểu mẫu trích dẫn, nội dung đã gõ không được lưu |
| K6 | **Không đạt** | Thêm nguồn lực bằng phím được (R003), nhưng ngay sau đó nút "Xóa" của dòng vừa thêm bị khóa (cùng lỗi `busy`); không xóa được bằng phím nếu không tải lại |
| C1 | Đạt | Nhãn quan hệ: Theo hướng dẫn 5,42; Khác biệt 5,44; Chưa có căn cứ 5,36 (≥ 4,5) |
| C2, C3, C4, C5 | Đạt (giữ) | 7,81 / 11,73 / 10,57 / 7,04 (placeholder) / 7,81 |

## Nguyên nhân gốc và việc phải sửa (để Lead tạo issue)
- **Tệp/hàm:** `normcore/public/js/procedure_editor/ProcedureEditor.vue`: `load()` (dòng ~299, `.finally(() => (this.loading = false))`) và `run()` (dòng ~341, `.finally(() => (this.busy = false))`). `this.call()` trả về promise của `frappe.call` (jQuery Deferred, không có `.finally`; console: `TypeError: …finally is not a function at Proxy.load / Proxy.run`).
- **Sửa gợi ý:** bọc kết quả `call()` bằng `Promise.resolve(...)` (promise gốc) hoặc dùng `.then(f, f)` thay `.finally`. Sau sửa: `busy` và `loading` về false; dải lỗi sai sau tạo/sao chép biến mất (nhánh `.catch` của `submitProcedureForm` không còn bị kích hoạt bởi lỗi `TypeError` của `load`); K3 (ASM-064) mới có tác dụng.
- **Test:** thêm kiểm tra hành vi (không chỉ đọc chuỗi mã), ví dụ test giao diện chạy trình duyệt hoặc test đơn vị gọi `load/run` với promise kiểu jQuery.
- **Bị chạm sau khi sửa phải kiểm lại:** E1, E4, E5, E6, E7, E12, K3, K6 (và các mã ghi liên tiếp).

Chưa ghi Test ref, As-Built, `DONE`.
