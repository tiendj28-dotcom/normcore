# FEAT-009 — Nhật ký hiện thực (NORM-18)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_pricing.py normcore/tests/golden/test_material_golden.py` | đỏ (không import được) → xanh sau khi viết `pricing.py`; 2 test tự sai dữ liệu mẫu (ngày chứng từ) đã sửa trong lượt viết; `pricing.py` cov 99% |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate && run-tests --module …test_nc_item && …test_nc_item_price && normcore.tests.test_permissions'` | rc=0; 10 OK; 13 OK; 3 OK. Lần đầu đỏ: validate chạy trước kiểm bắt buộc, Select tự chọn tùy chọn đầu → thêm tùy chọn rỗng đầu và kiểm `is not None` |
| T03 | `with_bench.sh 'migrate && run-tests --module normcore.api.test_item'` | 13 tests OK (TC-RES-01, 02, 08, TC-CLS-45..47, TC-ADM-02) |
| T04 | `pytest normcore/tests/unit/test_item_ui_conventions.py`; `with_bench.sh 'migrate && bench build --app normcore'` | 4 passed; build thoát 0. **Chưa kiểm trên trình duyệt** (preview thiếu site như FEAT-005) |
| T05 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0` |
| T06 | golden_engine (+ `--no-depr`), golden_cls; `pytest unit golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py`; `ruff check`, `ruff format --check` | golden rc=0; 120 passed, cov 98,83%; lần đầu `Ran 247`, 2 FAIL ở `test_importer.py` (Finance, RM thấy thêm bộ `nc_item`) → sửa kỳ vọng theo ASM-074 → `Ran 247 tests`, OK; conventions rc=0; ruff sạch |

## Sửa theo Reviewer và Lead (PR #26 @ 95c3a00, trả về lần 1)
Nguồn: bình luận Reviewer `01a20530-…`, Lead `01a2052d-…` và `01a20531-…`.

| Mục | Lệnh | Kết quả |
| :-- | :-- | :-- |
| B1 `material_line` quy đổi đơn vị (ASM-075) | `pytest normcore/tests/unit/test_pricing.py normcore/tests/golden` | 33 passed: HC_GLU 1 đơn vị ra `30000.00`, đơn giá khớp `golden_cls.unit_price`; mọi mặt hàng golden_cls khớp; số đơn vị = 1 vẫn khớp L02, L05, L06, L11; thiếu hoặc ≤ 0 báo lỗi |
| A ASM-071, AMD-005 `price_code`, bộ nhập `nc_item_price` | `with_bench.sh 'migrate; run-tests --module normcore.api.test_item'` | 23 tests OK (`test_FR_RES_012_don_gia_*`: tạo, cập nhật theo mã, nhập lại không đổi, mặt hàng lạ, thiếu trường, cùng số chứng từ không đè nhau, đã xác minh không ghi đè, Auditor và vai trò không quyền bị từ chối, tải mẫu rồi nhập lại) |
| A ASM-069 khóa đã xác minh; B4 `no_copy` | `… run-tests --module …test_nc_item_price` | 23 tests OK. Lưu ý: `frappe.copy_doc` phía máy chủ mặc định bỏ qua `no_copy`, test dùng `ignore_no_copy=False` như nút Nhân bản |
| B3 `getdate` | cùng lệnh | OK (`test_FR_RES_002_doi_rieng_valid_to_*`, nhập Excel đổi riêng `valid_to`) |
| A ASM-072, B2 | `… run-tests --module …test_nc_item`, `…api.test_item` | OK (hóa chất để trống bị từ chối cả form và Excel; API trả `norm_unit_price=None`) |
| B5–B8 | `pytest normcore/tests/unit/test_item_ui_conventions.py` | 6 passed (mọi `__()` có ngữ cảnh, bảng cuộn ngang); `vi.csv` đổi sang có ngữ cảnh |
| ASM-065 | `grep FEAT-012` trong tài liệu FEAT-009 | đã đổi sang FEAT-015 |
| Toàn bộ | golden (+`--no-depr`), `build_rtm.py docs`, `pytest unit golden --cov…`, `check_conventions.py`, ruff, `with_bench.sh 'migrate && bench build --app normcore && run-tests --app normcore'` | golden rc=0; `VAN DE: 0`; 127 passed, cov 98,86%; conventions rc=0; ruff sạch; **`Ran 278 tests`, FAILED (failures=2)** |

**Hai test đỏ có chủ ý (ASM-074, chờ tiendj28; Lead dặn không sửa thêm test cũ):**
- `normcore.api.test_importer.TestImporterAPI.test_finance_thay_bo_nhap_va_import_file_qua_file_rieng_tu`: `AssertionError: Lists differ: ['nc_item', 'nc_item_price', 'nc_job_title'] != ['nc_item', 'nc_job_title']`
- `normcore.api.test_importer.TestImporterAPI.test_vai_tro_chi_doc_va_auditor_bi_tu_choi`: `AssertionError: Lists differ: ['nc_item', 'nc_item_price'] != ['nc_item']`

Khi được duyệt: sửa đúng ba kỳ vọng đã nêu (hai ở `test_importer.py` thành thêm `nc_item_price`, Resource Manager `[nc_item, nc_item_price]`) cùng docstring `test_permissions.py:1`, rồi chạy lại toàn bộ.
