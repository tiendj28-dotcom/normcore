# Acceptance FEAT-006 — Kiểm định lại sau NORM-15 (NORM-16)

Kết luận: **rework — CHƯA NGHIỆM THU vì thiếu kết quả giao diện.** Mã, test và TC-PROC-09 đã đạt; lỗi design-defect cũ (ASM-017) đã được NORM-15 / ASM-046 sửa. Còn lại: giao diện SCR-DSK-007/009 chưa kiểm bằng trình duyệt (QA không có trình duyệt, "người duyệt kiểm tay"), và đọc mã thấy hai chỗ lệch `ui-design.md` cần sửa hoặc người duyệt bác bỏ.

## Môi trường kiểm
Nhánh `ai/NORM-16-reverify-006` = `develop` @ 85c4313 (chứa PR #17 271ced9). Site sạch `normcore-verify.test` (đã xóa). Mã được kiểm là checkout này (symlink `apps/normcore` tạm trỏ về đây, đã trả như cũ).

| Lệnh | Kết quả | Đạt |
| :-- | :-- | :-: |
| `bench --site normcore-verify.test run-tests --app normcore` | Ran 148 tests, OK | Đạt |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 69 passed; độ phủ 99% | Đạt |
| `golden_engine.py`, `--no-depr`, `golden_cls.py` | thoát 0 | Đạt |
| `python3 scripts/check_conventions.py` | thoát 0 | Đạt |
| `python3 docs/tools/build_rtm.py docs` | thoát 0, Must chưa có TC: 0 | Đạt |

## Độ phủ tiêu chí
| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| TC-PROC-01, 02, 03, 04, 08 | Như lần kiểm NORM-14, test không đổi (trừ TC-PROC-08 do QA NORM-14 thêm); chạy lại trên site sạch, xanh | Đạt |
| **TC-PROC-09** | `test_TC_PROC_09_trich_dan` kiểm đủ 4 thuộc tính cho cả trích dẫn bước ("Theo hướng dẫn", Thông tư 43/2013/TT-BYT, Điều 5, đoạn trích) và phần ("Khác biệt", Luật 15/2023/QH15, Điều 7, đoạn trích, lý do); sửa `legal_section` giữ `legal_document`; lọc theo bước/phần; mặc định "Chưa có căn cứ" | Đạt |
| **FR-PROC-013** | `test_FR_PROC_013_sao_chep` kiểm `legal_document`, `legal_section` đi theo trích dẫn khi sao chép, bước cấp lại mã | Đạt |
| Đột biến (làm hỏng mã, hoàn nguyên sau) | bỏ lưu `legal_document` → 2 test đỏ (TC-PROC-09, FR-PROC-013); bỏ lưu `legal_section` → 2 đỏ; bỏ `legal_section` khỏi `CITATION_FIELDS` → 2 lỗi. Test không yếu | Đạt |
| FR-PROC-005 (Should) | `test_FR_PROC_005_goi_y_va_de_trong_lien_ket` | Đạt |
| Quyền (NC Finance, NC Auditor, bản không ở Nháp) | `test_quyen_vai_tro_chi_doc_va_auditor_bi_tu_choi` và DI-07 xanh | Đạt |
| Tiêu chí giao diện: SCR-DSK-007/009 ở 1366×768, `vi`, bàn phím, tương phản NFR-USE-004 | **Chưa kiểm** — không có trình duyệt | **Chưa có kết quả** |

## Soát diff `98d21fe..85c4313 -- normcore`
- 5 tệp: `api/procedure.py`, `api/test_procedure.py`, `nc_procedure_citation.json`, `ProcedureEditor.vue`, `vi.csv` (+2 dòng). Không tệp nào ngoài phạm vi.
- Test: không xóa, không skip, không nới. `test_TC_PROC_09_trich_dan` viết lại **mạnh hơn** (thêm assertion 4 thuộc tính; ASM-046 đã được người duyệt đồng ý); `test_FR_PROC_013` thêm assertion; thêm test TC-PROC-08.
- Tài liệu chỉ đọc (`srs.md`, `test-cases.md`, `use-cases.md`, `golden/`, `implementation-plan.md`, `CLAUDE.md`, `.claude`, `.github`): `git diff --stat` rỗng.
- **ASM-046 không trái FR-PROC-007 / TC-PROC-09**: FR đòi lưu văn bản và mục, Data tạm lưu đúng; chỉ chưa là Link (FEAT-020). Chưa có AMD cho `data-model.md` mục 3.3 (Q4 của BA; người duyệt đã đồng ý ASM-046 đủ).

## Điểm cần xử lý ở giao diện (đọc mã `ProcedureEditor.vue`, chưa chạy trình duyệt)
1. **G1 — NC Auditor vẫn thấy "Tạo quy trình" (dòng 11) và "Sao chép từ quy trình này" (dòng 14, chỉ `v-if="doc"`)**; `ui-design.md` mục "Trạng thái" đòi ẩn mọi điều khiển ghi. Máy chủ vẫn từ chối. Đúng là lệch thiết kế.
2. **K3 — mất tiêu điểm sau Lên/Xuống** (dòng 350–362): `focus()` chạy trong chuỗi trước khi `run()` đặt `busy = false`, lúc đó mọi nút Lên/Xuống còn `disabled` nên bộ chọn `:not([disabled])` không tìm thấy nút. Nhiều khả năng đúng là lỗi; cần trình duyệt xác nhận.
3. **C4 — placeholder** ô biểu mẫu (nhãn nhìn thấy duy nhất, dòng 149–175) ~2,57:1 theo BA tính; người duyệt đã đồng ý placeholder thuộc chuẩn 4,5:1 (NFR-USE-004) → chưa đạt, cần sửa mã.

## Việc phải làm
1. Dev sửa G1 (ẩn "Tạo quy trình" và "Sao chép" khi `!can_edit`/vai trò chỉ đọc), K3 (đặt tiêu điểm sau khi `busy` về false), C4 (placeholder đủ 4,5:1 hoặc thêm nhãn nhìn thấy) — issue riêng.
2. Người duyệt kiểm tay trên staging http://112.213.88.40:8100, 1366×768, ngôn ngữ `vi`, tài khoản NC Clinician (A) và NC Auditor (B), theo bảng L1–L5, E1–E15, G1–G2, U1–U2, K1–K6, C1–C5 trong mô tả issue NORM-16; trả lời từng mã (ví dụ `E9 đạt`), kèm ảnh E5, E9, E12, E13, G1, U1. Mã chưa trả lời = chưa có kết quả.
3. Sau khi sửa và có kết quả giao diện: kiểm lại, nếu đạt mới ghi Test ref (`docs/rtm-testref.md`), cập nhật As-Built (dòng đầu, mục 4, mục 7), tạo `DONE`.

Chưa ghi Test ref, As-Built, DONE theo điều kiện trên.
