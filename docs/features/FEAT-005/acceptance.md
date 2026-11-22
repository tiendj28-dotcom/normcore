# Acceptance FEAT-005 — Kiểm định độc lập (NORM-17, QA)

Kết luận: **accepted**. Mã và test đạt; giao diện **chưa kiểm bằng trình duyệt** (xem mục cuối).

## Môi trường kiểm
Nhánh `feat/FEAT-005-danh-muc-ky-thuat` tại `1cc3a15`. **Không tạo được site sạch** `normcore-verify.test`: `DB_ROOT_PASSWORD` không có trong môi trường QA, `bench new-site` lỗi `Access denied for user 'root'` (đã dọn thư mục site dở). Thay bằng `migrate` rồi chạy toàn bộ trên site dùng chung `normcore.test` qua `with_bench.sh` (khóa, mã trỏ đúng checkout này). Kết quả đáng tin về mã; chưa chứng minh cài mới từ đầu (CI "Test trên site Frappe v15" của PR cài mới và xanh).

| Lệnh | Kết quả |
| :-- | :-- |
| `with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'` | rc=0, `Ran 182 tests`, OK |
| ba lệnh `--test` của TC-SVC-01, 03, 04 | mỗi lệnh `Ran 1 test` / `OK` |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` | 91 passed, độ phủ 98,9% |
| `golden_engine.py`, `golden_cls.py`, `check_conventions.py` | thoát 0 |
| `build_rtm.py docs` | `VAN DE: 0` |
| `gh pr checks 21` | cả hai job pass |

## Độ phủ tiêu chí
| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| TC-SVC-01 (10 dòng → 7 tạo; lỗi dòng 9, 10, 11 tiếng Việt) | `test_TC_SVC_01_nhap_danh_muc`: chế độ thử không ghi; ghi created=7; kiểm đúng ba thông báo (thiếu tên dòng 9; trùng SVC01 dòng 10; trùng SVC02 dòng 11) | Đạt |
| TC-SVC-03 (bốn mục, đều có liên kết) | `test_TC_SVC_03_tinh_trang_chuoi` (NC Finance): thứ tự procedure, norm_set, cost, price; mỗi mục có liên kết; ba liên kết đúng bản ghi; mục 4 `#nc-chain-price` | Đạt |
| TC-SVC-04 (K01 rồi K02) | `test_TC_SVC_04_nhieu_khoa` | Đạt |
| FR-SVC-001/002 | `test_FR_SVC_001_*`, `test_FR_SVC_002_thieu_ma` (cập nhật theo mã, chuyên khoa lạ, tải mẫu nhập lại) | Đạt |
| FR-SVC-003 | `test_FR_SVC_003_trung_khoa_bi_tu_choi`, `..._vai_tro_chi_doc_khong_sua` | Đạt |
| FR-SVC-004, FR-ACC-005 | `test_FR_SVC_004_*` (api/test_service.py: quyền theo vai trò, không hiện tiền), `test_FR_ACC_005_khong_lo_thong_tin`, `..._tu_choi`, `..._ham_duoc_whitelist_khong_guest`; 15 test đơn vị `test_chain.py` | Đạt |
| SCR-DSK-005 lọc danh sách | `test_SCR_DSK_005_loc_danh_sach` | Đạt |
| Vai trò không quyền + NC Auditor, DocType mới NC Specialty | `test_FR_ACC_002_vai_tro_chi_doc_khong_ghi`, `test_FR_ACC_007_auditor_chi_doc`, `test_FR_SVC_001_vai_tro_ngoai_ma_tran_khong_doc`, `test_FR_ADM_005_*` (chặn xóa khi đang tham chiếu), `test_FR_ACC_002_doc_controller_khong_xoa` | Đạt |
| Quyền theo ma trận | `test_permissions`, `check_conventions.py` thoát 0 | Đạt |

## 19 điều kiện của technical-design mục 6 (dòng → lệnh → kết quả)
Chạy lại ở `3e94707` (mã giống `1cc3a15`). Dòng 1–15, 17: `with_bench.sh 'bench --site normcore.test run-tests --module <M> --test <tên>'`, mỗi lệnh `Ran 1 test`, `OK`. Dòng 18: `--module` của `test_nc_specialty`. Dòng 16, 19: `pytest` tệp tương ứng.

| # | Test | Kết quả | Đạt |
| :-- | :-- | :-- | :-: |
| 1 | `test_TC_SVC_01_nhap_danh_muc` | Ran 1 test, OK | Đạt |
| 2 | `test_FR_SVC_001_tai_mau_nhap_lai` | Ran 1 test, OK | Đạt |
| 3 | `test_FR_SVC_001_cap_nhat_theo_ma` | Ran 1 test, OK | Đạt |
| 4 | `test_FR_SVC_001_chuyen_khoa_la` | Ran 1 test, OK | Đạt |
| 5 | `test_FR_SVC_002_thieu_ma` | Ran 1 test, OK | Đạt |
| 6 | `test_FR_SVC_001_vai_tro_chi_doc_bi_tu_choi` | Ran 1 test, OK | Đạt |
| 7 | `test_TC_SVC_04_nhieu_khoa` | Ran 1 test, OK | Đạt |
| 8 | `test_FR_SVC_003_trung_khoa_bi_tu_choi`, `test_FR_SVC_003_vai_tro_chi_doc_khong_sua` | mỗi test Ran 1 test, OK | Đạt |
| 9 | `test_TC_SVC_03_tinh_trang_chuoi` | Ran 1 test, OK | Đạt |
| 10 | `test_FR_SVC_004_chua_co_gi` | Ran 1 test, OK | Đạt |
| 11 | `test_FR_SVC_004_theo_khoa` | Ran 1 test, OK; thử bỏ lọc: xem mục dưới (đỏ) | Đạt |
| 12 | `test_FR_SVC_004_quyen_theo_vai_tro` | Ran 1 test, OK | Đạt |
| 13 | `test_FR_ACC_005_khong_lo_thong_tin` | Ran 1 test, OK | Đạt |
| 14 | `test_FR_SVC_004_khong_hien_tien` | Ran 1 test, OK | Đạt |
| 15 | `test_FR_ACC_005_tu_choi` | Ran 1 test, OK | Đạt |
| 16 | `test_chain.py` (`test_FR_SVC_004_*`) | 16 passed (yêu cầu ≥ 8) | Đạt |
| 17 | `test_SCR_DSK_005_loc_danh_sach` | Ran 1 test, OK | Đạt |
| 18 | `test_nc_specialty.py` | Ran 9 tests, OK | Đạt |
| 19 | `test_service_ui_conventions.py` | 6 passed | Đạt |

## Thử bỏ lọc trạng thái ở `normcore/api/service.py` (dòng 11)
Tạm xóa hai điều kiện lọc: `"workflow_state": "Đã ban hành"` ở `_procedure_rows` và `"status": "Đã khóa"` ở `_norm_rows` (chỉ trên bản làm việc, không commit, đã `git checkout` khôi phục). Chạy `--test test_FR_SVC_004_theo_khoa`: **FAIL** (`AssertionError: Lists differ: ['ok', 'ok'] != ['ok', 'empty']`, `FAILED (failures=1)`), tức quy trình Nháp bị chọn nhầm. Dòng 11 đủ nhạy để bắt lỗi bỏ lọc. Chưa thử bỏ riêng từng lọc.

## Preview (`multica env start preview`)
Chạy ở bước bổ sung: thoát lỗi `[preview] chưa có site normcore.test trong /home/claudebot/preview-bench (tạo một lần theo multica/README.md mục Preview site)`. Không có site preview nên không kiểm được giao diện. Cần người dựng `preview-bench` (README) và cấp `DB_ROOT_PASSWORD` cho QA.

## Soát diff test và tài liệu
- Chỉ một test bị đổi: `test_co_16_doctype_va_10_vai_tro` → `test_co_18_...` (16 → 18), đúng ASM-053/Lead đã chốt; mỗi dòng xóa khác không phải assertion. Không skip, không nới.
- `check_conventions.py` mở rộng bảng cho NC Specialty (thêm, không nới luật).
- Không sửa tài liệu chỉ đọc (srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github). AMD-003/004 sửa data-model, ux-foundations có hồ sơ.
- Phạm vi: chỉ FR-SVC-001..004; không thấy sửa ngoài phạm vi.

## Chưa kiểm được
- Preview không có site (xem mục Preview). Playwright MCP không kết nối được (`CONNECTION_CLOSED`) nên chưa mở được staging `http://112.213.88.40:8100` bằng trình duyệt; chưa xem bộ lọc khoa, bố cục bốn thẻ ở 1366×768 và 768 px. Như FEAT-004, đề nghị người duyệt bấm thử SCR-DSK-005/006 trên staging.
- ASM-048, ASM-060 chờ người ngoài squad xác nhận.
