# FEAT-039 — Nhật ký hiện thực (NORM-29)

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_readonly.py --cov=normcore.core.readonly --cov-fail-under=90`; `grep -n "import frappe" normcore/core/readonly.py` | Quan sát đỏ trước khi có mã (ImportError); sau đó 12 passed, phủ 100%; grep không in gì. Test so `WRITE_PTYPES` với `AUDITOR_FORBIDDEN` nên T01 đã đưa luôn ba cờ `import`, `share`, `set_user_permissions` vào `AUDITOR_FORBIDDEN` (phần này của T02); `check_conventions.py` thoát 0 |
| T02 | `python3 scripts/check_conventions.py`; `pytest normcore/tests/unit/test_permission_matrix.py` | rc=0; 12 passed (7 TC-ACC-04 cũ không sửa + 5 test_TC_CLS_44_nc06_*). Thêm luật NC-06 "thiếu quyền đọc" (DocType cha không phải bảng con) |
| T03 | `with_bench.sh 'migrate && run-tests --module normcore.tests.test_feat_039'`; `bench execute normcore.core.permissions.read_only_violations` | Lần đầu đỏ (Workflow giả commit ngầm, làm bẩn site: test sạch thấy 2 vi phạm); thêm dọn trong `tearDown`; chạy lại 2 lần: 3 tests OK. `execute` không in gì khi kết quả là `[]` (bench bỏ qua giá trị rỗng); có vi phạm thì in danh sách |
| T04 | `with_bench.sh 'run-tests --module normcore.tests.test_feat_039'` | 7 tests OK ngay lần đầu (không quan sát bước đỏ riêng: các thao tác đã kiểm quyền trước kiểm trạng thái nên không phải sửa mã nào). 14 thao tác ghi/xóa/duyệt (+ verify_price nếu có đơn giá) đều `PermissionError`; số bản ghi và `modified` không đổi. Không đổi mã nghiệp vụ |
