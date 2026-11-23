# Acceptance FEAT-006 — Kiểm định lại sau NORM-15 và NORM-22 (NORM-16)

Kết luận: **rework — chỉ thiếu kết quả Phần B (giao diện trên trình duyệt).** Phần A (lệnh, test, API, diff) đạt hết. Hai lỗi giao diện cũ (G1, K3, C4) đã được PR #27 (NORM-22) sửa trong mã và có test tĩnh, nhưng QA không có trình duyệt (Playwright MCP không kết nối được) và người duyệt chưa trả lời từng mã Phần B ("Đồng ý hết", "Duyệt hết", "Đã kiểm tra ok" không tính, G4'). Không ghi Test ref, As-Built, `DONE`.

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

## Phần B — chưa có kết quả
Không có trình duyệt trong môi trường QA (Playwright MCP: CONNECTION_CLOSED) nên người duyệt kiểm tay trên staging http://112.213.88.40:8100, 1366×768, ngôn ngữ `vi`, theo bảng mã L1–L5, E1–E15, G1–G2, U1–U2, K1–K6, C1–C5 trong mô tả issue NORM-16. Mã nào chưa trả lời riêng = chưa có kết quả. Ưu tiên bấm G1, K3, C4 (vừa sửa), E9, E10, E12 (trích dẫn có văn bản, mục), K1–K6, kèm ảnh E5, E9, E12, E13, G1, U1.

## Việc còn lại
1. Người duyệt trả lời từng mã Phần B.
2. Nếu đủ và đạt: QA ghi `accepted`, Test ref (`docs/rtm-testref.md`), As-Built (dòng đầu, mục 4, mục 7), `DONE`, chuyển In Review. Mã nào không đạt: issue sửa riêng.
