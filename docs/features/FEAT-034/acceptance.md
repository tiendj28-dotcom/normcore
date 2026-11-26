# Nghiệm thu FEAT-034 — Định mức theo hệ thống xét nghiệm

Commit đã kiểm: `f86a5f4` (nhánh `feat/FEAT-034-norm-test-system`, PR #58). Người kiểm: Tester iu (QA độc lập).

## Lệnh đã chạy
| Lệnh | Kết quả |
| :-- | :-- |
| `scripts/with_bench.sh` tạo site sạch `normcore-verify.test`, cài app, `run-tests --app normcore`, xóa site | Ran 1338 tests, OK, RC=0 |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 708 passed; độ phủ 99% |
| `python3 docs/golden/golden_engine.py && golden_cls.py` | chạy được, số khớp |
| `python3 scripts/check_conventions.py` | exit 0 |
| `python3 docs/tools/build_rtm.py docs` | không thêm vấn đề mới (Must chưa có TC: 0) |
| `gh pr checks 58` | 2/2 pass |

## Tiêu chí → bằng chứng
| Tiêu chí | Test | Đạt |
| :-- | :-- | :-- |
| TC-CLS-29 khởi tạo bộ GLU-A, khoản mục bắt buộc thêm dạng dòng chung chưa có lượng | `test_TC_CLS_29_*` (3 test) | Đạt |
| TC-CLS-30 cấp phát sinh, cờ k chỉ ở dòng Theo kết quả loại thuốc/vật tư, bật thì hao hụt về 0 | `test_TC_CLS_30_*` (4 test) | Đạt |
| TC-CLS-31 từ chối dòng dùng QC_L | `test_TC_CLS_31_*` (2 test) | Đạt |
| TC-CLS-32 xác nhận chuyên môn từ chối khi thiếu số XN mỗi ống / khoản mục bắt buộc; qua khi nhập hoặc "Không áp dụng" | `test_TC_CLS_32_*` (3 test) | Đạt |
| TC-CLS-33 sao chép GLU-A→GLU-B, khóa, xuất; tệp có cấp phát sinh, kế hoạch chất lượng, k | `test_TC_CLS_33_*` (6 test) | Đạt |
| DocType mới (NC Norm Template, Template Item): vai trò không quyền và NC Auditor | `test_nc_norm_template.py`, `api/test_norm_cls.py` | Đạt |

## Soát diff
- Không có test bị xóa, skip, nới (dòng "skipped" trong diff là tên trường của hàm sao chép, không phải test skip).
- Không sửa tài liệu chỉ đọc. Ngoài phạm vi: `scripts/check_conventions.py` thêm hàng ma trận cho NC Norm Template, cần cho DocType mới, chấp nhận.
- Đổi cấu trúc DocType đã lên staging có patch `set_norm_line_cost_level`, khai báo ở `patches.txt`.

## Chưa kiểm
- Kiểm giao diện bằng trình duyệt trên staging: nhánh chưa merge nên staging chưa có màn hình; phần giao diện được phủ bằng test unit (`test_norm_cls_ui.py`, `test_norm_template_ui.py`).

## Kiểm lại sau merge develop (HEAD `bd54fd5`)
Dev merge `origin/develop` (sau PR #57) và sắp lại `vi.csv`; Lead cho QA chạy lại nhanh.
| Lệnh | Kết quả |
| :-- | :-- |
| Site sạch `normcore-verify.test`, `run-tests --app normcore` | Ran 1390 tests, OK, RC=0 |
| pytest unit + golden + độ phủ | 743 passed, độ phủ 99% |
| `check_conventions.py` | exit 0 |
| `build_rtm.py docs` | không thêm vấn đề; Must chưa có TC: 0 |
| `vi.csv`: so dòng hai bên merge với HEAD | không thiếu dòng nào |
| Tài liệu chỉ đọc đổi từ `f86a5f4` | 0 tệp |
