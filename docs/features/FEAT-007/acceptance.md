# Acceptance FEAT-007 — Phê duyệt ba cấp, ban hành, in (NORM-44)

Kết luận: **accepted.** Kiểm độc lập sau khi PR #45 đã merge (merge commit `223e8af`) trước Review/QA, trên HEAD của develop `223e8afb1e4026c0a353c5defc8857b96aea1a43`. QA không viết FEAT này.

## Môi trường và giới hạn
- Không tạo được site sạch `normcore-verify.test`: runtime QA không có `DB_ROOT_PASSWORD` (`bench new-site` lỗi `Access denied for user 'root'`; đã xóa thư mục site dở). Thay bằng `migrate` rồi chạy toàn bộ test trên site dùng chung `normcore.test` qua `scripts/with_bench.sh`, cùng cách đã làm ở FEAT-005. Cài mới từ đầu được chứng minh bởi CI của PR #45 (job "Test trên site Frappe v15", pass, site mới).
- Staging http://112.213.88.40:8100 đã deploy `223e8af` (workflow "Deploy staging" run 45607095038 thành công) trước khi kiểm giao diện.
- Luồng ba cấp đầy đủ **không chạy qua giao diện trên staging**: `NC Settings.council_secretary` và `NC Department K01.head_user` chưa cấu hình, mà đề bài cấm sửa bản ghi có sẵn. Luồng này được kiểm bằng test tích hợp trên bench (bảng dưới, đi đường thật `apply_action`).

## Phần A — chạy lại
| Lệnh | Kết quả | Đạt |
| :-- | :-- | :-: |
| `bench --site normcore.test migrate && run-tests --app normcore` (qua `with_bench.sh`) | Ran 890 tests, OK | Đạt |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 448 passed, độ phủ 99% | Đạt |
| `golden_engine.py`, `golden_cls.py` | thoát 0 | Đạt |
| `check_conventions.py` | thoát 0 | Đạt |
| `build_rtm.py docs` | VAN DE: 0, Must chưa có TC: 0 | Đạt |
| CI PR #45 (`gh pr checks 45`) | "Test trên site Frappe v15" pass, "Tài liệu, golden, unit test" pass | Đạt |

## Phủ TC (mỗi TC có test cùng mã, assertion khớp kỳ vọng trong test-cases.md)
| TC | Test | Đạt |
| :-- | :-- | :-: |
| TC-PROC-05 | `api/test_procedure_workflow.py::test_TC_PROC_05_khac_biet_thieu_ly_do` + unit `test_procedure_validation` | Đạt |
| TC-PROC-06 | `test_TC_PROC_06_liet_ke_du_ba_loi` (tích hợp + unit): đủ 3 lỗi, vẫn Nháp | Đạt |
| TC-PROC-07 | `api/test_procedure_print.py`, `tests/test_procedure_docx.py`, unit printing; kiểm tay PDF ở Phần B | Đạt |
| TC-WF-01 | `test_TC_WF_01_luong_bon_trang_thai_va_thong_bao`, `_ca_am` | Đạt |
| TC-WF-02 | `test_TC_WF_02_tu_choi_o_ca_ba_cap` | Đạt |
| TC-WF-03 | `test_TC_WF_03_sua_mo_ta_buoc_qua_form_va_api_bi_tu_choi` (cả 5 trạng thái khóa, form lẫn API) | Đạt |
| TC-WF-04 | `api/test_procedure_workflow_jobs.py`, unit `test_procedure_approval` | Đạt |
| TC-WF-08 | `test_TC_WF_08_y_kien_theo_buoc_hien_cho_nguoi_soan_sau_khi_bi_tra_lai` | Đạt |
| FR-WF-013 | `test_FR_WF_013_nhac_khi_qua_han`, `_theo_cau_hinh_so_ngay` | Đạt |

## Soát diff PR #45 (như một lần review)
- Test cũ bị đổi (`test_feat_001`, `test_feat_039`, `test_form_actions`, `test_nc_audit_event`, `test_nc_costing_run`, `test_nc_norm_set`, `test_nc_clinical_procedure`): chỉ thay cách dựng dữ liệu "Đã ban hành"/"Chờ ban hành" bằng `tests/utils.py::publish_procedure`/`to_state` (do `allow_publish` bị bỏ); giá trị mong đợi và assertion giữ nguyên; không skip/xfail. Có dẫn "Quyết định Lead" PA1 (ASM-007-16). Chấp nhận.
- Quyền: `NC Review Comment` đúng hàng "Ý kiến thẩm định" của data-model mục 4 (Dept Head, Council, Director ghi; Auditor chỉ đọc; Resource Mgr không có quyền); `check_conventions.py` đã thêm đúng hàng ma trận. Không sửa tay `permissions.py`/sổ đăng ký chung.
- `api/procedure_workflow.py:61-81` (`_actor_error`) kiểm tường minh vai trò, khoa, thư ký trước mọi chuyển trạng thái; `:131` kiểm quyền đọc; Từ chối bắt buộc lý do (`:158`).
- Tài liệu chỉ đọc (`golden`, `srs.md`, `test-cases.md`, `use-cases.md`, `implementation-plan.md`, `CLAUDE.md`, `.claude`, `.github`, `.autopilot`): không đổi. `docs/data-model.md` đổi đúng theo AMD-007-01 (thư ký hội đồng) — không thuộc danh sách chỉ đọc.
- Không có mục bắt buộc sửa. Ghi nhận: Dev đã tự ghi `docs/as-built/FEAT-007.md` và Test ref khi chưa kiểm định; QA cập nhật dòng "nghiệm thu" và tiêu đề Test ref.

## Phần B — giao diện, staging (tài khoản NC Clinician khoa K01 và NC Auditor, không dùng Administrator để kiểm)
Dữ liệu: bản ghi có sẵn `QT-THU-NORM16-V-K01-v1` (Nháp) và `QT-SMOKE-…160328-K01-v1` (Đã ban hành); không tạo, sửa hay xóa bản ghi nào. Ảnh đính kèm ở bình luận NORM-44.
| Mã | Kiểm | Kết quả |
| :-- | :-- | :-: |
| SCR-DSK-009/010 (form) | Clinician mở bản Nháp: menu "Thao tác" có "Gửi duyệt"; bản Đã ban hành: dải "Quy trình đã ban hành, không sửa được", trường khóa | Đạt |
| SCR-DSK-010 (trình soạn) | Clinician: nút "Gửi duyệt", "In PDF", "Tải DOCX", khối "Ý kiến thẩm định" (lọc "Chỉ chưa xử lý"); Auditor: chỉ "In PDF", "Tải DOCX" và dòng "Bạn chỉ có quyền xem quy trình này" | Đạt |
| TC-PROC-07 (PDF, M) | `download_pdf` bản Nháp: bắt đầu `%PDF`, có "DỰ THẢO" hai lần, số hiệu, phiên bản, khối chữ ký (Người soạn/Trưởng khoa/Hội đồng chuyên môn/Giám đốc); bản Đã ban hành: không có "DỰ THẢO", có số QĐ `QD-SMOKE-20261121160328`, ngày hiệu lực 01/01/2026, Phiên bản 1, khối chữ ký | Đạt |
| FR-PROC-011 | `download_docx` trả tệp `PK` cho cả hai bản, mọi vai trò xem được | Đạt |
| Quyền (API, staging) | Auditor "Gửi duyệt" → 403 PermissionError; Clinician "Đồng ý" và "Ban hành" ở Nháp → 417 "không áp dụng ở trạng thái Nháp"; Clinician `update_step` bản Đã ban hành → 417 "không ở trạng thái Nháp"; Auditor `update_step` → 403; Auditor và Clinician tạo NC Review Comment → 403 (đúng ma trận: Clinician chỉ đọc) | Đạt |
| `get_review` | Auditor `actions=[]`; Clinician `actions=["Gửi duyệt"]` | Đạt |
| Nhãn tiếng Việt | Mọi nhãn, thông báo lỗi bằng tiếng Việt | Đạt |

Ghi chú: `frappe.utils.print_format.download_pdf` gốc của Frappe lỗi trên staging (wkhtmltopdf "ConnectionRefusedError" khi tải tài nguyên); đường in của sản phẩm (`api/procedure_workflow.download_pdf`) hoạt động. Không thuộc FEAT-007, nhưng người triển khai nên biết nếu bệnh viện in qua nút "In" mặc định của Frappe.
