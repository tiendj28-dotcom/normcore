# Acceptance FEAT-006 — Kiểm định độc lập (NORM-14)

Kết luận: **design-defect**. Mã và test đạt; thiết kế bỏ trường "văn bản, mục" của trích dẫn trái FR-PROC-007 (Must) / TC-PROC-09; giao diện chưa kiểm bằng trình duyệt.

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
| TC-PROC-01 (bản nháp v1, 8 phần) | `test_TC_PROC_01_tao_ban_nhap`: version 1, "Nháp", đúng 8 phần, 6 nhãn đầu đúng | Đạt |
| TC-PROC-02 (tạo lần hai bị từ chối, dẫn tới bản có) | `test_TC_PROC_02_...`: `ExistingProcedureError.existing` = tên bản nháp; chạy tay: "Dịch vụ này đã có bản đang soạn hoặc đang duyệt của khoa: QT-DVV1-KV1-v1" | Đạt |
| TC-PROC-03 (3 bước, đổi 1↔3, xóa 2, thêm mới → S004) | `test_TC_PROC_03_tich_hop_sap_lai_xoa_them` làm đúng chuỗi của TC, kiểm thứ tự S003,S001,S004 và S004 không tái dùng S002; thêm 3 test đơn vị bất biến. Chạy tay cho cùng kết quả | Đạt |
| TC-PROC-04 (nhân lực: chức danh, số người, mã dòng bất biến) | `test_TC_PROC_04_nguon_luc_nhan_luc`: R001, headcount 2, liên kết NC Job Title, sửa không đổi mã, xóa rồi thêm → R002 | Đạt |
| TC-PROC-08 (lịch sử trước/sau/người/thời điểm cho cả bước và nguồn lực) | Test gốc chỉ kiểm thời điểm của bước, bỏ thời điểm của dòng nguồn lực (yếu). QA thêm `test_TC_PROC_08_moc_thoi_gian_va_nguoi_cho_ca_hai_thay_doi` (commit 5dba6de), xanh | Đạt |
| TC-PROC-09 (trích dẫn lưu văn bản, mục, đoạn trích, quan hệ) | Test kiểm đích, quan hệ, đoạn trích, lý do, mặc định "Chưa có căn cứ", lọc theo bước/phần. **Không có "văn bản" và "mục"**: `nc_procedure_citation.json` chỉ có 5 trường (target_section, target_step_id, relation, quote, deviation_reason). Test dễ hơn TC; viết lại cho đủ cần mã sản phẩm | **Không** |
| FR-PROC-013 sao chép | `test_FR_PROC_013_sao_chep`; chạy tay: sao chép đủ bước, mã bước cấp lại S001..S003, ghi nguồn | Đạt |
| Tiêu chí 7 mục 5 (bàn phím, tương phản NFR-USE-004) | Chỉ soát tĩnh `ProcedureEditor.vue` (nút Lên/Xuống có aria-label, Esc đóng form). Chưa kiểm trong trình duyệt, chưa đo tương phản | **Chưa kiểm** |
| Mỗi DocType mới: vai trò không quyền + NC Auditor chỉ đọc | NC Procedure Citation (bảng con): `test_quyen_vai_tro_chi_doc_va_auditor_bi_tu_choi` chạy 13 hàm ghi với NC Finance và NC Auditor, đều `PermissionError`, dữ liệu không đổi; `test_permissions` quét 16 DocType | Đạt |

## Kiểm trực tiếp (hàm API như người dùng NC Clinician, site verify)
Tạo quy trình → 3 bước → sắp lại → xóa → bước mới S004 → nguồn lực nhân lực R001 (headcount 2) → trích dẫn → tạo lần hai bị từ chối → sao chép sang dịch vụ khác → có 7 bản ghi Version. Kết quả khớp TC. **Chưa làm bằng giao diện** (không có trình duyệt trong môi trường QA).

## Soát diff test và tài liệu
- Không có test bị xóa/skip/nới trong diff `f82065b..98d21fe`; chỉ đổi `test_co_14_doctype` → `test_co_16_doctype` (số DocType, theo ASM-037) và dữ liệu dựng.
- Fixture `make_procedure` bật `flags.ignore_single_active` (ASM-025): chỉ ở dữ liệu dựng; DI-02 có test riêng. Chấp nhận.
- Không sửa `docs/golden/`, `srs.md`, `use-cases.md`, `test-cases.md`, `implementation-plan.md`.
- AMD-001 đủ vấn đề/phương án/tệp sửa/ảnh hưởng; `data-model.md` mục 3.3 thêm đúng dòng đã nêu.

## ASM của FEAT-006 (017..025)
- **ASM-017 trái FR-PROC-007 / TC-PROC-09** → lý do của design-defect. Người duyệt đã hoãn đến FEAT-020 nhưng FR-PROC-007 là Must và TC-PROC-09 hiện nêu rõ "văn bản, mục".
- ASM-018, 019, 020, 021, 022, 023, 024, 025: lấp chỗ tài liệu chưa nói, không trái FR/TC (ASM-020 chặn tạo khi đã có bản ban hành cho tới FEAT-008; ASM-019 chỉ gợi ý NC Job Title, FR-PROC-005 là Should).

## Việc phải sửa (để người duyệt tạo issue)
1. Thêm vào NC Procedure Citation trường văn bản và mục (hoặc quyết định FR-PROC-007 chuyển FEAT-020 qua thủ tục sửa yêu cầu); `api/procedure.py::_apply_citation`, `add_citation`, `update_citation`; viết lại `test_TC_PROC_09_trich_dan` kiểm đủ 4 thuộc tính.
2. Người duyệt tự bấm giao diện ở 1366×768, ngôn ngữ `vi`, SCR-DSK-007/009: tạo quy trình, thêm 3 bước, Lên/Xuống, xóa, thêm bước (mã S004), thêm nguồn lực nhân lực, thêm trích dẫn, sao chép, xem lịch sử; dùng Tab/Enter/Esc không chuột; đo tương phản nhãn quan hệ và chữ phụ ≥ 4,5:1.
