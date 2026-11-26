# Acceptance FEAT-032 — Kế hoạch chất lượng và ngoại kiểm (NORM-45)

Kết luận: **accepted.** Kiểm độc lập sau khi PR #44 đã merge trước QA (merge commit `b0f8671`), trên HEAD develop `6ecef6de69bbe385d32fd99d67a7ca746bf5be9d`. QA không viết FEAT này.

## Phần A — chạy lại trên site sạch
| Lệnh | Kết quả | Đạt |
| :-- | :-- | :-: |
| `with_bench.sh`: `bench new-site normcore-verify.test --install-app normcore` rồi `run-tests --app normcore` | Ran 968 tests, OK (site xóa sau khi chạy) | Đạt |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` | 483 passed; độ phủ costing + benchmark 99%, `qc_plans.py` 97% | Đạt |
| `golden_engine.py`, `golden_cls.py` | thoát 0 | Đạt |
| `check_conventions.py` | thoát 0 | Đạt |
| `build_rtm.py docs` | không báo Must chưa có TC | Đạt |
| CI PR #44 | "Test trên site Frappe v15" và "Tài liệu, golden, unit test" SUCCESS | Đạt |

## Phủ TC
| TC | FR | Test | Đạt |
| :-- | :-- | :-- | :-: |
| TC-CLS-24 | FR-QC-001..003 | `test_TC_CLS_24_*` ở nc_qc_plan, nc_eqa_program, unit/test_qc_plans: bỏ từng trường bắt buộc → từ chối, điền đủ → lưu được; số 0 bị từ chối | Đạt |
| TC-CLS-25 | FR-QC-005, FR-QC-008 | `test_TC_CLS_25_vat_lieu_noi_kiem_sai_loai` (HC_GLU, thông báo nêu "HC_GLU" và "Vật liệu nội kiểm"), `_chat_chuan_sai_loai`, `_50_va_40_bi_tu_choi` (nêu 90 và 100), `_60_va_40_luu_duoc`, `_de_trong_chia_deu` ([0.5, 0.5]) | Đạt |
| TC-CLS-26 | FR-QC-007 | `api/test_qc_plan.py::test_TC_CLS_26_*`, unit: hệ thống Hóa sinh không kế hoạch hoặc 0 dòng nội kiểm → cảnh báo; có nội kiểm / nhóm khác → không; hàm không ném lỗi | Đạt một phần (xem dưới) |

TC-CLS-26 "vẫn khóa được bộ định mức": NC Norm Set chưa có `test_system` ở FEAT này; gắn cảnh báo vào bộ định mức và kiểm khóa thuộc FEAT-034 (ASM-032-05, Lead đã duyệt thiết kế). FEAT-034 phải thêm test đó.

Số liệu: số test ước tính khớp golden (600, 48, 12) ở `tests/golden/test_qc_plans_golden.py`; FEAT này không có phép tính tiền.

## Soát diff PR #44
- Không xóa, skip, nới test. Hai test cũ được sửa: `tests/unit/test_scope_registry.py` (tập DocType có phạm vi khoa thêm NC QC Plan, NC EQA Program, ASM-032-11 theo Quyết định Lead) và `api/test_system.py` (hàm `_qc_plan_values`, không phải test).
- Phạm vi: DocType mới, `costing/qc_plans.py`, `core/permissions.py` (`ScopeRule.via`, chỉ thêm), scope_rules JSON, bộ nhập, workspace, `vi.csv`, `check_conventions.py` (hai dòng `DOCTYPE_ROW`). Quyền theo dòng ma trận chung. Không sửa tài liệu chỉ đọc (docs chỉ thêm thư mục FEAT-032).

## Phần B — giao diện trên staging (http://112.213.88.40:8100, Clinician Test)
| Màn hình | Kết quả | Ảnh |
| :-- | :-- | :-- |
| SCR-DSK-033 Kế hoạch chất lượng (`/app/nc-qc-plan/new`) | Form có Hệ thống xét nghiệm, Số ngày chạy (mô tả ký hiệu D), bảng Nội kiểm, bảng Chuẩn máy, khối "Số test ước tính" hiện ngay (0 test, "Chưa đủ số liệu") | `evidence/scr-dsk-033-clinician.png` |
| SCR-DSK-034 Chương trình ngoại kiểm (`/app/nc-eqa-program/new`) | Đủ trường, phí vận chuyển mặc định 0, bảng dịch vụ + Tỷ lệ riêng, tóm tắt "Chia đều cho 1 dịch vụ (100.00%)" | `evidence/scr-dsk-034-clinician.png` |

Giới hạn: không tạo bản ghi THU- trên staging nên từ chối sai loại / tổng ≠ 100% kiểm bằng test bench, không bằng thao tác tay. Gọi REST tạo bản ghi rỗng bằng Clinician và Auditor đều trả 403 nhưng không dùng làm bằng chứng quyền vì thiếu CSRF token; quyền theo ma trận và phạm vi khoa dựa vào test bench (`test_nc_qc_plan.py`, `test_nc_eqa_program.py`, `test_permissions.py`).
