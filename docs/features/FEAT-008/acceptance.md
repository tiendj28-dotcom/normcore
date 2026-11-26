# Acceptance FEAT-008 — Sửa đổi, so sánh phiên bản, thu hồi (NORM-50)

Kết luận: **accepted.** Kiểm độc lập trên HEAD `97e58922d804ad244fe353b61be3407ea8b7e256` của nhánh PR #53 (sau khi Dev gộp develop/FEAT-012, kiểm lại: site sạch 1169 test OK, pytest 601 passed độ phủ 99%, CI xanh). QA không viết FEAT này.

## Phần A — chạy lại từ đầu
| Lệnh | Kết quả | Đạt |
| :-- | :-- | :-: |
| `with_bench.sh`: `new-site normcore-verify.test` + install-app + `run-tests --app normcore` + drop-site (một lần gọi) | Site sạch tạo được; Ran 1169 tests, OK; site đã xóa | Đạt |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 601 passed, 146 subtests; độ phủ 99% | Đạt |
| `golden_engine.py`, `golden_cls.py` | thoát 0 | Đạt |
| `check_conventions.py` | thoát 0 | Đạt |
| `build_rtm.py docs` | Must chưa có TC: 0, không vấn đề mới (đã hoàn tác rtm.md, verification-report.md do script sinh) | Đạt |
| CI PR #53 (`gh pr checks 53`) | "Test trên site Frappe v15" pass, "Tài liệu, golden, unit test" pass | Đạt |

## Phủ TC / FR
| Mã | Test | Đạt |
| :-- | :-- | :-: |
| TC-WF-05 (FR-WF-009) | `api/test_procedure_revision.py::test_TC_WF_05_sua_doi_giu_ma_buoc` + các test từ chối/đã có bản nháp | Đạt |
| TC-WF-06 (FR-WF-011) | `api/test_procedure_norm_flag.py::test_TC_WF_06_ban_hanh_gan_co_bo_dinh_muc`; unit `test_TC_WF_06_step_changes_them_bo_doi` | Đạt |
| TC-WF-07 (FR-WF-010, M) | `api/test_procedure_compare.py::test_TC_WF_07_so_sanh_phien_ban`; unit `test_TC_WF_07_diff_theo_phan_buoc_nguon_luc` | Đạt (dữ liệu); hiển thị xem mục giới hạn |
| FR-WF-012 | `api/test_procedure_withdraw.py` (có lý do, bị từ chối, sai trạng thái); unit `TestWithdraw` | Đạt |
| Quyền | Thu hồi chỉ NC Director, Auditor không sửa cờ (`test_truong_co_chi_doc_va_auditor_khong_sua`, `test_quyen_auditor_va_finance`), vai không quyền bị từ chối ở test sửa đổi/so sánh/thu hồi | Đạt |

## Soát diff
- Không có dòng test cũ bị xóa/skip/nới (diff test chỉ thêm; `test_procedure_approval.py` +15 dòng).
- Tài liệu chỉ đọc (srs, test-cases, use-cases, implementation-plan, golden, CLAUDE.md, .claude, .autopilot, .github): không đổi.
- Phạm vi: chỉ FR-WF-009..012; NC Norm Set chỉ thêm hai trường (theo Quyết định Lead Q1).

## Giới hạn
- **Giao diện không kiểm bằng Playwright:** staging chưa chạy nhánh này (chỉ deploy sau merge) và runtime QA không có tài khoản test. TC-WF-07 (loại M) được phủ bằng test API/unit về dữ liệu khác biệt theo phần, bước, dòng nguồn lực; màn SCR-DSK-011 (màu thêm/bỏ/đổi, 1366×768) cần xem mắt trên staging sau merge.
- Cài mới được chứng minh bởi site sạch `normcore-verify.test` ở trên.
