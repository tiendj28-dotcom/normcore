# Acceptance FEAT-006 — Kiểm định lại sau NORM-15 và NORM-22 (NORM-16)

Kết luận: **rework — Phần A đạt; Phần B (Playwright trên staging) kiểm được một phần, phần còn lại thiếu dữ liệu staging.** G1 và C4 (do PR #27 sửa) đạt trên giao diện thật. K3, và mọi mã cần quy trình "Nháp" (E1, E3–E14, K3, K4, K6, U1 của biểu mẫu nguồn lực/trích dẫn, C1) **chưa kiểm được**: tài khoản NC Clinician không tạo được dịch vụ kỹ thuật và cả 5 dịch vụ trên staging đã có bản "Đã ban hành". Có hai sai lệch nhỏ so với `ui-design.md` (L1, E15). Không ghi Test ref, As-Built, `DONE`.

Bằng chứng Phần B: kịch bản Playwright (Chromium headless, 1366×768, locale `vi`) chạy qua `~/pw-venv/run.sh` trên http://112.213.88.40:8100, ảnh theo mã đính kèm ở bình luận NORM-16. Theo ASM-099 (Quyết định Lead), kết quả này thay cho câu trả lời của người duyệt.

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

## G1, K3, C4 (đọc mã + test tĩnh; chưa kiểm trong trình duyệt)
| Mã | Mã nguồn | Test | Còn cần trình duyệt |
| :-- | :-- | :-- | :-- |
| G1 | nút "Tạo quy trình" và "Sao chép" có `v-if="canCreate"` = `frappe.model.can_create("NC Clinical Procedure")` | `test_G1_nut_ghi_an_khi_khong_co_quyen_tao` | Cần xem NC Auditor thật sự không thấy hai nút (`can_create` dựa vào dữ liệu boot) |
| K3 | `focus()` chạy sau khi `run()` xong (busy = false); ở biên chuyển sang nút còn lại của cùng bước | `test_K3_tieu_diem_sau_khi_busy_ve_false`, `test_K3_du_phong_khi_nut_bien_bi_khoa` | Cần bấm bằng phím thật |
| C4 | `::placeholder { color: var(--text-muted); opacity: 1 }` (7,81:1 theo số của BA) | `test_C4_placeholder_dung_mau_text_muted` | Cần đo bằng DevTools |

Cả bốn test trên đọc **văn bản mã nguồn Vue** bằng regex, không chạy giao diện; chúng chỉ chứng minh mã đã đổi như thiết kế, không chứng minh hành vi trong trình duyệt. Vì vậy chưa thay được Phần B.

## Phần B — kiểm bằng Playwright trên staging (ASM-099)

Tài khoản A = NC Clinician (khoa K01), B = NC Auditor (đều từ biến môi trường, không ghi mật khẩu). Dữ liệu có sẵn: 5 dịch vụ `SMOKE-*`, mỗi dịch vụ đã có một quy trình **Đã ban hành** của K01; không có bản Nháp. Hai tài khoản được QA đặt `language = vi` (mặc định là `en`, giao diện trước đó tiếng Anh).

| Mã | Kết quả | Điều thấy được |
| :-- | :-- | :-: |
| L1 | **Không đạt (nhỏ)** | Danh sách hiện cột Mã số, Trạng thái, Dịch vụ kỹ thuật; **không có cột Khoa chủ trì và Phiên bản** (chỉ có ô lọc Khoa chủ trì); không cuộn ngang; nhãn tiếng Việt. Tên DocType trên tiêu đề/nút ("NC Clinical Procedure", "Thêm NC Clinical Procedure") vẫn tiếng Anh |
| L2 | Đạt | Lọc Khoa chủ trì = K01 + Trạng thái = Nháp: "Không tìm thấy NC Clinical Procedure nào…", có nút Tạo |
| L3 | Một phần | "Đã ban hành" có chấm xanh và chữ; **Nháp (xám) chưa kiểm được**: không có bản Nháp |
| L4 | Đạt | Mở bản ghi có nút "Mở trình soạn"; bấm mở `/app/procedure-editor/<tên>`, ô chọn đúng bản |
| L5 | Đạt | NC Auditor mở danh sách: xem được, không có nút thêm |
| E1, E3–E14 | **Chưa kiểm được** | Cần bản Nháp: staging không có, NC Clinician không tạo được dịch vụ (`can_create` NC Technical Service = false), 5 dịch vụ đều đã có bản ban hành |
| E2 | Một phần | Tạo cho dịch vụ đã có bản **ban hành**: dải đỏ "Dịch vụ đã có quy trình cho khoa này: QT-SMOKE-…-v1" kèm liên kết tới bản đó (ASM-020). Trường hợp bản Nháp của TC chưa kiểm được |
| E15 | **Không đạt (nhỏ)** | Dịch vụ không tồn tại: thông báo tiếng Việt "Không thể tìm thấy Dịch vụ kỹ thuật: THU-NORM16-KHONG-TON-TAI", không nói "đã có quy trình", **nhưng hiện trong hộp thoại Desk "Tin nhắn", không phải dải lỗi đỏ trong trang** như `ui-design.md` mô tả |
| G1 | **Đạt** | NC Auditor mở bản ban hành: không còn nút "Tạo quy trình", "Sao chép từ quy trình này", Sửa, Xóa, Lên, Xuống, Thêm…; mọi ô văn bản readonly. (Dải hiện "Quy trình đã ban hành, chỉ đọc." vì bản này đã ban hành; dải "Bạn chỉ có quyền xem" cần bản Nháp: chưa kiểm được) |
| G2 | Đạt | NC Clinician mở bản ban hành: "Quy trình đã ban hành, chỉ đọc."; không có Sửa, Xóa, Lên, Xuống, Thêm…, Lưu phần; ô văn bản readonly (còn "Tạo quy trình", "Sao chép…" là đúng vì có quyền tạo) |
| U1 | Một phần | Biểu mẫu "Tạo quy trình" ở 1366×768: không cuộn ngang, ô không đè nhau. Biểu mẫu nguồn lực/trích dẫn cần bản Nháp: chưa kiểm được |
| U2 | Đạt (phạm vi mở được) | Trình soạn của bản ban hành, biểu mẫu tạo và hộp thoại lỗi: 100% tiếng Việt. Riêng DocType name ở L1 tiếng Anh |
| K1 | Đạt (trong phạm vi mở được) | Tab đi qua mọi điều khiển theo thứ tự nhìn thấy (Tạo quy trình → Sao chép → từng phần và ô văn bản → bước S001 → … → ô chọn), không kẹt |
| K2 | Đạt | 34/34 điều khiển có viền focus 2px (rgb 23,23,23) |
| K3 | **Chưa kiểm được** | Cần bản Nháp ≥ 2 bước (kể cả 2 bước và bước ở đầu/cuối); chỉ có test tĩnh của PR #27 |
| K4, K6 | **Chưa kiểm được** | Cần bản Nháp |
| K5 | Một phần | Esc đóng biểu mẫu "Tạo quy trình" không lưu; biểu mẫu trích dẫn cần bản Nháp |
| C1 | **Chưa kiểm được** | Chưa có trích dẫn nào để đo nhãn quan hệ |
| C2 | Đạt | chữ phụ `text-muted` và tiêu đề bảng nguồn lực: rgb(82,82,82) trên trắng = **7,81:1** |
| C3 | Đạt | chữ thường rgb(56,56,56)/trắng = **11,73:1**; chữ nút thường trên nền xám nhạt = **10,57:1** |
| C4 | **Đạt** | `::placeholder` ô biểu mẫu "Tạo quy trình": rgb(82,82,82), opacity 1, nền rgb(243,243,243) = **7,04:1** (trước sửa BA tính 2,57:1) |
| C5 | Đạt | nhãn "Đã ban hành" rgb(82,82,82) trên nền trong suốt/trắng = 7,81:1; dải thông báo 10,57:1 |

Tỷ lệ tính bằng `getComputedStyle` rồi công thức tương phản WCAG.

## Kết luận và việc còn lại
- **Đạt:** Phần A đầy đủ; G1 (lỗi ban đầu của NC Auditor) và C4 (placeholder) đã sửa đúng trên giao diện thật.
- **Chưa kiểm được (cần dữ liệu):** E1, E3–E14, K3, K4, K6, K5/U1/C1 phần còn lại, L3 (Nháp). Cần ít nhất 2 `NC Technical Service` chưa có quy trình của K01 (ví dụ `THU-NORM16-X`, `THU-NORM16-Y`) do vai trò có quyền tạo (không phải NC Clinician), và một chức danh nhân lực để gợi ý. Có dữ liệu này QA chạy lại E, K, U1, C1 bằng cùng kịch bản.
- **Sai lệch nhỏ cần quyết định (không chặn nghiệm thu nếu Lead chấp nhận bằng ASM):** L1 (cột Khoa chủ trì, Phiên bản không hiện trên danh sách), E15 (lỗi hiện ở hộp thoại thay vì dải đỏ).
- Chưa ghi Test ref, As-Built, `DONE`.
