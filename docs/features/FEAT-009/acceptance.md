# Nghiệm thu FEAT-009: Mặt hàng và đơn giá có chứng từ (gồm 1.1)

Kiểm tại commit `dc1d8fa9a4442501e1731c16f5aa30a30ac06258` (nhánh `ai/NORM-18-feat-009`, PR #26). Người kiểm: QA, độc lập với Dev.

## Lệnh đã chạy và kết quả

| Lệnh | Kết quả |
| :-- | :-- |
| `scripts/with_bench.sh 'bench new-site normcore-verify.test … --install-app normcore && set-config allow_tests true && run-tests --app normcore; drop-site'` (site sạch) | **Ran 411 tests, OK**; site đã xóa |
| `python3 docs/golden/golden_engine.py`, `golden_cls.py` | rc=0 |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90` | 169 passed; độ phủ 98,44% (pricing.py 99%, resources.py 97%) |
| `python3 scripts/check_conventions.py` | rc=0 |
| `python3 docs/tools/build_rtm.py docs` | Must chưa có TC: 0, không vấn đề mới |
| `gh pr checks 26` | cả hai job pass |

## Tiêu chí → bằng chứng

| Tiêu chí | Test | Kết quả |
| :-- | :-- | :-- |
| TC-RES-01, TC-CLS-45 (nguồn rồi ngày hiệu lực, theo 1.1) | `test_pricing.py`, `api/test_item.py` | Đạt |
| TC-RES-02 (quá 24 tháng, cảnh báo, vẫn tính) | `test_pricing.py`, `api/test_item.py` | Đạt |
| TC-RES-07 (thanh toán riêng, 0 đồng, có lý do loại; FR-RES-014) | `test_pricing.py`, `golden/test_material_golden.py` | Đạt |
| TC-RES-08 (nhập tệp, 2 dòng lỗi) | `api/test_item.py` | Đạt |
| TC-RES-09 (thiếu đơn vị tính bị từ chối) | `nc_item/test_nc_item.py` | Đạt |
| TC-CLS-46 (hết hiệu lực, xác minh cần tệp, cảnh báo chưa xác minh) | `nc_item_price/test_nc_item_price.py`, `test_pricing.py`, `api/test_item.py` | Đạt |
| TC-CLS-47 (6.000.000 / 200 = 30.000,0000) | `test_pricing.py`, `golden/test_material_golden.py` | Đạt |
| FR-RES-001, 013, 018 | `test_FR_RES_001/013/018*` | Đạt |
| Quyền: vai trò không quyền và NC Auditor, 2 DocType mới | `tests/test_permissions.py` (27 DocType) và test DocType | Đạt |

## Soát diff
- Test cũ bị sửa: `test_importer.py` (danh sách bộ nhập thêm `nc_item`, `nc_item_price`) và `test_permissions.py` (25→27 DocType). Chỉ mở rộng theo ASM-096 (Lead duyệt), không nới, không skip, không đổi giá trị tiền.
- Không có `skip`/`expectedFailure` thêm mới.
- Tài liệu chỉ đọc (srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github): không bị sửa.
- Phạm vi: chỉ tệp FEAT-009; `scripts/check_conventions.py` thêm 2 dòng cho DocType mới (chấp nhận được).

## Ca đổi loại mặt hàng (Lead yêu cầu, ASM-094)

Lệnh (site sạch `normcore-verify.test`, qua `with_bench.sh`, `bench --site … console`, Administrator, rollback sau khi chạy, site đã xóa):
1. Tạo NC Item loại "Vật tư tiêu hao", để trống số đơn vị định mức → **lưu được, `norm_units_per_purchase_unit = 1`**.
2. Đổi `item_type` sang "Hóa chất" rồi `save()` → **lưu được, `item_type = Hóa chất`, số đơn vị vẫn 1,0**.

Kết quả: đúng mong đợi (FR-RES-018 chỉ buộc khai số đơn vị lúc tạo; `_check_norm_units` thấy 1 > 0 nên không chặn). Hệ quả: mặt hàng hóa chất có thể mang số đơn vị định mức 1 do mặc định cũ, không do người dùng khai. Ghi ở As-Built mục 7.

## Giới hạn
Playwright MCP không kết nối được (CONNECTION_CLOSED) nên **chưa kiểm bằng giao diện trình duyệt**. Quyền vai trò và luồng API được kiểm qua test trên site sạch (vai trò không quyền, NC Auditor, Resource Manager, Finance).

## Verdict: accepted
