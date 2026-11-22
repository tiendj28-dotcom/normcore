# FEAT-001 implementation log
Site kiểm: `norm12.test` (site `normcore.test` dùng chung có DocType của NORM-11 nên không dùng được cho toàn app).

- T01–T08 (commit `cc8f8bd`): `bench --site norm12.test run-tests --app normcore --module normcore.tests.test_feat_001` → `Ran 19 tests ... OK`. Test viết cùng lượt với mã, chưa chạy đỏ riêng trước (ghi trung thực).
- Lần chạy đầu của từng nhóm đỏ rồi sửa: thiếu mã khoa ném `ValidationError` (không phải `MandatoryError`); Select bắt buộc tự điền tùy chọn đầu (ASM-045); thông báo xóa của Frappe chỉ nêu bản ghi đầu tiên (thêm `core/references.py`).
- T09: toàn app lần đầu `110 tests, FAILED (errors=3)` ở `api/test_procedure.py` (Clinician chưa gán khoa, G5). Người duyệt chọn (a) → thêm một dòng `assign_department` vào `setUp` (ASM-037). Sau đó: `Ran 110 tests ... OK`.
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` → `43 passed`; engine.py 99%.
- `pytest normcore/tests/unit -k TC_ACC_04 -v` → 6 passed. `python3 scripts/check_conventions.py` → thoát 0.

## Sửa theo review (PR #14)
- Lệch quy trình: issue yêu cầu mỗi task một commit `FEAT-001 Tnn:`, nhưng lần đầu push chỉ có một commit WIP gộp T01–T08 (đã push nên không viết lại). Từ lần sửa này mỗi việc một commit.
- Lint: B905 (`zip(..., strict=True)`, dòng ma trận sai số cột nay báo NC-08 thay vì cắt bớt) và `ruff format` (chỉ khoảng trắng, ngắt dòng). `ruff check normcore scripts && ruff format --check normcore scripts` → thoát 0.
- R9: thêm `test_TC_ACC_01_auditor_doc_lan_tinh_gia_khong_ghi`. Toàn app trên `norm12.test`: `Ran 112 tests ... OK`.

## Sửa theo review lần 3 (nút "Bỏ gán")
- Lỗi: `frm.dashboard.wrapper` không tồn tại. Sửa: `frm.layout.show_message(html, "blue", true)` và gắn sự kiện ở `frm.layout.message` (ủy quyền `a[data-user]`); xóa thông báo cũ trước khi vẽ lại vì `show_message` nối thêm.
- Chạy `nc_department.js` bằng Node với bản giả lập tối thiểu (`frm.layout.message` có `off/on`, `show_message` nối thêm như Frappe thật; không phải trình duyệt): vẽ 2 lần → 1 khối, có liên kết "Bỏ gán"; bấm → gọi `unassign_department {"user":"a@x.test","department":"K01"}` rồi `list_department_users` để vẽ lại; không lỗi.
- Chưa có ảnh chụp giao diện: môi trường agent không có trình duyệt (không Chromium/Playwright).
