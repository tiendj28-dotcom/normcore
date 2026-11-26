# Nghiệm thu FEAT-017: Phân bổ hai cấp và đối soát

Người kiểm: QA (Multica, Tester iu). Commit đã kiểm: xem `verdict.json`. Kết luận: **accepted**.

## Lệnh đã chạy lại
| Lệnh | Kết quả |
| :-- | :-- |
| `python3 docs/golden/golden_engine.py && golden_cls.py` | chạy được |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 859 passed; độ phủ tổng 99%; `reconcile.py` 100% |
| site sạch `normcore-verify.test` (new-site, install-app, `run-tests --app normcore`, drop-site) | 1530 test OK, 389,6 giây |
| `python3 scripts/check_conventions.py` | không lỗi |
| `python3 docs/tools/build_rtm.py docs` | Must chưa có TC: 0; không thêm vấn đề mới |
| `gh pr checks 65` | 2 job pass (Tài liệu/golden/unit; site Frappe v15) |

## Tiêu chí
| Mã | Test | Kết quả |
| :-- | :-- | :-- |
| TC-COST-02 | `normcore/tests/golden/test_allocation_golden.py` | Đạt |
| TC-COST-03 | `normcore/tests/golden/test_allocation_golden.py` | Đạt |
| TC-COST-05 | `normcore/tests/golden/test_allocation_golden.py` | Đạt |
| TC-COST-08 | `normcore/tests/golden/test_allocation_golden.py` | Đạt |
| TC-COST-10 | `test_nc_costing_run_allocation.py` | Đạt |
| TC-COST-14 | `normcore/tests/test_costing_perf.py`: tính 7,6 giây, ghi 35,8 giây, tổng 43,4 giây (ngưỡng 5 phút) | Đạt |
| TC-COST-16 | `test_nc_costing_run_allocation.py`, `test_allocation_golden.py` | Đạt |
| Quyền | `api/test_costing_reconciliation.py`: NC Clinician bị `PermissionError`, NC Auditor chỉ đọc; ma trận `perm_matrix/nc_reconciliation_line.json` | Đạt |
| Soát diff test | không có dòng test cũ bị xóa; không skip/xfail (chữ `skipped` chỉ là tên trường dữ liệu) | Đạt |
| Tài liệu chỉ đọc | diff không chạm srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |

## Giới hạn
Giao diện SCR-DSK-024 chưa kiểm bằng trình duyệt (Playwright) trong lượt này; kiểm bằng test API/báo cáo (`test_nc_reconciliation.py`, `test_reconciliation_ui.py`).
