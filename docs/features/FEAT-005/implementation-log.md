# FEAT-005 — Nhật ký hiện thực (NORM-17)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `python3 docs/tools/build_rtm.py docs`; `git diff --name-only origin/develop...HEAD -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/implementation-plan.md docs/golden` | `VAN DE: 0`; không in gì. Áp AMD-003 (`data-model.md`), AMD-004 (`ux-foundations.md`); ASM-047, 051, 054 dẫn thêm bình luận Lead `01a2028d-…` |
| T02 | `check_conventions.py`; `with_bench.sh 'migrate; run-tests --module …test_nc_specialty; run-tests --module normcore.tests.test_permissions'` | rc=0; 6 tests OK; 3 tests OK (test_co_18_doctype…). Test chặn xóa vì tham chiếu viết ở T03 |
| T03 | `with_bench.sh 'migrate; run-tests --module …test_nc_technical_service; …test_nc_specialty; --test test_TC_SVC_04_nhieu_khoa'` | 4 tests OK; 9 tests OK; `Ran 1 test` OK (viết test và mã cùng lượt, không quan sát bước đỏ riêng) |
| T04 | `with_bench.sh 'run-tests --module …test_nc_technical_service; --test test_TC_SVC_01_nhap_danh_muc; --module normcore.api.test_importer'`; `git diff --stat origin/develop...HEAD -- <tệp khung importer>` | 10 tests OK; `Ran 1 test` OK; 8 tests OK; diff khung rỗng; pytest unit xanh |
| T05 | `pytest normcore/tests/unit/test_chain.py -v`; `grep -n frappe normcore/procedure/chain.py` | 15 passed (**đính chính:** ghi chú cũ "theo 5.3" về `rows=[]` sai cho trường hợp phạm vi khoa; 5.3 điểm 4–5 giữ dòng khoa, xem mục Sửa theo Reviewer); grep không in gì |
| T06 | `with_bench.sh 'run-tests --module normcore.api.test_service; …--test test_TC_SVC_03_tinh_trang_chuoi; --module normcore.tests.test_feat_001'` | 7 tests OK; `Ran 1 test` OK; 20 tests OK (**đính chính:** kỳ vọng `rows=[]` ở phạm vi khoa sai, đã sửa ở mục Sửa theo Reviewer) |
| T07 | `pytest normcore/tests/unit/test_service_ui_conventions.py`; `with_bench.sh '… --test test_SCR_DSK_005_loc_danh_sach'` | 4 passed; `Ran 1 test` OK. Lọc `frappe.get_list` qua bảng con đúng, không lặp dòng. Bộ lọc `page.add_field` chưa chạy trên trình duyệt |
| T08 | `with_bench.sh 'migrate && bench build --app normcore'`; `multica env start preview` | rc=0; Workspace có 3 lối tắt. Preview lỗi: "chưa có site normcore.test trong /home/claudebot/preview-bench" → **chưa kiểm trên trình duyệt** (1366 × 768, 768 px, NC Finance, NC Document Controller, NC Auditor) |
| T09 | — | Nợ kỹ thuật ở `docs/as-built/FEAT-005.md` mục 7 |
| T10 | golden_engine (+ `--no-depr`), golden_cls, `build_rtm.py docs`; `pytest unit golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `with_bench.sh 'migrate && run-tests --app normcore'`; `check_conventions.py`; `ruff check`, `ruff format --check` | golden rc=0, `VAN DE: 0`; 88 passed, cov 98,9%; `Ran 180 tests`, OK; conventions rc=0; ruff sạch |

## Sửa theo Reviewer (PR #21 @ 6bc2a7f, trả về lần 1)
| Mục | Lệnh | Kết quả |
| :-- | :-- | :-- |
| 1 liên kết `#nc-chain-price` | thêm `test_lien_ket_the_gia_chan_noi_bot…` | đỏ → xanh sau khi thêm `e.stopPropagation()`; bỏ `after_save` (API gọi một lần) |
| 2 dòng khoa không quyền | `test_chain.py`, `test_service.py` sửa kỳ vọng theo 5.3 điểm 4–5 và Quyết định Lead | đỏ (3 test chain, 1 test API) → xanh: giữ dòng (tên khoa, `state`), `status` trống, `name/route/date/doctype` rỗng; phép so "có và không có bản ghi" giữ nguyên. `rows=[]` chỉ còn cho thiếu quyền mức vai trò |
| 3 ASM-047 trên form | JS hiện `message` của mục rồi các dòng khoa | thêm nhãn "Chưa có trong phạm vi khoa của bạn" khi mục rỗng và còn dòng khoa |
| 4 tiêu chí 11, 14 | `test_service.py`: thêm bộ "Nháp" v7 và "Đã thay thế" v8 > bản "Đã khóa"; dòng 14 dùng `ROLES` | thử bỏ lọc `status` ở `service.py` → `test_FR_SVC_004_theo_khoa` **đỏ**; đã khôi phục. Mười vai trò không có khóa tiền |
| Nên sửa | `vi.csv` ngữ cảnh `NC Technical Service` cho Active/Inactive, bỏ dòng trùng; `chain._route` mã hóa URL (+ test); bỏ `set_value` vô dụng; sửa chú thích `check_conventions.py`; **ASM-062** | xong |
| T10 lại | golden, `build_rtm.py`; `pytest unit golden --cov… --cov-fail-under=90`; `with_bench.sh 'migrate; bench build; run-tests --app normcore'`; `check_conventions.py`; ruff | golden rc=0, `VAN DE: 0`; 91 passed, cov 98,9%; `Ran 182 tests` OK, build rc=0; conventions rc=0; ruff sạch. Giao diện vẫn **chưa kiểm trên trình duyệt** |
